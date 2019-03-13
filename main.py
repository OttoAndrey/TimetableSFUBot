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

def get_html(url):
    html = requests.get(url[:-1])
    return html.text

def get_group_url(user_message):
    f = open('text')
    group_url = 'Не удалось найти расписание'
    for line in f:
        if user_message.lower() in line:
            group_url = 'http://edu.sfu-kras.ru/timetable' + line[line.find('?'):]
            break

    return group_url

def get_timetable_week(html):
    soup = BeautifulSoup(html, 'lxml')

    type_of_week = soup.find('div', class_='content').find('p').find('b').text[5:]

    # Все строчки таблицы
    table = soup.find('table', class_='table timetable')
    week = ''

    for row in table:
        if hasattr(row.find('th', colspan=4), 'text'):
            week += '{0}/{1}'.format(row.find('th', colspan=4).text.upper(), type_of_week) + '\n'

        if hasattr(row.find('td', width='1%'), 'text'):
            if hasattr(row.find('td', class_='nobr'), 'text'):
                if hasattr(row.find('td', class_='light', width='40%').find('b'), 'text'):
                    if hasattr(row.find('td', class_='light', width='40%'), 'contents'):
                        if hasattr(row.find('td', class_='light', width='40%').find('em'), 'text'):
                            week += '{0} {1} {2}{3} /{4}/ Аудитория: {5}'.format(row.find('td', width='1%').text,
                                                                             row.find('td', class_='nobr').text,
                                                                             row.find('td', class_='light',
                                                                                      width='40%').find('b').text,
                                                                             row.find('td', class_='light',
                                                                                      width='40%').contents[1],
                                                                             row.find('td', class_='light',
                                                                                      width='40%').find('em').text,
                                                                             row.find('td', class_='light',
                                                                                      width='40%').find(
                                                                                 'b').findNextSibling('a').text) + '\n'
                        else:
                            week += '{0} {1} {2}'.format(row.find('td', width='1%').text,
                                                               row.find('td', class_='nobr').text,
                                                               row.find('td', class_='light', width='40%').find(
                                                                   'b').text) + '\n'

    return week
# ////////////////////////////

def send_message(chat_id, text='Не удалось найти расписание'):
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

        group_url = get_group_url(message)

        if group_url != 'Не удалось найти расписание':
            send_message(chat_id, get_timetable_week(get_html(group_url)))
        elif group_url == 'Не удалось найти расписание':
            send_message(chat_id)

        return jsonify(r)
    return 'kek'

if __name__ == '__main__':
    app.run()