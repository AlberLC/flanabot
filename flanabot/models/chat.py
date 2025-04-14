__all__ = ['Chat']

from dataclasses import dataclass, field

from multibot import Chat as MultiBotChat


@dataclass(eq=False)
class Chat(MultiBotChat):
    config: dict = field(default_factory=lambda: {
        'auto_insult': True,
        'auto_scraping': True,
        'auto_weather_chart': False,
        'check_flood': False,
        'punish': False,
        'scraping_delete_original': True,
        'ubereats': False
    })
    btc_offers_max_eur: float | None = None
    ubereats: dict = field(default_factory=lambda: {
        'cookies': [],
        'last_codes': [],
        'seconds': 86700,
        'next_execution': None
    })
