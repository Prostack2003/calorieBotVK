import re
from config import user_states
from database import SessionLocal
from utils.messenger import send_message
from utils.fuzzy_search import search_products, extract_weight_from_text
from keyboards.keyboards import get_main_keyboard, get_cancel_keyboard, get_product_selection_keyboard
from .log import save_log

def handle_search(user_id, peer_id, text, target_date=None):
    session = SessionLocal()
    try:
        weight = extract_weight_from_text(text)
        clean_text = re.sub(r'\d+(?:\.\d+)?\s*(?:г|гр|грамм|граммов|gram)', '', text, flags=re.IGNORECASE).strip()
        clean_text = re.sub(r'[,\.\s]+', ' ', clean_text).strip()
        
        if not clean_text:
            send_message(peer_id, "Не удалось определить название продукта.", get_main_keyboard())
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
        
        products = search_products(clean_text, user_id, session, limit=5)
        
        if not products:
            send_message(peer_id, 
                f"Не нашел '{clean_text}' в базе.\n\n"
                f"Хотите добавить свой продукт? Напишите 'да' или название другого продукта.", 
                get_main_keyboard())
            user_states[user_id] = {'state': 'ask_custom', 'query': clean_text, 'weight': weight, 'add_date': target_date}
            return
        
        user_states[user_id] = {'state': 'selecting', 'products': products, 'weight': weight, 'add_date': target_date}
        
        date_str = f" за {target_date.strftime('%d.%m.%Y')}" if target_date else ""
        msg = f"Найденные продукты{date_str}:\n\n"
        for i, p in enumerate(products, 1):
            msg += f"{i}. {p['name']} ({p['calories']} ккал/100г)\n"
        msg += f"\nВес: {weight}г" if weight else "\nВес не указан."
        
        send_message(peer_id, msg, get_product_selection_keyboard(products))
    finally:
        session.close()


def handle_selection(user_id, peer_id, product_name):
    if user_id not in user_states: return
    state = user_states[user_id]
    selected = next((p for p in state['products'] if p['name'] == product_name), None)
    
    if not selected:
        send_message(peer_id, "Продукт не найден.", get_main_keyboard())
        return
    
    target_date = state.get('add_date')
    
    if state['weight']:
        save_log(user_id, peer_id, selected, state['weight'], target_date)
    else:
        user_states[user_id] = {'state': 'weight', 'product': selected, 'add_date': target_date}
        date_str = f" за {target_date.strftime('%d.%m.%Y')}" if target_date else ""
        send_message(peer_id, f"Выбрано: {selected['name']}{date_str}\nВведите вес в граммах:", get_cancel_keyboard())

def handle_selection_from_list(user_id, peer_id, product_name):
    from database import UserProduct, GlobalProduct
    
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

def handle_weight(user_id, peer_id, text):
    if user_id not in user_states: return
    try:
        weight = float(text.strip())
        if weight <= 0:
            raise ValueError("weight_zero")
        if weight > 10000:
            send_message(
                peer_id, 
                "❌ Слишком большой вес! Максимум 10000г (10кг).\n"
                "Если вы действительно съели столько, разделите на несколько порций.",
                get_cancel_keyboard()
            )
            return
        target_date = user_states[user_id].get('add_date')
        save_log(user_id, peer_id, user_states[user_id]['product'], weight, target_date)
    except ValueError as e:
        if "weight_zero" in str(e):
            send_message(peer_id, "❌ Вес должен быть больше нуля. Введите число (например: 150)", get_cancel_keyboard())
        else:
            send_message(peer_id, "❌ Введите число (например: 150)", get_cancel_keyboard())
    if user_id not in user_states: return
    try:
        weight = float(text.strip())
        if weight <= 0:
            raise ValueError("Вес должен быть больше нуля")
        if weight > 10000:  # Максимум 10 кг
            send_message(
                peer_id, 
                "❌ Слишком большой вес! Максимум 10000г (10кг).\n"
                "Если вы действительно съели столько, разделите на несколько порций.",
                get_cancel_keyboard()
            )
            return
        target_date = user_states[user_id].get('add_date')
        save_log(user_id, peer_id, user_states[user_id]['product'], weight, target_date)
    except ValueError as e:
        if "больше нуля" in str(e):
            send_message(peer_id, "❌ Вес должен быть больше нуля. Введите число (например: 150)", get_cancel_keyboard())
        else:
            send_message(peer_id, "❌ Введите число (например: 150)", get_cancel_keyboard())