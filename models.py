import psycopg2
import transliterate
from app import DATABASE_URL


def get_all_subscribers():
    connect = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = connect.cursor()
    cursor.execute("SELECT chat_id, number_of_group FROM users WHERE subscription=(%(first)s)", {'first': True})

    all_subs = cursor.fetchall()

    connect.commit()
    cursor.close()
    connect.close()

    return all_subs


def get_current_subscription(chat_id):
    connect = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = connect.cursor()
    cursor.execute("SELECT * FROM users WHERE chat_id=(%(first)s)", {'first': chat_id})

    current_subscription = cursor.fetchone()[4]

    connect.commit()
    cursor.close()
    connect.close()

    return current_subscription


def subscription_on(chat_id):
    connect = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = connect.cursor()

    cursor.execute("UPDATE users SET subscription=(%(first)s) WHERE chat_id=(%(second)s)",
                   {'first': True, 'second': chat_id})

    connect.commit()
    cursor.close()
    connect.close()

    return True


def subscription_off(chat_id):
    connect = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = connect.cursor()

    cursor.execute("UPDATE users SET subscription=(%(first)s) WHERE chat_id=(%(second)s)",
                   {'first': False, 'second': chat_id})

    connect.commit()
    cursor.close()
    connect.close()

    return True


def clear_table_of_urls():
    connect = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = connect.cursor()

    cursor.execute("DELETE FROM urls_of_group")

    connect.commit()
    cursor.close()
    connect.close()

    return True


def create_row_table_of_urls(d):
    connect = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = connect.cursor()

    for li in d:
        cursor.execute("INSERT INTO urls_of_group (number_of_group, number_of_group_en, part_of_url) "
                       "VALUES (%(first)s, %(second)s, %(third)s)",
                       {'first': li, 'second': transliterate.translit(li, reversed=True), 'third': d[li]})

    connect.commit()
    cursor.close()
    connect.close()

    return True


def get_part_of_url(number_of_group):
    connect = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = connect.cursor()

    cursor.execute("SELECT part_of_url "
                   "FROM urls_of_group "
                   "WHERE number_of_group LIKE '%{0}%' OR number_of_group_en LIKE '%{0}%'".format(number_of_group))

    part_of_url = cursor.fetchone()[0]

    connect.commit()
    cursor.close()
    connect.close()

    return part_of_url


