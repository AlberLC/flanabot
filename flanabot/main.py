import os

import flanautils

os.environ |= flanautils.find_environment_variables('../.env')

import asyncio
from multibot import TwitchBot
from flanabot.bots.flana_disc_bot import FlanaDiscBot
from flanabot.bots.flana_tele_bot import FlanaTeleBot


async def main():
    flana_disc_bot = FlanaDiscBot()
    flana_tele_bot = FlanaTeleBot()
    t = TwitchBot(
        bot_token=os.environ['TWITCH_ACCESS_TOKEN'],
        initial_channels=['flanaganvaquero'],
        owner_name='flanaganvaquero'
    )

    @t.register(always=True)
    async def asd(message):
        await t.send('@flanaganvaquero adios', message, reply_to=message)
        # await message.chat.original_object._ws.reply(message.id, f"PRIVMSG #{message.author.name.lower()} :awdwhkajwd\r\n")
        # await message.original_object.channel.reply('asd')
        # m = await t.send('hola', message, reply_to=message.id)
        # await t.send('me respondo a mi mismo', message, reply_to=m)

    await asyncio.gather(
        flana_disc_bot.start(),
        flana_tele_bot.start(),
        t.start()
    )


if __name__ == '__main__':
    asyncio.run(main())
