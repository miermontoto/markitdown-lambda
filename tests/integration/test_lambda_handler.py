import unittest
from unittest.mock import patch, MagicMock
import json
import os
from src.handler import lambda_handler
from tests.fixtures import (
    API_GATEWAY_EVENT,
    S3_EVENT,
    DIRECT_INVOCATION_EVENT
)


class TestLambdaHandlerIntegration(unittest.TestCase):
    """pruebas de integración para el handler principal"""
    
    def setUp(self):
        """configurar antes de cada prueba"""
        self.original_api_key = os.environ.get('API_KEY')
        os.environ['API_KEY'] = 'test-api-key'
    
    def tearDown(self):
        """limpiar después de cada prueba"""
        if self.original_api_key:
            os.environ['API_KEY'] = self.original_api_key
        elif 'API_KEY' in os.environ:
            del os.environ['API_KEY']
    
    @patch('src.core.converters.markitdown')
    def test_api_gateway_flow(self, mock_markitdown):
        """prueba flujo completo de API Gateway"""
        # configurar mock
        mock_result = MagicMock()
        mock_result.text_content = "# Converted Content\n\nThis is the converted markdown."
        mock_markitdown.convert_stream.return_value = mock_result
        
        # ejecutar handler
        result = lambda_handler(API_GATEWAY_EVENT, {})
        
        # verificar respuesta
        self.assertEqual(result['statusCode'], 200)
        self.assertIn('headers', result)
        self.assertIn('body', result)
        
        body = json.loads(result['body'])
        self.assertIn('markdown', body)
        self.assertIn('metadata', body)
        self.assertIn('Converted Content', body['markdown'])
    
    @patch('src.handlers.s3_handler.s3_client')
    @patch('src.core.converters.markitdown')
    def test_s3_event_flow(self, mock_markitdown, mock_s3):
        """prueba flujo completo de evento S3"""
        # configurar mocks
        mock_s3.get_object.return_value = {
            'Body': MagicMock(read=lambda: b'Test S3 content')
        }
        
        mock_result = MagicMock()
        mock_result.text_content = "# S3 Content\n\nProcessed from S3."
        mock_markitdown.convert_stream.return_value = mock_result
        
        # ejecutar handler
        result = lambda_handler(S3_EVENT, {})
        
        # verificar respuesta
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertIn('results', body)
        self.assertEqual(len(body['results']), 1)
        self.assertEqual(body['results'][0]['status'], 'success')
        
        # verificar que se guardó en S3
        mock_s3.put_object.assert_called_once()
    
    @patch('src.core.converters.markitdown')
    def test_direct_invocation_flow(self, mock_markitdown):
        """prueba flujo de invocación directa"""
        # configurar mock
        mock_result = MagicMock()
        mock_result.text_content = "# Direct Content"
        mock_markitdown.convert_stream.return_value = mock_result
        
        # ejecutar handler
        result = lambda_handler(DIRECT_INVOCATION_EVENT, {})
        
        # verificar respuesta
        self.assertIn('markdown', result)
        self.assertIn('metadata', result)
        self.assertEqual(result['markdown'], "# Direct Content")
    
    def test_invalid_event_handling(self):
        """prueba manejo de eventos inválidos"""
        invalid_event = {'invalid': 'event'}
        
        with self.assertRaises(ValueError):
            lambda_handler(invalid_event, {})
    
    @patch('src.core.converters.markitdown')
    def test_api_gateway_error_handling(self, mock_markitdown):
        """prueba manejo de errores en API Gateway"""
        # configurar mock para fallar
        mock_markitdown.convert_stream.side_effect = Exception("Conversion error")
        
        # ejecutar handler
        result = lambda_handler(API_GATEWAY_EVENT, {})
        
        # verificar respuesta de error
        self.assertEqual(result['statusCode'], 500)
        body = json.loads(result['body'])
        self.assertEqual(body['error'], 'Internal server error')
        self.assertIn('Conversion error', body['details'])
    
    def test_unauthorized_api_request(self):
        """prueba rechazo de request no autorizado"""
        # crear evento sin autorización
        unauthorized_event = API_GATEWAY_EVENT.copy()
        unauthorized_event['headers'] = {'Content-Type': 'application/json'}
        
        result = lambda_handler(unauthorized_event, {})
        
        self.assertEqual(result['statusCode'], 401)
        body = json.loads(result['body'])
        self.assertEqual(body['error'], 'Unauthorized')


if __name__ == '__main__':
    unittest.main()