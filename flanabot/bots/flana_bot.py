__all__ = ['FlanaBot']

import asyncio
import datetime
import math
import random
import re
from abc import ABC
from typing import Iterable, Sequence

import flanaapis.geolocation.functions
import flanaapis.weather.functions
import flanautils
import plotly.graph_objects
import pymongo
from flanaapis import InstagramLoginError, MediaNotFoundError, Place, PlaceNotFoundError, WeatherEmoji, instagram, tiktok, twitter, youtube
from flanautils import Media, MediaType, NotFoundError, OrderedSet, Source, TimeUnits, TraceMetadata, return_if_first_empty
from multibot import Action, BadRoleError, BotAction, ButtonsGroup, MultiBot, RegisteredCallback, Role, SendError, User, admin, bot_mentioned, constants as multibot_constants, group, ignore_self_message, inline, reply

from flanabot import constants
from flanabot.models import Chat, Message, Punishment, WeatherChart


# ----------------------------------------------------------------------------------------------------- #
# --------------------------------------------- FLANA_BOT --------------------------------------------- #
# ----------------------------------------------------------------------------------------------------- #
class FlanaBot(MultiBot, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock = asyncio.Lock()

    # ----------------------------------------------------------- #
    # -------------------- PROTECTED METHODS -------------------- #
    # ----------------------------------------------------------- #
    def _add_handlers(self):
        super()._add_handlers()

        self.register(self._on_bye, multibot_constants.KEYWORDS['bye'])

        self.register(self._on_choose, constants.KEYWORDS['choose'], priority=2)
        self.register(self._on_choose, constants.KEYWORDS['random'], priority=2)
        self.register(self._on_choose, (constants.KEYWORDS['choose'], constants.KEYWORDS['random']), priority=2)

        self.register(self._on_config, multibot_constants.KEYWORDS['config'])
        self.register(self._on_config, (multibot_constants.KEYWORDS['show'], multibot_constants.KEYWORDS['config']))

        self.register(self._on_dice, constants.KEYWORDS['dice'])

        self.register(self._on_hello, multibot_constants.KEYWORDS['hello'])

        self.register(self._on_new_message_default, default=True)

        self.register(self._on_no_delete_original, (multibot_constants.KEYWORDS['negate'], multibot_constants.KEYWORDS['delete']))
        self.register(self._on_no_delete_original, (multibot_constants.KEYWORDS['negate'], multibot_constants.KEYWORDS['message']))
        self.register(self._on_no_delete_original, (multibot_constants.KEYWORDS['negate'], multibot_constants.KEYWORDS['delete'], multibot_constants.KEYWORDS['message']))
        self.register(self._on_no_delete_original, (multibot_constants.KEYWORDS['deactivate'], multibot_constants.KEYWORDS['delete'], multibot_constants.KEYWORDS['message']))

        self.register(self._on_poll, constants.KEYWORDS['poll'], priority=2)

        self.register(self._on_poll_multi, (constants.KEYWORDS['poll'], constants.KEYWORDS['multiple_answer']), priority=2)

        self.register(self._on_punish, constants.KEYWORDS['punish'])
        self.register(self._on_punish, (multibot_constants.KEYWORDS['deactivate'], constants.KEYWORDS['unpunish']))
        self.register(self._on_punish, (multibot_constants.KEYWORDS['deactivate'], multibot_constants.KEYWORDS['permission']))

        self.register(self._on_recover_message, multibot_constants.KEYWORDS['reset'])
        self.register(self._on_recover_message, (multibot_constants.KEYWORDS['reset'], multibot_constants.KEYWORDS['message']))

        self.register(self._on_roles, multibot_constants.KEYWORDS['permission'])
        self.register(self._on_roles, multibot_constants.KEYWORDS['role'])
        self.register(self._on_roles, (multibot_constants.KEYWORDS['permission'], multibot_constants.KEYWORDS['role']))
        self.register(self._on_roles, (multibot_constants.KEYWORDS['change'], multibot_constants.KEYWORDS['permission']))
        self.register(self._on_roles, (multibot_constants.KEYWORDS['activate'], multibot_constants.KEYWORDS['role']))
        self.register(self._on_roles, (multibot_constants.KEYWORDS['deactivate'], multibot_constants.KEYWORDS['role']))

        self.register(self._on_scraping, constants.KEYWORDS['scraping'])

        self.register(self._on_scraping_audio, multibot_constants.KEYWORDS['audio'])
        self.register(self._on_scraping_audio, (multibot_constants.KEYWORDS['audio'], constants.KEYWORDS['scraping']))

        self.register(self._on_song_info, constants.KEYWORDS['song_info'])

        self.register(self._on_stop_poll, multibot_constants.KEYWORDS['deactivate'])
        self.register(self._on_stop_poll, (multibot_constants.KEYWORDS['deactivate'], constants.KEYWORDS['poll']))
        self.register(self._on_stop_poll, multibot_constants.KEYWORDS['stop'])
        self.register(self._on_stop_poll, (multibot_constants.KEYWORDS['stop'], constants.KEYWORDS['poll']))

        self.register(self._on_unpunish, constants.KEYWORDS['unpunish'])
        self.register(self._on_unpunish, (multibot_constants.KEYWORDS['deactivate'], constants.KEYWORDS['punish']))
        self.register(self._on_unpunish, (multibot_constants.KEYWORDS['activate'], multibot_constants.KEYWORDS['permission']))

        self.register(self._on_weather_chart, constants.KEYWORDS['weather_chart'])
        self.register(self._on_weather_chart, (multibot_constants.KEYWORDS['show'], constants.KEYWORDS['weather_chart']))

        self.register_button(self._on_config_button_press, ButtonsGroup.CONFIG)
        self.register_button(self._on_poll_button_press, ButtonsGroup.POLL)
        self.register_button(self._on_roles_button_press, ButtonsGroup.ROLES)
        self.register_button(self._on_weather_button_press, ButtonsGroup.WEATHER)

    async def _changeable_roles(self, group_: int | str | Chat | Message) -> list[Role]:
        pass

    @admin(False)
    @group
    async def _check_message_flood(self, message: Message):
        if await self.is_punished(message.author, message.chat):
            return

        last_2s_messages = Message.find({
            'platform': self.platform.value,
            'author': message.author.object_id,
            'chat': message.chat.object_id,
            'date': {'$gte': datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=2)}
        })
        last_7s_messages = Message.find({
            'platform': self.platform.value,
            'author': message.author.object_id,
            'chat': message.chat.object_id,
            'date': {'$gte': datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=7)}
        })

        if len(last_2s_messages) >= constants.FLOOD_2s_LIMIT or len(last_7s_messages) >= constants.FLOOD_7s_LIMIT:
            punishment = Punishment.find_one({
                'platform': self.platform.value,
                'user_id': message.author.id,
                'group_id': message.chat.group_id
            })
            punishment_seconds = (getattr(punishment, 'level', 0) + 2) ** constants.PUNISHMENT_INCREMENT_EXPONENT
            try:
                await self.punish(message.author.id, message.chat.group_id, punishment_seconds, message)
            except BadRoleError as e:
                await self._manage_exceptions(e, message)
            else:
                await self.send(f'Castigado durante {TimeUnits(seconds=punishment_seconds).to_words()}.', message)

    def _distribute_buttons(self, texts: Sequence[str]) -> list[list[str]]:
        pass

    @staticmethod
    def _get_options(text: str, discarded_words: Iterable = ()) -> list[str]:
        options = (option for option in text.split() if not flanautils.cartesian_product_string_matching(option.lower(), discarded_words, min_ratio=multibot_constants.PARSE_CALLBACKS_MIN_RATIO_DEFAULT))
        text = ' '.join(options)

        conjunctions = [f' {conjunction} ' for conjunction in flanautils.CommonWords.get('conjunctions')]
        if any(char in text for char in (',', ';', *conjunctions)):
            conjunction_parts = [f'(?:[,;]*{conjunction}[,;]*)+' for conjunction in conjunctions]
            options = re.split(f"{'|'.join(conjunction_parts)}|[,;]+", text)
            return [option.strip() for option in options if option]
        else:
            return text.split()

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

    @staticmethod
    def _medias_sended_info(medias: Iterable[Media]) -> str:
        medias_count = {
            Source.TWITTER: {MediaType.IMAGE: 0, MediaType.AUDIO: 0, MediaType.GIF: 0, MediaType.VIDEO: 0, None: 0, MediaType.ERROR: 0},
            Source.INSTAGRAM: {MediaType.IMAGE: 0, MediaType.AUDIO: 0, MediaType.GIF: 0, MediaType.VIDEO: 0, None: 0, MediaType.ERROR: 0},
            Source.TIKTOK: {MediaType.IMAGE: 0, MediaType.AUDIO: 0, MediaType.GIF: 0, MediaType.VIDEO: 0, None: 0, MediaType.ERROR: 0},
            Source.REDDIT: {MediaType.IMAGE: 0, MediaType.AUDIO: 0, MediaType.GIF: 0, MediaType.VIDEO: 0, None: 0, MediaType.ERROR: 0},
            Source.YOUTUBE: {MediaType.IMAGE: 0, MediaType.AUDIO: 0, MediaType.GIF: 0, MediaType.VIDEO: 0, None: 0, MediaType.ERROR: 0},
            None: {MediaType.IMAGE: 0, MediaType.AUDIO: 0, MediaType.GIF: 0, MediaType.VIDEO: 0, None: 0, MediaType.ERROR: 0}
        }
        for media in medias:
            medias_count[media.source][media.type_] += 1

        medias_sended_info = []
        for source, media_type_count in medias_count.items():
            source_medias_sended_info = []
            for media_type, count in media_type_count.items():
                if count:
                    if count == 1:
                        type_text = {MediaType.IMAGE: 'imagen',
                                     MediaType.AUDIO: 'audio',
                                     MediaType.GIF: 'gif',
                                     MediaType.VIDEO: 'vídeo',
                                     None: 'cosa que no sé que tipo de archivo es',
                                     MediaType.ERROR: 'error'}[media_type]
                    else:
                        type_text = {MediaType.IMAGE: 'imágenes',
                                     MediaType.AUDIO: 'audios',
                                     MediaType.GIF: 'gifs',
                                     MediaType.VIDEO: 'vídeos',
                                     None: 'cosas que no sé que tipos de archivos son',
                                     MediaType.ERROR: 'errores'}[media_type]
                    source_medias_sended_info.append(f'{count} {type_text}')
            if source_medias_sended_info:
                medias_sended_info.append(f"{flanautils.join_last_separator(source_medias_sended_info, ', ', ' y ')} de {source.name if source else 'algún sitio'}")

        medias_sended_info_joined = flanautils.join_last_separator(medias_sended_info, ',\n', ' y\n')
        new_line = ' ' if len(medias_sended_info) == 1 else '\n'
        return f'{new_line}{medias_sended_info_joined}:'

    async def _punish(self, user: int | str | User, group_: int | str | Chat | Message, message: Message = None):
        pass

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

    async def _scrape_and_send(self, message: Message, audio_only=False) -> OrderedSet[Media]:
        kwargs = {}
        if self._parse_callbacks(message.text, [RegisteredCallback(..., [['sin'], ['timeout', 'limite']])]):
            kwargs['timeout_for_media'] = None
        if not (medias := await self._search_medias(message, audio_only, **kwargs)):
            return OrderedSet()

        sended_media_messages, _ = await self.send_medias(medias, message)
        sended_media_messages = OrderedSet(sended_media_messages)

        await self.send_inline_results(message)

        return sended_media_messages

    async def _scrape_send_and_delete(
        self,
        message: Message,
        audio_only=False,
        sended_media_messages: OrderedSet[Media] = None
    ) -> OrderedSet[Media]:
        if sended_media_messages is None:
            sended_media_messages = OrderedSet()

        sended_media_messages += await self._scrape_and_send(message, audio_only)

        if (
                sended_media_messages
                and
                message.chat.is_group
                and
                not message.replied_message
                and
                message.chat.config['delete_original']
        ):
            # noinspection PyTypeChecker
            BotAction(Action.MESSAGE_DELETED, message, affected_objects=[message, *sended_media_messages]).save()
            await self.delete_message(message)

        return sended_media_messages

    async def _search_medias(self, message: Message, audio_only=False, timeout_for_media: int | float = None) -> OrderedSet[Media]:
        medias = OrderedSet()

        tweet_ids = twitter.find_tweet_ids(message.text)
        instagram_ids = instagram.find_instagram_ids(message.text)
        tiktok_ids = await tiktok.find_tiktok_ids(message.text)
        tiktok_download_urls = tiktok.find_download_urls(message.text)
        youtube_ids = youtube.find_youtube_ids(message.text)

        if not any((tweet_ids, instagram_ids, tiktok_ids, tiktok_download_urls, youtube_ids)):
            return medias

        bot_state_message = await self.send(random.choice(constants.SCRAPING_PHRASES), message)

        gather_result = asyncio.gather(
            twitter.get_medias(tweet_ids, audio_only),
            instagram.get_medias(instagram_ids, audio_only),
            tiktok.get_medias(tiktok_ids, tiktok_download_urls, audio_only),
            youtube.get_medias(youtube_ids, audio_only, timeout_for_media),
            return_exceptions=True
        )

        await gather_result
        await self.delete_message(bot_state_message)

        medias, exceptions = flanautils.filter_exceptions(gather_result.result())
        await self._manage_exceptions(exceptions, message)

        return OrderedSet(*medias)

    async def _unpunish(self, user: int | str | User, group_: int | str | Chat | Message, message: Message = None):
        pass

    # ---------------------------------------------- #
    #                    HANDLERS                    #
    # ---------------------------------------------- #
    async def _on_bye(self, message: Message):
        if message.chat.is_private or self.is_bot_mentioned(message):
            await self.send_bye(message)

    async def _on_choose(self, message: Message):
        if message.chat.is_group and not self.is_bot_mentioned(message):
            return

        discarded_words = {
            *constants.KEYWORDS['choose'],
            *constants.KEYWORDS['random'],
            self.name.lower(), f'<@{self.id}>',
            'entre', 'between'
        }

        if options := self._get_options(message.text, discarded_words):
            for i in range(1, len(options) - 1):
                try:
                    n1 = flanautils.cast_number(options[i - 1])
                except ValueError:
                    try:
                        n1 = flanautils.words_to_numbers(options[i - 1], ignore_no_numbers=False)
                    except KeyError:
                        continue
                try:
                    n2 = flanautils.cast_number(options[i + 1])
                except ValueError:
                    try:
                        n2 = flanautils.words_to_numbers(options[i + 1], ignore_no_numbers=False)
                    except KeyError:
                        continue
                if options[i] in ('al', 'to'):
                    await self.send(random.randint(math.ceil(n1), math.floor(n2)), message)
                    return
            await self.send(random.choice(options), message)
        else:
            await self.send(random.choice(('¿Que elija el qué?', '¿Y las opciones?', '?', '🤔')), message)

    async def _on_config_button_press(self, message: Message):
        await self.accept_button_event(message)

        if message.buttons_info.presser_user.is_admin is False:
            return

        config = message.buttons_info.pressed_text.split()[1]
        message.chat.config[config] = not message.chat.config[config]
        message.buttons_info.pressed_button.text = f"{'✔' if message.chat.config[config] else '❌'} {config}"

        await self.edit(message.buttons_info.buttons, message)

    @group
    @bot_mentioned
    async def _on_config(self, message: Message):
        buttons_texts = [(f"{'✔' if v else '❌'} {k}", v) for k, v in message.chat.config.items()]
        await self.delete_message(message)
        await self.send('<b>Estos son los ajustes del chat:</b>\n\n', flanautils.chunks(buttons_texts, 3), message, buttons_key=ButtonsGroup.CONFIG)

    async def _on_dice(self, message: Message):
        if message.chat.is_group and not self.is_bot_mentioned(message):
            return

        if top_number := flanautils.sum_numbers_in_text(message.text):
            await self.send(random.randint(1, math.floor(top_number)), message)
        else:
            await self.send(random.choice(('¿De cuántas caras?', '¿Y el número?', '?', '🤔')), message)

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

    @ignore_self_message
    async def _on_new_message_raw(self, message: Message):
        await super()._on_new_message_raw(message)
        if message.chat.config['check_flood'] and message.chat.config['punish'] and not message.is_inline:
            async with self.lock:
                await self._check_message_flood(message)

    async def _on_no_delete_original(self, message: Message):
        if not await self._scrape_and_send(message):
            await self._on_recover_message(message)

    async def _on_poll(self, message: Message, is_multiple_answer=False):
        if message.chat.is_group and not self.is_bot_mentioned(message):
            return

        await self.delete_message(message)

        discarded_words = {*constants.KEYWORDS['poll'], *constants.KEYWORDS['multiple_answer'], self.name.lower(), f'<@{self.id}>'}
        if final_options := [f'{option[0].upper()}{option[1:]}' for option in self._get_options(message.text, discarded_words)]:
            await self.send(
                f"Encuesta {'multirespuesta ' if is_multiple_answer else ''}en curso...",
                self._distribute_buttons(final_options),
                message,
                buttons_key=ButtonsGroup.POLL,
                contents={'poll': {'is_active': True, 'is_multiple_answer': is_multiple_answer, 'votes': {option: [] for option in final_options}}}
            )
        else:
            await self.send(random.choice(('¿Y las opciones?', '?', '🤔')), message)

    async def _on_poll_multi(self, message: Message):
        await self._on_poll(message, is_multiple_answer=True)

    async def _on_poll_button_press(self, message: Message):
        await self.accept_button_event(message)
        if not message.contents['poll']['is_active']:
            return

        option_name = results[0] if (results := re.findall('(.*?) ➜.+', message.buttons_info.pressed_text)) else message.buttons_info.pressed_text
        selected_option_votes = message.contents['poll']['votes'][option_name]
        presser_id = message.buttons_info.presser_user.id
        presser_name = message.buttons_info.presser_user.name.split('#')[0]

        if [presser_id, presser_name] in selected_option_votes:
            selected_option_votes.remove([presser_id, presser_name])
        else:
            if not message.contents['poll']['is_multiple_answer']:
                for option_votes in message.contents['poll']['votes'].values():
                    try:
                        option_votes.remove([presser_id, presser_name])
                    except ValueError:
                        pass
                    else:
                        break
            selected_option_votes.append((presser_id, presser_name))

        if message.contents['poll']['is_multiple_answer']:
            total_votes = len({option_vote[0] for option_votes in message.contents['poll']['votes'].values() if option_votes for option_vote in option_votes})
        else:
            total_votes = sum(len(option_votes) for option_votes in message.contents['poll']['votes'].values())

        if total_votes:
            buttons = []
            for option, option_votes in message.contents['poll']['votes'].items():
                ratio = f'{len(option_votes)}/{total_votes}'
                names = f"({', '.join(option_vote[1] for option_vote in option_votes)})" if option_votes else ''
                buttons.append(f'{option} ➜ {ratio} {names}')
        else:
            buttons = list(message.contents['poll']['votes'].keys())

        await self.edit(self._distribute_buttons(buttons), message)

    @bot_mentioned
    @group
    @admin(send_negative=True)
    async def _on_punish(self, message: Message):
        if not message.chat.config['punish']:
            return

        for user in await self._find_users_to_punish(message):
            await self.punish(user, message, flanautils.words_to_time(message.text), message)

    async def _on_ready(self):
        await super()._on_ready()
        await flanautils.do_every(constants.CHECK_PUNISHMENTS_EVERY_SECONDS, Punishment.check_olds, self._unpunish, self.platform)

    @inline(False)
    async def _on_recover_message(self, message: Message):
        if message.replied_message:
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

        affected_object_ids = [affected_message_object_id for affected_message_object_id in message_deleted_bot_action.affected_objects]
        deleted_messages: list[Message] = [affected_message for affected_object_id in affected_object_ids if (affected_message := Message.find_one({'platform': self.platform.value, '_id': affected_object_id})).author.id != self.id]
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
            self._distribute_buttons(options),
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

        await self.edit(self._distribute_buttons(await self._role_state_options(message, user_role_names)), message)

        message.buttons_info.presser_user.save()

    async def _on_scraping(self, message: Message, audio_only=False) -> OrderedSet[Media]:
        sended_media_messages = OrderedSet()

        if message.replied_message:
            sended_media_messages += await self._scrape_and_send(message.replied_message, audio_only)

        return await self._scrape_send_and_delete(message, audio_only, sended_media_messages)

    async def _on_scraping_audio(self, message: Message) -> OrderedSet[Media]:
        return await self._on_scraping(message, audio_only=True)

    @reply
    async def _on_song_info(self, message: Message):
        song_infos = message.replied_message.song_infos if message.replied_message else []

        if song_infos:
            for song_info in song_infos:
                await self.send_song_info(song_info, message)
        elif message.chat.is_private or self.is_bot_mentioned(message):
            await self._manage_exceptions(SendError('No hay información musical en ese mensaje.'), message)

    async def _on_stop_poll(self, message: Message):
        if poll_message := message.replied_message:
            if poll_message.contents.get('poll') is None:
                return
        elif (
                (message.chat.is_private or self.is_bot_mentioned(message))
                and
                flanautils.cartesian_product_string_matching(message.text, constants.KEYWORDS['poll'], min_ratio=multibot_constants.PARSE_CALLBACKS_MIN_RATIO_DEFAULT)
                and
                (poll_message := Message.find_one({'contents.poll.is_active': True}, sort_keys=(('date', pymongo.DESCENDING),)))
        ):
            poll_message = await self.get_message(poll_message.chat.id, poll_message.id)
        else:
            return

        winners = []
        max_votes = 1
        for option, votes in poll_message.contents['poll']['votes'].items():
            if len(votes) > max_votes:
                winners = [option]
                max_votes = len(votes)
            elif len(votes) == max_votes:
                winners.append(option)

        match winners:
            case [_, _, *_]:
                winners = [f'<b>{winner}</b>' for winner in winners]
                text = f"Encuesta finalizada. Los ganadores son: {flanautils.join_last_separator(winners, ', ', ' y ')}."
            case [winner]:
                text = f'Encuesta finalizada. Ganador: <b>{winner}</b>.'
            case _:
                text = 'Encuesta finalizada.'

        poll_message.contents['poll']['is_active'] = False

        await self.edit(text, poll_message)
        if not message.replied_message:
            await self.send(text, reply_to=poll_message)

    @group
    @bot_mentioned
    @admin(send_negative=True)
    async def _on_unpunish(self, message: Message):
        if not message.chat.config['punish']:
            return

        for user in await self._find_users_to_punish(message):
            await self.unpunish(user, message, message)

    async def _on_weather_button_press(self, message: Message):
        await self.accept_button_event(message)

        match message.buttons_info.pressed_text:
            case WeatherEmoji.ZOOM_IN.value:
                message.weather_chart.zoom_in()
            case WeatherEmoji.ZOOM_OUT.value:
                message.weather_chart.zoom_out()
            case WeatherEmoji.LEFT.value:
                message.weather_chart.move_left()
            case WeatherEmoji.RIGHT.value:
                message.weather_chart.move_right()
            case WeatherEmoji.PRECIPITATION_VOLUME.value:
                message.weather_chart.trace_metadatas['rain_volume'].show = not message.weather_chart.trace_metadatas['rain_volume'].show
                message.weather_chart.trace_metadatas['snow_volume'].show = not message.weather_chart.trace_metadatas['snow_volume'].show
            case emoji if emoji in WeatherEmoji.values:
                trace_metadata_name = WeatherEmoji(emoji).name.lower()
                message.weather_chart.trace_metadatas[trace_metadata_name].show = not message.weather_chart.trace_metadatas[trace_metadata_name].show
            case _:
                return

        message.weather_chart.apply_zoom()
        message.weather_chart.draw()

        image_bytes = message.weather_chart.to_image()
        await self.edit(Media(image_bytes, MediaType.IMAGE, 'jpg'), message)

    async def _on_weather_chart(self, message: Message):
        bot_state_message: Message | None = None
        if message.is_inline:
            show_progress_state = False
        elif message.chat.is_group and not self.is_bot_mentioned(message):
            if message.chat.config['weather_chart']:
                if BotAction.find_one({'action': Action.AUTO_WEATHER_CHART.value, 'chat': message.chat.object_id, 'date': {'$gt': datetime.datetime.now(datetime.timezone.utc) - constants.AUTO_WEATHER_EVERY}}):
                    return
                show_progress_state = False
            else:
                return
        else:
            show_progress_state = True

        possible_mentioned_ids = []
        for user in message.mentions:
            possible_mentioned_ids.append(user.name.lower())
            possible_mentioned_ids.append(user.name.split('#')[0].lower())
            possible_mentioned_ids.append(str(user.id))

        if roles := await self.get_group_roles(message):
            for role in roles:
                possible_mentioned_ids.append(str(role.id))

        original_text_words = flanautils.remove_accents(message.text.lower())
        original_text_words = original_text_words.replace(',', ' ').replace(';', ' ').replace('-', ' -')
        original_text_words = flanautils.translate(
            original_text_words,
            {symbol: None for symbol in set(flanautils.SYMBOLS) - {'-', '.'}}
        ).split()
        # noinspection PyTypeChecker
        place_words = (
                OrderedSet(original_text_words)
                - flanautils.cartesian_product_string_matching(original_text_words, multibot_constants.KEYWORDS['show'], min_ratio=0.85).keys()
                - flanautils.cartesian_product_string_matching(original_text_words, constants.KEYWORDS['weather_chart'], min_ratio=0.85).keys()
                - flanautils.cartesian_product_string_matching(original_text_words, multibot_constants.KEYWORDS['date'], min_ratio=0.85).keys()
                - flanautils.cartesian_product_string_matching(original_text_words, multibot_constants.KEYWORDS['thanks'], min_ratio=0.85).keys()
                - possible_mentioned_ids
                - flanautils.CommonWords.get()
        )
        if not place_words:
            if not message.is_inline:
                await self.send_error(random.choice(('¿Tiempo dónde?', 'Indica el sitio.', 'Y el sitio?', 'y el sitio? me lo invento?')), message)
            return

        if 'calle' in original_text_words:
            place_words.insert(0, 'calle')
        place_query = ' '.join(place_words)
        if len(place_query) >= constants.MAX_PLACE_QUERY_LENGTH:
            if show_progress_state:
                await self.send_error(Media(str(flanautils.resolve_path('resources/mucho_texto.png')), MediaType.IMAGE, 'jpg', Source.LOCAL), message, send_as_file=False)
            return
        if show_progress_state:
            bot_state_message = await self.send(f'Buscando "{place_query}" en el mapa 🧐...', message)

        result: str | Place | None = None
        async for result in flanaapis.geolocation.functions.find_place_showing_progress(place_query):
            if isinstance(result, str) and bot_state_message:
                await self.edit(result, bot_state_message)

        place: Place = result
        if not place:
            if bot_state_message:
                await self.delete_message(bot_state_message)
                await self._manage_exceptions(PlaceNotFoundError(place_query), message)
            return

        if bot_state_message:
            bot_state_message = await self.edit(f'Obteniendo datos del tiempo para "{place_query}"...', bot_state_message)
        current_weather, day_weathers = await flanaapis.weather.functions.get_day_weathers_by_place(place)

        if bot_state_message:
            bot_state_message = await self.edit('Creando gráficas del tiempo...', bot_state_message)

        weather_chart = WeatherChart(
            _font={'size': 30},
            _title={
                'text': place.name[:40].strip(' ,-'),
                'xref': 'paper',
                'yref': 'paper',
                'xanchor': 'left',
                'yanchor': 'top',
                'x': 0.025,
                'y': 0.975,
                'font': {
                    'size': 50,
                    'family': 'open sans'
                }
            },
            _legend={'x': 0.99, 'y': 0.99, 'xanchor': 'right', 'yanchor': 'top', 'bgcolor': 'rgba(0,0,0,0)'},
            _margin={'l': 20, 'r': 20, 't': 20, 'b': 20},
            trace_metadatas={
                'temperature': TraceMetadata(name='temperature', group='temperature', legend='Temperatura', show=False, color='#ff8400', default_min=0, default_max=40, y_tick_suffix=' ºC', y_axis_width=130),
                'temperature_feel': TraceMetadata(name='temperature_feel', group='temperature', legend='Sensación de temperatura', show=True, color='red', default_min=0, default_max=40, y_tick_suffix=' ºC', y_axis_width=130),
                'clouds': TraceMetadata(name='clouds', legend='Nubes', show=False, color='#86abe3', default_min=-100, default_max=100, y_tick_suffix=' %', hide_y_ticks_if='{tick} < 0'),
                'visibility': TraceMetadata(name='visibility', legend='Visibilidad', show=False, color='#c99a34', default_min=0, default_max='{max_y_data} * 2', y_tick_suffix=' km', y_delta_tick=2, hide_y_ticks_if='{tick} > {max_y_data}'),
                'uvi': TraceMetadata(name='uvi', legend='UVI', show=False, color='#ffd000', default_min=-12, default_max=12, hide_y_ticks_if='{tick} < 0', y_delta_tick=1, y_axis_width=75),
                'humidity': TraceMetadata(name='humidity', legend='Humedad', show=False, color='#2baab5', default_min=0, default_max=100, y_tick_suffix=' %'),
                'precipitation_probability': TraceMetadata(name='precipitation_probability', legend='Probabilidad de precipitaciones', show=True, color='#0033ff', default_min=-100, default_max=100, y_tick_suffix=' %', hide_y_ticks_if='{tick} < 0'),
                'rain_volume': TraceMetadata(plotly.graph_objects.Histogram, name='rain_volume', group='precipitation', legend='Volumen de lluvia', show=True, color='#34a4eb', opacity=0.3, default_min=-10, default_max=10, y_tick_suffix=' mm', y_delta_tick=1, hide_y_ticks_if='{tick} < 0', y_axis_width=130),
                'snow_volume': TraceMetadata(plotly.graph_objects.Histogram, name='snow_volume', group='precipitation', legend='Volumen de nieve', show=True, color='#34a4eb', opacity=0.8, pattern={'shape': '.', 'fgcolor': '#ffffff', 'bgcolor': '#b0d6f3', 'solidity': 0.5, 'size': 14}, default_min=-10, default_max=10, y_tick_suffix=' mm', y_delta_tick=1, hide_y_ticks_if='{tick} < 0', y_axis_width=130),
                'pressure': TraceMetadata(name='pressure', legend='Presión', show=False, color='#31a339', default_min=1013.25 - 90, default_max=1013.25 + 90, y_tick_suffix=' hPa', y_axis_width=225),
                'wind_speed': TraceMetadata(name='wind_speed', legend='Velocidad del viento', show=False, color='#d8abff', default_min=-120, default_max=120, y_tick_suffix=' km/h', hide_y_ticks_if='{tick} < 0', y_axis_width=165)
            },
            x_data=[instant_weather.date_time for day_weather in day_weathers for instant_weather in day_weather.instant_weathers],
            all_y_data=[],
            current_weather=current_weather,
            day_weathers=day_weathers,
            timezone=(timezone := next(iter(day_weathers)).timezone),
            place=place,
            view_position=datetime.datetime.now(timezone)
        )

        weather_chart.apply_zoom()
        weather_chart.draw()
        if not (image_bytes := weather_chart.to_image()):
            if bot_state_message:
                await self.delete_message(bot_state_message)
            raise NotFoundError('No hay suficientes datos del tiempo.')

        if bot_state_message:
            bot_state_message = await self.edit('Enviando...', bot_state_message)
        bot_message: Message = await self.send(
            Media(image_bytes, MediaType.IMAGE, 'jpg'),
            [
                [WeatherEmoji.ZOOM_IN.value, WeatherEmoji.ZOOM_OUT.value, WeatherEmoji.LEFT.value, WeatherEmoji.RIGHT.value],
                [WeatherEmoji.TEMPERATURE.value, WeatherEmoji.TEMPERATURE_FEEL.value, WeatherEmoji.CLOUDS.value, WeatherEmoji.VISIBILITY.value, WeatherEmoji.UVI.value],
                [WeatherEmoji.HUMIDITY.value, WeatherEmoji.PRECIPITATION_PROBABILITY.value, WeatherEmoji.PRECIPITATION_VOLUME.value, WeatherEmoji.PRESSURE.value, WeatherEmoji.WIND_SPEED.value]
            ],
            message,
            buttons_key=ButtonsGroup.WEATHER,
            send_as_file=False
        )
        await self.send_inline_results(message)

        if bot_state_message:
            await self.delete_message(bot_state_message)

        if bot_message:
            bot_message.weather_chart = weather_chart
            bot_message.save()
            if not self.is_bot_mentioned(message):
                # noinspection PyTypeChecker
                BotAction(Action.AUTO_WEATHER_CHART, message, affected_objects=[bot_message]).save()

    # -------------------------------------------------------- #
    # -------------------- PUBLIC METHODS -------------------- #
    # -------------------------------------------------------- #
    async def is_punished(self, user: int | str | User, group_: int | str | Chat | Message) -> bool:
        pass

    async def punish(self, user: int | str | User, group_: int | str | Chat | Message, time: int | datetime.timedelta = None, message: Message = None):
        # noinspection PyTypeChecker
        punishment = Punishment(self.platform, self.get_user_id(user), self.get_group_id(group_), time)
        await punishment.apply(self._punish, self._unpunish, message)

    async def send_bye(self, message: Message) -> multibot_constants.ORIGINAL_MESSAGE:
        return await self.send(random.choice((*constants.BYE_PHRASES, flanautils.CommonWords.random_time_greeting())), message)

    async def send_hello(self, message: Message) -> multibot_constants.ORIGINAL_MESSAGE:
        return await self.send(random.choice((*constants.HELLO_PHRASES, flanautils.CommonWords.random_time_greeting())), message)

    async def send_insult(self, message: Message) -> multibot_constants.ORIGINAL_MESSAGE | None:
        await self.typing_delay(message)
        return await self.send(random.choice(constants.INSULTS), message)

    async def send_medias(self, medias: OrderedSet[Media], message: Message, send_song_info=False) -> tuple[list[Message], int]:
        sended_media_messages = []
        fails = 0
        bot_state_message: Message | None = None
        sended_info_message: Message | None = None

        if not message.is_inline:
            bot_state_message: Message = await self.send('Enviando...', message)

        if message.chat.is_group:
            sended_info_message = await self.send(f"{message.author.name.split('#')[0]} compartió{self._medias_sended_info(medias)}", message)

        for media in medias:
            if not media.content:
                fails += 1
                continue

            if media.song_info:
                message.song_infos.add(media.song_info)
                message.save()

            if bot_message := await self.send(media, message):
                sended_media_messages.append(bot_message)
                if media.song_info and bot_message:
                    bot_message.song_infos.add(media.song_info)
                    bot_message.save()
            else:
                fails += 1

            if send_song_info and media.song_info:
                await self.send_song_info(media.song_info, message)

        if fails and sended_info_message:
            if fails == len(medias):
                await self.delete_message(sended_info_message)
        if bot_state_message:
            await self.delete_message(bot_state_message)

        return sended_media_messages, fails

    @return_if_first_empty(exclude_self_types='FlanaBot', globals_=globals())
    async def send_song_info(self, song_info: Media, message: Message):
        attributes = (
            f'Título: {song_info.title}\n' if song_info.title else '',
            f'Autor: {song_info.author}\n' if song_info.author else '',
            f'Álbum: {song_info.album}\n' if song_info.album else '',
            f'Previa:'
        )
        await self.send(''.join(attributes), message)
        if song_info:
            await self.send(song_info, message)

    async def unpunish(self, user: int | str | User, group_: int | str | Chat | Message, message: Message = None):
        # noinspection PyTypeChecker
        punishment = Punishment(self.platform, self.get_user_id(user), self.get_group_id(group_))
        await punishment.remove(self._unpunish, message)
