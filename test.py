import uuid
from flask import Flask, render_template, request, jsonify, url_for, redirect
import os

import pymysql
import pymysql.cursors

from datetime import datetime

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


@app.route('/')
def hello_world():
    now = datetime.now()
    return f'Hello, World! {now.strftime("%Y%m/%d %H:%M:%S")}'


@app.route('/resjson', methods=["POST"])
def resjson():
    data = {
        "id": 1,
        "name": "Andersen"
    }
    return jsonify(data)


@app.route('/test')
def test():
    return f'{uuid.uuid4()}'


@app.route('/testform')
def testform():
    title = "測試表單"
    return render_template("testform.html", htmlTitle=title)


@app.route('/testformto', methods=["POST"])
def testformto():

    print('payload', request.form)
    form = request.form
    uname = form['uname']  # or: request.form.get('uname')
    return f'data is: {uname}'


@app.route('/selectone')
def selectone():
    with conn.cursor() as cursor:
        sql = "SELECT `name`, `tel`, `created_date` FROM friends WHERE `id` = %s"
        cursor.execute(sql, (1))
        result = cursor.fetchone()
        print(result)
    return jsonify(result)


@app.route("/insertone/<uname>/<utel>")
def insertone(uname, utel):
    iid = 0
    with conn.cursor() as cursor:
        sql = "INSERT INTO friends(`name`, `tel`) VALUES(%s, %s)"
        try:
            cursor.execute(sql, (uname, utel))
            conn.commit()
        except:
            print('insert fail')
            conn.rollback()
        print('sql str:', cursor._last_executed)
        iid = cursor.lastrowid
    return f'{iid}'

@app.route("/updateone/<token>/<uuid>")
def updateone(token, uuid):
    iid = 0
    with conn.cursor() as cursor:
        sql = "UPDATE notify_list SET token = %s WHERE uuid = %s"
        try:
            cursor.execute(sql, (token, uuid))
            conn.commit()
        except:
            print('update fail')
            conn.rollback()
        print('sql str:', cursor._last_executed)
        affected_rows = cursor.rowcount
    return f'{affected_rows}'

@app.route('/redirect')
def url_redirect():
    google = 'https://www.google.com.tw/search?sxsrf=ALeKk03lPH3tlko-TOzlVHn4KtLcf6Je4g%3A1607906661711&source=hp&ei=ZbXWX7CjKcWlmAXDl6Jo&q=%E8%96%A9%E7%88%BE%E9%81%94%E7%84%A1%E9%9B%99%E7%81%BD%E5%8E%84%E5%95%9F%E7%A4%BA%E9%8C%84&oq=&gs_lcp=CgZwc3ktYWIQAxgIMgcIIxDqAhAnMgcIIxDqAhAnMgcIIxDqAhAnMgcIIxDqAhAnMgcIIxDqAhAnMgcIIxDqAhAnMgcIIxDqAhAnMgcIIxDqAhAnMgcIIxDqAhAnMgcIIxDqAhAnUABYAGChtApoAXAAeACAAQCIAQCSAQCYAQCqAQdnd3Mtd2l6sAEK&sclient=psy-ab'
    return redirect(google)


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)

# sql 查詢
def sql_select(sql):

    return ""
