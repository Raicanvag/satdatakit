# SatDataKit Makefile
# Author: Rafael Cañete Vazquez

.PHONY: help test lint format clean docker-build docker-run

help:
	@echo "SatDataKit Development Commands"
	@echo "  test          Run test suite"
	@echo "  lint          Run linters"
	@echo "  format        Format code"
	@echo "  clean         Remove build artifacts"
	@echo "  docker-build  Build Docker image"
	@echo "  docker-run    Run Jupyter Lab in Docker"

test:
	pytest tests/ -v --cov=satdatakit

lint:
	ruff check src/satdatakit tests
	mypy src/satdatakit

format:
	black src/satdatakit tests
	ruff check --fix src/satdatakit tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/

docker-build:
	docker-compose build satdatakit

docker-run:
	docker-compose up satdatakit
