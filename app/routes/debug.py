from flask import Blueprint, jsonify, request, current_app
import json

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
