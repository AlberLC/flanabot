from dataclasses import dataclass, field

from multibot.models import Chat as MultiBotChat, User


@dataclass(eq=False)
class Chat(MultiBotChat):
    DEFAULT_CONFIG = {'auto_covid_chart': True,
                      'auto_currency_chart': True,
                      'auto_delete_original': True,
                      'auto_insult': True,
                      'auto_scraping': True,
                      'auto_weather_chart': True}
    users: list[User] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        self.config = self.DEFAULT_CONFIG | self.config
