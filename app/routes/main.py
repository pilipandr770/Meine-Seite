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


@main_bp.route('/index')
def index():
    """Alias endpoint so url_for('main.index') works across the codebase."""
    return home()

@main_bp.route('/set_language/<lang>')
def set_language(lang):
    """Set language preference and redirect back to current page"""
    if lang in ['uk', 'de', 'en']:
        session['lang'] = lang
        session.modified = True  # Force session save
        print(f"Language set to: {lang}")  # Debug logging
    
    # Get the redirect URL from query parameter or referrer
    redirect_url = request.args.get('redirect')
    print(f"Redirect parameter: {redirect_url}")  # Debug logging
    
    if redirect_url:
        print(f"Redirecting to parameter: {redirect_url}")
        return redirect(redirect_url)
    
    # Fallback to referrer
    referrer = request.referrer
    print(f"Referrer: {referrer}")  # Debug logging
    
    if referrer and request.host in referrer:
        print(f"Redirecting to referrer: {referrer}")
        return redirect(referrer)
    else:
        print("Redirecting to home")
        return redirect(url_for('main.home'))
