import time
import telegram.ext
import telegram
import os
import requests
import logging
import json

from dotenv import load_dotenv

load_dotenv()

root_logger= logging.getLogger()
root_logger.setLevel(logging.INFO)
handler = logging.FileHandler('main.log', 'w', 'utf-8') 
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
root_logger.addHandler(handler)



PRACTICUM_TOKEN = os.getenv('PRACTICUM')
TELEGRAM_TOKEN = os.getenv('TELEGRAM')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def chec1k_tokens():
    """Проверяем обязательные переменные"""
    ENV_VARS = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for var in ENV_VARS:
        try:
            var in os.environ
        except Exception as critical:
            logging.critical(f'Отсутствие обязательной переменной {var}')


def send_message(bot, message):
    """Выводит сообщение в бот"""
    chat_id = TELEGRAM_CHAT_ID
    text = message
    bot.send_message(chat_id, text)


def get_api_answer(timestamp):
    api_out = requests.get(ENDPOINT, headers=HEADERS, params={'from_date': timestamp})
    return api_out.json()

def check_response(response):
    if response["homeworks"] == None:
        main()
    else:
        return response


def parse_status(homework):
    homework_name = homework["homeworks"][0]["lesson_name"]
    status = homework["homeworks"][0]["status"]
    verdict = HOMEWORK_VERDICTS[status]
    return(f'Изменился статус проверки работы "{homework_name}". {verdict}')

def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            chec1k_tokens()
            get_api = get_api_answer(timestamp)
            response = check_response(get_api)
            maseg = parse_status(response)
            send_message(bot, maseg)
            time.sleep(RETRY_PERIOD)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
