import random
import time
import os
from config import vk
from utils.logger import logger


def get_random_id():
    """Генерация уникального ID для сообщения"""
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


def send_document(peer_id, filepath, message=""):
    """Отправка документа пользователю"""
    try:
        if not os.path.exists(filepath):
            logger.error(f"❌ Файл не найден: {filepath}")
            return False
        
        # Получаем URL для загрузки
        upload_url = vk.docs.getMessagesUploadServer(type='doc', peer_id=peer_id)['upload_url']
        
        # Загружаем файл
        import requests
        with open(filepath, 'rb') as file:
            response = requests.post(upload_url, files={'file': file})
            file_data = response.json()
        
        # Сохраняем документ
        doc = vk.docs.save(file=file_data['file'], title=os.path.basename(filepath))['doc']
        
        # Формируем attachment
        attachment = f"doc{doc['owner_id']}_{doc['id']}"
        
        # Отправляем сообщение с документом
        vk.messages.send(
            peer_id=peer_id,
            message=message,
            attachment=attachment,
            random_id=get_random_id()
        )
        
        logger.info(f"📄 Документ отправлен: {filepath}")
        
        # Удаляем файл после отправки
        try:
            os.remove(filepath)
            logger.debug(f"🗑️ Файл удалён: {filepath}")
        except Exception as e:
            logger.warning(f"Не удалось удалить файл {filepath}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки документа: {e}", exc_info=True)
        return False


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