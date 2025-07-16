import json
import os
from typing import Any, Dict, Optional
from urllib.parse import unquote
from src.handlers.base import EventHandler
from src.core.converters import convert_to_markdown
from src.utils.utils import get_current_timestamp, is_s3_event


class S3Handler(EventHandler):
    """
    maneja eventos de s3 para conversión de archivos
    """

    def __init__(self, s3_client=None):
        """
        inicializa el handler con cliente s3 opcional (dependency injection)
        """
        if s3_client is None:
            import boto3
            s3_client = boto3.client('s3')
        self.s3_client = s3_client

    def can_handle(self, event: Dict[str, Any]) -> bool:
        """
        determina si este handler puede manejar el evento
        """
        return is_s3_event(event)

    def handle(self, event: Dict[str, Any], context: Optional[Any] = None) -> Dict[str, Any]:
        """
        procesa eventos de s3
        """
        results = []

        for record in event['Records']:
            result = self._process_record(record)
            results.append(result)

        return {
            'statusCode': 200,
            'body': json.dumps({'results': results})
        }

    def _process_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        procesa un registro individual de s3
        """
        # obtener información del archivo
        bucket = record['s3']['bucket']['name']
        key = unquote(record['s3']['object']['key'])

        print(f"Processing file: s3://{bucket}/{key}")

        try:
            # descargar archivo de s3
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read()

            # convertir a markdown
            result = convert_to_markdown(content, key)

            # generar key de salida
            output_key = self._generate_output_key(key)

            # guardar resultado en s3
            self._save_converted_file(bucket, output_key, result)

            print(f"Successfully converted {key} to {output_key}")

            return {
                'source': key,
                'output': output_key,
                'status': 'success'
            }

        except Exception as e:
            print(f"Error processing {key}: {str(e)}")

            # guardar información del error
            self._save_error_info(bucket, key, e)

            return {
                'source': key,
                'status': 'error',
                'error': str(e)
            }

    def _generate_output_key(self, input_key: str) -> str:
        """
        genera la key de salida basada en la key de entrada
        """
        output_key = input_key.replace('input/', 'output/')
        if not output_key.endswith('.md'):
            output_key = os.path.splitext(output_key)[0] + '.md'
        return output_key

    def _save_converted_file(self, bucket: str, key: str, result: Dict[str, Any]) -> None:
        """
        guarda el archivo convertido en s3
        """
        self.s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=result['markdown'].encode('utf-8'),
            ContentType='text/markdown',
            Metadata={
                'original-format': result['metadata']['original_format'],
                'converted-at': result['metadata']['converted_at']
            }
        )

    def _save_error_info(self, bucket: str, key: str, error: Exception) -> None:
        """
        guarda información del error en el bucket
        """
        error_key = key.replace('input/', 'errors/')
        error_key = os.path.splitext(error_key)[0] + '_error.json'

        error_info = {
            'source_key': key,
            'error': str(error),
            'error_type': type(error).__name__,
            'timestamp': get_current_timestamp(),
            'bucket': bucket
        }

        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=error_key,
                Body=json.dumps(error_info, indent=2).encode('utf-8'),
                ContentType='application/json'
            )
        except Exception as save_error:
            print(f"Error saving error info: {str(save_error)}")


# instancia global para compatibilidad
_default_handler = None


def _get_default_handler():
    """obtiene la instancia por defecto del handler"""
    global _default_handler
    if _default_handler is None:
        _default_handler = S3Handler()
    return _default_handler


# mantener compatibilidad con imports existentes
def handle_s3_event(event):
    """función de compatibilidad para mantener api existente"""
    handler = _get_default_handler()
    return handler.handle(event)


# exportar s3_client para compatibilidad con tests
def __getattr__(name):
    if name == 's3_client':
        return _get_default_handler().s3_client
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
