from datetime import datetime, date
from config import user_states
from database import SessionLocal, User
from utils.messenger import send_message
from keyboards.keyboards import (
    get_main_keyboard, get_cancel_keyboard,
    get_settings_keyboard_v2, get_confirm_reset_keyboard
)
from handlers.export import generate_user_report_pdf
from handlers.onboarding import start_onboarding, handle_onboarding
from handlers.food import (
    handle_search, handle_selection, handle_selection_from_list,
    handle_weight, save_custom_product, delete_log_by_id,
    ask_add_date, handle_date_input,
    get_user_products_list, delete_user_product, confirm_delete_user_product,
    confirm_save_custom_product, edit_custom_kbju, cancel_custom_product
)
from handlers.stats import get_daily_stats, get_or_create_user, get_daily_logs_for_deletion
from handlers.faq import get_faq_text
from handlers.admin import (
    is_admin, get_all_users_stats, get_user_report,
    get_users_list, get_weekly_stats, get_admin_day_detail
)


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


def route_payload(user_id, peer_id, payload_data):
    """Обработка нажатий кнопок (payload)"""

    # Кнопка "Начать" (первый запуск)
    if payload_data.get('command') == 'start':
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
        return

    cmd = payload_data.get('cmd')

    # --- Статистика ---
    if cmd == 'stats':
        if not require_profile(user_id, peer_id):
            return
        send_result(peer_id, get_daily_stats(user_id))
        return

    if cmd == 'stats_date':
        if not require_profile(user_id, peer_id):
            return
        try:
            target_date = datetime.strptime(payload_data['date'], '%Y-%m-%d').date()
            send_result(peer_id, get_daily_stats(user_id, target_date))
        except ValueError:
            send_message(peer_id, "❌ Неверный формат даты.", get_main_keyboard())
        return

    if cmd == 'show_delete':
        if not require_profile(user_id, peer_id):
            return
        try:
            target_date = datetime.strptime(payload_data['date'], '%Y-%m-%d').date()
            send_result(peer_id, get_daily_logs_for_deletion(user_id, target_date))
        except ValueError:
            send_message(peer_id, "❌ Неверный формат даты.", get_main_keyboard())
        return

        # --- Экспорт PDF ---
    if cmd == 'export_pdf':
        if not require_profile(user_id, peer_id):
            return
        try:
            target_date = datetime.strptime(payload_data['date'], '%Y-%m-%d').date()
            filepath = generate_user_report_pdf(user_id, target_date, target_date)
            
            if filepath:
                # Отправляем документ через ВК API
                from config import vk
                from utils.messenger import send_document
                
                send_document(peer_id, filepath, "📄 Ваш отчёт по питанию")
                send_message(peer_id, "✅ PDF отправлен!", get_main_keyboard())
            else:
                send_message(peer_id, "❌ Не удалось создать отчёт. Возможно, нет данных за этот день.", get_main_keyboard())
        except Exception as e:
            from utils.logger import logger
            logger.error(f"Ошибка экспорта PDF: {e}", exc_info=True)
            send_message(peer_id, f"❌ Ошибка создания отчёта: {e}", get_main_keyboard())
        return

    # --- Удаление записей ---
    if cmd == 'delete_by_id':
        delete_log_by_id(user_id, peer_id, payload_data['log_id'])
        return

    # --- Добавление еды ---
    if cmd == 'add':
        if not require_profile(user_id, peer_id):
            return
        ask_add_date(user_id, peer_id)
        return

    if cmd == 'set_add_date':
        if not require_profile(user_id, peer_id):
            return
        try:
            target_date = datetime.strptime(payload_data['date'], '%Y-%m-%d').date()
            user_states[user_id] = {'state': 'adding_food', 'add_date': target_date}
            send_message(peer_id,
                f"✅ Будем добавлять за {target_date.strftime('%d.%m.%Y')}\n\n"
                "Напишите название продукта и вес (например: банан 150г)",
                get_main_keyboard())
        except ValueError:
            send_message(peer_id, "❌ Неверный формат даты.", get_main_keyboard())
        return

    if cmd == 'ask_date_input':
        if not require_profile(user_id, peer_id):
            return
        user_states[user_id] = {'state': 'input_date'}
        send_message(peer_id, "Введите дату в формате ДД.ММ или ДД.ММ.ГГГГ (например: 05.07 или 05.07.2026):", get_cancel_keyboard())
        return

    if cmd == 'select':
        handle_selection(user_id, peer_id, payload_data['product'])
        return

    if cmd == 'select_from_list':
        handle_selection_from_list(user_id, peer_id, payload_data['product_name'])
        return

    if cmd == 'manual_input':
        if not require_profile(user_id, peer_id):
            return
        send_message(peer_id, "Напишите название продукта и вес (например: банан 150г)", get_main_keyboard())
        return

    # --- Админские команды ---
    if cmd == 'week':
        send_result(peer_id, get_weekly_stats())
        return

    if cmd == 'admin_day_detail':
        send_result(peer_id, get_admin_day_detail(payload_data['user_id'], payload_data['date']))
        return

    # --- Навигация ---
    if cmd == 'cancel':
        if user_id in user_states:
            del user_states[user_id]
        send_message(peer_id, "Отменено.", get_main_keyboard())
        return

    if cmd == 'faq':
        send_message(peer_id, get_faq_text(), get_main_keyboard())
        return

    if cmd == 'main_menu':
        if user_id in user_states:
            del user_states[user_id]
        send_message(peer_id, "Главное меню:", get_main_keyboard())
        return

    if cmd == 'goals':
        if not require_profile(user_id, peer_id):
            return
        user = get_or_create_user(user_id)
        goal_text = get_goal_text(user['goal'])
        send_message(peer_id,
            f"🎯 Ваша цель: {goal_text}\n"
            f"🔥 Калории: {round(user['daily_calories'])} ккал/день\n"
            f"Б: {round(user['daily_proteins'], 1)}г | "
            f"Ж: {round(user['daily_fats'], 1)}г | "
            f"У: {round(user['daily_carbs'], 1)}г",
            get_main_keyboard())
        return

    # --- Настройки и сброс профиля ---
    if cmd == 'settings':
        if not require_profile(user_id, peer_id):
            return
        user = get_or_create_user(user_id)
        gender_text = 'Мужской' if user['gender'] == 'male' else 'Женский'
        goal_text = get_goal_text(user['goal'])
        send_message(peer_id,
            f"⚙️ Ваши данные:\n"
            f"Имя: {user['name']}\nПол: {gender_text}\n"
            f"Возраст: {user['age']}\nРост: {user['height']} см\n"
            f"Вес: {user['weight']} кг\nЦель: {goal_text}",
            get_settings_keyboard_v2())
        return

    if cmd == 'reset_profile':
        if not require_profile(user_id, peer_id):
            return
        send_message(peer_id,
            "⚠️ Вы уверены, что хотите сбросить профиль?\n\n"
            "Все ваши данные (имя, возраст, рост, вес, цель) будут удалены.\n"
            "Дневник питания сохранится.",
            get_confirm_reset_keyboard())
        return

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
        return

    if cmd == 'confirm_reset_no':
        send_message(peer_id, "Отменено. Возвращаемся в главное меню.", get_main_keyboard())
        return

    # --- Мои продукты ---
    if cmd == 'my_products':
        if not require_profile(user_id, peer_id):
            return
        send_result(peer_id, get_user_products_list(user_id))
        return

    if cmd == 'delete_my_product':
        if not require_profile(user_id, peer_id):
            return
        delete_user_product(user_id, peer_id, payload_data['product_id'])
        return

    if cmd == 'confirm_delete_product_yes':
        if not require_profile(user_id, peer_id):
            return
        confirm_delete_user_product(user_id, peer_id, payload_data['product_id'])
        return

    # --- Подтверждение КБЖУ своего продукта ---
    if cmd == 'confirm_custom_yes':
        confirm_save_custom_product(user_id, peer_id)
        return

    if cmd == 'confirm_custom_edit':
        edit_custom_kbju(user_id, peer_id)
        return

    if cmd == 'confirm_custom_cancel':
        cancel_custom_product(user_id, peer_id)
        return

    # --- Дисклеймер ---
    if cmd == 'start_onboarding':
        handle_onboarding(user_id, peer_id, 'disclaimer', None)
        return

    # --- Онбординг ---
    if cmd in ('gender', 'activity', 'goal'):
        handle_onboarding(user_id, peer_id, cmd, payload_data.get('value'))
        return


def route_text(user_id, peer_id, text):
    """Обработка текстовых команд"""

    # Отмена
    if text.lower() in ('отмена', 'отменить', 'назад', 'cancel'):
        if user_id in user_states:
            del user_states[user_id]
        send_message(peer_id, "Отменено.", get_main_keyboard())
        return

    # Админские команды
    if is_admin(user_id) and route_admin_commands(user_id, peer_id, text):
        return

    # /start
    if text.lower() in ('/start', 'старт', 'начать'):
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
        return

    # Состояния пользователя
    if user_id in user_states:
        state = user_states[user_id]['state']

        # Онбординг
        if state in ('onboarding_name', 'onboarding_age', 'onboarding_height', 'onboarding_weight'):
            handle_onboarding(user_id, peer_id, None, text)
            return

        # Подтверждение КБЖУ
        if state == 'confirm_custom':
            send_message(peer_id,
                "Используйте кнопки выше:\n"
                "✅ Всё верно, сохранить\n"
                "✏️ Ввести заново\n"
                "❌ Отмена",
                get_cancel_keyboard())
            return

    # Для остальных действий нужен профиль
    if not require_profile(user_id, peer_id):
        return

    # Состояния пользователя (остальные)
    if route_user_states(user_id, peer_id, text):
        return

    # Поиск продукта
    if text:
        handle_search(user_id, peer_id, text)


def route_admin_commands(user_id, peer_id, text):
    """Обработка админских команд. Возвращает True, если команда обработана."""
    if text.lower() == '/stats':
        send_result(peer_id, get_all_users_stats())
        return True

    if text.lower() == '/week':
        send_result(peer_id, get_weekly_stats())
        return True

    if text.lower() == '/users':
        send_message(peer_id, get_users_list(), get_main_keyboard())
        return True

    if text.lower().startswith('/report'):
        parts = text.split()
        if len(parts) < 2:
            send_message(peer_id, "Используйте: /report <ID>\nНапример: /report 734594067", get_main_keyboard())
        else:
            try:
                send_message(peer_id, get_user_report(int(parts[1])), get_main_keyboard())
            except ValueError:
                send_message(peer_id, "❌ ID должен быть числом.", get_main_keyboard())
        return True

    if text.lower() == '/admin':
        send_message(peer_id,
            "🔐 Админ-панель:\n\n"
            "/stats - Статистика за сегодня\n"
            "/week - Отчет за последние 7 дней\n"
            "/users - Список всех пользователей\n"
            "/report <ID> - Детальный отчёт\n"
            "/admin - Эта справка",
            get_main_keyboard())
        return True

    return False


def route_user_states(user_id, peer_id, text):
    """Обработка состояний пользователя. Возвращает True, если состояние обработано."""
    if user_id not in user_states:
        return False

    state = user_states[user_id]['state']

    if state == 'input_date':
        handle_date_input(user_id, peer_id, text)
        return True

    if state == 'weight':
        handle_weight(user_id, peer_id, text)
        return True

    if state in ('custom_name', 'custom_kbzhu'):
        save_custom_product(user_id, peer_id, text)
        return True

    if state == 'ask_custom':
        if text.lower() == 'да':
            user_states[user_id]['state'] = 'custom_name'
            send_message(peer_id, "Как называется продукт?", get_cancel_keyboard())
        else:
            handle_search(user_id, peer_id, text)
        return True

    if state == 'selecting':
        if text.isdigit():
            n = int(text)
            prods = user_states[user_id]['products']
            if 1 <= n <= len(prods):
                handle_selection(user_id, peer_id, prods[n-1]['name'])
        else:
            handle_selection(user_id, peer_id, text)
        return True

    if state == 'adding_food':
        handle_search(user_id, peer_id, text, user_states[user_id].get('add_date'))
        return True

    return False


def send_result(peer_id, result):
    """Универсальная отправка результата (строка или кортеж)"""
    if isinstance(result, tuple):
        msg, keyboard = result
        send_message(peer_id, msg, keyboard if keyboard else get_main_keyboard())
    else:
        send_message(peer_id, result, get_main_keyboard())