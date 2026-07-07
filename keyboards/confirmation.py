import json


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