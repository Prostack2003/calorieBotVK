from config import user_states, vk
from database import SessionLocal, User
from utils.messenger import send_message
from utils.calculator import calculate_norm
from keyboards import (
    get_cancel_keyboard, get_gender_keyboard,
    get_activity_keyboard, get_goal_keyboard, get_main_keyboard
)


def get_goal_text(goal_key):
    """Возвращает название цели на русском"""
    return {
        'lose': 'Похудение',
        'maintain': 'Поддержание',
        'gain': 'Набор массы'
    }.get(goal_key, goal_key)


def start_onboarding(user_id, peer_id):
    user_states[user_id] = {'state': 'onboarding_name'}
    send_message(peer_id, 
        "🎯 Давайте познакомимся!\n\n"
        "Как вас зовут?",
        get_cancel_keyboard())


def handle_onboarding(user_id, peer_id, cmd, value):
    if user_id not in user_states:
        return
    
    state = user_states[user_id]['state']
    
    if state == 'onboarding_name':
        user_states[user_id]['name'] = value.strip()
        user_states[user_id]['state'] = 'onboarding_gender'
        send_message(peer_id, f"Приятно познакомиться, {value}! Укажите ваш пол:", get_gender_keyboard())
        
    elif cmd == 'gender' and state == 'onboarding_gender':
        user_states[user_id]['gender'] = value
        user_states[user_id]['state'] = 'onboarding_age'
        send_message(peer_id, "Введите ваш возраст (лет):", get_cancel_keyboard())
        
    elif state == 'onboarding_age':
        try:
            age = int(value)
            # ИСПРАВЛЕНИЕ #12: Минимальный возраст — 18 лет
            if age < 18 or age > 100:
                raise ValueError
            user_states[user_id]['age'] = age
            user_states[user_id]['state'] = 'onboarding_height'
            send_message(peer_id, "Введите ваш рост (см):", get_cancel_keyboard())
        except ValueError:
            send_message(peer_id, "Введите число от 18 до 100:", get_cancel_keyboard())
            
    elif state == 'onboarding_height':
        try:
            height = float(value)
            if height < 100 or height > 250:
                raise ValueError
            user_states[user_id]['height'] = height
            user_states[user_id]['state'] = 'onboarding_weight'
            send_message(peer_id, "Введите ваш вес (кг):", get_cancel_keyboard())
        except ValueError:
            send_message(peer_id, "Введите число от 100 до 250:", get_cancel_keyboard())
            
    elif state == 'onboarding_weight':
        try:
            weight = float(value)
            if weight < 30 or weight > 300:
                raise ValueError
            user_states[user_id]['weight'] = weight
            user_states[user_id]['state'] = 'onboarding_activity'
            send_message(peer_id, "Выберите уровень активности:", get_activity_keyboard())
        except ValueError:
            send_message(peer_id, "Введите число от 30 до 300:", get_cancel_keyboard())
            
    elif cmd == 'activity' and state == 'onboarding_activity':
        user_states[user_id]['activity'] = float(value)
        user_states[user_id]['state'] = 'onboarding_goal'
        send_message(peer_id, "Выберите цель:", get_goal_keyboard())
        
    elif cmd == 'goal' and state == 'onboarding_goal':
        user_states[user_id]['goal'] = value
        
        norm = calculate_norm(
            user_states[user_id]['gender'],
            user_states[user_id]['age'],
            user_states[user_id]['height'],
            user_states[user_id]['weight'],
            user_states[user_id]['activity'],
            user_states[user_id]['goal']
        )
        
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(vk_id=user_id).first()
            if not user:
                user = User(vk_id=user_id)
                session.add(user)
            
            user.name = user_states[user_id]['name']
            user.gender = user_states[user_id]['gender']
            user.age = user_states[user_id]['age']
            user.height = user_states[user_id]['height']
            user.weight = user_states[user_id]['weight']
            user.activity = user_states[user_id]['activity']
            user.goal = user_states[user_id]['goal']
            user.daily_calories = norm['calories']
            user.daily_proteins = norm['proteins']
            user.daily_fats = norm['fats']
            user.daily_carbs = norm['carbs']
            user.onboarded = True
            
            session.commit()
            
            # ИСПРАВЛЕНИЕ #6: Перевод цели на русский
            goal_text = get_goal_text(user_states[user_id]['goal'])
            
            msg = (f"✅ Настройка завершена!\n\n"
                   f"🎯 Ваша суточная норма:\n"
                   f"🔥 Калории: {norm['calories']} ккал\n"
                   f"🥩 Белки: {norm['proteins']}г\n"
                   f"🥑 Жиры: {norm['fats']}г\n"
                   f"🍞 Углеводы: {norm['carbs']}г\n\n"
                   f"Цель: {goal_text}\n\n"
                   f"Теперь можете добавлять еду!")
            
            send_message(peer_id, msg, get_main_keyboard())
            del user_states[user_id]
            
        except Exception as e:
            session.rollback()
            send_message(peer_id, "Ошибка сохранения профиля.", get_main_keyboard())
        finally:
            session.close()