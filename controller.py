import requests
import re
import psycopg2
import schedule
import threading
import time
from app import DATABASE_URL, ADMIN_CHAT_ID, URL
from view import get_timetable_teacher, get_timetable_week, get_timetable_day, get_timetable_today
from view import get_timetable_tomorrow, get_subscribers_timetable, subscription, update_table_of_urls
from models import get_part_of_url


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
        elif message == '/update_table':
            if chat_id == int(ADMIN_CHAT_ID):
                send_message(chat_id, update_table_of_urls())
            else:
                send_message(chat_id, 'Вы не имеете доступа к данной команде')
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


def get_html(url):
    """
    Получает на вход ссылку на страницу
    Возвращает html-текст этой страницы
    """
    html = requests.get(url)
    return html.text


def get_group_url(number_of_group):
    """
    Получает на вход номер группы
    Возвращает ссылку на расписание группы
    """

    part_of_url = get_part_of_url(number_of_group)

    try:
        group_url = 'http://edu.sfu-kras.ru/timetable' + part_of_url
    except TypeError:
        return 'Не удалось найти группу'

    return group_url


def get_teacher_url(message):
    """
    Получает на вход сообщение пользователя с фамилией и инициалами преподавателя
    Возвращает ссылку на расписание преподавателя
    """
    message = message.replace('.', '')
    message = message.split(' ')
    teacher_url = 'http://edu.sfu-kras.ru/timetable?teacher={0}+{1}.+{2}.'.format(message[0], message[1], message[2])
    return teacher_url


def get_text_of_command(message):
    """
    Получает на вход команду пользователя
    Возвращает ответ в соответствии с командой
    """
    commands = ['/start', '/help', '/registration', '/success_registration']
    answer = ''
    for command in commands:
        if message == command:
            f = open('texts/' + message[1:], encoding='utf-8')
            for line in f:
                answer += line
            f.close()
            break
    return answer


def send_every_day_timetable():
    head_of_message = get_subscribers_timetable()[0]
    subs = get_subscribers_timetable()[1]

    for sub in subs:
        send_message(sub[0], head_of_message + get_timetable_tomorrow(get_html(get_group_url(sub[1]))))


schedule.every().day.at("14:00").do(send_every_day_timetable)


def schedule_run():
    while True:
        schedule.run_pending()
        time.sleep(1)


t = threading.Thread(target=schedule_run, name='тест')
t.start()


def send_message(chat_id, text='Не удалось найти группу'):
    """
    Получает chat_id пользователя и сообщение для отправки
    Возвращает пост запрос
    """
    url = URL + 'sendMessage'
    answer = {'chat_id': chat_id, 'text': text}
    r = requests.post(url, json=answer)
    return r.json()
