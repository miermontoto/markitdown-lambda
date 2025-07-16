import unittest
from unittest.mock import patch, MagicMock
import json
import base64
import os
from src.handlers.api import handle_api_gateway_event, handle_direct_invocation
from tests.fixtures import (
    API_GATEWAY_EVENT, 
    API_GATEWAY_EVENT_BASE64,
    API_GATEWAY_EVENT_NO_AUTH,
    DIRECT_INVOCATION_EVENT,
    DIRECT_INVOCATION_EVENT_BASE64
)


class TestApiHandler(unittest.TestCase):
    """pruebas para el manejador de API Gateway"""
    
    def setUp(self):
        """configurar antes de cada prueba"""
        # guardar API_KEY original
        self.original_api_key = os.environ.get('API_KEY')
        # configurar API_KEY de prueba
        os.environ['API_KEY'] = 'test-api-key'
    
    def tearDown(self):
        """limpiar después de cada prueba"""
        if self.original_api_key:
            os.environ['API_KEY'] = self.original_api_key
        elif 'API_KEY' in os.environ:
            del os.environ['API_KEY']
    
    @patch('src.handlers.api.convert_to_markdown')
    def test_handle_api_gateway_event_success(self, mock_convert):
        """prueba manejo exitoso de evento API Gateway"""
        # configurar mock
        mock_convert.return_value = {
            'markdown': '# Test Markdown\n\nThis is a test.',
            'metadata': {
                'original_format': 'md',
                'converted_at': '2024-01-01T12:00:00Z',
                'size': 28
            }
        }
        
        result = handle_api_gateway_event(API_GATEWAY_EVENT)
        
        # verificar respuesta
        self.assertEqual(result['statusCode'], 200)
        self.assertIn('Content-Type', result['headers'])
        self.assertIn('Access-Control-Allow-Origin', result['headers'])
        
        # verificar body
        body = json.loads(result['body'])
        self.assertIn('markdown', body)
        self.assertIn('metadata', body)
        
        # verificar llamada a convert_to_markdown
        mock_convert.assert_called_once_with(
            '# Test Markdown\n\nThis is a test.',
            'test.md'
        )
    
    @patch('src.handlers.api.convert_to_markdown')
    def test_handle_api_gateway_event_base64(self, mock_convert):
        """prueba manejo de contenido base64"""
        mock_convert.return_value = {
            'markdown': 'Test content',
            'metadata': {'original_format': 'txt'}
        }
        
        result = handle_api_gateway_event(API_GATEWAY_EVENT_BASE64)
        
        self.assertEqual(result['statusCode'], 200)
        # verificar que se decodificó el base64
        mock_convert.assert_called_once()
        args = mock_convert.call_args[0]
        self.assertEqual(args[0], b'Test content')
    
    def test_handle_api_gateway_event_unauthorized(self):
        """prueba rechazo por falta de autorización"""
        result = handle_api_gateway_event(API_GATEWAY_EVENT_NO_AUTH)
        
        self.assertEqual(result['statusCode'], 401)
        body = json.loads(result['body'])
        self.assertEqual(body['error'], 'Unauthorized')
    
    def test_handle_api_gateway_event_missing_body(self):
        """prueba error por falta de body"""
        event = {
            'httpMethod': 'POST',
            'headers': {'Authorization': 'Bearer test-api-key'},
            'body': ''
        }
        
        result = handle_api_gateway_event(event)
        
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertEqual(body['error'], 'Missing request body')
    
    def test_handle_api_gateway_event_missing_content(self):
        """prueba error por falta de content en request"""
        event = {
            'httpMethod': 'POST',
            'headers': {'Authorization': 'Bearer test-api-key'},
            'body': '{"filename": "test.txt"}'
        }
        
        result = handle_api_gateway_event(event)
        
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertEqual(body['error'], 'Missing content in request')
    
    @patch('src.handlers.api.convert_to_markdown')
    def test_handle_api_gateway_event_conversion_error(self, mock_convert):
        """prueba manejo de error en conversión"""
        mock_convert.side_effect = Exception("Conversion failed")
        
        result = handle_api_gateway_event(API_GATEWAY_EVENT)
        
        self.assertEqual(result['statusCode'], 500)
        body = json.loads(result['body'])
        self.assertEqual(body['error'], 'Internal server error')
        self.assertIn('Conversion failed', body['details'])
    
    @patch('src.handlers.api.convert_to_markdown')
    def test_handle_direct_invocation_success(self, mock_convert):
        """prueba invocación directa exitosa"""
        mock_convert.return_value = {
            'markdown': '# Direct Test\n\nThis is a direct invocation test.',
            'metadata': {'original_format': 'md'}
        }
        
        result = handle_direct_invocation(DIRECT_INVOCATION_EVENT)
        
        self.assertIn('markdown', result)
        mock_convert.assert_called_once()
    
    @patch('src.handlers.api.convert_to_markdown')
    def test_handle_direct_invocation_base64(self, mock_convert):
        """prueba invocación directa con base64"""
        mock_convert.return_value = {
            'markdown': 'Test content for direct',
            'metadata': {'original_format': 'txt'}
        }
        
        result = handle_direct_invocation(DIRECT_INVOCATION_EVENT_BASE64)
        
        mock_convert.assert_called_once()
        args = mock_convert.call_args[0]
        self.assertEqual(args[0], b'Test content for direct')
    
    def test_handle_direct_invocation_invalid_event(self):
        """prueba error con evento inválido"""
        invalid_events = [
            {},  # evento vacío
            {'filename': 'test.txt'},  # sin content
            'not a dict',  # no es diccionario
            None  # None
        ]
        
        for event in invalid_events:
            with self.assertRaises(ValueError) as context:
                handle_direct_invocation(event)
            self.assertIn("Direct invocation requires 'content' field", 
                         str(context.exception))


if __name__ == '__main__':
    unittest.main()