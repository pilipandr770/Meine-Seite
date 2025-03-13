import os
import openai
import logging
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from app.models.client import db, ClientRequest
from app.expert_data import EXPERT_DATA  # 🔹 Додаємо експертний досвід
from werkzeug.utils import secure_filename  # <-- added import

# Завантажуємо змінні середовища
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

chatbot_bp = Blueprint("chatbot", __name__)

# Налаштовуємо логування
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

UPLOAD_FOLDER = "temp_audio"  # New: Directory for temporary audio files
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🔹 Головний асистент (маркетолог і представник компанії)
MAIN_PROMPT = """
Вітаю! Я — віртуальний асистент Andrii Pylypchuk,  
який допоможе вам розібратися у світі IT, автоматизації та штучного інтелекту.

📌 **Хто я та чому вам вигідно працювати з Andrii Pylypchuk?**  
- Я працюю як **ІТ-консультант та проєкт-менеджер**, допомагаючи клієнтам структурувати їхні ідеї.  
- Andrii Pylypchuk — **досвідчений розробник з 20-річним стажем** у Python та AI.  
- Ми допомагаємо бізнесам створювати **ефективні цифрові рішення** з використанням OpenAI.  

Якщо ви хочете дізнатися, як ваш бізнес може **автоматизувати роботу, залучати більше клієнтів та зменшувати витрати** —  
я із задоволенням вам допоможу!  
"""

# 🔹 Функція для отримання промпту асистента
def get_expert_prompt(category):
    # If category is not defined in EXPERT_DATA, fall back to MAIN_PROMPT
    if category not in EXPERT_DATA:
        print(f"Category '{category}' not found in expert data. Using MAIN_PROMPT fallback.")
        return MAIN_PROMPT

    data = EXPERT_DATA[category]
    experience_text = "\n".join([f"- {exp}" for exp in data["experience"]])
    return f"""
        {data['marketing']}

        🔹 **Моя роль як ІТ-консультанта та проєкт-менеджера:**
        - Допомагати клієнтам сформувати чітке технічне завдання.
        - Пропонувати рішення, що підходять для конкретного бізнесу.
        - Розбивати складні ідеї на прості кроки, щоб їх було легко реалізувати.

        🔹 **Що ми можемо зробити:**
        {experience_text}

        📌 Давайте обговоримо ваш проєкт! Я тут, щоб допомогти вам знайти найкраще рішення.
    """

# 🔹 Генерація відповіді OpenAI
def generate_response(prompt, user_message):
    if not user_message:
        return jsonify({"error": "Порожнє повідомлення"}), 400

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": user_message}]
        )
        bot_reply = response.choices[0].message.content
        return jsonify({"response": bot_reply})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# 🔹 Головний маркетинговий асистент (відповідає за загальні питання)
@chatbot_bp.route("/", methods=["POST"])
def main_chatbot():
    data = request.json
    user_message = data.get("message", "")
    return generate_response(MAIN_PROMPT, user_message)

# 🔹 Тематичні асистенти (експерти у своїх напрямах)
@chatbot_bp.route("/<string:category>", methods=["POST"])
def category_chatbot(category):
    data = request.json
    print("Received payload:", data)  # Log the request payload
    user_message = data.get("message", "")

    expert_prompt = get_expert_prompt(category)
    if not expert_prompt:
        return jsonify({"error": "Невідома категорія"}), 400

    return generate_response(expert_prompt, user_message)

@chatbot_bp.route("/voice", methods=["POST"])
def voice_chat():
    if "audio" not in request.files:
        print("❌ Файл не отримано!")
        return jsonify({"error": "Файл не знайдено"}), 400

    audio_file = request.files["audio"]
    filename = secure_filename(audio_file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    audio_file.save(file_path)
    print(f"✅ Отримано файл: {file_path}")

    try:
        # Використовуємо Whisper для розпізнавання голосу
        with open(file_path, "rb") as file:
            transcription = openai.Audio.transcribe("whisper-1", file)
        os.remove(file_path)  # Видаляємо файл після обробки
        user_message = transcription["text"].strip()
        print(f"✅ Whisper розпізнав: {user_message}")

        if not user_message:
            return jsonify({"error": "Не вдалося розпізнати голос"}), 400

        # GPT-4 генерує відповідь
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Розпізнано голосове повідомлення:"},
                {"role": "user", "content": user_message}
            ]
        )
        bot_reply = response.choices[0].message.content
        print(f"✅ GPT-4 відповів: {bot_reply}")

        return jsonify({"transcription": user_message, "response": bot_reply})

    except Exception as e:
        print("❌ Помилка у Flask:", str(e))
        return jsonify({"error": str(e)}), 500
