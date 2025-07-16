import os


def validate_api_key(event):
    """valida el api key del request"""
    api_key = os.environ.get('API_KEY')
    if not api_key:
        # si no hay api key configurada, permitir acceso
        return True

    headers = event.get('headers', {})
    # soportar ambos formatos de header
    auth_header = headers.get('authorization') or headers.get('Authorization')
    x_api_key = headers.get('x-api-key') or headers.get('X-API-Key')

    # verificar bearer token
    if auth_header and auth_header.startswith('Bearer '):
        provided_key = auth_header[7:]  # quitar "Bearer "
        return provided_key == api_key

    # verificar x-api-key
    if x_api_key:
        return x_api_key == api_key

    return False
