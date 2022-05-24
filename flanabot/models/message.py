from __future__ import annotations  # todo0 remove in 3.11

from dataclasses import dataclass, field
from typing import Iterable

from flanautils import Media, OrderedSet
from multibot.models import Message as MultiBotMessage, User

from flanabot.models.chat import Chat
from flanabot.models.weather_chart import WeatherChart


@dataclass(eq=False)
class Message(MultiBotMessage):
    author: User = None
    mentions: Iterable[User] = field(default_factory=list)
    chat: Chat = None
    replied_message: Message = None
    weather_chart: WeatherChart = None
    song_infos: OrderedSet[Media] = field(default_factory=OrderedSet)
