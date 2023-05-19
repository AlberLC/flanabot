__all__ = ['FlanaBot']

import asyncio
import datetime
import random
import time
from abc import ABC
from typing import Iterable

import flanautils
import pymongo
import pytz
from flanaapis import InstagramLoginError, MediaNotFoundError, PlaceNotFoundError
from flanautils import return_if_first_empty
from multibot import BadRoleError, MultiBot, RegisteredCallback, Role, User, bot_mentioned, constants as multibot_constants, group, inline, owner

from flanabot import constants
from flanabot.bots.connect_4_bot import Connect4Bot
from flanabot.bots.penalty_bot import PenaltyBot
from flanabot.bots.poll_bot import PollBot
from flanabot.bots.scraper_bot import ScraperBot
from flanabot.bots.ubereats_bot import UberEatsBot
from flanabot.bots.weather_bot import WeatherBot
from flanabot.models import Action, BotAction, ButtonsGroup, Chat, Message


# ----------------------------------------------------------------------------------------------------- #
# --------------------------------------------- FLANA_BOT --------------------------------------------- #
# ----------------------------------------------------------------------------------------------------- #
class FlanaBot(Connect4Bot, PenaltyBot, PollBot, ScraperBot, UberEatsBot, WeatherBot, MultiBot, ABC):
    Chat = Chat
    Message = Message

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tunnel_chat = None
        self.help_calls = {}

    # -------------------------------------------------------- #
    # ------------------- PROTECTED METHODS ------------------ #
    # -------------------------------------------------------- #
    def _add_handlers(self):
        super()._add_handlers()

        self.register(self._on_activate_tunnel, (multibot_constants.KEYWORDS['activate'], constants.KEYWORDS['tunnel']))

        self.register(self._on_bye, multibot_constants.KEYWORDS['bye'])

        self.register(self._on_config, multibot_constants.KEYWORDS['config'])
        self.register(self._on_config, (multibot_constants.KEYWORDS['show'], multibot_constants.KEYWORDS['config']))

        self.register(self._on_database_messages, (multibot_constants.KEYWORDS['last'], multibot_constants.KEYWORDS['message']))
        self.register(lambda message: self._on_database_messages(message, simple=True), (multibot_constants.KEYWORDS['last'], multibot_constants.KEYWORDS['message'], multibot_constants.KEYWORDS['simple']))

        self.register(self._on_deactivate_tunnel, (multibot_constants.KEYWORDS['deactivate'], constants.KEYWORDS['tunnel']))

        self.register(self._on_delete, multibot_constants.KEYWORDS['delete'])
        self.register(self._on_delete, (multibot_constants.KEYWORDS['delete'], multibot_constants.KEYWORDS['message']))

        self.register(self._on_hello, multibot_constants.KEYWORDS['hello'])

        self.register(self._on_help, multibot_constants.KEYWORDS['help'])

        self.register(self._on_new_message_default, default=True)

        self.register(self._on_recover_message, multibot_constants.KEYWORDS['reset'])
        self.register(self._on_recover_message, multibot_constants.KEYWORDS['message'])
        self.register(self._on_recover_message, (multibot_constants.KEYWORDS['reset'], multibot_constants.KEYWORDS['message']))

        self.register(self._on_roles, multibot_constants.KEYWORDS['permission'])
        self.register(self._on_roles, multibot_constants.KEYWORDS['role'])
        self.register(self._on_roles, (multibot_constants.KEYWORDS['permission'], multibot_constants.KEYWORDS['role']))
        self.register(self._on_roles, (multibot_constants.KEYWORDS['change'], multibot_constants.KEYWORDS['permission']))
        self.register(self._on_roles, (multibot_constants.KEYWORDS['activate'], multibot_constants.KEYWORDS['role']))
        self.register(self._on_roles, (multibot_constants.KEYWORDS['deactivate'], multibot_constants.KEYWORDS['role']))

        self.register(self._on_tunnel_message, always=True)

        self.register(self._on_users, multibot_constants.KEYWORDS['user'])

        self.register_button(self._on_config_button_press, ButtonsGroup.CONFIG)
        self.register_button(self._on_roles_button_press, ButtonsGroup.ROLES)
        self.register_button(self._on_users_button_press, ButtonsGroup.USERS)

    async def _changeable_roles(self, group_: int | str | Chat | Message) -> list[Role]:
        return []

    @return_if_first_empty(exclude_self_types='FlanaBot', globals_=globals())
    async def _get_message(
        self,
        event: multibot_constants.MESSAGE_EVENT,
        pull_overwrite_fields: Iterable[str] = ('_id', 'config', 'date', 'ubereats')
    ) -> Message:
        return await super()._get_message(event, pull_overwrite_fields)

    @return_if_first_empty(exclude_self_types='FlanaBot', globals_=globals())
    async def _manage_exceptions(
        self,
        exceptions: Exception | Iterable[Exception],
        context: Chat | Message,
        reraise=False,
        print_traceback=False
    ):
        if not isinstance(exceptions, Iterable):
            exceptions = (exceptions,)

        for exception in exceptions:
            try:
                raise exception
            except BadRoleError as e:
                await self.send_error(f'Rol no encontrado en {e}', context)
            except InstagramLoginError as e:
                await self.send_error(f'No me puedo loguear en Instagram {random.choice(multibot_constants.SAD_EMOJIS)}  👉  {e}', context)
            except MediaNotFoundError as e:
                await self.send_error(f'No he podido sacar nada de {e.source} {random.choice(multibot_constants.SAD_EMOJIS)}', context)
            except PlaceNotFoundError as e:
                await self.send_error(f'No he podido encontrar "{e}" {random.choice(multibot_constants.SAD_EMOJIS)}', context)
            except Exception as e:
                await super()._manage_exceptions(e, context, reraise, print_traceback)

    async def _role_state_options(self, group_: int | str | Chat | Message, activated_user_role_names: list[str]) -> list[str]:
        options = []
        for role in await self._changeable_roles(group_):
            if role.name == '@everyone':
                continue

            if role.name in activated_user_role_names:
                options.append(f'✔ {role.name}')
            else:
                options.append(f'❌ {role.name}')
        options.reverse()

        return options

    # ---------------------------------------------- #
    #                    HANDLERS                    #
    # ---------------------------------------------- #
    async def _on_activate_tunnel(self, message: Message):
        keywords = (*multibot_constants.KEYWORDS['activate'], *constants.KEYWORDS['tunnel'])
        try:
            chat_id_or_name = next(part for part in flanautils.remove_accents(message.text.lower()).split() if not flanautils.cartesian_product_string_matching(part, keywords, multibot_constants.PARSER_MIN_SCORE_DEFAULT))
        except StopIteration:
            return

        chat_id_or_name = flanautils.cast_number(chat_id_or_name, raise_exception=False)
        if (chat := await self.get_chat(chat_id_or_name)) or (chat := await self.get_chat(await self.get_user(chat_id_or_name))):
            self.tunnel_chat = chat
            await self.send(f"Túnel abierto con <b>{chat.name}{f' ({chat.group_name})' if chat.group_name else ''}</b>.", message)
        else:
            await self.send_error('Chat inválido.', message)

    async def _on_bye(self, message: Message):
        if message.chat.is_private or self.is_bot_mentioned(message):
            await self.send_bye(message)

    async def _on_config(self, message: Message):
        if message.chat.is_private:
            config_names = ('auto_insult', 'auto_scraping', 'scraping_delete_original', 'ubereats')
        elif self.is_bot_mentioned(message):
            config_names = (
                'auto_insult',
                'auto_scraping',
                'auto_weather_chart',
                'check_flood',
                'punish',
                'scraping_delete_original'
            )
        else:
            return

        buttons_texts = []
        for k, v in message.chat.config.items():
            if k not in config_names:
                continue
            if k == 'ubereats':
                k = f"ubereats (cada {flanautils.TimeUnits(seconds=message.chat.ubereats['seconds']).to_words()})"
            buttons_texts.append((f"{'✔' if v else '❌'} {k}", v))

        await self.send('<b>Estos son los ajustes del chat:</b>\n\n', flanautils.chunks(buttons_texts, 3), message, buttons_key=ButtonsGroup.CONFIG)
        await self.delete_message(message)

    async def _on_config_button_press(self, message: Message):
        await self.accept_button_event(message)

        if message.buttons_info.presser_user.is_admin is False or not message.buttons_info.pressed_button:
            return

        config_name = message.buttons_info.pressed_text.split()[1]
        message.chat.config[config_name] = not message.chat.config[config_name]
        if config_name == 'ubereats':
            if message.chat.config[config_name]:
                await self.start_ubereats(message.chat)
            else:
                await self.stop_ubereats(message.chat)
            button_text = f"ubereats (cada {flanautils.TimeUnits(seconds=message.chat.ubereats['seconds']).to_words()})"
        else:
            button_text = config_name
        message.buttons_info.pressed_button.text = f"{'✔' if message.chat.config[config_name] else '❌'} {button_text}"

        await self.edit(message.buttons_info.buttons, message)

    @owner
    async def _on_database_messages(self, message: Message, simple=False):
        if message.chat.is_group and not self.is_bot_mentioned(message):
            return

        n_messages = flanautils.text_to_number(message.text)
        if not n_messages:
            n_messages = 1

        await self.send(
            self.get_formatted_last_database_messages(
                n_messages,
                timezone=pytz.timezone('Europe/Madrid'),
                simple=simple
            ),
            message
        )
        await self.delete_message(message)

    async def _on_deactivate_tunnel(self, message: Message):
        self.tunnel_chat = None
        await self.send('Túnel cerrado.', message)

    @inline(False)
    async def _on_delete(self, message: Message):
        if message.replied_message:
            if not self.is_bot_mentioned(message):
                return

            if message.author.is_admin or message.replied_message.author.id == self.id:
                flanautils.do_later(flanautils.text_to_time(message.text).total_seconds(), self.delete_message, message.replied_message)
                await self.delete_message(message)
            elif message.chat.is_group:
                await self.send_negative(message)
        elif (
            (message.chat.is_private or self.is_bot_mentioned(message))
            and
            (n_messages := flanautils.text_to_number(message.text))
        ):
            if message.author.is_admin is False:
                await self.send_negative(message)
                return

            if n_messages <= 0:
                await self.delete_message(message)
                return

            await self.clear(n_messages + 1, message.chat)

    async def _on_hello(self, message: Message):
        if message.chat.is_private or self.is_bot_mentioned(message):
            await self.send_hello(message)

    async def _on_help(self, message: Message):
        now = datetime.timedelta(seconds=time.time())
        if (
            message.chat.is_group
            and
            not self.is_bot_mentioned(message)
            or
            self.help_calls.get(message.chat.id)
            and
            now - self.help_calls[message.chat.id] <= datetime.timedelta(minutes=1)
        ):
            return

        self.help_calls[message.chat.id] = now

        await self.send(
            '<b>Necesita ayuda:</b>\n'
            '<b>User:</b>\n'
            f'    <b>id:</b> <code>{message.author.id}</code>\n'
            f'    <b>name:</b> <code>{message.author.name}</code>\n'
            f'    <b>is_admin:<b> <code>{message.author.is_admin}</code>\n'
            f'    <b>is_bot:</b> <code>{message.author.is_bot}</code>\n'
            '\n'
            '<b>Chat:</b>\n'
            f'    <b>id:</b> <code>{message.chat.id}</code>\n'
            f'    <b>name:</b> <code>{message.chat.name}</code>\n'
            f'    <b>group_id:</b> <code>{message.chat.group_id}</code>\n'
            f'    <b>group_name:</b> <code>{message.chat.group_name}</code>',
            await self.owner_chat
        )
        await self.send('Se ha notificado a Flanagan. Se pondrá en contacto contigo cuando pueda.', message)

    async def _on_new_message_default(self, message: Message):
        if message.is_inline:
            await self._on_scraping(message)
        elif (
            (
                message.chat.is_group
                and
                not self.is_bot_mentioned(message)
                and
                not message.chat.config['auto_scraping']
                or
                not await self._on_scraping(message, scrape_replied=False)
            )
            and
            message.author.id != self.owner_id
            and
            (
                not message.replied_message
                or
                message.replied_message.author.id != self.id
                or
                not message.replied_message.medias
            )
            and
            (
                self.is_bot_mentioned(message)
                or
                message.chat.config['auto_insult']
                and
                random.random() < constants.INSULT_PROBABILITY
            )
            and
            (
                not self.tunnel_chat
                or
                self.tunnel_chat != message.chat
            )
        ):
            await self.send_insult(message)

    async def _on_ready(self):
        await super()._on_ready()
        flanautils.do_every(multibot_constants.CHECK_OLD_DATABASE_MESSAGES_EVERY_SECONDS, self.check_old_database_actions)
        for chat in Chat.find({
            'platform': self.platform.value,
            'config.ubereats': {"$exists": True, "$eq": True},
            'ubereats.cookies': {"$exists": True, "$ne": []}
        }):
            chat = await self.get_chat(chat.id)
            chat.pull_from_database(overwrite_fields=('_id', 'config', 'ubereats'))
            if (
                chat.ubereats['next_execution']
                and
                (delta_time := chat.ubereats['next_execution'] - datetime.datetime.now(datetime.timezone.utc)) > datetime.timedelta()
            ):
                flanautils.do_later(delta_time, self.start_ubereats, chat)
            else:
                await self.start_ubereats(chat)

    @inline(False)
    async def _on_recover_message(self, message: Message):
        if message.replied_message and message.replied_message.author.id == self.id:
            message_deleted_bot_action = BotAction.find_one({
                'platform': self.platform.value,
                'action': Action.MESSAGE_DELETED.value,
                'chat': message.chat.object_id,
                'affected_objects': message.replied_message.object_id
            })
        elif self.is_bot_mentioned(message):
            message_deleted_bot_action = BotAction.find_one({
                'platform': self.platform.value,
                'action': Action.MESSAGE_DELETED.value,
                'chat': message.chat.object_id,
                'date': {'$gt': datetime.datetime.now(datetime.timezone.utc) - constants.RECOVERY_DELETED_MESSAGE_BEFORE}
            }, sort_keys=(('date', pymongo.DESCENDING),))
        else:
            return

        if not message_deleted_bot_action:
            await self.send_error('No hay nada que recuperar.', message)
            return

        deleted_messages: list[Message] = []
        for affected_object_id in message_deleted_bot_action.affected_objects:
            if (affected_message := self.Message.find_one({'platform': self.platform.value, '_id': affected_object_id})).author.id != self.id:
                deleted_messages.append(affected_message)

        for deleted_message in deleted_messages:
            await self.send(deleted_message.text, message)

    @group
    @bot_mentioned
    async def _on_roles(self, message: Message):
        user_role_names = [role.name for role in await self.get_current_roles(message.author)]
        if not (options := await self._role_state_options(message, user_role_names)):
            return

        await self.send(
            f'<b>Roles de {message.author.name}:</b>',
            self.distribute_buttons(options, vertically=True),
            message,
            buttons_key=ButtonsGroup.ROLES,
            data={'user_id': message.author.id}
        )
        await self.delete_message(message)

    async def _on_roles_button_press(self, message: Message):
        await self.accept_button_event(message)
        if message.buttons_info.presser_user.id != message.data['user_id']:
            return

        role = await self.find_role(message.buttons_info.pressed_text[1:].strip(), message)
        user_role_names = [role.name for role in await self.get_current_roles(message.buttons_info.presser_user)]
        if role.name in user_role_names:
            await self.remove_role(message.buttons_info.presser_user, message, role)
            message.buttons_info.presser_user.roles.remove(role)
            user_role_names.remove(role.name)
        else:
            await self.add_role(message.buttons_info.presser_user, message, role)
            message.buttons_info.presser_user.roles.append(role)
            user_role_names.append(role.name)

        await self.edit(self.distribute_buttons(await self._role_state_options(message, user_role_names), vertically=True), message)

        message.buttons_info.presser_user.save()

    async def _on_tunnel_message(self, message: Message):
        if (
            not self.tunnel_chat
            or
            self._parse_callbacks(
                message.text,
                [
                    RegisteredCallback(..., (multibot_constants.KEYWORDS['activate'], constants.KEYWORDS['tunnel'])),
                    RegisteredCallback(..., (multibot_constants.KEYWORDS['deactivate'], constants.KEYWORDS['tunnel']))
                ]
            )
        ):
            return

        if message.chat == self.tunnel_chat:
            await self.send(f"<b>{message.author.name.split('#')[0]}:</b> {message.text}", await self.owner_chat)
        elif message.author.id == self.owner_id and message.chat.is_private:
            if message.text:
                await self.send(message.text, self.tunnel_chat)
            else:
                await self.send('No puedo enviar un mensaje sin texto.', message)

    @group
    @bot_mentioned
    async def _on_users(self, message: Message):
        if not (role_names := [role.name for role in await self.get_group_roles(message.chat.group_id)]):
            return

        try:
            role_names.remove('@everyone')
        except ValueError:
            pass

        user_names = [f'<@{user.id}>' for user in await self.find_users_by_roles([], message)]
        joined_user_names = ', '.join(user_names)
        bot_message = await self.send(
            f"<b>{len(user_names)} usuario{'' if len(user_names) == 1 else 's'}:</b>",
            message
        )
        await self.edit(
            f"<b>{len(user_names)} usuario{'' if len(user_names) == 1 else 's'}:</b>\n{joined_user_names}\n\n<b>Filtrar usuarios por roles:</b>",
            flanautils.chunks([f'❌ {role_name}' for role_name in role_names], 5),
            bot_message,
            buttons_key=ButtonsGroup.USERS
        )
        await self.delete_message(message)

    async def _on_users_button_press(self, message: Message):
        await self.accept_button_event(message)

        pressed_button = message.buttons_info.pressed_button
        pressed_button.is_checked = not pressed_button.is_checked
        pressed_button_role_name = message.buttons_info.pressed_text.split(maxsplit=1)[1]
        pressed_button.text = f"{'✔' if pressed_button.is_checked else '❌'} {pressed_button_role_name}"

        selected_role_names = [checked_button.text.split(maxsplit=1)[1] for checked_button in message.buttons_info.checked_buttons]
        user_names = [f'<@{user.id}>' for user in await self.find_users_by_roles(selected_role_names, message)]
        joined_user_names = ', '.join(user_names)
        await self.edit(
            f"<b>{len(user_names)} usuario{'' if len(user_names) == 1 else 's'}:</b>\n"
            f"{joined_user_names}\n\n"
            f"<b>Filtrar usuarios por roles:</b>",
            message.buttons_info.buttons,
            message
        )

    # -------------------------------------------------------- #
    # -------------------- PUBLIC METHODS -------------------- #
    # -------------------------------------------------------- #
    def check_old_database_actions(self):
        before_date = datetime.datetime.now(datetime.timezone.utc) - multibot_constants.DATABASE_MESSAGE_EXPIRATION_TIME
        BotAction.delete_many_raw({'platform': self.platform.value, 'date': {'$lte': before_date}})

    async def send_bye(self, chat: int | str | User | Chat | Message) -> multibot_constants.ORIGINAL_MESSAGE:
        chat = await self.get_chat(chat)
        return await self.send(random.choice((*constants.BYE_PHRASES, flanautils.CommonWords.random_time_greeting())), chat)

    async def send_hello(self, chat: int | str | User | Chat | Message) -> multibot_constants.ORIGINAL_MESSAGE:
        chat = await self.get_chat(chat)
        return await self.send(random.choice((*constants.HELLO_PHRASES, flanautils.CommonWords.random_time_greeting())), chat)

    async def send_insult(self, chat: int | str | User | Chat | Message) -> multibot_constants.ORIGINAL_MESSAGE | None:
        chat = await self.get_chat(chat)
        async with await self.typing(chat):
            await asyncio.sleep(random.randint(1, 3))
            return await self.send(random.choice(constants.INSULTS), chat)
