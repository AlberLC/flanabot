__all__ = ['LolMythicShopBot']

import asyncio
import hashlib
import multiprocessing
import re
import xml.etree.ElementTree
from abc import ABC
from collections.abc import Iterable
from pathlib import Path
from typing import Never

import aiohttp
import cv2
import flanautils
import numpy
import playwright.async_api
import pytesseract
from flanautils import Media, MediaType
from multibot import MultiBot

import constants
from lru_cache import FIFOCache


# ----------------------------------------------------------------------------------------------------- #
# ---------------------------------------- LOL_MYTHIC_SHOP_BOT ---------------------------------------- #
# ----------------------------------------------------------------------------------------------------- #
class LolMythicShopBot(MultiBot, ABC):
    # -------------------------------------------------------- #
    # ------------------- PROTECTED METHODS ------------------ #
    # -------------------------------------------------------- #
    @staticmethod
    def _check_image_text(subimage_name: str, image_text: str) -> bool:
        return any(name_word in image_text.lower() for name_word in subimage_name.lower().split('_'))

    @staticmethod
    def _check_is_image_in_image(
        subimage: str | Path | numpy.ndarray,
        image: str | Path | numpy.ndarray,
        scales: Iterable[float] = numpy.linspace(0.3, 2, 10)
    ) -> bool:
        return bool(
            # flanautils.search_features_in_image(
            #     subimage,
            #     image,
            #     min_matches=8,
            #     scales=scales,
            #     multi_scale_mode=flanautils.MultiScaleMode.FIRST
            # )
            # or
            flanautils.search_in_image(
                subimage,
                image,
                confidence=0.5,
                scales=scales,
                multi_scale_mode=flanautils.MultiScaleMode.FIRST
            )
        )

    @classmethod
    def _check_lol_mythic_shop_images(cls, image: str | Path | numpy.ndarray, queue: multiprocessing.Queue) -> None:
        image_text = pytesseract.image_to_string(flanautils.to_ndarray(image))

        for emote_name, emote_image_names in constants.LOL_MYTHIC_SHOP_IMAGES.items():
            first_emote_image_path = constants.LOL_MYTHIC_SHOP_IMAGES_PATH / emote_image_names[0]
            first_emote_image_path_str = str(first_emote_image_path)
            image_bytes = cv2.imencode('.png', cv2.cvtColor(image, cv2.COLOR_BGR2RGB))[1].tobytes()

            if cls._check_image_text(emote_name, image_text):
                queue.put(first_emote_image_path_str)
                queue.put(image_bytes)

            for emote_image_name in emote_image_names:
                if cls._check_is_image_in_image(constants.LOL_MYTHIC_SHOP_IMAGES_PATH / emote_image_name, image):
                    queue.put(first_emote_image_path_str)
                    queue.put(image_bytes)
                    break

    @classmethod
    async def _check_nitter_urls(
        cls,
        image_urls: Iterable[str],
        processed_image_urls: FIFOCache[str],
        processed_image_hashes: FIFOCache[bytes],
        session: aiohttp.ClientSession(),
        browser_context: playwright.async_api.BrowserContext,
        queue: multiprocessing.Queue
    ) -> None:
        for image_url in image_urls:
            if image_url in processed_image_urls:
                continue

            try:
                async with session.get(image_url) as response:
                    image_bytes = await response.read()
            except TimeoutError, aiohttp.ClientError:
                if not (image_bytes := await cls._fetch_browser_image(image_url, browser_context)):
                    continue

            # noinspection PyUnboundLocalVariable
            if (image_hash := hashlib.sha256(image_bytes).digest()) in processed_image_hashes:
                processed_image_urls.add(image_url)
                continue

            try:
                cls._check_lol_mythic_shop_images(
                    cv2.imdecode(numpy.frombuffer(image_bytes, numpy.uint8), cv2.IMREAD_COLOR_RGB),
                    queue
                )
            except Exception as e:
                queue.put(f'error: {e}')
            else:
                processed_image_urls.add(image_url)
                processed_image_hashes.add(image_hash)

    @staticmethod
    async def _fetch_browser_image(url: str, browser_context: playwright.async_api.BrowserContext) -> bytes | None:
        try:
            page = await browser_context.new_page()
            return await (await page.goto(url)).body()
        except playwright.async_api.Error:
            pass

    @classmethod
    async def _fetch_image_urls(
        cls,
        session: aiohttp.ClientSession,
        browser_context: playwright.async_api.BrowserContext
    ) -> list[str]:
        image_urls = []

        for future in asyncio.as_completed(
            (
                    cls._fetch_rss_xml_http(constants.LOL_MYTHIC_SHOP_URLS[0], session),
                    cls._fetch_rss_xml_browser(constants.LOL_MYTHIC_SHOP_URLS[1], browser_context)
            )
        ):
            if not (xml_ := await future):
                continue

            try:
                root = xml.etree.ElementTree.fromstring(xml_)
            except xml.etree.ElementTree.ParseError:
                continue

            for item in root.findall('./channel/item'):
                description = item.find('description').text
                image_urls.extend(
                    url.replace('pic/media', 'pic/orig/media')
                    for url in re.findall(r'<img\s+src=["\'](.*?)["\']', description, re.IGNORECASE)
                )

        return image_urls

    @staticmethod
    async def _fetch_rss_xml_browser(url: str, browser_context: playwright.async_api.BrowserContext) -> str | None:
        try:
            page = await browser_context.new_page()
            await page.goto(url)
            await page.wait_for_load_state('networkidle')

            return await page.locator('pre').text_content()
        except playwright.async_api.Error:
            pass

    @staticmethod
    async def _fetch_rss_xml_http(url: str, session: aiohttp.ClientSession) -> str | None:
        try:
            async with session.get(url, headers={'User-Agent': flanautils.USER_AGENT}) as response:
                return await response.text()
        except TimeoutError, aiohttp.ClientError:
            pass

    async def _start_lol_mythic_shop_checker(self) -> Never:
        queue = multiprocessing.Queue()

        multiprocessing.Process(target=start_lol_mythic_shop_checker_process, args=(queue,)).start()

        while True:
            try:
                result = await asyncio.to_thread(queue.get)

                if isinstance(result, bytes):
                    message_content = Media(result, MediaType.IMAGE)
                elif result.startswith('error: '):
                    message_content = result
                else:
                    message_content = Media(result)

                await self.send(message_content, await self.owner_chat)
            except Exception as e:
                try:
                    await self.send(str(e), await self.owner_chat)
                except Exception as e:
                    print(e, flush=True)

    # -------------------------------------------------------- #
    # -------------------- PUBLIC METHODS -------------------- #
    # -------------------------------------------------------- #
    @classmethod
    async def run_lol_mythic_shop_checker(cls, queue: multiprocessing.Queue) -> Never:
        processed_image_urls = FIFOCache[str](max_size=100)
        processed_image_hashes = FIFOCache[bytes](max_size=100)

        while True:
            async with (
                aiohttp.ClientSession() as session,
                playwright.async_api.async_playwright() as playwright_,
                await playwright_.chromium.launch() as browser,
                await browser.new_context(user_agent=flanautils.USER_AGENT) as browser_context
            ):
                await cls._check_nitter_urls(
                    await cls._fetch_image_urls(session, browser_context),
                    processed_image_urls,
                    processed_image_hashes,
                    session,
                    browser_context,
                    queue
                )

            await asyncio.sleep(constants.LOL_MYTHIC_SHOP_CHECK_EVERY_SECONDS)


def start_lol_mythic_shop_checker_process(queue: multiprocessing.Queue) -> Never:
    # noinspection PyUnreachableCode
    asyncio.run(LolMythicShopBot.run_lol_mythic_shop_checker(queue))
