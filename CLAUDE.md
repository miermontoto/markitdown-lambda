# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Lambda wrapper that converts any file to Markdown using Microsoft's markitdown library. It supports multiple input methods: API REST, S3 events, and direct Lambda invocation.

## Build and Development Commands

```bash
# install dependencies
make install      # instala dependencias de producción
make install-dev  # instala también dependencias de desarrollo

# quality checks  
make check       # ejecutar lint + typecheck + tests (run this before commits)
make lint        # ejecutar flake8
make typecheck   # verificar tipos con pyright
make test        # ejecutar todos los tests
make coverage    # ejecutar tests con reporte de cobertura

# test specific functionality
uv run pytest tests/unit/test_api.py -v        # run specific test file
uv run pytest tests/unit/test_api.py::TestApiHandler::test_handle_api_gateway_event_success -v  # run specific test

# deploy and manage
pnpm deploy      # desplegar en AWS
pnpm remove      # eliminar de AWS
pnpm logs        # ver logs en tiempo real

# local testing
pnpm try         # probar con tests/test_event.json
pnpm invoke <file.json>  # probar con archivo específico
```

## Architecture

The codebase uses a **handler registry pattern** for routing different event types:

1. **Entry Point**: `src/handler.py:lambda_handler` - receives all Lambda events
2. **Registry System**: `src/handlers/registry.py` - auto-discovers and registers handlers by priority
3. **Event Handlers**: 
   - `ApiHandler` (priority 5) - handles API Gateway REST requests
   - `S3Handler` (priority 10) - handles S3 object creation events
4. **Core Components**:
   - `src/core/auth.py` - API authentication (Bearer token or X-API-Key)
   - `src/core/converters.py` - file to markdown conversion using markitdown
   - `src/core/dependencies.py` - dependency injection container
   - `src/core/responses.py` - response builders for different event types

### Handler Flow
1. Event arrives at `lambda_handler`
2. Registry finds appropriate handler via `can_handle()` method
3. Handler processes event and returns appropriate response format
4. API Gateway events get HTTP responses with CORS headers
5. S3 events process files and save results back to S3

## Testing Strategy

- **Unit tests** in `tests/unit/` - test individual components
- **Integration tests** in `tests/integration/` - test full Lambda flow
- All handlers must implement `EventHandler` abstract base class
- Use dependency injection for testability (S3 client, API key, etc.)

## Environment Configuration

Key environment variables (configured in `.env`):
- `S3_BUCKET_NAME` - bucket for input/output/errors
- `API_KEY` - optional auth token for API
- `AWS_MEMORY_SIZE` - Lambda memory (default: 1024 MB)
- `AWS_TIMEOUT_IN_SECS` - Lambda timeout (default: 300 seconds)

## Code Style Notes

- flake8 ignores: W291 (trailing whitespace), W292 (no newline at EOF), W293 (blank line whitespace)
- comentarios en español minúscula, términos técnicos en inglés
- prefer lambda functions and logical programming over loops