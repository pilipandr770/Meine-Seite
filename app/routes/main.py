# routes/main.py

from flask import Blueprint, render_template, request, redirect, url_for, session
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import Config

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    # Default language switched to German ('de')
    lang = session.get("lang", "de")
    default_titles = {"de": "Startseite", "uk": "Головна", "en": "Home"}
    return render_template('index.html', title=default_titles.get(lang, "Startseite"), lang=lang)

@main_bp.route('/set_language/<language>')
def set_language(language):
    if language in Config.SUPPORTED_LANGUAGES:
        session["lang"] = language  # ⬅️ зберігаємо вибір мови в сесію
    return redirect(request.referrer or url_for("main.home"))
