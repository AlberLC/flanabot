from __future__ import annotations  # todo0 remove when it's by default

__all__ = ['BtcOffersBot']

import asyncio
import functools
import json
import os
from abc import ABC
from collections.abc import Callable

import aiohttp
import flanautils
from multibot import MultiBot, constants as multibot_constants
from websockets.asyncio import client

import constants
from flanabot.models import Chat, Message


# ---------------------------------------------------- #
# -------------------- DECORATORS -------------------- #
# ---------------------------------------------------- #
def preprocess_btc_offers(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(self: BtcOffersBot, message: Message):
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

        if parsed_number and not any((eur_mode, usd_mode, premium_mode)):
            eur_mode = True

        if eur_mode:
            query = {'max_price_eur': parsed_number}
        elif usd_mode:
            query = {'max_price_usd': parsed_number}
        elif premium_mode:
            query = {'max_premium': parsed_number}
        else:
            query = {}

        return await func(self, message, query)

    return wrapper


# ---------------------------------------------------------------------------------------------------- #
# ------------------------------------------ BTC_OFFERS_BOT ------------------------------------------ #
# ---------------------------------------------------------------------------------------------------- #
class BtcOffersBot(MultiBot, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._websocket: client.ClientConnection | None = None
        self._notification_task: asyncio.Task[None] | None = None
        self._api_endpoint = f"{os.environ['BTC_OFFERS_API_HOST']}:{os.environ['BTC_OFFERS_API_PORT']}/offers"

    # -------------------------------------------------------- #
    # ------------------- PROTECTED METHODS ------------------ #
    # -------------------------------------------------------- #
    def _add_handlers(self):
        super()._add_handlers()

        self.register(self._on_btc_offers, keywords=constants.KEYWORDS['offer'])
        self.register(self._on_btc_offers, keywords=constants.KEYWORDS['money'])
        self.register(self._on_btc_offers, keywords=(constants.KEYWORDS['offer'], constants.KEYWORDS['money']))

        self.register(self._on_notify_btc_offers, keywords=constants.KEYWORDS['notify'])
        self.register(self._on_notify_btc_offers, keywords=(constants.KEYWORDS['notify'], constants.KEYWORDS['offer']))
        self.register(self._on_notify_btc_offers, keywords=(constants.KEYWORDS['notify'], constants.KEYWORDS['money']))
        self.register(self._on_notify_btc_offers, keywords=(constants.KEYWORDS['notify'], constants.KEYWORDS['offer'], constants.KEYWORDS['money']))

        self.register(self._on_stop_btc_offers_notification, keywords=(multibot_constants.KEYWORDS['deactivate'], constants.KEYWORDS['offer']))
        self.register(self._on_stop_btc_offers_notification, keywords=(multibot_constants.KEYWORDS['deactivate'], constants.KEYWORDS['money']))
        self.register(self._on_stop_btc_offers_notification, keywords=(multibot_constants.KEYWORDS['deactivate'], constants.KEYWORDS['notify']))
        self.register(self._on_stop_btc_offers_notification, keywords=(multibot_constants.KEYWORDS['stop'], constants.KEYWORDS['offer']))
        self.register(self._on_stop_btc_offers_notification, keywords=(multibot_constants.KEYWORDS['stop'], constants.KEYWORDS['money']))
        self.register(self._on_stop_btc_offers_notification, keywords=(multibot_constants.KEYWORDS['stop'], constants.KEYWORDS['notify']))

    async def _send_offers(self, offers: list[dict], chat: Chat, notifications_disabled=False):
        offers_parts = []
        for i, offer in enumerate(offers, start=1):
            offer_parts = [
                f'<b>{i}.</b>',
                f"<b>Plataforma:</b> <code>{offer['exchange']}</code>",
                f"<b>Id:</b> <code>{offer['id']}</code>"
            ]

            if offer['author']:
                offer_parts.append(f"<b>Autor:</b> <code>{offer['author']}</code>")

            payment_methods_text = ''.join(f'\n    <code>{payment_method}</code>' for payment_method in offer['payment_methods'])

            offer_parts.extend(
                (
                    f"<b>Cantidad:</b> <code>{offer['amount']}</code>",
                    f"<b>Precio (EUR):</b> <code>{offer['price_eur']:.2f} €</code>",
                    f"<b>Precio (USD):</b> <code>{offer['price_usd']:.2f} $</code>",
                    f"<b>Prima:</b> <code>{offer['premium']:.2f} %</code>",
                    f'<b>Métodos de pago:</b>{payment_methods_text}'
                )
            )

            if offer['description']:
                offer_parts.append(f"<b>Descripción:</b>\n<code><code><code>{offer['description']}</code></code></code>")

            offers_parts.append('\n'.join(offer_parts))

        offers_parts_chunks = flanautils.chunks(offers_parts, 5)

        messages_parts = [
            [
                '<b>💰💰💰 OFERTAS BTC 💰💰💰</b>',
                '',
                '\n\n'.join(offers_parts_chunks[0])
            ]
        ]

        for offers_parts_chunk in offers_parts_chunks[1:]:
            messages_parts.append(
                [
                    '­',
                    '\n\n'.join(offers_parts_chunk)
                ]
            )

        if notifications_disabled:
            messages_parts[-1].extend(
                (
                    '',
                    '-' * 70,
                    '<b>ℹ️ Los avisos de ofertas de BTC se han desactivado. Si quieres volver a recibirlos, no dudes en pedírmelo.</b>'
                )
            )

        for message_parts in messages_parts:
            await self.send('\n'.join(message_parts), chat)

    async def _wait_btc_offers_notification(self):
        while True:
            data = json.loads(await self._websocket.recv())
            chat = await self.get_chat(data['chat_id'])
            chat.btc_offers_max_eur = None
            chat.save(pull_exclude_fields=('btc_offers_max_eur',))
            await self._send_offers(data['offers'], chat, notifications_disabled=True)

    # ---------------------------------------------- #
    #                    HANDLERS                    #
    # ---------------------------------------------- #

    @preprocess_btc_offers
    async def _on_btc_offers(self, message: Message, query: dict[str, float]):
        bot_state_message = await self.send('Obteniendo ofertas BTC...', message)

        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://{self._api_endpoint}', params=query) as response:
                offers = await response.json()

        if offers:
            await self._send_offers(offers, message.chat)
            await self.delete_message(bot_state_message)
        else:
            await self.edit('No hay ofertas BTC actualmente que cumplan esa condición.', bot_state_message)

    @preprocess_btc_offers
    async def _on_notify_btc_offers(self, message: Message, query: dict[str, float]):
        if not query:
            await self.send_error('❌ Especifica una cantidad para poder avisarte.', message)
            return

        match query:
            case {'max_price_eur': max_price_eur}:
                response_text = f'✅ ¡Perfecto! Te avisaré cuando existan ofertas por {max_price_eur:.2f} € o menos.'
            case {'max_price_usd': max_price_usd}:
                response_text = f'✅ ¡Perfecto! Te avisaré cuando existan ofertas por {max_price_usd:.2f} $ o menos.'
            case _:
                response_text = f"✅ ¡Perfecto! Te avisaré cuando existan ofertas con una prima del {query['max_premium']:.2f} % o menor."

        await self.send(response_text, message)
        await self.start_btc_offers_notification(message.chat, max_price_eur)

    async def _on_ready(self):
        await super()._on_ready()

        for chat in self.Chat.find({
            'platform': self.platform.value,
            'btc_offers_max_eur': {'$exists': True, '$ne': None}
        }):
            chat = await self.get_chat(chat.id)
            chat.pull_from_database(overwrite_fields=('_id', 'btc_offers_max_eur'))
            await self.start_btc_offers_notification(chat, chat.btc_offers_max_eur)

    async def _on_stop_btc_offers_notification(self, message: Message):
        previous_btc_offers_max_eur = message.chat.btc_offers_max_eur

        await self.stop_btc_offers_notification(message.chat)

        if previous_btc_offers_max_eur:
            await self.send('🛑 Los avisos de ofertas de BTC se han desactivado.', message)
        else:
            await self.send('🤔 No existía ningún aviso de ofertas de BTC configurado.', message)

    # -------------------------------------------------------- #
    # -------------------- PUBLIC METHODS -------------------- #
    # -------------------------------------------------------- #
    async def start_btc_offers_notification(self, chat: Chat, max_price_eur: float):
        if not self._websocket:
            self._websocket = await client.connect(f'ws://{self._api_endpoint}')
            self._notification_task = asyncio.create_task(self._wait_btc_offers_notification())

        chat.btc_offers_max_eur = max_price_eur
        chat.save()
        await self._websocket.send(json.dumps({'action': 'start', 'chat_id': chat.id, 'max_price_eur': max_price_eur}))

    async def stop_btc_offers_notification(self, chat: Chat):
        if not self._websocket:
            return

        await self._websocket.send(json.dumps({'action': 'stop', 'chat_id': chat.id}))
        chat.btc_offers_max_eur = None
        chat.save(pull_exclude_fields=('btc_offers_max_eur',))
