import os

import flanautils

os.environ |= flanautils.find_environment_variables('../.env')

import asyncio

from flanabot.bots.flana_disc_bot import FlanaDiscBot
from flanabot.bots.flana_tele_bot import FlanaTeleBot


async def main():
    flana_disc_bot = FlanaDiscBot()
    flana_tele_bot = FlanaTeleBot()

    await asyncio.gather(
        flana_disc_bot.start(),
        flana_tele_bot.start()
    )


if __name__ == '__main__':
    asyncio.run(main())
