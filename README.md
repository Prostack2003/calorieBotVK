# 🥗 Calorie Bot — Бот для подсчёта КБЖУ ВКонтакте

VK-бот для ведения дневника питания и подсчёта калорий, белков, жиров и углеводов. Работает через Long Poll API ВКонтакте.

## ✨ Возможности

### 👤 Для пользователя
- 🎯 **Персональный расчёт нормы КБЖУ** по формуле Миффлина-Сан Жеора с учётом активности и цели
- 🍽 **Удобное добавление еды** — поиск по базе, выбор из списка или добавление своего продукта
- 📊 **Статистика** — итоги дня, прогресс к цели, детализация по продуктам
- 📥 **Экспорт в PDF** — отчёты за день или произвольный период
- 📦 **Мои продукты** — управление собственными продуктами (добавление/удаление)
- 📅 **Гибкая работа с датами** — добавление за прошлые дни (ДД.ММ или ДД.ММ.ГГГГ)
- 🗑 **Удаление записей** из дневника
- 🔒 **Дисклеймер** при первом запуске о конфиденциальности
- 📋 **FAQ** с подробной инструкцией

### 🔐 Для администратора
- 👥 `/users` — список всех пользователей
- 📊 `/stats` — статистика по всем пользователям за сегодня
- 📈 `/week` — отчёт за последние 7 дней
- 📋 `/report <ID>` — детальный отчёт по пользователю
- 📄 `/pdf <ID> [дата1] [дата2]` — экспорт PDF по любому пользователю
- 📖 `/admin` — справка по админ-панели

## 🛠 Технологии

- **Python 3.10+**
- **vk_api** — работа с ВКонтакте API
- **SQLAlchemy** — ORM для базы данных
- **SQLite** — хранилище данных
- **fpdf2** — генерация PDF-отчётов
- **DejaVu Sans** — шрифты с поддержкой кириллицы

## 📦 Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-username/calorieBot.git
cd calorieBot
```

### 2. Создание виртуального окружения

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка конфигурации

Создайте файл `config.py` и заполните:

```python
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

VK_TOKEN = "ваш_токен_сообщества"
VK_GROUP_ID = 123456789
ADMIN_ID = 123456789  # ваш VK ID

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, VK_GROUP_ID)

user_states = {}
```

### 5. Инициализация базы данных

```bash
python init_db.py
```

### 6. Скачивание шрифтов для PDF

Скачайте шрифты [DejaVu Sans](https://dejavu-fonts.github.io/Downloading.html) и поместите в папку `fonts/`:

```
calorieBot/
└── fonts/
    ├── DejaVuSans.ttf
    └── DejaVuSans-Bold.ttf
```

### 7. Запуск бота

```bash
python main.py
```

## 📁 Структура проекта

```
calorieBot/
├── main.py                      # Точка входа
├── config.py                    # Конфигурация (НЕ в git)
├── init_db.py                   # Инициализация БД
├── kbju_bot.db                  # База данных (НЕ в git)
├── requirements.txt             # Зависимости
├── .gitignore
│
├── data/
│   └── products.csv             # Начальная база продуктов
│
├── fonts/
│   ├── DejaVuSans.ttf           # Шрифт для PDF
│   └── DejaVuSans-Bold.ttf
│
├── logs/                        # Логи (НЕ в git)
│   ├── bot.log
│   └── errors.log
│
├── exports/                     # Сгенерированные PDF (НЕ в git)
│
├── database/
│   └── __init__.py              # Модели SQLAlchemy
│
├── handlers/
│   ├── router.py                # Маршрутизация команд
│   ├── onboarding.py            # Онбординг пользователя
│   ├── faq.py                   # FAQ
│   ├── admin.py                 # Админские команды
│   ├── food/                    # Работа с едой
│   │   ├── search.py            # Поиск продуктов
│   │   ├── custom.py            # Свои продукты
│   │   ├── log.py               # Дневник питания
│   │   └── products.py          # Выбор даты
│   ├── stats/                   # Статистика
│   │   ├── daily.py             # Дневная статистика
│   │   └── users.py             # Пользователи
│   └── export/                  # Экспорт
│       └── pdf_generator.py     # Генерация PDF
│
├── keyboards/
│   └── keyboards.py             # Все клавиатуры
│
└── utils/
    ├── messenger.py             # Отправка сообщений
    ├── calculator.py            # Расчёт нормы КБЖУ
    └── logger.py                # Логирование
```

## 🔐 Безопасность

### Что НЕ должно попасть в git

Проверьте `.gitignore`:

```gitignore
# База данных
*.db
*.sqlite
*.sqlite3

# Конфигурация с секретами
config.py
.env

# Виртуальное окружение
venv/
env/

# Логи
logs/
*.log

# Экспортированные PDF
exports/

# Python
__pycache__/
*.pyc
*.pyo

# IDE
.vscode/
.idea/
```

### Если БД случайно попала в git

```bash
git rm --cached kbju_bot.db
git commit -m "Убираем БД из git"
git push
```

## 🚀 Деплой на VPS

### 1. Подготовка сервера

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git
```

### 2. Клонирование и настройка

```bash
cd /var/www
git clone https://github.com/your-username/calorieBot.git
cd calorieBot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Создание systemd-сервиса

```bash
sudo nano /etc/systemd/system/caloriebot.service
```

```ini
[Unit]
Description=Calorie Bot
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/calorieBot
ExecStart=/var/www/calorieBot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4. Запуск

```bash
sudo systemctl daemon-reload
sudo systemctl enable caloriebot
sudo systemctl start caloriebot
sudo systemctl status caloriebot
```

### 5. Автоматические бэкапы БД

Создайте скрипт `/var/www/calorieBot/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/calorieBot"
mkdir -p $BACKUP_DIR
cp /var/www/calorieBot/kbju_bot.db $BACKUP_DIR/kbju_bot.db.$(date +%Y%m%d_%H%M%S)
find $BACKUP_DIR -name "kbju_bot.db.*" -mtime +7 -delete
```

Добавьте в crontab (`crontab -e`):

```bash
0 3 * * * /var/www/calorieBot/backup.sh
```

## 📊 Обновление бота

```bash
# 1. Остановить бота
sudo systemctl stop caloriebot

# 2. Бэкап БД (ОБЯЗАТЕЛЬНО!)
cp kbju_bot.db kbju_bot.db.backup_$(date +%Y%m%d)

# 3. Обновить код
git pull

# 4. Установить новые зависимости (если есть)
source venv/bin/activate
pip install -r requirements.txt

# 5. Запустить бота
sudo systemctl start caloriebot
```

⚠️ **Никогда не удаляйте `kbju_bot.db` при обновлении!**

## 🧪 Тестирование

После внесения изменений проверьте:

- [ ] Кнопка "Начать" при первом запуске
- [ ] Дисклеймер о конфиденциальности
- [ ] Онбординг (возраст от 18 лет)
- [ ] Добавление еды из базы
- [ ] Добавление своего продукта с подтверждением КБЖУ
- [ ] Удаление записи из дневника
- [ ] Удаление своего продукта через настройки
- [ ] Экспорт PDF за день и за период
- [ ] Сброс профиля через настройки с подтверждением
- [ ] Блокировка функций без настроенного профиля
- [ ] Отображение "Превышение" вместо отрицательного "Осталось"
- [ ] Логи в `logs/bot.log`

## 📝 Лицензия

MIT License

## 🤝 Поддержка

Если нашли ошибку или есть предложения — создайте Issue в репозитории.