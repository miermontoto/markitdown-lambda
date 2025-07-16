import json
from datetime import datetime, timezone


def get_file_extension(filename):
    """obtiene extensión del archivo"""
    if not filename:
        return None
    parts = filename.split('.')
    return parts[-1].lower() if len(parts) > 1 else 'unknown'


def get_current_timestamp():
    """obtiene timestamp actual en formato iso"""
    # usar replace para obtener formato ISO con Z en lugar de +00:00
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def create_api_response(status_code, body):
    """crea respuesta para api gateway"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }


def is_s3_event(event):
    """verifica si es un evento de s3"""
    if not event or not isinstance(event, dict):
        return False
    return 'Records' in event and event['Records'] and \
           len(event['Records']) > 0 and \
           event['Records'][0].get('eventSource') == 'aws:s3'


def is_api_gateway_event(event):
    """verifica si es un evento de api gateway"""
    if not event or not isinstance(event, dict):
        return False
    return 'httpMethod' in event or 'requestContext' in event
