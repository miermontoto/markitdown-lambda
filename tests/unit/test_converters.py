import unittest
from unittest.mock import patch, MagicMock
from src.core.converters import convert_to_markdown


class TestConverters(unittest.TestCase):
    """pruebas para el módulo de conversión"""
    
    def test_convert_text_to_markdown(self):
        """prueba conversión de texto simple"""
        content = "Hello World"
        result = convert_to_markdown(content)
        
        self.assertIn('markdown', result)
        self.assertIn('metadata', result)
        self.assertEqual(result['metadata']['original_format'], 'text')
        self.assertIsInstance(result['metadata']['size'], int)
        self.assertIn('converted_at', result['metadata'])
        
    def test_convert_with_filename(self):
        """prueba conversión con nombre de archivo"""
        content = "# Test Content\n\nThis is a test."
        result = convert_to_markdown(content, "test.md")
        
        self.assertIn('markdown', result)
        self.assertEqual(result['metadata']['original_format'], 'md')
        
    def test_convert_bytes_content(self):
        """prueba conversión de contenido en bytes"""
        content = b"Test bytes content"
        result = convert_to_markdown(content)
        
        self.assertIn('markdown', result)
        self.assertIn('Test bytes content', result['markdown'])
        
    def test_convert_binary_file(self):
        """prueba conversión de archivo binario"""
        # crear contenido binario de prueba
        binary_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        
        with patch('src.core.converters.markitdown') as mock_markitdown:
            # configurar mock
            mock_result = MagicMock()
            mock_result.text_content = "Mocked image content"
            mock_markitdown.convert.return_value = mock_result
            
            result = convert_to_markdown(binary_content, "test.png")
            
            # verificar que se llamó convert con archivo temporal
            mock_markitdown.convert.assert_called_once()
            
            self.assertEqual(result['markdown'], "Mocked image content")
            self.assertEqual(result['metadata']['original_format'], 'png')
    
    def test_convert_with_different_extensions(self):
        """prueba conversión con diferentes extensiones"""
        test_cases = [
            ("test.pdf", "pdf"),
            ("document.docx", "docx"),
            ("spreadsheet.xlsx", "xlsx"),
            ("presentation.pptx", "pptx"),
            ("data.csv", "csv"),
            ("config.json", "json"),
            ("webpage.html", "html"),
            ("noextension", "unknown")
        ]
        
        for filename, expected_format in test_cases:
            result = convert_to_markdown("Test content", filename)
            self.assertEqual(result['metadata']['original_format'], expected_format,
                             f"Failed for {filename}")
    
    def test_convert_error_handling(self):
        """prueba manejo de errores en conversión"""
        with patch('src.core.converters.markitdown') as mock_markitdown:
            # configurar mock para lanzar excepción
            mock_markitdown.convert_stream.side_effect = Exception("Conversion failed")
            
            with self.assertRaises(Exception) as context:
                convert_to_markdown("Test content")
            
            self.assertIn("Error converting to markdown", str(context.exception))
    
    def test_metadata_completeness(self):
        """verificar que metadata esté completa"""
        result = convert_to_markdown("Test content", "test.txt")
        
        required_fields = ['original_format', 'converted_at', 'size', 'title']
        for field in required_fields:
            self.assertIn(field, result['metadata'],
                          f"Missing metadata field: {field}")


if __name__ == '__main__':
    unittest.main()