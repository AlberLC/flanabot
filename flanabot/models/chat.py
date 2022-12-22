__all__ = ['Chat']

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
        'scraping_delete_original': True
    }

    config: dict[str, bool] = field(default_factory=dict)

    def __post_init__(self):
        super().__post_init__()
        self.config = self.DEFAULT_CONFIG | self.config
