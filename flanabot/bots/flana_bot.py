import asyncio
import datetime
import itertools
import pprint
import random
import time as time_module
from abc import ABC
from asyncio import Future
from typing import Iterable, Iterator, Type

import flanaapis.geolocation.functions
import flanaapis.weather.functions
import flanautils
import plotly.graph_objects
from flanaapis import InstagramLoginError, MediaNotFoundError, Place, PlaceNotFoundError, WeatherEmoji, instagram, tiktok, twitter
from flanautils import Media, MediaType, NotFoundError, OrderedSet, Source, TimeUnits, TraceMetadata, return_if_first_empty
from multibot import Action, BotAction, MultiBot, SendError, admin, bot_mentioned, constants as multibot_constants, group, ignore_self_message, inline, reply

from flanabot import constants
from flanabot.exceptions import BadRoleError, UserDisconnectedError
from flanabot.models.chat import Chat
from flanabot.models.message import Message
from flanabot.models.punishments import Mute, Punishment, PunishmentBase
from flanabot.models.weather_chart import WeatherChart


# ----------------------------------------------------------------------------------------------------- #
# --------------------------------------------- FLANA_BOT --------------------------------------------- #
# ----------------------------------------------------------------------------------------------------- #


class FlanaBot(MultiBot, ABC):
    # ----------------------------------------------------------- #
    # -------------------- PROTECTED METHODS -------------------- #
    # ----------------------------------------------------------- #
    def _add_handlers(self):
        super()._add_handlers()

        self.register(self._on_bye, constants.KEYWORDS['bye'])

        self.register(self._on_config_list_show, constants.KEYWORDS['config'])
        self.register(self._on_config_list_show, constants.KEYWORDS['help'])
        self.register(self._on_config_list_show, (constants.KEYWORDS['show'], constants.KEYWORDS['config']))
        self.register(self._on_config_list_show, (constants.KEYWORDS['help'], constants.KEYWORDS['config']))
        self.register(self._on_config_list_show, (constants.KEYWORDS['show'], constants.KEYWORDS['help']))
        self.register(self._on_config_list_show, (constants.KEYWORDS['show'], constants.KEYWORDS['help'], constants.KEYWORDS['config']))

        self.register(self._on_covid_chart, constants.KEYWORDS['covid_chart'])

        self.register(self._on_currency_chart, constants.KEYWORDS['currency_chart'])
        self.register(self._on_currency_chart, (constants.KEYWORDS['show'], constants.KEYWORDS['currency_chart']))

        self.register(self._on_currency_chart_config_activate, (constants.KEYWORDS['activate'], constants.KEYWORDS['currency_chart']))
        self.register(self._on_currency_chart_config_activate, (constants.KEYWORDS['activate'], constants.KEYWORDS['currency_chart'], constants.KEYWORDS['config']))

        self.register(self._on_currency_chart_config_change, (constants.KEYWORDS['change'], constants.KEYWORDS['currency_chart']))
        self.register(self._on_currency_chart_config_change, (constants.KEYWORDS['change'], constants.KEYWORDS['currency_chart'], constants.KEYWORDS['config']))

        self.register(self._on_currency_chart_config_deactivate, (constants.KEYWORDS['deactivate'], constants.KEYWORDS['currency_chart']))
        self.register(self._on_currency_chart_config_deactivate, (constants.KEYWORDS['deactivate'], constants.KEYWORDS['currency_chart'], constants.KEYWORDS['config']))

        self.register(self._on_currency_chart_config_show, (constants.KEYWORDS['currency_chart'], constants.KEYWORDS['config']))
        self.register(self._on_currency_chart_config_show, (constants.KEYWORDS['show'], constants.KEYWORDS['currency_chart'], constants.KEYWORDS['config']))

        self.register(self._on_delete_original_config_activate, (constants.KEYWORDS['activate'], multibot_constants.KEYWORDS['delete']))
        self.register(self._on_delete_original_config_activate, (constants.KEYWORDS['activate'], multibot_constants.KEYWORDS['delete'], multibot_constants.KEYWORDS['message']))
        self.register(self._on_delete_original_config_activate, (constants.KEYWORDS['activate'], multibot_constants.KEYWORDS['delete'], constants.KEYWORDS['config']))
        self.register(self._on_delete_original_config_activate, (constants.KEYWORDS['activate'], multibot_constants.KEYWORDS['delete'], multibot_constants.KEYWORDS['message'], constants.KEYWORDS['config']))

        self.register(self._on_delete_original_config_change, (constants.KEYWORDS['change'], multibot_constants.KEYWORDS['delete']))
        self.register(self._on_delete_original_config_change, (constants.KEYWORDS['change'], multibot_constants.KEYWORDS['delete'], multibot_constants.KEYWORDS['message']))
        self.register(self._on_delete_original_config_change, (constants.KEYWORDS['change'], multibot_constants.KEYWORDS['delete'], constants.KEYWORDS['config']))
        self.register(self._on_delete_original_config_change, (constants.KEYWORDS['change'], multibot_constants.KEYWORDS['delete'], multibot_constants.KEYWORDS['message'], constants.KEYWORDS['config']))

        self.register(self._on_delete_original_config_deactivate, (constants.KEYWORDS['deactivate'], multibot_constants.KEYWORDS['delete']))
        self.register(self._on_delete_original_config_deactivate, (constants.KEYWORDS['deactivate'], multibot_constants.KEYWORDS['delete'], multibot_constants.KEYWORDS['message']))
        self.register(self._on_delete_original_config_deactivate, (constants.KEYWORDS['deactivate'], multibot_constants.KEYWORDS['delete'], constants.KEYWORDS['config']))
        self.register(self._on_delete_original_config_deactivate, (constants.KEYWORDS['deactivate'], multibot_constants.KEYWORDS['delete'], multibot_constants.KEYWORDS['message'], constants.KEYWORDS['config']))

        self.register(self._on_delete_original_config_show, (constants.KEYWORDS['show'], multibot_constants.KEYWORDS['delete']))
        self.register(self._on_delete_original_config_show, (multibot_constants.KEYWORDS['delete'], constants.KEYWORDS['config']))
        self.register(self._on_delete_original_config_show, (constants.KEYWORDS['show'], multibot_constants.KEYWORDS['delete'], multibot_constants.KEYWORDS['message']))
        self.register(self._on_delete_original_config_show, (constants.KEYWORDS['show'], multibot_constants.KEYWORDS['delete'], constants.KEYWORDS['config']))
        self.register(self._on_delete_original_config_show, (multibot_constants.KEYWORDS['delete'], multibot_constants.KEYWORDS['message'], constants.KEYWORDS['config']))
        self.register(self._on_delete_original_config_show, (constants.KEYWORDS['show'], multibot_constants.KEYWORDS['delete'], multibot_constants.KEYWORDS['message'], constants.KEYWORDS['config']))

        self.register(self._on_hello, constants.KEYWORDS['hello'])

        self.register(self._on_mute, constants.KEYWORDS['mute'])
        self.register(self._on_mute, (('haz', 'se'), constants.KEYWORDS['mute']))
        self.register(self._on_mute, (constants.KEYWORDS['deactivate'], constants.KEYWORDS['unmute']))
        self.register(self._on_mute, (constants.KEYWORDS['deactivate'], constants.KEYWORDS['sound']))

        self.register(self._on_new_message_default, default=True)

        self.register(self._on_no_delete_original, (constants.KEYWORDS['negate'], multibot_constants.KEYWORDS['delete']))
        self.register(self._on_no_delete_original, (constants.KEYWORDS['negate'], multibot_constants.KEYWORDS['message']))
        self.register(self._on_no_delete_original, (constants.KEYWORDS['negate'], multibot_constants.KEYWORDS['delete'], multibot_constants.KEYWORDS['message']))
        self.register(self._on_no_delete_original, (constants.KEYWORDS['deactivate'], multibot_constants.KEYWORDS['delete'], multibot_constants.KEYWORDS['message']))

        self.register(self._on_punish, constants.KEYWORDS['punish'])
        self.register(self._on_punish, (constants.KEYWORDS['deactivate'], constants.KEYWORDS['unpunish']))
        self.register(self._on_punish, (constants.KEYWORDS['deactivate'], constants.KEYWORDS['permission']))

        self.register(self._on_recover_message, (constants.KEYWORDS['reset'], multibot_constants.KEYWORDS['message']))

        self.register(self._on_scraping, constants.KEYWORDS['scraping'])

        self.register(self._on_scraping_config_activate, (constants.KEYWORDS['activate'], constants.KEYWORDS['scraping']))
        self.register(self._on_scraping_config_activate, (constants.KEYWORDS['activate'], constants.KEYWORDS['scraping'], constants.KEYWORDS['config']))

        self.register(self._on_scraping_config_change, (constants.KEYWORDS['change'], constants.KEYWORDS['scraping']))
        self.register(self._on_scraping_config_change, (constants.KEYWORDS['change'], constants.KEYWORDS['scraping'], constants.KEYWORDS['config']))

        self.register(self._on_scraping_config_deactivate, (constants.KEYWORDS['deactivate'], constants.KEYWORDS['scraping']))
        self.register(self._on_scraping_config_deactivate, (constants.KEYWORDS['deactivate'], constants.KEYWORDS['scraping'], constants.KEYWORDS['config']))

        self.register(self._on_scraping_config_show, (constants.KEYWORDS['show'], constants.KEYWORDS['scraping']))
        self.register(self._on_scraping_config_show, (constants.KEYWORDS['scraping'], constants.KEYWORDS['config']))
        self.register(self._on_scraping_config_show, (constants.KEYWORDS['show'], constants.KEYWORDS['scraping'], constants.KEYWORDS['config']))

        self.register(self._on_song_info, constants.KEYWORDS['song_info'])

        self.register(self._on_unmute, constants.KEYWORDS['unmute'])
        self.register(self._on_unmute, (constants.KEYWORDS['deactivate'], constants.KEYWORDS['mute']))
        self.register(self._on_unmute, (constants.KEYWORDS['activate'], constants.KEYWORDS['sound']))

        self.register(self._on_unpunish, constants.KEYWORDS['unpunish'])

        self.register(self._on_unpunish, (constants.KEYWORDS['deactivate'], constants.KEYWORDS['punish']))
        self.register(self._on_unpunish, (constants.KEYWORDS['activate'], constants.KEYWORDS['permission']))

        self.register(self._on_weather_chart, constants.KEYWORDS['weather_chart'])
        self.register(self._on_weather_chart, (constants.KEYWORDS['show'], constants.KEYWORDS['weather_chart']))

        self.register(self._on_weather_chart_config_activate, (constants.KEYWORDS['activate'], constants.KEYWORDS['weather_chart']))
        self.register(self._on_weather_chart_config_activate, (constants.KEYWORDS['activate'], constants.KEYWORDS['weather_chart'], constants.KEYWORDS['config']))

        self.register(self._on_weather_chart_config_change, (constants.KEYWORDS['change'], constants.KEYWORDS['weather_chart']))
        self.register(self._on_weather_chart_config_change, (constants.KEYWORDS['change'], constants.KEYWORDS['weather_chart'], constants.KEYWORDS['config']))

        self.register(self._on_weather_chart_config_deactivate, (constants.KEYWORDS['deactivate'], constants.KEYWORDS['weather_chart']))
        self.register(self._on_weather_chart_config_deactivate, (constants.KEYWORDS['deactivate'], constants.KEYWORDS['weather_chart'], constants.KEYWORDS['config']))

        self.register(self._on_weather_chart_config_show, (constants.KEYWORDS['weather_chart'], constants.KEYWORDS['config']))
        self.register(self._on_weather_chart_config_show, (constants.KEYWORDS['show'], constants.KEYWORDS['weather_chart'], constants.KEYWORDS['config']))

    async def _change_config(self, config_name: str, message: Message, value: bool = None):
        if value is None:
            value = not message.chat.config[config_name]

        message.chat.config[config_name] = value
        message.chat.save()

        await self.send(f"He {'activado ✔' if value else 'desactivado ❌'} {config_name}.", message)

    @admin(False)
    @group
    async def _check_message_flood(self, message: Message):
        if message.author.is_punished:
            return

        last_2s_messages = Message.find({
            'author': message.author.object_id,
            'last_update': {
                '$gte': datetime.datetime.now() - datetime.timedelta(seconds=2)
            }
        })
        last_7s_messages = Message.find({
            'author': message.author.object_id,
            'last_update': {
                '$gte': datetime.datetime.now() - datetime.timedelta(seconds=7),
                '$lt': datetime.datetime.now() - datetime.timedelta(seconds=2)
            }
        })

        if len(last_2s_messages) >= 5 or len(last_7s_messages) >= 7:
            n_punishments = len(Punishment.find({'user_id': message.author.id, 'group_id': message.chat.group_id}))
            punishment_seconds = (n_punishments + 2) ** constants.PUNISHMENT_INCREMENT_EXPONENT
            try:
                await self.punish(message.author.id, message.chat.group_id, punishment_seconds, message)
            except BadRoleError as e:
                await self._manage_exceptions(e, message)
            else:
                # noinspection PyTypeChecker
                Punishment(message.author.id, message.author.group_id, datetime.datetime.now() + datetime.timedelta(punishment_seconds)).save()
                await self.send(f'Castigado durante {TimeUnits(punishment_seconds).to_words()}.', message)

    @staticmethod
    async def _check_messages():
        Message.collection.delete_many({'last_update': {'$lte': datetime.datetime.now() - multibot_constants.MESSAGE_EXPIRATION_TIME}})

    async def _check_mutes(self):
        mute_groups = self._get_grouped_punishments(Mute)

        now = datetime.datetime.now()
        for (user_id, group_id), sorted_mutes in mute_groups:
            if (last_mute := sorted_mutes[-1]).until <= now:
                await self.unmute(user_id, group_id)
                last_mute.delete()

    async def _check_punishments(self):
        punishment_groups = self._get_grouped_punishments(Punishment)

        now = datetime.datetime.now()
        for (user_id, group_id), sorted_punishments in punishment_groups:
            if now < (last_punishment := sorted_punishments[-1]).until:
                continue

            if last_punishment.until + constants.PUNISHMENTS_RESET <= now:
                for old_punishment in sorted_punishments:
                    old_punishment.delete()

            if last_punishment.is_active:
                await self.unpunish(user_id, group_id)
                last_punishment.is_active = False
                last_punishment.save()

    async def _create_empty_message(self) -> Message:
        return Message()

    @staticmethod
    def _get_grouped_punishments(PunishmentClass: Type[PunishmentBase]) -> tuple[tuple[tuple[int, int], list[PunishmentBase]]]:
        sorted_punishments = PunishmentClass.find(sort_keys=('user_id', 'group_id', 'until'))
        group_iterator: Iterator[
            tuple[
                tuple[int, int],
                Iterator[PunishmentClass]
            ]
        ] = itertools.groupby(sorted_punishments, key=lambda punishment: (punishment.user_id, punishment.group_id))
        return tuple(((user_id, group_id), list(group_)) for (user_id, group_id), group_ in group_iterator)

    @return_if_first_empty(exclude_self_types='FlanaBot', globals_=globals())
    async def _manage_exceptions(self, exceptions: BaseException | Iterable[BaseException], message: Message):
        if not isinstance(exceptions, Iterable):
            exceptions = (exceptions,)

        for exception in exceptions:
            try:
                raise exception
            except BadRoleError as e:
                await self.send_error(f'Rol no encontrado en {e}', message)
            except InstagramLoginError as e:
                await self.send_error(f'No me puedo loguear en Instagram  {random.choice(multibot_constants.SAD_EMOJIS)}  👉  {e}', message)
            except MediaNotFoundError as e:
                await self.send_error(f'No he podido sacar nada de {e.source}  {random.choice(multibot_constants.SAD_EMOJIS)}', message)
            except PlaceNotFoundError as e:
                await self.send_error(f'No he podido encontrar "{e}"  {random.choice(multibot_constants.SAD_EMOJIS)}', message)
            except Exception as e:
                await super()._manage_exceptions(e, message)

    @staticmethod
    def _medias_sended_info(medias: Iterable[Media]) -> str:
        medias_count = {
            Source.TWITTER: {MediaType.IMAGE: 0, MediaType.AUDIO: 0, MediaType.GIF: 0, MediaType.VIDEO: 0, None: 0, MediaType.ERROR: 0},
            Source.INSTAGRAM: {MediaType.IMAGE: 0, MediaType.AUDIO: 0, MediaType.GIF: 0, MediaType.VIDEO: 0, None: 0, MediaType.ERROR: 0},
            Source.TIKTOK: {MediaType.IMAGE: 0, MediaType.AUDIO: 0, MediaType.GIF: 0, MediaType.VIDEO: 0, None: 0, MediaType.ERROR: 0},
            Source.REDDIT: {MediaType.IMAGE: 0, MediaType.AUDIO: 0, MediaType.GIF: 0, MediaType.VIDEO: 0, None: 0, MediaType.ERROR: 0},
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

    async def _mute(self, user_id: int, group_id: int):
        pass

    async def _punish(self, user_id: int, group_id: int):
        pass

    async def _search_and_send_medias(self, message: Message, send_song_info=False) -> list[Message]:
        sended_media_messages = []

        if medias := await self._search_medias(message):
            sended_media_messages, _ = await self.send_medias(medias, message, send_song_info)

        return sended_media_messages

    async def _search_medias(self, message: Message) -> OrderedSet[Media]:
        bot_state_message: Message | None = None
        start_time = time_module.perf_counter()

        results: Future = asyncio.gather(
            twitter.get_medias(message.text),
            instagram.get_medias(message.text),
            tiktok.get_medias(message.text),
            return_exceptions=True
        )

        if not message.is_inline and (self.is_bot_mentioned(message) or not message.chat.is_group):
            while not results.done():
                if constants.SCRAPING_MESSAGE_WAITING_TIME <= time_module.perf_counter() - start_time:
                    bot_state_message = await self.send(random.choice(constants.SCRAPING_PHRASES), message)
                    break
                await asyncio.sleep(0.1)

        await results
        if bot_state_message:
            await self.delete_message(bot_state_message)

        results, exceptions = flanautils.filter_exceptions(results.result())

        await self._manage_exceptions(exceptions, message)

        return OrderedSet(*results)

    async def _show_config(self, config_name: str, message: Message):
        await self.send(f"{config_name} está {'activado ✔' if message.chat.config.get(config_name) else 'desactivado ❌'}", message)

    async def _unmute(self, user_id: int, group_id: int):
        pass

    async def _unpunish(self, user_id: int, group_id: int):
        pass

    # ---------------------------------------------- #
    #                    HANDLERS                    #
    # ---------------------------------------------- #
    async def _on_bye(self, message: Message):
        if not message.chat.is_group or self.is_bot_mentioned(message):
            await self.send_bye(message)

    @group
    @bot_mentioned
    async def _on_config_list_show(self, message: Message):
        config_info = pprint.pformat(message.chat.config)
        config_info = flanautils.translate(config_info, {'{': None, '}': None, ',': None, 'True': '✔', "'": None, 'False': '❌'})
        config_info = config_info.splitlines()
        config_info = '\n'.join(config_info_.strip() for config_info_ in config_info)
        await self.send(f'<b>Estos son los ajustes del grupo:</b>\n\n<code>{config_info}</code>', message)

    async def _on_covid_chart(self, message: Message):  # todo2
        pass

    async def _on_currency_chart(self, message: Message):  # todo2
        pass

    @admin
    @group
    @bot_mentioned
    async def _on_currency_chart_config_activate(self, message: Message):
        await self._change_config('auto_currency_chart', message, True)

    @admin
    @group
    @bot_mentioned
    async def _on_currency_chart_config_change(self, message: Message):
        await self._change_config('auto_currency_chart', message)

    @admin
    @group
    @bot_mentioned
    async def _on_currency_chart_config_deactivate(self, message: Message):
        await self._change_config('auto_currency_chart', message, False)

    @admin
    @group
    @bot_mentioned
    async def _on_currency_chart_config_show(self, message: Message):
        await self._show_config('auto_currency_chart', message)

    @admin
    @group
    @bot_mentioned
    async def _on_delete_original_config_activate(self, message: Message):
        await self._change_config('auto_delete_original', message, True)

    @admin
    @group
    @bot_mentioned
    async def _on_delete_original_config_change(self, message: Message):
        await self._change_config('auto_delete_original', message)

    @admin
    @group
    @bot_mentioned
    async def _on_delete_original_config_deactivate(self, message: Message):
        await self._change_config('auto_delete_original', message, False)

    @admin
    @group
    @bot_mentioned
    async def _on_delete_original_config_show(self, message: Message):
        await self._show_config('auto_delete_original', message)

    async def _on_hello(self, message: Message):
        if not message.chat.is_group or self.is_bot_mentioned(message):
            await self.send_hello(message)

    @group
    @bot_mentioned
    @admin(send_negative=True)
    async def _on_mute(self, message: Message):
        await self._update_punishment(self.mute, message, time=flanautils.words_to_time(message.text))

    async def _on_new_message_default(self, message: Message):
        if message.is_inline:
            await self._on_scraping(message)
        elif (
                message.chat.is_group
                and
                not self.is_bot_mentioned(message)
                and
                not message.chat.config['auto_scraping']
                or
                not await self._on_scraping(message)
        ):
            await self.send_bad_phrase(message)

    @ignore_self_message
    async def _on_new_message_raw(self, message: Message):
        await super()._on_new_message_raw(message)
        if not message.is_inline:
            await self._check_message_flood(message)

    async def _on_no_delete_original(self, message: Message):
        if not await self._on_scraping(message, delete_original=False):
            await self._on_recover_message(message)

    @bot_mentioned
    @group
    @admin(send_negative=True)
    async def _on_punish(self, message: Message):
        await self._update_punishment(self.punish, message, time=flanautils.words_to_time(message.text))

    async def _on_ready(self):
        await super()._on_ready()
        await flanautils.do_every(constants.CHECK_MUTES_EVERY_SECONDS, self._check_mutes)
        await flanautils.do_every(constants.CHECK_MESSAGE_EVERY_SECONDS, self._check_messages)
        await flanautils.do_every(constants.CHECK_PUNISHMENTS_EVERY_SECONDS, self._check_punishments)

    @inline(False)
    async def _on_recover_message(self, message: Message):
        if message.replied_message:
            message_deleted_bot_action = BotAction.find_one({'action': bytes(Action.MESSAGE_DELETED), 'chat': message.chat.object_id, 'affected_objects': message.replied_message.object_id})
        elif self.is_bot_mentioned(message):
            message_deleted_bot_action = BotAction.find_one({'action': bytes(Action.MESSAGE_DELETED), 'chat': message.chat.object_id, 'date': {'$gt': datetime.datetime.now() - constants.RECOVERY_DELETED_MESSAGE_BEFORE}})
        else:
            return

        if not message_deleted_bot_action:
            await self.send_error(random.choice(constants.RECOVER_PHRASES), message)
            return

        affected_object_ids = [affected_message_object_id for affected_message_object_id in message_deleted_bot_action.affected_objects]
        deleted_messages: list[Message] = [affected_message for affected_object_id in affected_object_ids if (affected_message := Message.find_one({'_id': affected_object_id})).author.id != self.bot_id]
        for deleted_message in deleted_messages:
            await self.send(deleted_message.text, message)

        message_deleted_bot_action.delete()

    async def _on_scraping(self, message: Message, delete_original: bool = None) -> OrderedSet[Media]:
        sended_media_messages = await self._search_and_send_medias(message.replied_message) if message.replied_message else OrderedSet()
        sended_media_messages += await self._search_and_send_medias(message)
        await self.send_inline_results(message)

        if (
                sended_media_messages
                and
                message.chat.is_group
                and
                (
                        (
                                delete_original is None
                                and
                                message.chat.config['auto_delete_original']
                        )
                        or
                        (
                                delete_original is not None
                                and
                                delete_original
                        )
                )
        ):
            # noinspection PyTypeChecker
            BotAction(Action.MESSAGE_DELETED, message, affected_objects=[message, *sended_media_messages]).save()
            await self.delete_message(message)

        return sended_media_messages

    @admin
    @group
    @bot_mentioned
    async def _on_scraping_config_activate(self, message: Message):
        await self._change_config('auto_scraping', message, True)

    @admin
    @group
    @bot_mentioned
    async def _on_scraping_config_change(self, message: Message):
        await self._change_config('auto_scraping', message)

    @admin
    @group
    @bot_mentioned
    async def _on_scraping_config_deactivate(self, message: Message):
        await self._change_config('auto_scraping', message, False)

    @admin
    @group
    @bot_mentioned
    async def _on_scraping_config_show(self, message: Message):
        await self._show_config('auto_scraping', message)

    @reply
    async def _on_song_info(self, message: Message):
        song_infos = message.replied_message.song_infos if message.replied_message else []

        if song_infos:
            for song_info in song_infos:
                await self.send_song_info(song_info, message)
        elif self.is_bot_mentioned(message) or not message.chat.is_group:
            await self._manage_exceptions(SendError('No hay información musical en ese mensaje.'), message)

    @group
    @bot_mentioned
    @admin(send_negative=True)
    async def _on_unmute(self, message: Message):
        await self._update_punishment(self.unmute, message)

    @group
    @bot_mentioned
    @admin(send_negative=True)
    async def _on_unpunish(self, message: Message):
        await self._update_punishment(self.unpunish, message)

    async def _on_weather_chart(self, message: Message):
        bot_state_message: Message | None = None
        if message.is_inline:
            show_progress_state = False
        elif message.chat.is_group and not self.is_bot_mentioned(message):
            if message.chat.config['auto_weather_chart']:
                if BotAction.find_one({'action': bytes(Action.AUTO_WEATHER_CHART), 'chat': message.chat.object_id, 'date': {'$gt': datetime.datetime.now() - constants.AUTO_WEATHER_EVERY}}):
                    return
                show_progress_state = False
            else:
                return
        else:
            show_progress_state = True

        user_names_with_at_sign = {user.name.lower() for user in message.chat.users}
        user_names_without_at_sign = {user.name.lower().replace('@', '') for user in message.chat.users}
        original_text_words = flanautils.remove_accents(message.text.lower())
        original_text_words = flanautils.translate(
            original_text_words,
            {symbol: None for symbol in set(flanautils.SYMBOLS) - {'-', '.'}}
        ).split()
        place_words = (
                OrderedSet(original_text_words)
                - flanautils.cartesian_product_string_matching(original_text_words, constants.KEYWORDS['show'], min_ratio=0.85).keys()
                - flanautils.cartesian_product_string_matching(original_text_words, constants.KEYWORDS['weather_chart'], min_ratio=0.85).keys()
                - flanautils.cartesian_product_string_matching(original_text_words, constants.KEYWORDS['date'], min_ratio=0.85).keys()
                - flanautils.cartesian_product_string_matching(original_text_words, constants.KEYWORDS['thanks'], min_ratio=0.85).keys()
                - user_names_with_at_sign
                - user_names_without_at_sign
                - flanautils.CommonWords.all_words
        )
        if not place_words:
            if not message.is_inline:
                await self.send_error(random.choice(('¿Tiempo dónde?', 'Indica el sitio.', 'Y el sitio?', 'y el sitio? me lo invento?')), message)
            return

        if 'calle' in original_text_words:
            place_words.insert(0, 'calle')
        place_query = ' '.join(place_words)
        if len(place_query) >= constants.MAX_PLACE_QUERY_LENGTH:
            if not message.is_inline:
                await self.send_error(Media('resources/mucho_texto.png'), message)
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
            Media(image_bytes, MediaType.IMAGE),
            [
                [WeatherEmoji.ZOOM_IN.value, WeatherEmoji.ZOOM_OUT.value, WeatherEmoji.LEFT.value, WeatherEmoji.RIGHT.value],
                [WeatherEmoji.TEMPERATURE.value, WeatherEmoji.TEMPERATURE_FEEL.value, WeatherEmoji.CLOUDS.value, WeatherEmoji.VISIBILITY.value, WeatherEmoji.UVI.value],
                [WeatherEmoji.HUMIDITY.value, WeatherEmoji.PRECIPITATION_PROBABILITY.value, WeatherEmoji.PRECIPITATION_VOLUME.value, WeatherEmoji.PRESSURE.value, WeatherEmoji.WIND_SPEED.value]
            ],
            message,
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

    @admin
    @group
    @bot_mentioned
    async def _on_weather_chart_config_activate(self, message: Message):
        await self._change_config('auto_weather_chart', message, True)

    @admin
    @group
    @bot_mentioned
    async def _on_weather_chart_config_change(self, message: Message):
        await self._change_config('auto_weather_chart', message)

    @admin
    @group
    @bot_mentioned
    async def _on_weather_chart_config_deactivate(self, message: Message):
        await self._change_config('auto_weather_chart', message, False)

    @admin
    @group
    @bot_mentioned
    async def _on_weather_chart_config_show(self, message: Message):
        await self._show_config('auto_weather_chart', message)

    # -------------------------------------------------------- #
    # -------------------- PUBLIC METHODS -------------------- #
    # -------------------------------------------------------- #
    async def is_deaf(self, user_id: int, group_id: int) -> bool:
        pass

    async def is_muted(self, user_id: int, group_id: int) -> bool:
        pass

    async def mute(self, user_id: int, group_id: int, time: int | datetime.timedelta, message: Message = None):
        if isinstance(time, int):
            time = datetime.timedelta(seconds=time)

        try:
            await self._mute(user_id, group_id)
        except UserDisconnectedError as e:
            await self._manage_exceptions(e, message if message else Message(chat=Chat(group_id=group_id)))
        else:
            if time:
                # noinspection PyTypeChecker
                Mute(user_id, group_id, until=datetime.datetime.now() + time).save()
                if datetime.timedelta() < time <= constants.TIME_THRESHOLD_TO_MANUAL_UNMUTE:
                    await flanautils.do_later(time, self._check_mutes)
            else:
                # noinspection PyTypeChecker
                Mute(user_id, group_id).save()

    async def punish(self, user_id: int, group_id: int, time: int | datetime.timedelta, message: Message = None):
        if isinstance(time, int):
            time = datetime.timedelta(seconds=time)

        try:
            await self._punish(user_id, group_id)
        except BadRoleError as e:
            await self._manage_exceptions(e, message if message else Message(chat=Chat(group_id=group_id)))
        else:
            if time:
                # noinspection PyTypeChecker
                Punishment(user_id, group_id, until=datetime.datetime.now() + time).save()
                if datetime.timedelta() < time <= constants.TIME_THRESHOLD_TO_MANUAL_UNPUNISH:
                    await flanautils.do_later(time, self._check_punishments)
            else:
                # noinspection PyTypeChecker
                Punishment(user_id, group_id).save()

    async def send_bad_phrase(self, message: Message, probability=0.00166666667) -> multibot_constants.ORIGINAL_MESSAGE | None:
        if not self.is_bot_mentioned(message) and random.random() >= probability or message.author.id == self.owner_id:
            return

        await self.typing_delay(message)

        return await self.send(random.choice(constants.BAD_PHRASES), message)

    async def send_bye(self, message: Message) -> multibot_constants.ORIGINAL_MESSAGE:
        return await self.send(random.choice((*constants.BYE_PHRASES, flanautils.CommonWords.random_time_greeting())), message)

    async def send_hello(self, message: Message) -> multibot_constants.ORIGINAL_MESSAGE:
        return await self.send(random.choice((*constants.HELLO_PHRASES, flanautils.CommonWords.random_time_greeting())), message)

    @return_if_first_empty(exclude_self_types='FlanaBot', globals_=globals())
    async def send_medias(self, medias: OrderedSet[Media], message: Message, send_song_info=False) -> tuple[list[Message], int]:
        sended_media_messages = []
        fails = 0
        bot_state_message: Message | None = None
        sended_info_message: Message | None = None

        if not message.is_inline:
            bot_state_message: Message = await self.send('Descargando...', message)

        if message.chat.is_group:
            sended_info_message = await self.send(f'{message.author.name} compartió{self._medias_sended_info(medias)}', message)

        for media in medias:
            if not media.content:
                fails += 1
                continue

            if media.song_info:
                message.song_infos.add(media.song_info)
                message.save()

            try:
                bot_message = await self.send(media, message)
            except SendError as e:
                await self._manage_exceptions(e, message)
                fails += 1
            else:
                sended_media_messages.append(bot_message)
                if media.song_info and bot_message:
                    bot_message.song_infos.add(media.song_info)
                    bot_message.save()

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
            f"{f'Álbum: {song_info.album}'}\n" if song_info.album else '',
            f'Previa:'
        )
        await self.send(''.join(attributes), message)
        if song_info:
            await self.send(song_info, message)

    async def unmute(self, user_id: int, group_id: int, message: Message = None):
        try:
            await self._unmute(user_id, group_id)
        except UserDisconnectedError as e:
            await self._manage_exceptions(e, message if message else Message(chat=Chat(group_id=group_id)))

    async def unpunish(self, user_id: int, group_id: int, message: Message = None):
        try:
            await self._unpunish(user_id, group_id)
        except BadRoleError as e:
            await self._manage_exceptions(e, message if message else Message(chat=Chat(group_id=group_id)))
