# fixtures para pruebas

API_GATEWAY_EVENT = {
    "httpMethod": "POST",
    "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-api-key"
    },
    "body": '{"content": "# Test Markdown\\n\\nThis is a test.", "filename": "test.md"}',
    "isBase64Encoded": False,
    "requestContext": {
        "accountId": "123456789012",
        "apiId": "1234567890",
        "protocol": "HTTP/1.1",
        "httpMethod": "POST",
        "path": "/convert",
        "stage": "prod",
        "requestId": "test-request-id"
    }
}

API_GATEWAY_EVENT_BASE64 = {
    "httpMethod": "POST",
    "headers": {
        "Content-Type": "application/json",
        "X-API-Key": "test-api-key"
    },
    "body": '{"content": "VGVzdCBjb250ZW50", "filename": "test.txt", "base64": true}',
    "isBase64Encoded": False
}

API_GATEWAY_EVENT_NO_AUTH = {
    "httpMethod": "POST",
    "headers": {
        "Content-Type": "application/json"
    },
    "body": '{"content": "Test content"}',
    "isBase64Encoded": False
}

S3_EVENT = {
    "Records": [{
        "eventVersion": "2.1",
        "eventSource": "aws:s3",
        "awsRegion": "eu-west-1",
        "eventTime": "2024-01-01T12:00:00.000Z",
        "eventName": "ObjectCreated:Put",
        "s3": {
            "bucket": {
                "name": "test-bucket",
                "arn": "arn:aws:s3:::test-bucket"
            },
            "object": {
                "key": "input/test-document.txt",
                "size": 1024,
                "eTag": "test-etag"
            }
        }
    }]
}

DIRECT_INVOCATION_EVENT = {
    "content": "# Direct Test\n\nThis is a direct invocation test.",
    "filename": "direct.md"
}

DIRECT_INVOCATION_EVENT_BASE64 = {
    "content": "VGVzdCBjb250ZW50IGZvciBkaXJlY3Q=",
    "filename": "direct.txt",
    "base64": True
}