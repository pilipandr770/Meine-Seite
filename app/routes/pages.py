from flask import Blueprint, render_template

pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/privacy')
def privacy():
    return render_template('privacy.html', title="Політика конфіденційності", lang="uk")

@pages_bp.route('/impressum')
def impressum():
    return render_template('impressum.html', title="Impressum", lang="uk")

@pages_bp.route('/contact')
def contact():
    return render_template('contact.html', title="Контакти", lang="uk")

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
        return render_template("service_template.html",
                               service_name=service["name"],
                               service_title=service["title"],
                               service_description=service["description"],
                               chat_endpoint=service["chat_endpoint"],
                               submit_endpoint=service["submit_endpoint"])
    return service_page

for service in services:
    pages_bp.add_url_rule(f'/{service["name"]}', endpoint=f'service_page_{service["name"]}', view_func=generate_service_page(service))
