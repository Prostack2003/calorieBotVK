import requests
import re
import time
from bs4 import BeautifulSoup
from utils.logger import logger


BASE_URL = "https://calorizator.ru"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}
TIMEOUT = 20  # Увеличили до 20 секунд
MAX_PRODUCTS = 5


def search_calorizator(query: str, limit: int = 5) -> list:
    """
    Поиск продуктов на Calorizator.ru.
    Стратегия:
    1. Поиск по сайту → находим ссылки на продукты
    2. Для каждой ссылки парсим КБЖУ со страницы продукта
    """
    logger.info(f"🔍 Calorizator: Поиск '{query}'")
    
    if not query or len(query.strip()) < 2:
        return []
    
    try:
        # Шаг 1: Поиск по сайту
        search_url = f"{BASE_URL}/search/node/{requests.utils.quote(query)}"
        logger.info(f"🔍 Calorizator: URL поиска {search_url}")
        
        response = requests.get(search_url, headers=HEADERS, timeout=TIMEOUT)
        
        if response.status_code != 200:
            logger.error(f"❌ Calorizator: HTTP {response.status_code}")
            return []
        
        # Шаг 2: Парсинг результатов поиска — ищем ссылки на продукты
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Находим все ссылки, содержащие /product/ в href
        product_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/product/' in href and href not in product_links:
                product_links.append(href)
        
        logger.info(f"🔍 Calorizator: Найдено {len(product_links)} ссылок на продукты")
        
        if not product_links:
            return []
        
        # Шаг 3: Получаем КБЖУ для каждого продукта (максимум limit)
        products = []
        for link in product_links[:limit * 2]:  # Берём с запасом, т.к. некоторые могут не иметь КБЖУ
            if len(products) >= limit:
                break
            
            try:
                # Небольшая задержка, чтобы не перегружать сайт
                time.sleep(0.5)
                
                kbju = _get_product_kbju(link)
                if kbju:
                    products.append({
                        'name': kbju['name'],
                        'calories': kbju['calories'],
                        'proteins': kbju['proteins'],
                        'fats': kbju['fats'],
                        'carbs': kbju['carbs'],
                        'source': 'calorizator',
                        'url': link
                    })
            except Exception as e:
                logger.debug(f"🔍 Calorizator: Пропуск {link}: {e}")
                continue
        
        logger.info(f"✅ Calorizator: Найдено {len(products)} продуктов с КБЖУ")
        return products
        
    except requests.exceptions.Timeout:
        logger.error(f"⏱️ Calorizator: Таймаут после {TIMEOUT}с")
        return []
    except Exception as e:
        logger.error(f"❌ Calorizator: Ошибка {e}", exc_info=True)
        return []


def _get_product_kbju(product_url: str) -> dict:
    """Получение КБЖУ со страницы продукта"""
    try:
        full_url = product_url if product_url.startswith('http') else f"{BASE_URL}{product_url}"
        
        response = requests.get(full_url, headers=HEADERS, timeout=TIMEOUT)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Извлекаем название продукта (заголовок h1)
        h1 = soup.find('h1')
        if not h1:
            return None
        name = h1.get_text(strip=True)
        
        if not name:
            return None
        
        # Ищем КБЖУ в fieldset с классом group-base
        fieldset = soup.find('fieldset', class_='group-base')
        if not fieldset:
            return None
        
        # Извлекаем значения по CSS-классам
        kcal = _extract_field_value(fieldset, 'field-field-kcal')
        protein = _extract_field_value(fieldset, 'field-field-protein')
        fat = _extract_field_value(fieldset, 'field-field-fat')
        carb = _extract_field_value(fieldset, 'field-field-carbohydrate')
        
        if kcal is None or kcal <= 0:
            return None
        
        return {
            'name': name,
            'calories': kcal,
            'proteins': protein or 0,
            'fats': fat or 0,
            'carbs': carb or 0
        }
        
    except Exception as e:
        logger.error(f"❌ Calorizator get KBJU: {e}")
        return None


def _extract_field_value(fieldset, field_class: str) -> float:
    """Извлечение числового значения из поля fieldset"""
    try:
        field = fieldset.find('div', class_=field_class)
        if not field:
            return None
        
        # Ищем div с классом field-item
        field_items = field.find_all('div', class_='field-item')
        
        for item in field_items:
            # Получаем текст, убираем метку и лишние символы
            text = item.get_text(strip=True)
            
            # Убираем метку типа "Калории, ккал:"
            text = re.sub(r'^[^:]+:\s*', '', text)
            text = text.replace(',', '.').replace('&nbsp;', '').strip()
            
            # Извлекаем число
            match = re.search(r'[\d.]+', text)
            if match:
                return float(match.group())
        
        return None
    except Exception as e:
        logger.debug(f"❌ Calorizator extract: {e}")
        return None