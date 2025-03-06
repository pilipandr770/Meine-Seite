import os
import openai
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv

# Завантажуємо змінні середовища
load_dotenv()

# Отримуємо API-ключ OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Створюємо Blueprint для чат-бота
chatbot_bp = Blueprint("chatbot", __name__)

# Додаємо системний промпт
SYSTEM_PROMPT = """
Ти — розумний помічник для IT-фахівця. Відповідай професійно, коротко та по суті.
Можеш допомогти з питаннями щодо веб-розробки, Python, Flask, Docker, AI та автоматизації бізнесу.
"""

@chatbot_bp.route("/", methods=["POST"], strict_slashes=False)
def chatbot():
    data = request.json
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "Порожнє повідомлення"}), 400

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
        )
        bot_reply = response.choices[0].message.content
        return jsonify({"response": bot_reply})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
