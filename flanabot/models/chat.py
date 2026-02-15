__all__ = ['Chat']

from dataclasses import dataclass, field
from typing import Any

from multibot import Chat as MultiBotChat


@dataclass(eq=False)
class Chat(MultiBotChat):
    btc_offers: dict[str, Any] = field(
        default_factory=lambda: {
            'blocked_authors': [],
            'query': {}
        }
    )
    config: dict[str, bool] = field(
        default_factory=lambda: {
            'auto_insult': True,
            'auto_scraping': True,
            'auto_weather_chart': False,
            'check_flood': False,
            'check_spam': False,
            'client_connection_notifications': True,
            'punish': False,
            'scraping_delete_original': True,
            'ubereats': False
        }
    )
    ubereats: dict[str, Any] = field(
        default_factory=lambda: {
            'cookies': [],
            'last_codes': [],
            'next_execution': None,
            'seconds': 86700
        }
    )
