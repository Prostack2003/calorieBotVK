import re
import json
from datetime import date, datetime, timedelta
from config import user_states
from database import SessionLocal, DailyLog, UserProduct, GlobalProduct, User
from utils.messenger import send_message, notify_admin
from utils.fuzzy_search import search_products, extract_weight_from_text
from keyboards.keyboards import (
    get_main_keyboard, get_cancel_keyboard, get_product_selection_keyboard
)

def handle_search(user_id, peer_id, text, target_date=None):
    session = SessionLocal()
    try:
        weight = extract_weight_from_text(text)
        clean_text = re.sub(r'\d+(?:\.\d+)?\s*(?:г|гр|грамм|граммов|gram)', '', text, flags=re.IGNORECASE).strip()
        clean_text = re.sub(r'[,\.\s]+', ' ', clean_text).strip()
        
        if not clean_text:
            send_message(peer_id, "Не удалось определить название продукта.", get_main_keyboard())
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
            f"📊 КБЖУ на 100г: {product.calories} ккал | Б:{product.proteins} Ж:{product.fats} У:{product.carbs}\n\n"
            "⚖️ Введите вес в граммах (например: 150):",
            get_cancel_keyboard()
        )
    finally:
        session.close()


def handle_weight(user_id, peer_id, text):
    if user_id not in user_states: return
    try:
        weight = float(text.strip())
        if weight <= 0: raise ValueError
        target_date = user_states[user_id].get('add_date')
        save_log(user_id, peer_id, user_states[user_id]['product'], weight, target_date)
    except ValueError:
        send_message(peer_id, "Введите число (например: 150)", get_cancel_keyboard())

def save_custom_product(user_id, peer_id, text):
    state = user_states[user_id]
    
    if state['state'] == 'custom_name':
        user_states[user_id]['custom_name'] = text
        user_states[user_id]['state'] = 'custom_kbzhu'
        send_message(peer_id, f"Принято: {text}.\nТеперь введите КБЖУ на 100г в формате: К Б Ж У\n(например: 120 10 5 20)", get_cancel_keyboard())
        
    elif state['state'] == 'custom_kbzhu':
        parts = text.strip().split()
        if len(parts) != 4:
            send_message(peer_id, "Неверный формат. Введите 4 числа через пробел: К Б Ж У", get_cancel_keyboard())
            return
        
        try:
            c, p, f, u = map(float, parts)
        except ValueError:
            send_message(peer_id, "Введите только числа.", get_cancel_keyboard())
            return
        
        session = SessionLocal()
        try:
            new_prod = UserProduct(user_id=user_id, name=state['custom_name'], calories=c, proteins=p, fats=f, carbs=u)
            session.add(new_prod)
            session.commit()
            
            target_date = state.get('add_date')
            date_str = f" за {target_date.strftime('%d.%m.%Y')}" if target_date else ""
            
            send_message(peer_id, f"✅ Продукт '{state['custom_name']}' сохранен!\n\nТеперь напишите его вес{date_str} (например: 150г)", get_cancel_keyboard())
            user_states[user_id] = {'state': 'weight', 'product': {'name': state['custom_name'], 'calories': c, 'proteins': p, 'fats': f, 'carbs': u}, 'add_date': target_date}
        except Exception as e:
            session.rollback()
            send_message(peer_id, "Ошибка сохранения.", get_main_keyboard())
        finally:
            session.close()


def save_log(user_id, peer_id, product, weight, target_date=None):
    """Сохранение записи в БД (с возможностью указать дату)"""
    if target_date is None:
        target_date = date.today()
    
    session = SessionLocal()
    try:
        m = weight / 100.0
        
        calories = round(product['calories'] * m, 1)
        proteins = round(product['proteins'] * m, 1)
        fats = round(product['fats'] * m, 1)
        carbs = round(product['carbs'] * m, 1)
        
        log = DailyLog(
            user_id=user_id, 
            date=target_date,  # Используем выбранную дату
            product_name=product['name'], 
            weight=weight,
            calories=calories, 
            proteins=proteins, 
            fats=fats, 
            carbs=carbs
        )
        session.add(log)
        session.commit()
        
        if user_id in user_states: 
            del user_states[user_id]
        
        user = session.query(User).filter_by(vk_id=user_id).first()
        user_name = user.name if user and user.name else f"Пользователь {user_id}"
        
        date_str = target_date.strftime('%d.%m.%Y')
        msg = (f"✅ Добавлено за {date_str}!\n"
               f"{product['name']} - {weight}г\n"
               f"Ккал: {calories} | Б:{proteins} Ж:{fats} У:{carbs}")
        
        send_message(peer_id, msg, get_main_keyboard())
        notify_admin(user_id, user_name, msg)
        
    except Exception as e:
        session.rollback()
        print(f"Ошибка БД: {e}")
        send_message(peer_id, "Ошибка сохранения.", get_main_keyboard())
    finally:
        session.close()

def delete_log(user_id, peer_id, log_id):
    session = SessionLocal()
    try:
        log = session.query(DailyLog).filter_by(id=log_id, user_id=user_id).first()
        if not log:
            send_message(peer_id, "Запись не найдена.", get_main_keyboard())
            return
        
        session.delete(log)
        session.commit()
        
        user = session.query(User).filter_by(vk_id=user_id).first()
        user_name = user.name if user and user.name else f"Пользователь {user_id}"
        
        send_message(peer_id, f"🗑 Удалено: {log.product_name} ({log.weight}г)", get_main_keyboard())
        notify_admin(user_id, user_name, f" Удалил: {log.product_name} ({log.weight}г)")
        
    except Exception as e:
        session.rollback()
        send_message(peer_id, "Ошибка удаления.", get_main_keyboard())
    finally:
        session.close()

def delete_log_by_id(user_id, peer_id, log_id):
    """Удаление записи по ID (для навигации по датам)"""
    session = SessionLocal()
    try:
        log = session.query(DailyLog).filter_by(id=log_id, user_id=user_id).first()
        if not log:
            send_message(peer_id, "Запись не найдена.", get_main_keyboard())
            return
        
        log_date = log.date
        session.delete(log)
        session.commit()
        
        user = session.query(User).filter_by(vk_id=user_id).first()
        user_name = user.name if user and user.name else f"Пользователь {user_id}"
        
        send_message(peer_id, f"🗑 Удалено: {log.product_name} ({log.weight}г)", get_main_keyboard())
        notify_admin(user_id, user_name, f"🗑 Удалил: {log.product_name} ({log.weight}г) за {log_date.strftime('%d.%m.%Y')}")
        
    except Exception as e:
        session.rollback()
        print(f"Ошибка удаления: {e}")
        send_message(peer_id, "Ошибка удаления.", get_main_keyboard())
    finally:
        session.close()

def get_products_list(user_id):
    session = SessionLocal()
    try:
        global_products = session.query(GlobalProduct).order_by(GlobalProduct.name).all()
        user_products = session.query(UserProduct).filter_by(user_id=user_id).order_by(UserProduct.name).all()
        
        msg = "📦 Доступные продукты:\n\n"
        
        if user_products:
            msg += " Ваши продукты:\n"
            for p in user_products:
                msg += f"• {p.name} ({p.calories} ккал/100г)\n"
            msg += "\n"
        
        if global_products:
            msg += "📚 База бота:\n"
            for p in global_products:
                msg += f"• {p.name} ({p.calories} ккал/100г)\n"
        
        msg += "\n💡 Напишите название продукта и вес:\n"
        msg += "Например: банан 150г"
        
        keyboard = json.dumps({
            "one_time": True,
            "buttons": [
                [{"action": {"type": "text", "label": "Понятно", "payload": "{\"cmd\":\"manual_input\"}"}, "color": "primary"}]
            ]
        }, ensure_ascii=False)
        
        return msg, keyboard
    finally:
        session.close()

def get_date_selection_keyboard():
    """Клавиатура выбора даты для добавления еды"""
    yesterday = date.today() - timedelta(days=1)
    
    keyboard = json.dumps({
        "one_time": True,
        "buttons": [
            [
                {"action": {"type": "text", "label": "✅ Сегодня", "payload": json.dumps({"cmd": "set_add_date", "date": date.today().strftime('%Y-%m-%d')})}, "color": "primary"},
                {"action": {"type": "text", "label": "◀️ Вчера", "payload": json.dumps({"cmd": "set_add_date", "date": yesterday.strftime('%Y-%m-%d')})}, "color": "secondary"}
            ],
            [
                {"action": {"type": "text", "label": "📅 Выбрать дату", "payload": "{\"cmd\":\"ask_date_input\"}"}, "color": "secondary"}
            ]
        ]
    }, ensure_ascii=False)
    
    return keyboard

def ask_add_date(user_id, peer_id):
    """Спросить дату для добавления еды"""
    user_states[user_id] = {'state': 'ask_add_date'}
    send_message(
        peer_id,
        "📅 За какую дату добавляем еду?\n\n"
        "Или напишите дату в формате ДД.ММ (например: 05.07)",
        get_date_selection_keyboard()
    )

def handle_date_input(user_id, peer_id, text):
    """Обработка ввода даты вручную"""
    try:
        # Пробуем разные форматы
        for fmt in ['%d.%m', '%d.%m.%Y', '%d/%m', '%d/%m/%Y']:
            try:
                parsed_date = datetime.strptime(text, fmt).date()
                # Если год не указан, используем текущий
                if parsed_date.year == 1900:
                    parsed_date = parsed_date.replace(year=date.today().year)
                
                # Проверяем, что дата не в будущем
                if parsed_date > date.today():
                    send_message(peer_id, " Нельзя добавить еду в будущее. Выберите дату сегодня или раньше.", get_main_keyboard())
                    return
                
                # Сохраняем дату в состоянии
                user_states[user_id] = {'state': 'adding_food', 'add_date': parsed_date}
                send_message(
                    peer_id,
                    f"✅ Будем добавлять за {parsed_date.strftime('%d.%m.%Y')}\n\n"
                    "Напишите название продукта и вес (например: банан 150г)",
                    get_main_keyboard()
                )
                return
            except ValueError:
                continue
        
        send_message(peer_id, "❌ Неверный формат. Используйте ДД.ММ (например: 05.07)", get_main_keyboard())
        
    except Exception as e:
        send_message(peer_id, "❌ Ошибка обработки даты.", get_main_keyboard())