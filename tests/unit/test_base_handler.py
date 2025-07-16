import unittest
from typing import Any
from src.handlers.base import EventHandler


class ConcreteHandler(EventHandler):
    """implementación concreta para testing"""
    
    def __init__(self):
        self.can_handle_result = True
        self.handle_result: Any = {"success": True}
    
    def can_handle(self, event):
        return self.can_handle_result
    
    def handle(self, event, context=None):
        if isinstance(self.handle_result, Exception):
            raise self.handle_result
        return self.handle_result


class TestEventHandler(unittest.TestCase):
    """pruebas para la interfaz base EventHandler"""
    
    def setUp(self):
        """configurar handler de prueba"""
        self.handler = ConcreteHandler()
    
    def test_abstract_methods_must_be_implemented(self):
        """verifica que las clases abstractas no se pueden instanciar"""
        # intentar crear una clase que no implemente todos los métodos abstractos
        class IncompleteHandler(EventHandler):
            def can_handle(self, event):
                return True
            # falta implementar handle()
        
        with self.assertRaises(TypeError):
            IncompleteHandler()  # type: ignore
    
    def test_can_handle_method(self):
        """prueba el método can_handle"""
        event = {"test": "event"}
        
        # caso positivo
        self.handler.can_handle_result = True
        self.assertTrue(self.handler.can_handle(event))
        
        # caso negativo
        self.handler.can_handle_result = False
        self.assertFalse(self.handler.can_handle(event))
    
    def test_handle_method(self):
        """prueba el método handle"""
        event = {"test": "event"}
        context = {"test": "context"}
        
        # caso exitoso
        expected = {"success": True, "data": "test"}
        self.handler.handle_result = expected
        result = self.handler.handle(event, context)
        self.assertEqual(result, expected)
        
        # caso con error
        self.handler.handle_result = ValueError("Test error")
        with self.assertRaises(ValueError):
            self.handler.handle(event, context)
    
    def test_format_response_success(self):
        """prueba format_response con resultado exitoso"""
        result = {"data": "test data"}
        response = self.handler.format_response(result)
        self.assertEqual(response, result)
    
    def test_format_response_error(self):
        """prueba format_response con error"""
        error = ValueError("Test error message")
        response = self.handler.format_response(None, error)
        
        self.assertIn('error', response)
        self.assertIn('error_type', response)
        self.assertEqual(response['error'], 'Test error message')
        self.assertEqual(response['error_type'], 'ValueError')
    
    def test_format_error_response(self):
        """prueba _format_error_response directamente"""
        error = RuntimeError("Runtime error occurred")
        response = self.handler._format_error_response(error)
        
        self.assertEqual(response['error'], 'Runtime error occurred')
        self.assertEqual(response['error_type'], 'RuntimeError')
    
    def test_format_response_with_custom_error(self):
        """prueba format_response con tipo de error personalizado"""
        class CustomError(Exception):
            pass
        
        error = CustomError("Custom error message")
        response = self.handler.format_response(None, error)
        
        self.assertEqual(response['error'], 'Custom error message')
        self.assertEqual(response['error_type'], 'CustomError')
    
    def test_handle_with_no_context(self):
        """prueba handle sin contexto"""
        event = {"test": "event"}
        expected = {"result": "no context"}
        self.handler.handle_result = expected
        
        # llamar sin contexto
        result = self.handler.handle(event)
        self.assertEqual(result, expected)
    
    def test_inheritance_pattern(self):
        """verifica que la herencia funciona correctamente"""
        # verificar que ConcreteHandler es instancia de EventHandler
        self.assertIsInstance(self.handler, EventHandler)
        
        # verificar que tiene todos los métodos requeridos
        self.assertTrue(hasattr(self.handler, 'can_handle'))
        self.assertTrue(hasattr(self.handler, 'handle'))
        self.assertTrue(hasattr(self.handler, 'format_response'))
        self.assertTrue(hasattr(self.handler, '_format_error_response'))


if __name__ == '__main__':
    unittest.main()