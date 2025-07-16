import unittest
from unittest.mock import patch, MagicMock, call
import json
from botocore.exceptions import ClientError
from src.handlers.s3 import handle_s3_event
from tests.fixtures import S3_EVENT


class TestS3Handler(unittest.TestCase):
    """pruebas para el manejador de eventos S3"""
    
    def setUp(self):
        """limpiar el handler singleton antes de cada test"""
        import src.handlers.s3
        src.handlers.s3._default_handler = None
    
    @patch('boto3.client')
    @patch('src.handlers.s3.convert_to_markdown')
    def test_handle_s3_event_success(self, mock_convert, mock_boto3_client):
        """prueba procesamiento exitoso de evento S3"""
        # configurar mocks
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3
        mock_s3.get_object.return_value = {
            'Body': MagicMock(read=lambda: b'Test file content')
        }
        
        mock_convert.return_value = {
            'markdown': '# Test file content',
            'metadata': {
                'original_format': 'txt',
                'converted_at': '2024-01-01T12:00:00Z'
            }
        }
        
        result = handle_s3_event(S3_EVENT)
        
        # verificar respuesta
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertEqual(len(body['results']), 1)
        self.assertEqual(body['results'][0]['status'], 'success')
        self.assertEqual(body['results'][0]['source'], 'input/test-document.txt')
        self.assertEqual(body['results'][0]['output'], 'output/test-document.md')
        
        # verificar llamadas S3
        mock_s3.get_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='input/test-document.txt'
        )
        
        mock_s3.put_object.assert_called_once()
        put_args = mock_s3.put_object.call_args
        self.assertEqual(put_args[1]['Bucket'], 'test-bucket')
        self.assertEqual(put_args[1]['Key'], 'output/test-document.md')
        self.assertEqual(put_args[1]['ContentType'], 'text/markdown')
    
    @patch('boto3.client')
    @patch('src.handlers.s3.convert_to_markdown')
    def test_handle_s3_event_conversion_error(self, mock_convert, mock_boto3_client):
        """prueba manejo de error en conversión"""
        # configurar mocks
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3
        mock_s3.get_object.return_value = {
            'Body': MagicMock(read=lambda: b'Test file content')
        }
        
        mock_convert.side_effect = Exception("Conversion failed")
        
        result = handle_s3_event(S3_EVENT)
        
        # verificar respuesta
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertEqual(body['results'][0]['status'], 'error')
        self.assertIn('Conversion failed', body['results'][0]['error'])
        
        # verificar que se intentó guardar el error
        put_calls = mock_s3.put_object.call_args_list
        self.assertEqual(len(put_calls), 1)
        error_call = put_calls[0]
        self.assertEqual(error_call[1]['Key'], 'errors/test-document_error.json')
        self.assertEqual(error_call[1]['ContentType'], 'application/json')
    
    @patch('boto3.client')
    def test_handle_s3_event_get_object_error(self, mock_boto3_client):
        """prueba error al obtener objeto de S3"""
        # configurar mock para lanzar error
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3
        mock_s3.get_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey', 'Message': 'Object not found'}},
            'GetObject'
        )
        
        result = handle_s3_event(S3_EVENT)
        
        # verificar respuesta
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertEqual(body['results'][0]['status'], 'error')
        self.assertIn('NoSuchKey', body['results'][0]['error'])
    
    @patch('boto3.client')
    @patch('src.handlers.s3.convert_to_markdown')
    def test_handle_s3_event_multiple_records(self, mock_convert, mock_boto3_client):
        """prueba procesamiento de múltiples registros"""
        # crear evento con múltiples registros
        multi_event = {
            'Records': [
                {
                    'eventSource': 'aws:s3',
                    's3': {
                        'bucket': {'name': 'test-bucket'},
                        'object': {'key': f'input/file{i}.txt'}
                    }
                } for i in range(3)
            ]
        }
        
        # configurar mocks
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3
        mock_s3.get_object.return_value = {
            'Body': MagicMock(read=lambda: b'Content')
        }
        mock_convert.return_value = {
            'markdown': 'Converted content',
            'metadata': {'original_format': 'txt', 'converted_at': '2024-01-01T12:00:00Z'}
        }
        
        result = handle_s3_event(multi_event)
        
        # verificar que se procesaron todos los archivos
        body = json.loads(result['body'])
        self.assertEqual(len(body['results']), 3)
        self.assertEqual(mock_s3.get_object.call_count, 3)
        self.assertEqual(mock_s3.put_object.call_count, 3)
    
    @patch('boto3.client')
    @patch('src.handlers.s3.convert_to_markdown')
    def test_handle_s3_event_special_characters(self, mock_convert, mock_boto3_client):
        """prueba manejo de caracteres especiales en nombres"""
        # evento con caracteres especiales codificados
        special_event = {
            'Records': [{
                'eventSource': 'aws:s3',
                's3': {
                    'bucket': {'name': 'test-bucket'},
                    'object': {'key': 'input/test+file%20with%20spaces.txt'}
                }
            }]
        }
        
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3
        mock_s3.get_object.return_value = {
            'Body': MagicMock(read=lambda: b'Content')
        }
        mock_convert.return_value = {
            'markdown': 'Content',
            'metadata': {'original_format': 'txt', 'converted_at': '2024-01-01T12:00:00Z'}
        }
        
        result = handle_s3_event(special_event)
        
        # verificar que se decodificó correctamente
        mock_s3.get_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='input/test+file with spaces.txt'
        )
        
        # verificar output key
        put_args = mock_s3.put_object.call_args
        self.assertEqual(put_args[1]['Key'], 'output/test+file with spaces.md')


if __name__ == '__main__':
    unittest.main()