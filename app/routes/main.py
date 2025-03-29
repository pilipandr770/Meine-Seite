# routes/main.py

from flask import Blueprint, render_template, request, redirect, url_for, session
from app.config import Config

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    lang = session.get("lang", "uk")  # ⬅️ зчитуємо з session (як на інших сторінках)
    return render_template('index.html', title="Головна", lang=lang)

@main_bp.route('/set_language/<language>')
def set_language(language):
    if language in Config.SUPPORTED_LANGUAGES:
        session["lang"] = language  # ⬅️ зберігаємо вибір мови в сесію
    return redirect(request.referrer or url_for("main.home"))
