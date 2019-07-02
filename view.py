import requests
import re
import psycopg2
import transliterate
from app import DATABASE_URL, URL_TIMETABLE
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

pin = u'\U00002B50'


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
                                week += pin + '{0} {1} {2} |{3}{4}| Каб: {5}'.format(
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
                                week += pin + '{0} {1} {2}{3} /{4}/ Каб: {5}'.format(
                                    row.find('td', width='1%').text,
                                    row.find('td', class_='nobr').text,
                                    row.find('td', class_='light', width='40%').find('b').text,
                                    row.find('td', class_='light', width='40%').contents[1],
                                    row.find('td', class_='light', width='40%').find('em').text,
                                    row.find('td', class_='light', width='40%').find('b').findNextSibling('a').text) + \
                                        '\n'
                            else:
                                week += pin + '{0} {1} {2}'.format(row.find('td', width='1%').text,
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
                                week += pin + '{0} {1} {2}{3} /{4}/ Каб: {5}'.format(
                                    row.find('td', width='1%').text,
                                    row.find('td', class_='nobr').text,
                                    row.find('td', width='40%').find('b').text,
                                    row.find('td', width='40%').contents[1],
                                    row.find('td', width='40%').find('em').text,
                                    row.find('td', width='40%').find('b').findNextSibling('a').text) + '\n'
                            else:
                                week += pin + '{0} {1} {2}'.format(row.find('td', width='1%').text,
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
                                week += pin+ '{0} {1} {2}{3} /{4}/ Каб: {5}'.format(
                                    row.find('td', width='1%').text,
                                    row.find('td', class_='nobr').text,
                                    a.find('b').text,
                                    a.contents[1],
                                    a.find('em').text,
                                    a.find('b').findNextSibling('a').text) + '\n'

                            else:
                                week += pin + '{0} {1} {2}'.format(row.find('td', width='1%').text,
                                                                             row.find('td', class_='nobr').text,
                                                                             a.find('b').text) + '\n'

    if week == '' or week == temp:
        week = group + '\n' + 'Расписания на эту неделю нет'
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
                                            timetable_day += pin + '{0} {1}\n{2} {3}\n{4}\nКаб: {5}'.format(
                                                row.find('td', width='1%').text,
                                                row.find('td', class_='nobr').text,
                                                row.find('td', class_='light', width='40%').find('b').text,
                                                row.find('td', class_='light', width='40%').contents[1],
                                                row.find('td', class_='light', width='40%').find('em').text,
                                                row.find('td', class_='light', width='40%').find('b').
                                                    findNextSibling('a').text) + '\n' + '\n'
                                        else:
                                            timetable_day += pin + '{0} {1}\n{2}'.format(
                                                row.find('td', width='1%').text,
                                                row.find('td', class_='nobr').text,
                                                row.find('td', class_='light', width='40%').find('b').text) + '\n' + '\n'
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
                                            timetable_day += pin + '{0} {1}\n{2} {3}\n{4}\nКаб: {5}'.format(
                                                row.find('td', width='1%').text,
                                                row.find('td', class_='nobr').text,
                                                row.find('td', class_='light', width='40%').find('b').text,
                                                row.find('td', class_='light', width='40%').contents[1],
                                                row.find('td', class_='light', width='40%').find('em').text,
                                                row.find('td', class_='light', width='40%').
                                                    find('b').findNextSibling('a').text) + '\n' + '\n'
                                        else:
                                            timetable_day += pin + '{0} {1}\n{2}'.format(
                                                row.find('td', width='1%').text,
                                                row.find('td', class_='nobr').text,
                                                row.find('td', class_='light', width='40%').find('b').text) + '\n' + '\n'
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
                                                timetable_day += pin + '{0} {1}\n{2} {3}\n{4}\nКаб: {5}'.format(
                                                    row.find('td', width='1%').text,
                                                    row.find('td', class_='nobr').text,
                                                    a.find('b').text,
                                                    a.contents[1],
                                                    a.find('em').text,
                                                    a.find('b').findNextSibling('a').text) + '\n' + '\n'
                                            else:
                                                timetable_day += pin + '{0} {1}\n{2}'.format(
                                                    row.find('td', width='1%').text,
                                                    row.find('td', class_='nobr').text,
                                                    a.find('b').text) + '\n' + '\n'
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
                                                timetable_day += pin + '{0} {1}\n{2} {3}\n{4}\nКаб: {5}'.format(
                                                    row.find('td', width='1%').text,
                                                    row.find('td', class_='nobr').text,
                                                    row.find('td', width='40%').find('b').text,
                                                    row.find('td', width='40%').contents[1],
                                                    row.find('td', width='40%').find('em').text,
                                                    row.find('td', width='40%').find('b').findNextSibling('a').text) + '\n' + '\n'
                                            else:
                                                timetable_day += pin + '{0} {1}\n{2}'.format(
                                                    row.find('td', width='1%').text,
                                                    row.find('td', class_='nobr').text,
                                                    row.find('td', width='40%').find('b').text) + '\n' + '\n'
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
                                                timetable_day += pin + '{0} {1}\n{2} {3}\n{4}\nКаб: {5}'.format(
                                                    row.find('td', width='1%').text,
                                                    row.find('td', class_='nobr').text,
                                                    row.find('td', class_='light', width='40%').find('b').text,
                                                    row.find('td', class_='light', width='40%').contents[1],
                                                    row.find('td', class_='light', width='40%').find('em').text,
                                                    row.find('td', class_='light', width='40%').find('b').
                                                        findNextSibling('a').text) + '\n' + '\n'

                                            else:
                                                timetable_day += pin + '{0} {1}\n{2}'.format(
                                                    row.find('td', width='1%').text,
                                                    row.find('td', class_='nobr').text,
                                                    row.find('td', class_='light', width='40%').find('b').text) + '\n' + '\n'
                            row = row.findNext('tr')
                    except AttributeError:
                        pass

                    break

    if timetable_day == '' + group + '\n' or timetable_day == temp:
        timetable_day += 'Расписания на завтра нет'
    return timetable_day


def get_subscribers_timetable():
    """
    Ежедневная рассылка расписания
    """
    connect = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = connect.cursor()
    cursor.execute("SELECT chat_id, number_of_group FROM users WHERE subscription=(%(first)s)", {'first': True})

    all_subs = cursor.fetchall()

    connect.commit()
    cursor.close()
    connect.close()

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

    return answer, all_subs


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


def update_table_of_urls():
    """
     Формирует таблицу в базе данных для хранения названия групп и ссылок на их расписание
    """
    html = requests.get(URL_TIMETABLE)
    soup = BeautifulSoup(html.text, 'lxml')

    all_li = soup.find('section', class_='tabs-page active timetable-groups').find('ul').find_all('li')
    # словарь: ключ - номер группы, значение - часть url'а
    d = {}
    for li in all_li:
        try:
            if li.find('a').get('href')[0] == '?':
                href = li.find('a').get('href')
                li = li.text

                # Убирает 10ый и часть 9го пункт
                li = re.sub('\(10 чел.\)|\(9 чел.\)|\(8 чел.\)|\(17 чел.\)', '', li)
                li = re.sub('\(а\)  \(подгруппа 1\)', '1', li)
                li = re.sub('\(а\)  \(подгруппа 2\)', '2', li)
                # Убирает 8ой и часть 9го пункт
                li = re.sub('\(а\)', '1', li)
                li = re.sub('\(б\)', '2', li)
                # Условие убирает 11ый пункт
                if li[0] == '3':
                    li = li[li.find('('):]
                # Убирает 7ой пункт
                li = re.sub('\(1 подгруппа\) \(подгруппа 1\)', '1', li)
                li = re.sub('\(1 подгруппа\) \(подгруппа 2\)', '2', li)
                # Убираает 2ой, 3ий, 12ый пункт
                li = re.sub('\ |\ |подгруппа|\(|\)|п/г', '', li)

                d[li.lower()] = href
        except:
            pass

    connect = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = connect.cursor()

    cursor.execute("DELETE FROM urls_of_group")

    connect.commit()

    for li in d:
        cursor.execute("INSERT INTO urls_of_group (number_of_group, number_of_group_en, part_of_url) "
                       "VALUES (%(first)s, %(second)s, %(third)s)",
                       {'first': li, 'second': transliterate.translit(li, reversed=True), 'third': d[li]})

    connect.commit()
    cursor.close()
    connect.close()

    return 'Ссылки на группы успешно обновлены'
