.PHONY: help install proto build up down logs test clean

# ============================================================================
# HLCS - Makefile
# ============================================================================

help:  ## Show this help
	@echo "HLCS - High-Level Consciousness System"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install Python dependencies
	pip install -r requirements.txt

proto:  ## Generate gRPC code from proto files
	bash scripts/generate_proto.sh

build:  ## Build Docker image
	docker-compose build

up:  ## Start HLCS (Docker)
	docker-compose up -d
	@echo ""
	@echo "✅ HLCS started!"
	@echo "   REST API: http://localhost:4001"
	@echo "   gRPC:     localhost:4000 (placeholder)"
	@echo ""
	@echo "Try: curl http://localhost:4001/health"

down:  ## Stop HLCS
	docker-compose down

logs:  ## Show logs
	docker-compose logs -f hlcs

restart:  ## Restart HLCS
	docker-compose restart hlcs

status:  ## Check status
	@curl -s http://localhost:4001/api/v1/status | python -m json.tool

test-query:  ## Test query endpoint
	@curl -X POST http://localhost:4001/api/v1/query \
		-H "Content-Type: application/json" \
		-d '{"query": "Explica qué es HLCS"}' | python -m json.tool

test:  ## Run tests
	pytest tests/ -v --cov=src/hlcs --cov-report=html

test-fast:  ## Run tests (no coverage)
	pytest tests/ -v

clean:  ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ htmlcov/ .coverage

dev-rest:  ## Run REST server locally (dev mode)
	@echo "Starting HLCS REST Gateway on http://localhost:4001..."
	python -m src.hlcs.rest_gateway.server

dev-grpc:  ## Run gRPC server locally (dev mode)
	@echo "Starting HLCS gRPC Server on localhost:4000..."
	python -m src.hlcs.grpc_server.server

shell:  ## Open shell in running container
	docker-compose exec hlcs /bin/bash

ps:  ## Show running containers
	docker-compose ps
