import json


def get_main_keyboard():
    """Главная клавиатура бота"""
    keyboard = {
        "one_time": False,
        "buttons": [
            [
                {"action": {"type": "text", "label": "📊 Статистика", "payload": "{\"cmd\":\"stats\"}"}, "color": "primary"},
                {"action": {"type": "text", "label": "➕ Добавить еду", "payload": "{\"cmd\":\"add\"}"}, "color": "primary"}
            ],
            [
                {"action": {"type": "text", "label": "🎯 Мои цели", "payload": "{\"cmd\":\"goals\"}"}, "color": "secondary"},
                {"action": {"type": "text", "label": "⚙️ Настройки", "payload": "{\"cmd\":\"settings\"}"}, "color": "secondary"}
            ],
            [
                {"action": {"type": "text", "label": "❓ FAQ", "payload": "{\"cmd\":\"faq\"}"}, "color": "secondary"}
            ]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)


def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    keyboard = {
        "one_time": True,
        "buttons": [
            [{"action": {"type": "text", "label": "❌ Отмена", "payload": "{\"cmd\":\"cancel\"}"}, "color": "negative"}]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)


def get_gender_keyboard():
    """Клавиатура выбора пола"""
    keyboard = {
        "one_time": True,
        "buttons": [
            [
                {"action": {"type": "text", "label": "👨 Мужской", "payload": "{\"cmd\":\"gender\",\"value\":\"male\"}"}, "color": "primary"},
                {"action": {"type": "text", "label": "👩 Женский", "payload": "{\"cmd\":\"gender\",\"value\":\"female\"}"}, "color": "primary"}
            ]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)


def get_activity_keyboard():
    """Клавиатура выбора уровня активности"""
    return json.dumps({
        "one_time": True,
        "buttons": [
            [{"action": {"type": "text", "label": "Минимальная (сидячая работа)", "payload": "{\"cmd\":\"activity\",\"value\":1.2}"}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "Слабая (1-3 тренировки/нед)", "payload": "{\"cmd\":\"activity\",\"value\":1.375}"}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "Умеренная (3-5 тренировок/нед)", "payload": "{\"cmd\":\"activity\",\"value\":1.55}"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "Высокая (6-7 тренировок/нед)", "payload": "{\"cmd\":\"activity\",\"value\":1.725}"}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "Экстремальная (2 раза в день)", "payload": "{\"cmd\":\"activity\",\"value\":1.9}"}, "color": "secondary"}]
        ]
    }, ensure_ascii=False)


def get_goal_keyboard():
    """Клавиатура выбора цели"""
    keyboard = {
        "one_time": True,
        "buttons": [
            [{"action": {"type": "text", "label": "Похудение (-20%)", "payload": "{\"cmd\":\"goal\",\"value\":\"lose\"}"}, "color": "negative"}],
            [{"action": {"type": "text", "label": "Поддержание веса", "payload": "{\"cmd\":\"goal\",\"value\":\"maintain\"}"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "Набор массы (+15%)", "payload": "{\"cmd\":\"goal\",\"value\":\"gain\"}"}, "color": "positive"}]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)


def get_product_selection_keyboard(products):
    """Клавиатура выбора продукта из списка"""
    buttons = []
    for i, product in enumerate(products):
        # Обрезаем длинные названия
        short_name = product['name'][:30] if len(product['name']) > 30 else product['name']
        label = f"{i+1}. {short_name}"
        
        # Дополнительная проверка длины
        if len(label) > 40:
            label = label[:37] + "..."
        
        buttons.append([{
            "action": {
                "type": "text", 
                "label": label, 
                "payload": json.dumps({"cmd": "select", "product": product['name']})
            }, 
            "color": "secondary"
        }])
    
    buttons.append([{
        "action": {"type": "text", "label": "Отмена", "payload": "{\"cmd\":\"cancel\"}"}, 
        "color": "negative"
    }])
    
    return json.dumps({"one_time": True, "buttons": buttons}, ensure_ascii=False)


def get_delete_keyboard(logs):
    """Клавиатура удаления записей из дневника"""
    buttons = []
    for log in logs:
        short_name = log.product_name[:30] if len(log.product_name) > 30 else log.product_name
        label = f"{short_name} ({log.weight}г)"
        if len(label) > 40:
            label = label[:37] + "..."
        
        buttons.append([{
            "action": {
                "type": "text", 
                "label": label, 
                "payload": json.dumps({"cmd": "delete", "log_id": log.id})
            }, 
            "color": "negative"
        }])
    
    buttons.append([{
        "action": {"type": "text", "label": "◀️ Назад", "payload": "{\"cmd\":\"stats\"}"}, 
        "color": "secondary"
    }])
    
    return json.dumps({"one_time": True, "buttons": buttons}, ensure_ascii=False)


def get_settings_keyboard():
    """Клавиатура для настроек с кнопкой сброса профиля"""
    return json.dumps({
        "one_time": True,
        "buttons": [
            [{"action": {"type": "text", "label": "🔄 Сбросить профиль", "payload": "{\"cmd\":\"reset_profile\"}"}, "color": "negative"}],
            [{"action": {"type": "text", "label": "◀️ В главное меню", "payload": "{\"cmd\":\"main_menu\"}"}, "color": "secondary"}]
        ]
    }, ensure_ascii=False)


def get_settings_keyboard_v2():
    """Клавиатура настроек с кнопкой 'Мои продукты'"""
    return json.dumps({
        "one_time": True,
        "buttons": [
            [{"action": {"type": "text", "label": "📦 Мои продукты", "payload": "{\"cmd\":\"my_products\"}"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "🔄 Сбросить профиль", "payload": "{\"cmd\":\"reset_profile\"}"}, "color": "negative"}],
            [{"action": {"type": "text", "label": "◀️ В главное меню", "payload": "{\"cmd\":\"main_menu\"}"}, "color": "secondary"}]
        ]
    }, ensure_ascii=False)


def get_confirm_reset_keyboard():
    """Клавиатура подтверждения сброса профиля"""
    return json.dumps({
        "one_time": True,
        "buttons": [
            [
                {"action": {"type": "text", "label": "✅ Да, сбросить", "payload": "{\"cmd\":\"confirm_reset_yes\"}"}, "color": "negative"},
                {"action": {"type": "text", "label": "❌ Отмена", "payload": "{\"cmd\":\"confirm_reset_no\"}"}, "color": "secondary"}
            ]
        ]
    }, ensure_ascii=False)


def get_user_products_keyboard(products):
    """Клавиатура со списком продуктов пользователя и кнопками удаления"""
    buttons = []
    for product in products:
        # Обрезаем длинные названия
        name = product.name
        if len(name) > 28:
            name = name[:25] + "..."
        
        label = f"🗑 {name} ({product.calories} ккал)"
        if len(label) > 40:
            label = label[:37] + "..."
        
        payload = json.dumps({
            "cmd": "delete_my_product", 
            "product_id": product.id
        })
        buttons.append([{
            "action": {"type": "text", "label": label, "payload": payload},
            "color": "negative"
        }])
    
    buttons.append([{
        "action": {"type": "text", "label": "◀️ Назад к настройкам", "payload": "{\"cmd\":\"settings\"}"},
        "color": "secondary"
    }])
    
    return json.dumps({"one_time": True, "buttons": buttons}, ensure_ascii=False)


def get_confirm_delete_product_keyboard(product_id, product_name):
    """Клавиатура подтверждения удаления продукта"""
    return json.dumps({
        "one_time": True,
        "buttons": [
            [
                {
                    "action": {
                        "type": "text", 
                        "label": "✅ Да, удалить", 
                        "payload": json.dumps({"cmd": "confirm_delete_product_yes", "product_id": product_id})
                    }, 
                    "color": "negative"
                },
                {
                    "action": {"type": "text", "label": "❌ Отмена", "payload": "{\"cmd\":\"my_products\"}"}, 
                    "color": "secondary"
                }
            ]
        ]
    }, ensure_ascii=False)


def get_confirm_kbju_keyboard():
    """Клавиатура подтверждения КБЖУ при добавлении своего продукта"""
    return json.dumps({
        "one_time": True,
        "buttons": [
            [
                {
                    "action": {
                        "type": "text", 
                        "label": "✅ Всё верно, сохранить", 
                        "payload": "{\"cmd\":\"confirm_custom_yes\"}"
                    }, 
                    "color": "positive"
                }
            ],
            [
                {
                    "action": {
                        "type": "text", 
                        "label": "✏️ Ввести заново", 
                        "payload": "{\"cmd\":\"confirm_custom_edit\"}"
                    }, 
                    "color": "primary"
                },
                {
                    "action": {
                        "type": "text", 
                        "label": "❌ Отмена", 
                        "payload": "{\"cmd\":\"confirm_custom_cancel\"}"
                    }, 
                    "color": "negative"
                }
            ]
        ]
    }, ensure_ascii=False)