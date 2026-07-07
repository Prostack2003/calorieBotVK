import re
from config import user_states
from database import SessionLocal, UserProduct, GlobalProduct
from utils.messenger import send_message
from utils.fuzzy_search import search_products, extract_weight_from_text
from keyboards import get_main_keyboard, get_cancel_keyboard, get_product_selection_keyboard


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
        
        # Проверка веса на разумный диапазон
        if weight is not None:
            if weight <= 0:
                send_message(
                    peer_id,
                    "❌ Вес должен быть больше нуля.\n\n"
                    "Попробуйте ещё раз, например: банан 150г",
                    get_main_keyboard()
                )
                return
            
            if weight > 10000:
                send_message(
                    peer_id,
                    "❌ Слишком большой вес! Максимум 10000г (10кг).\n"
                    "Если вы действительно съели столько, разделите на несколько порций.\n\n"
                    "Попробуйте ещё раз, например: банан 150г",
                    get_main_keyboard()
                )
                return
        
        # Проверка: если вес был указан, но не прошёл валидацию
        has_weight_in_text = bool(re.search(r'\d+(?:\.\d+)?\s*(?:г|гр|грамм|граммов|gram)', text, flags=re.IGNORECASE))
        if has_weight_in_text and weight is None:
            send_message(
                peer_id,
                "❌ Некорректный вес. Вес должен быть от 1 до 10000 грамм.\n\n"
                "Попробуйте ещё раз, например: банан 150г",
                get_main_keyboard()
            )
            return
        
        # ============================================
        # ШАГ 1: Поиск в локальной базе
        # ============================================
        products = search_products(clean_text, user_id, session, limit=5)
        
        if products:
            # Нашли в локальной базе — показываем результат
            user_states[user_id] = {'state': 'selecting', 'products': products, 'weight': weight, 'add_date': target_date}
            
            date_str = f" за {target_date.strftime('%d.%m.%Y')}" if target_date else ""
            msg = f"Найденные продукты{date_str}:\n\n"
            for i, p in enumerate(products, 1):
                msg += f"{i}. {p['name']} ({p['calories']} ккал/100г)\n"
            msg += f"\nВес: {weight}г" if weight else "\nВес не указан."
            
            send_message(peer_id, msg, get_product_selection_keyboard(products))
            return
        
        # ============================================
        # ШАГ 2: Локально не нашли — ищем в FatSecret API
        # ============================================
        from utils.logger import logger
        logger.info(f"🔍 Локальная база пуста для '{clean_text}', ищем в FatSecret...")
        
        from utils.fatsecret_api import search_fatsecret
        fs_products = search_fatsecret(clean_text, limit=5)
        
        if fs_products:
            logger.info(f"✅ FatSecret: найдено {len(fs_products)} продуктов")
            
            user_states[user_id] = {
                'state': 'selecting',
                'products': fs_products,
                'weight': weight,
                'add_date': target_date
            }
            
            date_str = f" за {target_date.strftime('%d.%m.%Y')}" if target_date else ""
            msg = f"🍎 В локальной базе не нашёл, но нашёл в FatSecret ({len(fs_products)}):{date_str}\n\n"
            for i, p in enumerate(fs_products, 1):
                msg += f"{i}. {p['name']} ({p['calories']} ккал/100г)\n"
            msg += f"\nВес: {weight}г" if weight else "\nВес не указан."
            
            send_message(peer_id, msg, get_product_selection_keyboard(fs_products))
            return
        
        # ============================================
        # ШАГ 3: Не нашли нигде — предлагаем добавить свой
        # ============================================
        logger.info(f"❌ FatSecret: ничего не найдено по запросу '{clean_text}'")
        
        send_message(peer_id, 
            f"Не нашел '{clean_text}' ни в базе, ни в FatSecret.\n\n"
            f"Хотите добавить свой продукт? Напишите 'да' или название другого продукта.", 
            get_main_keyboard())
        user_states[user_id] = {'state': 'ask_custom', 'query': clean_text, 'weight': weight, 'add_date': target_date}
        
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