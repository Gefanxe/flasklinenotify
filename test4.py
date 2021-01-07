import uuid
from flask import Flask, render_template, request, Response, jsonify, redirect, has_request_context, copy_current_request_context
from functools import wraps
from concurrent.futures import Future, ThreadPoolExecutor
import os
from datetime import datetime
import pymysql
import pymysql.cursors
import asyncio
import aiohttp
import json
import time
from aiostream.stream import list as alist

loop = asyncio.get_event_loop()

def run_async(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        call_result = Future()

        def _run():
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(func(*args, **kwargs))
            except Exception as error:
                call_result.set_exception(error)
            else:
                call_result.set_result(result)
            finally:
                loop.close()

        loop_executor = ThreadPoolExecutor(max_workers=1)
        if has_request_context():
            _run = copy_current_request_context(_run)
        loop_future = loop_executor.submit(_run)
        loop_future.result()
        return call_result.result()

    return _wrapper

app = Flask(
    __name__,
    static_url_path='',
    static_folder='static'
)


@app.route('/')
def hello_world():
    now = datetime.now()
    return f'Hello, World! {now.strftime("%Y%m/%d %H:%M:%S")}'


@app.route("/progresstest", methods=['GET'])
def progresstest():
    title = "進度條測試"
    return render_template("mng/progress_test.jinja", htmlTitle=title)


@app.route('/progress', methods=['GET'])
def progress():
    def generate():
        x = 0

        while x <= 100:
            yield "data:" + str(x) + "\n\n"
            x = x + 10
            time.sleep(0.5)

    return Response(generate(), mimetype='text/event-stream')


async def fetch(url, semaphore):
    async with semaphore:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.read()


async def run():
    url = 'http://localhost:3000/delay?_id={0}'
    semaphore = asyncio.Semaphore(500)  # 限制併發量為500
    to_get = [fetch(url.format(idx), semaphore) for idx, value in enumerate(range(10))]  # 總共1000任務
    # await asyncio.wait(to_get)
    # results = await asyncio.gather(*to_get, return_exceptions=True)
    # print(results)
    for first_completed in asyncio.as_completed(to_get):
        res = json.loads(await first_completed)
        # print('y', res)
        yield res
        # res = await first_completed
        # r = json.loads(res)
        # print(f'Done {r.get("id")}')


@app.route('/progress2', methods=['GET'])
@run_async
async def progress2():
    async def generate():
        for r in loop.run_until_complete(run()):
            yield await r

    # res = loop.run_until_complete(run())
    # loop.close()
    return Response(generate(), mimetype='text/event-stream')