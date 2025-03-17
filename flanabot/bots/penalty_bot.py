__all__ = ['PenaltyBot']

import asyncio
import datetime
from abc import ABC

import flanautils
from flanautils import TimeUnits
from multibot import MultiBot, RegisteredCallback, User, admin, bot_mentioned, constants as multibot_constants, group, ignore_self_message

from flanabot import constants
from flanabot.models import Chat, Message, Punishment


# ------------------------------------------------------------------------------------------------------- #
# --------------------------------------------- PENALTY_BOT --------------------------------------------- #
# ------------------------------------------------------------------------------------------------------- #
class PenaltyBot(MultiBot, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock = asyncio.Lock()

    # -------------------------------------------------------- #
    # ------------------- PROTECTED METHODS ------------------ #
    # -------------------------------------------------------- #
    def _add_handlers(self):
        super()._add_handlers()

        self.register(self._on_ban, keywords=multibot_constants.KEYWORDS['ban'])

        self.register(self._on_mute, keywords=multibot_constants.KEYWORDS['mute'])
        self.register(self._on_mute, keywords=(('haz', 'se'), multibot_constants.KEYWORDS['mute']))
        self.register(self._on_mute, keywords=(multibot_constants.KEYWORDS['deactivate'], multibot_constants.KEYWORDS['unmute']))
        self.register(self._on_mute, keywords=(multibot_constants.KEYWORDS['deactivate'], multibot_constants.KEYWORDS['sound']))

        self.register(self._on_punish, keywords=constants.KEYWORDS['punish'])
        self.register(self._on_punish, keywords=(multibot_constants.KEYWORDS['deactivate'], constants.KEYWORDS['unpunish']))
        self.register(self._on_punish, keywords=(multibot_constants.KEYWORDS['deactivate'], multibot_constants.KEYWORDS['permission']))

        self.register(self._on_unban, keywords=multibot_constants.KEYWORDS['unban'])

        self.register(self._on_unmute, keywords=multibot_constants.KEYWORDS['unmute'])
        self.register(self._on_unmute, keywords=(multibot_constants.KEYWORDS['deactivate'], multibot_constants.KEYWORDS['mute']))
        self.register(self._on_unmute, keywords=(multibot_constants.KEYWORDS['activate'], multibot_constants.KEYWORDS['sound']))

        self.register(self._on_unpunish, keywords=constants.KEYWORDS['unpunish'])
        self.register(self._on_unpunish, keywords=(multibot_constants.KEYWORDS['deactivate'], constants.KEYWORDS['punish']))
        self.register(self._on_unpunish, keywords=(multibot_constants.KEYWORDS['activate'], multibot_constants.KEYWORDS['permission']))

    @admin(False)
    @group
    async def _check_message_flood(self, message: Message):
        if await self.is_punished(message.author, message.chat):
            return

        last_2s_messages = self.Message.find({
            'platform': self.platform.value,
            'author': message.author.object_id,
            'chat': message.chat.object_id,
            'date': {'$gte': datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=2)}
        })
        last_7s_messages = self.Message.find({
            'platform': self.platform.value,
            'author': message.author.object_id,
            'chat': message.chat.object_id,
            'date': {'$gte': datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=7)}
        })

        if len(last_2s_messages) > constants.FLOOD_2s_LIMIT or len(last_7s_messages) > constants.FLOOD_7s_LIMIT:
            punishment = Punishment.find_one({
                'platform': self.platform.value,
                'user_id': message.author.id,
                'group_id': message.chat.group_id
            })
            punishment_seconds = (getattr(punishment, 'level', 0) + 2) ** constants.PUNISHMENT_INCREMENT_EXPONENT
            await self.punish(message.author.id, message.chat.group_id, punishment_seconds, message, flood=True)
            await self.send(f'Castigado durante {TimeUnits(seconds=punishment_seconds).to_words()}.', message)

    @admin(False)
    @group
    async def _check_message_spam(self, message: Message) -> bool:
        if await self.is_punished(message.author, message.chat):
            return True

        spam_messages = self.Message.find({
            'text': message.text,
            'platform': self.platform.value,
            'author': message.author.object_id,
            'date': {'$gte': datetime.datetime.now(datetime.timezone.utc) - constants.SPAM_TIME_RANGE},
        })

        chats = {message.chat for message in spam_messages}
        if len(chats) <= constants.SPAM_CHANNELS_LIMIT:
            return False

        await self.punish(message.author.id, message.chat.group_id)
        await asyncio.sleep(constants.SPAM_DELETION_DELAY.total_seconds())  # We make sure to also delete any messages they may have sent before the punishment
        spam_messages = self.Message.find({
            'text': message.text,
            'platform': self.platform.value,
            'author': message.author.object_id,
            'date': {
                '$gte': datetime.datetime.now(datetime.timezone.utc)
                        -
                        constants.SPAM_TIME_RANGE
                        -
                        constants.SPAM_DELETION_DELAY
            },
            'is_deleted': False
        })
        chats = {message.chat for message in spam_messages}

        for message in spam_messages:
            await self.delete_message(await self.get_message(message.id, message.chat.id))

        groups_data = {chat.group_id: chat.group_name for chat in chats}
        owner_message_parts = [
            '<b>Spammer castigado:</b>',
            '<b>User:</b>',
            f'    <b>id:</b> <code>{message.author.id}</code>',
            f'    <b>name:</b> <code>{message.author.name}</code>',
            f'    <b>is_admin:<b> <code>{message.author.is_admin}</code>',
            f'    <b>is_bot:</b> <code>{message.author.is_bot}</code>',
            '',
            f'<b>Chats: {len(chats)}</b>',
            '',
            '<b>Groups:</b>',
            '\n\n'.join(
                f'    <b>group_id:</b> <code>{group_id}</code>\n'
                f'    <b>group_name:</b> <code>{group_name}</code>'
                for group_id, group_name in groups_data.items()
            )
        ]
        await self.send('\n'.join(owner_message_parts), await self.owner_chat)

        return True

    async def _punish(self, user: int | str | User, group_: int | str | Chat | Message, message: Message = None):
        pass

    async def _unpunish(self, user: int | str | User, group_: int | str | Chat | Message, message: Message = None):
        pass

    # ---------------------------------------------- #
    #                    HANDLERS                    #
    # ---------------------------------------------- #
    @bot_mentioned
    @group
    @admin(send_negative=True)
    async def _on_ban(self, message: Message):
        for user in await self._find_users_to_punish(message):
            await self.ban(user, message, flanautils.text_to_time(await self.filter_mention_ids(message.text, message)), message)

    @group
    @bot_mentioned
    @admin(send_negative=True)
    async def _on_mute(self, message: Message):
        for user in await self._find_users_to_punish(message):
            await self.mute(user, message, flanautils.text_to_time(await self.filter_mention_ids(message.text, message)), message)

    @ignore_self_message
    async def _on_new_message_raw(
        self,
        message: Message,
        whitelist_callbacks: set[RegisteredCallback] | None = None,
        blacklist_callbacks: set[RegisteredCallback] | None = None
    ):
        await super()._on_new_message_raw(message, whitelist_callbacks, blacklist_callbacks)
        if message.chat.config['check_flood'] and message.chat.config['punish'] and not message.is_inline:
            async with self.lock:
                if not await self._check_message_spam(message):
                    await self._check_message_flood(message)

    @bot_mentioned
    @group
    @admin(send_negative=True)
    async def _on_punish(self, message: Message):
        if not message.chat.config['punish']:
            return

        for user in await self._find_users_to_punish(message):
            await self.punish(user, message, flanautils.text_to_time(await self.filter_mention_ids(message.text, message)), message)

    async def _on_ready(self):
        if not self._is_initialized:
            flanautils.do_every(constants.CHECK_PUNISHMENTS_EVERY_SECONDS, self.check_old_punishments)

        await super()._on_ready()

    @bot_mentioned
    @group
    @admin(send_negative=True)
    async def _on_unban(self, message: Message):
        for user in await self._find_users_to_punish(message):
            await self.unban(user, message, message)

    @group
    @bot_mentioned
    @admin(send_negative=True)
    async def _on_unmute(self, message: Message):
        for user in await self._find_users_to_punish(message):
            await self.unmute(user, message, message)

    @group
    @bot_mentioned
    @admin(send_negative=True)
    async def _on_unpunish(self, message: Message):
        if not message.chat.config['punish']:
            return

        for user in await self._find_users_to_punish(message):
            await self.unpunish(user, message, message)

    # -------------------------------------------------------- #
    # -------------------- PUBLIC METHODS -------------------- #
    # -------------------------------------------------------- #
    async def check_old_punishments(self):
        punishments = Punishment.find({'platform': self.platform.value}, lazy=True)

        for punishment in punishments:
            now = datetime.datetime.now(datetime.timezone.utc)
            if not punishment.until or now < punishment.until:
                continue

            await self._remove_penalty(punishment, self._unpunish)

            if punishment.last_update + constants.PUNISHMENTS_RESET_TIME <= now:
                punishment.level -= 1
                punishment.delete()

    async def is_punished(self, user: int | str | User, group_: int | str | Chat | Message) -> bool:
        pass

    async def punish(
        self,
        user: int | str | User,
        group_: int | str | Chat | Message,
        time: int | datetime.timedelta = None,
        message: Message = None,
        flood=False
    ):
        # noinspection PyTypeChecker
        punishment = Punishment(self.platform, self.get_user_id(user), self.get_group_id(group_), time)
        punishment.pull_from_database(overwrite_fields=('level',), exclude_fields=('until',))
        if flood:
            punishment.level += 1

        await self._punish(punishment.user_id, punishment.group_id)
        punishment.save(pull_exclude_fields=('until',))
        await self._unpenalize_later(punishment, self._unpunish, message)

    async def unpunish(self, user: int | str | User, group_: int | str | Chat | Message, message: Message = None):
        # noinspection PyTypeChecker
        punishment = Punishment(self.platform, self.get_user_id(user), self.get_group_id(group_))
        await self._remove_penalty(punishment, self._unpunish, message)
