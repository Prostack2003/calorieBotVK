import re
from config import user_states
from database import SessionLocal, UserProduct, GlobalProduct
from utils.messenger import send_message
from utils.fuzzy_search import search_products, extract_weight_from_text
from keyboards import get_main_keyboard, get_cancel_keyboard, get_product_selection_keyboard, get_source_selection_keyboard


def handle_search(user_id, peer_id, text, target_date=None):
    """Обработка поиска продукта"""
    session = SessionLocal()
    try:
        weight = extract_weight_from_text(text)
        clean_text = re.sub(r'\d+(?:\.\d+)?\s*(?:г|гр|грамм|граммов|gram)', '', text, flags=re.IGNORECASE).strip()
        clean_text = re.sub(r'[,\.\s]+', ' ', clean_text).strip()
        
        if not clean_text:
            send_message(peer_id, "Не удалось определить название продукта.", get_main_keyboard())
            return
        
        # Проверка веса
        if weight is not None:
            if weight <= 0:
                send_message(peer_id, "❌ Вес должен быть больше нуля.\n\nПопробуйте ещё раз, например: банан 150г", get_main_keyboard())
                return
            if weight > 10000:
                send_message(peer_id, "❌ Слишком большой вес! Максимум 10000г (10кг).\n\nПопробуйте ещё раз, например: банан 150г", get_main_keyboard())
                return
        
        has_weight_in_text = bool(re.search(r'\d+(?:\.\d+)?\s*(?:г|гр|грамм|граммов|gram)', text, flags=re.IGNORECASE))
        if has_weight_in_text and weight is None:
            send_message(peer_id, "❌ Некорректный вес. Вес должен быть от 1 до 10000 грамм.\n\nПопробуйте ещё раз, например: банан 150г", get_main_keyboard())
            return
        
        # ============================================
        # ШАГ 1: Поиск в локальной базе (максимум 5)
        # ============================================
        products = search_products(clean_text, user_id, session, limit=5)
        
        if products:
            # Нашли в локальной базе — показываем с кнопками выбора источника
            user_states[user_id] = {
                'state': 'selecting',
                'products': products,
                'weight': weight,
                'add_date': target_date,
                'source': 'local'  # ← Помечаем источник
            }
            
            date_str = f" за {target_date.strftime('%d.%m.%Y')}" if target_date else ""
            msg = f"📦 Найдено в базе ({len(products)}):{date_str}\n\n"
            for i, p in enumerate(products, 1):
                msg += f"{i}. {p['name']} ({p['calories']} ккал/100г)\n"
            
            if weight:
                msg += f"\n⚖️ Вес: {weight}г"
            else:
                msg += f"\n⚖️ Вес не указан"
            
            msg += "\n\nВыберите продукт или:"
            
            send_message(peer_id, msg, get_product_selection_keyboard(products, show_online=True))
            return
        
        # ============================================
        # ШАГ 2: Не нашли локально — предлагаем варианты
        # ============================================
        from utils.logger import logger
        logger.info(f"🔍 Локальная база пуста для '{clean_text}'")
        
        # Сразу показываем меню выбора
        user_states[user_id] = {
            'state': 'ask_source',
            'query': clean_text,
            'weight': weight,
            'add_date': target_date
        }
        
        msg = f"❌ Не нашёл '{clean_text}' в локальной базе.\n\n"
        msg += "Что хотите сделать?"
        
        send_message(peer_id, msg, get_source_selection_keyboard())
        
    finally:
        session.close()

def handle_selection(user_id, peer_id, product_name):
    """Обработка выбора продукта из списка"""
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    selected = next((p for p in state['products'] if p['name'] == product_name), None)
    
    if not selected:
        send_message(peer_id, "Продукт не найден.", get_main_keyboard())
        return
    
    target_date = state.get('add_date')
    
    if state['weight']:
        # Вес уже известен — сразу сохраняем
        from .log import save_log
        save_log(user_id, peer_id, selected, state['weight'], target_date)
    else:
        # Веса нет — переходим в состояние ввода веса
        user_states[user_id] = {'state': 'weight', 'product': selected, 'add_date': target_date}
        date_str = f" за {target_date.strftime('%d.%m.%Y')}" if target_date else ""
        send_message(peer_id, f"Выбрано: {selected['name']}{date_str}\nВведите вес в граммах:", get_cancel_keyboard())


def handle_selection_from_list(user_id, peer_id, product_name):
    """Альтернативный выбор продукта (через payload)"""
    session = SessionLocal()
    try:
        product = session.query(UserProduct).filter_by(user_id=user_id, name=product_name).first()
        if not product:
            product = session.query(GlobalProduct).filter_by(name=product_name).first()
        
        if not product:
            send_message(peer_id, "Продукт не найден.", get_main_keyboard())
            return
        
        product_data = {
            'name': product.name,
            'calories': product.calories,
            'proteins': product.proteins,
            'fats': product.fats,
            'carbs': product.carbs
        }
        
        user_states[user_id] = {'state': 'weight', 'product': product_data}
        
        send_message(
            peer_id,
            f"✅ Вы выбрали: {product.name}\n"
            f" КБЖУ на 100г: {product.calories} ккал | Б:{product.proteins} Ж:{product.fats} У:{product.carbs}\n\n"
            "️ Введите вес в граммах (например: 150):",
            get_cancel_keyboard()
        )
    finally:
        session.close()


def handle_search_online(user_id, peer_id):
    """Поиск в интернете (Calorizator)"""
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    query = state.get('query') or state.get('products', [{}])[0].get('name', '').split()[0]
    weight = state.get('weight')
    target_date = state.get('add_date')
    
    if not query:
        send_message(peer_id, "❌ Не удалось определить запрос.", get_main_keyboard())
        return
    
    from utils.logger import logger
    logger.info(f"🌐 Поиск в интернете: '{query}'")
    
    from utils.calorizator_api import search_calorizator
    online_products = search_calorizator(query, limit=5)
    
    if online_products:
        user_states[user_id] = {
            'state': 'selecting',
            'products': online_products,
            'weight': weight,
            'add_date': target_date,
            'source': 'online'  # ← Помечаем источник
        }
        
        date_str = f" за {target_date.strftime('%d.%m.%Y')}" if target_date else ""
        msg = f"🌐 Найдено в интернете ({len(online_products)}):{date_str}\n\n"
        for i, p in enumerate(online_products, 1):
            msg += f"{i}. {p['name']} ({p['calories']} ккал/100г)\n"
        
        if weight:
            msg += f"\n⚖️ Вес: {weight}г"
        else:
            msg += f"\n⚖️ Вес не указан"
        
        send_message(peer_id, msg, get_product_selection_keyboard(online_products, show_online=False))
    else:
        send_message(peer_id, f"❌ Не нашёл '{query}' в интернете.\n\nХотите добавить свой продукт?", get_main_keyboard())
        user_states[user_id] = {'state': 'ask_custom', 'query': query, 'weight': weight, 'add_date': target_date}


def handle_ask_custom(user_id, peer_id):
    """Переход к добавлению своего продукта"""
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    query = state.get('query', '')
    weight = state.get('weight')
    target_date = state.get('add_date')
    
    user_states[user_id] = {
        'state': 'ask_custom',
        'query': query,
        'weight': weight,
        'add_date': target_date
    }
    
    msg = f"✏️ Хотите добавить свой продукт?\n\n"
    if query:
        msg += f"Название: {query}\n"
    msg += "\nНапишите 'да' для добавления или название другого продукта."
    
    send_message(peer_id, msg, get_main_keyboard())