import requests
import os
import re
import psycopg2
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_sslify import SSLify
from bs4 import BeautifulSoup

TOKEN = os.getenv('TOKEN')
DATABASE_URL = os.environ['DATABASE_URL']
URL = 'https://api.telegram.org/bot' + TOKEN + '/'
proxies = {'https': 'http://212.184.186.146:8080'}

app = Flask(__name__)
sslify = SSLify(app)

START = """
Этот бот поможет вам узнать расписание групп и преподавателей Сибирского Федерального университета

Используйте команду /registration, чтобы затем использовать другие команды

Если ваша группа разделена на подгруппы, например "ВЦ18-01АСУ (1 подгруппа) и ВЦ18-01АСУ (2 подгруппа)",
то достаточно будет написать "вц18-01асу1" или "вц18-01асу2"

Чтобы узнать расписание преподавателя надо написать фамилию и инициалы через пробел
например: "Кукарцев в в"

Также можно просто использовать номер группы, чтобы получить расписание
например: "ки15-17б" - распсиание на текущую неделю

Чтобы получить расписание на сегодня
например: "сб18-11б сегодня"

Чтобы получить расписание на завтра
например: "ки15-16б завтра"

Также можно узнать расписание на нечетную(1) и четную неделю(2)
например: "ки17-03б 1" - расписание на нечетную неделю
"ки17-03б 2" - расписание на четную неделю

Также можно узнать расписание на определенный день через сокращенные названия дней (пн, вт, ср, чт, пт, сб)
например: "ки15-17б вт" - расписание на вторник
"сб15-12б пт" - расписание на пятницу
"""

HELP = """
Используйте команду /registration, чтобы затем использовать другие команды

Если ваша группа разделена на подгруппы, например "ВЦ18-01АСУ (1 подгруппа) и ВЦ18-01АСУ (2 подгруппа)",
то достаточно будет написать "вц18-01асу1" или "вц18-01асу2"

Чтобы узнать расписание преподавателя надо написать фамилию и инициалы через пробел
например: "Кукарцев в в"

Также можно просто использовать номер группы, чтобы получить расписание
например: "ки15-17б" - распсиание на текущую неделю

Чтобы получить расписание на сегодня
например: "сб18-11б сегодня"

Чтобы получить расписание на завтра
например: "ки15-16б завтра"

Также можно узнать расписание на нечетную(1) и четную неделю(2)
например: "ки17-03б 1" - расписание на нечетную неделю
"ки17-03б 2" - расписание на четную неделю

Также можно узнать расписание на определенный день через сокращенные названия дней (пн, вт, ср, чт, пт, сб)
например: "ки15-17б вт" - расписание на вторник
"сб15-12б пт" - расписание на пятницу

Команды:
/help - информация по командам
/registration - зарегистрировать группу для использования сокращенных команд
/today - расписание на сегодня
/tomorrow - расписание на завтра
/week - расписание на текущую неделю
/week_odd - нечётная неделя
/week_even - чётная неделя
"""

REGISTRATION = """
Введите номер группы

Если ваша группа разделена на подгруппы, например "ВЦ18-01АСУ (1 подгруппа) и ВЦ18-01АСУ (2 подгруппа)",
то достаточно будет написать "вц18-01асу1" или "вц18-01асу2"
"""

SUCCESS_REGISTRATION = """
Расписание успешно установлено

Теперь вам доступны команды
Команды:
/today
/tomorrow
/week
/week_odd
/week_even  
"""

# ////////////////////////

def get_html(url):
    html = requests.get(url)
    return html.text


def get_teacher_url(message):
    message = message.replace('.', '')
    message = message.split(' ')
    teacher_url = 'http://edu.sfu-kras.ru/timetable?teacher={0}+{1}.+{2}.'.format(message[0], message[1], message[2])
    return teacher_url


def get_group_url(number_of_group):
    f = open('text', encoding='utf-8')
    group_url = 'Не удалось найти группу'
    for line in f:
        if number_of_group.lower() in line:
            group_url = 'http://edu.sfu-kras.ru/timetable' + line[line.find('?'):-1]
            break
    f.close()
    return group_url


def get_timetable_week(html, type='текущая неделя'):
    odd = ['нечет', 'нечетная', 'нечетная неделя', 'нечёт', 'нечётная', 'нечётная неделя', 'н', '1']
    even = ['чет', 'четная', 'четная неделя', 'чёт', 'чётная', 'чётная неделя', 'ч', '2']
    soup = BeautifulSoup(html, 'lxml')
    type_of_week = soup.find('div', class_='content').find('p').find('b').text[5:]
    table = soup.find('table', class_='table timetable')
    h3 = soup.find('h3').text
    start = h3.index(':')
    group = h3[start + 2:]
    week = '' + group

    if type == 'текущая неделя':
        # текущая неделя
        for row in table:
            if hasattr(row.find('th', colspan=4), 'text'):
                week += '\n'
                week += '{0}/{1}/{2}'.format(row.find('th', colspan=4).text.upper(), type_of_week, type) + '\n'
                temp = week
            if hasattr(row.find('td', width='1%'), 'text'):
                if hasattr(row.find('td', class_='nobr'), 'text'):
                    if hasattr(row.find('td', class_='light', width='40%').find('b'), 'text'):
                        if hasattr(row.find('td', class_='light', width='40%'), 'contents'):
                            if hasattr(row.find('td', class_='light', width='40%').find('em'), 'text'):
                                week += u'\U00002B55' + '{0} {1} {2}{3} /{4}/ Каб: {5}'.format(
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
                                week += u'\U00002B55' + '{0} {1} {2}'.format(row.find('td', width='1%').text,
                                                                             row.find('td', class_='nobr').text,
                                                                             row.find('td', class_='light',
                                                                                      width='40%').find(
                                                                                 'b').text) + '\n'

    elif type in odd:
        # нечетная неделя
        for row in table:
            if hasattr(row.find('th', colspan=4), 'text'):
                week += '\n'
                week += '{0}/{1}'.format(row.find('th', colspan=4).text.upper(), 'нечетная неделя') + '\n'
                temp = week
            if hasattr(row.find('td', width='1%'), 'text'):
                if hasattr(row.find('td', class_='nobr'), 'text'):
                    if hasattr(row.find('td', width='40%').find('b'), 'text'):
                        if hasattr(row.find('td', width='40%'), 'contents'):
                            if hasattr(row.find('td', width='40%').find('em'), 'text'):
                                week += u'\U00002B55' + '{0} {1} {2}{3} /{4}/ Каб: {5}'.format(
                                    row.find('td', width='1%').text,
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
                                week += u'\U00002B55' + '{0} {1} {2}'.format(row.find('td', width='1%').text,
                                                                             row.find('td', class_='nobr').text,
                                                                             row.find('td', width='40%').find(
                                                                                 'b').text) + '\n'
    elif type in even:
        # четная неделя
        for row in table:
            if hasattr(row.find('th', colspan=4), 'text'):
                week += '\n'
                week += '{0}/{1}'.format(row.find('th', colspan=4).text.upper(), 'четная неделя') + '\n'
                temp = week
            if hasattr(row.find('td', width='1%'), 'text'):
                if hasattr(row.find('td', class_='nobr'), 'text'):
                    if hasattr(row.find('td', width='40%'), 'text'):
                        a = row.find('td', width='40%').nextSibling

                        if a is None:
                            a = row.find('td', width='40%')

                        elif a.find('b') is None:
                            continue

                        if hasattr(row.find('td', width='40%'), 'contents'):
                            if hasattr(row.find('em'), 'text'):
                                week += u'\U00002B55' + '{0} {1} {2}{3} /{4}/ Каб: {5}'.format(
                                    row.find('td', width='1%').text,
                                    row.find('td', class_='nobr').text,
                                    a.find('b').text,
                                    a.contents[1],
                                    a.find('em').text,
                                    a.find('b').findNextSibling(
                                        'a').text) + '\n'

                            else:
                                week += u'\U00002B55' + '{0} {1} {2}'.format(row.find('td', width='1%').text,
                                                                             row.find('td', class_='nobr').text,
                                                                             a.find('b').text) + '\n'

    if week == '' or week == temp:
        week = group + '\n' + 'Расписания на эту неделю нет'
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
                                week += u'\U00002B55' + '{0} {1} {2} |{3}{4}| Каб: {5}'.format(
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

    if week == teacher_name + '\n':
        week = 'Расписание на преподавателя нет'

    return week


def get_timetable_day(html, day):
    soup = BeautifulSoup(html, 'lxml')
    type_of_week = soup.find('div', class_='content').find('p').find('b').text[5:]
    table = soup.find('table', class_='table timetable')

    h3 = soup.find('h3').text
    start = h3.index(':')
    group = h3[start + 2:]
    timetable_day = '' + group + '\n'

    for row in table:
        if hasattr(row.find('th', colspan=4), 'text'):
            if row.find('th', colspan=4).text == day:
                timetable_day += '{0}/{1}'.format(row.find('th', colspan=4).text.upper(), type_of_week) + '\n'
                temp = timetable_day
                row = row.findNext('tr')
                row = row.findNext('tr')

                try:
                    while row.find('td'):
                        if hasattr(row.find('td', width='1%'), 'text'):
                            if hasattr(row.find('td', class_='nobr'), 'text'):
                                if hasattr(row.find('td', class_='light', width='40%').find('b'), 'text'):
                                    if hasattr(row.find('td', class_='light', width='40%'), 'contents'):
                                        if hasattr(row.find('td', class_='light', width='40%').find('em'), 'text'):
                                            timetable_day += u'\U00002B55' + '{0} {1} {2}{3} /{4}/ Каб: {5}'.format(
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
                                            timetable_day += u'\U00002B55' + '{0} {1} {2}'.format(
                                                row.find('td', width='1%').text,
                                                row.find('td', class_='nobr').text,
                                                row.find('td', class_='light',
                                                         width='40%').find(
                                                    'b').text) + '\n'
                        row = row.findNext('tr')
                except AttributeError:
                    pass

                break

    if timetable_day == '' + group + '\n' or timetable_day == temp:
        timetable_day = group + '\n' + 'Расписания на этот день нет'
    return timetable_day


def get_timetable_today(html):
    now = datetime.now()
    day = now.strftime('%A')
    days_of_the_week = {'Monday': 'Понедельник', 'Tuesday': 'Вторник', 'Wednesday': 'Среда', 'Thursday': 'Четверг',
                        'Friday': 'Пятница', 'Saturday': 'Суббота', 'Sunday': 'Воскресенье'}

    for key, value in days_of_the_week.items():
        if day == key:
            day = value
            break

    soup = BeautifulSoup(html, 'lxml')
    type_of_week = soup.find('div', class_='content').find('p').find('b').text[5:]

    h3 = soup.find('h3').text
    start = h3.index(':')
    group = h3[start + 2:]

    table = soup.find('table', class_='table timetable')
    timetable_day = '' + group + '\n'

    for row in table:
        if hasattr(row.find('th', colspan=4), 'text'):
            if row.find('th', colspan=4).text == day:
                timetable_day += '{0}/{1}'.format(row.find('th', colspan=4).text.upper(), type_of_week) + '\n'
                temp = timetable_day
                row = row.findNext('tr')
                row = row.findNext('tr')

                try:
                    while row.find('td'):
                        if hasattr(row.find('td', width='1%'), 'text'):
                            if hasattr(row.find('td', class_='nobr'), 'text'):
                                if hasattr(row.find('td', class_='light', width='40%').find('b'), 'text'):
                                    if hasattr(row.find('td', class_='light', width='40%'), 'contents'):
                                        if hasattr(row.find('td', class_='light', width='40%').find('em'), 'text'):
                                            timetable_day += u'\U00002B55' + '{0} {1} {2}{3} /{4}/ Каб: {5}'.format(
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
                                            timetable_day += u'\U00002B55' + '{0} {1} {2}'.format(
                                                row.find('td', width='1%').text,
                                                row.find('td', class_='nobr').text,
                                                row.find('td', class_='light',
                                                         width='40%').find(
                                                    'b').text) + '\n'
                        row = row.findNext('tr')
                except AttributeError:
                    pass

                break

    if timetable_day == '' + group + '\n' or timetable_day == temp:
        timetable_day += 'Расписания на сегодня нет'
    return timetable_day


def get_timetable_tomorrow(html):
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    day = tomorrow.strftime('%A')
    days_of_the_week = {'Monday': 'Понедельник', 'Tuesday': 'Вторник', 'Wednesday': 'Среда', 'Thursday': 'Четверг',
                        'Friday': 'Пятница', 'Saturday': 'Суббота', 'Sunday': 'Воскресенье'}

    for key, value in days_of_the_week.items():
        if day == key:
            day = value
            break

    soup = BeautifulSoup(html, 'lxml')
    current_type_of_week = soup.find('div', class_='content').find('p').find('b').text[5:]

    h3 = soup.find('h3').text
    start = h3.index(':')
    group = h3[start + 2:]

    table = soup.find('table', class_='table timetable')
    timetable_day = '' + group + '\n'

    if day == 'Понедельник' and current_type_of_week == 'нечётная неделя':
        for row in table:
            if hasattr(row.find('th', colspan=4), 'text'):
                if row.find('th', colspan=4).text == day:
                    timetable_day += '{0}/{1}'.format(row.find('th', colspan=4).text.upper(), 'чётная неделя') + '\n'
                    temp = timetable_day
                    row = row.findNext('tr')
                    row = row.findNext('tr')

                    try:
                        while row.find('td'):
                            if hasattr(row.find('td', width='1%'), 'text'):
                                if hasattr(row.find('td', class_='nobr'), 'text'):
                                    if hasattr(row.find('td', width='40%'), 'text'):

                                        a = row.find('td', width='40%').nextSibling

                                        if a is None:
                                            a = row.find('td', width='40%')

                                        elif a.find('b') is None:
                                            break

                                        if hasattr(row.find('td', width='40%'), 'contents'):
                                            if hasattr(row.find('em'), 'text'):
                                                timetable_day += u'\U00002B55' + '{0} {1} {2}{3} /{4}/ Каб: {5}'.format(
                                                    row.find('td', width='1%').text,
                                                    row.find('td', class_='nobr').text,
                                                    a.find('b').text,
                                                    a.contents[1],
                                                    a.find('em').text,
                                                    a.find('b').findNextSibling(
                                                        'a').text) + '\n'
                                            else:
                                                timetable_day += u'\U00002B55' + '{0} {1} {2}'.format(
                                                    row.find('td', width='1%').text,
                                                    row.find('td', class_='nobr').text,
                                                    a.find('b').text) + '\n'
                            row = row.findNext('tr')
                    except AttributeError:
                        pass

                    break

    elif day == 'Понедельник' and current_type_of_week == 'чётная неделя':
        for row in table:
            if hasattr(row.find('th', colspan=4), 'text'):
                if row.find('th', colspan=4).text == day:
                    timetable_day += '{0}/{1}'.format(row.find('th', colspan=4).text.upper(), 'нечётная неделя') + '\n'
                    temp = timetable_day
                    row = row.findNext('tr')
                    row = row.findNext('tr')

                    try:
                        while row.find('td'):
                            if hasattr(row.find('td', width='1%'), 'text'):
                                if hasattr(row.find('td', class_='nobr'), 'text'):
                                    if hasattr(row.find('td', width='40%').find('b'), 'text'):
                                        if hasattr(row.find('td', width='40%'), 'contents'):
                                            if hasattr(row.find('td', width='40%').find('em'), 'text'):
                                                timetable_day += u'\U00002B55' + '{0} {1} {2}{3} /{4}/ Каб: {5}'.format(
                                                    row.find('td', width='1%').text,
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
                                                timetable_day += u'\U00002B55' + '{0} {1} {2}'.format(
                                                    row.find('td', width='1%').text,
                                                    row.find('td', class_='nobr').text,
                                                    row.find('td', width='40%').find(
                                                        'b').text) + '\n'
                            row = row.findNext('tr')
                    except AttributeError:
                        pass

                    break

    else:
        for row in table:
            if hasattr(row.find('th', colspan=4), 'text'):
                if row.find('th', colspan=4).text == day:
                    timetable_day += '{0}/{1}'.format(row.find('th', colspan=4).text.upper(),
                                                      current_type_of_week) + '\n'
                    temp = timetable_day
                    row = row.findNext('tr')
                    row = row.findNext('tr')

                    try:
                        while row.find('td'):
                            if hasattr(row.find('td', width='1%'), 'text'):
                                if hasattr(row.find('td', class_='nobr'), 'text'):
                                    if hasattr(row.find('td', class_='light', width='40%').find('b'), 'text'):
                                        if hasattr(row.find('td', class_='light', width='40%'), 'contents'):
                                            if hasattr(row.find('td', class_='light', width='40%').find('em'), 'text'):
                                                timetable_day += u'\U00002B55' + '{0} {1} {2}{3} /{4}/ Каб: {5}'.format(
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
                                                timetable_day += u'\U00002B55' + '{0} {1} {2}'.format(
                                                    row.find('td', width='1%').text,
                                                    row.find('td', class_='nobr').text,
                                                    row.find('td', class_='light',
                                                             width='40%').find(
                                                        'b').text) + '\n'
                            row = row.findNext('tr')
                    except AttributeError:
                        pass

                    break

    if timetable_day == '' + group + '\n' or timetable_day == temp:
        timetable_day += 'Расписания на завтра нет'
    return timetable_day


def user_massages_handler(chat_id, message):
    message = message.lower().lstrip().rstrip()

    dic_days = {'пн': 'понедельник',
                'вт': 'вторник',
                'ср': 'среда',
                'чт': 'четверг',
                'пт': 'пятница',
                'сб': 'суббота'}

    types_of_week = ['нечет', 'нечетная', 'нечетная неделя', 'нечёт', 'нечётная', 'нечётная неделя', 'н', '1', 'чет',
                     'четная', 'четная неделя', 'чёт', 'чётная', 'чётная неделя', 'ч', '2']

    # connect = psycopg2.connect(DATABASE_URL, sslmode='require')
    connect = psycopg2.connect(dbname='test', user='postgres', host='localhost')
    cursor = connect.cursor()

    # Команды
    if re.fullmatch(r'/\w+', message):

        cursor.execute("SELECT * FROM users WHERE chat_id=(%(first)s)", {'first': chat_id})
        number_of_group = ''

        try:
            number_of_group = cursor.fetchone()[3]
        except:
            pass

        if message == '/start':
            send_message(chat_id, START)
        elif message == '/help':
            send_message(chat_id, HELP)
        elif message == '/registration':
            cursor.execute("SELECT * FROM users WHERE chat_id=(%(first)s)", {'first': chat_id})

            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO users (chat_id, last_message) VALUES (%(first)s, %(second)s)",
                               {'first': chat_id, 'second': message})

            send_message(chat_id, REGISTRATION)
        elif number_of_group == '':
            send_message(chat_id, 'Воспользуйтесь регистарицей, чтобы использовать короткие команды')
        elif message == '/week':
            send_message(chat_id, get_timetable_week(get_html(get_group_url(number_of_group))))
        elif message == '/today':
            send_message(chat_id, get_timetable_today(get_html(get_group_url(number_of_group))))
        elif message == '/tomorrow':
            send_message(chat_id, get_timetable_tomorrow(get_html(get_group_url(number_of_group))))
        elif message == '/week_odd':
            send_message(chat_id, get_timetable_week(get_html(get_group_url(number_of_group)), 'нечет'))
        elif message == '/week_even':
            send_message(chat_id, get_timetable_week(get_html(get_group_url(number_of_group)), 'чет'))
        else:
            send_message(chat_id, 'Такой команды нет')

    # Расписание на сегодня
    elif re.fullmatch(r'\w{2,3}\d{2}-\w+ сегодня', message) or re.fullmatch(r'\w{2,3}\d{2}-\w+-\w+ сегодня', message) or re.fullmatch(
            r'\w{2,3}\d{2}-\w+/\w+ сегодня', message):
        start = message.index(' ')
        number_of_group = message[:start]
        send_message(chat_id, get_timetable_today(get_html(get_group_url(number_of_group))))

    # Расписание на завтра
    elif re.fullmatch(r'\w{2,3}\d{2}-\w+ завтра', message) or re.fullmatch(r'\w{2,3}\d{2}-\w+-\w+ завтра', message) or re.fullmatch(
            r'\w{2,3}\d{2}-\w+/\w+ завтра', message):
        start = message.index(' ')
        number_of_group = message[:start]
        send_message(chat_id, get_timetable_tomorrow(get_html(get_group_url(number_of_group))))

    # Расписание на текущую неделю
    elif re.fullmatch(r'\w{2,3}\d{2}-\w+', message) or re.fullmatch(r'\w{2,3}\d{2}-\w+-\w+', message) or re.fullmatch(
            r'\w{2,3}\d{2}-\w+/\w+', message):
        group_url = get_group_url(message)
        if group_url == 'Не удалось найти группу':
            send_message(chat_id, group_url)
        elif group_url != 'Не удалось найти группу':
            cursor.execute("SELECT * FROM users WHERE chat_id=(%(first)s)", {'first': chat_id})
            last_message = ''

            try:
                last_message = cursor.fetchone()[2]
            except:
                pass

            if last_message == '/registration':
                cursor.execute("UPDATE users SET number_of_group=(%(first)s) WHERE chat_id=(%(second)s)",
                               {'first': message, 'second': chat_id})
                send_message(chat_id, SUCCESS_REGISTRATION)
            else:
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
                for key, value in dic_days.items():
                    if second_part == key or second_part == value:
                        second_part = value.title()
                        break
                send_message(chat_id, get_timetable_day(get_html(get_group_url(number_of_group)), second_part))
            # расписание на определенную неделю
            elif second_part in types_of_week:
                send_message(chat_id, get_timetable_week(get_html(get_group_url(number_of_group)), second_part))
            else:
                send_message(chat_id, 'Неправильно составлен запрос')

    # Расписание преподавателя на неделю
    elif re.fullmatch(r'\w+ \w. \w.', message) or re.fullmatch(r'\w+ \w \w', message) \
            or re.fullmatch(r'\w+ \w. \w', message):
        send_message(chat_id, get_timetable_teacher(get_html(get_teacher_url(message))))

    else:
        send_message(chat_id, 'Неправильно составлен запрос')

    cursor.execute("UPDATE users SET last_message=(%(first)s) WHERE chat_id=(%(second)s)",
                   {'first': message, 'second': chat_id})

    connect.commit()
    cursor.close()
    connect.close()

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
