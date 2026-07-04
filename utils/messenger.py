import random
import json
from config import vk, ADMIN_ID

def send_message(peer_id, text, keyboard=None):
    """Отправка сообщения пользователю"""
    try:
        params = {
            "peer_id": peer_id,
            "message": text,
            "random_id": random.randint(1, 2147483647)
        }
        if keyboard:
            if isinstance(keyboard, str):
                params["keyboard"] = keyboard
            else:
                params["keyboard"] = json.dumps(keyboard)
        vk.messages.send(**params)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def notify_admin(user_id, user_name, text):
    """Отправка уведомления администратору"""
    if ADMIN_ID:
        try:
            vk.messages.send(
                peer_id=int(ADMIN_ID),
                message=f"👤 {user_name} (ID: {user_id}):\n{text}",
                random_id=random.randint(1, 2147483647)
            )
        except Exception as e:
            print(f"Не удалось отправить админу: {e}")