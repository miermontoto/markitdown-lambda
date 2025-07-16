import unittest
import os
from unittest.mock import patch
from src.core.auth import validate_api_key


class TestAuth(unittest.TestCase):
    """pruebas para el módulo de autenticación"""
    
    def setUp(self):
        """configurar antes de cada prueba"""
        # guardar valor original de API_KEY si existe
        self.original_api_key = os.environ.get('API_KEY')
    
    def tearDown(self):
        """limpiar después de cada prueba"""
        # restaurar API_KEY original
        if self.original_api_key:
            os.environ['API_KEY'] = self.original_api_key
        elif 'API_KEY' in os.environ:
            del os.environ['API_KEY']
    
    def test_no_api_key_configured(self):
        """si no hay API_KEY configurada, debe permitir acceso"""
        # asegurar que no hay API_KEY
        if 'API_KEY' in os.environ:
            del os.environ['API_KEY']
        
        event = {'headers': {}}
        self.assertTrue(validate_api_key(event))
    
    def test_valid_bearer_token(self):
        """validar bearer token correcto"""
        os.environ['API_KEY'] = 'test-secret-key'
        
        event = {
            'headers': {
                'Authorization': 'Bearer test-secret-key'
            }
        }
        self.assertTrue(validate_api_key(event))
    
    def test_valid_x_api_key(self):
        """validar x-api-key correcto"""
        os.environ['API_KEY'] = 'test-secret-key'
        
        event = {
            'headers': {
                'X-API-Key': 'test-secret-key'
            }
        }
        self.assertTrue(validate_api_key(event))
    
    def test_invalid_bearer_token(self):
        """rechazar bearer token incorrecto"""
        os.environ['API_KEY'] = 'test-secret-key'
        
        event = {
            'headers': {
                'Authorization': 'Bearer wrong-key'
            }
        }
        self.assertFalse(validate_api_key(event))
    
    def test_invalid_x_api_key(self):
        """rechazar x-api-key incorrecto"""
        os.environ['API_KEY'] = 'test-secret-key'
        
        event = {
            'headers': {
                'x-api-key': 'wrong-key'
            }
        }
        self.assertFalse(validate_api_key(event))
    
    def test_missing_auth_headers(self):
        """rechazar si no hay headers de autorización"""
        os.environ['API_KEY'] = 'test-secret-key'
        
        event = {'headers': {}}
        self.assertFalse(validate_api_key(event))
    
    def test_case_insensitive_headers(self):
        """headers deben ser case-insensitive"""
        os.environ['API_KEY'] = 'test-secret-key'
        
        # probar diferentes combinaciones de mayúsculas
        test_cases = [
            {'authorization': 'Bearer test-secret-key'},
            {'AUTHORIZATION': 'Bearer test-secret-key'},
            {'x-api-key': 'test-secret-key'},
            {'X-Api-Key': 'test-secret-key'}
        ]
        
        for headers in test_cases:
            event = {'headers': headers}
            self.assertTrue(validate_api_key(event), 
                          f"Failed for headers: {headers}")


if __name__ == '__main__':
    unittest.main()