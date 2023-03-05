__all__ = ['UberEatsBot']

import asyncio
import datetime
import random
from abc import ABC

import flanautils
import playwright.async_api
import pyperclip
from multibot import MultiBot, group

import constants
from flanabot.models import Chat, Message


# ---------------------------------------------------------------------------------------------------- #
# --------------------------------------------- POLL_BOT --------------------------------------------- #
# ---------------------------------------------------------------------------------------------------- #
class UberEatsBot(MultiBot, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.playwright: playwright.async_api.Playwright | None = None
        self.browser: playwright.async_api.Browser | None = None
        self.tasks = {}

    # -------------------------------------------------------- #
    # ------------------- PROTECTED METHODS ------------------ #
    # -------------------------------------------------------- #
    def _add_handlers(self):
        super()._add_handlers()

        self.register(self._on_ubereats, 'ubereats', priority=2)

    async def _cancel_scraping_task(self, chat: Chat):
        if not (task := self.tasks.get(chat.id)) or task.done():
            return

        await self._close_playwright()
        task.cancel()
        del self.tasks[chat.id]

    async def _close_playwright(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _scrape_codes(self, chat: Chat) -> list[str]:
        codes = []

        self.playwright = await playwright.async_api.async_playwright().start()

        chat.pull_from_database(overwrite_fields=('ubereats_cookies',))
        for i, cookies in enumerate(chat.ubereats_cookies):
            for _ in range(3):
                try:
                    self.browser = await self.playwright.chromium.launch()
                    context: playwright.async_api.BrowserContext = await self.browser.new_context()
                    await context.add_cookies(cookies)

                    page = await context.new_page()
                    await page.goto('https://www.myunidays.com/ES/es-ES/partners/ubereats/access/online')

                    if button := await page.query_selector("button[class='button highlight']"):
                        await button.click()
                    else:
                        await page.click("'Revelar código'")
                    while len(context.pages) != 2:
                        await asyncio.sleep(0.5)
                    page = context.pages[1]

                    if not (new_code_button := await page.query_selector("button[class='getNewCode button secondary']")):
                        new_code_button = await page.query_selector("'Obtener nuevo código'")
                    if new_code_button and await new_code_button.is_enabled():
                        await new_code_button.click()
                    await page.wait_for_load_state('networkidle')

                    if code_input := await page.query_selector("input[class='code toCopy']"):
                        code = await code_input.input_value()
                    else:
                        if button := await page.query_selector("button[class='copy button quarternary']"):
                            await button.click()
                        else:
                            await page.click("'Copiar'")
                        code = pyperclip.paste()
                    codes.append(code)

                    chat.ubereats_cookies[i] = await context.cookies('https://www.myunidays.com')

                except playwright.async_api.Error:
                    pass
                else:
                    break
                finally:
                    if self.browser:
                        await self.browser.close()

        if self.playwright:
            await self.playwright.stop()

        chat.save()

        return codes

    # ---------------------------------------------- #
    #                    HANDLERS                    #
    # ---------------------------------------------- #
    @group(False)
    async def _on_ubereats(self, message: Message):
        if not message.chat.ubereats_cookies:
            return

        time = flanautils.text_to_time(message.text)
        if not time:
            bot_state_message = await self.send(random.choice(constants.SCRAPING_PHRASES), message)
            await self.send_ubereats_code(message.chat)
            await self.delete_message(bot_state_message)
            return

        if time < datetime.timedelta(days=1, minutes=5):
            await self.send('El mínimo es 1 día y 5 minutos.', message)
            return

        seconds = int(time.total_seconds())
        message.chat.ubereats_seconds = seconds
        message.save()
        period = flanautils.TimeUnits(seconds=seconds)
        await self.send(f'A partir de ahora te enviaré un código de UberEats cada <b>{period.to_words()}</b>.', message)
        await self.start_ubereats(message.chat)

    # -------------------------------------------------------- #
    # -------------------- PUBLIC METHODS -------------------- #
    # -------------------------------------------------------- #
    async def send_ubereats_code(self, chat: Chat):
        new_codes = []
        for code in await self._scrape_codes(chat):
            new_codes.append(code)

            if code in chat.ubereats_last_codes:
                warning_text = '<i>Código ya enviado anteriormente:</i>'
            else:
                warning_text = ''
            await self.send(f'{warning_text}  <code>{code}</code>', chat, silent=True)

        chat.ubereats_last_codes = new_codes
        chat.save()

    async def start_ubereats(self, chat: Chat, send_code_now=True):
        await self._cancel_scraping_task(chat)
        chat.config['ubereats'] = True
        chat.save(pull_overwrite_fields=('ubereats_cookies',))
        self.tasks[chat.id] = await flanautils.do_every(chat.ubereats_seconds, self.send_ubereats_code, chat, do_first_now=send_code_now)

    async def stop_ubereats(self, chat: Chat):
        await self._cancel_scraping_task(chat)
        chat.config['ubereats'] = False
        chat.save(pull_overwrite_fields=('ubereats_cookies',))
