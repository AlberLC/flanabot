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
        self.tasks: dict = {
            7749879: None
        }

    # -------------------------------------------------------- #
    # ------------------- PROTECTED METHODS ------------------ #
    # -------------------------------------------------------- #
    def _add_handlers(self):
        super()._add_handlers()

        self.register(self._on_ubereats, 'ubereats', priority=2)

    @staticmethod
    async def _scrape_code(chat: Chat) -> str:
        async with playwright.async_api.async_playwright() as playwright_:
            async with await playwright_.chromium.launch() as browser:
                context: playwright.async_api.BrowserContext = await browser.new_context()
                await context.add_cookies(chat.ubereats_cookies)
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

                chat.ubereats_cookies = await context.cookies('https://www.myunidays.com')
                chat.save()

                return code

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
        code = await self._scrape_code(chat)

        if chat.ubereats_last_code == code:
            warning_text = '<i>Código ya enviado anteriormente:</i>'
        else:
            chat.ubereats_last_code = code
            chat.save()
            warning_text = ''

        await self.send(f'{warning_text}  <code>{code}</code>', chat, silent=True)

    async def start_ubereats(self, chat: Chat, send_code_now=True):
        chat.config['ubereats'] = True
        chat.save()
        if self.tasks[chat.id]:
            self.tasks[chat.id].cancel()
        self.tasks[chat.id] = await flanautils.do_every(chat.ubereats_seconds, self.send_ubereats_code, chat, do_first_now=send_code_now)

    def stop_ubereats(self, chat: Chat):
        chat.config['ubereats'] = False
        chat.save()
        if self.tasks[chat.id]:
            self.tasks[chat.id].cancel()
            self.tasks[chat.id] = None
