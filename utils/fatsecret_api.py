import requests
import time
from config import FATSECRET_CLIENT_ID, FATSECRET_CLIENT_SECRET
from utils.logger import logger


# Кэш для access token
_access_token = None
_token_expires_at = 0


def _get_access_token() -> str:
    """Получение access token через OAuth 2.0"""
    global _access_token, _token_expires_at
    
    if _access_token and time.time() < _token_expires_at - 60:
        return _access_token
    
    if not FATSECRET_CLIENT_ID or not FATSECRET_CLIENT_SECRET:
        raise ValueError("FatSecret credentials не настроены в config.py")
    
    logger.info("🔐 FatSecret: Получение access token...")
    
    url = "https://oauth.fatsecret.com/connect/token"
    data = {
        "grant_type": "client_credentials",
        "scope": "basic",
        "client_id": FATSECRET_CLIENT_ID,
        "client_secret": FATSECRET_CLIENT_SECRET
    }
    
    try:
        response = requests.post(url, data=data, timeout=15)
        response.raise_for_status()
        
        result = response.json()
        _access_token = result.get("access_token")
        expires_in = result.get("expires_in", 3600)
        _token_expires_at = time.time() + expires_in
        
        logger.info(f"✅ FatSecret: Token получен, действует {expires_in}с")
        return _access_token
        
    except Exception as e:
        logger.error(f"❌ FatSecret: Ошибка получения token: {e}")
        raise


def search_fatsecret(query: str, limit: int = 5) -> list:
    """
    Поиск продуктов в FatSecret API через OAuth 2.0.
    """
    logger.info(f"🍎 FatSecret: Поиск '{query}'")
    
    if not query or len(query.strip()) < 2:
        return []
    
    try:
        token = _get_access_token()
    except Exception as e:
        logger.error(f"❌ FatSecret: Не удалось получить token: {e}")
        return []
    
    # Пробуем несколько вариантов запроса
    strategies = [
        _search_via_post,
        _search_via_get,
    ]
    
    for strategy in strategies:
        try:
            results = strategy(token, query, limit)
            if results:
                logger.info(f"✅ FatSecret: Найдено {len(results)} продуктов через {strategy.__name__}")
                return results
        except Exception as e:
            logger.warning(f"⚠️ FatSecret: Стратегия {strategy.__name__} не сработала: {e}")
            continue
    
    logger.warning(f"❌ FatSecret: Не найдено по запросу '{query}'")
    return []


def _search_via_post(token: str, query: str, limit: int) -> list:
    """Поиск через POST запрос"""
    url = "https://platform.fatsecret.com/rest/server.api"
    
    params = {
        "method": "foods.search",
        "search_expression": query,
        "max_results": limit,
        "page_number": 0,
        "format": "json"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    logger.info(f"🍎 FatSecret POST: {url}")
    logger.info(f"🍎 FatSecret POST: Параметры {params}")
    
    response = requests.post(url, params=params, headers=headers, timeout=15)
    
    logger.info(f"🍎 FatSecret POST: Статус {response.status_code}")
    logger.info(f"🍎 FatSecret POST: Ответ (первые 500 символов): {response.text[:500]}")
    
    if response.status_code != 200:
        return []
    
    try:
        data = response.json()
        return _parse_search_results(data, limit)
    except Exception as e:
        logger.error(f"❌ FatSecret POST: Ошибка парсинга JSON: {e}")
        return []


def _search_via_get(token: str, query: str, limit: int) -> list:
    """Поиск через GET запрос"""
    url = "https://platform.fatsecret.com/rest/server.api"
    
    params = {
        "method": "foods.search",
        "search_expression": query,
        "max_results": limit,
        "page_number": 0,
        "format": "json"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    logger.info(f"🍎 FatSecret GET: {url}")
    logger.info(f"🍎 FatSecret GET: Параметры {params}")
    
    response = requests.get(url, params=params, headers=headers, timeout=15)
    
    logger.info(f"🍎 FatSecret GET: Статус {response.status_code}")
    logger.info(f"🍎 FatSecret GET: Ответ (первые 500 символов): {response.text[:500]}")
    
    if response.status_code != 200:
        return []
    
    try:
        data = response.json()
        return _parse_search_results(data, limit)
    except Exception as e:
        logger.error(f"❌ FatSecret GET: Ошибка парсинга JSON: {e}")
        return []


def _parse_search_results(data: dict, limit: int) -> list:
    """Парсинг результатов поиска с детальным логированием"""
    logger.info(f"🍎 FatSecret: Парсинг ответа: {list(data.keys())}")
    
    products = []
    
    try:
        foods_data = data.get("foods", {})
        if not foods_data:
            logger.warning(f"⚠️ FatSecret: Нет поля 'foods' в ответе")
            return []
        
        logger.info(f"🍎 FatSecret: Структура foods: {list(foods_data.keys())}")
        
        foods = foods_data.get("food", [])
        if isinstance(foods, dict):
            foods = [foods]
        
        logger.info(f"🍎 FatSecret: Найдено {len(foods)} продуктов в ответе")
        
        for food in foods:
            try:
                name = food.get("food_name", "").strip()
                if not name:
                    continue
                
                brand = food.get("brand_name", "")
                if brand:
                    name = f"{name} ({brand})"
                
                servings = food.get("servings", {}).get("serving", [])
                if isinstance(servings, dict):
                    servings = [servings]
                
                per_100g = None
                for serving in servings:
                    metric_amount = serving.get("metric_serving_amount")
                    if metric_amount and float(metric_amount) == 100.0:
                        per_100g = serving
                        break
                
                if not per_100g and servings:
                    per_100g = servings[0]
                
                if not per_100g:
                    logger.debug(f"🍎 FatSecret: Пропуск '{name}' — нет порции")
                    continue
                
                c = float(per_100g.get("calories", 0) or 0)
                p = float(per_100g.get("protein", 0) or 0)
                f = float(per_100g.get("fat", 0) or 0)
                u = float(per_100g.get("carbohydrate", 0) or 0)
                
                if c <= 0:
                    logger.debug(f"🍎 FatSecret: Пропуск '{name}' — нет калорий")
                    continue
                
                products.append({
                    "name": name,
                    "calories": round(c, 1),
                    "proteins": round(p, 1),
                    "fats": round(f, 1),
                    "carbs": round(u, 1),
                    "source": "fatsecret"
                })
                
                if len(products) >= limit:
                    break
                    
            except (ValueError, TypeError, KeyError) as e:
                logger.debug(f"🍎 FatSecret: Пропуск продукта: {e}")
                continue
        
        logger.info(f"✅ FatSecret: Успешно распарсено {len(products)} продуктов")
        return products
        
    except Exception as e:
        logger.error(f"❌ FatSecret: Ошибка парсинга: {e}", exc_info=True)
        return []