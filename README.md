# markitdown-lambda

Lambda wrapper que convierte cualquier archivo a Markdown usando [markitdown de Microsoft](https://github.com/microsoft/markitdown).

## Requisitos

- Node.js 18+ (recomendado: usar [fnm](https://github.com/Schniz/fnm))
- pnpm (`npm install -g pnpm`) - gestor de paquetes más rápido y eficiente
- Python 3.11
- AWS CLI configurado
- Serverless Framework (`pnpm install -g serverless`)

## Setup

### Instalación de dependencias

```bash
# opción 1: usando make
make install      # instala dependencias de producción
make install-dev  # instala también dependencias de desarrollo

# opción 2: manualmente
pnpm install                     # dependencias node
pip install -r requirements.txt  # dependencias python

# para desarrollo (incluye pytest, black, flake8)
pip install -r requirements-dev.txt

# nota: si usas uv (gestor de paquetes Python más rápido)
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt
```

### Configuración

```bash
# configurar entorno
cp config/.env.example .env

# editar .env con tus valores
```

### Despliegue

```bash
# desplegar en AWS
pnpm run deploy
```

## Uso

### API REST

```bash
# convertir contenido directo
curl -X POST https://<subdomain>.<domain>/convert \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{"content": "# Hola mundo"}'

# convertir archivo en base64 (usando X-API-Key)
curl -X POST https://<subdomain>.<domain>/convert \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "content": "base64-del-archivo",
    "filename": "documento.pdf",
    "base64": true
  }'
```

### Integración con S3

- Cualquier archivo subido a `s3://<bucket>/input/` aparecerá convertido en `s3://<bucket>/output/`.
- Los archivos se borran automáticamente después de 15 días.
- Si hay errores, se guardan en `s3://<bucket>/errors/`.

### Invocación directa

```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='markdown-converter-prod-markdownConverter',
    Payload=json.dumps({
        'content': 'Contenido a convertir',
        'filename': 'doc.txt'
    })
)
```

## Variables de entorno

- `S3_BUCKET_NAME`: Bucket único para todo (input/, output/, errors/)
- `AWS_MEMORY_SIZE`: RAM de la Lambda (default: 1024 MB)
- `AWS_TIMEOUT_IN_SECS`: Timeout (default: 300 segundos)
- `API_KEY`: Token de autorización (opcional - si no se configura, la API estará abierta)

## Autorización

La API soporta dos formas de enviar el token:

- **Bearer Token**: `Authorization: Bearer <API_KEY>`
- **X-API-Key**: `X-API-Key: <API_KEY>`

*nota: la autorización solo aplica para requests HTTP. Los eventos de S3 e invocaciones directas usan permisos IAM.*

## Desarrollo local

```bash
# probar con evento de ejemplo
pnpm run try

# o con tu propio evento
pnpm run invoke mi-evento.json

# ver logs
pnpm run logs

# ver todos los comandos disponibles
pnpm run
```

## Tests

```bash
# ejecutar todas las pruebas
pnpm test
```

### Estructura de pruebas

- **tests/unit/**: Pruebas unitarias para cada módulo
  - `test_auth.py`: Autorización y API keys
  - `test_converters.py`: Conversión a markdown
  - `test_api_handler.py`: Manejo de API Gateway
  - `test_s3_handler.py`: Procesamiento de S3
  - `test_utils.py`: Funciones utilitarias

- **tests/integration/**: Pruebas de integración
  - `test_lambda_handler.py`: Flujos completos end-to-end

- **tests/fixtures.py**: Datos de prueba compartidos

## Dependencias

### Producción
- **markitdown**: Biblioteca de Microsoft para conversión a Markdown
- **boto3**: AWS SDK para Python (interacción con S3)

### Desarrollo
- **pytest**: Framework de testing
- **pytest-cov**: Cobertura de código
- **black**: Formateador de código Python
- **flake8**: Linter para Python
- **mypy**: Type checking estático

### Node/Serverless
- **serverless**: Framework de deployment
- **serverless-python-requirements**: Manejo de dependencias Python
- **serverless-dotenv-plugin**: Variables de entorno
- **serverless-domain-manager**: Gestión de dominios personalizados
