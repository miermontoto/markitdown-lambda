.PHONY: help install install-dev clean test

help:
	@echo "Comandos disponibles:"
	@echo "  make install     - Instalar todas las dependencias"
	@echo "  make install-dev - Instalar dependencias de desarrollo"
	@echo "  make clean       - Limpiar archivos temporales"
	@echo "  make test        - Ejecutar pruebas"

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