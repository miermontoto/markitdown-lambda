import json
from typing import Any, Dict, Optional, Union


class ResponseBuilder:
    """
    constructor de respuestas estandarizadas para diferentes tipos de eventos
    """

    @staticmethod
    def api_gateway_response(
        status_code: int,
        body: Union[Dict[str, Any], str],
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        construye una respuesta para api gateway

        Args:
            status_code: Código de estado HTTP
            body: Cuerpo de la respuesta (dict o string)
            headers: Headers adicionales

        Returns:
            Dict con formato de respuesta de API Gateway
        """
        if headers is None:
            headers = {}

        # headers por defecto
        default_headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-API-Key',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        }

        # combinar headers
        final_headers = {**default_headers, **headers}

        # convertir body a string si es necesario
        if isinstance(body, dict):
            body_str = json.dumps(body)
        else:
            body_str = body

        return {
            'statusCode': status_code,
            'headers': final_headers,
            'body': body_str
        }

    @staticmethod
    def s3_batch_response(results: list) -> Dict[str, Any]:
        """
        construye una respuesta para procesamiento batch de s3

        Args:
            results: Lista de resultados de procesamiento

        Returns:
            Dict con formato de respuesta batch
        """
        # contar éxitos y errores
        success_count = sum(1 for r in results if r.get('status') == 'success')
        error_count = sum(1 for r in results if r.get('status') == 'error')

        return {
            'statusCode': 200,
            'body': json.dumps({
                'results': results,
                'summary': {
                    'total': len(results),
                    'success': success_count,
                    'errors': error_count
                }
            })
        }

    @staticmethod
    def direct_invocation_response(
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        construye una respuesta para invocación directa

        Args:
            success: Si la operación fue exitosa
            data: Datos de respuesta (si fue exitosa)
            error: Mensaje de error (si falló)

        Returns:
            Dict con respuesta estructurada
        """
        if success and data:
            return data
        elif not success and error:
            return {
                'error': error,
                'success': False
            }
        else:
            raise ValueError("Invalid response state: either data or error must be provided")

    @staticmethod
    def error_response(
        error: Exception,
        event_type: str = 'unknown'
    ) -> Dict[str, Any]:
        """
        construye una respuesta de error genérica

        Args:
            error: La excepción que ocurrió
            event_type: Tipo de evento (api_gateway, s3, direct)

        Returns:
            Dict con respuesta de error apropiada para el tipo de evento
        """
        error_info = {
            'error': str(error),
            'error_type': type(error).__name__
        }

        if event_type == 'api_gateway':
            return ResponseBuilder.api_gateway_response(
                status_code=500,
                body={
                    'error': 'Internal server error',
                    'details': str(error)
                }
            )
        elif event_type == 's3':
            return ResponseBuilder.s3_batch_response([{
                'status': 'error',
                'error': str(error),
                'source': 'unknown'
            }])
        else:
            return ResponseBuilder.direct_invocation_response(
                success=False,
                error=str(error)
            )


# funciones de conveniencia para mantener compatibilidad
def create_api_response(status_code: int, body: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """
    función de compatibilidad para crear respuestas api gateway
    """
    return ResponseBuilder.api_gateway_response(status_code, body)


def create_error_response(error: Exception, event_type: str = 'unknown') -> Dict[str, Any]:
    """
    función de compatibilidad para crear respuestas de error
    """
    return ResponseBuilder.error_response(error, event_type)
