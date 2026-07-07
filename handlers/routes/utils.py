from datetime import datetime, date
from config import user_states
from utils.messenger import send_message
from keyboards.keyboards import get_main_keyboard, get_cancel_keyboard
from handlers.stats import get_or_create_user
from handlers.onboarding import start_onboarding


def require_profile(user_id, peer_id):
    """Проверяет, прошёл ли пользователь онбординг."""
    user = get_or_create_user(user_id)
    if not user['onboarded']:
        send_message(
            peer_id,
            "⚠️ Сначала нужно настроить профиль!\n\n"
            "Давайте рассчитаем вашу суточную норму КБЖУ — это займёт 1 минуту.",
            get_cancel_keyboard()
        )
        start_onboarding(user_id, peer_id)
        return False
    return True


def get_goal_text(goal_key):
    """Возвращает название цели на русском"""
    return {
        'lose': 'Похудение',
        'maintain': 'Поддержание',
        'gain': 'Набор массы'
    }.get(goal_key, goal_key)


def send_result(peer_id, result):
    """Универсальная отправка результата (строка или кортеж)"""
    if isinstance(result, tuple):
        msg, keyboard = result
        send_message(peer_id, msg, keyboard if keyboard else get_main_keyboard())
    else:
        send_message(peer_id, result, get_main_keyboard())


def parse_date(date_str):
    """Парсинг даты из строки ДД.ММ или ДД.ММ.ГГГГ"""
    for fmt in ['%d.%m.%Y', '%d.%m']:
        try:
            d = datetime.strptime(date_str, fmt).date()
            if d.year == 1900:
                d = d.replace(year=date.today().year)
            return d
        except ValueError:
            continue
    return None