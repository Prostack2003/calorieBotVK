from datetime import date
from config import user_states
from database import SessionLocal, DailyLog, User
from utils.messenger import send_message, notify_admin
from keyboards.keyboards import get_main_keyboard

def save_log(user_id, peer_id, product, weight, target_date=None):
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
            date=target_date,
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