import os
from flask import Flask, request, jsonify
from flask_sslify import SSLify
from environs import Env

env = Env()
env.read_env()

DATABASE_URL = env.dj_db_url('DATABASE_URL')
TOKEN = os.getenv('TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
URL = 'https://api.telegram.org/bot' + TOKEN + '/'
URL_TIMETABLE = 'http://edu.sfu-kras.ru/timetable'

app = Flask(__name__)
sslify = SSLify(app)


from controller import user_massages_handler


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        r = request.get_json()
        chat_id = r['message']['chat']['id']
        message = r['message']['text']

        user_massages_handler(chat_id, message)

        return jsonify(r)
    return 'kek'
