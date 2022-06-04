__all__ = ['Chat']

from dataclasses import dataclass

from multibot.models import Chat as MultiBotChat


@dataclass(eq=False)
class Chat(MultiBotChat):
    DEFAULT_CONFIG = {'auto_covid_chart': True,
                      'auto_currency_chart': True,
                      'auto_delete_original': True,
                      'auto_insult': True,
                      'auto_scraping': True,
                      'auto_weather_chart': True}

    def __post_init__(self):
        super().__post_init__()
        self.config = self.DEFAULT_CONFIG | self.config
