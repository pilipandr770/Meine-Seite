from flask import Blueprint, jsonify, request, current_app, Markup
import json
from flask_login import login_required
import os

debug_bp = Blueprint('debug', __name__)

@debug_bp.route('/debug/request', methods=['POST'])
def debug_request():
    """Debug endpoint to log request details"""
    try:
        # Get the headers
        headers = {k: v for k, v in request.headers.items()}
        
        # Get form or JSON data
        form_data = {}
        for key in request.form:
            form_data[key] = request.form[key]
        
        json_data = {}
        if request.is_json:
            json_data = request.get_json()
        
        # Compile debug info
        debug_info = {
            'method': request.method,
            'path': request.path,
            'headers': headers,
            'form_data': form_data,
            'json_data': json_data,
            'content_type': request.content_type,
            'content_length': request.content_length
        }
        
        # Log the debug info
        current_app.logger.debug(f"Debug request info: {json.dumps(debug_info, indent=2)}")
        
        return jsonify({
            'success': True,
            'message': 'Request logged successfully',
            'debug_info': debug_info
        })
    except Exception as e:
        current_app.logger.error(f"Error in debug endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@debug_bp.route('/fix-templates', methods=['GET'])
@login_required
def fix_templates():
    """Apply quick fixes to the template environment"""
    if 'FLASK_ENV' not in os.environ or os.environ['FLASK_ENV'] != 'development':
        # Only allow in development mode or with proper auth
        if not request.args.get('auth_key') == os.environ.get('DEBUG_AUTH_KEY'):
            return jsonify({
                'success': False,
                'message': 'Not authorized'
            }), 403
    
    try:
        # Add the nl2br filter to the template environment
        @current_app.template_filter('nl2br')
        def nl2br_filter(s):
            if s is None:
                return ""
            return Markup(s.replace('\n', '<br>'))
        
        return jsonify({
            'success': True,
            'message': 'Template fixes applied successfully',
            'fixes': ['nl2br filter added']
        })
    except Exception as e:
        current_app.logger.error(f"Error applying template fixes: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
