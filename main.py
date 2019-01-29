import requests
token = '649594459:AAH1hu90_ZrEhAtZehVDL9xYvkiE2MnLvhU'
URL = 'https://api.telegram.org/bot' + token + '/'
proxies = {'https': 'http://94.254.19.237:58661'}

def get_updates():
    url = URL + 'getupdates'
    print(url)
    r = requests.get(url, proxies=proxies)
    print(r)
    return r.json()

def get_message():
    data = get_updates()

    chat_id = data['result'][-1]['message']['chat']['id']
    message_text = data['result'][-1]['message']['text']

    message = {'chat_id': chat_id,
               'text': message_text}
    return message

def send_message(chat_id, text='wait, please'):
    url = URL + 'sendmessage?chat_id={}&text={}'.format(chat_id, text)
    requests.get(url, proxies=proxies)

def main():
    # get_updates()
    answer = get_message()
    chat_id = answer['chat_id']
    text = answer['text']

    if len(text) != 0:
        send_message(chat_id, 'ты кек')

if __name__ == '__main__':
    main()
print(1)
print(2)
