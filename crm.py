from flask import Blueprint, request, jsonify
from app.models.client import db, Client

crm_bp = Blueprint("crm", __name__)

@crm_bp.route("/crm/clients", methods=["POST"])
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

@crm_bp.route("/crm/clients", methods=["GET"])
def get_clients():
    clients = Client.query.all()
    return jsonify([client.to_dict() for client in clients])
