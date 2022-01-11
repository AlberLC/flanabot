from __future__ import annotations  # todo0 remove in 3.11

from dataclasses import dataclass, field

from flanautils import Media, OrderedSet
from multibot import Message as MultiBotMessage

from flanabot.models.weather_chart import WeatherChart


@dataclass(eq=False)
class Message(MultiBotMessage):
    weather_chart: WeatherChart = None
    song_infos: OrderedSet[Media] = field(default_factory=OrderedSet)
