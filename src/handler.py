import json
from src.utils.utils import is_s3_event, is_api_gateway_event, create_api_response
from src.handlers.s3 import handle_s3_event
from src.handlers.api import handle_api_gateway_event, handle_direct_invocation


def lambda_handler(event, context):
    """
    handler principal que maneja api gateway, s3 events y invocaciones directas
    """
    print(f"Event received: {json.dumps(event)}")

    try:
        # detectar tipo de evento
        if is_s3_event(event):
            return handle_s3_event(event)
        elif is_api_gateway_event(event):
            return handle_api_gateway_event(event)
        else:
            # asumir invocación directa
            return handle_direct_invocation(event)

    except Exception as e:
        print(f"Error in lambda handler: {str(e)}")

        # retornar error apropiado según el contexto
        if is_api_gateway_event(event):
            return create_api_response(500, {
                'error': 'Internal server error',
                'details': str(e)
            })
        else:
            raise e
