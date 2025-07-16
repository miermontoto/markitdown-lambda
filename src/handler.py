import json
from typing import Any, Dict, Optional
from src.handlers.registry import get_handler_for_event, auto_register_handlers
from src.core.responses import ResponseBuilder
from src.utils.utils import is_api_gateway_event


# auto-registrar handlers al importar
auto_register_handlers()


def lambda_handler(event: Dict[str, Any], context: Optional[Any] = None) -> Any:
    """
    handler principal que usa el registro para delegar a handlers específicos
    """
    print(f"Event received: {json.dumps(event)}")

    try:
        # buscar handler apropiado
        handler = get_handler_for_event(event)

        if handler:
            # delegar al handler encontrado
            return handler.handle(event, context)
        else:
            # no se encontró handler apropiado
            error_msg = "No handler found for this event type"
            print(f"Error: {error_msg}")
            print(f"Event structure: {list(event.keys()) if isinstance(event, dict) else type(event)}")

            # determinar tipo de respuesta de error
            if is_api_gateway_event(event):
                # para API Gateway, retornar error con headers CORS
                headers = {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
                return ResponseBuilder.error(
                    message=error_msg,
                    status_code=400,
                    headers=headers
                )
            else:
                raise ValueError(error_msg)

    except Exception as e:
        print(f"Error in lambda handler: {str(e)}")

        # manejar error según el tipo de evento
        if is_api_gateway_event(event):
            headers = {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
            return ResponseBuilder.error(
                message='Internal server error',
                status_code=500,
                details={'error': str(e)},
                headers=headers
            )
        else:
            # para otros tipos de eventos, relanzar la excepción
            raise e
