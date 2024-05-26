__all__ = ['FlanaDiscBot']

import asyncio
import datetime
import math
import os
import random
from collections import defaultdict

import discord
import pytz
from flanautils import Media, NotFoundError, OrderedSet
from multibot import BadRoleError, DiscordBot, Platform, Role, User, admin, bot_mentioned, constants as multibot_constants, group

from flanabot import constants
from flanabot.bots.flana_bot import FlanaBot
from flanabot.models import Chat, Message, Punishment
from models.heating_context import ChannelData, HeatingContext


# ---------------------------------------------------------------------------------------------------- #
# ------------------------------------------ FLANA_DISC_BOT ------------------------------------------ #
# ---------------------------------------------------------------------------------------------------- #
class FlanaDiscBot(DiscordBot, FlanaBot):
    def __init__(self):
        super().__init__(os.environ['DISCORD_BOT_TOKEN'])
        self.heating_contexts: dict[int, HeatingContext] = defaultdict(HeatingContext)

    # -------------------------------------------------------- #
    # ------------------- PROTECTED METHODS ------------------ #
    # -------------------------------------------------------- #
    def _add_handlers(self):
        super()._add_handlers()
        self.client.add_listener(self._on_member_join, 'on_member_join')
        self.client.add_listener(self._on_member_remove, 'on_member_remove')
        self.client.add_listener(self._on_voice_state_update, 'on_voice_state_update')

        self.register(self._on_audit_log, keywords=multibot_constants.KEYWORDS['audit'])
        self.register(self._on_restore_channel_names, keywords=(multibot_constants.KEYWORDS['reset'], multibot_constants.KEYWORDS['chat']))

    async def _changeable_roles(self, group_: int | str | Chat | Message) -> list[Role]:
        group_roles = await self.get_group_roles(group_)
        group_id = self.get_group_id(group_)
        return [role for role in group_roles if role.id in constants.CHANGEABLE_ROLES[Platform.DISCORD][group_id]]

    async def _heat_channel(self, channel: discord.VoiceChannel):
        async def set_fire_to(channel_key: str, depends_on: str, firewall=0):
            fire_score = random.randint(0, channels_data[depends_on].n_fires - channels_data[channel_key].n_fires) - firewall // 2
            if fire_score < 1:
                if not channels_data[channel_key].n_fires:
                    return
                channels_data[channel_key].n_fires -= 1
            elif fire_score == 1:
                return
            else:
                channels_data[channel_key].n_fires += 1

            if channels_data[channel_key].n_fires:
                new_name_ = '🔥' * channels_data[channel_key].n_fires
            else:
                new_name_ = channels_data[channel_key].original_name
            await channels_data[channel_key].channel.edit(name=new_name_)

        voice_channels = {}
        for voice_channel in channel.guild.voice_channels:
            voice_channels[voice_channel.id] = voice_channel

        channels_data = {}
        for letter, channel_id in constants.DISCORD_HOT_CHANNEL_IDS.items():
            channels_data[letter] = ChannelData(
                channel=voice_channels[channel_id],
                original_name=voice_channels[channel_id].name
            )

        heating_context = self.heating_contexts[channel.guild.id]
        heating_context.channels_data = channels_data

        while True:
            await asyncio.sleep(constants.HEAT_PERIOD_SECONDS)

            if channel.members:
                heating_context.heat_level += 0.5
            else:
                if heating_context.heat_level == -1:
                    return

                heating_context.heat_level -= 0.5
                if heating_context.heat_level > len(constants.DISCORD_HEAT_NAMES) - 1:
                    heating_context.heat_level = float(int(heating_context.heat_level))

            if not heating_context.heat_level.is_integer():
                continue

            i = int(heating_context.heat_level)
            if i == -1:
                n_fires = 0
                new_name = channels_data['C'].original_name
            elif i < len(constants.DISCORD_HEAT_NAMES):
                n_fires = 0
                new_name = constants.DISCORD_HEAT_NAMES[i]
            else:
                n_fires = i - len(constants.DISCORD_HEAT_NAMES) + 1
                n_fires = round(math.log(n_fires + 4, 1.2) - 8)
                new_name = '🔥' * n_fires
            channels_data['C'].n_fires = n_fires
            if channel.name != new_name:
                await channel.edit(name=new_name)

            await set_fire_to('B', depends_on='C', firewall=len(channels_data['B'].channel.members))
            await set_fire_to('A', depends_on='B', firewall=len(channels_data['A'].channel.members))
            await set_fire_to('D', depends_on='C', firewall=len(channels_data['C'].channel.members))
            await set_fire_to('E', depends_on='D', firewall=len(channels_data['D'].channel.members))

    async def _punish(self, user: int | str | User, group_: int | str | Chat | Message, message: Message = None):
        user_id = self.get_user_id(user)
        try:
            await self.add_role(user_id, group_, 'Castigado')
            await self.remove_role(user_id, group_, 'Persona')
        except AttributeError:
            raise BadRoleError(str(self._punish))

    async def _search_medias(
        self,
        message: Message,
        force=False,
        audio_only=False,
        timeout_for_media: int | float = constants.SCRAPING_TIMEOUT_SECONDS
    ) -> OrderedSet[Media]:
        return await super()._search_medias(message, force, audio_only, timeout_for_media)

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
    @group
    @bot_mentioned
    async def _on_audit_log(self, message: Message):
        audit_entries = await self.find_audit_entries(
            message,
            limit=constants.AUDIT_LOG_LIMIT,
            actions=(discord.AuditLogAction.member_disconnect, discord.AuditLogAction.member_move),
            after=datetime.datetime.now(datetime.timezone.utc) - constants.AUDIT_LOG_AGE
        )
        await self.delete_message(message)
        if not audit_entries:
            await self.send_error(f'No hay entradas en el registro de auditoría <i>(desconectar y mover)</i> en la última hora.', message)
            return

        message_parts = ['<b>Registro de auditoría (solo desconectar y mover):</b>', '']
        for entry in audit_entries:
            author = await self._create_user_from_discord_user(entry.user)
            date_string = entry.created_at.astimezone(pytz.timezone('Europe/Madrid')).strftime('%d/%m/%Y  %H:%M:%S')
            if entry.action is discord.AuditLogAction.member_disconnect:
                message_parts.append(f"<b>{author.name}</b> ha <b>desconectado</b> {entry.extra.count} {'usuario' if entry.extra.count == 1 else 'usuarios'}  <i>({date_string})</i>")
            elif entry.action is discord.AuditLogAction.member_move:
                message_parts.append(f"<b>{author.name}</b> ha <b>movido</b> {entry.extra.count} {'usuario' if entry.extra.count == 1 else 'usuarios'} a {entry.extra.channel.name}  <i>({date_string})</i>")

        await self.send('\n'.join(message_parts), message)

    async def _on_member_join(self, member: discord.Member):
        user = await self._create_user_from_discord_user(member)
        user.pull_from_database(overwrite_fields=('roles',))
        for role in user.roles:
            try:
                await self.add_role(user, member.guild.id, role.id)
            except NotFoundError:
                pass

    async def _on_member_remove(self, member: discord.Member):
        (await self._create_user_from_discord_user(member)).save()

    @group
    @bot_mentioned
    @admin(send_negative=True)
    async def _on_restore_channel_names(self, message: Message):
        await self.delete_message(message)
        await self.restore_channel_names(self.get_group_id(message))

    async def _on_voice_state_update(self, _: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if getattr(before.channel, 'id', None) == constants.DISCORD_HOT_CHANNEL_IDS['C']:
            channel = before.channel
        elif getattr(after.channel, 'id', None) == constants.DISCORD_HOT_CHANNEL_IDS['C']:
            channel = after.channel
        else:
            return

        heating_context = self.heating_contexts[channel.guild.id]
        if not heating_context.is_active:
            heating_context.is_active = True
            await self._heat_channel(channel)
            heating_context.is_active = False

    # -------------------------------------------------------- #
    # -------------------- PUBLIC METHODS -------------------- #
    # -------------------------------------------------------- #
    async def is_punished(self, user: int | str | User, group_: int | str | Chat | Message) -> bool:
        user = await self.get_user(user, group_)
        group_id = self.get_group_id(group_)

        return bool(Punishment.find({
            'platform': self.platform.value,
            'user_id': user.id,
            'group_id': group_id,
            'is_active': True
        }))

    async def restore_channel_names(self, group_id: int):
        heating_context = self.heating_contexts[group_id]

        for channel_data in heating_context.channels_data.values():
            if channel_data.channel.name != channel_data.original_name:
                await channel_data.channel.edit(name=channel_data.original_name)
            channel_data.n_fires = 0

        heating_context.heat_level = 0.0
