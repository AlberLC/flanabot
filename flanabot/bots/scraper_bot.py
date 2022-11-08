__all__ = ['ScraperBot']

import asyncio
import random
from abc import ABC
from typing import Iterable

import flanautils
from flanaapis import instagram, tiktok, twitter, youtube
from flanautils import Media, MediaType, OrderedSet, Source, return_if_first_empty
from multibot import MultiBot, RegisteredCallback, SendError, constants as multibot_constants, reply

from flanabot import constants
from flanabot.models import Action, BotAction, Message


# ----------------------------------------------------------------------------------------------------- #
# --------------------------------------------- SCRAPER_BOT --------------------------------------------- #
# ----------------------------------------------------------------------------------------------------- #
class ScraperBot(MultiBot, ABC):
    # ----------------------------------------------------------- #
    # -------------------- PROTECTED METHODS -------------------- #
    # ----------------------------------------------------------- #
    def _add_handlers(self):
        super()._add_handlers()

        self.register(self._on_no_delete_original, (multibot_constants.KEYWORDS['negate'], multibot_constants.KEYWORDS['delete']))
        self.register(self._on_no_delete_original, (multibot_constants.KEYWORDS['negate'], multibot_constants.KEYWORDS['message']))
        self.register(self._on_no_delete_original, (multibot_constants.KEYWORDS['negate'], multibot_constants.KEYWORDS['delete'], multibot_constants.KEYWORDS['message']))
        self.register(self._on_no_delete_original, (multibot_constants.KEYWORDS['deactivate'], multibot_constants.KEYWORDS['delete'], multibot_constants.KEYWORDS['message']))
        self.register(self._on_scraping, constants.KEYWORDS['scraping'])

        self.register(self._on_scraping_audio, multibot_constants.KEYWORDS['audio'])
        self.register(self._on_scraping_audio, (multibot_constants.KEYWORDS['audio'], constants.KEYWORDS['scraping']))

        self.register(self._on_song_info, constants.KEYWORDS['song_info'])

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

    # ---------------------------------------------- #
    #                    HANDLERS                    #
    # ---------------------------------------------- #
    async def _on_no_delete_original(self, message: Message):
        if not await self._scrape_and_send(message):
            await self._on_recover_message(message)

    async def _on_recover_message(self, message: Message):
        pass

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

    # -------------------------------------------------------- #
    # -------------------- PUBLIC METHODS -------------------- #
    # -------------------------------------------------------- #
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
