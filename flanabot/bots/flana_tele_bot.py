from __future__ import annotations  # todo0 remove in 3.11

import functools
import os
from typing import Callable

import telethon.tl.functions
from multibot import TelegramBot, find_message, user_client

from flanabot.bots.flana_bot import FlanaBot
from flanabot.models import Message


# ---------------------------------------------------------- #
# ----------------------- DECORATORS ----------------------- #
# ---------------------------------------------------------- #


def whitelisted_event(func: Callable) -> Callable:
    @functools.wraps(func)
    @find_message
    async def wrapper(self: FlanaTeleBot, message: Message):
        if message.author.id not in self.whitelist_ids:
            return

        return await func(self, message)

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
        self.whitelist_ids = []

    # ----------------------------------------------------------- #
    # -------------------- PROTECTED METHODS -------------------- #
    # ----------------------------------------------------------- #
    @user_client
    async def _get_contacts_ids(self) -> list[int]:
        async with self.user_client:
            contacts_data = await self.user_client(telethon.tl.functions.contacts.GetContactsRequest(hash=0))

        return [contact.user_id for contact in contacts_data.contacts]

    @user_client
    async def _update_whitelist(self):
        self.whitelist_ids = [self.owner_id, self.bot_id] + await self._get_contacts_ids()

    # ---------------------------------------------- #
    #                    HANDLERS                    #
    # ---------------------------------------------- #
    @whitelisted_event
    async def _on_inline_query_raw(self, message: Message):
        await super()._on_new_message_raw(message)

    @whitelisted_event
    async def _on_new_message_raw(self, message: Message):
        await super()._on_new_message_raw(message)

    async def _on_ready(self):
        await super()._on_ready()
        await self._update_whitelist()

    # -------------------------------------------------------- #
    # -------------------- PUBLIC METHODS -------------------- #
    # -------------------------------------------------------- #
