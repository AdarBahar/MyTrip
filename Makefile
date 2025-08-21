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
	@echo ""
	@echo "Testing commands:"
	@echo "  test         - Run all tests"
	@echo "  test.backend - Run backend API tests"
	@echo "  test.auth    - Run authentication tests"
	@echo "  test.trips   - Run trips API tests"
	@echo "  test.routing - Run routing API tests"
	@echo "  test.health  - Run health check tests"
	@echo "  test.coverage- Run tests with coverage report"
	@echo "  test.quick   - Run quick tests only"
	@echo "  test.frontend- Run frontend tests"
	@echo "  test.e2e     - Run end-to-end tests"
	@echo "  test.watch   - Run tests in watch mode"
	@echo ""
	@echo "Database commands:"
	@echo "  db.migrate   - Run database migrations"
	@echo "  db.seed      - Seed database with demo data"
	@echo "  db.reset     - Reset database (drop and recreate)"
	@echo ""
	@echo "Development commands:"
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
	@echo "🧪 Running all tests..."
	cd backend && python run_tests.py all --verbose

test.backend:
	@echo "🧪 Running backend API tests..."
	cd backend && python run_tests.py all --verbose

test.auth:
	@echo "🧪 Running authentication tests..."
	cd backend && python run_tests.py auth --verbose

test.trips:
	@echo "🧪 Running trips API tests..."
	cd backend && python run_tests.py trips --verbose

test.trip-dates:
	@echo "🧪 Running trip date management tests..."
	cd backend && python run_tests.py trips --verbose
	cd frontend && pnpm test -- tests/components/trips tests/lib/api/trips.test.ts tests/integration/trip-date-management.test.tsx

test.routing:
	@echo "🧪 Running routing API tests..."
	cd backend && python run_tests.py routing --verbose

test.health:
	@echo "🧪 Running health check tests..."
	cd backend && python run_tests.py health --verbose

test.coverage:
	@echo "🧪 Running tests with coverage report..."
	cd backend && python run_tests.py all --coverage --verbose

test.quick:
	@echo "🧪 Running quick tests (excluding slow tests)..."
	cd backend && pytest -m "not slow" --tb=short

test.frontend:
	@echo "🧪 Running frontend tests..."
	cd frontend && pnpm test

test.e2e:
	@echo "🧪 Running end-to-end tests..."
	cd frontend && pnpm test:e2e

test.watch:
	@echo "🧪 Running tests in watch mode..."
	cd backend && pytest --tb=short -f

# Setup commands for new developers
setup:
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file from .env.example"; fi
	$(MAKE) install
	@echo "Setup complete! Run 'make up' to start the application."