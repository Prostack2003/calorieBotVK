import json


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