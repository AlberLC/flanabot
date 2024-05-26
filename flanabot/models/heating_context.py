__all__ = ['ChannelData', 'HeatingContext']

from dataclasses import dataclass, field

import discord


@dataclass
class ChannelData:
    channel: discord.VoiceChannel
    original_name: str
    n_fires: int = 0


@dataclass
class HeatingContext:
    channels_data: dict[str, ChannelData] = field(default_factory=dict)
    is_active: bool = False
    heat_level: float = -1
