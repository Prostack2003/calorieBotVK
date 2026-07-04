import os
from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll
from dotenv import load_dotenv

load_dotenv()

VK_TOKEN = os.getenv("VK_GROUP_TOKEN")
VK_GROUP_ID = int(os.getenv("VK_GROUP_ID"))
ADMIN_ID = os.getenv("ADMIN_ID")

if not VK_TOKEN or not VK_GROUP_ID:
    raise ValueError("Укажите VK_GROUP_TOKEN и VK_GROUP_ID в файле .env")

# Инициализация VK API
vk_session = VkApi(token=VK_TOKEN)
longpoll = VkBotLongPoll(vk_session, VK_GROUP_ID)
vk = vk_session.get_api()

# Словарь состояний пользователей (глобальный)
user_states = {}