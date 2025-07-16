"""
test de integración para el endpoint de health
"""
import json
import pytest
from unittest.mock import patch
from src.handler import lambda_handler


class TestHealthEndpoint:
    """tests de integración para el endpoint de health"""
    
    @pytest.fixture
    def health_event(self):
        """evento http get para /health"""
        return {
            'version': '2.0',
            'routeKey': 'GET /health',
            'rawPath': '/health',
            'headers': {
                'content-type': 'application/json'
            },
            'requestContext': {
                'http': {
                    'method': 'GET',
                    'path': '/health'
                },
                'routeKey': 'GET /health'
            }
        }
    
    def test_health_endpoint_returns_200(self, health_event):
        """verifica que el endpoint de health retorna 200"""
        with patch.dict('os.environ', {
            'APP_NAME': 'test-app',
            'APP_VERSION': '1.2.3',
            'INPUT_BUCKET': 'test-bucket'
        }):
            response = lambda_handler(health_event)
            
            assert response['statusCode'] == 200
            assert 'Content-Type' in response['headers']
            assert response['headers']['Content-Type'] == 'application/json'
            
            body = json.loads(response['body'])
            assert body['status'] == 'healthy'
            assert body['service'] == 'test-app'
            assert body['version'] == '1.2.3'
    
    def test_health_endpoint_no_auth_required(self, health_event):
        """verifica que health no requiere autenticación"""
        with patch.dict('os.environ', {'API_KEY': 'secret-key'}):
            # sin header de autorización
            response = lambda_handler(health_event)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['status'] == 'healthy'