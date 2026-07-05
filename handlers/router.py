from datetime import datetime
from config import user_states
from database import SessionLocal, User
from utils.messenger import send_message
from keyboards.keyboards import get_main_keyboard, get_cancel_keyboard
from handlers.onboarding import start_onboarding, handle_onboarding
from handlers.food import (
    handle_search, handle_selection, handle_selection_from_list,
    handle_weight, save_custom_product, delete_log_by_id,
    ask_add_date, handle_date_input
)
from handlers.stats import get_daily_stats, get_or_create_user, get_daily_logs_for_deletion
from handlers.faq import get_faq_text
from handlers.admin import (
    is_admin, get_all_users_stats, get_user_report, 
    get_users_list, get_weekly_stats, get_admin_day_detail
)

def route_payload(user_id, peer_id, payload_data):
    """Обработка нажатий кнопок (payload)"""
    cmd = payload_data.get('cmd')
    
    # --- Команды статистики ---
    if cmd == 'stats':
        result = get_daily_stats(user_id)
        send_result(peer_id, result)
        return
    
    if cmd == 'stats_date':
        try:
            target_date = datetime.strptime(payload_data['date'], '%Y-%m-%d').date()
            result = get_daily_stats(user_id, target_date)
            send_result(peer_id, result)
        except ValueError:
            send_message(peer_id, "❌ Неверный формат даты.", get_main_keyboard())
        return
    
    if cmd == 'show_delete':
        try:
            target_date = datetime.strptime(payload_data['date'], '%Y-%m-%d').date()
            result = get_daily_logs_for_deletion(user_id, target_date)
            send_result(peer_id, result)
        except ValueError:
            send_message(peer_id, "❌ Неверный формат даты.", get_main_keyboard())
        return
    
    # --- Команды удаления ---
    if cmd == 'delete_by_id':
        delete_log_by_id(user_id, peer_id, payload_data['log_id'])
        return
    
    # --- Команды добавления еды ---
    if cmd == 'add':
        ask_add_date(user_id, peer_id)
        return
    
    if cmd == 'set_add_date':
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
        return
    
    if cmd == 'ask_date_input':
        user_states[user_id] = {'state': 'input_date'}
        send_message(peer_id, "Введите дату в формате ДД.ММ (например: 05.07):", get_cancel_keyboard())
        return
    
    if cmd == 'select':
        handle_selection(user_id, peer_id, payload_data['product'])
        return
    
    if cmd == 'select_from_list':
        handle_selection_from_list(user_id, peer_id, payload_data['product_name'])
        return
    
    if cmd == 'manual_input':
        send_message(peer_id, "Напишите название продукта и вес (например: банан 150г)", get_main_keyboard())
        return
    
    # --- Админские команды ---
    if cmd == 'week':
        result = get_weekly_stats()
        send_result(peer_id, result)
        return
    
    if cmd == 'admin_day_detail':
        result = get_admin_day_detail(payload_data['user_id'], payload_data['date'])
        send_result(peer_id, result)
        return
    
    # --- Прочие команды ---
    if cmd == 'cancel':
        if user_id in user_states:
            del user_states[user_id]
        send_message(peer_id, "Отменено.", get_main_keyboard())
        return
    
    if cmd == 'faq':
        send_message(peer_id, get_faq_text(), get_main_keyboard())
        return
    
    if cmd == 'main_menu':
        send_message(peer_id, "Главное меню:", get_main_keyboard())
        return
    
    if cmd == 'goals':
        user = get_or_create_user(user_id)
        if user['onboarded']:
            send_message(peer_id, 
                f"🎯 Ваша цель: {round(user['daily_calories'])} ккал/день\n"
                f"Б: {round(user['daily_proteins'], 1)}г | Ж: {round(user['daily_fats'], 1)}г | У: {round(user['daily_carbs'], 1)}г",
                get_main_keyboard())
        else:
            start_onboarding(user_id, peer_id)
        return
    
    if cmd == 'settings':
        user = get_or_create_user(user_id)
        if user['onboarded']:
            gender_text = 'Мужской' if user['gender'] == 'male' else 'Женский'
            send_message(peer_id, 
                f"⚙️ Ваши данные:\n"
                f"Имя: {user['name']}\nПол: {gender_text}\n"
                f"Возраст: {user['age']}\nРост: {user['height']} см\n"
                f"Вес: {user['weight']} кг\nЦель: {user['goal']}\n\n"
                f"Чтобы изменить, напишите 'сбросить профиль'",
                get_main_keyboard())
        else:
            start_onboarding(user_id, peer_id)
        return
    
    # --- Онбординг ---
    if cmd in ('gender', 'activity', 'goal'):
        handle_onboarding(user_id, peer_id, cmd, payload_data.get('value'))
        return

def route_text(user_id, peer_id, text):
    """Обработка текстовых команд"""
    # --- Отмена ---
    if text.lower() in ('отмена', 'отменить', 'назад', 'cancel'):
        if user_id in user_states:
            del user_states[user_id]
        send_message(peer_id, "Отменено.", get_main_keyboard())
        return
    
    # --- Сброс профиля ---
    if text.lower() == 'сбросить профиль':
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(vk_id=user_id).first()
            if user:
                user.onboarded = False
                session.commit()
                send_message(peer_id, "Профиль сброшен. Давайте настроим заново!", get_main_keyboard())
                start_onboarding(user_id, peer_id)
            else:
                send_message(peer_id, "У вас нет профиля.", get_main_keyboard())
        finally:
            session.close()
        return
    
    # --- Админские команды ---
    if is_admin(user_id) and route_admin_commands(user_id, peer_id, text):
        return
    
    # --- Состояния пользователя ---
    if route_user_states(user_id, peer_id, text):
        return
    
    # --- Команда /start ---
    if text.lower() in ('/start', 'старт', 'начать'):
        user = get_or_create_user(user_id)
        if user['onboarded']:
            user_name = user['name'] if user['name'] else ""
            greeting = f"Привет, {user_name}!" if user_name else "Привет!"
            send_message(peer_id, f"{greeting} Я бот для подсчета КБЖУ.\nНапиши продукт и вес (банан 150г) или нажми кнопки.", get_main_keyboard())
        else:
            start_onboarding(user_id, peer_id)
        return
    
    # --- Поиск продукта ---
    if text:
        handle_search(user_id, peer_id, text)

def route_admin_commands(user_id, peer_id, text):
    """Обработка админских команд. Возвращает True, если команда обработана."""
    if text.lower() == '/stats':
        result = get_all_users_stats()
        send_result(peer_id, result)
        return True
    
    if text.lower() == '/week':
        result = get_weekly_stats()
        send_result(peer_id, result)
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
    
    if state in ('onboarding_name', 'onboarding_age', 'onboarding_height', 'onboarding_weight'):
        handle_onboarding(user_id, peer_id, None, text)
        return True
    
    return False

def send_result(peer_id, result):
    """Универсальная отправка результата (строка или кортеж)"""
    if isinstance(result, tuple):
        msg, keyboard = result
        send_message(peer_id, msg, keyboard if keyboard else get_main_keyboard())
    else:
        send_message(peer_id, result, get_main_keyboard())