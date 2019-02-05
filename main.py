import requests
import json
from flask import Flask
from flask import request
from flask import jsonify
from flask_sslify import SSLify

token = '649594459:AAH1hu90_ZrEhAtZehVDL9xYvkiE2MnLvhU'
URL = 'https://api.telegram.org/bot' + token + '/'
proxies = {'https': 'http://193.85.228.180:	36247'}

app = Flask(__name__)
sslify = SSLify(app)

# def get_updates():
#     url = URL + 'getupdates'
#     print(url)
#     r = requests.get(url, proxies=proxies)
#     print(r)
#     return r.json()

# def get_message():
#     data = get_updates()
#
#     chat_id = data['result'][-1]['message']['chat']['id']
#     message_text = data['result'][-1]['message']['text']
#
#     message = {'chat_id': chat_id,
#                'text': message_text}
#     return message

def send_message(chat_id, text='wait, please'):
    url = URL + 'sendMessage'
    answer = {'chat_id': chat_id, 'text': text}
    r = requests.post(url, json=answer, proxies=proxies)
    return r.json()

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        r = request.get_json()
        chat_id = r['message']['chat']['id']
        message = r['message']['text']

        if len(message) != 0:
            send_message(chat_id, message)

        return jsonify(r)
    return '<h1>test</h1>'

def main():
    # answer = get_message()
    # chat_id = answer['chat_id']
    # text = answer['text']
    #
    # if len(text) != 0:
    #     send_message(chat_id)
    pass

if __name__ == '__main__':
    # main()
    app.run()
