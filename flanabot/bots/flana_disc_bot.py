__all__ = ['FlanaDiscBot']

import asyncio
import datetime
import math
import os
import random

import discord
import flanautils
import pytz
from flanautils import Media, NotFoundError, OrderedSet
from multibot import BadRoleError, DiscordBot, Platform, Role, User, bot_mentioned, constants as multibot_constants, group

from flanabot import constants
from flanabot.bots.flana_bot import FlanaBot
from flanabot.models import Chat, Message, Punishment


# ---------------------------------------------------------------------------------------------------- #
# ------------------------------------------ FLANA_DISC_BOT ------------------------------------------ #
# ---------------------------------------------------------------------------------------------------- #
class FlanaDiscBot(DiscordBot, FlanaBot):
    def __init__(self):
        super().__init__(os.environ['DISCORD_BOT_TOKEN'])
        self.heating = False
        self.heat_level = 0.0

    # -------------------------------------------------------- #
    # ------------------- PROTECTED METHODS ------------------ #
    # -------------------------------------------------------- #
    def _add_handlers(self):
        super()._add_handlers()
        self.client.add_listener(self._on_member_join, 'on_member_join')
        self.client.add_listener(self._on_member_remove, 'on_member_remove')
        self.client.add_listener(self._on_voice_state_update, 'on_voice_state_update')

        self.register(self._on_audit_log, multibot_constants.KEYWORDS['audit'])

    async def _changeable_roles(self, group_: int | str | Chat | Message) -> list[Role]:
        group_id = self.get_group_id(group_)
        r = await self.get_group_roles(group_)
        return [role for role in r if role.id in constants.CHANGEABLE_ROLES[Platform.DISCORD][group_id]]

    async def _heat_channel(self, channel: discord.VoiceChannel):
        async def set_fire_to(channel_key: str, depends_on: str, firewall=0):
            fire_score = random.randint(0, channels[depends_on]['n_fires'] - channels[channel_key]['n_fires']) - firewall // 2
            if fire_score < 1:
                if not channels[channel_key]['n_fires']:
                    return
                channels[channel_key]['n_fires'] -= 1
            elif fire_score == 1:
                return
            else:
                channels[channel_key]['n_fires'] += 1

            if channels[channel_key]['n_fires']:
                new_name_ = '🔥' * channels[channel_key]['n_fires']
            else:
                new_name_ = channels[channel_key]['original_name']
            await channels[channel_key]['object'].edit(name=new_name_)

        channels = {}
        for letter, channel_id in constants.DISCORD_HOT_CHANNEL_IDS.items():
            channel_ = flanautils.find(channel.guild.voice_channels, condition=lambda c: c.id == channel_id)
            channels[letter] = {
                'object': channel_,
                'original_name': channel_.name,
                'n_fires': 0
            }

        while True:
            await asyncio.sleep(constants.HEAT_PERIOD_SECONDS)

            if channel.members:
                self.heat_level += 0.5
            else:
                if not self.heat_level:
                    return
                self.heat_level -= 0.5
                if self.heat_level > len(constants.DISCORD_HEAT_NAMES) - 1:
                    self.heat_level = float(int(self.heat_level))

            if not self.heat_level.is_integer():
                continue

            i = int(self.heat_level)
            if not i:
                n_fires = 0
                new_name = channels['C']['original_name']
            elif i < len(constants.DISCORD_HEAT_NAMES):
                n_fires = 0
                new_name = constants.DISCORD_HEAT_NAMES[i]
            else:
                n_fires = i - len(constants.DISCORD_HEAT_NAMES) + 1
                n_fires = round(math.log(n_fires + 4, 1.2) - 8)
                new_name = '🔥' * n_fires
            channels['C']['n_fires'] = n_fires
            if channel.name != new_name:
                await channel.edit(name=new_name)

            await set_fire_to('B', depends_on='C', firewall=len(channels['B']['object'].members))
            await set_fire_to('A', depends_on='B', firewall=len(channels['A']['object'].members))
            await set_fire_to('D', depends_on='C', firewall=len(channels['C']['object'].members))
            await set_fire_to('E', depends_on='D', firewall=len(channels['D']['object'].members))

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

    async def _on_voice_state_update(self, _: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if getattr(before.channel, 'id', None) == constants.DISCORD_HOT_CHANNEL_IDS['C']:
            channel = before.channel
        elif getattr(after.channel, 'id', None) == constants.DISCORD_HOT_CHANNEL_IDS['C']:
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
    async def is_punished(self, user: int | str | User, group_: int | str | Chat | Message) -> bool:
        user = await self.get_user(user, group_)
        group_id = self.get_group_id(group_)

        return bool(Punishment.find({
            'platform': self.platform.value,
            'user_id': user.id,
            'group_id': group_id,
            'is_active': True
        }))
