from flask import Blueprint, request, jsonify
from app.models.client import db, Client, ClientRequest

crm_bp = Blueprint("crm", __name__)

# Додавання клієнта в базу (цей маршрут залишимо для зручності, якщо ти будеш його використовувати)
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

# Виправлений маршрут для збереження ТЗ
@crm_bp.route("/submit_task", methods=["POST"])
def submit_task():
    data = request.json
    
    # Отримуємо всі дані, які передаються формою
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
    contact_info = data.get("contact_info")

    # Перевірка обов'язкових полів
    required_fields = [project_type, project_name, task_description, contact_method]
    if not all(required_fields):
        return jsonify({"error": "Будь ласка, заповніть всі обов'язкові поля."}), 400

    # Видаляємо контактну інформацію, якщо анонімно
    if contact_method.lower() == "анонімно":
        contact_info = None

    # Створюємо новий запис ТЗ
    new_request = ClientRequest(
        project_type=project_type,
        task_description=task_description,
        contact_method=contact_method,
        contact_info=contact_info
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

    return jsonify({"message": "Заявка прийнята", "request": new_request.to_dict()}), 201
