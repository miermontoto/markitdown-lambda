# Markdown Converter Lambda

Lambda que convierte cualquier archivo a Markdown usando markitdown de Microsoft.

## ¿Qué hace?

Convierte PDFs, Word, Excel, PowerPoint, HTML, CSV, JSON y más a Markdown limpio.

## Setup rápido

```bash
# configurar entorno
npm install
cp .env.example .env

# desplegar
npm run deploy
```

## Cómo usarlo

### API REST

```bash
# convertir contenido directo
curl -X POST https://md.okticket.io/convert \
  -H "Content-Type: application/json" \
  -d '{"content": "# Hola mundo"}'

# convertir archivo en base64
curl -X POST https://md.okticket.io/convert \
  -H "Content-Type: application/json" \
  -d '{
    "content": "base64-del-archivo",
    "filename": "documento.pdf",
    "base64": true
  }'
```

### S3 automático

Sube cualquier archivo a `s3://tu-bucket/input/` y aparecerá convertido en `s3://tu-bucket/output/`.

Los archivos se borran automáticamente después de 15 días. Si hay errores, se guardan en `s3://tu-bucket/errors/`.

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
- `AWS_MEMORY_SIZE`: RAM del Lambda (default: 1024 MB)
- `AWS_TIMEOUT_IN_SECS`: Timeout (default: 300 segundos)

## Desarrollo local

```bash
# probar localmente
npm test

# o con tu propio evento
npm run invoke mi-evento.json

# ver logs
npm run logs

# ver todos los comandos disponibles
npm run
```

## Notas

- Serverless Framework v4
- Python 3.11 en ARM64 (más barato y rápido)
- Soporta archivos hasta el límite de Lambda (10GB con EFS, 512MB sin él)
