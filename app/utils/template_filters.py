"""
Custom template filters for the application.
"""
from flask import Markup

def register_template_filters(app):
    """Register custom template filters with the Flask application."""
    
    @app.template_filter('nl2br')
    def nl2br_filter(s):
        """
        Convert newlines in a string to HTML <br> tags.
        
        Args:
            s (str): The input string to process
            
        Returns:
            Markup: A safe HTML string with newlines replaced by <br> tags
        """
        if s is None:
            return ""
        return Markup(s.replace('\n', '<br>'))
