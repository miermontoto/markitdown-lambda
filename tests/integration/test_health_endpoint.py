"""
test de integración para el endpoint de health
"""
import json
import pytest


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
        from src.handler import lambda_handler
        
        response = lambda_handler(health_event)
        
        assert response['statusCode'] == 200
        assert 'Content-Type' in response['headers']
        assert response['headers']['Content-Type'] == 'application/json'
        
        body = json.loads(response['body'])
        assert body['status'] == 'healthy'
        # verificar que los campos esperados estén presentes
        assert 'service' in body
        assert 'version' in body
        assert 'region' in body
        assert 'runtime' in body
        assert 'bucket' in body
        
        # verificar que los valores no estén vacíos
        assert body['service'] is not None
        assert body['version'] is not None
    
    def test_health_endpoint_no_auth_required(self, health_event):
        """verifica que health no requiere autenticación"""
        from src.handler import lambda_handler
        
        # sin header de autorización
        response = lambda_handler(health_event)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'healthy'