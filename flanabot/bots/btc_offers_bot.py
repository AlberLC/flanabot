__all__ = ['BtcOffersBot']

import asyncio
import datetime
import functools
import json
import os
from abc import ABC
from collections import defaultdict
from collections.abc import Awaitable, Callable

import aiohttp
import flanautils
import websockets
from multibot import MultiBot, constants as multibot_constants

from flanabot import constants
from flanabot.models import Chat, Message
from models.dated_offers import DatedOffers
from models.enums import Exchange, PaymentMethod


# ---------------------------------------------------- #
# -------------------- DECORATORS -------------------- #
# ---------------------------------------------------- #
def preprocess_btc_offers(
    func: Callable[[BtcOffersBot, Message, dict], Awaitable[None]]
) -> Callable[[BtcOffersBot, Message], Awaitable[None]]:
    @functools.wraps(func)
    async def wrapper(self: BtcOffersBot, message: Message) -> None:
        if message.chat.is_group and not self.is_bot_mentioned(message):
            return

        eur_mode = (
            '€' in message.text
            or
            bool(
                flanautils.cartesian_product_string_matching(
                    message.text,
                    constants.KEYWORDS['eur'],
                    multibot_constants.PARSER_MIN_SCORE_DEFAULT
                )
            )
        )
        usd_mode = (
            '$' in message.text
            or
            bool(
                flanautils.cartesian_product_string_matching(
                    message.text,
                    constants.KEYWORDS['usd'],
                    multibot_constants.PARSER_MIN_SCORE_DEFAULT
                )
            )
        )
        premium_mode = (
            '%' in message.text
            or
            bool(
                flanautils.cartesian_product_string_matching(
                    message.text,
                    constants.KEYWORDS['premium'],
                    multibot_constants.PARSER_MIN_SCORE_DEFAULT
                )
            )
        )

        if len([arg for arg in (eur_mode, usd_mode, premium_mode) if arg]) > 1:
            await self.send_error(
                'Indica únicamente uno de los siguientes: precio en euros, precio en dólares o prima.',
                message
            )
            return

        parsed_number = flanautils.text_to_number(message.text, accept_comma=True)

        if not premium_mode and parsed_number < 0 or not flanautils.validate_mongodb_number(parsed_number):
            await self.send_error('❌ Por favor, introduce un número válido.', message)
            return

        query = {}

        if payment_methods := self._find_payment_methods(message.text):
            query['payment_methods'] = [payment_method.value for payment_method in payment_methods]

        if exchanges := self._find_exchanges(message.text):
            query['exchanges'] = [exchange.value for exchange in exchanges]

        if eur_mode:
            query['max_price_eur'] = parsed_number
            query['limit'] = constants.BTC_OFFERS_MAX_LIMIT
        elif usd_mode:
            query['max_price_usd'] = parsed_number
            query['limit'] = constants.BTC_OFFERS_MAX_LIMIT
        elif premium_mode:
            query['max_premium'] = parsed_number
            query['limit'] = constants.BTC_OFFERS_MAX_LIMIT
        elif parsed_number:
            query['limit'] = min(parsed_number, constants.BTC_OFFERS_MAX_LIMIT)
        else:
            query['limit'] = constants.BTC_OFFERS_DEFAULT_LIMIT

        query['ignore_authors'] = message.chat.btc_offers['blocked_authors']

        await func(self, message, query)

    return wrapper


# ---------------------------------------------------------------------------------------------------- #
# ------------------------------------------ BTC_OFFERS_BOT ------------------------------------------ #
# ---------------------------------------------------------------------------------------------------- #
class BtcOffersBot(MultiBot, ABC):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._btc_offers_api_endpoint = (
            f'{os.environ['BTC_OFFERS_API_HOST']}:{os.environ['BTC_OFFERS_API_PORT']}/offers'
        )
        self._btc_offers_lock = asyncio.Lock()
        self._btc_offers_notifications_task: asyncio.Task[None] | None = None
        self._btc_offers_websocket: websockets.ClientConnection | None = None
        self._payment_method_keyword_max_words = 0
        self._payment_methods_keywords_groups = {}

        for payment_method, payment_method_keywords in constants.KEYWORDS['btc_offers_payment_methods'].items():
            payment_method_keywords_groups = defaultdict(set)

            for payment_method_keyword in payment_method_keywords:
                keyword_words = payment_method_keyword.split()

                if len(keyword_words) > self._payment_method_keyword_max_words:
                    self._payment_method_keyword_max_words = len(keyword_words)

                payment_method_keywords_groups[len(keyword_words)].add(payment_method_keyword)

            self._payment_methods_keywords_groups[payment_method] = sorted(
                payment_method_keywords_groups.items(), key=lambda item: -item[0]
            )

    # -------------------------------------------------------- #
    # ------------------- PROTECTED METHODS ------------------ #
    # -------------------------------------------------------- #
    def _add_handlers(self) -> None:
        super()._add_handlers()

        self.register(self._on_block_authors, keywords=(multibot_constants.KEYWORDS['block'], constants.KEYWORDS['offer']))
        self.register(self._on_block_authors, keywords=(multibot_constants.KEYWORDS['block'], constants.KEYWORDS['money']))
        self.register(self._on_block_authors, keywords=(multibot_constants.KEYWORDS['ignore'], constants.KEYWORDS['offer']))
        self.register(self._on_block_authors, keywords=(multibot_constants.KEYWORDS['ignore'], constants.KEYWORDS['money']))
        self.register(self._on_block_authors, extra_kwargs={'delete': True}, keywords=((*multibot_constants.KEYWORDS['deactivate'], *multibot_constants.KEYWORDS['delete']), multibot_constants.KEYWORDS['block'], constants.KEYWORDS['offer']))
        self.register(self._on_block_authors, extra_kwargs={'delete': True}, keywords=((*multibot_constants.KEYWORDS['deactivate'], *multibot_constants.KEYWORDS['delete']), multibot_constants.KEYWORDS['block'], constants.KEYWORDS['money']))
        self.register(self._on_block_authors, extra_kwargs={'delete': True}, keywords=((*multibot_constants.KEYWORDS['deactivate'], *multibot_constants.KEYWORDS['delete']), multibot_constants.KEYWORDS['ignore'], constants.KEYWORDS['offer']))
        self.register(self._on_block_authors, extra_kwargs={'delete': True}, keywords=((*multibot_constants.KEYWORDS['deactivate'], *multibot_constants.KEYWORDS['delete']), multibot_constants.KEYWORDS['ignore'], constants.KEYWORDS['money']))
        self.register(self._on_block_authors, extra_kwargs={'delete': True}, keywords=(multibot_constants.KEYWORDS['unblock'], constants.KEYWORDS['offer']))
        self.register(self._on_block_authors, extra_kwargs={'delete': True}, keywords=(multibot_constants.KEYWORDS['unblock'], constants.KEYWORDS['money']))

        self.register(self._on_btc_offers, keywords=constants.KEYWORDS['offer'])
        self.register(self._on_btc_offers, keywords=constants.KEYWORDS['money'])

        self.register(self._on_notify_btc_offers, keywords=constants.KEYWORDS['notify'])
        self.register(self._on_notify_btc_offers, keywords=(constants.KEYWORDS['notify'], constants.KEYWORDS['offer']))
        self.register(self._on_notify_btc_offers, keywords=(constants.KEYWORDS['notify'], constants.KEYWORDS['money']))

        self.register(self._on_stop_btc_offers_notification, keywords=(multibot_constants.KEYWORDS['deactivate'], constants.KEYWORDS['offer']))
        self.register(self._on_stop_btc_offers_notification, keywords=(multibot_constants.KEYWORDS['deactivate'], constants.KEYWORDS['money']))
        self.register(self._on_stop_btc_offers_notification, keywords=(multibot_constants.KEYWORDS['deactivate'], constants.KEYWORDS['notify']))
        self.register(self._on_stop_btc_offers_notification, keywords=(multibot_constants.KEYWORDS['deactivate'], constants.KEYWORDS['notify'], constants.KEYWORDS['offer']))
        self.register(self._on_stop_btc_offers_notification, keywords=(multibot_constants.KEYWORDS['deactivate'], constants.KEYWORDS['notify'], constants.KEYWORDS['money']))
        self.register(self._on_stop_btc_offers_notification, keywords=(multibot_constants.KEYWORDS['stop'], constants.KEYWORDS['offer']))
        self.register(self._on_stop_btc_offers_notification, keywords=(multibot_constants.KEYWORDS['stop'], constants.KEYWORDS['money']))
        self.register(self._on_stop_btc_offers_notification, keywords=(multibot_constants.KEYWORDS['stop'], constants.KEYWORDS['notify']))
        self.register(self._on_stop_btc_offers_notification, keywords=(multibot_constants.KEYWORDS['stop'], constants.KEYWORDS['notify'], constants.KEYWORDS['offer']))
        self.register(self._on_stop_btc_offers_notification, keywords=(multibot_constants.KEYWORDS['stop'], constants.KEYWORDS['notify'], constants.KEYWORDS['money']))

    async def _cancel_btc_offers_notifications_task(self) -> None:
        if self._btc_offers_notifications_task and not self._btc_offers_notifications_task.done():
            self._btc_offers_notifications_task.cancel()
            await asyncio.sleep(0)

    def _find_chats_to_notify(self) -> list[Chat]:
        return self.Chat.find({'platform': self.platform.value, 'btc_offers.query': {'$exists': True, '$ne': {}}})

    @staticmethod
    def _find_exchanges(text: str) -> list[Exchange]:
        exchanges = []
        normalized_text = flanautils.remove_accents(text.lower())

        for exchange, exchange_keywords in constants.KEYWORDS['btc_offers_exchanges'].items():
            for exchange_keyword in exchange_keywords:
                if flanautils.cartesian_product_string_matching(
                    normalized_text,
                    exchange_keyword,
                    multibot_constants.PARSER_MIN_SCORE_DEFAULT
                ):
                    exchanges.append(exchange)
                    break

        return exchanges

    @staticmethod
    def _generate_ngrams(text: str, max_n: int) -> defaultdict[int, set[str]]:
        ngrams = defaultdict(set)

        words = text.split()

        for n in range(1, max_n + 1):
            n_ngrams = set()

            for i in range(len(words) - n + 1):
                n_ngrams.add(' '.join(words[i:i + n]))

            if n_ngrams:
                ngrams[n] = n_ngrams

        return ngrams

    @staticmethod
    def _normalize_text(text: str) -> str:
        return ' '.join(
            ''.join(
                character if character.isalnum() or character.isspace() else ' '
                for character in flanautils.remove_accents(text.lower(), lazy=True)
            ).split()
        )

    def _find_payment_methods(self, text: str) -> list[PaymentMethod]:
        normalized_text = self._normalize_text(text)
        text_ngrams = self._generate_ngrams(normalized_text, self._payment_method_keyword_max_words)
        payment_methods = []

        for payment_method, payment_method_keywords_groups in self._payment_methods_keywords_groups.items():
            for group_word_count, payment_method_keywords_group in payment_method_keywords_groups:
                for payment_method_keyword in payment_method_keywords_group:
                    for text_ngram in text_ngrams[group_word_count]:
                        if flanautils.cartesian_product_string_matching(
                            (payment_method_keyword,),
                            (text_ngram,),
                            min_score=multibot_constants.PARSER_MIN_SCORE_DEFAULT
                        ):
                            if payment_method not in payment_methods:
                                payment_methods.append(payment_method)

                            normalized_text = normalized_text.replace(text_ngram, '')
                            text_ngrams = self._generate_ngrams(normalized_text, self._payment_method_keyword_max_words)

        return payment_methods

    def _is_websocket_connected(self) -> bool:
        return (
            self._btc_offers_websocket
            and
            self._btc_offers_websocket.state in {websockets.State.CONNECTING, websockets.State.OPEN}
        )

    async def _send_blocked_authors(self, chat: Chat) -> None:
        if chat.btc_offers['blocked_authors']:
            text = '\n'.join(
                (
                    '<b>🚫 Autores de ofertas BTC bloqueados:</b>',
                    '',
                    *(
                        f'<code>{i}. {author}</code>'
                        for i, author in enumerate(sorted(chat.btc_offers['blocked_authors']), start=1)
                    )
                )
            )
        else:
            text = '🟢 No hay autores de ofertas BTC bloqueados.'

        await self.send(text, chat)

    async def _send_btc_offers(
        self,
        dated_offers: DatedOffers,
        chat: Chat,
        notifications_disabled: bool = False
    ) -> None:
        offers_parts = []

        for i, offer in enumerate(dated_offers.offers, start=1):
            offer_parts = [
                f'<b>{i}.</b>',
                f'<b>Plataforma:</b> <code>{offer['exchange']}</code>',
                f'<b>Id:</b> <code>{offer['id']}</code>'
            ]

            payment_methods_text = ''.join(
                f'\n    <code>{payment_method}</code>' for payment_method in offer['payment_methods']
            )

            offer_parts.extend(
                (
                    f'<b>Cantidad:</b> <code>{offer['amount']}</code>',
                    f'<b>Precio (EUR):</b> <code>{offer['price_eur']:.2f} €</code>',
                    f'<b>Precio (USD):</b> <code>{offer['price_usd']:.2f} $</code>',
                    f'<b>Prima:</b> <code>{flanautils.format_decimal(offer['premium'], decimals=2)} %</code>',
                    f'<b>Métodos de pago:</b>{payment_methods_text}'
                )
            )

            if offer['author']:
                offer_parts.append(f'<b>Autor:</b> <code>{offer['author']}</code>')

            if offer['trades'] is not None:
                offer_parts.append(f'<b>Nº de operaciones:</b> <code>{offer['trades']}</code>')

            if offer['rating'] is not None:
                offer_parts.append(
                    f'<b>Valoración:</b> <code>{flanautils.format_decimal(offer['rating'] * 100, decimals=2)} %</code>'
                )

            if offer['url']:
                offer_parts.append(f'<b>Url:</b> {offer['url']}')

            if offer['description']:
                offer_parts.append(f'<b>Descripción:</b>\n<blockquote>{offer['description']}</blockquote>')

            offers_parts.append(offer_parts)

        if dated_offers.updated_at:
            elapsed_time = datetime.datetime.now(datetime.UTC) - dated_offers.updated_at
            elapsed_seconds = int(elapsed_time.total_seconds())
            elapsed_minutes = int(elapsed_seconds / 60)
            elapsed_hours = int(elapsed_minutes / 60)

            if elapsed_time.days > 0:
                time_unit_description = f'{elapsed_time.days} d'
            elif elapsed_hours > 0:
                time_unit_description = f'{elapsed_hours} h'
            elif elapsed_minutes > 0:
                time_unit_description = f'{elapsed_minutes} m'
            else:
                time_unit_description = f'{elapsed_seconds} s'

            elapsed_time_description = f'· hace {time_unit_description}'
        else:
            elapsed_time_description = ''

        message_data = {'btc_offers': True}

        await self.send(f'<b>💰💰💰 OFERTAS BTC 💰💰💰</b>{elapsed_time_description}', chat, data=message_data)

        for offer_parts in offers_parts:
            await self.send('\n'.join(offer_parts), chat, data=message_data, enable_link_previews=False)

        if notifications_disabled:
            await self.send(
                f'{'-' * 70}\n'
                '<b>ℹ️ Los avisos de ofertas BTC se han eliminado. Si quieres volver a recibirlos, no dudes en pedírmelo.</b>',
                chat,
                data=message_data
            )

    async def _wait_btc_offers_notification(self) -> None:
        while True:
            while True:
                try:
                    data = json.loads(await self._btc_offers_websocket.recv())
                except websockets.ConnectionClosed:
                    await self.start_all_btc_offers_notifications()
                else:
                    break

            chat = await self.get_chat(data['chat_id'])
            chat.pull_from_database(overwrite_fields=('btc_offers',))
            chat.btc_offers['query'] = {}
            chat.save()

            await self._send_offers(DatedOffers.from_dict(data['dated_offers']), chat, notifications_disabled=True)

    # ---------------------------------------------- #
    #                    HANDLERS                    #
    # ---------------------------------------------- #
    async def _on_block_authors(self, message: Message, delete: bool = False) -> None:
        if message.chat.is_group and not self.is_bot_mentioned(message):
            return

        authors = {
            word
            for word in await self.filter_mention_ids(message.text, message, delete_names=True)
            if not flanautils.cartesian_product_string_matching(
                word.lower(),
                (
                    *multibot_constants.KEYWORDS['user'],
                    *multibot_constants.KEYWORDS['block'],
                    *multibot_constants.KEYWORDS['ignore'],
                    *constants.KEYWORDS['offer'],
                    *constants.KEYWORDS['money']
                ),
                multibot_constants.PARSER_MIN_SCORE_DEFAULT
            )
        }

        chat = message.chat

        if authors:
            if delete:
                chat.btc_offers['blocked_authors'] = tuple(set(chat.btc_offers['blocked_authors']) - authors)
            else:
                chat.btc_offers['blocked_authors'] = tuple(set(chat.btc_offers['blocked_authors']) | authors)

            chat.save()

        await self._send_blocked_authors(chat)

    @preprocess_btc_offers
    async def _on_btc_offers(self, message: Message, query: dict[str, float | list[str]]) -> None:
        bot_state_message = await self.send('Obteniendo ofertas BTC...', message)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://{self._btc_offers_api_endpoint}', params=query) as response:
                    dated_offers = DatedOffers.from_dict(await response.json())
        except aiohttp.ClientConnectorError:
            await self.send_error('❌🌐 El servidor de ofertas BTC no está disponible.', bot_state_message, edit=True)
            return

        if dated_offers:
            await self._send_offers(dated_offers, message.chat)
            await self.delete_message(bot_state_message)
        else:
            await self.edit('ℹ️🔍 No hay ofertas BTC actualmente que cumplan esa condición.', bot_state_message)

    @preprocess_btc_offers
    async def _on_notify_btc_offers(self, message: Message, query: dict[str, float | list[str]]) -> None:
        options_parts = []

        if 'exchanges' in query:
            options_parts.append(f'de {flanautils.join_last_separator(query['exchanges'], ', ', ' y ')}')

        if 'payment_methods' in query:
            options_parts.append(f'con {flanautils.join_last_separator(query['payment_methods'], ', ', ' y ')}')

        match query:
            case {'max_price_eur': max_price_eur}:
                options_parts.append(f'por {max_price_eur:.2f} € o menos')
            case {'max_price_usd': max_price_usd}:
                options_parts.append(f'por {max_price_usd:.2f} $ o menos')
            case {'max_premium': max_premium}:
                options_parts.append(
                    f'con una prima del {flanautils.format_decimal(max_premium, decimals=2)} % o menor'
                )
            case _:
                await self.send_error('❌ Especifica una cantidad para poder avisarte.', message)
                return

        if len(options_parts) == 1:
            options_text = f' {options_parts[0]}.'
        else:
            options_text = f'\n- {'\n- '.join(options_parts)}'

        await self.send(f'✅ ¡Perfecto! Te avisaré cuando existan ofertas{options_text}', message)
        await self.start_btc_offers_notification(message.chat, query)

    async def _on_ready(self) -> None:
        await super()._on_ready()
        asyncio.create_task(self.start_all_btc_offers_notifications())

    async def _on_stop_btc_offers_notification(self, message: Message) -> None:
        if message.chat.is_group and not self.is_bot_mentioned(message):
            return

        previous_btc_offers_query = message.chat.btc_offers['query']

        await self.stop_btc_offers_notification(message.chat)

        if previous_btc_offers_query:
            await self.send('🛑 Los avisos de ofertas BTC se han eliminado.', message)
        else:
            await self.send('🤔 No existía ningún aviso de ofertas BTC configurado.', message)

    # -------------------------------------------------------- #
    # -------------------- PUBLIC METHODS -------------------- #
    # -------------------------------------------------------- #
    async def start_all_btc_offers_notifications(self) -> None:
        if chats := self._find_chats_to_notify():
            for chat in chats:
                await self.start_btc_offers_notification(chat, chat.btc_offers['query'])
        else:
            await self._cancel_btc_offers_notifications_task()

    async def start_btc_offers_notification(self, chat: Chat, query: dict[str, float | list[str]]) -> None:
        chat.btc_offers['query'] = query
        chat.save()

        async with self._btc_offers_lock:
            if not self._is_websocket_connected():
                while True:
                    try:
                        self._btc_offers_websocket = await websockets.connect(
                            f'ws://{self._btc_offers_api_endpoint}/ws/notifications'
                        )
                    except ConnectionRefusedError:
                        await asyncio.sleep(constants.BTC_OFFERS_WEBSOCKET_RETRY_DELAY_SECONDS)
                    else:
                        break

        if not self._btc_offers_notifications_task or self._btc_offers_notifications_task.done():
            self._btc_offers_notifications_task = asyncio.create_task(self._wait_btc_offers_notification())

        await self._btc_offers_websocket.send(json.dumps({'action': 'start', 'chat_id': chat.id, 'query': query}))

    async def stop_all_btc_offers_notification(self) -> None:
        for chat in self._find_chats_to_notify():
            await self.stop_btc_offers_notification(chat)

        await self._cancel_btc_offers_notifications_task()

    async def stop_btc_offers_notification(self, chat: Chat) -> None:
        if self._is_websocket_connected():
            await self._btc_offers_websocket.send(json.dumps({'action': 'stop', 'chat_id': chat.id}))

        chat.btc_offers['query'] = {}
        chat.save()
