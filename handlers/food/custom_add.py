from config import user_states
from database import SessionLocal, UserProduct
from utils.messenger import send_message
from keyboards.keyboards import (
    get_main_keyboard,
    get_cancel_keyboard,
    get_confirm_kbju_keyboard
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

        # Сохраняем значения в состоянии и показываем подтверждение
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