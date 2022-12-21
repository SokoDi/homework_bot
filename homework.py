import time
import telegram.ext
import telegram
import os
import requests
import logging
from settings.settings import RETRY_PERIOD, ENDPOINT, HOMEWORK_VERDICTS
from settings.exceptions import CustomError

from http import HTTPStatus
from dotenv import load_dotenv

load_dotenv()

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('main.log', 'w', 'utf-8')
handler.setFormatter(
    logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
)
root_logger.addHandler(handler)


PRACTICUM_TOKEN = os.getenv('PRACTICUM')
TELEGRAM_TOKEN = os.getenv('TELEGRAM')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


def check_tokens():
    """Проверяем обязательные переменные."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Выводит сообщение в бот."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
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
    try:
        if isinstance(api_out.json(), dict):
            api_out = api_out.json()
    except TypeError:
        logging.error('Не валидные данные json()')
    return api_out


def check_response(response):
    """Проверка наличия передоваемых данных с API."""
    try:
        return response['homeworks'][0]
    except CustomError:
        if not response['homeworks']:
            logging.debug('Список "response" пуст')
            raise CustomError('Список "response" пуст')
    except Exception:
        if not isinstance(response, dict):
            raise TypeError(
                'Ошибка типа данных "response" не содержит словарь'
            )
        if 'homeworks' not in response:
            raise KeyError('Нет ключа "homeworks" ')
        if not isinstance(response['homeworks'], list):
            raise TypeError(
                'Ошибка типа данных "homeworks" не содержит список'
            )


def parse_status(homework):
    """Оброботка и передача статуса проекта."""
    if 'homework_name' not in homework:
        raise KeyError(
            'Переменная "homework" не содержит ключ "homework_name"'
        )
    homework_name = homework['homework_name']
    if 'status' not in homework:
        raise KeyError(
            'Переменная "status" не содержит ключ "homework_name"'
        )
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise KeyError('Не известный статус')
    verdict = HOMEWORK_VERDICTS[status]
    return (f'Изменился статус проверки работы "{homework_name}". {verdict}')


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствие обязательной переменной')
        return
    new_stats = ''
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            get_api = get_api_answer(timestamp)
            response = check_response(get_api)
            if response is None:
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
    main()
