from config import user_states
from utils.messenger import send_message
from keyboards import get_main_keyboard
from handlers.routes.admin_routes import handle_admin_text
from handlers.routes.stats_routes import handle_stats_payload, handle_stats_text
from handlers.routes.food_routes import handle_food_payload, handle_food_text
from handlers.routes.profile_routes import (
    handle_profile_payload, handle_profile_text,
    handle_start_button, handle_start_text
)
from handlers.routes.utils import require_profile


def route_payload(user_id, peer_id, payload_data):
    """Главный диспетчер payload-команд"""

    # Кнопка "Начать" (первый запуск)
    if payload_data.get('command') == 'start':
        handle_start_button(user_id, peer_id)
        return

    cmd = payload_data.get('cmd')
    if not cmd:
        return

    # Базовая навигация
    if cmd == 'cancel':
        if user_id in user_states:
            del user_states[user_id]
        send_message(peer_id, "Отменено.", get_main_keyboard())
        return

    if cmd == 'faq':
        from handlers.faq import get_faq_text
        send_message(peer_id, get_faq_text(), get_main_keyboard())
        return

    if cmd == 'main_menu':
        if user_id in user_states:
            del user_states[user_id]
        send_message(peer_id, "Главное меню:", get_main_keyboard())
        return

    # Диспетчеризация по доменам
    if handle_stats_payload(user_id, peer_id, cmd, payload_data):
        return
    if handle_food_payload(user_id, peer_id, cmd, payload_data):
        return
    if handle_profile_payload(user_id, peer_id, cmd, payload_data):
        return


def route_text(user_id, peer_id, text):
    """Главный диспетчер текстовых команд"""

    # Отмена
    if text.lower() in ('отмена', 'отменить', 'назад', 'cancel'):
        if user_id in user_states:
            del user_states[user_id]
        send_message(peer_id, "Отменено.", get_main_keyboard())
        return

    # Админские команды (проверяются первыми!)
    if handle_admin_text(user_id, peer_id, text):
        return

    # /start
    if text.lower() in ('/start', 'старт', 'начать'):
        handle_start_text(user_id, peer_id)
        return

    # Диспетчеризация по доменам
    if handle_profile_text(user_id, peer_id, text):
        return
    if handle_stats_text(user_id, peer_id, text):
        return
    if handle_food_text(user_id, peer_id, text):
        return

    # Поиск продукта (fallback)
    if require_profile(user_id, peer_id):
        if text:
            from handlers.food import handle_search
            handle_search(user_id, peer_id, text)