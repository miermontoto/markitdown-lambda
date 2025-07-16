.PHONY: help install install-dev clean test coverage lint typecheck pyright check

help:
	@echo "Comandos disponibles:"
	@echo "  make install     - Instalar todas las dependencias"
	@echo "  make install-dev - Instalar dependencias de desarrollo"
	@echo "  make clean       - Limpiar archivos temporales"
	@echo "  make test        - Ejecutar pruebas"
	@echo "  make coverage    - Ejecutar pruebas con reporte de cobertura"
	@echo "  make lint        - Ejecutar linter (flake8)"
	@echo "  make typecheck   - Ejecutar verificación de tipos (pyright)"
	@echo "  make pyright     - Ejecutar pyright para análisis de tipos"
	@echo "  make check       - Ejecutar tests, lint y typecheck"

install:
	pnpm install
	uv venv
	uv pip install -r requirements.txt

install-dev: install
	uv pip install -r requirements-dev.txt

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

test:
	uv run pytest tests/ -v

coverage:
	uv run pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

lint:
	uv run flake8 src/ tests/

typecheck:
	uv run pyright

pyright:
	uv run pyright

check: lint typecheck test
	@echo "✓ Todas las verificaciones pasaron exitosamente"