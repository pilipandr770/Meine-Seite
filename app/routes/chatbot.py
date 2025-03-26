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
Вітаю! Я — ваш персональний цифровий асистент, що представляє компанію Andrii Pylypchuk.

📌 **Що я можу для вас зробити?**
- Пояснити, як працює сайт та які можливості він надає.
- Розповісти про послуги: веб-розробка, чат-боти, автоматизація, AI, медіабаїнг, бази даних.
- Допомогти знайти потрібний розділ або напрямок.
- Підказати, як краще спланувати роботу над вашим проєктом.

🔹 **Як це працює?**
1️⃣ **Оберіть напрямок роботи** – натисніть на розділ, який вас цікавить.
2️⃣ **Поспілкуйтеся з нашим експертним асистентом** – у кожному розділі є спеціалізований AI, який допоможе вам скласти ТЗ.
3️⃣ **Оформіть заявку** – після уточнення всіх деталей ви можете залишити заявку та отримати консультацію.

📢 **Розкажіть, що вас цікавить, і я допоможу вам знайти найкраще рішення!**
"""

# 🔹 Функція для отримання промпту асистента

def get_expert_prompt(category):
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
