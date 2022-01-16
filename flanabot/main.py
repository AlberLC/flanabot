import os

import flanautils

os.environ |= flanautils.find_environment_variables('../.env')

import asyncio

from flanabot.bots.flana_tele_bot import FlanaTeleBot


async def main():
    flana_tele_bot = FlanaTeleBot()

    await asyncio.gather(
        flana_tele_bot.start()
    )


if __name__ == '__main__':
    asyncio.run(main())
