# routes/chatbot.py

import os
import logging
import traceback
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI

# Fix import paths
import sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
from app.models.client import db, ClientRequest

# Fix expert_data import
try:
    from expert_data import EXPERT_DATA
except ImportError:
    # Try relative import as fallback
    from ..expert_data import EXPERT_DATA

# Завантаження змінних середовища
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load system instructions
def load_system_instructions(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logging.error(f"Error loading system instructions from {file_path}: {str(e)}")
        return None

# Paths to system instructions
MAIN_ASSISTANT_INSTRUCTIONS_PATH = os.path.join(parent_dir, 'system_instructions', 'main_assistant_instructions.md')

# Simple in-memory cache for system instructions to avoid repeated disk IO
_system_instruction_cache = {}

def get_system_instructions_cached(path: str):
    from time import time
    cache_entry = _system_instruction_cache.get(path)
    if cache_entry and (time() - cache_entry['ts'] < 300):  # 5 min TTL
        return cache_entry['content']
    content = load_system_instructions(path)
    if content:
        _system_instruction_cache[path] = {'content': content, 'ts': time()}
    return content

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
    use_chat_completion = os.getenv("USE_CHAT_COMPLETION", "false").lower() == "true"

    if not user_message:
        return jsonify({"error": "Порожнє повідомлення"}), 400

    try:
        # If we have a valid assistant ID and are not using chat completion, use the Assistants API
        if assistant_id and not use_chat_completion:
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
        
        # Fallback to Chat Completion API if assistant ID is not available or we've configured to use chat completion
        else:
            logger.info("Using Chat Completion API instead of Assistants API")
            
            # Load the detailed system instructions for the main assistant
            system_message = get_system_instructions_cached(MAIN_ASSISTANT_INSTRUCTIONS_PATH)
            
            # Fallback if instructions can't be loaded
            if not system_message:
                system_message = "Ви професійний асистент сайту Rozoom. Допомагайте користувачам з їхніми запитаннями."
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini which your API key has access to
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7
            )
            
            return jsonify({"response": response.choices[0].message.content})
    except Exception as e:
        logger.exception("Помилка у головному асистенті")
        return jsonify({"error": str(e)}), 500


# 🔹 Тематичні асистенти (експерти за напрямами)
@chatbot_bp.route("/<string:category>", methods=["POST"])
def category_chatbot(category):
    data = request.get_json()
    print("📥 Запит JSON:", request.data)  # Debug: вміст запиту
    print("📥 Заголовки:", request.headers)  # Debug: заголовки запиту
    if not data or "message" not in data:
        return jsonify({"error": "Немає тексту повідомлення"}), 400

    user_message = data["message"]
    expert_info = EXPERT_DATA.get(category)
    if not expert_info:
        return jsonify({"error": "Невідома категорія"}), 400

    assistant_id = expert_info.get("assistant_id") or os.getenv("TASK_ASSISTANT_ID")
    use_chat_completion = os.getenv("USE_CHAT_COMPLETION", "false").lower() == "true"

    try:
        # If we have a valid assistant ID and are not using chat completion, use the Assistants API
        if assistant_id and not use_chat_completion:
            thread = client.beta.threads.create()

            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"Користувач зараз у розділі '{category}' і хоче сформувати ТЗ. Врахуй це."
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
        
        # Fallback to Chat Completion API if assistant ID is not available or we've configured to use chat completion
        else:
            logger.info(f"Using Chat Completion API instead of Assistants API for category {category}")
            category_name = expert_info.get("name", category)
            
            # Try to load category-specific instructions
            category_instructions_path = os.path.join(parent_dir, 'system_instructions', 'expert_instructions', f'{category}.md')
            system_message = get_system_instructions_cached(category_instructions_path)
            if not system_message:
                # Generic fallback for TЗ structuring
                generic_tz_path = os.path.join(parent_dir, 'system_instructions', 'expert_instructions', '_tz_assistant.md')
                system_message = get_system_instructions_cached(generic_tz_path)
            
            # Fallback if category-specific instructions can't be loaded
            if not system_message:
                system_message = f"Ви експерт у сфері {category_name}. Користувач зараз у розділі '{category}' і хоче сформувати ТЗ. Допоможіть йому створити детальне технічне завдання на основі його запиту."
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini which your API key has access to
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7
            )
            
            return jsonify({"response": response.choices[0].message.content})
    except Exception as e:
        logger.exception(f"Помилка у асистенті категорії {category}")
        return jsonify({"error": str(e)}), 500


# 🔹 Обробка голосових повідомлень
@chatbot_bp.route("/voice", methods=["POST"])
def voice_chatbot():
    assistant_id = os.getenv("MAIN_ASSISTANT_ID")
    use_chat_completion = os.getenv("USE_CHAT_COMPLETION", "false").lower() == "true"
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

        # If we have a valid assistant ID and are not using chat completion, use the Assistants API
        if assistant_id and not use_chat_completion:
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
        
        # Fallback to Chat Completion API if assistant ID is not available or we've configured to use chat completion
        else:
            logger.info("Using Chat Completion API instead of Assistants API for voice message")
            system_message = "Ви професійний асистент, який відповідає на голосові запити користувачів. Дайте чітку та корисну відповідь на запит користувача."
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini which your API key has access to
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": transcription}
                ],
                temperature=0.7
            )
            
            return jsonify({"transcription": transcription, "response": response.choices[0].message.content})

    except Exception as e:
        print("🔥 Внутрішня помилка:", traceback.format_exc())
        return jsonify({"error": str(e)}), 500
