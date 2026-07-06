import json
from datetime import datetime
from config import longpoll, VK_GROUP_ID
from vk_api.bot_longpoll import VkBotEventType
from handlers.router import route_payload, route_text

print(f"🤖 Бот запущен. Группа ID: {VK_GROUP_ID}")
print("⏳ Ожидание сообщений...\n")

# ИСПРАВЛЕНИЕ #8: Защита от повторной обработки событий
processed_events = set()
MAX_PROCESSED_EVENTS = 1000  # Максимальное количество хранимых ID

try:
    for event in longpoll.listen():
        if event.type != VkBotEventType.MESSAGE_NEW:
            continue
        
        message = event.obj['message']
        event_id = message.get('conversation_message_id') or message.get('id')
        
        # Проверяем, не обрабатывали ли мы уже это событие
        if event_id in processed_events:
            continue
        
        # Добавляем ID в множество обработанных
        processed_events.add(event_id)
        
        # Ограничиваем размер множества
        if len(processed_events) > MAX_PROCESSED_EVENTS:
            # Удаляем самые старые (примерно)
            processed_events.clear()
        
        peer_id = message['peer_id']
        user_id = message['from_id']
        text = message.get('text', '').strip()
        payload_raw = message.get('payload')
        
        # Обработка кнопок
        if payload_raw:
            try:
                payload_data = json.loads(payload_raw)
                route_payload(user_id, peer_id, payload_data)
            except json.JSONDecodeError:
                pass
            continue
        
        # Обработка текста
        if text:
            route_text(user_id, peer_id, text)

except KeyboardInterrupt:
    print("\n👋 Бот остановлен.")
except Exception as e:
    print(f"💥 Критическая ошибка: {e}")
    import traceback
    traceback.print_exc()