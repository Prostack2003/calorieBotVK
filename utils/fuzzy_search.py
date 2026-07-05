import re
from thefuzz import process, fuzz
from sqlalchemy.orm import Session
from database.models import GlobalProduct, UserProduct

def search_products(query: str, user_id: int, session: Session, limit: int = 5, threshold: int = 70):
    """
    Нечеткий поиск продуктов
    
    Args:
        query: Запрос пользователя (например, "греча")
        user_id: VK ID пользователя
        session: Сессия SQLAlchemy
        limit: Максимальное количество результатов
        threshold: Минимальный процент схожести (0-100)
    
    Returns:
        Список словарей с продуктами: [{name, calories, proteins, fats, carbs, source}]
    """
    results = []
    
    # 1. Сначала ищем в личных продуктах пользователя
    user_products = session.query(UserProduct).filter(UserProduct.user_id == user_id).all()
    user_product_names = {p.name: p for p in user_products}
    
    if user_product_names:
        user_matches = process.extract(
            query,
            user_product_names.keys(),
            scorer=fuzz.WRatio,
            limit=limit
        )
        
        for name, score in user_matches:
            if score >= threshold:
                product = user_product_names[name]
                results.append({
                    'name': product.name,
                    'calories': product.calories,
                    'proteins': product.proteins,
                    'fats': product.fats,
                    'carbs': product.carbs,
                    'score': score,
                    'source': 'user'
                })
    
    # 2. Затем ищем в общей базе
    global_products = session.query(GlobalProduct).all()
    global_product_names = {p.name: p for p in global_products}
    
    if global_product_names:
        global_matches = process.extract(
            query,
            global_product_names.keys(),
            scorer=fuzz.WRatio,
            limit=limit
        )
        
        for name, score in global_matches:
            if score >= threshold:
                product = global_product_names[name]
                results.append({
                    'name': product.name,
                    'calories': product.calories,
                    'proteins': product.proteins,
                    'fats': product.fats,
                    'carbs': product.carbs,
                    'score': score,
                    'source': 'global'
                })
    
    # Сортируем по score и убираем дубликаты
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Убираем дубликаты по имени
    seen = set()
    unique_results = []
    for r in results:
        if r['name'] not in seen:
            seen.add(r['name'])
            unique_results.append(r)
    
    return unique_results[:limit]


def extract_weight_from_text(text: str) -> float:
    """
    Извлечение веса из текста пользователя
    
    Примеры:
        "150г гречки" -> 150.0
        "гречка 200 грамм" -> 200.0
        "100 г риса" -> 100.0
    
    Returns:
        Вес в граммах или None, если не найден
    """
    # Паттерн для поиска числа с "г", "гр", "грамм"
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:г|гр|грамм|gram)',
        r'(\d+(?:\.\d+)?)\s*г',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    
    return None

