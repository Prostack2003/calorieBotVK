import json

def get_main_keyboard():
    return json.dumps({
        "one_time": False,
        "buttons": [
            [{"action": {"type": "text", "label": "Статистика", "payload": "{\"cmd\":\"stats\"}"}, "color": "primary"},
             {"action": {"type": "text", "label": "Добавить еду", "payload": "{\"cmd\":\"add\"}"}, "color": "positive"}],
            [{"action": {"type": "text", "label": "Мои цели", "payload": "{\"cmd\":\"goals\"}"}, "color": "secondary"},
             {"action": {"type": "text", "label": "Настройки", "payload": "{\"cmd\":\"settings\"}"}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "FAQ", "payload": "{\"cmd\":\"faq\"}"}, "color": "secondary"}]
        ]
    }, ensure_ascii=False)

def get_cancel_keyboard():
    return json.dumps({
        "one_time": True,
        "buttons": [[{"action": {"type": "text", "label": "Отмена", "payload": "{\"cmd\":\"cancel\"}"}, "color": "negative"}]]
    }, ensure_ascii=False)

def get_gender_keyboard():
    return json.dumps({
        "one_time": True,
        "buttons": [
            [{"action": {"type": "text", "label": "Мужской", "payload": "{\"cmd\":\"gender\",\"value\":\"male\"}"}, "color": "primary"},
             {"action": {"type": "text", "label": "Женский", "payload": "{\"cmd\":\"gender\",\"value\":\"female\"}"}, "color": "secondary"}]
        ]
    }, ensure_ascii=False)

def get_activity_keyboard():
    return json.dumps({
        "one_time": True,
        "buttons": [
            [{"action": {"type": "text", "label": "Минимальная (сидячий)", "payload": "{\"cmd\":\"activity\",\"value\":1.2}"}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "Слабая (1-3 раза/нед)", "payload": "{\"cmd\":\"activity\",\"value\":1.375}"}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "Умеренная (3-5 раз/нед)", "payload": "{\"cmd\":\"activity\",\"value\":1.55}"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "Высокая (6-7 раз/нед)", "payload": "{\"cmd\":\"activity\",\"value\":1.725}"}, "color": "secondary"}],
            [{"action": {"type": "text", "label": "Экстремальная (2 раза/день)", "payload": "{\"cmd\":\"activity\",\"value\":1.9}"}, "color": "secondary"}]
        ]
    }, ensure_ascii=False)

def get_goal_keyboard():
    return json.dumps({
        "one_time": True,
        "buttons": [
            [{"action": {"type": "text", "label": "Похудение (-20%)", "payload": "{\"cmd\":\"goal\",\"value\":\"lose\"}"}, "color": "negative"}],
            [{"action": {"type": "text", "label": "Поддержание", "payload": "{\"cmd\":\"goal\",\"value\":\"maintain\"}"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "Набор массы (+15%)", "payload": "{\"cmd\":\"goal\",\"value\":\"gain\"}"}, "color": "positive"}]
        ]
    }, ensure_ascii=False)

def get_product_selection_keyboard(products):
    buttons = []
    for i, product in enumerate(products):
        short_name = product['name'][:30] if len(product['name']) > 30 else product['name']
        label = f"{i+1}. {short_name}"
        if len(label) > 40:
            label = label[:37] + "..."
        buttons.append([{"action": {"type": "text", "label": label, "payload": json.dumps({"cmd": "select", "product": product['name']})}, "color": "secondary"}])
    buttons.append([{"action": {"type": "text", "label": "Отмена", "payload": "{\"cmd\":\"cancel\"}"}, "color": "negative"}])
    return json.dumps({"one_time": True, "buttons": buttons}, ensure_ascii=False)

def get_delete_keyboard(logs):
    buttons = []
    for i, log in enumerate(logs, 1):
        short_name = log.product_name[:30] if len(log.product_name) > 30 else log.product_name
        label = f"{i}. {short_name} ({log.weight}г)"
        if len(label) > 40:
            label = label[:37] + "..."
        buttons.append([{"action": {"type": "text", "label": label, "payload": json.dumps({"cmd": "delete", "log_id": log.id})}, "color": "negative"}])
    buttons.append([{"action": {"type": "text", "label": "Отмена", "payload": "{\"cmd\":\"cancel\"}"}, "color": "secondary"}])
    return json.dumps({"one_time": True, "buttons": buttons}, ensure_ascii=False)