from datetime import datetime, timezone
# importar create_api_response desde el módulo de respuestas para compatibilidad
from src.core.responses import create_api_response


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


def is_s3_event(event):
    """verifica si es un evento de s3"""
    if not event or not isinstance(event, dict):
        return False
    
    if 'Records' not in event:
        return False
    
    records = event['Records']
    if not isinstance(records, list) or len(records) == 0:
        return False
    
    # verificar que el primer record es de S3
    first_record = records[0]
    if not isinstance(first_record, dict):
        return False
    
    return first_record.get('eventSource') == 'aws:s3'


def is_api_gateway_event(event):
    """verifica si es un evento de api gateway"""
    if not event or not isinstance(event, dict):
        return False
    return 'httpMethod' in event or 'requestContext' in event
