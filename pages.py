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
