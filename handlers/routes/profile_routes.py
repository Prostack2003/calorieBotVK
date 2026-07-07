from config import user_states
from database import SessionLocal, User
from utils.messenger import send_message
from keyboards.keyboards import (
    get_main_keyboard, get_cancel_keyboard,
    get_settings_keyboard_v2, get_confirm_reset_keyboard
)
from handlers.routes.utils import require_profile, get_goal_text, send_result
from handlers.stats import get_or_create_user
from handlers.onboarding import start_onboarding, handle_onboarding


def handle_start_button(user_id, peer_id):
    """Обработка кнопки 'Начать'"""
    user = get_or_create_user(user_id)
    if user['onboarded']:
        name = user['name']
        greeting = f"Привет, {name}!" if name else "Привет!"
        send_message(peer_id,
            f"{greeting} Я бот для подсчета КБЖУ.\n"
            "Напиши продукт и вес (банан 150г) или нажми кнопки.",
            get_main_keyboard())
    else:
        start_onboarding(user_id, peer_id)


def handle_start_text(user_id, peer_id):
    """Обработка текста /start"""
    user = get_or_create_user(user_id)
    if user['onboarded']:
        user_name = user['name'] if user['name'] else ""
        greeting = f"Привет, {user_name}!" if user_name else "Привет!"
        send_message(peer_id,
            f"{greeting} Я бот для подсчета КБЖУ.\n"
            "Напиши продукт и вес (банан 150г) или нажми кнопки.",
            get_main_keyboard())
    else:
        start_onboarding(user_id, peer_id)


def handle_profile_payload(user_id, peer_id, cmd, payload_data):
    """Обработка payload-команд профиля. Возвращает True если обработано."""

    if cmd == 'goals':
        if not require_profile(user_id, peer_id):
            return True
        user = get_or_create_user(user_id)
        goal_text = get_goal_text(user['goal'])
        send_message(peer_id,
            f"🎯 Ваша цель: {goal_text}\n"
            f"🔥 Калории: {round(user['daily_calories'])} ккал/день\n"
            f"Б: {round(user['daily_proteins'], 1)}г | "
            f"Ж: {round(user['daily_fats'], 1)}г | "
            f"У: {round(user['daily_carbs'], 1)}г",
            get_main_keyboard())
        return True

    if cmd == 'settings':
        if not require_profile(user_id, peer_id):
            return True
        user = get_or_create_user(user_id)
        gender_text = 'Мужской' if user['gender'] == 'male' else 'Женский'
        goal_text = get_goal_text(user['goal'])
        send_message(peer_id,
            f"⚙️ Ваши данные:\n"
            f"Имя: {user['name']}\nПол: {gender_text}\n"
            f"Возраст: {user['age']}\nРост: {user['height']} см\n"
            f"Вес: {user['weight']} кг\nЦель: {goal_text}",
            get_settings_keyboard_v2())
        return True

    if cmd == 'reset_profile':
        if not require_profile(user_id, peer_id):
            return True
        send_message(peer_id,
            "⚠️ Вы уверены, что хотите сбросить профиль?\n\n"
            "Все ваши данные (имя, возраст, рост, вес, цель) будут удалены.\n"
            "Дневник питания сохранится.",
            get_confirm_reset_keyboard())
        return True

    if cmd == 'confirm_reset_yes':
        session = SessionLocal()
        try:
            db_user = session.query(User).filter_by(vk_id=user_id).first()
            if db_user:
                db_user.onboarded = False
                session.commit()
                send_message(peer_id, "Профиль сброшен. Давайте настроим заново!", get_main_keyboard())
                start_onboarding(user_id, peer_id)
            else:
                send_message(peer_id, "У вас нет профиля.", get_main_keyboard())
        finally:
            session.close()
        return True

    if cmd == 'confirm_reset_no':
        send_message(peer_id, "Отменено. Возвращаемся в главное меню.", get_main_keyboard())
        return True

    if cmd == 'my_products':
        if not require_profile(user_id, peer_id):
            return True
        from handlers.food import get_user_products_list
        send_result(peer_id, get_user_products_list(user_id))
        return True

    if cmd == 'delete_my_product':
        if not require_profile(user_id, peer_id):
            return True
        from handlers.food import delete_user_product
        delete_user_product(user_id, peer_id, payload_data['product_id'])
        return True

    if cmd == 'confirm_delete_product_yes':
        if not require_profile(user_id, peer_id):
            return True
        from handlers.food import confirm_delete_user_product
        confirm_delete_user_product(user_id, peer_id, payload_data['product_id'])
        return True

    if cmd == 'start_onboarding':
        handle_onboarding(user_id, peer_id, 'disclaimer', None)
        return True

    if cmd in ('gender', 'activity', 'goal'):
        handle_onboarding(user_id, peer_id, cmd, payload_data.get('value'))
        return True

    return False


def handle_profile_text(user_id, peer_id, text):
    """Обработка текстовых состояний профиля. Возвращает True если обработано."""
    if user_id not in user_states:
        return False

    state = user_states[user_id]['state']

    # Онбординг
    if state in ('onboarding_name', 'onboarding_age', 'onboarding_height', 'onboarding_weight'):
        handle_onboarding(user_id, peer_id, None, text)
        return True

    # Подтверждение КБЖУ (текст вместо кнопки)
    if state == 'confirm_custom':
        send_message(peer_id,
            "Используйте кнопки выше:\n"
            "✅ Всё верно, сохранить\n"
            "✏️ Ввести заново\n"
            "❌ Отмена",
            get_cancel_keyboard())
        return True

    return False