"""
Модуль для парсинга курсов валют
Содержит два парсера:
1. parse_rbc_rates() - курсы наличных валют с РБК (для разных банков)
2. parse_cbr_rates() - официальные курсы ЦБ РФ
"""

import json
import time
import re
import requests
from typing import Dict, List, Optional
from datetime import datetime

# Импорты для РБК парсера
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from bs4 import BeautifulSoup
    import config
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Внимание: Selenium не установлен. Парсер РБК недоступен.")


# ========== ПАРСЕР ЦБ РФ ==========

def parse_cbr_rates() -> Optional[Dict]:
    """
    Парсит официальные курсы валют ЦБ РФ через JSON API
    
    Returns:
        dict: Словарь с курсами валют или None при ошибке
        {
            'date': '2025-11-02T11:30:00+03:00',
            'timestamp': '2025-11-01T19:53:03.396Z',
            'valutes': {
                'USD': {'name': 'Доллар США', 'course': 80.89, ...},
                ...
            }
        }
    """
    url = 'https://www.cbr-xml-daily.ru/daily_json.js'
    
    try:
        print('Запрос к API ЦБ РФ...')
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('Valute') or not data['Valute'].get('USD'):
            raise ValueError("Данные некорректны - отсутствуют основные валюты")
        
        result = {}
        date = data.get('Date', datetime.now().isoformat())
        
        # Обрабатываем все валюты
        for key, valute in data['Valute'].items():
            course = float(valute['Value']) / float(valute['Nominal'])
            
            result[key] = {
                'name': valute['Name'],
                'nominal': int(valute['Nominal']),
                'value': float(valute['Value']),
                'course': round(course, 4),
                'charCode': valute['CharCode'],
                'numCode': valute['NumCode']
            }
        
        output = {
            'date': date,
            'timestamp': datetime.now().isoformat(),
            'valutes': result
        }
        
        # Сохраняем в файл
        with open('cbr_rates.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f'✓ ЦБ РФ: получено {len(result)} валют')
        return output
        
    except requests.RequestException as e:
        print(f'✗ Ошибка запроса к ЦБ РФ: {e}')
        return None
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        print(f'✗ Ошибка парсинга данных ЦБ РФ: {e}')
        return None
    except Exception as e:
        print(f'✗ Неожиданная ошибка (ЦБ РФ): {e}')
        return None


# ========== ПАРСЕР РБК ==========

def parse_rbc_rates() -> Optional[List[Dict]]:
    """
    Парсит курсы наличных валют с РБК (для разных банков)
    
    Returns:
        list: Список словарей с курсами или None при ошибке
        [
            {'bank': 'Название банка', 'buy': 81.6, 'sell': 80.9},
            ...
        ]
    """
    if not SELENIUM_AVAILABLE:
        print('✗ Парсер РБК недоступен: требуется Selenium')
        return None
    
    driver = None
    temp_dir = None
    
    try:
        print('Инициализация браузера для РБК...')
        driver = _setup_driver()
        temp_dir = getattr(driver, 'temp_dir', None)
        
        url = _build_url()
        print(f'Открываем страницу: {url}')
        
        driver.get(url)
        _wait_for_page_ready(driver)
        
        _click_professional_version(driver)
        
        results = _parse_rates_table(driver)
        
        if results:
            # Сохраняем в файл
            with open('rbc_rates.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f'✓ РБК: получено {len(results)} записей')
        
        return results
        
    except Exception as e:
        print(f'✗ Ошибка парсинга РБК: {e}')
        return None
        
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        
        # Очистка временной директории
        if temp_dir:
            import shutil
            import os
            try:
                time.sleep(1)
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ РБК ==========

def _setup_driver():
    """Настройка Chrome драйвера"""
    import tempfile
    import os
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Работа в фоне
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    
    temp_dir = tempfile.mkdtemp(prefix='chrome_profile_')
    options.add_argument(f'--user-data-dir={temp_dir}')
    
    driver = webdriver.Chrome(options=options)
    driver.temp_dir = temp_dir
    driver.set_page_load_timeout(60)
    driver.set_script_timeout(60)
    
    return driver


def _build_url(currency=None, city=None, diapason=None):
    """Построение URL с параметрами"""
    params = config.DEFAULT_PARAMS.copy()
    
    if currency is not None:
        params['currency'] = currency
    if city is not None:
        params['city'] = city
    if diapason is not None:
        params['diapason'] = diapason
    
    query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
    return f"{config.BASE_URL}?{query_string}"


def _wait_for_page_ready(driver, timeout=30):
    """Ожидание загрузки страницы"""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        time.sleep(3)
        return True
    except:
        return False


def _click_professional_version(driver):
    """Переключение на профессиональную версию"""
    try:
        if not _wait_for_page_ready(driver):
            return False
        
        wait = WebDriverWait(driver, config.ELEMENT_WAIT_TIMEOUT)
        
        try:
            toggle_button = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "js-toggle-versions-text"))
            )
            label = toggle_button.text.strip()
            
            if 'Стандартная версия' in label:
                return True
            
            btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "js-toggle-versions-text")))
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(2)
            return True
        except:
            return True
    except:
        return True


def _parse_rates_table(driver):
    """Парсинг таблицы с курсами"""
    try:
        wait = WebDriverWait(driver, 30)
        
        # Пробуем найти элементы
        selectors = ['.quote__office__one.js-one-office', '.quote__office__one']
        element_found = False
        
        for selector in selectors:
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                element_found = True
                break
            except:
                continue
        
        time.sleep(5)
        
        # Скролл для загрузки всех элементов
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        rows = soup.select('.quote__office__one.js-one-office')
        if not rows:
            rows = soup.select('.quote__office__one')
        
        if not rows:
            return []
        
        results = []
        
        for row in rows:
            # Пропускаем заголовки и скрытые элементы
            style = row.get('style', '')
            if 'display:none' in style or 'display: none' in style:
                continue
            
            if row.find(attrs={'data-banner': True}):
                continue
            
            classes = row.get('class', [])
            if 'quote__office_head' in classes or 'quote__office_head__one' in str(classes):
                continue
            
            # Извлекаем данные
            name_elem = row.select_one('.quote__office__one__name')
            buy_elem = row.select_one('.quote__office__cell.quote__office__one__buy') or \
                       row.select_one('.quote__office__one__buy')
            sell_elem = row.select_one('.quote__office__cell.quote__office__one__sell') or \
                        row.select_one('.quote__office__one__sell')
            
            def get_text(elem):
                if not elem:
                    return None
                text = elem.get_text(strip=True, separator=' ')
                text = text.replace('\xa0', ' ').replace(',', '.')
                text = ' '.join(text.split())
                match = re.search(r'\d+\.?\d*', text)
                return match.group(0) if match else None
            
            def get_name_text(elem):
                if not elem:
                    return None
                text = elem.get_text(strip=True, separator=' ')
                text = text.replace('\xa0', ' ')
                text = ' '.join(text.split())
                cleaned = text.replace('.', '').replace(',', '').replace(' ', '').replace('-', '').replace('+', '')
                if cleaned.isdigit() and len(cleaned) < 5:
                    return None
                return text if text else None
            
            name = get_name_text(name_elem)
            buy = get_text(buy_elem)
            sell = get_text(sell_elem)
            
            # Фильтрация
            if not name or len(name.strip()) < 3:
                continue
            if name in ['Банк', 'Продажа', 'Покупка']:
                continue
            if name.strip().replace('.', '').replace(',', '').replace(' ', '').replace('-', '').isdigit():
                continue
            
            # Проверка чисел
            def is_number(s):
                if not s:
                    return False
                try:
                    float(s)
                    return True
                except:
                    return False
            
            if is_number(buy) or is_number(sell):
                try:
                    buy_float = float(buy) if buy and is_number(buy) else None
                    sell_float = float(sell) if sell and is_number(sell) else None
                    
                    if buy_float is not None or sell_float is not None:
                        results.append({
                            'bank': name,
                            'buy': buy_float,
                            'sell': sell_float
                        })
                except:
                    continue
        
        # Удаляем дубликаты и сортируем
        unique_results = []
        seen = set()
        for r in results:
            key = (r['bank'], r['buy'], r['sell'])
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
        
        unique_results.sort(key=lambda x: (x['buy'] if x['buy'] is not None else 1e9, x['bank']))
        
        return unique_results
        
    except Exception as e:
        print(f'Ошибка при парсинге таблицы: {e}')
        return []


# ========== ГЛАВНАЯ ФУНКЦИЯ ==========

def parse_all_rates():
    """
    Запускает оба парсера и возвращает результаты
    
    Returns:
        tuple: (rbc_data, cbr_data)
    """
    print('=' * 60)
    print('Запуск парсеров курсов валют')
    print('=' * 60)
    
    cbr_data = parse_cbr_rates()
    print()
    rbc_data = parse_rbc_rates()
    
    return rbc_data, cbr_data


if __name__ == "__main__":
    parse_all_rates()


