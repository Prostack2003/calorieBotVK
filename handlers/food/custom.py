import json
from config import user_states
from database import SessionLocal, UserProduct
from utils.messenger import send_message
from keyboards.keyboards import get_main_keyboard, get_cancel_keyboard

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
        
        # Преобразуем в список для клавиатуры
        msg = f"📦 Ваши продукты ({len(products)} шт.):\n\n"
        msg += "Нажмите на продукт, чтобы удалить его."
        
        from keyboards.keyboards import get_user_products_keyboard
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
        
        from keyboards.keyboards import get_confirm_delete_product_keyboard
        keyboard = get_confirm_delete_product_keyboard(product.id, product.name)
        
        send_message(
            peer_id,
            f"⚠️ Удалить продукт \"{product.name}\"?\n\n"
            f"📊 КБЖУ на 100г:\n"
            f"🔥 {product.calories} ккал | Б:{product.proteins} Ж:{product.fats} У:{product.carbs}\n\n"
            "Это действие нельзя отменить.",
            keyboard
        )
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