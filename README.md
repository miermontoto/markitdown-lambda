# markitdown-lambda

Lambda wrapper que convierte cualquier archivo a Markdown usando [markitdown de Microsoft](https://github.com/microsoft/markitdown).

## Setup

```bash
# instalar dependencias
npm install

# configurar entorno
cp .env.example .env

# desplegar en AWS
npm run deploy
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

Nota: La autorización solo aplica para requests HTTP. Los eventos de S3 y las invocaciones directas usan permisos IAM.

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
