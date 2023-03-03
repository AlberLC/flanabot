__all__ = ['BotAction']

import datetime
from dataclasses import dataclass, field

from flanautils import DCMongoBase, FlanaBase
from multibot import Platform, User

from flanabot.models.chat import Chat
from flanabot.models.enums import Action
from flanabot.models.message import Message


@dataclass(eq=False)
class BotAction(DCMongoBase, FlanaBase):
    collection_name = 'bot_action'
    unique_keys = 'message'
    nullable_unique_keys = 'message'

    platform: Platform = None
    action: Action = None
    message: Message = None
    author: User = None
    chat: Chat = None
    affected_objects: list = field(default_factory=list)
    date: datetime.datetime = field(default_factory=datetime.datetime.now)

    def __post_init__(self):
        super().__post_init__()
        self.author = self.author or getattr(self.message, 'author', None)
        self.chat = self.chat or getattr(self.message, 'chat', None)
