.PHONY: help up down logs restart clean build test db.migrate db.seed db.reset dev.backend dev.frontend install lint format

# Default target
help:
	@echo "Available commands:"
	@echo "  up           - Start all services with Docker Compose"
	@echo "  down         - Stop all services"
	@echo "  logs         - View logs from all services"
	@echo "  restart      - Restart all services"
	@echo "  clean        - Clean up containers and volumes"
	@echo "  build        - Build all Docker images"
	@echo "  test         - Run all tests"
	@echo "  db.migrate   - Run database migrations"
	@echo "  db.seed      - Seed database with demo data"
	@echo "  db.reset     - Reset database (drop and recreate)"
	@echo "  dev.backend  - Run backend in development mode"
	@echo "  dev.frontend - Run frontend in development mode"
	@echo "  install      - Install dependencies for both backend and frontend"
	@echo "  lint         - Run linting for both backend and frontend"
	@echo "  format       - Format code for both backend and frontend"

# Docker Compose commands
up:
	docker-compose up -d
	@echo "Services started. Access:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend API: http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  Note: Using external MySQL database"

down:
	docker-compose down

logs:
	docker-compose logs -f

restart:
	docker-compose restart

clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

build:
	docker-compose build

# Database commands
db.migrate:
	docker-compose exec backend alembic upgrade head

db.seed:
	docker-compose exec backend python -m app.scripts.seed

db.reset:
	@echo "⚠️  Cannot reset external MySQL database"
	@echo "   Please manually reset your MySQL database and run:"
	@echo "   make db.migrate && make db.seed"

# Development commands (without Docker)
dev.backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev.frontend:
	cd frontend && pnpm dev

# Installation commands
install:
	cd backend && pip install -r requirements.txt
	cd frontend && pnpm install

# Code quality commands
lint:
	cd backend && ruff check . && black --check . && isort --check-only .
	cd frontend && pnpm lint

format:
	cd backend && black . && isort . && ruff check . --fix
	cd frontend && pnpm format

# Testing commands
test:
	cd backend && pytest
	cd frontend && pnpm test

test.e2e:
	cd frontend && pnpm test:e2e

# Setup commands for new developers
setup:
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file from .env.example"; fi
	$(MAKE) install
	@echo "Setup complete! Run 'make up' to start the application."