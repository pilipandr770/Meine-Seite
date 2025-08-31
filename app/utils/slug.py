"""Slug generation utilities for RoZoom application"""
import re
import unidecode

def generate_slug(text):
    """
    Generate a URL-friendly slug from the provided text.
    
    Args:
        text (str): The text to convert to a slug
        
    Returns:
        str: A URL-friendly slug
    """
    # Convert to ASCII and lowercase
    text = unidecode.unidecode(text).lower()
    
    # Replace non-alphanumeric characters with hyphens
    text = re.sub(r'[^a-z0-9]+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    # Replace multiple consecutive hyphens with a single one
    text = re.sub(r'-+', '-', text)
    
    return text
