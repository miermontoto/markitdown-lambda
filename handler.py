import json
import base64
import boto3
import os
from urllib.parse import unquote_plus
from markitdown import MarkItDown

# inicializar cliente s3 y markitdown
s3_client = boto3.client('s3')
markitdown = MarkItDown()


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
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Internal server error',
                    'details': str(e)
                })
            }
        else:
            raise e


def is_s3_event(event):
    """verifica si es un evento de s3"""
    return 'Records' in event and event['Records'] and \
           event['Records'][0].get('eventSource') == 'aws:s3'


def is_api_gateway_event(event):
    """verifica si es un evento de api gateway"""
    return 'httpMethod' in event or 'requestContext' in event


def handle_s3_event(event):
    """procesa eventos de s3"""
    results = []

    for record in event['Records']:
        # obtener información del archivo
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])

        print(f"Processing file: s3://{bucket}/{key}")

        try:
            # descargar archivo de s3
            response = s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read()

            # convertir a markdown
            result = convert_to_markdown(content, key)

            # generar key de salida
            output_key = key.replace('input/', 'output/')
            if not output_key.endswith('.md'):
                output_key = os.path.splitext(output_key)[0] + '.md'

            # guardar resultado en s3 (mismo bucket, directorio output)
            s3_client.put_object(
                Bucket=bucket,
                Key=output_key,
                Body=result['markdown'].encode('utf-8'),
                ContentType='text/markdown',
                Metadata={
                    'original-format': result['metadata']['original_format'],
                    'converted-at': result['metadata']['converted_at']
                }
            )

            results.append({
                'source': key,
                'output': output_key,
                'status': 'success'
            })

            print(f"Successfully converted {key} to {output_key}")

        except Exception as e:
            print(f"Error processing {key}: {str(e)}")

            # guardar información del error en el bucket
            error_key = key.replace('input/', 'errors/')
            error_key = os.path.splitext(error_key)[0] + '_error.json'

            error_info = {
                'source_key': key,
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': get_current_timestamp(),
                'bucket': bucket
            }

            try:
                s3_client.put_object(
                    Bucket=bucket,
                    Key=error_key,
                    Body=json.dumps(error_info, indent=2).encode('utf-8'),
                    ContentType='application/json'
                )
            except Exception as save_error:
                print(f"Error saving error info: {str(save_error)}")

            results.append({
                'source': key,
                'status': 'error',
                'error': str(e)
            })

    return {
        'statusCode': 200,
        'body': json.dumps({'results': results})
    }


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


def handle_api_gateway_event(event):
    """procesa requests de api gateway"""
    try:
        # validar autorización
        if not validate_api_key(event):
            return create_api_response(401, {'error': 'Unauthorized'})

        # obtener body del request
        body = event.get('body', '')
        if not body:
            return create_api_response(400, {'error': 'Missing request body'})

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
            return create_api_response(400, {'error': 'Missing content in request'})

        content = data['content']
        filename = data.get('filename')

        # si el contenido viene en base64
        if data.get('base64'):
            content = base64.b64decode(content)

        result = convert_to_markdown(content, filename)

        return create_api_response(200, result)

    except Exception as e:
        print(f"Error in API handler: {str(e)}")
        return create_api_response(500, {
            'error': 'Internal server error',
            'details': str(e)
        })


def handle_direct_invocation(event):
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


def convert_to_markdown(content, filename=None):
    """convierte contenido a markdown usando markitdown"""
    try:
        import tempfile
        import io

        # mantener el contenido original en bytes y detectar si es texto
        if isinstance(content, bytes):
            try:
                text_content = content.decode('utf-8')
                is_text = True
            except UnicodeDecodeError:
                # si no se puede decodificar, es binario
                is_text = False
                binary_content = content
        else:
            # si ya es string, es texto
            is_text = True
            text_content = content

        # si tenemos un nombre de archivo y es binario, guardarlo temporalmente
        if filename and not is_text:
            _, ext = os.path.splitext(filename)

            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(binary_content)
                tmp_path = tmp.name

            try:
                result = markitdown.convert(tmp_path)
            finally:
                os.unlink(tmp_path)
        else:
            # convertir texto directamente usando stream
            # crear stream desde el contenido
            if is_text:
                content_stream = io.BytesIO(text_content.encode('utf-8'))
            else:
                # este caso no debería ocurrir, pero por seguridad
                content_stream = io.BytesIO(content if isinstance(content, bytes) else str(content).encode('utf-8'))

            # usar convert_stream
            result = markitdown.convert_stream(content_stream, file_extension=get_file_extension(filename) if filename else '.txt')

        return {
            'markdown': result.text_content,
            'metadata': {
                'original_format': get_file_extension(filename) if filename else 'text',
                'converted_at': get_current_timestamp(),
                'size': len(result.text_content),
                'title': getattr(result, 'title', None)
            }
        }

    except Exception as e:
        raise Exception(f"Error converting to markdown: {str(e)}")


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


def get_file_extension(filename):
    """obtiene extensión del archivo"""
    if not filename:
        return None
    parts = filename.split('.')
    return parts[-1].lower() if len(parts) > 1 else 'unknown'


def get_current_timestamp():
    """obtiene timestamp actual en formato iso"""
    from datetime import datetime
    return datetime.utcnow().isoformat() + 'Z'
