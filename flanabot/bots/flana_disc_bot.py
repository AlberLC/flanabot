import asyncio
import os

import discord
from multibot import DiscordBot

from flanabot import constants
from flanabot.bots.flana_bot import FlanaBot
from flanabot.exceptions import BadRoleError, UserDisconnectedError
from flanabot.models import User

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
    'Canal INFIERNO',
    'La Palma 🌋'
]
HOT_CHANNEL_ID = 493530483045564417
ROLES = {
    'Administrador': 387344390030360587,
    'Carroñero': 493523298429435905,
    'al lol': 881238165476741161,
    'Persona': 866046517998387220,
    'Castigado': 877662459568209921,
    'Bot': 493784221085597706
}


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

    async def _mute(self, user_id: int, group_id: int):
        user = await self.get_user(user_id, group_id)
        try:
            await user.original_object.edit(mute=True)
        except discord.errors.HTTPException:
            raise UserDisconnectedError

    async def _punish(self, user_id: int, group_id: int):
        user = await self.get_user(user_id, group_id)
        try:
            await user.original_object.remove_roles(self._find_role_by_id(ROLES['Persona'], user.original_object.guild.roles))
            await user.original_object.add_roles(self._find_role_by_id(ROLES['Castigado'], user.original_object.guild.roles))
        except AttributeError:
            raise BadRoleError(str(self._punish))

    async def _unmute(self, user_id: int, group_id: int):
        user = await self.get_user(user_id, group_id)
        try:
            await user.original_object.edit(mute=False)
        except discord.errors.HTTPException:
            raise UserDisconnectedError

    async def _unpunish(self, user_id: int, group_id: int):
        user = await self.get_user(user_id, group_id)
        try:
            await user.original_object.remove_roles(self._find_role_by_id(ROLES['Castigado'], user.original_object.guild.roles))
            await user.original_object.add_roles(self._find_role_by_id(ROLES['Persona'], user.original_object.guild.roles))
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
    async def is_deaf(self, user_id: int, group_id: int) -> bool:
        user = await self.get_user(user_id, group_id)
        return user.original_object.voice.deaf

    async def is_muted(self, user_id: int, group_id: int) -> bool:
        user = await self.get_user(user_id, group_id)
        return user.original_object.voice.mute

    @staticmethod
    def is_self_deaf(user: User) -> bool:
        return user.original_object.voice.self_deaf

    @staticmethod
    def is_self_muted(user: User) -> bool:
        return user.original_object.voice.self_mute
