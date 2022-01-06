from __future__ import annotations  # todo0 remove in 3.11

import datetime
from dataclasses import dataclass, field
from typing import Iterable

from flanautils import Media, OrderedSet
from multibot import EventComponent, constants as multibot_constants, db

from flanabot.models.chat import Chat
from flanabot.models.user import User
from flanabot.models.weather_chart import WeatherChart


@dataclass(eq=False)
class Message(EventComponent):
    collection = db.message
    _unique_keys = ('id', 'author')
    _nullable_unique_keys = ('id', 'author')

    id: int | str = None
    author: User = None
    text: str = None
    button_text: str = None
    mentions: Iterable[User] = field(default_factory=list)
    chat: Chat = None
    replied_message: Message = None
    weather_chart: WeatherChart = None
    last_update: datetime.datetime = None
    song_infos: OrderedSet[Media] = field(default_factory=OrderedSet)
    is_inline: bool = None
    contents: list = field(default_factory=list)
    is_deleted: bool = False
    original_object: multibot_constants.ORIGINAL_MESSAGE = None
    original_event: multibot_constants.MESSAGE_EVENT = None

    def save(self, pull_exclude: Iterable[str] = (), pull_database_priority=False, references=True):
        self.last_update = datetime.datetime.now()
        super().save(pull_exclude, pull_database_priority, references)
