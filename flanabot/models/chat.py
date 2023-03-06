__all__ = ['Chat']

import datetime
from dataclasses import dataclass, field

from multibot import Chat as MultiBotChat


@dataclass(eq=False)
class Chat(MultiBotChat):
    DEFAULT_CONFIG = {
        'auto_insult': True,
        'auto_scraping': True,
        'auto_weather_chart': False,
        'check_flood': False,
        'punish': False,
        'scraping_delete_original': True,
        'ubereats': False
    }

    config: dict = field(default_factory=dict)
    ubereats_cookies: list[list[dict]] = field(default_factory=list)
    ubereats_last_codes: list[str] = field(default_factory=list)
    ubereats_seconds: int = 86700
    ubereats_next_execution: datetime.datetime = None

    def __post_init__(self):
        super().__post_init__()
        self.config = self.DEFAULT_CONFIG | self.config
