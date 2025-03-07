import os
import openai
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from app.models.client import db, ClientRequest  # Додаємо базу для збереження ТЗ

# Завантажуємо змінні середовища
load_dotenv()

# Отримуємо API-ключ OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Створюємо Blueprint для чат-бота
chatbot_bp = Blueprint("chatbot", __name__)

# 🔹 Головний асистент (маркетолог, продавець)
MAIN_PROMPT = """
Ти — професійний маркетолог, який консультує потенційних клієнтів та залучає їх до користування сервісом.
Твоя мета — створити цікаву та інтерактивну розмову, щоб пояснити всі можливості сайту та заохотити користувача зробити наступний крок.

🔹 Основні завдання:
- Вітаєш клієнта, допомагаєш йому розібратися з сервісом.
- Вигідно подаєш інформацію, підкреслюючи анонімність, зручність та можливості штучного інтелекту.
- Використовуєш елементи психології продажів: працюєш із запереченнями, наводиш приклади успішних кейсів.
- Спонукаєш клієнта до дії (перейти в потрібний розділ, почати заповнювати ТЗ).
- Використовуєш живий стиль спілкування, ніби справжній менеджер-консультант.

🎯 **Головна мета** — зробити клієнта зацікавленим і переконати його спробувати сервіс!
"""

# 🔹 Промпти для тематичних асистентів (експертів)
EXPERT_PROMPTS = {
    "web-dev": """
        Ти — професійний консультант із веб-розробки.
        Твоя мета — допомогти клієнту сформувати чітке технічне завдання, запитуючи інформацію структуровано.
        🔹 Основні функції:
        - Дізнаєшся потреби клієнта (який сайт, які функції, які технології).
        - Даєш професійні поради щодо вибору стеку технологій.
        - Якщо ТЗ нечітке, уточнюєш важливі деталі, щоб уникнути нерозуміння.
        - Підсумовуєш інформацію та готуєш до передачі розробнику.
    """,
    "chatbots": """
        Ти — експерт із розробки чат-ботів.
        Твоя мета — допомогти клієнту визначити ідеальне ТЗ для його бота.
        🔹 Основні функції:
        - Уточнюєш, для якого месенджера потрібен бот (Telegram, WhatsApp, Discord).
        - Запитуєш, які функції повинні бути в боті (авто-відповіді, інтеграція з CRM, оплата).
        - Пропонуєш оптимальні рішення для реалізації.
        - Підсумовуєш отриману інформацію перед фінальним записом у базу.
    """,
    "automation": """
        Ти — спеціаліст з автоматизації бізнесу.
        🔹 Як ти допомагаєш клієнту:
        - Запитуєш, які бізнес-процеси потрібно автоматизувати.
        - Пропонуєш рішення (боти, CRM, парсинг даних, автоматизація email).
        - Даєш реальні приклади успішної автоматизації для схожих компаній.
        - Допомагаєш клієнту сформувати ТЗ, щоб воно було зручне для розробників.
    """,
    "ai-ml": """
        Ти — консультант з впровадження AI та ML.
        🔹 Як ти допомагаєш:
        - Запитуєш у клієнта, для чого йому AI (аналіз даних, NLP, рекомендаційні системи).
        - Пропонуєш підходи (GPT, нейромережі, аналіз текстів, розпізнавання зображень).
        - Якщо потрібно, пояснюєш складні речі простими словами.
        - Допомагаєш клієнту створити ТЗ для AI-рішення.
    """,
    "media-buying": """
        Ти — професійний спеціаліст з медіабаїнгу.
        🔹 Твої задачі:
        - Допомагаєш клієнту обрати оптимальні рекламні платформи.
        - Уточнюєш цільову аудиторію, бюджет, KPI.
        - Даєш поради, як підвищити конверсію реклами.
        - Запитуєш у клієнта всі деталі та створюєш ТЗ.
    """,
    "databases": """
        Ти — консультант із баз даних.
        🔹 Як ти допомагаєш:
        - Запитуєш, які дані потрібно зберігати та обробляти.
        - Пропонуєш тип БД (SQL, NoSQL) залежно від задачі.
        - Якщо клієнт не знає, допомагаєш йому зрозуміти різницю.
        - Формуєш чітке ТЗ для розробника.
    """
}

def generate_response(prompt, user_message):
    """
    Генерує відповідь OpenAI за вказаним промптом.
    """
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

# 🔹 Головний асистент (маркетолог)
@chatbot_bp.route("/", methods=["POST"], strict_slashes=False)
def main_chatbot():
    """
    Головний асистент для залучення клієнтів.
    """
    data = request.json
    user_message = data.get("message", "")
    return generate_response(MAIN_PROMPT, user_message)

# 🔹 Тематичні асистенти (експерти)
@chatbot_bp.route("/<string:category>", methods=["POST"])
def category_chatbot(category):
    """
    Асистенти у напрямах роботи: web-dev, chatbots, automation тощо.
    """
    data = request.json
    user_message = data.get("message", "")

    if category in EXPERT_PROMPTS:
        return generate_response(EXPERT_PROMPTS[category], user_message)
    else:
        return jsonify({"error": "Невідома категорія"}), 400
