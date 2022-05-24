import asyncio
import os

import discord
from multibot import BadRoleError, DiscordBot, User

from flanabot import constants
from flanabot.bots.flana_bot import FlanaBot
from flanabot.models import Chat, Punishment

HEAT_NAMES = [
    'Canal Congelado',
    'Canal Fresquito',
    'Canal Templaillo',
    'Canal Calentito',
    'Canal Caloret',
    'Canal Caliente',
    'Canal Olor a Vasco',
    'Verano Cordobés al Sol',
    'Canal Ardiendo',
    'abrid las putas ventanas y traed el extintor',
    'Canal INFIERNO'
]
HOT_CHANNEL_ID = 493530483045564417


# ---------------------------------------------------------------------------------------------------- #
# ------------------------------------------ FLANA_DISC_BOT ------------------------------------------ #
# ---------------------------------------------------------------------------------------------------- #
class FlanaDiscBot(DiscordBot, FlanaBot):
    def __init__(self):
        super().__init__(os.environ['DISCORD_BOT_TOKEN'])
        self.heating = False
        self.heat_level = 0

    # ----------------------------------------------------------- #
    # -------------------- PROTECTED METHODS -------------------- #
    # ----------------------------------------------------------- #
    def _add_handlers(self):
        super()._add_handlers()
        self.bot_client.add_listener(self._on_voice_state_update, 'on_voice_state_update')

    async def _heat_channel(self, channel: discord.VoiceChannel):
        while True:
            await asyncio.sleep(constants.HEAT_PERIOD_SECONDS)

            if channel.members:
                if self.heat_level == len(HEAT_NAMES) - 1:
                    return
                self.heat_level += 0.5
            elif not channel.members:
                if not self.heat_level:
                    return
                self.heat_level -= 0.5
            else:
                continue

            await channel.edit(name=HEAT_NAMES[int(self.heat_level)])

    async def _punish(self, user: int | str | User, group_: int | str | Chat):
        user_id = self._get_user_id(user)
        try:
            await self.add_role(user_id, group_, 'Castigado')
            await self.remove_role(user_id, group_, 'Persona')
        except AttributeError:
            raise BadRoleError(str(self._punish))

    async def _unpunish(self, user: int | str | User, group_: int | str | Chat):
        user_id = self._get_user_id(user)
        try:
            await self.add_role(user_id, group_, 'Persona')
            await self.remove_role(user_id, group_, 'Castigado')
        except AttributeError:
            raise BadRoleError(str(self._unpunish))

    # ---------------------------------------------- #
    #                    HANDLERS                    #
    # ---------------------------------------------- #
    async def _on_voice_state_update(self, _: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if getattr(before.channel, 'id', None) == HOT_CHANNEL_ID:
            channel = before.channel
        elif getattr(after.channel, 'id', None) == HOT_CHANNEL_ID:
            channel = after.channel
        else:
            return

        if not self.heating:
            self.heating = True
            await self._heat_channel(channel)
            self.heating = False

    # -------------------------------------------------------- #
    # -------------------- PUBLIC METHODS -------------------- #
    # -------------------------------------------------------- #
    async def is_punished(self, user: int | str | User, group_: int | str | Chat):
        user = await self.get_user(user, group_)
        group_id = self._get_group_id(group_)
        return group_id in {punishment.group_id for punishment in Punishment.find({
            'platform': self.bot_platform.value,
            'user_id': user.id,
            'group_id': group_id,
            'is_active': True
        })}
