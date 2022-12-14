import time
import telegram.ext
import telegram
import os
import requests
import logging

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


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
        except:
            logging.CRITICAL(f'Отсутствие обязательной переменной {var}')
            return False


def send_message(bot, message):
    """Выводит сообщение в бот"""
    chat_id = TELEGRAM_CHAT_ID
    text = message
    bot.send_message(chat_id, text)


def get_api_answer(timestamp):
    try:
        homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=timestamp)
        homework_statuses.status_code == 200
    except requests.RequestException:
        logging.error(f'Ошибка при запросе к основному API')
    return homework_statuses.json()

def check_response(response):
    ...


def parse_status(homework):
    ...

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    chec1k_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    get_api_answer(timestamp)
    send_message(bot, parse_status())

    ...

    while True:
        try:
            response = get_api_answer(timestamp)

            time.sleep(10.0)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(10.0)


if __name__ == '__main__':
    main()
