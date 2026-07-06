import json
from config import user_states
from database import SessionLocal, UserProduct, DailyLog
from utils.messenger import send_message
from keyboards.keyboards import (
    get_main_keyboard, 
    get_cancel_keyboard, 
    get_confirm_kbju_keyboard,
    get_user_products_keyboard,
    get_confirm_delete_product_keyboard
)


def save_custom_product(user_id, peer_id, text):
    """Обработка ввода данных своего продукта"""
    state = user_states[user_id]
    
    if state['state'] == 'custom_name':
        user_states[user_id]['custom_name'] = text
        user_states[user_id]['state'] = 'custom_kbzhu'
        send_message(
            peer_id, 
            f"Принято: {text}.\n\n"
            "Теперь введите КБЖУ на 100г в формате: К Б Ж У\n"
            "(например: 120 10 5 20)",
            get_cancel_keyboard()
        )
        
    elif state['state'] == 'custom_kbzhu':
        parts = text.strip().split()
        if len(parts) != 4:
            send_message(
                peer_id, 
                "❌ Неверный формат. Введите 4 числа через пробел: К Б Ж У\n"
                "(например: 120 10 5 20)",
                get_cancel_keyboard()
            )
            return
        
        try:
            c, p, f, u = map(float, parts)
        except ValueError:
            send_message(peer_id, "❌ Введите только числа.", get_cancel_keyboard())
            return
        
        # Проверка на адекватность значений
        if c < 0 or p < 0 or f < 0 or u < 0:
            send_message(peer_id, "❌ Значения не могут быть отрицательными.", get_cancel_keyboard())
            return
        
        if c > 1000 or p > 100 or f > 100 or u > 100:
            send_message(
                peer_id, 
                "❌ Подозрительно большие значения. Проверьте, пожалуйста.\n"
                "Введите КБЖУ заново:",
                get_cancel_keyboard()
            )
            return
        
        # ИСПРАВЛЕНИЕ #4: Сохраняем значения в состоянии и показываем подтверждение
        user_states[user_id]['custom_c'] = c
        user_states[user_id]['custom_p'] = p
        user_states[user_id]['custom_f'] = f
        user_states[user_id]['custom_u'] = u
        user_states[user_id]['state'] = 'confirm_custom'
        
        msg = (
            f"📦 Проверьте данные перед сохранением:\n\n"
            f"🏷️ Название: {state['custom_name']}\n\n"
            f"📊 КБЖУ на 100г:\n"
            f"🔥 Калории: {c} ккал\n"
            f"🥩 Белки: {p}г\n"
            f"🥑 Жиры: {f}г\n"
            f"🍞 Углеводы: {u}г\n\n"
            f"💡 Проверьте на упаковке продукта или в интернете,\n"
            f"что значения соответствуют действительности."
        )
        
        send_message(peer_id, msg, get_confirm_kbju_keyboard())


def confirm_save_custom_product(user_id, peer_id):
    """Подтверждённое сохранение своего продукта"""
    state = user_states[user_id]
    
    session = SessionLocal()
    try:
        new_prod = UserProduct(
            user_id=user_id,
            name=state['custom_name'],
            calories=state['custom_c'],
            proteins=state['custom_p'],
            fats=state['custom_f'],
            carbs=state['custom_u']
        )
        session.add(new_prod)
        session.commit()
        
        target_date = state.get('add_date')
        date_str = f" за {target_date.strftime('%d.%m.%Y')}" if target_date else ""
        
        product_data = {
            'name': state['custom_name'],
            'calories': state['custom_c'],
            'proteins': state['custom_p'],
            'fats': state['custom_f'],
            'carbs': state['custom_u']
        }
        
        send_message(
            peer_id,
            f"✅ Продукт '{state['custom_name']}' сохранён!\n\n"
            f"Теперь напишите его вес{date_str} (например: 150г)",
            get_cancel_keyboard()
        )
        
        # Переходим в состояние ввода веса
        user_states[user_id] = {
            'state': 'weight',
            'product': product_data,
            'add_date': target_date
        }
    except Exception as e:
        session.rollback()
        send_message(peer_id, "❌ Ошибка сохранения.", get_main_keyboard())
    finally:
        session.close()


def edit_custom_kbju(user_id, peer_id):
    """Запрос повторного ввода КБЖУ"""
    user_states[user_id]['state'] = 'custom_kbzhu'
    send_message(
        peer_id,
        f"✏️ Введите КБЖУ заново для продукта \"{user_states[user_id]['custom_name']}\":\n\n"
        "Формат: К Б Ж У (например: 120 10 5 20)",
        get_cancel_keyboard()
    )


def cancel_custom_product(user_id, peer_id):
    """Отмена добавления своего продукта"""
    if user_id in user_states:
        del user_states[user_id]
    send_message(peer_id, "❌ Добавление продукта отменено.", get_main_keyboard())


def get_user_products_list(user_id):
    """Получить список продуктов пользователя с клавиатурой"""
    session = SessionLocal()
    try:
        products = session.query(UserProduct).filter_by(user_id=user_id).order_by(UserProduct.name).all()
        
        if not products:
            msg = "📦 У вас пока нет своих продуктов.\n\nДобавить можно через поиск продукта — если бот не найдёт его в базе, предложит добавить свой."
            keyboard = json.dumps({
                "one_time": True,
                "buttons": [[{
                    "action": {"type": "text", "label": "◀️ Назад к настройкам", "payload": "{\"cmd\":\"settings\"}"},
                    "color": "secondary"
                }]]
            }, ensure_ascii=False)
            return msg, keyboard
        
        msg = f"📦 Ваши продукты ({len(products)} шт.):\n\n"
        msg += "Нажмите на продукт, чтобы удалить его."
        
        keyboard = get_user_products_keyboard(products)
        
        return msg, keyboard
    finally:
        session.close()


def delete_user_product(user_id, peer_id, product_id):
    """Показать подтверждение удаления продукта"""
    session = SessionLocal()
    try:
        product = session.query(UserProduct).filter_by(id=product_id, user_id=user_id).first()
        
        if not product:
            send_message(peer_id, "❌ Продукт не найден.", get_main_keyboard())
            return
        
        # Считаем, сколько раз продукт использовался в дневнике
        usage_count = session.query(DailyLog).filter_by(
            user_id=user_id,
            product_name=product.name
        ).count()
        
        keyboard = get_confirm_delete_product_keyboard(product.id, product.name)
        
        msg = f"⚠️ Удалить продукт \"{product.name}\"?\n\n"
        msg += f"📊 КБЖУ на 100г:\n"
        msg += f"🔥 {product.calories} ккал | Б:{product.proteins} Ж:{product.fats} У:{product.carbs}\n\n"
        
        if usage_count > 0:
            msg += f"ℹ️ Этот продукт использовался в дневнике {usage_count} раз(а).\n"
            msg += "Записи в дневнике сохранятся — это ваша история питания.\n\n"
        else:
            msg += "Этот продукт ещё не использовался в дневнике.\n\n"
        
        msg += "Удалить только из списка продуктов?"
        
        send_message(peer_id, msg, keyboard)
    finally:
        session.close()


def confirm_delete_user_product(user_id, peer_id, product_id):
    """Подтверждённое удаление продукта"""
    session = SessionLocal()
    try:
        product = session.query(UserProduct).filter_by(id=product_id, user_id=user_id).first()
        
        if not product:
            send_message(peer_id, "❌ Продукт не найден.", get_main_keyboard())
            return
        
        product_name = product.name
        session.delete(product)
        session.commit()
        
        send_message(peer_id, f"✅ Продукт \"{product_name}\" удалён.", get_main_keyboard())
    except Exception as e:
        session.rollback()
        send_message(peer_id, "❌ Ошибка удаления.", get_main_keyboard())
    finally:
        session.close()