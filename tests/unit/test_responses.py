import unittest
import json
from src.core.responses import (
    ResponseBuilder,
    create_api_response,
    create_error_response
)


class TestResponseBuilder(unittest.TestCase):
    """pruebas para ResponseBuilder genérico"""
    
    def test_build_basic_response(self):
        """prueba construir respuesta básica"""
        response = ResponseBuilder.build(200)
        
        self.assertEqual(response, {'statusCode': 200})
    
    def test_build_with_body_dict(self):
        """prueba construir respuesta con body dict"""
        body = {"message": "Success", "data": {"id": 123}}
        response = ResponseBuilder.build(200, body)
        
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('body', response)
        self.assertIsInstance(response['body'], str)
        
        parsed_body = json.loads(response['body'])
        self.assertEqual(parsed_body['message'], 'Success')
        self.assertEqual(parsed_body['data']['id'], 123)
    
    def test_build_with_body_string(self):
        """prueba construir respuesta con body string"""
        response = ResponseBuilder.build(404, "Not found")
        
        self.assertEqual(response['statusCode'], 404)
        self.assertEqual(response['body'], "Not found")
    
    def test_build_with_headers(self):
        """prueba construir respuesta con headers"""
        headers = {
            'Content-Type': 'text/plain',
            'X-Custom-Header': 'custom-value'
        }
        response = ResponseBuilder.build(201, "Created", headers)
        
        self.assertEqual(response['statusCode'], 201)
        self.assertEqual(response['headers'], headers)
        self.assertEqual(response['body'], "Created")
    
    def test_build_with_base64_encoded(self):
        """prueba construir respuesta con base64"""
        response = ResponseBuilder.build(200, "data", is_base64_encoded=True)
        
        self.assertEqual(response['statusCode'], 200)
        self.assertTrue(response['isBase64Encoded'])
    
    def test_success_response(self):
        """prueba respuesta de éxito"""
        data = {"result": "ok", "count": 5}
        response = ResponseBuilder.success(data)
        
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('body', response)
        
        body = json.loads(response['body'])
        self.assertEqual(body['result'], 'ok')
        self.assertEqual(body['count'], 5)
    
    def test_success_with_custom_status(self):
        """prueba respuesta de éxito con status personalizado"""
        response = ResponseBuilder.success("Created", status_code=201)
        
        self.assertEqual(response['statusCode'], 201)
        self.assertEqual(response['body'], "Created")
    
    def test_success_with_headers(self):
        """prueba respuesta de éxito con headers"""
        headers = {'Location': '/resource/123'}
        response = ResponseBuilder.success(
            {"id": 123},
            status_code=201,
            headers=headers
        )
        
        self.assertEqual(response['statusCode'], 201)
        self.assertEqual(response['headers'], headers)
    
    def test_error_response_basic(self):
        """prueba respuesta de error básica"""
        response = ResponseBuilder.error("Something went wrong")
        
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'Something went wrong')
    
    def test_error_with_custom_status(self):
        """prueba error con status personalizado"""
        response = ResponseBuilder.error("Not found", status_code=404)
        
        self.assertEqual(response['statusCode'], 404)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'Not found')
    
    def test_error_with_type(self):
        """prueba error con tipo"""
        response = ResponseBuilder.error(
            "Invalid input",
            status_code=400,
            error_type="ValidationError"
        )
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'Invalid input')
        self.assertEqual(body['error_type'], 'ValidationError')
    
    def test_error_with_details(self):
        """prueba error con detalles"""
        details = {
            'field': 'email',
            'reason': 'invalid format'
        }
        response = ResponseBuilder.error(
            "Validation failed",
            status_code=422,
            details=details
        )
        
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'Validation failed')
        self.assertEqual(body['details'], details)
    
    def test_json_response(self):
        """prueba respuesta JSON"""
        data = {"key": "value", "number": 42}
        response = ResponseBuilder.json(data)
        
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['headers']['Content-Type'], 'application/json')
        
        body = json.loads(response['body'])
        self.assertEqual(body, data)
    
    def test_json_with_custom_headers(self):
        """prueba JSON con headers personalizados"""
        data = {"test": "data"}
        custom_headers = {'X-Total-Count': '100'}
        
        response = ResponseBuilder.json(data, headers=custom_headers)
        
        headers = response['headers']
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertEqual(headers['X-Total-Count'], '100')
    
    def test_batch_response(self):
        """prueba respuesta batch"""
        results = [
            {"id": 1, "status": "success"},
            {"id": 2, "status": "success"},
            {"id": 3, "status": "error", "error": "Failed"}
        ]
        
        response = ResponseBuilder.batch(results)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['results'], results)
        self.assertNotIn('summary', body)
    
    def test_batch_with_summary(self):
        """prueba batch con resumen"""
        results = [
            {"status": "success"},
            {"status": "success"},
            {"status": "error"}
        ]
        summary = {
            'total': 3,
            'success': 2,
            'errors': 1
        }
        
        response = ResponseBuilder.batch(results, summary=summary)
        
        body = json.loads(response['body'])
        self.assertEqual(body['results'], results)
        self.assertEqual(body['summary'], summary)
    
    def test_batch_with_custom_status(self):
        """prueba batch con status personalizado"""
        results = []
        response = ResponseBuilder.batch(results, status_code=204)
        
        self.assertEqual(response['statusCode'], 204)


class TestCompatibilityFunctions(unittest.TestCase):
    """pruebas para funciones de compatibilidad"""
    
    def test_create_api_response(self):
        """prueba función de compatibilidad create_api_response"""
        body = {"test": "data"}
        response = create_api_response(201, body)
        
        self.assertEqual(response['statusCode'], 201)
        self.assertIn('headers', response)
        self.assertEqual(response['headers']['Content-Type'], 'application/json')
        self.assertEqual(response['headers']['Access-Control-Allow-Origin'], '*')
        
        parsed_body = json.loads(response['body'])
        self.assertEqual(parsed_body, body)
    
    def test_create_error_response(self):
        """prueba función de compatibilidad create_error_response"""
        error = RuntimeError("Test error")
        response = create_error_response(error)
        
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'Test error')
        self.assertEqual(body['error_type'], 'RuntimeError')


if __name__ == '__main__':
    unittest.main()