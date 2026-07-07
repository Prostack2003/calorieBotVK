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
├── .env                         # Переменные окружения
├── backup.sh                    # Скрипт бэкапа БД
│
├── data/
│   └── products.csv             # Начальная база продуктов
│
├── database/
│   ├── __init__.py
│   ├── database.py              # Подключение к БД
│   └── models.py                # Модели SQLAlchemy
│
├── fonts/                       # Шрифты для PDF
│   ├── DejaVuSans.ttf
│   ├── DejaVuSans-Bold.ttf
│   └── ...
│
├── logs/                        # Логи (НЕ в git)
│
├── exports/                     # Сгенерированные PDF (НЕ в git)
│
├── handlers/
│   ├── router.py                # Главный диспетчер команд
│   ├── onboarding.py            # Онбординг пользователя
│   ├── faq.py                   # FAQ
│   │
│   ├── admin/                   # Админские команды
│   │   ├── __init__.py
│   │   ├── auth.py              # Авторизация админа
│   │   ├── daily.py             # Статистика за день
│   │   ├── weekly.py            # Статистика за неделю
│   │   ├── users.py             # Список пользователей
│   │   └── report.py            # Детальный отчёт
│   │
│   ├── export/                  # Экспорт данных
│   │   ├── __init__.py
│   │   └── pdf_generator.py     # Генерация PDF
│   │
│   ├── food/                    # Работа с едой
│   │   ├── __init__.py
│   │   ├── selector.py          # Поиск и выбор продукта
│   │   ├── weight.py            # Ввод веса
│   │   ├── custom_add.py        # Добавление своего продукта
│   │   ├── custom_manage.py     # Управление списком продуктов
│   │   ├── log.py               # Дневник питания
│   │   └── products.py          # Выбор даты
│   │
│   ├── routes/                  # Роутеры по доменам
│   │   ├── __init__.py
│   │   ├── utils.py             # Общие функции
│   │   ├── stats_routes.py      # Статистика и экспорт
│   │   ├── food_routes.py       # Добавление еды
│   │   ├── profile_routes.py    # Профиль и настройки
│   │   └── admin_routes.py      # Админские команды
│   │
│   └── stats/                   # Статистика
│       ├── __init__.py
│       ├── daily.py             # Дневная статистика
│       └── user.py              # Пользователи
│
├── keyboards/                   # Клавиатуры по доменам
│   ├── __init__.py
│   ├── main.py                  # Главная клавиатура
│   ├── navigation.py            # Навигация
│   ├── registration.py          # Онбординг (пол, активность, цель)
│   ├── products.py              # Выбор продукта
│   ├── analytics.py             # Статистика и удаление
│   ├── profile.py               # Настройки и профиль
│   └── confirmation.py          # Подтверждения
│
└── utils/
    ├── __init__.py
    ├── messenger.py             # Отправка сообщений
    ├── calculator.py            # Расчёт нормы КБЖУ
    ├── logger.py                # Логирование
    └── fuzzy_search.py          # Нечёткий поиск продуктов
```

## 🏗️ Архитектурные принципы

Проект следует принципу **разделения ответственности**:

### 1. Роутинг по доменам (`handlers/routes/`)
Главный `router.py` — это тонкий диспетчер, который передаёт команды в специализированные роутеры:
- `stats_routes.py` — статистика, удаление, экспорт PDF
- `food_routes.py` — добавление еды, выбор продуктов
- `profile_routes.py` — профиль, настройки, онбординг
- `admin_routes.py` — админские команды

### 2. Состояния FSM в отдельных файлах (`handlers/food/`)
Каждое состояние конечного автомата — в своём модуле:
- `selector.py` — поиск и выбор продукта (состояния `selecting`, `ask_custom`)
- `weight.py` — ввод веса (состояние `weight`)
- `custom_add.py` — добавление своего продукта (состояния `custom_name`, `custom_kbzhu`, `confirm_custom`)
- `custom_manage.py` — управление списком продуктов (без состояний)

### 3. Клавиатуры по доменам (`keyboards/`)
Все клавиатуры сгруппированы по назначению:
- `navigation.py` — главная навигация
- `registration.py` — онбординг
- `analytics.py` — статистика и удаление
- `profile.py` — настройки и управление профилем
- `confirmation.py` — подтверждения действий

### 4. Чистая бизнес-логика vs UI
Разделение логики и представления:
- `handlers/stats/daily.py` — только получение и форматирование данных
- `handlers/stats/keyboards.py` — только клавиатуры
- `handlers/stats/deletion.py` — только удаление записей

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

### Онбординг и профиль
- [ ] Кнопка "Начать" при первом запуске
- [ ] Дисклеймер о конфиденциальности
- [ ] Онбординг (возраст от 18 лет)
- [ ] Блокировка функций без настроенного профиля
- [ ] Сброс профиля через настройки с подтверждением

### Добавление еды
- [ ] Добавление еды из базы (с весом и без)
- [ ] Добавление своего продукта с подтверждением КБЖУ
- [ ] Выбор даты при добавлении (сегодня / вчера / произвольная)
- [ ] Пропуск выбора даты — добавление за сегодня с явным уведомлением
- [ ] Обработка некорректного веса

### Статистика и экспорт
- [ ] Отображение "Превышение" вместо отрицательного "Осталось"
- [ ] Стабильное форматирование списка продуктов (двухстрочная структура)
- [ ] Экспорт PDF за день
- [ ] Экспорт PDF за произвольный период
- [ ] Удаление записи из дневника

### Мои продукты
- [ ] Удаление своего продукта через настройки
- [ ] Подтверждение удаления с информацией об использовании в дневнике
- [ ] Записи в дневнике сохраняются после удаления продукта из списка

### Прочее
- [ ] Логи в `logs/bot.log`
- [ ] Админские команды (`/stats`, `/users`, `/report`, `/pdf`, `/admin`)

## 📝 Лицензия

MIT License

## 🤝 Поддержка

Если нашли ошибку или есть предложения — создайте Issue в репозитории.