# config.py

# URL для парсинга
BASE_URL = "https://cash.rbc.ru/cash/"

# Параметры по умолчанию
DEFAULT_PARAMS = {
    'currency': 3,  # валюта
    'city': 1,      # город (Москва)
    'diapason': 'all'  # все банки
}

# Таймауты
PAGE_LOAD_TIMEOUT = 10
ELEMENT_WAIT_TIMEOUT = 5