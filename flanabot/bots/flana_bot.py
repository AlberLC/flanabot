__all__ = ['FlanaBot']

import datetime
import random
from abc import ABC
from typing import Iterable

import flanautils
import pymongo
from flanaapis import InstagramLoginError, MediaNotFoundError, PlaceNotFoundError
from flanautils import return_if_first_empty
from multibot import BadRoleError, LimitError, MultiBot, Role, bot_mentioned, constants as multibot_constants, group, inline

from flanabot import constants
from flanabot.bots.connect_4_bot import Connect4Bot
from flanabot.bots.penalty_bot import PenaltyBot
from flanabot.bots.poll_bot import PollBot
from flanabot.bots.scraper_bot import ScraperBot
from flanabot.bots.weather_bot import WeatherBot
from flanabot.models import Action, BotAction, ButtonsGroup, Chat, Message


# ----------------------------------------------------------------------------------------------------- #
# --------------------------------------------- FLANA_BOT --------------------------------------------- #
# ----------------------------------------------------------------------------------------------------- #
class FlanaBot(Connect4Bot, PenaltyBot, PollBot, ScraperBot, WeatherBot, MultiBot, ABC):
    Chat = Chat
    Message = Message

    # ----------------------------------------------------------- #
    # -------------------- PROTECTED METHODS -------------------- #
    # ----------------------------------------------------------- #
    def _add_handlers(self):
        super()._add_handlers()

        self.register(self._on_bye, multibot_constants.KEYWORDS['bye'])

        self.register(self._on_config, multibot_constants.KEYWORDS['config'])
        self.register(self._on_config, (multibot_constants.KEYWORDS['show'], multibot_constants.KEYWORDS['config']))

        self.register(self._on_delete, multibot_constants.KEYWORDS['delete'])
        self.register(self._on_delete, (multibot_constants.KEYWORDS['delete'], multibot_constants.KEYWORDS['message']))

        self.register(self._on_hello, multibot_constants.KEYWORDS['hello'])

        self.register(self._on_new_message_default, default=True)

        self.register(self._on_recover_message, multibot_constants.KEYWORDS['reset'])
        self.register(self._on_recover_message, (multibot_constants.KEYWORDS['reset'], multibot_constants.KEYWORDS['message']))

        self.register(self._on_roles, multibot_constants.KEYWORDS['permission'])
        self.register(self._on_roles, multibot_constants.KEYWORDS['role'])
        self.register(self._on_roles, (multibot_constants.KEYWORDS['permission'], multibot_constants.KEYWORDS['role']))
        self.register(self._on_roles, (multibot_constants.KEYWORDS['change'], multibot_constants.KEYWORDS['permission']))
        self.register(self._on_roles, (multibot_constants.KEYWORDS['activate'], multibot_constants.KEYWORDS['role']))
        self.register(self._on_roles, (multibot_constants.KEYWORDS['deactivate'], multibot_constants.KEYWORDS['role']))

        self.register(self._on_users, multibot_constants.KEYWORDS['user'])

        self.register_button(self._on_config_button_press, ButtonsGroup.CONFIG)
        self.register_button(self._on_roles_button_press, ButtonsGroup.ROLES)
        self.register_button(self._on_users_button_press, ButtonsGroup.USERS)

    async def _changeable_roles(self, group_: int | str | Chat | Message) -> list[Role]:
        pass

    @return_if_first_empty(exclude_self_types='FlanaBot', globals_=globals())
    async def _manage_exceptions(self, exceptions: BaseException | Iterable[BaseException], context: Chat | Message):
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
                await super()._manage_exceptions(e, context)

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
    async def _on_bye(self, message: Message):
        if message.chat.is_private or self.is_bot_mentioned(message):
            await self.send_bye(message)

    @group
    @bot_mentioned
    async def _on_config(self, message: Message):
        if not message.chat.config:
            return

        buttons_texts = [(f"{'✔' if v else '❌'} {k}", v) for k, v in message.chat.config.items()]
        await self.delete_message(message)
        await self.send('<b>Estos son los ajustes del chat:</b>\n\n', flanautils.chunks(buttons_texts, 3), message, buttons_key=ButtonsGroup.CONFIG)

    async def _on_config_button_press(self, message: Message):
        await self.accept_button_event(message)

        if message.buttons_info.presser_user.is_admin is False:
            return

        config = message.buttons_info.pressed_text.split()[1]
        message.chat.config[config] = not message.chat.config[config]
        message.buttons_info.pressed_button.text = f"{'✔' if message.chat.config[config] else '❌'} {config}"

        await self.edit(message.buttons_info.buttons, message)

    @inline(False)
    async def _on_delete(self, message: Message):
        if message.replied_message:
            if message.replied_message.author.id == self.id:
                await self.delete_message(message.replied_message)
                if message.chat.is_group:
                    await self.delete_message(message)
            elif message.chat.is_group and self.is_bot_mentioned(message):
                await self.send_negative(message)
        elif message.chat.is_group and self.is_bot_mentioned(message) and (n_messages := flanautils.sum_numbers_in_text(message.text)):
            if not message.author.is_admin:
                await self.send_negative(message)
                return

            if n_messages <= 0:
                await self._manage_exceptions(ValueError(), message)
                return

            try:
                await self.clear(n_messages, message.chat)
            except LimitError as e:
                await self._manage_exceptions(e, message)

    async def _on_hello(self, message: Message):
        if message.chat.is_private or self.is_bot_mentioned(message):
            await self.send_hello(message)

    async def _on_new_message_default(self, message: Message):
        if message.is_inline:
            await self._scrape_and_send(message)
        elif (
                (
                        message.chat.is_group
                        and
                        not self.is_bot_mentioned(message)
                        and
                        not message.chat.config['scraping']
                        or
                        not await self._scrape_send_and_delete(message)
                )
                and
                (
                        message.author.id != self.owner_id
                        and
                        (
                                not message.replied_message
                                or
                                message.replied_message.author.id != self.id
                                or
                                not message.replied_message.contents.get('media')
                        )
                        and
                        (
                                self.is_bot_mentioned(message)
                                or
                                (
                                        message.chat.config['insult']
                                        and
                                        random.random() < constants.INSULT_PROBABILITY
                                )
                        )
                )
        ):
            await self.send_insult(message)

    @inline(False)
    async def _on_recover_message(self, message: Message):
        if message.replied_message and message.replied_message.author.id == self.id:
            message_deleted_bot_action = BotAction.find_one({'action': Action.MESSAGE_DELETED.value, 'chat': message.chat.object_id, 'affected_objects': message.replied_message.object_id})
        elif self.is_bot_mentioned(message):
            message_deleted_bot_action = BotAction.find_one({
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

        await self.delete_message(message)
        await self.send(
            f'<b>Roles de {message.author.name}:</b>',
            self.distribute_buttons(options, vertically=True),
            message,
            buttons_key=ButtonsGroup.ROLES,
            contents={'user_id': message.author.id}
        )

    async def _on_roles_button_press(self, message: Message):
        await self.accept_button_event(message)
        if message.buttons_info.presser_user.id != message.contents['user_id']:
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

    @group
    @bot_mentioned
    async def _on_users(self, message: Message):
        role_names = [role.name for role in await self.get_group_roles(message.chat.group_id)]
        role_names.remove('@everyone')

        user_names = [f'<@{user.id}>' for user in await self.find_users_by_roles([], message)]
        joined_user_names = ', '.join(user_names)
        await self.delete_message(message)
        bot_message = await self.send(
            f"<b>{len(user_names)} usuario{'' if len(user_names) == 1 else 's'}:</b>",
            flanautils.chunks([f'❌ {role_name}' for role_name in role_names], 5),
            message,
            buttons_key=ButtonsGroup.USERS
        )
        await self.edit(f"<b>{len(user_names)} usuario{'' if len(user_names) == 1 else 's'}:</b>\n{joined_user_names}\n\n<b>Filtrar usuarios por roles:</b>", bot_message)

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
    @classmethod
    async def clear_old_database_items(cls):
        await super().clear_old_database_items()
        before_date = datetime.datetime.now(datetime.timezone.utc) - multibot_constants.MESSAGE_EXPIRATION_TIME
        BotAction.collection.delete_many({'date': {'$lte': before_date}})

    async def send_bye(self, message: Message) -> multibot_constants.ORIGINAL_MESSAGE:
        return await self.send(random.choice((*constants.BYE_PHRASES, flanautils.CommonWords.random_time_greeting())), message)

    async def send_hello(self, message: Message) -> multibot_constants.ORIGINAL_MESSAGE:
        return await self.send(random.choice((*constants.HELLO_PHRASES, flanautils.CommonWords.random_time_greeting())), message)

    async def send_insult(self, message: Message) -> multibot_constants.ORIGINAL_MESSAGE | None:
        await self.typing_delay(message)
        return await self.send(random.choice(constants.INSULTS), message)
