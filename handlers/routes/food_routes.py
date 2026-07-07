from datetime import datetime
from config import user_states
from utils.messenger import send_message
from keyboards.keyboards import get_main_keyboard, get_cancel_keyboard
from handlers.routes.utils import require_profile


def handle_food_payload(user_id, peer_id, cmd, payload_data):
    """Обработка payload-команд еды. Возвращает True если обработано."""

    if cmd == 'add':
        if not require_profile(user_id, peer_id):
            return True
        from handlers.food import ask_add_date
        ask_add_date(user_id, peer_id)
        return True

    if cmd == 'set_add_date':
        if not require_profile(user_id, peer_id):
            return True
        try:
            target_date = datetime.strptime(payload_data['date'], '%Y-%m-%d').date()
            user_states[user_id] = {'state': 'adding_food', 'add_date': target_date}
            send_message(
                peer_id,
                f"✅ Будем добавлять за {target_date.strftime('%d.%m.%Y')}\n\n"
                "Напишите название продукта и вес (например: банан 150г)",
                get_main_keyboard()
            )
        except ValueError:
            send_message(peer_id, "❌ Неверный формат даты.", get_main_keyboard())
        return True

    if cmd == 'ask_date_input':
        if not require_profile(user_id, peer_id):
            return True
        user_states[user_id] = {'state': 'input_date'}
        send_message(peer_id, "Введите дату в формате ДД.ММ или ДД.ММ.ГГГГ (например: 05.07 или 05.07.2026):", get_cancel_keyboard())
        return True

    if cmd == 'select':
        from handlers.food import handle_selection
        handle_selection(user_id, peer_id, payload_data['product'])
        return True

    if cmd == 'select_from_list':
        from handlers.food import handle_selection_from_list
        handle_selection_from_list(user_id, peer_id, payload_data['product_name'])
        return True

    if cmd == 'manual_input':
        if not require_profile(user_id, peer_id):
            return True
        send_message(peer_id, "Напишите название продукта и вес (например: банан 150г)", get_main_keyboard())
        return True

    if cmd == 'confirm_custom_yes':
        from handlers.food import confirm_save_custom_product
        confirm_save_custom_product(user_id, peer_id)
        return True

    if cmd == 'confirm_custom_edit':
        from handlers.food import edit_custom_kbju
        edit_custom_kbju(user_id, peer_id)
        return True

    if cmd == 'confirm_custom_cancel':
        from handlers.food import cancel_custom_product
        cancel_custom_product(user_id, peer_id)
        return True

    return False


def handle_food_text(user_id, peer_id, text):
    """Обработка текстовых состояний еды. Возвращает True если обработано."""
    if user_id not in user_states:
        return False

    state = user_states[user_id]['state']

    if state == 'input_date':
        from handlers.food import handle_date_input
        handle_date_input(user_id, peer_id, text)
        return True

    if state == 'weight':
        from handlers.food import handle_weight
        handle_weight(user_id, peer_id, text)
        return True

    if state in ('custom_name', 'custom_kbzhu'):
        from handlers.food import save_custom_product
        save_custom_product(user_id, peer_id, text)
        return True

    if state == 'ask_custom':
        if text.lower() == 'да':
            user_states[user_id]['state'] = 'custom_name'
            send_message(peer_id, "Как называется продукт?", get_cancel_keyboard())
        else:
            from handlers.food import handle_search
            handle_search(user_id, peer_id, text)
        return True

    if state == 'selecting':
        from handlers.food import handle_selection
        if text.isdigit():
            n = int(text)
            prods = user_states[user_id]['products']
            if 1 <= n <= len(prods):
                handle_selection(user_id, peer_id, prods[n-1]['name'])
        else:
            handle_selection(user_id, peer_id, text)
        return True

    if state == 'adding_food':
        from handlers.food import handle_search
        handle_search(user_id, peer_id, text, user_states[user_id].get('add_date'))
        return True

    return False