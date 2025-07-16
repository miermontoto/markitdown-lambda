import unittest
import json
from src.core.responses import (
    ResponseBuilder,
    create_api_response,
    create_error_response
)


class TestResponseBuilder(unittest.TestCase):
    """pruebas para ResponseBuilder"""
    
    def test_api_gateway_response_with_dict_body(self):
        """prueba crear respuesta API Gateway con body dict"""
        body = {"message": "Success", "data": {"id": 123}}
        response = ResponseBuilder.api_gateway_response(200, body)
        
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('headers', response)
        self.assertIn('body', response)
        
        # verificar headers por defecto
        headers = response['headers']
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertEqual(headers['Access-Control-Allow-Origin'], '*')
        self.assertIn('Access-Control-Allow-Headers', headers)
        self.assertIn('Access-Control-Allow-Methods', headers)
        
        # verificar body es string JSON
        self.assertIsInstance(response['body'], str)
        parsed_body = json.loads(response['body'])
        self.assertEqual(parsed_body['message'], 'Success')
        self.assertEqual(parsed_body['data']['id'], 123)
    
    def test_api_gateway_response_with_string_body(self):
        """prueba crear respuesta API Gateway con body string"""
        body = "Plain text response"
        response = ResponseBuilder.api_gateway_response(404, body)
        
        self.assertEqual(response['statusCode'], 404)
        self.assertEqual(response['body'], body)
    
    def test_api_gateway_response_with_custom_headers(self):
        """prueba crear respuesta API Gateway con headers personalizados"""
        body = {"status": "ok"}
        custom_headers = {
            'X-Custom-Header': 'custom-value',
            'Content-Type': 'text/plain'  # sobrescribir default
        }
        
        response = ResponseBuilder.api_gateway_response(201, body, custom_headers)
        
        headers = response['headers']
        self.assertEqual(headers['X-Custom-Header'], 'custom-value')
        self.assertEqual(headers['Content-Type'], 'text/plain')
        # otros headers por defecto deben mantenerse
        self.assertEqual(headers['Access-Control-Allow-Origin'], '*')
    
    def test_s3_batch_response(self):
        """prueba crear respuesta batch de S3"""
        results = [
            {"source": "file1.txt", "status": "success", "output": "file1.md"},
            {"source": "file2.txt", "status": "success", "output": "file2.md"},
            {"source": "file3.txt", "status": "error", "error": "Conversion failed"}
        ]
        
        response = ResponseBuilder.s3_batch_response(results)
        
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('body', response)
        
        body = json.loads(response['body'])
        self.assertIn('results', body)
        self.assertIn('summary', body)
        
        # verificar resumen
        summary = body['summary']
        self.assertEqual(summary['total'], 3)
        self.assertEqual(summary['success'], 2)
        self.assertEqual(summary['errors'], 1)
        
        # verificar resultados
        self.assertEqual(len(body['results']), 3)
        self.assertEqual(body['results'], results)
    
    def test_s3_batch_response_all_success(self):
        """prueba respuesta batch con todos exitosos"""
        results = [
            {"source": f"file{i}.txt", "status": "success", "output": f"file{i}.md"}
            for i in range(5)
        ]
        
        response = ResponseBuilder.s3_batch_response(results)
        body = json.loads(response['body'])
        
        self.assertEqual(body['summary']['total'], 5)
        self.assertEqual(body['summary']['success'], 5)
        self.assertEqual(body['summary']['errors'], 0)
    
    def test_s3_batch_response_all_errors(self):
        """prueba respuesta batch con todos errores"""
        results = [
            {"source": f"file{i}.txt", "status": "error", "error": f"Error {i}"}
            for i in range(3)
        ]
        
        response = ResponseBuilder.s3_batch_response(results)
        body = json.loads(response['body'])
        
        self.assertEqual(body['summary']['total'], 3)
        self.assertEqual(body['summary']['success'], 0)
        self.assertEqual(body['summary']['errors'], 3)
    
    def test_direct_invocation_response_success(self):
        """prueba respuesta de invocación directa exitosa"""
        data = {
            "markdown": "# Converted content",
            "metadata": {"format": "md", "size": 100}
        }
        
        response = ResponseBuilder.direct_invocation_response(True, data=data)
        
        # debe retornar los datos directamente
        self.assertEqual(response, data)
    
    def test_direct_invocation_response_error(self):
        """prueba respuesta de invocación directa con error"""
        error_msg = "Processing failed"
        
        response = ResponseBuilder.direct_invocation_response(False, error=error_msg)
        
        self.assertIn('error', response)
        self.assertIn('success', response)
        self.assertEqual(response['error'], error_msg)
        self.assertFalse(response['success'])
    
    def test_direct_invocation_response_invalid_state(self):
        """prueba respuesta de invocación directa con estado inválido"""
        # sin data ni error
        with self.assertRaises(ValueError) as context:
            ResponseBuilder.direct_invocation_response(True)
        
        self.assertIn("either data or error must be provided", str(context.exception))
        
        # success=True pero sin data
        with self.assertRaises(ValueError):
            ResponseBuilder.direct_invocation_response(True, error="error")
        
        # success=False pero sin error
        with self.assertRaises(ValueError):
            ResponseBuilder.direct_invocation_response(False, data={"test": "data"})
    
    def test_error_response_api_gateway(self):
        """prueba respuesta de error para API Gateway"""
        error = RuntimeError("Something went wrong")
        response = ResponseBuilder.error_response(error, 'api_gateway')
        
        self.assertEqual(response['statusCode'], 500)
        self.assertIn('headers', response)
        
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'Internal server error')
        self.assertEqual(body['details'], 'Something went wrong')
    
    def test_error_response_s3(self):
        """prueba respuesta de error para S3"""
        error = ValueError("Invalid file format")
        response = ResponseBuilder.error_response(error, 's3')
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        
        self.assertIn('results', body)
        self.assertEqual(len(body['results']), 1)
        self.assertEqual(body['results'][0]['status'], 'error')
        self.assertEqual(body['results'][0]['error'], 'Invalid file format')
        self.assertEqual(body['results'][0]['source'], 'unknown')
    
    def test_error_response_direct(self):
        """prueba respuesta de error para invocación directa"""
        error = TypeError("Type mismatch")
        response = ResponseBuilder.error_response(error, 'direct')
        
        self.assertIn('error', response)
        self.assertIn('success', response)
        self.assertEqual(response['error'], 'Type mismatch')
        self.assertFalse(response['success'])
    
    def test_error_response_unknown_type(self):
        """prueba respuesta de error para tipo desconocido"""
        error = Exception("Generic error")
        response = ResponseBuilder.error_response(error, 'unknown')
        
        # debe usar formato de invocación directa como default
        self.assertIn('error', response)
        self.assertIn('success', response)
        self.assertEqual(response['error'], 'Generic error')
        self.assertFalse(response['success'])


class TestCompatibilityFunctions(unittest.TestCase):
    """pruebas para funciones de compatibilidad"""
    
    def test_create_api_response(self):
        """prueba función de compatibilidad create_api_response"""
        body = {"test": "data"}
        response = create_api_response(201, body)
        
        self.assertEqual(response['statusCode'], 201)
        self.assertIn('headers', response)
        self.assertIn('body', response)
        
        # verificar que es equivalente a ResponseBuilder
        builder_response = ResponseBuilder.api_gateway_response(201, body)
        self.assertEqual(response, builder_response)
    
    def test_create_error_response(self):
        """prueba función de compatibilidad create_error_response"""
        error = RuntimeError("Test error")
        
        # probar diferentes tipos de evento
        api_response = create_error_response(error, 'api_gateway')
        s3_response = create_error_response(error, 's3')
        direct_response = create_error_response(error, 'direct')
        
        # verificar que son equivalentes a ResponseBuilder
        self.assertEqual(api_response, ResponseBuilder.error_response(error, 'api_gateway'))
        self.assertEqual(s3_response, ResponseBuilder.error_response(error, 's3'))
        self.assertEqual(direct_response, ResponseBuilder.error_response(error, 'direct'))


if __name__ == '__main__':
    unittest.main()