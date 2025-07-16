import os
import tempfile
import io
from markitdown import MarkItDown
from src.utils.utils import get_file_extension, get_current_timestamp

# inicializar markitdown globalmente
markitdown = MarkItDown()


def convert_to_markdown(content, filename=None):
    """convierte contenido a markdown usando markitdown"""
    try:
        # mantener el contenido original en bytes y detectar si es texto
        if isinstance(content, bytes):
            try:
                text_content = content.decode('utf-8')
                is_text = True
            except UnicodeDecodeError:
                # si no se puede decodificar, es binario
                is_text = False
                binary_content = content
        else:
            # si ya es string, es texto
            is_text = True
            text_content = content

        # si tenemos un nombre de archivo y es binario, guardarlo temporalmente
        if filename and not is_text:
            _, ext = os.path.splitext(filename)

            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(binary_content)
                tmp_path = tmp.name

            try:
                result = markitdown.convert(tmp_path)
            finally:
                os.unlink(tmp_path)
        else:
            # convertir texto directamente usando stream
            # crear stream desde el contenido
            if is_text:
                content_stream = io.BytesIO(text_content.encode('utf-8'))
            else:
                # este caso no debería ocurrir, pero por seguridad
                content_stream = io.BytesIO(content if isinstance(content, bytes) else str(content).encode('utf-8'))

            # usar convert_stream
            result = markitdown.convert_stream(content_stream, file_extension=get_file_extension(filename) if filename else '.txt')

        return {
            'markdown': result.text_content,
            'metadata': {
                'original_format': get_file_extension(filename) if filename else 'text',
                'converted_at': get_current_timestamp(),
                'size': len(result.text_content),
                'title': getattr(result, 'title', None)
            }
        }

    except Exception as e:
        raise Exception(f"Error converting to markdown: {str(e)}")
