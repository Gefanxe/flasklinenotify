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

from lotify.client import Client


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

conn = pymysql.connect(host=os.getenv("CLEARDB_DATABASE_HOST"),
                       user=os.getenv("CLEARDB_DATABASE_USER"),
                       password=os.getenv("CLEARDB_DATABASE_PASSWORD"),
                       db=os.getenv("CLEARDB_DATABASE_DB"),
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

CLIENT_ID = os.getenv("LINE_CLIENT_ID")
SECRET = os.getenv("LINE_CLIENT_SECRET")
URI = os.getenv("LINE_REDIRECT_URI")
lotify = Client(client_id=CLIENT_ID, client_secret=SECRET, redirect_uri=URI)

# 給 cron-job.org 打的API, 為了不要讓heroku在指定時間內睡著


@app.route('/')
def hello_world():
    now = datetime.now()
    # print('env:', os.getenv("CLEARDB_DATABASE_USER"))
    return f'Hello, World! {now.strftime("%Y%m/%d %H:%M:%S")}'

# region APP ==================================================================

# 註冊頁


@app.route("/register", methods=['GET'])
def register():
    title = "註冊通知"
    return render_template("app/register.html", htmlTitle=title)

# 將通知人與UUID先存起來,待之後拿到Token對應起來放


@app.route("/registerto", methods=["POST"])
def registerto():
    notifyUser = request.form.get("notifyUser")
    userUuid = uuid.uuid4().hex
    iid = 0
    with conn.cursor() as cursor:
        sql = "INSERT INTO notify_list(`notifyUser`, `uuid`, `regisDate`) VALUES(%s, %s, NOW());"
        try:
            cursor.execute(sql, (notifyUser, userUuid))
            conn.commit()
        except:
            print('insert error: ', cursor)
            conn.rollback()
        iid = cursor.lastrowid
    if iid == 0:
        # TODO: 資料新增失敗頁(頁面上要有導回register的按鈕)
        return render_template("app/regist_fail.html", reason="sql insert fail")
    else:
        link = lotify.get_auth_link(state=userUuid)
        return redirect(link)

# 寫回資料庫對應UUID的Token


@app.route("/lncallback")
def lncallback():
    uuid = request.args.get("state")
    token = lotify.get_access_token(code=request.args.get("code"))

    affected_rows = 0
    with conn.cursor() as cursor:
        sql = "UPDATE notify_list SET token = %s WHERE uuid = %s"
        try:
            cursor.execute(sql, (token, uuid))
            conn.commit()
        except pymysql.InternalError as e:
            print('sql: ', cursor._executed)
            print('sql error: ', e.args)
            conn.rollback()
        affected_rows = cursor.rowcount
    if affected_rows > 0:
        # TODO: 更新成功頁面
        return render_template("app/regist_success.html", userToken=token)
    else:
        # TODO: 更新失敗頁面
        return render_template("app/regist_fail.html", reason="update token fail")


@app.route("/lnrevoke", methods=["POST"])
def lnrevoke():
    payload = request.get_json()
    userToken = payload.get("token")

    # affected_rows = 0
    with conn.cursor() as cursor:
        sql = "UPDATE notify_list SET revokeDate = NOW() WHERE token = %s AND revokeDate IS NULL"
        try:
            cursor.execute(sql, (userToken))
            conn.commit()
        except pymysql.InternalError as e:
            print('sql: ', cursor._executed)
            print('sql error: ', e.args)
            conn.rollback()
        affected_rows = cursor.rowcount

    print("affected_rows:", affected_rows)
    if affected_rows > 0:
        response = lotify.revoke(access_token=userToken)
        returnResult = response.get("message")
    else:
        returnResult = {
            "result": "no records"
        }
    return jsonify(result=returnResult)

# endregion APP

# region MNG ==================================================================


@app.route("/dashboard", methods=['GET'])
def dashboard():
    title = "主控台"
    return render_template("mng/dashboard.html", htmlTitle=title)


@app.route("/progresstest", methods=['GET'])
def progresstest():
    title = "進度條測試"
    return render_template("mng/progress_test.html", htmlTitle=title)

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
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for first_completed in asyncio.as_completed(to_get):
        # res = await first_completed
        # r = json.loads(res)
        yield loop.run_until_complete(first_completed)

@app.route("/progress", methods=['GET'])
# @run_async
def progress():
    # loop = asyncio.get_event_loop()
    # run()
    # loop.run_until_complete(run())
    
    # done, obj = loop.run_until_complete(run())
    # # return jsonify(result=res)
    # returnResult = {
    #     "result": "no records"
    # }
    # return jsonify(result=returnResult)
    for element in run():
        print('e', element)
        # Response(element, mimetype='text/event-stream')
    return "Health check passed"

# @app.route('/progress')
# def progress():
#     def generate():
#         x = 0

#         while x <= 100:
#             yield "data:" + str(x) + "\n\n"
#             x = x + 10
#             time.sleep(0.5)

#     return Response(generate(), mimetype='text/event-stream')


# endregion MNG

# ====================以下待整理==========================================
@app.route("/index")
def home():
    link = lotify.get_auth_link(state=uuid.uuid4())
    return render_template("notify_index.html", auth_url=link)


@app.route("/callback")
def confirm():
    print('request.args', request.args)
    token = lotify.get_access_token(code=request.args.get("code"))
    return render_template("notify_confirm.html", token=token)


@app.route("/notify/send", methods=["POST"])
def send():
    payload = request.get_json()
    response = lotify.send_message(
        access_token=payload.get("token"), message=payload.get("message")
    )
    return jsonify(result=response.get("message")), response.get("status")


@app.route("/notify/send/sticker", methods=["POST"])
def send_sticker():
    payload = request.get_json()
    response = lotify.send_message_with_sticker(
        access_token=payload.get("token"),
        message=payload.get("message"),
        sticker_id=630,
        sticker_package_id=4,
    )
    return jsonify(result=response.get("message")), response.get("status")


@app.route("/notify/send/url", methods=["POST"])
def send_url():
    payload = request.get_json()
    response = lotify.send_message_with_image_url(
        access_token=payload.get("token"),
        message=payload.get("message"),
        image_fullsize=payload.get("url"),
        image_thumbnail=payload.get("url"),
    )
    return jsonify(result=response.get("message")), response.get("status")


@app.route("/notify/send/path", methods=["POST"])
def send_file():
    payload = request.get_json()
    response = lotify.send_message_with_image_file(
        access_token=payload.get("token"),
        message=payload.get("message"),
        file=open("./test_data/dog.png", "rb"),
    )
    return jsonify(result=response.get("message")), response.get("status")


@app.route("/notify/revoke", methods=["POST"])
def revoke():
    payload = request.get_json()
    response = lotify.revoke(access_token=payload.get("token"))
    return jsonify(result=response.get("message")), response.get("status")

# 錯誤處理


@app.errorhandler(Exception)
def exception_handler(error):
    print('Exception error: ', error)
    # return "!!!!" + repr(error)

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)

# if __name__ == '__main__':
#     app.run()
