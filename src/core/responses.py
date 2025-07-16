import json
from typing import Any, Dict, Optional, Union


class ResponseBuilder:
    """
    constructor genérico de respuestas estructuradas
    """

    @staticmethod
    def build(
        status_code: int,
        body: Union[Dict[str, Any], str, None] = None,
        headers: Optional[Dict[str, str]] = None,
        is_base64_encoded: bool = False
    ) -> Dict[str, Any]:
        """
        construye una respuesta genérica con estructura estándar

        Args:
            status_code: Código de estado HTTP
            body: Cuerpo de la respuesta (dict, string o None)
            headers: Headers HTTP opcionales
            is_base64_encoded: Si el body está codificado en base64

        Returns:
            Dict con respuesta estructurada
        """
        response: Dict[str, Any] = {
            'statusCode': status_code
        }

        if headers:
            response['headers'] = headers

        if body is not None:
            if isinstance(body, dict):
                response['body'] = json.dumps(body)
            else:
                response['body'] = body

        if is_base64_encoded:
            response['isBase64Encoded'] = True

        return response

    @staticmethod
    def success(
        data: Union[Dict[str, Any], str],
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        construye una respuesta exitosa

        Args:
            data: Datos de respuesta
            status_code: Código de estado (default: 200)
            headers: Headers opcionales

        Returns:
            Dict con respuesta de éxito
        """
        return ResponseBuilder.build(
            status_code=status_code,
            body=data,
            headers=headers
        )

    @staticmethod
    def error(
        message: str,
        status_code: int = 500,
        error_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        construye una respuesta de error

        Args:
            message: Mensaje de error
            status_code: Código de estado (default: 500)
            error_type: Tipo de error opcional
            details: Detalles adicionales del error
            headers: Headers opcionales

        Returns:
            Dict con respuesta de error
        """
        error_body: Dict[str, Any] = {'error': message}

        if error_type:
            error_body['error_type'] = error_type

        if details:
            error_body['details'] = details

        return ResponseBuilder.build(
            status_code=status_code,
            body=error_body,
            headers=headers
        )

    @staticmethod
    def json(
        data: Any,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        construye una respuesta JSON con headers apropiados

        Args:
            data: Datos a serializar como JSON
            status_code: Código de estado (default: 200)
            headers: Headers adicionales

        Returns:
            Dict con respuesta JSON
        """
        json_headers = {'Content-Type': 'application/json'}
        if headers:
            json_headers.update(headers)

        return ResponseBuilder.build(
            status_code=status_code,
            body=data if isinstance(data, str) else json.dumps(data),
            headers=json_headers
        )

    @staticmethod
    def batch(
        results: list,
        status_code: int = 200,
        summary: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        construye una respuesta para operaciones batch

        Args:
            results: Lista de resultados
            status_code: Código de estado (default: 200)
            summary: Resumen opcional de los resultados
            headers: Headers opcionales

        Returns:
            Dict con respuesta batch
        """
        body: Dict[str, Any] = {'results': results}

        if summary:
            body['summary'] = summary

        return ResponseBuilder.build(
            status_code=status_code,
            body=body,
            headers=headers
        )


# funciones de conveniencia para mantener compatibilidad
def create_api_response(status_code: int, body: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """
    función de compatibilidad para crear respuestas api gateway
    """
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }
    return ResponseBuilder.build(status_code, body, headers)


def create_error_response(error: Exception, event_type: str = 'unknown') -> Dict[str, Any]:
    """
    función de compatibilidad para crear respuestas de error
    nota: esta función es obsoleta, usar ResponseBuilder.error directamente
    """
    return ResponseBuilder.error(
        message=str(error),
        error_type=type(error).__name__
    )
