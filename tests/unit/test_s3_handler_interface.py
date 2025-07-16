import unittest
from unittest.mock import patch, MagicMock
from src.handlers.s3 import S3Handler
from src.handlers.base import EventHandler
from tests.fixtures import S3_EVENT


class TestS3HandlerInterface(unittest.TestCase):
    """pruebas para los métodos de interfaz de S3Handler"""
    
    def setUp(self):
        """configurar antes de cada prueba"""
        # crear handler con mock s3 client
        self.mock_s3_client = MagicMock()
        self.handler = S3Handler(s3_client=self.mock_s3_client)
    
    def test_handler_is_event_handler(self):
        """verifica que S3Handler implementa EventHandler"""
        self.assertIsInstance(self.handler, EventHandler)
    
    def test_can_handle_s3_event(self):
        """prueba can_handle con evento S3 válido"""
        self.assertTrue(self.handler.can_handle(S3_EVENT))
    
    def test_can_handle_s3_event_variations(self):
        """prueba can_handle con variaciones de eventos S3"""
        # evento mínimo S3
        minimal_s3_event = {
            "Records": [{
                "eventSource": "aws:s3"
            }]
        }
        self.assertTrue(self.handler.can_handle(minimal_s3_event))
        
        # múltiples registros
        multi_record_event = {
            "Records": [
                {"eventSource": "aws:s3"},
                {"eventSource": "aws:s3"},
                {"eventSource": "aws:s3"}
            ]
        }
        self.assertTrue(self.handler.can_handle(multi_record_event))
    
    def test_can_handle_non_s3_events(self):
        """prueba can_handle rechaza eventos no-S3"""
        # evento API Gateway
        api_event = {"httpMethod": "POST", "body": "test"}
        self.assertFalse(self.handler.can_handle(api_event))
        
        # invocación directa
        direct_event = {"content": "test content"}
        self.assertFalse(self.handler.can_handle(direct_event))
        
        # evento con Records pero no S3
        other_event = {
            "Records": [{
                "eventSource": "aws:dynamodb"
            }]
        }
        self.assertFalse(self.handler.can_handle(other_event))
    
    def test_can_handle_invalid_events(self):
        """prueba can_handle con eventos inválidos"""
        # evento vacío
        self.assertFalse(self.handler.can_handle({}))
        
        # no es diccionario
        self.assertFalse(self.handler.can_handle("not a dict"))
        self.assertFalse(self.handler.can_handle(None))
        self.assertFalse(self.handler.can_handle([]))
        
        # Records vacío
        self.assertFalse(self.handler.can_handle({"Records": []}))
        
        # Records no es lista
        self.assertFalse(self.handler.can_handle({"Records": "not a list"}))
    
    @patch('src.handlers.s3.convert_to_markdown')
    def test_handle_returns_batch_response(self, mock_convert):
        """prueba handle retorna respuesta batch estructurada"""
        # configurar mocks
        self.mock_s3_client.get_object.return_value = {
            'Body': MagicMock(read=lambda: b'Test content')
        }
        mock_convert.return_value = {
            'markdown': 'Converted content',
            'metadata': {'original_format': 'txt', 'converted_at': '2024-01-01T12:00:00Z'}
        }
        
        result = self.handler.handle(S3_EVENT)
        
        self.assertEqual(result['statusCode'], 200)
        self.assertIn('body', result)
        self.assertIn('results', result['body'])
    
    def test_handle_with_context(self):
        """prueba handle con contexto Lambda"""
        context = {
            'function_name': 'test-function',
            'request_id': 'test-123'
        }
        
        # configurar mocks
        self.mock_s3_client.get_object.return_value = {
            'Body': MagicMock(read=lambda: b'Test')
        }
        
        with patch('src.handlers.s3.convert_to_markdown') as mock_convert:
            mock_convert.return_value = {'markdown': 'test', 'metadata': {}}
            
            # contexto se pasa pero no se usa actualmente
            result = self.handler.handle(S3_EVENT, context)
            self.assertEqual(result['statusCode'], 200)
    
    def test_dependency_injection(self):
        """prueba que la inyección de dependencias funciona"""
        # crear cliente S3 personalizado
        custom_client = MagicMock()
        custom_client.get_object.return_value = {
            'Body': MagicMock(read=lambda: b'Custom content')
        }
        
        # crear handler con cliente personalizado
        custom_handler = S3Handler(s3_client=custom_client)
        
        with patch('src.handlers.s3.convert_to_markdown') as mock_convert:
            mock_convert.return_value = {'markdown': 'test', 'metadata': {}}
            
            custom_handler.handle(S3_EVENT)
            
            # verificar que se usó el cliente personalizado
            custom_client.get_object.assert_called_once()
            self.mock_s3_client.get_object.assert_not_called()
    
    def test_default_s3_client_creation(self):
        """prueba creación de cliente S3 por defecto"""
        with patch('boto3.client') as mock_boto3_client:
            mock_default_client = MagicMock()
            mock_boto3_client.return_value = mock_default_client
            
            # crear handler sin cliente
            handler = S3Handler()
            
            # verificar que se creó cliente S3
            mock_boto3_client.assert_called_once_with('s3', region_name='us-east-1')
            self.assertEqual(handler.s3_client, mock_default_client)
    
    def test_private_methods_exist(self):
        """verifica que los métodos privados existen"""
        self.assertTrue(hasattr(self.handler, '_process_record'))
        self.assertTrue(hasattr(self.handler, '_generate_output_key'))
        self.assertTrue(hasattr(self.handler, '_save_converted_file'))
        self.assertTrue(hasattr(self.handler, '_save_error_info'))
    
    def test_handle_multiple_records(self):
        """prueba manejo de múltiples registros S3"""
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
        
        self.mock_s3_client.get_object.return_value = {
            'Body': MagicMock(read=lambda: b'Content')
        }
        
        with patch('src.handlers.s3.convert_to_markdown') as mock_convert:
            mock_convert.return_value = {'markdown': 'test', 'metadata': {}}
            
            result = self.handler.handle(multi_event)
            body = result['body']
            
            # verificar que procesó todos los registros
            self.assertIn('"results":', body)
            self.assertEqual(self.mock_s3_client.get_object.call_count, 3)
    
    def test_handle_error_doesnt_stop_batch(self):
        """prueba que errores no detienen el procesamiento batch"""
        # configurar para que falle en el segundo archivo
        def side_effect(*args, **kwargs):
            key = kwargs.get('Key', '')
            if 'file1' in key:
                raise Exception("File 1 error")
            return {'Body': MagicMock(read=lambda: b'Content')}
        
        self.mock_s3_client.get_object.side_effect = side_effect
        
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
        
        with patch('src.handlers.s3.convert_to_markdown') as mock_convert:
            mock_convert.return_value = {'markdown': 'test', 'metadata': {}}
            
            result = self.handler.handle(multi_event)
            
            # debe completar con éxito aunque un archivo falle
            self.assertEqual(result['statusCode'], 200)
            # debe haber intentado procesar todos los archivos
            self.assertEqual(self.mock_s3_client.get_object.call_count, 3)


if __name__ == '__main__':
    unittest.main()