import json
import base64
from src.core.auth import validate_api_key
from src.core.converters import convert_to_markdown
from src.utils.utils import create_api_response


def handle_api_gateway_event(event):
    """procesa requests de api gateway"""
    try:
        # validar autorización
        if not validate_api_key(event):
            return create_api_response(401, {'error': 'Unauthorized'})

        # obtener body del request
        body = event.get('body', '')
        if not body:
            return create_api_response(400, {'error': 'Missing request body'})

        # decodificar base64 si es necesario
        if event.get('isBase64Encoded'):
            body = base64.b64decode(body)

        # parsear json
        try:
            data = json.loads(body)
        except (json.JSONDecodeError, TypeError):
            # si no es json, asumir que es contenido directo
            data = {'content': body}

        # validar entrada
        if 'content' not in data:
            return create_api_response(400, {'error': 'Missing content in request'})

        content = data['content']
        filename = data.get('filename')

        # si el contenido viene en base64
        if data.get('base64'):
            content = base64.b64decode(content)

        result = convert_to_markdown(content, filename)

        return create_api_response(200, result)

    except Exception as e:
        print(f"Error in API handler: {str(e)}")
        return create_api_response(500, {
            'error': 'Internal server error',
            'details': str(e)
        })


def handle_direct_invocation(event):
    """procesa invocaciones directas lambda"""
    # validar estructura del evento
    if not isinstance(event, dict) or 'content' not in event:
        raise ValueError("Direct invocation requires 'content' field")

    content = event['content']
    filename = event.get('filename')

    # decodificar base64 si es necesario
    if event.get('base64'):
        content = base64.b64decode(content)

    return convert_to_markdown(content, filename)
