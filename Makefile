.PHONY: dev down test smoke build lint help

help:
	@echo "Available targets:"
	@echo "  dev    - Start development environment"
	@echo "  down   - Stop development environment"
	@echo "  test   - Run test suite"
	@echo "  smoke  - Run smoke tests"
	@echo "  build  - Build Docker images"
	@echo "  lint   - Run linter (ruff)"

dev:
	docker-compose -f infra/docker-compose.yml up -d

down:
	docker-compose -f infra/docker-compose.yml down

test:
	pytest tests/ -v

smoke:
	pytest tests/ -v -m smoke

build:
	docker-compose -f infra/docker-compose.yml build

lint:
	ruff check src/ scripts/ tests/
