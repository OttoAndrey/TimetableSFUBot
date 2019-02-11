import requests
from flask import Flask
from flask import request
from flask import jsonify
from flask_sslify import SSLify
from bs4 import BeautifulSoup

token = '649594459:AAH1hu90_ZrEhAtZehVDL9xYvkiE2MnLvhU'
URL = 'https://api.telegram.org/bot' + token + '/'
proxies = {'https': 'http://193.85.228.180:	36247'}

app = Flask(__name__)
sslify = SSLify(app)

# ////////////////////////
URL_of_group = ""

def get_html(url):
    r = requests.get(url)
    return r.text

def get_timetable_week(html):
    timetable = ''
    soup = BeautifulSoup(html, 'lxml')
    trows = soup.find('table', class_='table timetable').find_all('tr', class_='table-center')
    for row in trows:
        timetable += row.text + '\n'

    return timetable
# ////////////////////////////

def send_message(chat_id, text='wait, please'):
    url = URL + 'sendMessage'
    answer = {'chat_id': chat_id, 'text': text}
    r = requests.post(url, json=answer)
    return r.json()

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        r = request.get_json()
        chat_id = r['message']['chat']['id']
        message = r['message']['text']

        if message == 'Ки15-17б':
            URL_of_group = 'http://edu.sfu-kras.ru/timetable?group=КИ15-17б'
        elif message == 'Сб18-11б':
            URL_of_group = 'http://edu.sfu-kras.ru/timetable?group=СБ18+-+11Б'

        # ответ
        send_message(chat_id, get_timetable_week(get_html(URL_of_group)))

        return jsonify(r)
    return 'kek'

if __name__ == '__main__':
    app.run()