import time
import telegram.ext
import telegram
import os
import requests
import logging

from http import HTTPStatus
from dotenv import load_dotenv

load_dotenv()

root_logger = logging.getLogger(__name__)


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


def check_tokens():
    """Проверяем обязательные переменные."""
    ENV_VARS = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for var in ENV_VARS:
        try:
            var in os.environ
        except Exception:
            logging.critical(f'Отсутствие обязательной переменной {var}')
        if var is None:
            return False


def send_message(bot, message):
    """Выводит сообщение в бот."""
    try:
        chat_id = TELEGRAM_CHAT_ID
        text = message
        bot.send_message(chat_id, text)
        logging.debug('Сообщение было корректно отправленно в бот!')
    except Exception:
        logging.error('Бот не смог отправить сообщение')


def get_api_answer(timestamp):
    """Делаем запрос к API."""
    try:
        api_out = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
    except requests.RequestException:
        logging.error('Сервис недоступен!')
    if api_out.status_code != HTTPStatus.OK:
        raise Exception.EndpointNotOK('Статус отличен от 200 ')
    return api_out.json()


def check_response(response):
    """Проверка наличия передоваемых данных с API."""
    if not isinstance(response, dict):
        raise TypeError('asd')
    if 'homeworks' not in response:
        raise KeyError('Нет ключа "homeworks" ')
    if not isinstance(response['homeworks'], list):
        raise TypeError(
            'Ошибка типа данных "homeworks" не содержит список'
        )
    if not response['homeworks']:
        return False
    return response['homeworks'][0]


def parse_status(homework):
    """Оброботка и передача статуса проекта."""
    if 'homework_name' not in homework:
        raise KeyError(
            'Переменная "homework" не содержит ключ "homework_name"'
        )
    homework_name = homework['homework_name']
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise KeyError('Не известный статус')
    verdict = HOMEWORK_VERDICTS[status]
    return (f'Изменился статус проверки работы "{homework_name}". {verdict}')


def main():
    """Основная логика работы бота."""
    new_stats = ''
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            if check_tokens() is False:
                break
            get_api = get_api_answer(timestamp)
            response = check_response(get_api)
            if response is False:
                logging.debug('Список "response" пуст')
                time.sleep(RETRY_PERIOD)
                continue
            if new_stats == response['status']:
                time.sleep(RETRY_PERIOD)
                continue
            new_stats = response['status']
            new_massage = parse_status(response)
            send_message(bot, new_massage)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    root_logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler('main.log', 'w', 'utf-8')
    handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
    )
    root_logger.addHandler(handler)
    main()
