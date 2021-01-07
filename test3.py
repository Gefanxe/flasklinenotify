import time
import asyncio
import aiohttp
import json


url = 'http://localhost:3000/delay?_id={0}'


async def fetch(url, semaphore):
    async with semaphore:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.read()


async def run():
    semaphore = asyncio.Semaphore(500)  # 限制併發量為500
    to_get = [fetch(url.format(idx), semaphore) for idx, value in enumerate(range(10))]  # 總共1000任務
    # await asyncio.wait(to_get)
    # results = await asyncio.gather(*to_get, return_exceptions=True)
    # print(results)
    for first_completed in asyncio.as_completed(to_get):
        res = await first_completed
        r = json.loads(res)
        print(f'Done {r.get("id")}')


if __name__ == '__main__':
    #  now=lambda :time.time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
