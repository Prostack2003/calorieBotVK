import json


import json


def get_product_selection_keyboard(products, show_online=True):
    """Клавиатура выбора продукта из списка"""
    buttons = []
    
    for i, product in enumerate(products[:5]):  # Максимум 5 продуктов
        # Передаем индекс продукта, а не название
        payload_data = {
            "cmd": "select_product",
            "idx": i  # Индекс в списке
        }
        
        # Проверяем длину payload
        payload_str = json.dumps(payload_data, ensure_ascii=False)
        if len(payload_str) > 255:
            # Если слишком длинно, сокращаем название
            short_name = product['name'][:30] + "..."
            payload_data = {
                "cmd": "select_product",
                "idx": i,
                "name": short_name
            }
        
        buttons.append([{
            "action": {
                "type": "text",
                "label": product['name'][:40],  # Обрезаем длинное название
                "payload": json.dumps(payload_data, ensure_ascii=False)
            },
            "color": "primary"
        }])
    
    # Кнопка "Искать в интернете" (только для локальных результатов)
    if show_online:
        buttons.append([{
            "action": {
                "type": "text",
                "label": "🔍 Искать в интернете",
                "payload": json.dumps({"cmd": "search_online"}, ensure_ascii=False)
            },
            "color": "secondary"
        }])
    
    # Кнопка "Добавить свой"
    buttons.append([{
        "action": {
            "type": "text",
            "label": "✏️ Добавить свой продукт",
            "payload": json.dumps({"cmd": "ask_custom"}, ensure_ascii=False)
        },
        "color": "secondary"
    }])
    
    # Кнопка "Отмена"
    buttons.append([{
        "action": {
            "type": "text",
            "label": "❌ Отмена",
            "payload": json.dumps({"cmd": "cancel"}, ensure_ascii=False)
        },
        "color": "negative"
    }])
    
    return json.dumps({"one_time": True, "buttons": buttons}, ensure_ascii=False)

def get_source_selection_keyboard():
    """Клавиатура выбора источника поиска"""
    buttons = [
        [{
            "action": {
                "type": "text",
                "label": "🔍 Поискать в интернете",
                "payload": json.dumps({"cmd": "search_online"})
            },
            "color": "primary"
        }],
        [{
            "action": {
                "type": "text",
                "label": "✏️ Добавить свой продукт",
                "payload": json.dumps({"cmd": "ask_custom"})
            },
            "color": "secondary"
        }],
        [{
            "action": {
                "type": "text",
                "label": "❌ Отмена",
                "payload": json.dumps({"cmd": "cancel"})
            },
            "color": "negative"
        }]
    ]
    
    return json.dumps({"one_time": True, "buttons": buttons}, ensure_ascii=False)