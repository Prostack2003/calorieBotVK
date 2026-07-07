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