"""
tests unitarios para el health handler
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from src.handlers.health import HealthHandler


class TestHealthHandler:
    """tests para HealthHandler"""
    
    @pytest.fixture
    def handler(self):
        """crea una instancia del handler"""
        return HealthHandler()
    
    @pytest.fixture
    def health_event(self):
        """evento de health check de api gateway"""
        return {
            'requestContext': {
                'http': {
                    'method': 'GET',
                    'path': '/health'
                }
            },
            'rawPath': '/health'
        }
    
    def test_can_handle_health_request(self, handler, health_event):
        """verifica que puede manejar requests de health"""
        assert handler.can_handle(health_event) is True
    
    def test_can_handle_post_health_returns_false(self, handler):
        """verifica que no maneja post en /health"""
        event = {
            'requestContext': {
                'http': {
                    'method': 'POST',
                    'path': '/health'
                }
            },
            'rawPath': '/health'
        }
        assert handler.can_handle(event) is False
    
    def test_can_handle_other_path_returns_false(self, handler):
        """verifica que no maneja otros paths"""
        event = {
            'requestContext': {
                'http': {
                    'method': 'GET',
                    'path': '/convert'
                }
            },
            'rawPath': '/convert'
        }
        assert handler.can_handle(event) is False
    
    @patch('src.handlers.health.get_config')
    def test_handle_returns_health_info(self, mock_get_config, handler, health_event):
        """verifica que retorna información de salud"""
        # configurar mock para retornar valores específicos
        def config_side_effect(key, default=None):
            config_map = {
                'APP_NAME': 'test-converter',
                'APP_VERSION': '2.0.0',
                'AWS_REGION': 'us-east-1',
                'INPUT_BUCKET': 'test-bucket'
            }
            return config_map.get(key, default)
        
        mock_get_config.side_effect = config_side_effect
        
        response = handler.handle(health_event)
        
        assert response['statusCode'] == 200
        assert 'Access-Control-Allow-Origin' in response['headers']
        
        body = json.loads(response['body'])
        assert body['status'] == 'healthy'
        assert body['service'] == 'test-converter'
        assert body['version'] == '2.0.0'
        assert body['region'] == 'us-east-1'
        assert body['bucket'] == 'test-bucket'
    
    def test_handle_with_context(self, handler, health_event):
        """verifica que incluye información del contexto"""
        context = MagicMock()
        context.function_name = 'my-function'
        context.function_version = '$LATEST'
        context.memory_limit_in_mb = 1024
        context.aws_request_id = 'request-123'
        
        response = handler.handle(health_event, context)
        body = json.loads(response['body'])
        
        assert 'function' in body
        assert body['function']['name'] == 'my-function'
        assert body['function']['version'] == '$LATEST'
        assert body['function']['memory_limit'] == 1024
        assert body['function']['request_id'] == 'request-123'