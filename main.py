import json
from datetime import datetime
from config import longpoll, VK_GROUP_ID
from vk_api.bot_longpoll import VkBotEventType
from handlers.router import route_payload, route_text
from utils.logger import logger

logger.info(f"🤖 Бот запущен. Группа ID: {VK_GROUP_ID}")
print("⏳ Ожидание сообщений...\n")

# ИСПРАВЛЕНИЕ #8: Защита от повторной обработки событий
processed_events = set()
MAX_PROCESSED_EVENTS = 1000

try:
    for event in longpoll.listen():
        if event.type != VkBotEventType.MESSAGE_NEW:
            continue
        
        message = event.obj['message']
        event_id = message.get('conversation_message_id') or message.get('id')
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if event_id in processed_events:
            logger.debug(f"Пропущено дублирующее событие: {event_id}")
            continue
        
        processed_events.add(event_id)
        
        if len(processed_events) > MAX_PROCESSED_EVENTS:
            processed_events.clear()
        
        peer_id = message['peer_id']
        user_id = message['from_id']
        text = message.get('text', '').strip()
        payload_raw = message.get('payload')
        
        # Логирование входящего сообщения
        if text:
            logger.info(f"📩 [User {user_id}] Текст: {text[:100]}")
        
        if payload_raw:
            try:
                payload_data = json.loads(payload_raw)
                cmd = payload_data.get('cmd') or payload_data.get('command')
                logger.info(f"🔘 [User {user_id}] Кнопка: {cmd}")
                route_payload(user_id, peer_id, payload_data)
            except json.JSONDecodeError as e:
                logger.warning(f"❌ Ошибка парсинга payload от {user_id}: {e}")
            except Exception as e:
                logger.error(f"💥 Ошибка обработки payload от {user_id}: {e}", exc_info=True)
            continue
        
        if text:
            try:
                route_text(user_id, peer_id, text)
            except Exception as e:
                logger.error(f"💥 Ошибка обработки текста от {user_id}: {e}", exc_info=True)

except KeyboardInterrupt:
    logger.info("👋 Бот остановлен пользователем (Ctrl+C)")
    print("\n👋 Бот остановлен.")
except Exception as e:
    logger.critical(f"💥 Критическая ошибка: {e}", exc_info=True)
    print(f"💥 Критическая ошибка: {e}")
    import traceback
    traceback.print_exc()