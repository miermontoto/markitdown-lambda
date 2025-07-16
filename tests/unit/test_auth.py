import unittest
from unittest.mock import patch
from src.core.auth import validate_api_key


class TestAuth(unittest.TestCase):
    """pruebas para el módulo de autenticación"""
    
    @patch('src.core.auth.get_config')
    def test_no_api_key_configured(self, mock_get_config):
        """si no hay API_KEY configurada, debe permitir acceso"""
        # simular que no hay API_KEY configurada
        mock_get_config.return_value = None
        
        event = {'headers': {}}
        self.assertTrue(validate_api_key(event))
    
    @patch('src.core.auth.get_config')
    def test_valid_bearer_token(self, mock_get_config):
        """validar bearer token correcto"""
        mock_get_config.return_value = 'test-secret-key'
        
        event = {
            'headers': {
                'Authorization': 'Bearer test-secret-key'
            }
        }
        
        self.assertTrue(validate_api_key(event))
    
    @patch('src.core.auth.get_config')
    def test_valid_x_api_key(self, mock_get_config):
        """validar x-api-key correcto"""
        mock_get_config.return_value = 'test-secret-key'
        
        event = {
            'headers': {
                'X-API-Key': 'test-secret-key'
            }
        }
        
        self.assertTrue(validate_api_key(event))
    
    @patch('src.core.auth.get_config')
    def test_invalid_bearer_token(self, mock_get_config):
        """rechazar bearer token incorrecto"""
        mock_get_config.return_value = 'test-secret-key'
        
        event = {
            'headers': {
                'Authorization': 'Bearer wrong-key'
            }
        }
        
        self.assertFalse(validate_api_key(event))
    
    @patch('src.core.auth.get_config')
    def test_invalid_x_api_key(self, mock_get_config):
        """rechazar x-api-key incorrecto"""
        mock_get_config.return_value = 'test-secret-key'
        
        event = {
            'headers': {
                'X-API-Key': 'wrong-key'
            }
        }
        
        self.assertFalse(validate_api_key(event))
    
    @patch('src.core.auth.get_config')
    def test_missing_auth_headers(self, mock_get_config):
        """rechazar si falta autenticación cuando API_KEY está configurada"""
        mock_get_config.return_value = 'test-secret-key'
        
        event = {'headers': {}}
        
        self.assertFalse(validate_api_key(event))
    
    @patch('src.core.auth.get_config')
    def test_case_insensitive_headers(self, mock_get_config):
        """verificar que los headers son case-insensitive"""
        mock_get_config.return_value = 'test-secret-key'
        
        # diferentes variaciones de case
        header_variations = [
            {'authorization': 'Bearer test-secret-key'},
            {'Authorization': 'Bearer test-secret-key'},
            {'AUTHORIZATION': 'Bearer test-secret-key'},
            {'x-api-key': 'test-secret-key'},
            {'X-Api-Key': 'test-secret-key'},
            {'X-API-KEY': 'test-secret-key'}
        ]
        
        for headers in header_variations:
            event = {'headers': headers}
            self.assertTrue(validate_api_key(event),
                            f"Failed for headers: {headers}")