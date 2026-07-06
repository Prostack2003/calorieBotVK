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


def send_document(peer_id, filepath, message="", max_retries=3):
    """Отправка документа пользователю с повторными попытками"""
    import requests
    import time
    
    for attempt in range(1, max_retries + 1):
        try:
            if not os.path.exists(filepath):
                logger.error(f"❌ Файл не найден: {filepath}")
                return False
            
            filename = os.path.basename(filepath)
            logger.info(f"📄 Загрузка документа (попытка {attempt}/{max_retries}): {filename}")
            
            # Получаем СВЕЖИЙ URL для загрузки (каждый раз новый!)
            upload_server = vk.docs.getMessagesUploadServer(type='doc', peer_id=peer_id)
            upload_url = upload_server['upload_url']
            
            # Загружаем файл
            with open(filepath, 'rb') as file:
                response = requests.post(
                    upload_url, 
                    files={'file': (filename, file, 'application/pdf')},
                    timeout=30
                )
            
            # Проверяем статус
            if response.status_code == 405:
                logger.warning(f"⚠️ HTTP 405 (попытка {attempt}/{max_retries}). Ждём 2 секунды...")
                time.sleep(2)
                continue
            
            if response.status_code != 200:
                logger.error(f"❌ Ошибка загрузки: HTTP {response.status_code}")
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                return False
            
            # Парсим ответ
            try:
                file_data = response.json()
            except Exception as e:
                logger.error(f"❌ Ошибка парсинга ответа: {e}")
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                return False
            
            if 'file' not in file_data:
                logger.error(f"❌ В ответе нет поля 'file': {file_data}")
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                return False
            
            # Сохраняем документ
            save_result = vk.docs.save(file=file_data['file'], title=filename)
            
            if 'doc' not in save_result:
                logger.error(f"❌ Ошибка сохранения документа: {save_result}")
                return False
            
            doc = save_result['doc']
            attachment = f"doc{doc['owner_id']}_{doc['id']}"
            
            # Отправляем сообщение с документом
            vk.messages.send(
                peer_id=peer_id,
                message=message,
                attachment=attachment,
                random_id=get_random_id()
            )
            
            logger.info(f"✅ Документ отправлен: {filename}")
            
            # Удаляем файл после отправки
            try:
                os.remove(filepath)
                logger.debug(f"🗑️ Файл удалён: {filepath}")
            except Exception as e:
                logger.warning(f"Не удалось удалить файл {filepath}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки документа (попытка {attempt}/{max_retries}): {e}", exc_info=True)
            if attempt < max_retries:
                time.sleep(2)
                continue
    
    logger.error(f"❌ Не удалось отправить документ после {max_retries} попыток")
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