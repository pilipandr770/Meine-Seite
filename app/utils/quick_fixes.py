"""
Quick fix script to add the nl2br template filter in a running Flask application.
This is meant to be used in a debug route or console to patch the app without a full redeploy.
"""
from flask import Markup, current_app

def apply_nl2br_filter():
    """
    Apply the nl2br template filter to the current Flask application instance.
    Returns True if successful, False otherwise.
    """
    try:
        @current_app.template_filter('nl2br')
        def nl2br_filter(s):
            if s is None:
                return ""
            return Markup(s.replace('\n', '<br>'))
        return True
    except Exception as e:
        print(f"Error applying nl2br filter: {e}")
        return False

# This function can be called from a debug route or console
def fix_template_filters():
    result = apply_nl2br_filter()
    return {
        "success": result,
        "message": "nl2br template filter added successfully" if result else "Failed to add nl2br filter"
    }
