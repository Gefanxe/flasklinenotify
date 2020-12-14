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


@app.route('/insertone')
def insertone():
    myVar = 'sql insert'
    return f'insertone! {myVar}'


@app.route('/selectone')
def selectone():
    with conn.cursor() as cursor:
        sql = "SELECT `name`, `tel`, `created_date` FROM friends WHERE `id` = %s"
        cursor.execute(sql, (1))
        result = cursor.fetchone()
        print(result)
    return jsonify(result)


@app.route('/redirect')
def url_redirect():
    google = 'https://www.google.com.tw/search?sxsrf=ALeKk03lPH3tlko-TOzlVHn4KtLcf6Je4g%3A1607906661711&source=hp&ei=ZbXWX7CjKcWlmAXDl6Jo&q=%E8%96%A9%E7%88%BE%E9%81%94%E7%84%A1%E9%9B%99%E7%81%BD%E5%8E%84%E5%95%9F%E7%A4%BA%E9%8C%84&oq=&gs_lcp=CgZwc3ktYWIQAxgIMgcIIxDqAhAnMgcIIxDqAhAnMgcIIxDqAhAnMgcIIxDqAhAnMgcIIxDqAhAnMgcIIxDqAhAnMgcIIxDqAhAnMgcIIxDqAhAnMgcIIxDqAhAnMgcIIxDqAhAnUABYAGChtApoAXAAeACAAQCIAQCSAQCYAQCqAQdnd3Mtd2l6sAEK&sclient=psy-ab'
    return redirect(google)


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)

# sql 查詢
