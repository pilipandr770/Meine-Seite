# routes/crm.py

from flask import Blueprint, request, jsonify
from app.models.client import db, Client, ClientRequest
import requests
import logging
from app.models.project import create_project_from_request, APIKey

# Создаем Blueprint для CRM
crm_bp = Blueprint("crm", __name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_telegram_credentials():
    """Получает данные для Telegram из переменных окружения, базы данных или значений по умолчанию"""
    import os
    try:
        # Сначала проверяем переменные окружения (приоритет)
        token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        # Если нет в переменных окружения, проверяем базу данных
        if not token:
            token = APIKey.get_key('telegram_bot_token')
        if not chat_id:
            chat_id = APIKey.get_key('telegram_chat_id')
        
        # Используем значения по умолчанию, если нигде не найдены
        if not token:
            token = "7572478553:AAEJxJ9Il80zrHAjcD7ZcQnht3EP-sHYrjs"
            logger.warning("Using default Telegram bot token! Set TELEGRAM_BOT_TOKEN env variable.")
        if not chat_id:
            chat_id = "7444992311"
            logger.warning("Using default Telegram chat ID! Set TELEGRAM_CHAT_ID env variable.")
            
        # Логируем используемые значения для отладки
        logger.info(f"Используем Telegram токен: {token[:5]}...{token[-5:]} и чат ID: {chat_id}")
            
        return token, chat_id
    except Exception as e:
        logger.error(f"Ошибка при получении Telegram-ключей: {e}")
        return "7572478553:AAEJxJ9Il80zrHAjcD7ZcQnht3EP-sHYrjs", "7444992311"

def send_telegram_message(text):
    try:
        token, chat_id = get_telegram_credentials()
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        
        logger.info(f"Отправка сообщения в Telegram на чат ID: {chat_id}")
        response = requests.post(url, data=data, timeout=10)
        
        logger.info(f"Статус ответа от Telegram: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Ошибка отправки в Telegram: {response.text}")
            return False
            
        logger.info("Сообщение успешно отправлено в Telegram")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке в Telegram: {e}")
        return False

# 🔹 Додати нового клієнта (опційно)
@crm_bp.route("/clients", methods=["POST"])
def add_client():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    message = data.get("message", "")

    if not name or not email:
        return jsonify({"error": "Ім'я та email є обов'язковими"}), 400

    new_client = Client(name=name, email=email, message=message)
    db.session.add(new_client)
    db.session.commit()

    return jsonify({"message": "Клієнт доданий", "client": new_client.to_dict()}), 201

# 🔸 Прийом ТЗ
@crm_bp.route("/submit_task", methods=["POST"])
def submit_task():
    data = request.json

    project_type = data.get("project_type")
    project_name = data.get("project_name")
    task_description = data.get("task_description")
    key_features = data.get("key_features")
    design_preferences = data.get("design_preferences")
    platform = data.get("platform")
    budget = data.get("budget")
    timeline = data.get("timeline")
    integrations = data.get("integrations")
    contact_method = data.get("contact_method")
    contact_info = data.get("contact_info", "Анонімно")

    # Валідація
    required_fields = [project_type, project_name, task_description, contact_method]
    if not all(required_fields):
        return jsonify({"error": "Будь ласка, заповніть всі обов'язкові поля."}), 400

    if contact_method.lower() == "анонімно":
        contact_info = None

    # Зберігання в базу
    new_request = ClientRequest(
        project_type=project_type,
        task_description=task_description,
        contact_method=contact_method,
        contact_info=contact_info
    )
    new_request.project_name = project_name
    new_request.key_features = key_features
    new_request.design_preferences = design_preferences
    new_request.platform = platform
    new_request.budget = budget
    new_request.timeline = timeline
    new_request.integrations = integrations

    db.session.add(new_request)
    db.session.commit()

    # Повне повідомлення в Telegram
    message = f"""
📩 <b>Нова заявка на розробку</b>

🔹 <b>Тип проєкту:</b> {project_type}
📛 <b>Назва:</b> {project_name}
📝 <b>Опис:</b> {task_description}
🧩 <b>Функціонал:</b> {key_features}
🎨 <b>Дизайн:</b> {design_preferences}
💻 <b>Платформа:</b> {platform}
💰 <b>Бюджет:</b> {budget}
⏱️ <b>Термін виконання:</b> {timeline}
🔗 <b>Інтеграції:</b> {integrations}

📞 <b>Спосіб зв'язку:</b> {contact_method}
📧 <b>Контакт:</b> {contact_info or "Немає"}

🆔 <b>ID заявки:</b> {new_request.id}
""".strip()

    # Отправляем в Telegram и логируем результат
    telegram_sent = send_telegram_message(message)
    if telegram_sent:
        logger.info(f"Telegram уведомление отправлено для заявки {new_request.id}")
    else:
        logger.warning(f"Не удалось отправить Telegram уведомление для заявки {new_request.id}")

    # Автоматическое создание проекта из ТЗ
    try:
        project = create_project_from_request(new_request)
        if project:
            logger.info(f"Автоматически создан проект {project.id} для заявки {new_request.id}")
            return jsonify({
                "message": "Заявка принята и проект создан", 
                "request": new_request.to_dict(),
                "project_id": project.id
            }), 201
    except Exception as e:
        logger.error(f"Ошибка при автосоздании проекта: {e}")
    
    return jsonify({"message": "Заявка принята", "request": new_request.to_dict()}), 201
