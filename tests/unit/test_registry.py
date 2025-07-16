import unittest
from unittest.mock import MagicMock, patch
from src.handlers.base import EventHandler
from src.handlers.registry import (
    HandlerRegistry, 
    register_handler, 
    get_handler_for_event, 
    clear_registry, 
    list_registered_handlers,
    auto_register_handlers
)


class TestHandler1(EventHandler):
    """handler de prueba 1"""
    def can_handle(self, event):
        return event.get('type') == 'test1'
    
    def handle(self, event, context=None):
        return {"handler": "test1"}


class TestHandler2(EventHandler):
    """handler de prueba 2"""
    def can_handle(self, event):
        return event.get('type') == 'test2'
    
    def handle(self, event, context=None):
        return {"handler": "test2"}


class FailingHandler(EventHandler):
    """handler que falla al inicializar"""
    def __init__(self):
        raise RuntimeError("Initialization failed")
    
    def can_handle(self, event):
        return False
    
    def handle(self, event, context=None):
        return {}


class TestHandlerRegistry(unittest.TestCase):
    """pruebas para HandlerRegistry"""
    
    def setUp(self):
        """crear registro limpio para cada test"""
        self.registry = HandlerRegistry()
    
    def test_register_single_handler(self):
        """prueba registrar un solo handler"""
        self.registry.register(TestHandler1)
        handlers = self.registry.list_handlers()
        self.assertEqual(len(handlers), 1)
        self.assertEqual(handlers[0], 'TestHandler1')
    
    def test_register_multiple_handlers(self):
        """prueba registrar múltiples handlers"""
        self.registry.register(TestHandler1)
        self.registry.register(TestHandler2)
        
        handlers = self.registry.list_handlers()
        self.assertEqual(len(handlers), 2)
        self.assertIn('TestHandler1', handlers)
        self.assertIn('TestHandler2', handlers)
    
    def test_register_with_priority(self):
        """prueba registrar handlers con prioridad"""
        self.registry.register(TestHandler1, priority=5)
        self.registry.register(TestHandler2, priority=10)
        
        handlers = self.registry.list_handlers()
        # TestHandler2 debe estar primero por mayor prioridad
        self.assertEqual(handlers[0], 'TestHandler2')
        self.assertEqual(handlers[1], 'TestHandler1')
    
    def test_get_handler_for_matching_event(self):
        """prueba obtener handler para evento que coincide"""
        self.registry.register(TestHandler1)
        self.registry.register(TestHandler2)
        
        # evento para handler 1
        event1 = {"type": "test1"}
        handler1 = self.registry.get_handler(event1)
        self.assertIsInstance(handler1, TestHandler1)
        
        # evento para handler 2
        event2 = {"type": "test2"}
        handler2 = self.registry.get_handler(event2)
        self.assertIsInstance(handler2, TestHandler2)
    
    def test_get_handler_no_match(self):
        """prueba obtener handler cuando no hay coincidencia"""
        self.registry.register(TestHandler1)
        self.registry.register(TestHandler2)
        
        event = {"type": "unknown"}
        handler = self.registry.get_handler(event)
        self.assertIsNone(handler)
    
    def test_clear_registry(self):
        """prueba limpiar el registro"""
        self.registry.register(TestHandler1)
        self.registry.register(TestHandler2)
        
        self.assertEqual(len(self.registry.list_handlers()), 2)
        
        self.registry.clear()
        self.assertEqual(len(self.registry.list_handlers()), 0)
    
    def test_lazy_initialization(self):
        """prueba que los handlers se inicializan lazy"""
        self.registry.register(TestHandler1)
        
        # no debe haber handlers instanciados aún
        self.assertEqual(len(self.registry._handlers), 0)
        
        # al buscar un handler, se deben inicializar
        event = {"type": "test1"}
        handler = self.registry.get_handler(event)
        
        self.assertIsNotNone(handler)
        self.assertEqual(len(self.registry._handlers), 1)
    
    def test_handler_initialization_error(self):
        """prueba manejo de error en inicialización de handler"""
        self.registry.register(FailingHandler)
        self.registry.register(TestHandler1)
        
        # debe continuar con otros handlers aunque uno falle
        event = {"type": "test1"}
        handler = self.registry.get_handler(event)
        
        self.assertIsInstance(handler, TestHandler1)
        # solo debe haber inicializado el handler exitoso
        self.assertEqual(len(self.registry._handlers), 1)
    
    def test_priority_ordering(self):
        """prueba que la prioridad funciona correctamente"""
        # handler que maneja todos los eventos
        class CatchAllHandler(EventHandler):
            def can_handle(self, event):
                return True
            def handle(self, event, context=None):
                return {"handler": "catchall"}
        
        # registrar con diferentes prioridades
        self.registry.register(CatchAllHandler, priority=1)
        self.registry.register(TestHandler1, priority=10)
        
        # aunque CatchAllHandler puede manejar todo,
        # TestHandler1 debe ser evaluado primero por mayor prioridad
        event = {"type": "test1"}
        handler = self.registry.get_handler(event)
        self.assertIsInstance(handler, TestHandler1)


class TestGlobalRegistryFunctions(unittest.TestCase):
    """pruebas para las funciones globales del registro"""
    
    def setUp(self):
        """limpiar registro global antes de cada test"""
        clear_registry()
    
    def tearDown(self):
        """limpiar registro global después de cada test"""
        clear_registry()
    
    def test_register_handler_global(self):
        """prueba registrar handler con función global"""
        register_handler(TestHandler1)
        handlers = list_registered_handlers()
        self.assertIn('TestHandler1', handlers)
    
    def test_get_handler_for_event_global(self):
        """prueba obtener handler con función global"""
        register_handler(TestHandler1)
        
        event = {"type": "test1"}
        handler = get_handler_for_event(event)
        self.assertIsInstance(handler, TestHandler1)
    
    def test_clear_registry_global(self):
        """prueba limpiar registro con función global"""
        register_handler(TestHandler1)
        register_handler(TestHandler2)
        
        self.assertEqual(len(list_registered_handlers()), 2)
        
        clear_registry()
        self.assertEqual(len(list_registered_handlers()), 0)
    
    def test_auto_register_handlers(self):
        """prueba auto-registro de handlers"""
        # limpiar cualquier registro previo
        clear_registry()
        
        # ejecutar auto-registro
        auto_register_handlers()
        
        handlers = list_registered_handlers()
        # debe haber registrado ambos handlers
        self.assertEqual(len(handlers), 2)
        self.assertIn('S3Handler', handlers)
        self.assertIn('ApiHandler', handlers)
    
    @patch('src.handlers.registry.print')
    def test_auto_register_handlers_import_error(self, mock_print):
        """prueba auto-registro cuando hay error de importación"""
        with patch('src.handlers.registry.register_handler') as mock_register:
            mock_register.side_effect = ImportError("Cannot import")
            
            # no debe lanzar excepción
            auto_register_handlers()
            
            # debe haber impreso warning
            mock_print.assert_called()


if __name__ == '__main__':
    unittest.main()