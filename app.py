import uuid
from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime
import pymysql
import pymysql.cursors

from lotify.client import Client

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

# 註冊頁
@app.route("/register")
def register():
    link = lotify.get_auth_link(state=uuid.uuid4())
    return render_template("register.html", auth_url=link)

# 將通知人與UUID先存起來,待之後拿到Token對應起來放
@app.route("/registerto", methods=["POST"])
def registerto():
    notifyUser = request.form.get("notifyUser")
    userUuid = uuid.uuid4()
    iid = 0
    with conn.cursor() as cursor:
        sql = "INSERT INTO notify_list(`notifyUser`, `uuid`, `regisDate`) VALUES(%s, %s, NOW())"
        try:
            cursor.execute(sql, (notifyUser, userUuid))
            conn.commit()
        except:
            conn.rollback()
        iid = cursor.lastrowid
    return iid

@app.route("/index")
def home():
    link = lotify.get_auth_link(state=uuid.uuid4())
    return render_template("notify_index.html", auth_url=link)


@app.route("/callback")
def confirm():
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
    return "!!!!" + repr(error)

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)

# if __name__ == '__main__':
#     app.run()
