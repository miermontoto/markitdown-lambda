import unittest
import os
from src.core.converters import convert_to_markdown


class TestPDFConversion(unittest.TestCase):
    """
    pruebas de integración para conversión de PDFs
    """
    
    def setUp(self):
        """configurar rutas de archivos de prueba"""
        self.test_files_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_files')
        self.test_pdf_path = os.path.join(self.test_files_dir, 'test.pdf')
    
    def test_pdf_file_exists(self):
        """verificar que el archivo PDF de prueba existe"""
        self.assertTrue(os.path.exists(self.test_pdf_path), 
                        f"Test PDF not found at {self.test_pdf_path}")
    
    def test_convert_pdf_to_markdown(self):
        """prueba conversión de PDF a markdown"""
        # leer el archivo PDF
        with open(self.test_pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        # convertir a markdown
        result = convert_to_markdown(pdf_content, 'test.pdf')
        
        # verificar estructura del resultado
        self.assertIn('markdown', result)
        self.assertIn('metadata', result)
        
        # verificar contenido
        markdown_text = result['markdown']
        self.assertIsInstance(markdown_text, str)
        self.assertGreater(len(markdown_text), 0)
        
        # verificar que contiene texto esperado
        self.assertIn('Test PDF Document', markdown_text)
        self.assertIn('test PDF file', markdown_text)
        self.assertIn('markitdown conversion', markdown_text)
        
        # verificar metadata
        metadata = result['metadata']
        self.assertEqual(metadata['original_format'], 'pdf')
        self.assertIn('converted_at', metadata)
        self.assertIn('size', metadata)
        self.assertGreater(metadata['size'], 0)
    
    def test_convert_pdf_binary_handling(self):
        """verificar que maneja correctamente contenido binario de PDF"""
        with open(self.test_pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        # verificar que es contenido binario (empieza con %PDF)
        self.assertTrue(pdf_content.startswith(b'%PDF'))
        
        # debe poder convertir sin errores
        result = convert_to_markdown(pdf_content, 'document.pdf')
        self.assertIn('markdown', result)
        self.assertIsInstance(result['markdown'], str)


if __name__ == '__main__':
    unittest.main()