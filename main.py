import requests
import os
import re
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


def get_teacher_url(message):
    message = message.split(' ')
    teacher_url = 'http://edu.sfu-kras.ru/timetable?teacher={0}+{1}+{2}'.format(message[0], message[1], message[2])
    return teacher_url


def get_group_url(number_of_group):
    f = open('text')
    group_url = 'Не удалось найти группу'
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
                                week += ':small_blue_diamond:{0} {1} {2}{3} /{4}/ Аудитория: {5}'.format(
                                    row.find('td', width='1%').text,
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

    elif type in ['нечет', 'нечетная', 'нечетная неделя', 'нечёт', 'нечётная', 'нечётная неделя', '1']:
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
    elif type in ['чет', 'четная', 'четная неделя', 'чёт', 'чётная', 'чётная неделя', '2']:
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


def get_timetable_teacher(html, type='текущая неделя'):
    soup = BeautifulSoup(html, 'lxml')
    teacher_name = soup.find('h3').text.title()
    type_of_week = soup.find('div', class_='content').find('p').find('b').text[5:]
    table = soup.find('table', class_='table timetable')

    week = '' + teacher_name + '\n'

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
                                week += ':small_blue_diamond:{0} {1} {2} |{3}{4}| Каб: {5}'.format(
                                    row.find('td', width='1%').text,
                                    row.find('td', class_='nobr').text,
                                    row.find('td', class_='light',
                                             width='40%').find(
                                        'a').text,
                                    row.find('td', class_='light',
                                             width='40%').find(
                                        'b').text,
                                    row.find('td', class_='light',
                                             width='40%').contents[3],
                                    row.find('td', class_='light',
                                             width='40%').find(
                                        'b').findNextSibling(
                                        'a').text) + '\n'

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

    types_of_week = ['нечет', 'нечетная', 'нечетная неделя', 'нечёт', 'нечётная', 'нечётная неделя' '1', 'чет',
                     'четная', 'четная неделя', 'чёт', 'чётная', 'чётная неделя', '2']

    # Команды
    if re.fullmatch(r'/\w+', message):
        if message == '/start':
            send_message(chat_id, 'Тут должно быть вступление, но его пока нет')
        else:
            send_message(chat_id, 'Такой команды нет')

    # Расписание на текущую неделю
    elif re.fullmatch(r'\w{2,3}\d{2}-\w+', message) or re.fullmatch(r'\w{2,3}\d{2}-\w+-\w+', message) or re.fullmatch(
            r'\w{2,3}\d{2}-\w+/\w+', message):
        group_url = get_group_url(message)
        if group_url == 'Не удалось найти группу':
            send_message(chat_id, group_url)
        elif group_url != 'Не удалось найти группу':
            send_message(chat_id, get_timetable_week(get_html(group_url)))

    # Расписание на определенную неделю и на определенный день недели
    elif re.search(r'\w{2,3}\d{2}-\w+ \w+', message) or re.search(r'\w{2,3}\d{2}-\w+-\w+ \w+', message) or re.search(
            r'\w{2,3}\d{2}-\w+/\w+ \w+', message):
        start = message.index(' ')
        number_of_group = message[:start]
        second_part = message[start + 1:]

        # неправильный запрос
        if get_group_url(number_of_group) == 'Не удалось найти группу':
            send_message(chat_id)
        else:
            # расписание на день
            if second_part in dic_days or second_part in dic_days.values():
                # этот цикцл уюрать в get_timetable_day()
                for key, value in dic_days.items():
                    if second_part == key:
                        second_part = value.title()
                        break
                    elif second_part == value:
                        second_part = value.title()
                        break

                send_message(chat_id, get_timetable_day(get_html(get_group_url(number_of_group)), second_part))
            # расписание на определенную неделю
            elif second_part in types_of_week:
                send_message(chat_id, get_timetable_week(get_html(get_group_url(number_of_group)), second_part))

    # Расписание преподавателя на неделю
    elif re.fullmatch(r'\w+ \w. \w.', message):
        send_message(chat_id, get_timetable_teacher(get_html(get_teacher_url(message))))

    else:
        send_message(chat_id, 'Неправильно составлен запрос')


# ////////////////////////////

def send_message(chat_id, text='Не удалось найти группу'):
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
