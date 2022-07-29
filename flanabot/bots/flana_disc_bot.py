__all__ = ['FlanaDiscBot']

import asyncio
import os
from typing import Sequence

import discord
import flanautils
from flanautils import NotFoundError
from multibot import BadRoleError, DiscordBot, Role, User, constants as multibot_constants

from flanabot import constants
from flanabot.bots.flana_bot import FlanaBot
from flanabot.models import Chat, Message, Punishment

CHANGEABLE_ROLES = {
    360868977754505217: [881238165476741161, 991454395663401072],
    862823584670285835: [976660580939202610, 984269640752590868],
}
HEAT_NAMES = [
    'Canal Congelado',
    'Canal Fresquito',
    'Canal Templaillo',
    'Canal Calentito',
    'Canal Caloret',
    'Canal Caliente',
    'Canal Olor a Vasco',
    'Canal Verano Cordobés al Sol',
    'Canal Al rojo vivo',
    'Canal Ardiendo',
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
        self.client.add_listener(self._on_member_join, 'on_member_join')
        self.client.add_listener(self._on_member_remove, 'on_member_remove')
        self.client.add_listener(self._on_voice_state_update, 'on_voice_state_update')

    async def _changeable_roles(self, group_: int | str | Chat | Message) -> list[Role]:
        group_id = self.get_group_id(group_)
        return [role for role in await self.get_group_roles(group_) if role.id in CHANGEABLE_ROLES[group_id]]

    # noinspection PyTypeChecker
    def _distribute_buttons(self, texts: Sequence[str]) -> list[list[str]]:
        if len(texts) <= multibot_constants.DISCORD_BUTTONS_MAX:
            return flanautils.chunks(texts, 1)
        else:
            return flanautils.chunks(texts, multibot_constants.DISCORD_BUTTONS_MAX)

    async def _heat_channel(self, channel: discord.VoiceChannel):
        while True:
            await asyncio.sleep(constants.HEAT_PERIOD_SECONDS)

            if channel.members:
                self.heat_level += 0.5
            else:
                if not self.heat_level:
                    return
                self.heat_level -= 0.5

            i = int(self.heat_level)
            if i < len(HEAT_NAMES):
                channel_name = HEAT_NAMES[i]
            else:
                channel_name = '🔥' * (i - len(HEAT_NAMES) + 1)
            await channel.edit(name=channel_name)

    async def _punish(self, user: int | str | User, group_: int | str | Chat | Message, message: Message = None):
        user_id = self.get_user_id(user)
        try:
            await self.add_role(user_id, group_, 'Castigado')
            await self.remove_role(user_id, group_, 'Persona')
        except AttributeError:
            raise BadRoleError(str(self._punish))

    async def _unpunish(self, user: int | str | User, group_: int | str | Chat | Message, message: Message = None):
        user_id = self.get_user_id(user)
        try:
            await self.add_role(user_id, group_, 'Persona')
            await self.remove_role(user_id, group_, 'Castigado')
        except AttributeError:
            raise BadRoleError(str(self._unpunish))

    # ---------------------------------------------- #
    #                    HANDLERS                    #
    # ---------------------------------------------- #
    async def _on_member_join(self, member: discord.Member):
        user = self._create_user_from_discord_user(member)
        user.pull_from_database(overwrite_fields=('roles',))
        for role in user.roles:
            try:
                await self.add_role(user, member.guild.id, role.id)
            except NotFoundError:
                pass

    async def _on_member_remove(self, member: discord.Member):
        self._create_user_from_discord_user(member).save()

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
    async def is_punished(self, user: int | str | User, group_: int | str | Chat | Message):
        user = await self.get_user(user, group_)
        group_id = self.get_group_id(group_)
        return group_id in {punishment.group_id for punishment in Punishment.find({
            'platform': self.platform.value,
            'user_id': user.id,
            'group_id': group_id,
            'is_active': True
        })}
