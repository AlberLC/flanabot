__all__ = ['WeatherBot']

import datetime
import random
from abc import ABC

import flanaapis.geolocation.functions
import flanaapis.weather.functions
import flanautils
import plotly.graph_objects
from flanaapis import Place, PlaceNotFoundError, WeatherEmoji
from flanautils import Media, MediaType, NotFoundError, OrderedSet, Source, TraceMetadata
from multibot import MultiBot, constants as multibot_constants

from flanabot import constants
from flanabot.models import Action, BotAction, ButtonsGroup, Message, WeatherChart


# ------------------------------------------------------------------------------------------------------- #
# --------------------------------------------- WEATHER_BOT --------------------------------------------- #
# ------------------------------------------------------------------------------------------------------- #
class WeatherBot(MultiBot, ABC):
    # -------------------------------------------------------- #
    # ------------------- PROTECTED METHODS ------------------ #
    # -------------------------------------------------------- #
    def _add_handlers(self):
        super()._add_handlers()

        self.register(self._on_weather, constants.KEYWORDS['weather'])
        self.register(self._on_weather, (multibot_constants.KEYWORDS['show'], constants.KEYWORDS['weather']))

        self.register_button(self._on_weather_button_press, ButtonsGroup.WEATHER)

    # ---------------------------------------------- #
    #                    HANDLERS                    #
    # ---------------------------------------------- #
    async def _on_weather(self, message: Message):
        bot_state_message: Message | None = None
        if message.is_inline:
            show_progress_state = False
        elif message.chat.is_group and not self.is_bot_mentioned(message):
            if message.chat.config['auto_weather_chart']:
                if BotAction.find_one({'platform': self.platform.value, 'action': Action.AUTO_WEATHER_CHART.value, 'chat': message.chat.object_id, 'date': {'$gt': datetime.datetime.now(datetime.timezone.utc) - constants.AUTO_WEATHER_EVERY}}):
                    return
                show_progress_state = False
            else:
                return
        else:
            show_progress_state = True

        original_text_words = flanautils.remove_accents(message.text.lower())
        original_text_words = flanautils.remove_symbols(original_text_words, ignore=('-', '.'), replace_with=' ').split()
        original_text_words = await self.filter_mention_ids(original_text_words, message, delete_names=True)

        # noinspection PyTypeChecker
        place_words = (
                OrderedSet(original_text_words)
                - flanautils.cartesian_product_string_matching(original_text_words, multibot_constants.KEYWORDS['show'], min_score=0.85).keys()
                - flanautils.cartesian_product_string_matching(original_text_words, constants.KEYWORDS['weather'], min_score=0.85).keys()
                - flanautils.cartesian_product_string_matching(original_text_words, multibot_constants.KEYWORDS['date'], min_score=0.85).keys()
                - flanautils.cartesian_product_string_matching(original_text_words, multibot_constants.KEYWORDS['thanks'], min_score=0.85).keys()
                - flanautils.CommonWords.get()
        )
        if not place_words:
            if not message.is_inline:
                await self.send_error(random.choice(('¿Tiempo dónde?', 'Indica el sitio.', 'Y el sitio?', 'y el sitio? me lo invento?')), message)
            return

        if 'calle' in original_text_words:
            place_words.insert(0, 'calle')
        place_query = ' '.join(place_words)
        if len(place_query) >= constants.MAX_PLACE_QUERY_LENGTH:
            if show_progress_state:
                await self.send_error(Media(str(flanautils.resolve_path('resources/mucho_texto.png')), MediaType.IMAGE, 'jpg', Source.LOCAL), message, send_as_file=False)
            return
        if show_progress_state:
            bot_state_message = await self.send(f'Buscando "{place_query}" en el mapa 🧐...', message)

        result: str | Place | None = None
        async for result in flanaapis.geolocation.functions.find_place_showing_progress(place_query):
            if isinstance(result, str) and bot_state_message:
                await self.edit(result, bot_state_message)

        place: Place = result
        if not place:
            if bot_state_message:
                await self.delete_message(bot_state_message)
            raise PlaceNotFoundError(place_query)

        if bot_state_message:
            bot_state_message = await self.edit(f'Obteniendo datos del tiempo para "{place_query}"...', bot_state_message)
        current_weather, day_weathers = await flanaapis.weather.functions.get_day_weathers_by_place(place)

        if bot_state_message:
            bot_state_message = await self.edit('Creando gráficas del tiempo...', bot_state_message)

        weather_chart = WeatherChart(
            _font={'size': 30},
            _title={
                'text': place.name[:40].strip(' ,-'),
                'xref': 'paper',
                'yref': 'paper',
                'xanchor': 'left',
                'yanchor': 'top',
                'x': 0.025,
                'y': 0.975,
                'font': {
                    'size': 50,
                    'family': 'open sans'
                }
            },
            _legend={'x': 0.99, 'y': 0.99, 'xanchor': 'right', 'yanchor': 'top', 'bgcolor': 'rgba(0,0,0,0)'},
            _margin={'l': 20, 'r': 20, 't': 20, 'b': 20},
            trace_metadatas={
                'temperature': TraceMetadata(name='temperature', group='temperature', legend='Temperatura', show=False, color='#ff8400', default_min=0, default_max=40, y_tick_suffix=' ºC', y_axis_width=130),
                'temperature_feel': TraceMetadata(name='temperature_feel', group='temperature', legend='Sensación de temperatura', show=True, color='red', default_min=0, default_max=40, y_tick_suffix=' ºC', y_axis_width=130),
                'clouds': TraceMetadata(name='clouds', legend='Nubes', show=False, color='#86abe3', default_min=-100, default_max=100, y_tick_suffix=' %', hide_y_ticks_if='{tick} < 0'),
                'visibility': TraceMetadata(name='visibility', legend='Visibilidad', show=False, color='#c99a34', default_min=0, default_max='{max_y_data} * 2', y_tick_suffix=' km', y_delta_tick=2, hide_y_ticks_if='{tick} > {max_y_data}'),
                'uvi': TraceMetadata(name='uvi', legend='UVI', show=False, color='#ffd000', default_min=-12, default_max=12, hide_y_ticks_if='{tick} < 0', y_delta_tick=1, y_axis_width=75),
                'humidity': TraceMetadata(name='humidity', legend='Humedad', show=False, color='#2baab5', default_min=0, default_max=100, y_tick_suffix=' %'),
                'precipitation_probability': TraceMetadata(name='precipitation_probability', legend='Probabilidad de precipitaciones', show=True, color='#0033ff', default_min=-100, default_max=100, y_tick_suffix=' %', hide_y_ticks_if='{tick} < 0'),
                'rain_volume': TraceMetadata(plotly.graph_objects.Histogram, name='rain_volume', group='precipitation', legend='Volumen de lluvia', show=True, color='#34a4eb', opacity=0.3, default_min=-10, default_max=10, y_tick_suffix=' mm', y_delta_tick=1, hide_y_ticks_if='{tick} < 0', y_axis_width=130),
                'snow_volume': TraceMetadata(plotly.graph_objects.Histogram, name='snow_volume', group='precipitation', legend='Volumen de nieve', show=True, color='#34a4eb', opacity=0.8, pattern={'shape': '.', 'fgcolor': '#ffffff', 'bgcolor': '#b0d6f3', 'solidity': 0.5, 'size': 14}, default_min=-10, default_max=10, y_tick_suffix=' mm', y_delta_tick=1, hide_y_ticks_if='{tick} < 0', y_axis_width=130),
                'pressure': TraceMetadata(name='pressure', legend='Presión', show=False, color='#31a339', default_min=1013.25 - 90, default_max=1013.25 + 90, y_tick_suffix=' hPa', y_axis_width=225),
                'wind_speed': TraceMetadata(name='wind_speed', legend='Velocidad del viento', show=False, color='#d8abff', default_min=-120, default_max=120, y_tick_suffix=' km/h', hide_y_ticks_if='{tick} < 0', y_axis_width=165)
            },
            x_data=[instant_weather.date_time for day_weather in day_weathers for instant_weather in day_weather.instant_weathers],
            all_y_data=[],
            current_weather=current_weather,
            day_weathers=day_weathers,
            timezone=(timezone := day_weathers[0].timezone),
            place=place,
            view_position=datetime.datetime.now(timezone)
        )

        weather_chart.apply_zoom()
        weather_chart.draw()
        if not (image_bytes := weather_chart.to_image()):
            if bot_state_message:
                await self.delete_message(bot_state_message)
            raise NotFoundError('No hay suficientes datos del tiempo.')

        if bot_state_message:
            bot_state_message = await self.edit('Enviando...', bot_state_message)
        bot_message: Message = await self.send(
            Media(image_bytes, MediaType.IMAGE, 'jpg'),
            [
                [WeatherEmoji.ZOOM_IN.value, WeatherEmoji.ZOOM_OUT.value, WeatherEmoji.LEFT.value, WeatherEmoji.RIGHT.value],
                [WeatherEmoji.TEMPERATURE.value, WeatherEmoji.TEMPERATURE_FEEL.value, WeatherEmoji.CLOUDS.value, WeatherEmoji.VISIBILITY.value, WeatherEmoji.UVI.value],
                [WeatherEmoji.HUMIDITY.value, WeatherEmoji.PRECIPITATION_PROBABILITY.value, WeatherEmoji.PRECIPITATION_VOLUME.value, WeatherEmoji.PRESSURE.value, WeatherEmoji.WIND_SPEED.value]
            ],
            message,
            buttons_key=ButtonsGroup.WEATHER,
            data={'weather_chart': weather_chart},
            send_as_file=False
        )
        await self.send_inline_results(message)

        if bot_state_message:
            await self.delete_message(bot_state_message)

        if bot_message and not self.is_bot_mentioned(message):
            # noinspection PyTypeChecker
            BotAction(self.platform.value, Action.AUTO_WEATHER_CHART, message, affected_objects=[bot_message]).save()

    async def _on_weather_button_press(self, message: Message):
        await self.accept_button_event(message)

        weather_chart = message.data['weather_chart']

        match message.buttons_info.pressed_text:
            case WeatherEmoji.ZOOM_IN.value:
                weather_chart.zoom_in()
            case WeatherEmoji.ZOOM_OUT.value:
                weather_chart.zoom_out()
            case WeatherEmoji.LEFT.value:
                weather_chart.move_left()
            case WeatherEmoji.RIGHT.value:
                weather_chart.move_right()
            case WeatherEmoji.PRECIPITATION_VOLUME.value:
                weather_chart.trace_metadatas['rain_volume'].show = not weather_chart.trace_metadatas['rain_volume'].show
                weather_chart.trace_metadatas['snow_volume'].show = not weather_chart.trace_metadatas['snow_volume'].show
            case emoji if emoji in WeatherEmoji.values:
                trace_metadata_name = WeatherEmoji(emoji).name.lower()
                weather_chart.trace_metadatas[trace_metadata_name].show = not weather_chart.trace_metadatas[trace_metadata_name].show
            case _:
                return

        weather_chart.apply_zoom()
        weather_chart.draw()

        image_bytes = weather_chart.to_image()
        await self.edit(Media(image_bytes, MediaType.IMAGE, 'jpg'), message)
