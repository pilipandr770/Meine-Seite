"""Centralized i18n utilities.
Add new translation keys here. Keep keys semantic and lower_snake_case.
"""
from flask import session

translations = {
    # Shop landing (single product hours)
    'development_hours_title': {
        'en': 'Development / Consulting Hours',
        'de': 'Entwicklungsstunden / Consulting',
        'uk': 'Години розробки / Консалтингу'
    },
    'development_hours_subtitle': {
        'en': 'Purchase service hours to work on your project',
        'de': 'Kaufen Sie Service‑Stunden für Ihr Projekt',
        'uk': 'Придбайте години послуг для роботи над вашим проєктом'
    },
    'order': {'en': 'Order', 'de': 'Bestellen', 'uk': 'Замовити'},
    'details': {'en': 'Details', 'de': 'Details', 'uk': 'Деталі'},
    'cart': {'en': 'Cart', 'de': 'Warenkorb', 'uk': 'Кошик'},
    'product_not_available': {'en': 'Product not available', 'de': 'Produkt nicht verfügbar', 'uk': 'Товар відсутній'},
    # Generic commerce
    'price': {'en': 'Price', 'de': 'Preis', 'uk': 'Ціна'},
    'quantity': {'en': 'Quantity', 'de': 'Menge', 'uk': 'Кількість'},
    'add_to_cart': {'en': 'Add to Cart', 'de': 'In den Warenkorb', 'uk': 'Додати до кошика'},
    'checkout': {'en': 'Checkout', 'de': 'Zur Kasse', 'uk': 'Оформлення замовлення'},
    'subtotal': {'en': 'Subtotal', 'de': 'Zwischensumme', 'uk': 'Підсумок'},
    'discount': {'en': 'Discount', 'de': 'Rabatt', 'uk': 'Знижка'},
    'tax': {'en': 'Tax', 'de': 'MwSt', 'uk': 'Податок'},
    'total': {'en': 'Total', 'de': 'Gesamtsumme', 'uk': 'Загальна сума'},
    # Navigation/account
    'profile': {'en': 'Profile', 'de': 'Profil', 'uk': 'Профіль'},
    'dashboard': {'en': 'Dashboard', 'de': 'Dashboard', 'uk': 'Панель'},
    'projects': {'en': 'Projects', 'de': 'Projekte', 'uk': 'Проєкти'},
    'logout': {'en': 'Logout', 'de': 'Abmelden', 'uk': 'Вийти'},
    'login': {'en': 'Login', 'de': 'Anmelden', 'uk': 'Увійти'},
}

SUPPORTED_LANGS = ('en', 'de', 'uk')
DEFAULT_LANG = 'de'

def translate(key: str, lang: str | None = None):
    if lang is None:
        lang = session.get('lang', DEFAULT_LANG)
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG
    entry = translations.get(key)
    if not entry:
        return key  # fallback displays key name
    return entry.get(lang) or entry.get(DEFAULT_LANG) or next(iter(entry.values()))

def register_i18n(app):
    # Jinja global function t('key')
    app.jinja_env.globals['t'] = translate
    # Provide current language globally
    @app.context_processor
    def inject_lang():
        return {'lang': session.get('lang', DEFAULT_LANG)}
