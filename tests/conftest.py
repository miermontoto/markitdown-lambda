"""
configuración global para los tests
"""
import os
import pytest


@pytest.fixture(autouse=True)
def aws_credentials():
    """
    configura las credenciales de AWS para los tests
    """
    # guardar valores originales
    original_values = {}
    env_vars = {
        'AWS_DEFAULT_REGION': 'us-east-1',
        'AWS_REGION': 'us-east-1',
        'AWS_ACCESS_KEY_ID': 'testing',
        'AWS_SECRET_ACCESS_KEY': 'testing',
        'AWS_SECURITY_TOKEN': 'testing',
        'AWS_SESSION_TOKEN': 'testing',
    }
    
    for key, value in env_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # restaurar valores originales
    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value