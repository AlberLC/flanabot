__all__ = ['whitelisted', 'FlanaTeleBot']

import asyncio
import functools
import os
from collections.abc import Iterable
from typing import Any, Callable

import aiohttp
import telethon.tl.functions
from flanautils import Media, OrderedSet
from multibot import RegisteredCallback, TelegramBot, find_message, use_user_client, user_client

from flanabot import constants
from flanabot.bots.flana_bot import FlanaBot
from flanabot.models import Chat, Message


# ---------------------------------------------------- #
# -------------------- DECORATORS -------------------- #
# ---------------------------------------------------- #
def whitelisted(func: Callable) -> Callable:
    @functools.wraps(func)
    @find_message
    async def wrapper(self: FlanaTeleBot, message: Message, *args, **kwargs) -> Any:
        if message.author.id not in self.whitelist_ids:
            return

        return await func(self, message, *args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------------------------------------- #
# ------------------------------------------ FLANA_TELE_BOT ------------------------------------------ #
# ---------------------------------------------------------------------------------------------------- #
class FlanaTeleBot(TelegramBot, FlanaBot):
    def __init__(self):
        super().__init__(
            api_id=os.environ['TELEGRAM_API_ID'],
            api_hash=os.environ['TELEGRAM_API_HASH'],
            bot_session=os.environ['TELEGRAM_BOT_SESSION'],
            user_session=os.environ['TELEGRAM_USER_SESSION']
        )
        self._client_connections_checker_task: asyncio.Task[None] | None = None
        self.whitelist_ids = []

    # -------------------------------------------------------- #
    # ------------------- PROTECTED METHODS ------------------ #
    # -------------------------------------------------------- #
    async def _check_new_client_connections(
        self,
        session: aiohttp.ClientSession,
        latest_client_connections_endpoint: str,
        headers: dict[str, str],
        latest_client_connection_id: str
    ) -> str | None:
        try:
            async with session.get(
                latest_client_connections_endpoint,
                params={'after_id': latest_client_connection_id} if latest_client_connection_id else None,
                headers=headers
            ) as response:
                response.raise_for_status()
                client_connections = await response.json()
        except aiohttp.ClientConnectorError, aiohttp.ClientResponseError:
            pass
        else:
            if client_connections:
                await self._send_client_connections(client_connections)
                return client_connections[0]['_id']

        return latest_client_connection_id

    async def _get_config_names(self, message: Message) -> list[str]:
        config_names = await super()._get_config_names(message)

        if message.chat == await self.owner_chat:
            config_names.append('client_connection_notifications')

        return sorted(config_names)

    @user_client
    async def _get_contacts_ids(self) -> list[int]:
        async with use_user_client(self):
            contacts_data = await self.user_client(telethon.tl.functions.contacts.GetContactsRequest(hash=0))

        return [contact.user_id for contact in contacts_data.contacts]

    async def _handle_config_change(self, config_name: str, message: Message) -> str:
        if config_name == 'client_connection_notifications':
            if message.chat.config[config_name]:
                await self.start_client_connections_checker(message.chat)
            else:
                await self.stop_client_connections_checker(message.chat)

            return config_name
        else:
            return await super()._handle_config_change(config_name, message)

    async def _run_client_connections_checker(self) -> None:
        latest_client_connections_endpoint = f'{self._flanaserver_api_base_url}/flanacs/client-connections/latest'
        headers = {'Authorization': f'Bearer {os.environ['FLANASERVER_API_TOKEN']}'}

        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    async with session.get(
                        latest_client_connections_endpoint,
                        params={'limit': 1},
                        headers=headers
                    ) as response:
                        if response.ok:
                            if latest_client_connections := await response.json():
                                latest_client_connection_id = latest_client_connections[0]['_id']
                            else:
                                latest_client_connection_id = None

                            break
                except aiohttp.ClientConnectorError:
                    pass

                await asyncio.sleep(constants.CHECK_CLIENT_CONNECTIONS_EVERY_SECONDS)

            while True:
                latest_client_connection_id = await self._check_new_client_connections(
                    session,
                    latest_client_connections_endpoint,
                    headers,
                    latest_client_connection_id
                )

                await asyncio.sleep(constants.CHECK_CLIENT_CONNECTIONS_EVERY_SECONDS)

    async def _search_medias(
        self,
        message: Message,
        force=False,
        audio_only=False,
        timeout_for_media: int | float = constants.SCRAPING_TIMEOUT_SECONDS
    ) -> OrderedSet[Media]:
        return await super()._search_medias(message, force, audio_only, timeout_for_media)

    async def _send_client_connections(self, client_connections: Iterable[dict[str, Any]]) -> None:
        for client_connection in client_connections:
            geojs_data = client_connection.get('geojs') or {}
            ip_geolocation_data = client_connection.get('ip_geolocation') or {}

            await self.send(
                '<b>FlanaCS client connection:</b>\n'
                '\n'
                f'<b>username:</b> <code>{client_connection.get('username')}</code>\n'
                f'<b>hostname:</b> <code>{client_connection.get('hostname')}</code>\n'
                f'<b>mac_address:</b> <code>{client_connection.get('mac_address')}</code>\n'
                f'<b>ip:</b> <code>{client_connection.get('ip')}</code>\n'
                '<b>geojs:</b>\n'
                f'<b>    country:</b> <code>{geojs_data.get('country')}</code>\n'
                f'<b>    region:</b> <code>{geojs_data.get('region')}</code>\n'
                f'<b>    city:</b> <code>{geojs_data.get('city')}</code>\n'
                '<b>ip_geolocation:</b>\n'
                f'<b>    country:</b> <code>{ip_geolocation_data.get('country')}</code>\n'
                f'<b>    state_province:</b> <code>{ip_geolocation_data.get('state_province')}</code>\n'
                f'<b>    district:</b> <code>{ip_geolocation_data.get('district')}</code>\n'
                f'<b>    city:</b> <code>{ip_geolocation_data.get('city')}</code>\n',
                await self.owner_chat,
                silent=True
            )

    @user_client
    async def _update_whitelist(self):
        self.whitelist_ids = [self.owner_id, self.id] + await self._get_contacts_ids()

    # ---------------------------------------------- #
    #                    HANDLERS                    #
    # ---------------------------------------------- #
    @whitelisted
    async def _on_inline_query_raw(self, message: Message):
        await super()._on_inline_query_raw(message)

    @whitelisted
    async def _on_new_message_raw(
        self,
        message: Message,
        whitelist_callbacks: set[RegisteredCallback] | None = None,
        blacklist_callbacks: set[RegisteredCallback] | None = None
    ):
        await super()._on_new_message_raw(message, whitelist_callbacks, blacklist_callbacks)

    async def _on_ready(self):
        await super()._on_ready()
        await self._update_whitelist()

        if (await self.owner_chat).config['client_connection_notifications']:
            await self.start_client_connections_checker(await self.owner_chat)

    # -------------------------------------------------------- #
    # -------------------- PUBLIC METHODS -------------------- #
    # -------------------------------------------------------- #
    async def start_client_connections_checker(self, chat: Chat) -> None:
        await self.stop_client_connections_checker(chat)

        self._client_connections_checker_task = asyncio.create_task(self._run_client_connections_checker())
        chat.config['client_connection_notifications'] = True
        chat.save()

    async def stop_client_connections_checker(self, chat: Chat) -> None:
        if self._client_connections_checker_task and not self._client_connections_checker_task.done():
            self._client_connections_checker_task.cancel()

        chat.config['client_connection_notifications'] = False
        chat.save()
