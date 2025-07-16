"""
tests unitarios para el servicio de configuración
"""
import pytest
import json
import os
import unittest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from src.core.config import ConfigService, get_config_service, get_config


class TestConfigService:
    """tests para ConfigService"""
    
    @pytest.fixture
    def mock_secrets_client(self):
        """mock del cliente de secrets manager"""
        return MagicMock()
    
    @pytest.fixture
    def config_service(self, mock_secrets_client):
        """crea una instancia del servicio con mock client"""
        service = ConfigService(secrets_client=mock_secrets_client)
        service.clear_cache()
        return service
    
    def test_get_from_env_var(self, config_service):
        """verifica que obtiene valores de variables de entorno"""
        with patch.dict('os.environ', {'TEST_VAR': 'test_value'}):
            value = config_service.get('TEST_VAR')
            assert value == 'test_value'
    
    def test_get_from_secrets_manager(self, mock_secrets_client):
        """verifica que obtiene valores de secrets manager"""
        # configurar mock con el config secret
        config_data = {
            'API_KEY': 'secret_value',
            'OTHER_KEY': 'other_value'
        }
        mock_secrets_client.get_secret_value.return_value = {
            'SecretString': json.dumps(config_data)
        }
        
        with patch.dict('os.environ', {'USE_SECRETS_MANAGER': 'true', 'SECRETS_PREFIX': 'test', 'STAGE': 'dev'}):
            # crear servicio con las env vars correctas
            service = ConfigService(secrets_client=mock_secrets_client)
            value = service.get('API_KEY')
            
            assert value == 'secret_value'
            # debe intentar obtener el config secret
            mock_secrets_client.get_secret_value.assert_called_with(SecretId='test/dev/config')
    
    def test_get_from_secrets_manager_json(self, config_service, mock_secrets_client):
        """verifica que maneja secretos json correctamente"""
        # configurar config secret
        config_data = {
            'API_KEY': 'json_secret_value',
            'DEBUG': 'true'
        }
        mock_secrets_client.get_secret_value.return_value = {
            'SecretString': json.dumps(config_data)
        }
        
        value = config_service.get('API_KEY')
        assert value == 'json_secret_value'
    
    def test_get_from_secrets_manager_complex_json(self, config_service, mock_secrets_client):
        """verifica que maneja valores complejos en el config secret"""
        # configurar config secret con valores complejos
        config_data = {
            'SIMPLE_VALUE': 'test',
            'NUMERIC_VALUE': 123,
            'BOOLEAN_VALUE': True,
            'COMPLEX_VALUE': {"key1": "value1", "key2": {"nested": "value2"}}
        }
        mock_secrets_client.get_secret_value.return_value = {
            'SecretString': json.dumps(config_data)
        }
        
        # valores simples se convierten a string
        assert config_service.get('SIMPLE_VALUE') == 'test'
        assert config_service.get('NUMERIC_VALUE') == '123'
        assert config_service.get('BOOLEAN_VALUE') == 'True'
        # valores complejos también se convierten a string
        complex_value = config_service.get('COMPLEX_VALUE')
        assert complex_value == "{'key1': 'value1', 'key2': {'nested': 'value2'}}"
    
    def test_secrets_manager_not_found(self, config_service, mock_secrets_client):
        """verifica que maneja secretos no encontrados"""
        # simular ResourceNotFoundException
        error_response = {'Error': {'Code': 'ResourceNotFoundException'}}
        mock_secrets_client.get_secret_value.side_effect = ClientError(error_response, 'GetSecretValue')
        
        with patch.dict('os.environ', {'TEST_VAR': 'env_value'}):
            value = config_service.get('TEST_VAR')
            assert value == 'env_value'
    
    def test_secrets_manager_error(self, config_service, mock_secrets_client):
        """verifica que maneja errores de secrets manager"""
        # simular otro error
        error_response = {'Error': {'Code': 'AccessDeniedException'}}
        mock_secrets_client.get_secret_value.side_effect = ClientError(error_response, 'GetSecretValue')
        
        with patch.dict('os.environ', {'TEST_VAR': 'env_value'}):
            value = config_service.get('TEST_VAR')
            assert value == 'env_value'
    
    def test_priority_secrets_over_env(self, config_service, mock_secrets_client):
        """verifica que secrets manager tiene prioridad sobre env vars"""
        config_data = {
            'TEST_VAR': 'secret_value'
        }
        mock_secrets_client.get_secret_value.return_value = {
            'SecretString': json.dumps(config_data)
        }
        
        with patch.dict('os.environ', {'TEST_VAR': 'env_value'}):
            value = config_service.get('TEST_VAR')
            assert value == 'secret_value'
    
    def test_cache_behavior(self, config_service, mock_secrets_client):
        """verifica que cachea valores correctamente"""
        # configurar respuesta del config secret
        config_secret = {
            'CACHE_TEST': 'cached_value',
            'OTHER_KEY': 'other_value'
        }
        mock_secrets_client.get_secret_value.return_value = {
            'SecretString': json.dumps(config_secret)
        }
        
        # primera llamada
        value1 = config_service.get('CACHE_TEST')
        # segunda llamada - debe venir del cache
        value2 = config_service.get('CACHE_TEST')
        # tercera llamada a otra clave - también del mismo secreto cacheado
        value3 = config_service.get('OTHER_KEY')
        
        assert value1 == value2 == 'cached_value'
        assert value3 == 'other_value'
        # debe llamar a secrets manager solo una vez (para cargar el config secret)
        assert mock_secrets_client.get_secret_value.call_count == 1
    
    def test_clear_cache(self, config_service):
        """verifica que limpia la cache"""
        with patch.dict('os.environ', {'TEST_VAR': 'value1'}):
            config_service.get('TEST_VAR')
            
        # cambiar valor en env
        with patch.dict('os.environ', {'TEST_VAR': 'value2'}):
            # sin limpiar cache, debe retornar valor cacheado
            assert config_service.get('TEST_VAR') == 'value1'
            
            # limpiar cache
            config_service.clear_cache()
            
            # ahora debe retornar nuevo valor
            assert config_service.get('TEST_VAR') == 'value2'
    
    def test_refresh_specific_key(self, config_service):
        """verifica que refresca una clave específica"""
        with patch.dict('os.environ', {'TEST_VAR': 'value1'}):
            config_service.get('TEST_VAR')
            
        with patch.dict('os.environ', {'TEST_VAR': 'value2'}):
            # refrescar clave específica
            new_value = config_service.refresh('TEST_VAR')
            assert new_value == 'value2'
    
    def test_get_bool_true_values(self, config_service):
        """verifica conversión a booleano para valores true"""
        for true_value in ['true', 'True', 'TRUE', '1', 'yes', 'YES', 'on', 'ON']:
            with patch.dict('os.environ', {'BOOL_VAR': true_value}):
                assert config_service.get_bool('BOOL_VAR') is True
    
    def test_get_bool_false_values(self, config_service):
        """verifica conversión a booleano para valores false"""
        for false_value in ['false', 'False', '0', 'no', 'off', 'anything']:
            with patch.dict('os.environ', {'BOOL_VAR': false_value}):
                assert config_service.get_bool('BOOL_VAR') is False
    
    def test_get_bool_default(self, config_service):
        """verifica valor por defecto para booleanos"""
        assert config_service.get_bool('NON_EXISTENT', default=True) is True
        assert config_service.get_bool('NON_EXISTENT', default=False) is False
    
    def test_get_int_valid(self, config_service):
        """verifica conversión a entero válida"""
        with patch.dict('os.environ', {'INT_VAR': '42'}):
            assert config_service.get_int('INT_VAR') == 42
    
    def test_get_int_invalid(self, config_service):
        """verifica manejo de entero inválido"""
        with patch.dict('os.environ', {'INT_VAR': 'not_a_number'}):
            assert config_service.get_int('INT_VAR', default=10) == 10
    
    def test_get_json_valid(self, config_service):
        """verifica parseo de json válido"""
        json_data = {"key": "value", "number": 123}
        with patch.dict('os.environ', {'JSON_VAR': json.dumps(json_data)}):
            result = config_service.get_json('JSON_VAR')
            assert result == json_data
    
    def test_get_json_invalid(self, config_service):
        """verifica manejo de json inválido"""
        with patch.dict('os.environ', {'JSON_VAR': 'not_json'}):
            default = {"default": "value"}
            result = config_service.get_json('JSON_VAR', default=default)
            assert result == default
    
    def test_disable_secrets_manager(self, config_service, mock_secrets_client):
        """verifica que se puede deshabilitar secrets manager"""
        with patch.dict('os.environ', {
            'USE_SECRETS_MANAGER': 'false',
            'TEST_VAR': 'env_value'
        }):
            # reinicializar servicio con nueva config
            service = ConfigService(secrets_client=mock_secrets_client)
            value = service.get('TEST_VAR')
            
            assert value == 'env_value'
            # no debe llamar a secrets manager
            mock_secrets_client.get_secret_value.assert_not_called()


class TestConfigHelpers:
    """tests para las funciones helper"""
    
    @patch('src.core.config._config_service')
    def test_get_config(self, mock_service):
        """verifica función helper get_config"""
        mock_service.get.return_value = 'test_value'
        
        # limpiar cache de lru_cache
        get_config.cache_clear()
        
        value = get_config('TEST_KEY', 'default')
        assert value == 'test_value'
        mock_service.get.assert_called_with('TEST_KEY', 'default')
    
    def test_get_config_service_singleton(self):
        """verifica que get_config_service retorna singleton"""
        service1 = get_config_service()
        service2 = get_config_service()
        assert service1 is service2


class TestConfigSecretIntegration(unittest.TestCase):
    """tests para la integración con el secreto de configuración completo"""
    
    def setUp(self):
        """configurar mocks para cada test"""
        # limpiar variables de entorno
        self.env_backup = os.environ.copy()
        os.environ['USE_SECRETS_MANAGER'] = 'true'
        os.environ['STAGE'] = 'test'
        
    def tearDown(self):
        """restaurar entorno original"""
        os.environ.clear()
        os.environ.update(self.env_backup)
    
    @patch('boto3.client')
    def test_load_config_secret_success(self, mock_boto3_client):
        """verifica que se carga correctamente el secreto de configuración"""
        # configurar mock del cliente
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        
        # configurar respuesta del secreto
        secret_data = {
            'API_KEY': 'secret-key-123',
            'APP_NAME': 'test-app',
            'APP_VERSION': '2.0.0',
            'CUSTOM_SETTING': 'custom-value'
        }
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps(secret_data)
        }
        
        # crear servicio
        service = ConfigService()
        
        # obtener valores
        assert service.get('API_KEY') == 'secret-key-123'
        assert service.get('APP_NAME') == 'test-app'
        assert service.get('APP_VERSION') == '2.0.0'
        assert service.get('CUSTOM_SETTING') == 'custom-value'
        
        # verificar que solo se llamó una vez (cache)
        mock_client.get_secret_value.assert_called_once_with(
            SecretId='markdown-converter/test/config'
        )
    
    @patch('boto3.client')
    def test_config_secret_priority_over_env(self, mock_boto3_client):
        """verifica que el secreto tiene prioridad sobre env vars"""
        # configurar env vars
        os.environ['APP_VERSION'] = '1.0.0'
        os.environ['APP_NAME'] = 'env-app'
        
        # configurar mock del cliente
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        
        # configurar respuesta del secreto
        secret_data = {
            'APP_VERSION': '2.0.0-from-secret',
            'APP_NAME': 'secret-app'
        }
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps(secret_data)
        }
        
        # crear servicio
        service = ConfigService()
        
        # verificar que usa valores del secreto, no de env
        assert service.get('APP_VERSION') == '2.0.0-from-secret'
        assert service.get('APP_NAME') == 'secret-app'
    
    @patch('boto3.client')
    def test_fallback_to_env_when_not_in_secret(self, mock_boto3_client):
        """verifica fallback a env var cuando no está en el secreto"""
        # configurar env var
        os.environ['LOCAL_ONLY_VAR'] = 'local-value'
        
        # configurar mock del cliente
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        
        # configurar respuesta del secreto (sin LOCAL_ONLY_VAR)
        secret_data = {
            'APP_NAME': 'test-app'
        }
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps(secret_data)
        }
        
        # crear servicio
        service = ConfigService()
        
        # verificar que obtiene del secreto lo que existe
        assert service.get('APP_NAME') == 'test-app'
        
        # verificar que obtiene de env var lo que no está en secreto
        assert service.get('LOCAL_ONLY_VAR') == 'local-value'
        
        # verificar que solo se hizo una llamada al secrets manager
        mock_client.get_secret_value.assert_called_once_with(
            SecretId='markdown-converter/test/config'
        )
    
    @patch('boto3.client')
    def test_config_secret_cache_behavior(self, mock_boto3_client):
        """verifica que el secreto se cachea correctamente"""
        # configurar mock del cliente
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        
        # configurar respuesta del secreto
        secret_data = {'TEST_KEY': 'test-value'}
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps(secret_data)
        }
        
        # crear servicio
        service = ConfigService()
        
        # hacer múltiples llamadas
        for _ in range(5):
            assert service.get('TEST_KEY') == 'test-value'
        
        # verificar que solo se cargó el secreto una vez
        mock_client.get_secret_value.assert_called_once()
    
    @patch('boto3.client')
    def test_clear_cache_clears_secrets_cache(self, mock_boto3_client):
        """verifica que clear_cache limpia también el cache de secretos"""
        # configurar mock del cliente
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        
        # configurar respuestas del secreto
        secret_data1 = {'TEST_KEY': 'value1'}
        secret_data2 = {'TEST_KEY': 'value2'}
        
        mock_client.get_secret_value.side_effect = [
            {'SecretString': json.dumps(secret_data1)},
            {'SecretString': json.dumps(secret_data2)}
        ]
        
        # crear servicio
        service = ConfigService()
        
        # primera llamada
        assert service.get('TEST_KEY') == 'value1'
        
        # limpiar cache
        service.clear_cache()
        
        # segunda llamada debe cargar nuevo valor
        assert service.get('TEST_KEY') == 'value2'
        
        # verificar que se llamó dos veces
        assert mock_client.get_secret_value.call_count == 2
    
