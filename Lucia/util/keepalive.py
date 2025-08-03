import asyncio
import aiohttp
import traceback
from info import *
from logging import LOGGER


async def ping_server():
    sleep_time = PING_INTERVAL
    while True:
        await asyncio.sleep(sleep_time)
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.get(URL) as resp:
                    LOGGER("Pinged server with response: {}".format(resp.status))
        except TimeoutError:
            LOGGER("Couldn't connect to the site URL..!")
        except Exception:
            traceback.print_exc()
