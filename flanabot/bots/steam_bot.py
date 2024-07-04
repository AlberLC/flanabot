__all__ = ['SteamBot']

import asyncio
import base64
import os
import random
import re
import urllib.parse
from abc import ABC
from collections import defaultdict
from collections.abc import Awaitable, Callable, Iterable, Iterator
from contextlib import asynccontextmanager
from typing import Any

import aiohttp
import flanautils
import playwright.async_api
import playwright.async_api
import plotly
from flanautils import Media, MediaType, Source
from multibot import LimitError, MultiBot, RegisteredCallback, constants as multibot_constants

import constants
from flanabot.models import Message, SteamRegion


# ----------------------------------------------------------------------------------------------------- #
# --------------------------------------------- constants.STEAM_BOT --------------------------------------------- #
# ----------------------------------------------------------------------------------------------------- #
class SteamBot(MultiBot, ABC):
    # -------------------------------------------------------- #
    # ------------------- PROTECTED METHODS ------------------ #
    # -------------------------------------------------------- #
    def _add_handlers(self):
        super()._add_handlers()

        self.register(self._on_steam, keywords='steam', priority=3)

    async def _add_app_price(
        self,
        app_prices: dict[str, dict[str, float]],
        steam_region: SteamRegion,
        app_ids: Iterable[str],
        session: aiohttp.ClientSession
    ) -> None:
        for ids_batch_batch in flanautils.chunks(
            flanautils.chunks(list(app_ids), constants.STEAM_IDS_BATCH),
            constants.STEAM_MAX_CONCURRENT_REQUESTS
        ):
            gather_results = await asyncio.gather(
                *(self._get_app_data(session, ids_batch, steam_region.code) for ids_batch in ids_batch_batch)
            )
            for gather_result in gather_results:
                for app_id, app_data in gather_result.items():
                    if (
                        (data := app_data.get('data'))
                        and
                        (price := data.get('price_overview', {}).get('final')) is not None
                    ):
                        app_prices[app_id][steam_region.code] = price / 100 / steam_region.eur_conversion_rate

    @staticmethod
    @asynccontextmanager
    async def _create_browser_context(
        browser: playwright.async_api.Browser
    ) -> Iterator[playwright.async_api.BrowserContext]:
        async with await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36',
            screen={
                'width': 1920,
                'height': 1080
            },
            viewport={
                'width': 1920,
                'height': 945
            },
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
            default_browser_type='chromium',
            locale='es-ES'
        ) as context:
            yield context

    async def _get_app_data(
        self,
        session: aiohttp.ClientSession,
        ids_batch: Iterable[str],
        country_code: str
    ) -> dict[str, Any]:
        async with session.get(
            constants.STEAM_APP_ENDPOINT_TEMPLATE.format(ids=','.join(ids_batch), country_code=country_code)
        ) as response:
            if response.status != 200:
                raise LimitError('🚫 Steam ban: espera 5 minutos antes de consultar de nuevo.')

            return await response.json()

    @staticmethod
    async def _get_exchange_data(session: aiohttp.ClientSession) -> dict[str, Any]:
        async with session.get(
            constants.STEAM_EXCHANGERATE_API_ENDPOINT.format(api_key=os.environ['EXCHANGERATE_API_KEY'])
        ) as response:
            exchange_data = await response.json()
            return exchange_data

    async def _get_most_games_ids(self, browser: playwright.async_api.Browser) -> set[str]:
        app_ids = set()

        re_pattern = fr'{urllib.parse.urlparse(constants.STEAM_MOST_URLS[0]).netloc}/\w+/(\d+)'
        async with self._create_browser_context(browser) as context:
            context.set_default_timeout(10000)
            page = await context.new_page()

            for url in constants.STEAM_MOST_URLS:
                await page.goto(url)
                try:
                    await page.wait_for_selector('tr td a[href]')
                except playwright.async_api.TimeoutError:
                    raise LimitError('🚫 Steam ban: espera 5 minutos antes de consultar de nuevo.')

                locator = page.locator('tr td a[href]')
                for i in range(await locator.count()):
                    href = await locator.nth(i).get_attribute('href')
                    app_ids.add(re.search(re_pattern, href).group(1))

        return app_ids

    @staticmethod
    def _insert_exchange_rates(
        steam_regions: dict[str, SteamRegion],
        exchange_data: dict[str, Any]
    ) -> dict[str, SteamRegion]:
        for steam_region in steam_regions.values():
            alpha_3_code = constants.STEAM_REGION_CODE_MAPPING[steam_region.code]
            steam_region.eur_conversion_rate = exchange_data['conversion_rates'][alpha_3_code]

        return steam_regions

    async def _scrape_steam_data(
        self,
        update_state: Callable[[str], Awaitable[Message]],
        update_steam_regions=False,
        most_games=True
    ) -> tuple[dict[str, SteamRegion], set[str]]:
        steam_regions = {steam_region.code: steam_region for steam_region in SteamRegion.find()}
        most_games_ids = set()

        if update_steam_regions or most_games:
            async with playwright.async_api.async_playwright() as playwright_:
                async with await playwright_.chromium.launch() as browser:
                    if update_steam_regions:
                        await update_state('Actualizando las regiones de Steam...')
                        SteamRegion.delete_many_raw({})
                        steam_regions = await self._update_steam_regions(browser)

                    if most_games:
                        await update_state('Obteniendo los juegos más jugados y vendidos de Steam...')
                        most_games_ids = await self._get_most_games_ids(browser)

                    return steam_regions, most_games_ids
        else:
            return steam_regions, most_games_ids

    async def _update_steam_regions(self, browser: playwright.async_api.Browser) -> dict[str, SteamRegion]:
        steam_regions = {}

        for app_id in constants.STEAM_APP_IDS_FOR_SCRAPE_COUNTRIES:
            async with self._create_browser_context(browser) as context:
                page = await context.new_page()
                await page.goto(f'{constants.STEAM_DB_URL}/app/{app_id}/')
                locator = page.locator("#prices td[class='price-line']")
                for i in range(await locator.count()):
                    td = locator.nth(i)
                    src = (await td.locator('img').get_attribute('src'))
                    name = (await td.text_content()).strip()
                    flag_url = f'{constants.STEAM_DB_URL}{src}'
                    region_code = await td.get_attribute('data-cc')
                    steam_region = SteamRegion(region_code, name, flag_url)
                    steam_region.save()
                    steam_regions[steam_region.code] = steam_region

                await asyncio.sleep(2)

        return steam_regions

    # ---------------------------------------------- #
    #                    HANDLERS                    #
    # ---------------------------------------------- #
    async def _on_steam(
        self,
        message: Message,
        update_steam_regions: bool | None = None,
        most_games: bool | None = None,
        last_games: bool | None = None,
        random_games: bool | None = None
    ):
        if message.chat.is_group and not self.is_bot_mentioned(message):
            return

        if update_steam_regions is None:
            update_steam_regions = bool(
                self._parse_callbacks(
                    message.text,
                    [
                        RegisteredCallback(
                            ...,
                            keywords=(multibot_constants.KEYWORDS['update'], constants.KEYWORDS['region'])
                        )
                    ]
                )
            )

        if most_games is None:
            most_games = bool(
                flanautils.cartesian_product_string_matching(
                    message.text,
                    ('jugados', 'played', 'sellers', 'selling', 'vendidos'),
                    multibot_constants.PARSER_MIN_SCORE_DEFAULT
                )
            )

        if last_games is None:
            last_games = bool(
                flanautils.cartesian_product_string_matching(
                    message.text,
                    multibot_constants.KEYWORDS['last'] + ('new', 'novedades', 'nuevos'),
                    multibot_constants.PARSER_MIN_SCORE_DEFAULT
                )
            )

        if random_games is None:
            random_games = bool(
                flanautils.cartesian_product_string_matching(
                    message.text,
                    multibot_constants.KEYWORDS['random'],
                    multibot_constants.PARSER_MIN_SCORE_DEFAULT
                )
            )

        if not any((most_games, last_games, random_games)):
            most_games = True
            last_games = True
            random_games = True

        update_state = self.create_message_updater(message, delete_user_message=True)

        chart_title_parts = []

        steam_regions, selected_app_ids = await self._scrape_steam_data(update_state, update_steam_regions, most_games)

        if most_games:
            chart_title_parts.append(f'los {len(selected_app_ids)} más jugados/vendidos')

        async with aiohttp.ClientSession() as session:
            if last_games or random_games:
                await update_state('Obteniendo todas las aplicaciones de Steam...')
                async with session.get(constants.STEAM_ALL_APPS_ENDPOINT) as response:
                    all_apps_data = await response.json()
                app_ids = [
                    str(app_id) for app_data in all_apps_data['applist']['apps'] if (app_id := app_data['appid'])
                ]

                if last_games:
                    selected_app_ids.update(app_ids[-constants.STEAM_LAST_GAMES:])
                    chart_title_parts.append(f'los {constants.STEAM_LAST_GAMES} más nuevos')

                if random_games:
                    selected_app_ids.update(random.sample(app_ids, constants.STEAM_RANDOM_GAMES))
                    chart_title_parts.append(f'{constants.STEAM_RANDOM_GAMES} aleatorios')

            exchange_data = await self._get_exchange_data(session)
            steam_regions = self._insert_exchange_rates(steam_regions, exchange_data)

            bot_state_message = await update_state('Obteniendo los precios para todas las regiones...')
            apps_prices = defaultdict(dict)
            try:
                await asyncio.gather(
                    *(
                        self._add_app_price(apps_prices, steam_region, selected_app_ids, session)
                        for steam_region in steam_regions.values()
                    )
                )
            except LimitError:
                await self.delete_message(bot_state_message)
                raise

            apps_prices = {k: v for k, v in apps_prices.items() if len(v) == len(steam_regions)}

            for app_prices in apps_prices.values():
                for region_code, price in app_prices.items():
                    steam_regions[region_code].total_price += price

            await update_state('Creando gráfico...')
            steam_regions_values = sorted(steam_regions.values(), key=lambda steam_region: steam_region.total_price)
            region_names = []
            region_total_prices = []
            bar_colors = []
            bar_line_colors = []
            images = []
            for i, steam_region in enumerate(steam_regions_values):
                region_names.append(steam_region.name)
                region_total_prices.append(steam_region.total_price)
                bar_colors.append(steam_region.bar_color)
                bar_line_colors.append(steam_region.bar_line_color)
                async with session.get(steam_region.flag_url) as response:
                    images.append({
                        'source': f'data:image/svg+xml;base64,{base64.b64encode(await response.read()).decode()}',
                        'xref': 'x',
                        'yref': 'paper',
                        'x': i,
                        'y': 0.04,
                        'sizex': 0.425,
                        'sizey': 0.0225,
                        'xanchor': 'center',
                        'opacity': 1,
                        'layer': 'above'
                    })

        figure = plotly.graph_objs.Figure(
            [
                plotly.graph_objs.Bar(
                    x=region_names,
                    y=region_total_prices,
                    marker={'color': bar_colors},
                )
            ]
        )
        figure.update_layout(
            width=1920,
            height=945,
            margin={'t': 20, 'r': 20, 'b': 20, 'l': 20},
            title={
                'text': f"{len(apps_prices)} juegos<br><sup>(solo los comparables entre {flanautils.join_last_separator(chart_title_parts, ', ', ' y ')})</sup>",
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.93,
                'font': {
                    'size': 35
                }
            },
            images=images,
            xaxis={'tickfont': {
                'size': 14
            }},
            yaxis={'ticksuffix': ' €', 'tickfont': {
                'size': 18
            }}
        )

        bot_state_message = await update_state('Enviando...')
        await self.send(Media(figure.to_image(), MediaType.IMAGE, 'png', Source.LOCAL), message)
        await self.delete_message(bot_state_message)

    # -------------------------------------------------------- #
    # -------------------- PUBLIC METHODS -------------------- #
    # -------------------------------------------------------- #
