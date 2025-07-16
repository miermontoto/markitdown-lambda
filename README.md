# markitdown-lambda

Lambda wrapper que convierte cualquier archivo a Markdown usando [markitdown de Microsoft](https://github.com/microsoft/markitdown).

## Requisitos

- Node.js 18+ (recomendado: usar [fnm](https://github.com/Schniz/fnm))
- pnpm (`npm install -g pnpm`) - gestor de paquetes más rápido y eficiente
- Python 3.11
- AWS CLI configurado
- Serverless Framework (`pnpm install -g serverless`)

## Setup

### Dependencias

```bash
# opción 1: usando make
make install      # instala dependencias de producción
make install-dev  # instala también dependencias de desarrollo
```

### Configurar entorno

```bash
# configurar entorno
cp .env.example .env

# editar .env con tus valores
```

### Despliegue

```bash
# desplegar en AWS
pnpm deploy
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
pnpm try

# o con tu propio evento
pnpm invoke mi-evento.json

# ver logs
pnpm logs

# ver todos los comandos disponibles
pnpm run
make help
```

## Tests

```bash
# ejecutar todos los tests
make test

# ejecutar tests con reporte de cobertura
make coverage
```

El reporte de cobertura muestra:

- En terminal: qué líneas no están cubiertas
- En HTML: abre `htmlcov/index.html` para ver detalles

## Calidad de código

```bash
# ejecutar linter (flake8)
make lint

# verificar tipos con pyright
make typecheck

# ejecutar solo pyright
make pyright

# ejecutar todas las verificaciones (lint + typecheck + tests)
make check
```

### Herramientas de calidad:

- **Flake8**: Linter para detectar errores de estilo y sintaxis
- **Pyright**: Analizador de tipos de Microsoft para Python
