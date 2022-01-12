from dataclasses import dataclass, field

from multibot import Chat as MultiBotChat

from flanabot.models.user import User


@dataclass(eq=False)
class Chat(MultiBotChat):
    DEFAULT_CONFIG = {'auto_clear': False,
                      'auto_covid_chart': True,
                      'auto_currency_chart': True,
                      'auto_delete_original': True,
                      'auto_scraping': True,
                      'auto_weather_chart': True}
    users: list[User] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if not self.config:
            self.config = self.DEFAULT_CONFIG
