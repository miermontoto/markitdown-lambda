.PHONY: help install deploy test clean lint format

help:
	@echo "Comandos disponibles:"
	@echo "  make install  - Instalar dependencias"
	@echo "  make deploy   - Desplegar a AWS"
	@echo "  make test     - Ejecutar pruebas"
	@echo "  make clean    - Limpiar archivos temporales"
	@echo "  make lint     - Verificar código"
	@echo "  make format   - Formatear código"

install:
	npm install
	pip install -r requirements.txt

deploy:
	npm run deploy

test:
	python -m pytest tests/
	npm test

clean:
	npm run clean
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	python -m flake8 src/

format:
	python -m black src/