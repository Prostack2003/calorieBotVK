import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger():
    """Настройка системы логирования"""
    
    # Создаём папку logs, если её нет
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Создаём логгер
    logger = logging.getLogger('calorie_bot')
    logger.setLevel(logging.INFO)
    
    # Формат сообщений
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # === Обработчик 1: Вывод в консоль ===
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # === Обработчик 2: Файл с ротацией ===
    # Максимум 5 МБ на файл, храним 3 последних файла
    file_handler = RotatingFileHandler(
        'logs/bot.log',
        maxBytes=5 * 1024 * 1024,  # 5 МБ
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # === Обработчик 3: Отдельный файл для ошибок ===
    error_handler = RotatingFileHandler(
        'logs/errors.log',
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # Добавляем обработчики к логгеру
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger


# Глобальный логгер
logger = setup_logger()