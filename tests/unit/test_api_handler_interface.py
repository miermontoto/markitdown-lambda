import unittest
from unittest.mock import patch, MagicMock
import os
from src.handlers.api import ApiHandler
from src.handlers.base import EventHandler
from tests.fixtures import (
    API_GATEWAY_EVENT,
    API_GATEWAY_EVENT_NO_AUTH,
    DIRECT_INVOCATION_EVENT
)


class TestApiHandlerInterface(unittest.TestCase):
    """pruebas para los métodos de interfaz de ApiHandler"""
    
    def setUp(self):
        """configurar antes de cada prueba"""
        self.handler = ApiHandler()
        # configurar API_KEY de prueba
        self.original_api_key = os.environ.get('API_KEY')
        os.environ['API_KEY'] = 'test-api-key'
    
    def tearDown(self):
        """limpiar después de cada prueba"""
        if self.original_api_key:
            os.environ['API_KEY'] = self.original_api_key
        elif 'API_KEY' in os.environ:
            del os.environ['API_KEY']
    
    def test_handler_is_event_handler(self):
        """verifica que ApiHandler implementa EventHandler"""
        self.assertIsInstance(self.handler, EventHandler)
    
    def test_can_handle_api_gateway_event(self):
        """prueba can_handle con evento API Gateway"""
        # evento válido de API Gateway
        self.assertTrue(self.handler.can_handle(API_GATEWAY_EVENT))
        
        # evento con solo httpMethod
        minimal_event = {"httpMethod": "GET"}
        self.assertTrue(self.handler.can_handle(minimal_event))
        
        # evento con solo requestContext
        context_event = {"requestContext": {"accountId": "123"}}
        self.assertTrue(self.handler.can_handle(context_event))
    
    def test_can_handle_direct_invocation(self):
        """prueba can_handle con invocación directa"""
        # evento válido de invocación directa
        self.assertTrue(self.handler.can_handle(DIRECT_INVOCATION_EVENT))
        
        # evento mínimo con content
        minimal_event = {"content": "test"}
        self.assertTrue(self.handler.can_handle(minimal_event))
    
    def test_can_handle_s3_event(self):
        """prueba can_handle no acepta eventos S3"""
        s3_event = {
            "Records": [{
                "eventSource": "aws:s3",
                "s3": {"bucket": {"name": "test"}}
            }]
        }
        self.assertFalse(self.handler.can_handle(s3_event))
    
    def test_can_handle_invalid_events(self):
        """prueba can_handle con eventos inválidos"""
        # evento vacío
        self.assertFalse(self.handler.can_handle({}))
        
        # no es diccionario
        self.assertFalse(self.handler.can_handle("not a dict"))
        self.assertFalse(self.handler.can_handle(None))
        self.assertFalse(self.handler.can_handle([]))
        
        # diccionario sin campos relevantes
        self.assertFalse(self.handler.can_handle({"random": "data"}))
    
    @patch('src.handlers.api.convert_to_markdown')
    def test_handle_routes_to_api_gateway(self, mock_convert):
        """prueba handle enruta correctamente a API Gateway"""
        mock_convert.return_value = {
            'markdown': 'Test content',
            'metadata': {'format': 'md'}
        }
        
        result = self.handler.handle(API_GATEWAY_EVENT)
        
        self.assertEqual(result['statusCode'], 200)
        self.assertIn('headers', result)
        self.assertIn('body', result)
    
    @patch('src.handlers.api.convert_to_markdown')
    def test_handle_routes_to_direct_invocation(self, mock_convert):
        """prueba handle enruta correctamente a invocación directa"""
        expected_result = {
            'markdown': 'Direct content',
            'metadata': {'format': 'txt'}
        }
        mock_convert.return_value = expected_result
        
        result = self.handler.handle(DIRECT_INVOCATION_EVENT)
        
        self.assertEqual(result, expected_result)
    
    def test_handle_with_context(self):
        """prueba handle con contexto Lambda"""
        context = {
            'function_name': 'test-function',
            'request_id': 'test-123'
        }
        
        # el contexto se pasa pero no se usa actualmente
        with patch('src.handlers.api.convert_to_markdown') as mock_convert:
            mock_convert.return_value = {'markdown': 'test'}
            
            result = self.handler.handle(DIRECT_INVOCATION_EVENT, context)
            self.assertIn('markdown', result)
    
    def test_handle_api_gateway_error_returns_response(self):
        """prueba que errores en API Gateway retornan respuesta estructurada"""
        with patch('src.handlers.api.convert_to_markdown') as mock_convert:
            mock_convert.side_effect = Exception("Conversion error")
            
            result = self.handler.handle(API_GATEWAY_EVENT)
            
            # debe retornar respuesta de error, no lanzar excepción
            self.assertEqual(result['statusCode'], 500)
            self.assertIn('error', result['body'])
    
    def test_handle_direct_invocation_error_raises(self):
        """prueba que errores en invocación directa lanzan excepción"""
        invalid_event = {"not_content": "test"}  # falta content requerido
        
        with self.assertRaises(ValueError) as context:
            self.handler.handle(invalid_event)
        
        self.assertIn("Direct invocation requires 'content' field", str(context.exception))
    
    def test_private_methods_exist(self):
        """verifica que los métodos privados existen"""
        self.assertTrue(hasattr(self.handler, '_handle_api_gateway'))
        self.assertTrue(hasattr(self.handler, '_handle_direct_invocation'))
    
    def test_handle_unauthorized_api_request(self):
        """prueba manejo de request no autorizado"""
        result = self.handler.handle(API_GATEWAY_EVENT_NO_AUTH)
        
        self.assertEqual(result['statusCode'], 401)
        self.assertIn('Unauthorized', result['body'])
    
    def test_can_handle_with_content_and_records(self):
        """prueba can_handle cuando evento tiene content y Records"""
        # este caso especial no debe ser manejado por ApiHandler
        mixed_event = {
            "content": "test",
            "Records": [{"eventSource": "aws:s3"}]
        }
        self.assertFalse(self.handler.can_handle(mixed_event))


if __name__ == '__main__':
    unittest.main()