__all__ = ['ScraperBot']

import asyncio
import datetime
import random
from abc import ABC
from collections import defaultdict
from typing import Iterable

import flanautils
from flanaapis import InstagramMediaNotFoundError, RedditMediaNotFoundError, instagram, reddit, tiktok, twitter, yt_dlp_wrapper
from flanautils import Media, MediaType, OrderedSet, return_if_first_empty
from multibot import MultiBot, RegisteredCallback, SendError, constants as multibot_constants, reply

from flanabot import constants
from flanabot.models import Action, BotAction, Message


# ------------------------------------------------------------------------------------------------------- #
# --------------------------------------------- SCRAPER_BOT --------------------------------------------- #
# ------------------------------------------------------------------------------------------------------- #
class ScraperBot(MultiBot, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner_chat = None
        self.instagram_ban_date = None

    # -------------------------------------------------------- #
    # ------------------- PROTECTED METHODS ------------------ #
    # -------------------------------------------------------- #
    def _add_handlers(self):
        super()._add_handlers()

        self.register(self._on_no_scraping, (multibot_constants.KEYWORDS['negate'], constants.KEYWORDS['scraping']))

        self.register(self._on_reset_instagram_ban, (multibot_constants.KEYWORDS['delete'], ('instagram',)))
        self.register(self._on_reset_instagram_ban, (multibot_constants.KEYWORDS['reset'], ('instagram',)))

        self.register(self._on_scraping, constants.KEYWORDS['scraping'])
        self.register(self._on_scraping, constants.KEYWORDS['force'])
        self.register(self._on_scraping, multibot_constants.KEYWORDS['audio'])
        self.register(lambda message: self._on_scraping(message, delete=False), (multibot_constants.KEYWORDS['negate'], multibot_constants.KEYWORDS['delete']))
        self.register(lambda message: self._on_scraping(message, delete=False), (multibot_constants.KEYWORDS['negate'], multibot_constants.KEYWORDS['message']))
        self.register(lambda message: self._on_scraping(message, delete=False), (multibot_constants.KEYWORDS['negate'], multibot_constants.KEYWORDS['delete'], multibot_constants.KEYWORDS['message']))

        self.register(self._on_song_info, constants.KEYWORDS['song_info'])

    @staticmethod
    async def _find_ids(text: str) -> tuple[OrderedSet[str], ...]:
        return (
            twitter.find_ids(text),
            instagram.find_ids(text),
            reddit.find_ids(text),
            await tiktok.find_users_and_ids(text),
            tiktok.find_download_urls(text)
        )

    @staticmethod
    def _get_keywords(delete=True, force=False, full=False, audio_only=False) -> list[str]:
        keywords = list(constants.KEYWORDS['scraping'])

        if not delete:
            keywords += [
                *multibot_constants.KEYWORDS['negate'],
                *multibot_constants.KEYWORDS['deactivate'],
                *multibot_constants.KEYWORDS['delete'],
                *multibot_constants.KEYWORDS['message']
            ]

        if force:
            keywords += constants.KEYWORDS['force']

        if full:
            keywords += ['sin', 'timeout', 'limite', *multibot_constants.KEYWORDS['all']]

        if audio_only:
            keywords += multibot_constants.KEYWORDS['audio']

        return keywords

    @staticmethod
    def _medias_sended_info(medias: Iterable[Media]) -> str:
        medias_count: dict = defaultdict(lambda: defaultdict(int))
        for media in medias:
            if not media.source or isinstance(media.source, str):
                medias_count[media.source][media.type_] += 1
            else:
                medias_count[media.source.name][media.type_] += 1

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
                medias_sended_info.append(f"{flanautils.join_last_separator(source_medias_sended_info, ', ', ' y ')} de {source if source else 'algún sitio'}")

        medias_sended_info_joined = flanautils.join_last_separator(medias_sended_info, ',\n', ' y\n')
        new_line = ' ' if len(medias_sended_info) == 1 else '\n'
        return f'{new_line}{medias_sended_info_joined}:'

    async def _scrape_and_send(
        self,
        message: Message,
        force=False,
        full=False,
        audio_only=False,
        send_user_context=True,
        keywords: list[str] = None,
        sended_media_messages: OrderedSet[Message] = None
    ) -> OrderedSet[Message]:
        if not keywords:
            keywords = []
        if sended_media_messages is None:
            sended_media_messages = OrderedSet()

        kwargs = {'timeout_for_media': None} if full else {}

        if not (medias := await self._search_medias(message, force, audio_only, **kwargs)):
            return OrderedSet()

        new_sended_media_messages, _ = await self.send_medias(medias, message, send_user_context=send_user_context, keywords=keywords)
        sended_media_messages |= new_sended_media_messages

        await self.send_inline_results(message)

        return sended_media_messages

    async def _scrape_send_and_delete(
        self,
        message: Message,
        force=False,
        full=False,
        audio_only=False,
        send_user_context=True,
        keywords: list[str] = None,
        sended_media_messages: OrderedSet[Message] = None
    ) -> OrderedSet[Message]:
        if not keywords:
            keywords = []
        if sended_media_messages is None:
            sended_media_messages = OrderedSet()

        sended_media_messages += await self._scrape_and_send(message, force, full, audio_only, send_user_context, keywords)

        if sended_media_messages and message.chat.config['scraping_delete_original']:
            # noinspection PyTypeChecker
            BotAction(self.platform.value, Action.MESSAGE_DELETED, message, affected_objects=[message, *sended_media_messages]).save()
            await self.delete_message(message)

        return sended_media_messages

    async def _search_medias(
        self,
        message: Message,
        force=False,
        audio_only=False,
        timeout_for_media: int | float = None
    ) -> OrderedSet[Media]:
        medias = OrderedSet()
        exceptions: list[Exception] = []

        ids = []
        media_urls = []
        for text_part in message.text.split():
            for i, platform_ids in enumerate(await self._find_ids(text_part)):
                try:
                    ids[i] |= platform_ids
                except IndexError:
                    ids.append(platform_ids)
            if not any(ids) and flanautils.find_urls(text_part):
                if force:
                    media_urls.append(text_part)
                elif not any(domain.lower() in text_part for domain in multibot_constants.GIF_DOMAINS):
                    media_urls.append(text_part)

        if not any(ids) and not media_urls:
            return medias

        bot_state_message = await self.send(random.choice(constants.SCRAPING_PHRASES), message)

        tweet_ids, instagram_ids, reddit_ids, tiktok_users_and_ids, tiktok_download_urls = ids

        try:
            reddit_medias = await reddit.get_medias(reddit_ids, 'h264', 'mp4', force, audio_only, timeout_for_media)
        except RedditMediaNotFoundError as e:
            exceptions.append(e)
            reddit_medias = ()
        reddit_urls = []
        for reddit_media in reddit_medias:
            if reddit_media.source:
                medias.add(reddit_media)
            else:
                reddit_urls.append(reddit_media.url)
        if force:
            media_urls.extend(reddit_urls)
        else:
            for reddit_url in reddit_urls:
                for domain in multibot_constants.GIF_DOMAINS:
                    if domain.lower() in reddit_url:
                        medias.add(Media(reddit_url, MediaType.GIF, source=domain))
                        break
                else:
                    media_urls.append(reddit_url)

        gather_result = asyncio.gather(
            twitter.get_medias(tweet_ids, audio_only),
            tiktok.get_medias(tiktok_users_and_ids, tiktok_download_urls, 'h264', 'mp4', force, audio_only, timeout_for_media),
            yt_dlp_wrapper.get_medias(media_urls, 'h264', 'mp4', force, audio_only, timeout_for_media),
            return_exceptions=True
        )

        await gather_result
        instagram_results = []
        if not self.instagram_ban_date or self.instagram_ban_date + constants.INSTAGRAM_BAN_SLEEP >= datetime.datetime.now(datetime.timezone.utc):
            try:
                instagram_results = await instagram.get_medias(instagram_ids, audio_only)
            except InstagramMediaNotFoundError:
                self.instagram_ban_date = datetime.datetime.now(datetime.timezone.utc)
                if not self.owner_chat:
                    self.owner_chat = await self.get_chat(self.owner_id) or await self.get_chat(await self.get_user(self.owner_id))
                await self.send('Instagram limite excedido.', self.owner_chat)
        if not instagram_results:
            instagram_results = await instagram.get_medias_v2(instagram_ids, audio_only)

        await self.delete_message(bot_state_message)

        gather_medias, gather_exceptions = flanautils.filter_exceptions(gather_result.result() + instagram_results)
        await self._manage_exceptions(exceptions + gather_exceptions, message, print_traceback=True)

        return medias | gather_medias

    # ---------------------------------------------- #
    #                    HANDLERS                    #
    # ---------------------------------------------- #
    async def _on_no_scraping(self, message: Message):
        pass

    async def _on_recover_message(self, message: Message):
        pass

    async def _on_reset_instagram_ban(self, _message: Message):
        self.instagram_ban_date = None

    async def _on_scraping(
        self,
        message: Message,
        delete=True,
        force: bool = None,
        full: bool = None,
        audio_only: bool = None,
        scrape_replied=True,
    ) -> OrderedSet[Message]:
        sended_media_messages = OrderedSet()
        if not message.chat.config['auto_scraping'] and not self.is_bot_mentioned(message):
            return sended_media_messages

        if force is None:
            force = bool(
                flanautils.cartesian_product_string_matching(
                    message.text,
                    constants.KEYWORDS['force'],
                    multibot_constants.PARSER_MIN_SCORE_DEFAULT
                )
            )

        if full is None:
            full = bool(
                self._parse_callbacks(
                    message.text,
                    [
                        RegisteredCallback(..., (('sin',), ('timeout', 'limite'))),
                        RegisteredCallback(..., multibot_constants.KEYWORDS['all'])
                    ]
                )
            )

        if audio_only is None:
            audio_only = bool(
                flanautils.cartesian_product_string_matching(
                    message.text,
                    multibot_constants.KEYWORDS['audio'],
                    multibot_constants.PARSER_MIN_SCORE_DEFAULT
                )
            )

        keywords = self._get_keywords(delete, force, full, audio_only)

        if scrape_replied and message.replied_message:
            sended_media_messages += await self._scrape_and_send(
                message.replied_message,
                force,
                full,
                audio_only,
                send_user_context=False
            )

        kwargs = {
            'message': message,
            'force': force,
            'full': full,
            'audio_only': audio_only,
            'keywords': keywords,
            'sended_media_messages': sended_media_messages
        }
        if delete:
            sended_media_messages |= await self._scrape_send_and_delete(**kwargs)
        else:
            sended_media_messages |= await self._scrape_and_send(**kwargs)
            if not sended_media_messages:
                await self._on_recover_message(message)

        return sended_media_messages

    @reply
    async def _on_song_info(self, message: Message):
        song_infos = message.replied_message.song_infos if message.replied_message else []

        if song_infos:
            for song_info in song_infos:
                await self.send_song_info(song_info, message)
        elif message.chat.is_private or self.is_bot_mentioned(message):
            raise SendError('No hay información musical en ese mensaje.')

    # -------------------------------------------------------- #
    # -------------------- PUBLIC METHODS -------------------- #
    # -------------------------------------------------------- #
    @return_if_first_empty(([], 0), exclude_self_types='ScraperBot', globals_=globals())
    async def send_medias(
        self,
        medias: OrderedSet[Media],
        message: Message,
        send_song_info=False,
        send_user_context=True,
        keywords: list[str] = None
    ) -> tuple[list[Message], int]:
        if not keywords:
            keywords = []

        sended_media_messages = []
        fails = 0
        bot_state_message: Message | None = None
        sended_info_message: Message | None = None
        user_text_bot_message: Message | None = None

        if not message.is_inline:
            bot_state_message: Message = await self.send('Enviando...', message)

        if message.chat.is_group:
            sended_info_message = await self.send(f"{message.author.name.split('#')[0]} compartió{self._medias_sended_info(medias)}", message, reply_to=message.replied_message)
            if (
                    send_user_context
                    and
                    (user_text := ' '.join(
                        [word for word in message.text.split()
                         if (
                                 not any(await self._find_ids(word))
                                 and
                                 not flanautils.find_urls(word)
                                 and
                                 not flanautils.cartesian_product_string_matching(word, keywords, multibot_constants.PARSER_MIN_SCORE_DEFAULT)
                                 and
                                 flanautils.remove_symbols(word).lower() not in (str(self.id), self.name.lower())
                         )]
                    ))
            ):
                user_text_bot_message = await self.send(user_text, message, reply_to=message.replied_message)

        for media in medias:
            if not media.content:
                fails += 1
                continue

            if media.song_info:
                message.song_infos.add(media.song_info)
                message.save()

            if bot_message := await self.send(media, message, reply_to=message.replied_message):
                sended_media_messages.append(bot_message)
                if media.song_info and bot_message:
                    bot_message.song_infos.add(media.song_info)
                    bot_message.save()
            else:
                fails += 1

            if send_song_info and media.song_info:
                await self.send_song_info(media.song_info, message)

        if fails == len(medias):
            if sended_info_message:
                await self.delete_message(sended_info_message)
            if user_text_bot_message:
                await self.delete_message(user_text_bot_message)

        if bot_state_message:
            await self.delete_message(bot_state_message)

        return sended_media_messages, fails

    @return_if_first_empty(exclude_self_types='ScraperBot', globals_=globals())
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
