from flask import Blueprint, request, jsonify
from app.models.client import db, Client, ClientRequest
import requests

TELEGRAM_BOT_TOKEN = "7572478553:AAEJxJ9Il80zrHAjcD7ZcQnht3EP-sHYrjs"
TELEGRAM_CHAT_ID = "7444992311"  # Отримати можна через @userinfobot

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, data=data)

crm_bp = Blueprint("crm", __name__)

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

@crm_bp.route("/submit_task", methods=["POST"])
def submit_task():
    data = request.json
    
    # Отримуємо всі дані
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

    # Перевірка обов'язкових полів
    required_fields = [project_type, project_name, task_description, contact_method]
    if not all(required_fields):
        return jsonify({"error": "Будь ласка, заповніть всі обов'язкові поля."}), 400

    # Створюємо новий запис ТЗ
    new_request = ClientRequest(
        project_type=project_type,
        task_description=task_description,
        contact_method=contact_method,
        contact_info=contact_info if contact_method.lower() != "анонімно" else None
    )

    # Додаємо всі додаткові поля
    new_request.project_name = project_name
    new_request.key_features = key_features
    new_request.design_preferences = design_preferences
    new_request.platform = platform
    new_request.budget = budget
    new_request.timeline = timeline
    new_request.integrations = integrations

    # Зберігаємо в базу
    db.session.add(new_request)
    db.session.commit()

    # Відправляємо повідомлення в Telegram
    message = f"📩 <b>Нова заявка</b>\n"
    message += f"🔹 <b>Проєкт:</b> {project_type}\n"
    message += f"📝 <b>Назва:</b> {project_name}\n"
    message += f"📝 <b>Опис:</b> {task_description}\n"
    message += f"📞 <b>Контакт:</b> {contact_info if contact_info != 'Анонімно' else 'Немає'}"
    
    try:
        send_telegram_message(message)
    except Exception as e:
        print(f"Failed to send Telegram notification: {str(e)}")

    return jsonify({"message": "Заявка прийнята", "request": new_request.to_dict()}), 201
