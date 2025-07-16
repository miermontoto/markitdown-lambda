import unittest
from unittest.mock import patch, MagicMock
from src.core.dependencies import (
    DependencyContainer,
    register_dependency,
    get_dependency,
    create_s3_client,
    create_api_key,
    create_bucket_name,
    register_default_dependencies
)


class TestDependencyContainer(unittest.TestCase):
    """pruebas para DependencyContainer"""
    
    def setUp(self):
        """crear contenedor limpio para cada test"""
        self.container = DependencyContainer()
    
    def test_register_and_get_dependency(self):
        """prueba registrar y obtener una dependencia"""
        def create_service():
            return {"type": "service", "id": 123}
        
        self.container.register("test_service", create_service)
        
        service = self.container.get("test_service")
        self.assertEqual(service["type"], "service")
        self.assertEqual(service["id"], 123)
    
    def test_singleton_behavior(self):
        """prueba comportamiento singleton"""
        call_count = 0
        
        def create_service():
            nonlocal call_count
            call_count += 1
            return {"instance": call_count}
        
        self.container.register("singleton_service", create_service, singleton=True)
        
        # obtener múltiples veces
        service1 = self.container.get("singleton_service")
        service2 = self.container.get("singleton_service")
        service3 = self.container.get("singleton_service")
        
        # debe ser la misma instancia
        self.assertEqual(service1, service2)
        self.assertEqual(service2, service3)
        self.assertEqual(call_count, 1)  # factory solo se llamó una vez
    
    def test_non_singleton_behavior(self):
        """prueba comportamiento no-singleton"""
        call_count = 0
        
        def create_service():
            nonlocal call_count
            call_count += 1
            return {"instance": call_count}
        
        self.container.register("transient_service", create_service, singleton=False)
        
        # obtener múltiples veces
        service1 = self.container.get("transient_service")
        service2 = self.container.get("transient_service")
        service3 = self.container.get("transient_service")
        
        # deben ser diferentes instancias
        self.assertNotEqual(service1["instance"], service2["instance"])
        self.assertNotEqual(service2["instance"], service3["instance"])
        self.assertEqual(call_count, 3)  # factory se llamó cada vez
    
    def test_get_unregistered_dependency(self):
        """prueba obtener dependencia no registrada"""
        with self.assertRaises(KeyError) as context:
            self.container.get("nonexistent")
        
        self.assertIn("Dependency 'nonexistent' not registered", str(context.exception))
    
    def test_clear_dependencies(self):
        """prueba limpiar todas las dependencias"""
        self.container.register("service1", lambda: {"id": 1})
        self.container.register("service2", lambda: {"id": 2})
        
        # verificar que existen
        self.assertIsNotNone(self.container.get("service1"))
        self.assertIsNotNone(self.container.get("service2"))
        
        # limpiar
        self.container.clear()
        
        # verificar que ya no existen
        with self.assertRaises(KeyError):
            self.container.get("service1")
        with self.assertRaises(KeyError):
            self.container.get("service2")
    
    def test_register_override(self):
        """prueba sobrescribir una dependencia registrada"""
        self.container.register("service", lambda: {"version": 1})
        service_v1 = self.container.get("service")
        self.assertEqual(service_v1["version"], 1)
        
        # sobrescribir
        self.container.register("service", lambda: {"version": 2})
        service_v2 = self.container.get("service")
        self.assertEqual(service_v2["version"], 2)


class TestFactoryFunctions(unittest.TestCase):
    """pruebas para las funciones factory"""
    
    @patch('boto3.client')
    def test_create_s3_client(self, mock_boto3_client):
        """prueba crear cliente S3"""
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        
        client = create_s3_client()
        
        mock_boto3_client.assert_called_once_with('s3')
        self.assertEqual(client, mock_client)
    
    @patch('src.core.dependencies.get_config')
    def test_create_api_key(self, mock_get_config):
        """prueba obtener API key desde config"""
        # sin API_KEY
        mock_get_config.return_value = None
        key = create_api_key()
        self.assertIsNone(key)
        
        # con API_KEY
        mock_get_config.return_value = 'test-key-123'
        key = create_api_key()
        self.assertEqual(key, 'test-key-123')
    
    @patch('src.core.dependencies.get_config')
    def test_create_bucket_name(self, mock_get_config):
        """prueba obtener nombre de bucket desde config"""
        # sin bucket name
        mock_get_config.return_value = None
        bucket = create_bucket_name()
        self.assertIsNone(bucket)
        
        # con bucket name
        mock_get_config.return_value = 'my-test-bucket'
        bucket = create_bucket_name()
        self.assertEqual(bucket, 'my-test-bucket')


class TestGlobalDependencyFunctions(unittest.TestCase):
    """pruebas para las funciones globales de dependencias"""
    
    def setUp(self):
        """limpiar contenedor global antes de cada test"""
        from src.core.dependencies import _container
        _container.clear()
        # re-registrar dependencias por defecto
        register_default_dependencies()
    
    def tearDown(self):
        """limpiar contenedor global después de cada test"""
        from src.core.dependencies import _container
        _container.clear()
    
    def test_register_and_get_global_dependency(self):
        """prueba registrar y obtener dependencia global"""
        def create_test_service():
            return {"name": "global_service"}
        
        register_dependency("test_global", create_test_service)
        
        service = get_dependency("test_global")
        self.assertEqual(service["name"], "global_service")
    
    @patch('boto3.client')
    def test_default_dependencies_registered(self, mock_boto3_client):
        """prueba que las dependencias por defecto se registran"""
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        
        # las dependencias por defecto deben estar disponibles
        s3_client = get_dependency('s3_client')
        self.assertEqual(s3_client, mock_client)
        
        # verificar que es singleton (no se crea nuevo cliente)
        s3_client2 = get_dependency('s3_client')
        self.assertEqual(s3_client, s3_client2)
        mock_boto3_client.assert_called_once()
    
    @patch('src.core.dependencies.get_config')
    def test_api_key_dependency(self, mock_get_config):
        """prueba dependencia de API key"""
        mock_get_config.return_value = 'dependency-test-key'
        # limpiar y re-registrar para que tome el nuevo valor
        from src.core.dependencies import _container
        _container.clear()
        register_default_dependencies()
        
        api_key = get_dependency('api_key')
        self.assertEqual(api_key, 'dependency-test-key')
    
    @patch('src.core.dependencies.get_config')
    def test_bucket_name_dependency(self, mock_get_config):
        """prueba dependencia de nombre de bucket"""
        mock_get_config.return_value = 'dependency-test-bucket'
        # limpiar y re-registrar para que tome el nuevo valor
        from src.core.dependencies import _container
        _container.clear()
        register_default_dependencies()
        
        bucket_name = get_dependency('bucket_name')
        self.assertEqual(bucket_name, 'dependency-test-bucket')


if __name__ == '__main__':
    unittest.main()