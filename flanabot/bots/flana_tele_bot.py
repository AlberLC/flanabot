from __future__ import annotations  # todo0 remove in 3.11

import functools
import os
from typing import Callable

import telethon.tl.functions
from flanaapis.weather.constants import WeatherEmoji
from flanautils import Media, MediaType, return_if_first_empty
from multibot import TelegramBot, constants as multibot_constants, find_message, user_client

from flanabot.bots.flana_bot import FlanaBot
from flanabot.models.chat import Chat
from flanabot.models.message import Message
from flanabot.models.user import User


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
    def _add_handlers(self):
        super()._add_handlers()
        self.register_button(self._on_button_press)

    @return_if_first_empty(exclude_self_types='FlanaTeleBot', globals_=globals())
    async def _create_chat_from_telegram_chat(self, telegram_chat: multibot_constants.TELEGRAM_CHAT) -> Chat | None:
        chat = await super()._create_chat_from_telegram_chat(telegram_chat)
        chat.config = Chat.DEFAULT_CONFIG
        return Chat.from_dict(chat.to_dict())

    @return_if_first_empty(exclude_self_types='FlanaTeleBot', globals_=globals())
    async def _create_user_from_telegram_user(self, original_user: multibot_constants.TELEGRAM_USER, group_id: int = None) -> User | None:
        return User.from_dict((await super()._create_user_from_telegram_user(original_user, group_id)).to_dict())

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
    async def _on_button_press(self, message: Message):
        await message.original_event.answer()

        match message.button_text:
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

        message.weather_chart.apply_zoom()
        message.weather_chart.draw()
        message.save()

        image_bytes = message.weather_chart.to_image()
        file = await self._prepare_media_to_send(Media(image_bytes, MediaType.IMAGE))

        try:
            await message.original_object.edit(file=file)
        except telethon.errors.rpcerrorlist.MessageNotModifiedError:
            pass

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
