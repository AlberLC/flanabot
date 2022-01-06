from dataclasses import dataclass, field

from multibot import Chat as MultiBotChat, EventComponent, T

DEFAULT_CONFIG = {'auto_clear': False,
                  'auto_covid_chart': True,
                  'auto_currency_chart': True,
                  'auto_delete_original': True,
                  'auto_scraping': True,
                  'auto_weather_chart': True}


@dataclass(eq=False)
class Chat(MultiBotChat):
    config: dict[str, bool] = field(default_factory=lambda: DEFAULT_CONFIG)

    @classmethod
    def from_event_component(cls, event_component: EventComponent) -> T:
        chat = super().from_event_component(event_component)
        chat.config = DEFAULT_CONFIG
        return chat
