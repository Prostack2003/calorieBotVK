from config import vk, longpoll, VK_GROUP_ID, user_states
from vk_api.bot_longpoll import VkBotEventType
import json

from database import SessionLocal, User
from utils.messenger import send_message
from keyboards.keyboards import get_main_keyboard, get_cancel_keyboard
from handlers.onboarding import start_onboarding, handle_onboarding
from handlers.food import (
    handle_search, handle_selection, handle_selection_from_list,
    handle_weight, save_custom_product, get_products_list
)
from handlers.stats import get_daily_stats, get_or_create_user
from handlers.faq import get_faq_text
from handlers.admin import is_admin, get_all_users_stats, get_user_report, get_users_list

print(f"Бот запущен. Группа ID: {VK_GROUP_ID}")
print("Ожидание сообщений...\n")

try:
    for event in longpoll.listen():
        if event.type != VkBotEventType.MESSAGE_NEW:
            continue
        
        msg = event.obj['message']
        peer_id = msg['peer_id']
        user_id = msg['from_id']
        text = msg.get('text', '').strip()
        payload_raw = msg.get('payload')
        
        # --- Обработка кнопок (payload) ---
        if payload_raw:
            try:
                pd = json.loads(payload_raw)
                cmd = pd.get('cmd')
                
                if cmd == 'stats':
                    result = get_daily_stats(user_id)
                    if isinstance(result, tuple):
                        send_message(peer_id, result[0], result[1])
                    else:
                        send_message(peer_id, result, get_main_keyboard())
                elif cmd == 'delete':
                    from handlers.food import delete_log
                    delete_log(user_id, peer_id, pd['log_id'])
                elif cmd == 'select':
                    handle_selection(user_id, peer_id, pd['product'])
                elif cmd == 'select_from_list':
                    handle_selection_from_list(user_id, peer_id, pd['product_name'])
                elif cmd == 'manual_input':
                    send_message(peer_id, "Напишите название продукта и вес (например: банан 150г)", get_main_keyboard())
                elif cmd == 'cancel':
                    if user_id in user_states: del user_states[user_id]
                    send_message(peer_id, "Отменено.", get_main_keyboard())
                elif cmd == 'add':
                    result = get_products_list(user_id)
                    send_message(peer_id, result[0], result[1])
                elif cmd == 'faq':
                    send_message(peer_id, get_faq_text(), get_main_keyboard())
                elif cmd == 'goals':
                    user = get_or_create_user(user_id)
                    if user['onboarded']:
                        send_message(peer_id, 
                            f"🎯 Ваша цель: {round(user['daily_calories'])} ккал/день\n"
                            f"Б: {round(user['daily_proteins'], 1)}г | Ж: {round(user['daily_fats'], 1)}г | У: {round(user['daily_carbs'], 1)}г",
                            get_main_keyboard())
                    else:
                        start_onboarding(user_id, peer_id)
                elif cmd == 'settings':
                    user = get_or_create_user(user_id)
                    if user['onboarded']:
                        gender_text = 'Мужской' if user['gender'] == 'male' else 'Женский'
                        send_message(peer_id, 
                            f"️ Ваши данные:\n"
                            f"Имя: {user['name']}\nПол: {gender_text}\n"
                            f"Возраст: {user['age']}\nРост: {user['height']} см\n"
                            f"Вес: {user['weight']} кг\nЦель: {user['goal']}\n\n"
                            f"Чтобы изменить, напишите 'сбросить профиль'",
                            get_main_keyboard())
                    else:
                        start_onboarding(user_id, peer_id)
                elif cmd == 'gender':
                    handle_onboarding(user_id, peer_id, cmd, pd['value'])
                elif cmd == 'activity':
                    handle_onboarding(user_id, peer_id, cmd, pd['value'])
                elif cmd == 'goal':
                    handle_onboarding(user_id, peer_id, cmd, pd['value'])
                continue
            except json.JSONDecodeError:
                pass
        
        # --- Обработка текста ---
        if text.lower() in ('отмена', 'отменить', 'назад', 'cancel'):
            if user_id in user_states: del user_states[user_id]
            send_message(peer_id, "Отменено.", get_main_keyboard())
            continue
        
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
            continue
        
        # --- Админские команды ---
        if is_admin(user_id):
            if text.lower() == '/stats':
                send_message(peer_id, get_all_users_stats(), get_main_keyboard())
                continue
            if text.lower() == '/users':
                send_message(peer_id, get_users_list(), get_main_keyboard())
                continue
            if text.lower().startswith('/report'):
                parts = text.split()
                if len(parts) < 2:
                    send_message(peer_id, "Используйте: /report <ID>\nНапример: /report 734594067", get_main_keyboard())
                    continue
                try:
                    send_message(peer_id, get_user_report(int(parts[1])), get_main_keyboard())
                except ValueError:
                    send_message(peer_id, "❌ ID должен быть числом.", get_main_keyboard())
                continue
            if text.lower() == '/admin':
                send_message(peer_id, 
                    "🔐 Админ-панель:\n\n"
                    "/stats - Общая статистика за сегодня\n"
                    "/users - Список всех пользователей\n"
                    "/report <ID> - Детальный отчёт\n"
                    "/admin - Эта справка",
                    get_main_keyboard())
                continue
        
        # --- Состояния пользователя ---
        if user_id in user_states:
            state = user_states[user_id]['state']
            
            if state == 'weight':
                handle_weight(user_id, peer_id, text)
                continue
            if state in ('custom_name', 'custom_kbzhu'):
                save_custom_product(user_id, peer_id, text)
                continue
            if state == 'ask_custom':
                if text.lower() == 'да':
                    user_states[user_id]['state'] = 'custom_name'
                    send_message(peer_id, "Как называется продукт?", get_cancel_keyboard())
                else:
                    handle_search(user_id, peer_id, text)
                continue
            if state == 'selecting':
                if text.isdigit():
                    n = int(text)
                    prods = user_states[user_id]['products']
                    if 1 <= n <= len(prods):
                        handle_selection(user_id, peer_id, prods[n-1]['name'])
                else:
                    handle_selection(user_id, peer_id, text)
                continue
            if state in ('onboarding_name', 'onboarding_age', 'onboarding_height', 'onboarding_weight'):
                handle_onboarding(user_id, peer_id, None, text)
                continue
        
        # --- Команды ---
        if text.lower() in ('/start', 'старт', 'начать'):
            user = get_or_create_user(user_id)
            if user['onboarded']:
                user_name = user['name'] if user['name'] else ""
                greeting = f"Привет, {user_name}!" if user_name else "Привет!"
                send_message(peer_id, f"{greeting} Я бот для подсчета КБЖУ.\nНапиши продукт и вес (банан 150г) или нажми кнопки.", get_main_keyboard())
            else:
                start_onboarding(user_id, peer_id)
            continue
        
        # --- Поиск продукта ---
        if text:
            handle_search(user_id, peer_id, text)

except KeyboardInterrupt:
    print("\nБот остановлен.")
except Exception as e:
    print(f"Критическая ошибка: {e}")
    import traceback
    traceback.print_exc()