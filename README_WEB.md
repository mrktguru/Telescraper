# Telegram Parser - Web Interface 🚀

Веб-интерфейс для парсинга комментариев из Telegram каналов с фильтрацией по ключевым словам.

## Возможности

### ✨ Основной функционал
- 🌐 **Веб-интерфейс** - удобный интерфейс на Bootstrap 5
- 🔐 **Аутентификация** - регистрация и вход по email
- 🚀 **Асинхронный парсинг** - задачи выполняются в фоне
- 📊 **Прогресс в реальном времени** - отслеживание процесса парсинга
- 🔍 **Фильтрация по ключевым словам** - с морфологией русского языка
- 📝 **История запусков** - все результаты сохраняются
- 💾 **Экспорт** - CSV и JSON форматы
- 📈 **Статистика** - детальная информация по каждому запуску

### 🎯 Фильтрация по ключевым словам

**Особенности:**
- Поддержка русской морфологии (pymorphy2)
- Автоматический поиск всех форм слова
- Два режима: "ИЛИ" (любое слово) и "И" (все слова)

**Пример:**
```
Ключевое слово: "купить"
Найдёт: купить, куплю, купил, купила, купят, куплен...
```

## Архитектура

```
┌─────────────────────────────────────────┐
│  Frontend (Bootstrap 5 + JavaScript)    │
│  - Responsive UI                        │
│  - Real-time progress updates           │
│  - AJAX for async operations            │
└──────────────┬──────────────────────────┘
               │ HTTP/JSON
┌──────────────┴──────────────────────────┐
│  Flask Web Application (web_app.py)     │
│  - Routes and API endpoints             │
│  - User authentication (Flask-Login)    │
│  - Task management                      │
└──────────────┬──────────────────────────┘
               │
┌──────────────┴──────────────────────────┐
│  Background Workers (Threading)         │
│  - Async task execution                 │
│  - Progress tracking                    │
└──────────────┬──────────────────────────┘
               │
┌──────────────┴──────────────────────────┐
│  Parser Library (parser_lib.py)         │
│  - Telethon integration                 │
│  - Comment extraction                   │
│  - Keyword filtering (pymorphy2)        │
└──────────────┬──────────────────────────┘
               │
┌──────────────┴──────────────────────────┐
│  SQLite Database (database.py)          │
│  - Users table                          │
│  - Tasks table                          │
│  - Results storage                      │
└─────────────────────────────────────────┘
```

## Структура проекта

```
Telescraper/
├── parser.py              # CLI интерфейс
├── parser_lib.py          # Библиотека парсинга
├── web_app.py             # Flask приложение
├── database.py            # Модели БД
├── requirements.txt       # CLI зависимости
├── requirements_web.txt   # Web зависимости
│
├── templates/             # HTML шаблоны
│   ├── base.html         # Базовый шаблон
│   ├── login.html        # Страница входа
│   ├── register.html     # Регистрация
│   ├── index.html        # Главная (форма парсинга)
│   ├── history.html      # История
│   └── results.html      # Результаты
│
├── static/               # Статические файлы
│   ├── css/
│   │   └── custom.css   # Кастомные стили
│   └── js/
│       └── app.js       # JavaScript
│
├── data/                 # Данные приложения
│   ├── app.db           # SQLite база
│   └── output/          # CSV/JSON файлы
│
└── deployment/           # Конфигурация для деплоя
    ├── nginx.conf       # Nginx конфиг
    ├── tgparser.service # Systemd service
    └── DEPLOY.md        # Инструкции по деплою
```

## Установка и запуск

### Локально (для разработки)

```bash
# 1. Установить зависимости
pip3 install -r requirements_web.txt

# 2. Настроить .env файл
cp .env.example .env
# Добавить Telegram API credentials и SECRET_KEY

# 3. Запустить приложение
python3 web_app.py

# 4. Открыть в браузере
http://localhost:5000
```

### На сервере (production)

См. детальные инструкции в [deployment/DEPLOY.md](deployment/DEPLOY.md)

Краткая версия:
```bash
# 1. Установить зависимости
pip3 install -r requirements_web.txt

# 2. Настроить systemd service
sudo cp deployment/tgparser.service /etc/systemd/system/
sudo systemctl enable tgparser
sudo systemctl start tgparser

# 3. Настроить Nginx
sudo cp deployment/nginx.conf /etc/nginx/sites-available/tgparser.conf
sudo ln -s /etc/nginx/sites-available/tgparser.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 4. Настроить SSL
sudo certbot --nginx -d tgparser.mrktgu.ru
```

## API Endpoints

### Аутентификация
- `GET /login` - Страница входа
- `POST /login` - Вход
- `GET /register` - Страница регистрации
- `POST /register` - Регистрация
- `GET /logout` - Выход

### Парсинг
- `GET /` - Главная страница (форма парсинга)
- `POST /api/parse` - Запустить парсинг
- `GET /api/status/<task_id>` - Получить статус задачи
- `GET /api/results/<task_id>` - Получить результаты

### История и результаты
- `GET /history` - История запусков
- `GET /results/<task_id>` - Просмотр результатов
- `GET /download/<task_id>.csv` - Скачать CSV
- `GET /download/<task_id>.json` - Скачать JSON
- `DELETE /api/task/<task_id>` - Удалить задачу

## Использование

### 1. Регистрация
- Откройте `/register`
- Введите email и пароль
- Нажмите "Зарегистрироваться"

### 2. Запуск парсинга
- Откройте главную страницу
- Введите URL канала (например: `https://t.me/okkosport`)
- Выберите количество постов
- (Опционально) Введите ключевые слова через запятую
- Выберите режим фильтрации: "ИЛИ" или "И"
- Нажмите "Начать парсинг"

### 3. Отслеживание прогресса
- Прогресс-бар показывает процесс выполнения
- Обновляется автоматически каждые 2 секунды

### 4. Просмотр результатов
- После завершения появится статистика
- Кнопки для скачивания CSV/JSON
- Кнопка "Посмотреть результаты" для детального просмотра

### 5. История
- В разделе "История" все прошлые запуски
- Можно скачать результаты или удалить задачи

## Особенности реализации

### Фоновые задачи
- Используется threading для асинхронного выполнения
- Задачи не блокируют веб-сервер
- Прогресс сохраняется в памяти и БД

### Морфология ключевых слов
```python
# Пример работы фильтрации
keywords = ["купить", "продать"]
mode = "or"  # или "and"

# Система найдёт все формы:
# купить → куплю, купил, купила, купят...
# продать → продам, продал, продали...
```

### База данных
**Users:**
- id, email, password_hash, created_at

**Tasks:**
- id, user_id, channel_url, posts_limit
- keywords, keyword_mode
- status, progress, result_json
- created_at, completed_at

## CLI vs Web

Оба интерфейса используют одну библиотеку (`parser_lib.py`):

**CLI (parser.py):**
```bash
python3 parser.py --channel https://t.me/channel --keywords "купить" --posts 50
```

**Web:**
- Удобный визуальный интерфейс
- История запусков
- Аутентификация
- Фоновое выполнение

Оба работают параллельно!

## Безопасность

- ✅ Хеширование паролей (Werkzeug)
- ✅ Flask-Login для сессий
- ✅ CSRF защита (Flask)
- ✅ SQL injection защита (параметризованные запросы)
- ✅ XSS защита (Jinja2 auto-escaping)
- ⚠️ Для production: настроить HTTPS, firewall, fail2ban

## Производительность

- Threading для фоновых задач
- Gunicorn с несколькими workers
- Nginx для статики и reverse proxy
- SQLite для малых/средних нагрузок
- (Для highload: переход на PostgreSQL + Celery + Redis)

## Мониторинг

### Логи
```bash
# Application logs
sudo journalctl -u tgparser -f

# Nginx access log
sudo tail -f /var/log/nginx/tgparser_access.log

# Nginx error log
sudo tail -f /var/log/nginx/tgparser_error.log
```

### Метрики
- Количество пользователей: `SELECT COUNT(*) FROM users`
- Количество задач: `SELECT COUNT(*) FROM tasks`
- Успешных задач: `SELECT COUNT(*) FROM tasks WHERE status='completed'`

## Roadmap (будущие улучшения)

- [ ] WebSocket для прогресса в реальном времени
- [ ] Планировщик задач (cron)
- [ ] Email уведомления
- [ ] Telegram бот интеграция
- [ ] Экспорт в Excel с форматированием
- [ ] Графики и аналитика
- [ ] API ключи для программного доступа
- [ ] Rate limiting
- [ ] Админ панель

## Troubleshooting

См. раздел "Troubleshooting" в [deployment/DEPLOY.md](deployment/DEPLOY.md)

## Лицензия

MIT

---

**Разработано с ❤️ для парсинга Telegram комментариев**
