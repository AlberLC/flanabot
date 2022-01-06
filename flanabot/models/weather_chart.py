import datetime
from dataclasses import dataclass, field

from flanaapis import InstantWeather, Place
from flanautils import DateChart, FlanaEnum


class Direction(FlanaEnum):
    LEFT = -1
    RIGHT = 1


@dataclass(unsafe_hash=True)
class WeatherChart(DateChart):
    current_weather: InstantWeather = None
    day_weathers: list = field(default_factory=list)
    timezone: datetime.timezone = None
    place: Place = None
    day_separator_width: float = 1
    zoom_level: int = 1
    view_position: datetime.datetime = None

    def __post_init__(self):
        super().__post_init__()
        self.legend = self._legend
        self.x_data = [instant_weather.date_time for day_weather in self.day_weathers for instant_weather in day_weather.instant_weathers]
        for trace_metadata in self.trace_metadatas.values():
            y_data = []
            for day_weather in self.day_weathers:
                for instant_weather in day_weather.instant_weathers:
                    y_data.append(getattr(instant_weather, trace_metadata.name))
            self.all_y_data.append(y_data)

    def add_lines(self):
        super().add_lines()

        try:
            first_dt = self.day_weathers[0].instant_weathers[0].date_time
            last_dt = self.day_weathers[-1].instant_weathers[-1].date_time
        except IndexError:
            return

        now = datetime.datetime.now(self.timezone)

        if self.show_now_vertical_line and first_dt <= now <= last_dt:
            self.figure.add_vline(x=now, line_width=1, line_dash='dot')
            self.figure.add_annotation(text="Ahora", yref="paper", x=now, y=0.01, showarrow=False)

        for day_weather in self.day_weathers:
            date_time = datetime.datetime(year=day_weather.date.year, month=day_weather.date.month, day=day_weather.date.day, tzinfo=self.timezone)
            if first_dt <= date_time <= last_dt:
                self.figure.add_vline(x=date_time, line_width=self.day_separator_width)

    # noinspection PyAttributeOutsideInit
    # noinspection PyUnboundLocalVariable
    def apply_zoom(self):
        self.clear()
        match self.zoom_level:
            case 0:
                self.xaxis = {
                    'tickformat': '%A %-d\n%B\n%Y',
                    'dtick': 24 * 60 * 60 * 1000,
                    'ticklabelmode': 'period',
                    'tickangle': None
                }
                self.day_separator_width = 1
            case _:
                match self.zoom_level:
                    case 1:
                        start_date = self.view_position - datetime.timedelta(days=3)
                        end_date = self.view_position + datetime.timedelta(days=3)
                        self.xaxis = {'tickformat': '%A %-d\n%B\n%Y', 'dtick': 24 * 60 * 60 * 1000, 'ticklabelmode': 'period'}
                        self.day_separator_width = 1
                    case 2:
                        start_date = self.view_position - datetime.timedelta(days=1)
                        end_date = self.view_position + datetime.timedelta(days=2)
                        self.xaxis = {'tickformat': '%-H\n%A %-d', 'dtick': 6 * 60 * 60 * 1000}
                        self.day_separator_width = 2
                    case 3:
                        start_date = self.view_position - datetime.timedelta(days=1)
                        end_date = self.view_position + datetime.timedelta(days=1)
                        self.xaxis = {'tickformat': '%-H\n%A %-d', 'dtick': 4 * 60 * 60 * 1000}
                        self.day_separator_width = 2
                    case 4:
                        start_date = self.view_position
                        end_date = self.view_position + datetime.timedelta(days=1)
                        self.xaxis = {'tickformat': '%-H\n%A %-d', 'dtick': 2 * 60 * 60 * 1000}
                        self.day_separator_width = 2
                    case 5:
                        start_date = self.view_position
                        end_date = self.view_position
                        self.xaxis = {'tickformat': '%-H\n%A %-d', 'dtick': 1 * 60 * 60 * 1000}
                        self.day_separator_width = 2

                self.xaxis = {
                    'range': (
                        (start_date - datetime.timedelta(days=1)).replace(hour=23),
                        (end_date + datetime.timedelta(days=1)).replace(hour=0)
                    ),
                    'tickangle': 0
                }

    def move_left(self):
        if self.zoom_level > 0 and self.x_data[0] <= self.view_position - datetime.timedelta(days=1):
            self.move_view_position(Direction.LEFT)

    def move_right(self):
        if self.zoom_level > 0 and self.view_position + datetime.timedelta(days=1) <= self.x_data[-1]:
            self.move_view_position(Direction.RIGHT)

    def move_view_position(self, direction: Direction):
        match self.zoom_level:
            case 0:
                return
            case _:
                time_delta = datetime.timedelta(days=1)
        self.view_position += time_delta * direction.value

    def zoom_in(self):
        if self.zoom_level < 5:
            self.zoom_level += 1

    def zoom_out(self):
        if 0 < self.zoom_level:
            self.zoom_level -= 1
