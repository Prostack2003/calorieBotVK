import json
from config import longpoll, VK_GROUP_ID
from vk_api.bot_longpoll import VkBotEventType
from handlers.router import route_payload, route_text

print(f"🤖 Бот запущен. Группа ID: {VK_GROUP_ID}")
print("⏳ Ожидание сообщений...\n")

try:
    for event in longpoll.listen():
        if event.type != VkBotEventType.MESSAGE_NEW:
            continue
        
        message = event.obj['message']
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