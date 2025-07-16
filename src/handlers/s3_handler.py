import json
import os
import boto3
from urllib.parse import unquote_plus
from src.core.converters import convert_to_markdown
from src.utils.utils import get_current_timestamp

# inicializar cliente s3
s3_client = boto3.client('s3')


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