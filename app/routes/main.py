from flask import Blueprint, render_template, request, redirect, url_for, session
from app.config import Config


main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    lang = session.get("lang", "uk")  # Отримуємо поточну мову (за замовчуванням українська)
    return render_template('index.html', title="Головна", lang=lang)

@main_bp.route('/set_language/<language>')
def set_language(language):
    if language in Config.SUPPORTED_LANGUAGES:
        session["lang"] = language  # Зберігаємо вибір мови в сесії
    return redirect(request.referrer or url_for("main.home"))  # Повертаємо на попередню сторінку
