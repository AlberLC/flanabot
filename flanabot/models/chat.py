__all__ = ['Chat']

from dataclasses import dataclass

from multibot.models import Chat as MultiBotChat


@dataclass(eq=False)
class Chat(MultiBotChat):
    DEFAULT_CONFIG = {'check_flood': False,
                      'delete_original': True,
                      'insult': True,
                      'punish': False,
                      'scraping': True,
                      'weather_chart': True}

    def __post_init__(self):
        super().__post_init__()
        self.config = self.DEFAULT_CONFIG | self.config
