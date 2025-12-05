from __future__ import annotations  # todo0 remove when it's by default

__all__ = ['BtcOffersBot']

import asyncio
import datetime
import functools
import json
import os
from abc import ABC
from collections.abc import Awaitable, Callable

import aiohttp
import flanautils
import websockets
from multibot import MultiBot, constants as multibot_constants

from flanabot import constants
from flanabot.models import Chat, Message
from models.offers_data import OffersData


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

        parsed_number = flanautils.text_to_number(message.text)

        if not premium_mode and parsed_number < 0 or not flanautils.validate_mongodb_number(parsed_number):
            await self.send_error('❌ Por favor, introduce un número válido.', message)
            return

        if eur_mode:
            query = {'max_price_eur': parsed_number}
        elif usd_mode:
            query = {'max_price_usd': parsed_number}
        elif premium_mode:
            query = {'max_premium': parsed_number}
        else:
            query = {'limit': parsed_number if parsed_number else constants.BTC_OFFERS_DEFAULT_LIMIT}

        query['ignore_authors'] = message.chat.btc_offers['blocked_authors']

        await func(self, message, query)

    return wrapper


# ---------------------------------------------------------------------------------------------------- #
# ------------------------------------------ BTC_OFFERS_BOT ------------------------------------------ #
# ---------------------------------------------------------------------------------------------------- #
class BtcOffersBot(MultiBot, ABC):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._websocket: websockets.ClientConnection | None = None
        self._notification_task: asyncio.Task[None] | None = None
        self._api_endpoint = f"{os.environ['BTC_OFFERS_API_HOST']}:{os.environ['BTC_OFFERS_API_PORT']}/offers"
        self._websocket_lock = asyncio.Lock()

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

    def _find_chats_to_notify(self) -> list[Chat]:
        return self.Chat.find({'platform': self.platform.value, 'btc_offers.query': {'$exists': True, '$ne': {}}})

    def _is_websocket_connected(self) -> bool:
        return self._websocket and self._websocket.state in {websockets.State.CONNECTING, websockets.State.OPEN}

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

    async def _send_offers(self, offers_data: OffersData, chat: Chat, notifications_disabled: bool = False) -> None:
        offers_parts = []

        for i, offer in enumerate(offers_data.offers, start=1):
            offer_parts = [
                f'<b>{i}.</b>',
                f"<b>Plataforma:</b> <code>{offer['exchange']}</code>",
                f"<b>Id:</b> <code>{offer['id']}</code>"
            ]

            if offer['author']:
                offer_parts.append(f"<b>Autor:</b> <code>{offer['author']}</code>")

            payment_methods_text = ''.join(
                f'\n    <code>{payment_method}</code>' for payment_method in offer['payment_methods']
            )

            rounded_premium = round(offer['premium'], 2)
            offer_parts.extend(
                (
                    f"<b>Cantidad:</b> <code>{offer['amount']}</code>",
                    f"<b>Precio (EUR):</b> <code>{offer['price_eur']:.2f} €</code>",
                    f"<b>Precio (USD):</b> <code>{offer['price_usd']:.2f} $</code>",
                    f"<b>Prima:</b> <code>{rounded_premium if rounded_premium else '0.00'} %</code>",
                    f'<b>Métodos de pago:</b>{payment_methods_text}'
                )
            )

            if offer['description']:
                offer_parts.append(
                    f"<b>Descripción:</b>\n<code><code><code>{offer['description']}</code></code></code>"
                )

            offers_parts.append(offer_parts)

        elapsed_time = datetime.datetime.now(datetime.UTC) - offers_data.updated_at
        elapsed_seconds = elapsed_time.total_seconds()
        elapsed_minutes = elapsed_seconds / 60
        elapsed_hours = elapsed_minutes / 60

        if elapsed_time.days > 0:
            elapsed_time_description = f'{elapsed_time.days} d'
        elif (elapsed_hours := int(elapsed_hours)) > 0:
            elapsed_time_description = f'{elapsed_hours} h'
        elif (elapsed_minutes := int(elapsed_minutes)) > 0:
            elapsed_time_description = f'{elapsed_minutes} m'
        else:
            elapsed_time_description = f'{int(elapsed_seconds)} s'

        await self.send(f'<b>💰💰💰 OFERTAS BTC 💰💰💰</b> · hace {elapsed_time_description}', chat)

        for offer_parts in offers_parts:
            await self.send('\n'.join(offer_parts), chat)

        if notifications_disabled:
            await self.send(
                f"{'-' * 70}\n"
                '<b>ℹ️ Los avisos de ofertas BTC se han eliminado. Si quieres volver a recibirlos, no dudes en pedírmelo.</b>',
                chat
            )

    async def _wait_btc_offers_notification(self) -> None:
        while True:
            while True:
                try:
                    data = json.loads(await self._websocket.recv())
                except websockets.ConnectionClosed:
                    await self.start_all_btc_offers_notifications()
                else:
                    break

            chat = await self.get_chat(data['chat_id'])
            chat.pull_from_database(overwrite_fields=('btc_offers',))
            chat.btc_offers['query'] = {}
            chat.save()

            await self._send_offers(OffersData.from_dict(data['offers_data']), chat, notifications_disabled=True)

    # ---------------------------------------------- #
    #                    HANDLERS                    #
    # ---------------------------------------------- #
    async def _on_block_authors(self, message: Message, delete: bool = False) -> None:
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
    async def _on_btc_offers(self, message: Message, query: dict[str, float]) -> None:
        bot_state_message = await self.send('Obteniendo ofertas BTC...', message)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://{self._api_endpoint}', params=query) as response:
                    offers_data = await response.json()
        except aiohttp.ClientConnectorError:
            await self.send_error('❌🌐 El servidor de ofertas BTC está desconectado.', bot_state_message, edit=True)
            return

        if offers_data:
            await self._send_offers(OffersData.from_dict(offers_data), message.chat)
            await self.delete_message(bot_state_message)
        else:
            await self.edit('No hay ofertas BTC actualmente que cumplan esa condición.', bot_state_message)

    @preprocess_btc_offers
    async def _on_notify_btc_offers(self, message: Message, query: dict[str, float]) -> None:
        match query:
            case {'max_price_eur': max_price_eur}:
                response_text = f'✅ ¡Perfecto! Te avisaré cuando existan ofertas por {max_price_eur:.2f} € o menos.'
            case {'max_price_usd': max_price_usd}:
                response_text = f'✅ ¡Perfecto! Te avisaré cuando existan ofertas por {max_price_usd:.2f} $ o menos.'
            case {'max_premium': max_premium}:
                rounded_max_premium = round(max_premium, 2)
                response_text = f"✅ ¡Perfecto! Te avisaré cuando existan ofertas con una prima del {rounded_max_premium if rounded_max_premium else '0.00'} % o menor."
            case _:
                await self.send_error('❌ Especifica una cantidad para poder avisarte.', message)
                return

        await self.send(response_text, message)
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
        elif self._notification_task and not self._notification_task.done():
            self._notification_task.cancel()
            await asyncio.sleep(0)

    async def start_btc_offers_notification(self, chat: Chat, query: dict[str, float]) -> None:
        async with self._websocket_lock:
            if not self._is_websocket_connected():
                while True:
                    try:
                        self._websocket = await websockets.connect(f'ws://{self._api_endpoint}')
                    except ConnectionRefusedError:
                        await asyncio.sleep(constants.BTC_OFFERS_WEBSOCKET_RETRY_DELAY_SECONDS)
                    else:
                        break

        if not self._notification_task or self._notification_task.done():
            self._notification_task = asyncio.create_task(self._wait_btc_offers_notification())

        chat.btc_offers['query'] = query
        chat.save()
        await self._websocket.send(json.dumps({'action': 'start', 'chat_id': chat.id, 'query': query}))

    async def stop_all_btc_offers_notification(self) -> None:
        for chat in self._find_chats_to_notify():
            await self.stop_btc_offers_notification(chat)

    async def stop_btc_offers_notification(self, chat: Chat) -> None:
        if self._is_websocket_connected():
            await self._websocket.send(json.dumps({'action': 'stop', 'chat_id': chat.id}))

        chat.btc_offers['query'] = {}
        chat.save()
