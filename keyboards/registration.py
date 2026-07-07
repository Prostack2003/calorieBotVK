import json


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