import json
import base64
from typing import Any, Dict, Optional
from src.handlers.base import EventHandler
from src.core.auth import validate_api_key
from src.core.converters import convert_to_markdown
from src.utils.utils import create_api_response, is_api_gateway_event


class ApiHandler(EventHandler):
    """
    maneja eventos de api gateway e invocaciones directas
    """
    
    def can_handle(self, event: Dict[str, Any]) -> bool:
        """
        determina si este handler puede manejar el evento
        soporta api gateway e invocaciones directas
        """
        # es api gateway si tiene httpMethod
        if is_api_gateway_event(event):
            return True
        
        # es invocación directa si tiene content y no es evento s3
        if isinstance(event, dict) and 'content' in event and 'Records' not in event:
            return True
        
        return False
    
    def handle(self, event: Dict[str, Any], context: Optional[Any] = None) -> Any:
        """
        maneja el evento según su tipo
        """
        if is_api_gateway_event(event):
            return self._handle_api_gateway(event)
        else:
            return self._handle_direct_invocation(event)
    
    def _handle_api_gateway(self, event: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def _handle_direct_invocation(self, event: Dict[str, Any]) -> Dict[str, Any]:
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


# mantener compatibilidad con imports existentes
def handle_api_gateway_event(event):
    """función de compatibilidad para mantener api existente"""
    handler = ApiHandler()
    return handler._handle_api_gateway(event)


def handle_direct_invocation(event):
    """función de compatibilidad para mantener api existente"""
    handler = ApiHandler()
    return handler._handle_direct_invocation(event)
