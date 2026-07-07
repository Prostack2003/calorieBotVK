import json
from datetime import date, datetime, timedelta
from config import user_states
from database import SessionLocal, GlobalProduct, UserProduct
from utils.messenger import send_message
from keyboards import get_main_keyboard, get_cancel_keyboard

def get_products_list(user_id):
    session = SessionLocal()
    try:
        global_products = session.query(GlobalProduct).order_by(GlobalProduct.name).all()
        user_products = session.query(UserProduct).filter_by(user_id=user_id).order_by(UserProduct.name).all()
        
        msg = " Доступные продукты:\n\n"
        
        if user_products:
            msg += "👤 Ваши продукты:\n"
            for p in user_products:
                msg += f"• {p.name} ({p.calories} ккал/100г)\n"
            msg += "\n"
        
        if global_products:
            msg += " База бота:\n"
            for p in global_products:
                msg += f"• {p.name} ({p.calories} ккал/100г)\n"
        
        msg += "\n💡 Напишите название продукта и вес:\n"
        msg += "Например: банан 150г"
        
        keyboard = json.dumps({
            "one_time": True,
            "buttons": [
                [{"action": {"type": "text", "label": "Понятно", "payload": "{\"cmd\":\"manual_input\"}"}, "color": "primary"}]
            ]
        }, ensure_ascii=False)
        
        return msg, keyboard
    finally:
        session.close()

def get_date_selection_keyboard():
    yesterday = date.today() - timedelta(days=1)
    
    keyboard = json.dumps({
        "one_time": True,
        "buttons": [
            [
                {"action": {"type": "text", "label": "✅ Сегодня", "payload": json.dumps({"cmd": "set_add_date", "date": date.today().strftime('%Y-%m-%d')})}, "color": "primary"},
                {"action": {"type": "text", "label": "◀️ Вчера", "payload": json.dumps({"cmd": "set_add_date", "date": yesterday.strftime('%Y-%m-%d')})}, "color": "secondary"}
            ],
            [
                {"action": {"type": "text", "label": "📅 Выбрать дату", "payload": "{\"cmd\":\"ask_date_input\"}"}, "color": "secondary"}
            ]
        ]
    }, ensure_ascii=False)
    
    return keyboard

def ask_add_date(user_id, peer_id):
    """Спросить дату для добавления еды"""
    user_states[user_id] = {'state': 'ask_add_date'}
    send_message(
        peer_id,
        "📅 За какую дату добавляем еду?\n\n"
        "💡 Или просто напишите продукт — добавится за сегодня.",
        get_date_selection_keyboard()
    )

def handle_date_input(user_id, peer_id, text):
    """Обработка ввода даты вручную"""
    try:
        # Пробуем разные форматы
        for fmt in ['%d.%m', '%d.%m.%Y', '%d/%m', '%d/%m/%Y']:
            try:
                parsed_date = datetime.strptime(text, fmt).date()
                # Если год не указан, используем текущий
                if parsed_date.year == 1900:
                    parsed_date = parsed_date.replace(year=date.today().year)
                
                # Проверяем, что дата не в будущем
                if parsed_date > date.today():
                    send_message(peer_id, "❌ Нельзя добавить еду в будущее. Выберите дату сегодня или раньше.", get_main_keyboard())
                    return
                
                # Сохраняем дату в состоянии
                user_states[user_id] = {'state': 'adding_food', 'add_date': parsed_date}
                send_message(
                    peer_id,
                    f"✅ Будем добавлять за {parsed_date.strftime('%d.%m.%Y')}\n\n"
                    "Напишите название продукта и вес (например: банан 150г)",
                    get_main_keyboard()
                )
                return
            except ValueError:
                continue
        
        send_message(peer_id, "❌ Неверный формат. Используйте ДД.ММ или ДД.ММ.ГГГГ (например: 05.07 или 05.07.2025)", get_main_keyboard())
        
    except Exception as e:
        send_message(peer_id, "❌ Ошибка обработки даты.", get_main_keyboard())

        