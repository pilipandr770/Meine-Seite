# Руководство по деплою на Render.com

## Первоначальная настройка

1. Зарегистрируйтесь в [Render.com](https://render.com/)
2. Соедините ваш GitHub репозиторий с Render
3. Создайте новый Web Service, выбрав репозиторий
4. Укажите основные настройки:
   - Name: rozoom-web-app
   - Runtime: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python init_database.py && gunicorn "run:app"`
   - Plan: Free (или другой по необходимости)

## Настройка переменных окружения

В дашборде Render.com добавьте следующие переменные окружения:

```
FLASK_APP=run.py
FLASK_DEBUG=0
POSTGRES_SCHEMA=rozoom_schema
ENVIRONMENT=production
SECRET_KEY=(генерируется автоматически)
TELEGRAM_BOT_TOKEN=ваш_токен_бота
TELEGRAM_CHAT_ID=ваш_id_чата
OPENAI_API_KEY=ваш_ключ_openai
```

## Настройка базы данных

1. Создайте новую базу данных PostgreSQL на Render
2. Скопируйте строку подключения (DATABASE_URL) в переменные окружения вашего веб-сервиса

## Автоматический деплой

После настройки каждый push в главную ветку вашего репозитория автоматически запустит деплой на Render.

## Проверка и отладка

- Мониторинг: Используйте секцию "Logs" на дашборде Render
- Ошибки: Проверьте логи на наличие сообщений об ошибках
- Статус: Убедитесь, что сервис имеет статус "Live"

## Получение Telegram ID

1. Начните диалог с @userinfobot в Telegram
2. Бот отправит ваш Telegram ID, который нужно использовать в переменной TELEGRAM_CHAT_ID

## Создание Telegram бота

1. Начните диалог с @BotFather в Telegram
2. Отправьте команду /newbot и следуйте инструкциям
3. Получите токен бота и используйте его в TELEGRAM_BOT_TOKEN
