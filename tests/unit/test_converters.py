import unittest
from src.core.converters import convert_to_markdown


class TestConverters(unittest.TestCase):
    """tests para el módulo de conversión"""
    
    def test_convert_text_to_markdown(self):
        """prueba conversión de texto simple"""
        content = "Hello World"
        result = convert_to_markdown(content)
        
        self.assertIn('markdown', result)
        self.assertIn('metadata', result)
        self.assertEqual(result['metadata']['original_format'], 'text')
        
    def test_convert_with_filename(self):
        """prueba conversión con nombre de archivo"""
        content = "# Test Content"
        result = convert_to_markdown(content, "test.md")
        
        self.assertIn('markdown', result)
        self.assertEqual(result['metadata']['original_format'], 'md')


if __name__ == '__main__':
    unittest.main()