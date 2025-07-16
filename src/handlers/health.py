"""
health check handler para verificar el estado del servicio
"""
from typing import Any, Dict
from src.handlers.base import EventHandler
from src.core.responses import ResponseBuilder
from src.core.config import get_config


class HealthHandler(EventHandler):
    """
    maneja health checks del servicio
    """

    def can_handle(self, event: Dict[str, Any]) -> bool:
        """
        verifica si este handler puede manejar el evento
        """
        # verificar si es un evento http get en /health
        if event.get('requestContext', {}).get('http', {}).get('method') == 'GET':
            path = event.get('rawPath', '')
            return path == '/health'
        return False

    def handle(self, event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
        """
        procesa el health check
        """
        # información del servicio
        health_info: Dict[str, Any] = {
            'status': 'healthy',
            'service': get_config('APP_NAME', 'markdown-converter'),
            'version': get_config('APP_VERSION', '1.0.0'),
            'region': get_config('AWS_REGION', 'unknown'),
            'runtime': get_config('AWS_EXECUTION_ENV', 'unknown'),
            'bucket': get_config('INPUT_BUCKET', 'not-configured')
        }

        # agregar información del contexto si está disponible
        if context:
            health_info['function'] = {
                'name': getattr(context, 'function_name', 'unknown'),
                'version': getattr(context, 'function_version', 'unknown'),
                'memory_limit': getattr(context, 'memory_limit_in_mb', 'unknown'),
                'request_id': getattr(context, 'aws_request_id', 'unknown')
            }

        # headers cors
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }

        return ResponseBuilder.success(
            data=health_info,
            headers=headers
        )
