# routes/chatbot.py

import os
import logging
import traceback
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
from app.models.client import db, ClientRequest
from app.expert_data import EXPERT_DATA

# Завантаження змінних середовища
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

chatbot_bp = Blueprint("chatbot", __name__)

# Налаштування логування
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 🔹 Головний асистент (на головній сторінці)
@chatbot_bp.route("/", methods=["POST"])
def main_chatbot():
    data = request.json
    user_message = data.get("message", "")
    assistant_id = os.getenv("MAIN_ASSISTANT_ID")

    if not user_message:
        return jsonify({"error": "Порожнє повідомлення"}), 400

    try:
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(thread_id=thread.id, role="user", content=user_message)
        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)

        while True:
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run.status == "completed":
                break
            elif run.status == "failed":
                return jsonify({"error": "Асистент не зміг відповісти"}), 500

        messages = client.beta.threads.messages.list(thread_id=thread.id)
        last_message = messages.data[0].content[0].text.value
        return jsonify({"response": last_message})
    except Exception as e:
        logger.exception("Помилка у головному асистенті")
        return jsonify({"error": str(e)}), 500


# 🔹 Тематичні асистенти (експерти за напрямами)
@chatbot_bp.route("/<string:category>", methods=["POST"])
def category_chatbot(category):
    data = request.json
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "Порожнє повідомлення"}), 400

    expert_info = EXPERT_DATA.get(category)
    if not expert_info:
        return jsonify({"error": "Невідома категорія"}), 400

    assistant_id = expert_info.get("assistant_id") or os.getenv("TASK_ASSISTANT_ID")

    try:
        thread = client.beta.threads.create()

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Користувач зараз перебуває у розділі '{category}' і хоче сформувати технічне завдання. Врахуй це при відповіді."
        )

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_message
        )

        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)

        while True:
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run.status == "completed":
                break
            elif run.status == "failed":
                return jsonify({"error": "Асистент не зміг відповісти"}), 500

        messages = client.beta.threads.messages.list(thread_id=thread.id)
        last_message = messages.data[0].content[0].text.value
        return jsonify({"response": last_message})
    except Exception as e:
        logger.exception(f"Помилка у асистенті категорії {category}")
        return jsonify({"error": str(e)}), 500


# 🔹 Обробка голосових повідомлень
@chatbot_bp.route("/voice", methods=["POST"])
def voice_chatbot():
    assistant_id = os.getenv("MAIN_ASSISTANT_ID")
    audio_file = request.files.get("audio")

    if not audio_file:
        return jsonify({"error": "Немає аудіофайлу"}), 400

    try:
        print("📥 Отримано файл:", audio_file.filename)
        print("📦 MIME:", audio_file.mimetype)

        try:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=(audio_file.filename, audio_file.stream, audio_file.mimetype),
                response_format="text"
            )
        except Exception as exc:
            if "whisper-1" in str(exc):
                return jsonify({"error": "Ваш проект не має доступу до моделі 'whisper-1'. Перевірте налаштування API ключа."}), 403
            raise exc

        print("📝 Транскрипція:", transcription)

        thread = client.beta.threads.create()
        client.beta.threads.messages.create(thread_id=thread.id, role="user", content=transcription)
        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)

        while True:
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run.status == "completed":
                break
            elif run.status == "failed":
                return jsonify({"error": "Асистент не зміг відповісти"}), 500

        messages = client.beta.threads.messages.list(thread_id=thread.id)
        last_message = messages.data[0].content[0].text.value

        return jsonify({"transcription": transcription, "response": last_message})

    except Exception as e:
        print("🔥 Внутрішня помилка:", traceback.format_exc())
        return jsonify({"error": str(e)}), 500
