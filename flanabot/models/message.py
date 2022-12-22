from __future__ import annotations  # todo0 remove when it's by default

__all__ = ['Message']

from dataclasses import dataclass, field

from flanautils import Media, OrderedSet
from multibot import Message as MultiBotMessage, User

from flanabot.models.chat import Chat


@dataclass(eq=False)
class Message(MultiBotMessage):
    author: User = None
    mentions: list[User] = field(default_factory=list)
    chat: Chat = None
    replied_message: Message = None
    song_infos: OrderedSet[Media] = field(default_factory=OrderedSet)
