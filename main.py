import requests
import os
from flask import Flask
from flask import request
from flask import jsonify
from flask_sslify import SSLify
from bs4 import BeautifulSoup

token = os.getenv('TOKEN')
URL = 'https://api.telegram.org/bot' + token + '/'
proxies = {'https': 'http://193.85.228.180:	36247'}

app = Flask(__name__)
sslify = SSLify(app)


# ////////////////////////

def get_html(url):
    html = requests.get(url)
    return html.text


def get_group_url(number_of_group):
    f = open('text')
    group_url = 'Не удалось найти расписание'
    for line in f:
        if number_of_group.lower() in line:
            group_url = 'http://edu.sfu-kras.ru/timetable' + line[line.find('?'):-1]
            break
    f.close()
    return group_url


def get_timetable_week(html, type='текущая неделя'):
    soup = BeautifulSoup(html, 'lxml')

    type_of_week = soup.find('div', class_='content').find('p').find('b').text[5:]

    # Все строчки таблицы
    table = soup.find('table', class_='table timetable')
    week = ''

    if type == 'текущая неделя':
        # текущая неделя
        for row in table:
            if hasattr(row.find('th', colspan=4), 'text'):
                week += '\n'
                week += '{0}/{1}/{2}'.format(row.find('th', colspan=4).text.upper(), type_of_week, type) + '\n'

            if hasattr(row.find('td', width='1%'), 'text'):
                if hasattr(row.find('td', class_='nobr'), 'text'):
                    if hasattr(row.find('td', class_='light', width='40%').find('b'), 'text'):
                        if hasattr(row.find('td', class_='light', width='40%'), 'contents'):
                            if hasattr(row.find('td', class_='light', width='40%').find('em'), 'text'):
                                week += '{0} {1} {2}{3} /{4}/ Аудитория: {5}'.format(row.find('td', width='1%').text,
                                                                                     row.find('td', class_='nobr').text,
                                                                                     row.find('td', class_='light',
                                                                                              width='40%').find(
                                                                                         'b').text,
                                                                                     row.find('td', class_='light',
                                                                                              width='40%').contents[1],
                                                                                     row.find('td', class_='light',
                                                                                              width='40%').find(
                                                                                         'em').text,
                                                                                     row.find('td', class_='light',
                                                                                              width='40%').find(
                                                                                         'b').findNextSibling(
                                                                                         'a').text) + '\n'
                            else:
                                week += '{0} {1} {2}'.format(row.find('td', width='1%').text,
                                                             row.find('td', class_='nobr').text,
                                                             row.find('td', class_='light', width='40%').find(
                                                                 'b').text) + '\n'

    elif type in ['нечет', 'нечетная', 'нечетная неделя', '1']:
        # нечетная неделя
        for row in table:
            if hasattr(row.find('th', colspan=4), 'text'):
                week += '\n'
                week += '{0}/{1}'.format(row.find('th', colspan=4).text.upper(), 'нечетная неделя') + '\n'

            if hasattr(row.find('td', width='1%'), 'text'):
                if hasattr(row.find('td', class_='nobr'), 'text'):
                    if hasattr(row.find('td', width='40%').find('b'), 'text'):
                        if hasattr(row.find('td', width='40%'), 'contents'):
                            if hasattr(row.find('td', width='40%').find('em'), 'text'):
                                week += '{0} {1} {2}{3} /{4}/ Аудитория: {5}'.format(row.find('td', width='1%').text,
                                                                                     row.find('td', class_='nobr').text,
                                                                                     row.find('td',
                                                                                              width='40%').find(
                                                                                         'b').text,
                                                                                     row.find('td',
                                                                                              width='40%').contents[1],
                                                                                     row.find('td',
                                                                                              width='40%').find(
                                                                                         'em').text,
                                                                                     row.find('td',
                                                                                              width='40%').find(
                                                                                         'b').findNextSibling(
                                                                                         'a').text) + '\n'
                            else:
                                week += '{0} {1} {2}'.format(row.find('td', width='1%').text,
                                                             row.find('td', class_='nobr').text,
                                                             row.find('td', width='40%').find(
                                                                 'b').text) + '\n'
    elif type in ['чет', 'четная', 'четная неделя', '2']:
        # четная неделя
        for row in table:
            if hasattr(row.find('th', colspan=4), 'text'):
                week += '\n'
                week += '{0}/{1}'.format(row.find('th', colspan=4).text.upper(), 'четная неделя') + '\n'

            if hasattr(row.find('td', width='1%'), 'text'):
                if hasattr(row.find('td', class_='nobr'), 'text'):
                    if hasattr(row.find('td', width='40%').find('b'), 'text'):
                        a = row.find('td', width='40%').nextSibling

                        if a is None:
                            a = row.find('td', width='40%')

                        elif a.find('b') is None:
                            continue

                        if hasattr(row.find('td', width='40%'), 'contents'):
                            if hasattr(row.find('td', width='40%').find('em'), 'text'):
                                week += '{0} {1} {2}{3} /{4}/ Аудитория: {5}'.format(row.find('td', width='1%').text,
                                                                                     row.find('td', class_='nobr').text,
                                                                                     a.find('b').text,
                                                                                     a.contents[1],
                                                                                     a.find('em').text,
                                                                                     a.find('b').findNextSibling(
                                                                                         'a').text) + '\n'

                            else:
                                week += '{0} {1} {2}'.format(row.find('td', width='1%').text,
                                                             row.find('td', class_='nobr').text,
                                                             a.find('b').text) + '\n'

    return week


def get_timetable_day(html, day):
    soup = BeautifulSoup(html, 'lxml')
    type_of_week = soup.find('div', class_='content').find('p').find('b').text[5:]
    table = soup.find('table', class_='table timetable')
    timetable_day = ''

    for row in table:
        if hasattr(row.find('th', colspan=4), 'text'):
            if row.find('th', colspan=4).text == day:
                timetable_day += '{0}/{1}'.format(row.find('th', colspan=4).text.upper(), type_of_week) + '\n'
                temp = '{0}/{1}'.format(row.find('th', colspan=4).text.upper(), type_of_week) + '\n'
                row = row.findNext('tr')
                row = row.findNext('tr')

                try:
                    while row.find('td'):
                        if hasattr(row.find('td', width='1%'), 'text'):
                            if hasattr(row.find('td', class_='nobr'), 'text'):
                                if hasattr(row.find('td', class_='light', width='40%').find('b'), 'text'):
                                    if hasattr(row.find('td', class_='light', width='40%'), 'contents'):
                                        if hasattr(row.find('td', class_='light', width='40%').find('em'), 'text'):
                                            timetable_day += '{0} {1} {2}{3} /{4}/ Аудитория: {5}'.format(
                                                row.find('td', width='1%').text,
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
                                            timetable_day += '{0} {1} {2}'.format(row.find('td', width='1%').text,
                                                                                  row.find('td', class_='nobr').text,
                                                                                  row.find('td', class_='light',
                                                                                           width='40%').find(
                                                                                      'b').text) + '\n'
                        row = row.findNext('tr')
                except(AttributeError):
                    pass

    if timetable_day == '' or timetable_day == temp:
        timetable_day = 'Расписания на этот день нет'
    return timetable_day


def user_massages_handler(chat_id, message):
    message = message.lower().lstrip().rstrip()

    dic_days = {'пн': 'понедельник',
                'вт': 'вторник',
                'ср': 'среда',
                'чт': 'четверг',
                'пт': 'пятница',
                'сб': 'суббота'}

    types_of_week = ['нечет', 'нечетная', 'нечетная неделя', '1', 'чет', 'четная', 'четная неделя', '2']

    # начало
    if message == '/start':
        send_message(chat_id, 'тут должно быть вступление, но его пока нет')

    # день недели
    elif ' ' in message:
        start = message.index(' ')
        number_of_group = message[:start]
        second_part = message[start + 1:]

        # неправильный запрос
        if get_group_url(number_of_group) == 'Не удалось найти расписание':
            send_message(chat_id)
        else:
            # расписание на день
            if second_part in dic_days or dic_days.values():
                send_message(chat_id, get_timetable_day(get_html(get_group_url(number_of_group)), second_part))
            # расписание на определенную неделю
            elif second_part in types_of_week:
                send_message(chat_id, get_timetable_week(get_html(get_group_url(number_of_group)), second_part))

    # неделя текущая
    else:
        group_url = get_group_url(message)
        if group_url == 'Не удалось найти расписание':
            send_message(chat_id, group_url)
        elif group_url != 'Не удалось найти расписание':
            send_message(chat_id, get_timetable_week(get_html(group_url)))


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

        user_massages_handler(chat_id, message)

        return jsonify(r)
    return 'kek'


if __name__ == '__main__':
    app.run()
