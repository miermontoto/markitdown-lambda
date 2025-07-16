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
                return ResponseBuilder.api_gateway_response(
                    status_code=400,
                    body={'error': error_msg}
                )
            else:
                raise ValueError(error_msg)

    except Exception as e:
        print(f"Error in lambda handler: {str(e)}")

        # determinar tipo de evento para respuesta de error apropiada
        event_type = 'unknown'
        if is_api_gateway_event(event):
            event_type = 'api_gateway'
        elif isinstance(event, dict) and 'Records' in event:
            event_type = 's3'
        elif isinstance(event, dict) and 'content' in event:
            event_type = 'direct'

        return ResponseBuilder.error_response(e, event_type)
