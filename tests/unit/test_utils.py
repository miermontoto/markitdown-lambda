import unittest
import json
from datetime import datetime
from src.utils.utils import (
    get_file_extension,
    get_current_timestamp,
    create_api_response,
    is_s3_event,
    is_api_gateway_event
)


class TestUtils(unittest.TestCase):
    """pruebas para funciones utilitarias"""
    
    def test_get_file_extension(self):
        """prueba obtención de extensiones de archivo"""
        test_cases = [
            ("document.pdf", "pdf"),
            ("report.docx", "docx"),
            ("data.CSV", "csv"),  # mayúsculas
            ("archive.tar.gz", "gz"),  # extensión múltiple
            ("noextension", "unknown"),
            ("", None),
            (None, None),
            (".hidden", "hidden"),  # archivo oculto
            ("file.with.dots.txt", "txt")
        ]
        
        for filename, expected in test_cases:
            result = get_file_extension(filename)
            self.assertEqual(result, expected, 
                           f"Failed for filename: {filename}")
    
    def test_get_current_timestamp(self):
        """prueba generación de timestamp"""
        # obtener timestamp
        timestamp = get_current_timestamp()
        
        # verificar formato ISO 8601 con Z
        self.assertTrue(timestamp.endswith('Z'))
        
        # verificar que se puede parsear
        try:
            # quitar la Z y parsear
            dt = datetime.fromisoformat(timestamp[:-1])
            self.assertIsInstance(dt, datetime)
        except ValueError:
            self.fail(f"Invalid timestamp format: {timestamp}")
        
        # verificar que es reciente (menos de 1 segundo)
        from datetime import timezone
        now = datetime.now(timezone.utc)
        # parsear con timezone
        parsed_time = datetime.fromisoformat(timestamp[:-1] + '+00:00')
        diff = (now - parsed_time).total_seconds()
        self.assertLess(diff, 1.0)
    
    def test_create_api_response(self):
        """prueba creación de respuesta API"""
        # respuesta exitosa
        response = create_api_response(200, {'message': 'Success'})
        
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['headers']['Content-Type'], 'application/json')
        self.assertEqual(response['headers']['Access-Control-Allow-Origin'], '*')
        
        body = json.loads(response['body'])
        self.assertEqual(body['message'], 'Success')
        
        # respuesta de error
        error_response = create_api_response(400, {'error': 'Bad Request'})
        self.assertEqual(error_response['statusCode'], 400)
        
        # respuesta con body complejo
        complex_body = {
            'data': [1, 2, 3],
            'nested': {'key': 'value'},
            'boolean': True,
            'null': None
        }
        complex_response = create_api_response(201, complex_body)
        parsed_body = json.loads(complex_response['body'])
        self.assertEqual(parsed_body, complex_body)
    
    def test_is_s3_event(self):
        """prueba detección de eventos S3"""
        # evento S3 válido
        s3_event = {
            'Records': [{
                'eventSource': 'aws:s3',
                's3': {'bucket': {'name': 'test'}}
            }]
        }
        self.assertTrue(is_s3_event(s3_event))
        
        # evento no S3
        non_s3_events = [
            {'Records': [{'eventSource': 'aws:sns'}]},  # otro servicio
            {'Records': []},  # sin registros
            {},  # sin Records
            {'httpMethod': 'POST'},  # API Gateway
            None  # None
        ]
        
        for event in non_s3_events:
            self.assertFalse(is_s3_event(event))
    
    def test_is_api_gateway_event(self):
        """prueba detección de eventos API Gateway"""
        # eventos API Gateway válidos
        api_events = [
            {'httpMethod': 'POST', 'body': 'test'},
            {'requestContext': {'apiId': '123'}},
            {'httpMethod': 'GET', 'requestContext': {}}
        ]
        
        for event in api_events:
            self.assertTrue(is_api_gateway_event(event))
        
        # eventos no API Gateway
        non_api_events = [
            {'Records': [{'eventSource': 'aws:s3'}]},  # S3
            {'content': 'test'},  # invocación directa
            {},  # vacío
            None  # None
        ]
        
        for event in non_api_events:
            self.assertFalse(is_api_gateway_event(event))


if __name__ == '__main__':
    unittest.main()