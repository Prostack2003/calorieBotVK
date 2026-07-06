import random
import time
from config import vk
from utils.logger import logger


def get_random_id():
    """Генерация уникального ID для сообщения (чтобы ВК не дублировал)"""
    return int(time.time() * 1000) + random.randint(0, 999)


def send_message(peer_id, message, keyboard=None):
    """Отправка сообщения пользователю"""
    try:
        if keyboard:
            vk.messages.send(
                peer_id=peer_id,
                message=message,
                keyboard=keyboard,
                random_id=get_random_id()
            )
        else:
            vk.messages.send(
                peer_id=peer_id,
                message=message,
                random_id=get_random_id()
            )
        logger.debug(f"📤 Отправлено сообщение пользователю {peer_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки сообщения пользователю {peer_id}: {e}")
        print(f"Ошибка отправки: {e}")


def notify_admin(user_id, user_name, action_text):
    """Уведомление администратора о действиях пользователя"""
    from config import ADMIN_ID
    if not ADMIN_ID:
        return
    
    try:
        admin_message = (
            f"🔔 Действие пользователя\n\n"
            f"👤 {user_name} (ID: {user_id})\n"
            f"📝 {action_text}"
        )
        vk.messages.send(
            peer_id=int(ADMIN_ID),
            message=admin_message,
            random_id=get_random_id()
        )
        logger.debug(f"📤 Уведомление админу отправлено")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления админу: {e}")