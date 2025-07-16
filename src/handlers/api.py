import json
import base64
from typing import Any, Dict, Optional
from src.handlers.base import EventHandler
from src.core.auth import validate_api_key
from src.core.converters import convert_to_markdown
from src.core.responses import ResponseBuilder
from src.utils.utils import is_api_gateway_event


class ApiHandler(EventHandler):
    """
    maneja eventos de api gateway e invocaciones directas
    """

    def can_handle(self, event: Any) -> bool:
        """
        determina si este handler puede manejar el evento
        soporta api gateway e invocaciones directas
        """
        # validar que el evento es un diccionario
        if not isinstance(event, dict):
            return False

        # es api gateway si tiene httpMethod
        if is_api_gateway_event(event):
            return True

        # es invocación directa si tiene content y no es evento s3
        if 'content' in event and 'Records' not in event:
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
        # headers por defecto para API Gateway
        api_headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-API-Key',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        }

        try:
            # validar autorización
            if not validate_api_key(event):
                return ResponseBuilder.error(
                    message='Unauthorized',
                    status_code=401,
                    headers=api_headers
                )

            # obtener body del request
            body = event.get('body', '')
            if not body:
                return ResponseBuilder.error(
                    message='Missing request body',
                    status_code=400,
                    headers=api_headers
                )

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
                return ResponseBuilder.error(
                    message='Missing content in request',
                    status_code=400,
                    headers=api_headers
                )

            content = data['content']
            filename = data.get('filename')

            # si el contenido viene en base64
            if data.get('base64'):
                content = base64.b64decode(content)

            result = convert_to_markdown(content, filename)

            return ResponseBuilder.success(
                data=result,
                headers=api_headers
            )

        except Exception as e:
            print(f"Error in API handler: {str(e)}")
            return ResponseBuilder.error(
                message='Internal server error',
                status_code=500,
                details={'error': str(e)},
                headers=api_headers
            )

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
