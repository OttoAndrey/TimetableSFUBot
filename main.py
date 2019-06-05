import requests
import os
import re
import psycopg2
import schedule
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_sslify import SSLify
from bs4 import BeautifulSoup

DATABASE_URL = os.environ['DATABASE_URL']
TOKEN = os.getenv('TOKEN')
URL = 'https://api.telegram.org/bot' + TOKEN + '/'

app = Flask(__name__)
sslify = SSLify(app)


# ////////////////////////


def get_html(url):
    """
    Получает на вход ссылку на страницу
    Возвращает html-текст этой страницы
    """
    html = requests.get(url)
    return html.text


def get_teacher_url(message):
    """
    Получает на вход сообщение пользователя с фамилией преподавателя
    Возвращает ссылку на расписание преподавателя
    """
    message = message.replace('.', '')
    message = message.split(' ')
    teacher_url = 'http://edu.sfu-kras.ru/timetable?teacher={0}+{1}.+{2}.'.format(message[0], message[1], message[2])
    return teacher_url


def get_group_url(number_of_group):
    """
    Получает на вход номер группы
    Возвращает ссылку на расписание группы
    """
    f = open('urls_of_group', encoding='utf-8')
    group_url = 'Не удалось найти группу'
    for line in f:
        if number_of_group.lower() in line:
            group_url = 'http://edu.sfu-kras.ru/timetable' + line[line.find('?'):-1]
            break
    f.close()
    return group_url


def get_timetable_week(html, type='текущая неделя'):
    """
    Получает на вход html-текст страницы группы и тип недели, который нужно сформировать
    Возвращает расписание на неделю
    """
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
                                    row.find('td', class_='light', width='40%').find('b').text,
                                    row.find('td', class_='light', width='40%').contents[1],
                                    row.find('td', class_='light', width='40%').find('em').text,
                                    row.find('td', class_='light', width='40%').find('b').findNextSibling('a').text) + \
                                        '\n '
                            else:
                                week += u'\U00002B55' + '{0} {1} {2}'.format(row.find('td', width='1%').text,
                                                                             row.find('td', class_='nobr').text,
                                                                             row.find('td', class_='light', width='40%')
                                                                             .find('b').text) + '\n'
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
                                    row.find('td', width='40%').find('b').text,
                                    row.find('td', width='40%').contents[1],
                                    row.find('td', width='40%').find('em').text,
                                    row.find('td', width='40%').find('b').findNextSibling('a').text) + '\n'
                            else:
                                week += u'\U00002B55' + '{0} {1} {2}'.format(row.find('td', width='1%').text,
                                                                             row.find('td', class_='nobr').text,
                                                                             row.find('td', width='40%').
                                                                             find('b').text) + '\n'
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
                                    a.find('b').findNextSibling('a').text) + '\n'

                            else:
                                week += u'\U00002B55' + '{0} {1} {2}'.format(row.find('td', width='1%').text,
                                                                             row.find('td', class_='nobr').text,
                                                                             a.find('b').text) + '\n'

    if week == '' or week == temp:
        week = group + '\n' + 'Расписания на эту неделю нет'
    return week


def get_timetable_teacher(html, type='текущая неделя'):
    """
    Получает на вход html-текст страницы преподавателя и тип недели, который нужно сформировать
    Возвращает расписание преподавателя на неделю
    """
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
                                    row.find('td', class_='light', width='40%').find('a').text,
                                    row.find('td', class_='light', width='40%').find('b').text,
                                    row.find('td', class_='light', width='40%').contents[3],
                                    row.find('td', class_='light', width='40%').find('b').findNextSibling('a').text) + \
                                        '\n'

    if week == teacher_name + '\n':
        week = 'Расписание на преподавателя нет'

    return week


def get_timetable_day(html, day):
    """
    Получает на вход html-текст страницы группы и день, который нужно сформировать
    Возвращает расписание на определенный день
    """
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
                                                row.find('td', class_='light', width='40%').find('b').text,
                                                row.find('td', class_='light', width='40%').contents[1],
                                                row.find('td', class_='light', width='40%').find('em').text,
                                                row.find('td', class_='light', width='40%').find('b').
                                                    findNextSibling('a').text) + '\n'
                                        else:
                                            timetable_day += u'\U00002B55' + '{0} {1} {2}'.format(
                                                row.find('td', width='1%').text,
                                                row.find('td', class_='nobr').text,
                                                row.find('td', class_='light', width='40%').find('b').text) + '\n'
                        row = row.findNext('tr')
                except AttributeError:
                    pass

                break

    if timetable_day == '' + group + '\n' or timetable_day == temp:
        timetable_day = group + '\n' + 'Расписания на этот день нет'
    return timetable_day


def get_timetable_today(html):
    """
    Получает на вход html-текст страницы группы
    Возвращает расписание на текущий день
    """
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
                                                row.find('td', class_='light', width='40%').find('b').text,
                                                row.find('td', class_='light', width='40%').contents[1],
                                                row.find('td', class_='light', width='40%').find('em').text,
                                                row.find('td', class_='light', width='40%').
                                                    find('b').findNextSibling('a').text) + '\n'
                                        else:
                                            timetable_day += u'\U00002B55' + '{0} {1} {2}'.format(
                                                row.find('td', width='1%').text,
                                                row.find('td', class_='nobr').text,
                                                row.find('td', class_='light', width='40%').find('b').text) + '\n'
                        row = row.findNext('tr')
                except AttributeError:
                    pass

                break

    if timetable_day == '' + group + '\n' or timetable_day == temp:
        timetable_day += 'Расписания на сегодня нет'
    return timetable_day


def get_timetable_tomorrow(html):
    """
    Получает на вход html-текст страницы группы
    Возвращает расписание на завтрашний день
    """
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
                                                    a.find('b').findNextSibling('a').text) + '\n'
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
                                                    row.find('td', width='40%').find('b').text,
                                                    row.find('td', width='40%').contents[1],
                                                    row.find('td', width='40%').find('em').text,
                                                    row.find('td', width='40%').find('b').findNextSibling('a').text) + \
                                                                 '\n'
                                            else:
                                                timetable_day += u'\U00002B55' + '{0} {1} {2}'.format(
                                                    row.find('td', width='1%').text,
                                                    row.find('td', class_='nobr').text,
                                                    row.find('td', width='40%').find('b').text) + '\n'
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
                                                    row.find('td', class_='light', width='40%').find('b').text,
                                                    row.find('td', class_='light', width='40%').contents[1],
                                                    row.find('td', class_='light', width='40%').find('em').text,
                                                    row.find('td', class_='light', width='40%').find('b').
                                                        findNextSibling('a').text) + '\n'

                                            else:
                                                timetable_day += u'\U00002B55' + '{0} {1} {2}'.format(
                                                    row.find('td', width='1%').text,
                                                    row.find('td', class_='nobr').text,
                                                    row.find('td', class_='light', width='40%').find('b').text) + '\n'
                            row = row.findNext('tr')
                    except AttributeError:
                        pass

                    break

    if timetable_day == '' + group + '\n' or timetable_day == temp:
        timetable_day += 'Расписания на завтра нет'
    return timetable_day


def subscription(chat_id):
    """
    Получает на вход chat_id пользователя
    Меняет поле subscription в базе данных
    Возвращает ответ о состоянии подписки пользователя
    """
    answer = ''
    connect = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = connect.cursor()
    cursor.execute("SELECT * FROM users WHERE chat_id=(%(first)s)", {'first': chat_id})
    current_subscription = cursor.fetchone()[4]

    if not current_subscription:
        cursor.execute("UPDATE users SET subscription=(%(first)s) WHERE chat_id=(%(second)s)",
                       {'first': True, 'second': chat_id})
        answer = 'Подписка подключена. Теперь вы будете получать уведомление о завтрашнем расписании'
    elif current_subscription:
        cursor.execute("UPDATE users SET subscription=(%(first)s) WHERE chat_id=(%(second)s)",
                       {'first': False, 'second': chat_id})
        answer = 'Подписка отключена'

    connect.commit()
    cursor.close()
    connect.close()

    return answer


def get_text_of_command(message):
    """
    Получает на вход команду пользователя
    Возвращает ответ в соответствии с командой
    """
    commands = ['/start', '/help', '/registration', '/success_subscription']
    answer = ''
    for command in commands:
        if message == command:
            f = open('texts/' + message[1:], encoding='utf-8')
            for line in f:
                answer += line
            f.close()
            break
    return answer


def user_massages_handler(chat_id, message):
    """
    Получает на вход chat_id и сообщение пользователя
    В соответствии с сообщением формирует ответ
    """
    message = message.lower().lstrip().rstrip()

    dic_days = {'пн': 'понедельник',
                'вт': 'вторник',
                'ср': 'среда',
                'чт': 'четверг',
                'пт': 'пятница',
                'сб': 'суббота'}

    types_of_week = ['нечет', 'нечетная', 'нечетная неделя', 'нечёт', 'нечётная', 'нечётная неделя', 'н', '1', 'чет',
                     'четная', 'четная неделя', 'чёт', 'чётная', 'чётная неделя', 'ч', '2']

    connect = psycopg2.connect(DATABASE_URL, sslmode='require')
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
            send_message(chat_id, get_text_of_command(message))
        elif message == '/help':
            send_message(chat_id, get_text_of_command(message))
        elif message == '/registration':
            cursor.execute("SELECT * FROM users WHERE chat_id=(%(first)s)", {'first': chat_id})

            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO users (chat_id, last_message) VALUES (%(first)s, %(second)s)",
                               {'first': chat_id, 'second': message})

            send_message(chat_id, get_text_of_command(message))
        elif number_of_group == '':
            send_message(chat_id, 'Воспользуйтесь регистарицей, чтобы использовать короткие команды')
        elif get_group_url(number_of_group) == 'Не удалось найти группу':
            send_message(chat_id, 'Не удалось найти группу. Возможно её не существует')
        elif message == '/subscription':
            send_message(chat_id, subscription(chat_id))
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
    elif re.fullmatch(r'\w{2,3}\d{2}-\w+ сегодня', message)\
            or re.fullmatch(r'\w{2,3}\d{2}-\w+-\w+ сегодня', message)\
            or re.fullmatch(r'\w{2,3}\d{2}-\w+/\w+ сегодня', message):
        start = message.index(' ')
        number_of_group = message[:start]
        send_message(chat_id, get_timetable_today(get_html(get_group_url(number_of_group))))

    # Расписание на завтра
    elif re.fullmatch(r'\w{2,3}\d{2}-\w+ завтра', message)\
            or re.fullmatch(r'\w{2,3}\d{2}-\w+-\w+ завтра', message)\
            or re.fullmatch(r'\w{2,3}\d{2}-\w+/\w+ завтра', message):
        start = message.index(' ')
        number_of_group = message[:start]
        send_message(chat_id, get_timetable_tomorrow(get_html(get_group_url(number_of_group))))

    # Расписание на текущую неделю
    elif re.fullmatch(r'\w{2,3}\d{2}-\w+', message)\
            or re.fullmatch(r'\w{2,3}\d{2}-\w+-\w+', message)\
            or re.fullmatch(r'\w{2,3}\d{2}-\w+/\w+', message):
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
                send_message(chat_id, get_text_of_command('/success_registration'))
            else:
                send_message(chat_id, get_timetable_week(get_html(group_url)))

    # Расписание на определенную неделю и на определенный день недели
    elif re.search(r'\w{2,3}\d{2}-\w+ \w+', message)\
            or re.search(r'\w{2,3}\d{2}-\w+-\w+ \w+', message)\
            or re.search(r'\w{2,3}\d{2}-\w+/\w+ \w+', message):
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
    elif re.fullmatch(r'\w+ \w. \w.', message)\
            or re.fullmatch(r'\w+ \w \w', message) \
            or re.fullmatch(r'\w+ \w. \w', message):
        send_message(chat_id, get_timetable_teacher(get_html(get_teacher_url(message))))

    else:
        send_message(chat_id, 'Неправильно составлен запрос')

    cursor.execute("UPDATE users SET last_message=(%(first)s) WHERE chat_id=(%(second)s)",
                   {'first': message, 'second': chat_id})

    connect.commit()
    cursor.close()
    connect.close()


def every_day_timetable():
    """
    Ежедневная рассылка расписания
    """
    connect = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = connect.cursor()
    cursor.execute("SELECT chat_id, number_of_group FROM users WHERE subscription=(%(first)s)", {'first': True})

    all_subs = cursor.fetchall()

    tomorrow = datetime.now() + timedelta(days=1)
    date = tomorrow.strftime('%d.%m.%Y')
    day = tomorrow.strftime('%A')
    days_of_the_week = {'Monday': 'Понедельник', 'Tuesday': 'Вторник', 'Wednesday': 'Среда', 'Thursday': 'Четверг',
                        'Friday': 'Пятница', 'Saturday': 'Суббота', 'Sunday': 'Воскресенье'}

    for key, value in days_of_the_week.items():
        if day == key:
            day = value
            break

    answer = 'Ваше расписание на завтра ({0} {1})'.format(date, day) + '\n'

    for sub in all_subs:
        send_message(sub[0], answer + get_timetable_tomorrow(get_html(get_group_url(sub[1]))))

    connect.commit()
    cursor.close()
    connect.close()


schedule.every().day.at("14:00").do(every_day_timetable)


def schedule_run():
    while True:
        schedule.run_pending()
        time.sleep(1)


t = threading.Thread(target=schedule_run, name='тест')
t.start()


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
