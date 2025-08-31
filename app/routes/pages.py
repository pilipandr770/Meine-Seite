# routes/pages.py
from flask import Blueprint, render_template, session, request, flash, redirect, url_for

pages_bp = Blueprint('pages', __name__)

# Translation helper function
def get_page_text(key, lang=None):
    """Get translated text for page messages"""
    if lang is None:
        lang = session.get("lang", "de")
    
    translations = {
        'message_sent': {
            'uk': 'Повідомлення надіслано успішно.',
            'de': 'Nachricht erfolgreich gesendet.',
            'en': 'Message sent successfully.'
        },
        'send_error': {
            'uk': 'Виникла помилка при надсиланні.',
            'de': 'Beim Senden ist ein Fehler aufgetreten.',
            'en': 'An error occurred while sending.'
        },
        'fill_all_fields': {
            'uk': 'Заповніть усі поля.',
            'de': 'Bitte füllen Sie alle Felder aus.',
            'en': 'Please fill in all fields.'
        }
    }
    
    return translations.get(key, {}).get(lang, translations.get(key, {}).get('en', key))

@pages_bp.route('/privacy')
def privacy():
    lang = session.get("lang", "de")
    titles = {"de": "Datenschutz", "uk": "Політика конфіденційності", "en": "Privacy Policy"}
    return render_template('privacy.html', title=titles.get(lang, 'Datenschutz'), lang=lang)

@pages_bp.route('/impressum')
def impressum():
    lang = session.get("lang", "de")
    return render_template('impressum.html', title="Impressum", lang=lang)

@pages_bp.route('/qr-codes')
def qr_codes():
    lang = session.get("lang", "de")
    title_map = {"uk": "QR-коди", "de": "QR-Codes", "en": "QR Codes"}
    title = title_map.get(lang, "QR-Codes")
    return render_template('qr_codes.html', title=title, lang=lang)

@pages_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    lang = session.get("lang", "de")
    if request.method == 'POST':
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        
        if name and email and message:
            msg = f"📬 <b>Нове повідомлення з контактної форми</b>\n\n" \
                  f"👤 <b>Ім’я:</b> {name}\n" \
                  f"📧 <b>Email:</b> {email}\n" \
                  f"📝 <b>Повідомлення:</b> {message}"
            try:
                send_telegram_message(msg)  # або email
                flash(get_page_text('message_sent'), "success")
            except Exception as e:
                print(f"❌ Не вдалося надіслати повідомлення: {e}")
                flash(get_page_text('send_error'), "error")
        else:
            flash(get_page_text('fill_all_fields'), "error")
        return redirect(url_for("pages.contact"))
    
    return render_template('contact.html', title="Контакти", lang=lang)

services = [
    {
        "name": "web-dev",
        "title": "Веб-розробка",
        "description": "Створення сайтів, веб-додатків, API та інтеграцій.",
        "chat_endpoint": "/chatbot/web-dev",
        "submit_endpoint": "/crm/submit_task"
    },
    {
        "name": "chatbots",
        "title": "Розробка ботів",
        "description": "Створення Telegram, WhatsApp, Discord-ботів для автоматизації бізнесу.",
        "chat_endpoint": "/chatbot/chatbots",
        "submit_endpoint": "/crm/submit_task"
    },
    {
        "name": "automation",
        "title": "Автоматизація рутинних задач, інтеграція AI, CRM-системи.",
        "description": "Автоматизація рутинних задач, інтеграція AI та CRM-систем.",
        "chat_endpoint": "/chatbot/automation",
        "submit_endpoint": "/crm/submit_task"
    },
    {
        "name": "ai-ml",
        "title": "AI та машинне навчання",
        "description": "Використання штучного інтелекту для аналізу даних, NLP, розпізнавання голосу.",
        "chat_endpoint": "/chatbot/ai-ml",
        "submit_endpoint": "/crm/submit_task"
    },
    {
        "name": "media-buying",
        "title": "Медіабаїнг",
        "description": "Оптимізація рекламних кампаній, таргетинг, аналітика ефективності.",
        "chat_endpoint": "/chatbot/media-buying",
        "submit_endpoint": "/crm/submit_task"
    },
    {
        "name": "databases",
        "title": "Бази даних",
        "description": "Проектування, оптимізація, зберігання великих масивів інформації.",
        "chat_endpoint": "/chatbot/databases",
        "submit_endpoint": "/crm/submit_task"
    }
]

def generate_service_page(service):
    def service_page():
        lang = session.get("lang", "de")
        return render_template(
            "service_template.html",
            service_name=service["name"],
            service_title=service["title"],
            service_description=service["description"],
            chat_endpoint=service["chat_endpoint"],
            submit_endpoint=service["submit_endpoint"],
            lang=lang
        )
    return service_page

for service in services:
    pages_bp.add_url_rule(
        f'/{service["name"]}',
        endpoint=f'service_page_{service["name"]}',
        view_func=generate_service_page(service)
    )
