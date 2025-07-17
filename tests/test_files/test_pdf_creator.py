#!/usr/bin/env python3
"""
crea un PDF de prueba simple para los tests
"""
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os


def create_test_pdf():
    """
    crea un PDF simple con texto para pruebas
    """
    pdf_path = os.path.join(os.path.dirname(__file__), 'test.pdf')
    
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    
    # título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "Test PDF Document")
    
    # contenido
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 150, "This is a test PDF file for markitdown conversion.")
    c.drawString(100, height - 180, "It contains multiple lines of text.")
    c.drawString(100, height - 210, "Each line should be converted to markdown.")
    
    # lista
    c.drawString(100, height - 260, "Features:")
    c.drawString(120, height - 280, "• Text extraction")
    c.drawString(120, height - 300, "• Multiple paragraphs")
    c.drawString(120, height - 320, "• Basic formatting")
    
    # guardar
    c.save()
    print(f"Test PDF created at: {pdf_path}")


if __name__ == "__main__":
    create_test_pdf()