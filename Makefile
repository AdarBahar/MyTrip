.PHONY: help up down logs restart clean build test db.migrate db.seed db.reset dev.backend dev.frontend install lint format

# Default target
help:
	@echo "Available commands:"
	@echo "  up           - Start all services with Docker Compose"
	@echo "  down         - Stop all services"
	@echo "  logs         - View logs from all services"
	@echo "  restart      - Restart all services"
	@echo "  hard-restart - Stop, clean, and restart all services"
	@echo "  status       - Check service status and health"
	@echo "  fix-docker   - Fix Docker daemon issues"
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
	@echo "  check.config - Validate application configuration"
	@echo "  graphhopper-israel - Download Israel map, clear cache, start GH (selfhost)"
	@echo "  up-selfhost       - Start only GraphHopper (selfhost) and wait for health"
	@echo "  down-selfhost     - Stop and remove GraphHopper (selfhost)"
	@echo "  api-e2e           - Run full-flow API test and export artifacts"

# Auto-enable selfhost GraphHopper profile when .env sets GRAPHHOPPER_MODE=selfhost
PROFILE_FLAGS := $(shell grep -q '^GRAPHHOPPER_MODE=selfhost' .env 2>/dev/null && echo '--profile selfhost' || echo '')

# Docker Compose commands
up:
	docker-compose $(PROFILE_FLAGS) up -d
	@echo "Services started. Access:"
	@echo "  Frontend: http://localhost:3500"
	@echo "  Backend API: http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  Note: Using external MySQL database"

down:
	docker-compose down

logs:
	docker-compose $(PROFILE_FLAGS) logs -f

restart:
	# Ensure GraphHopper is included and up when in selfhost mode
	docker-compose $(PROFILE_FLAGS) up -d graphhopper
	docker-compose $(PROFILE_FLAGS) restart
	@echo "Services restarted. Checking health..."
	@sleep 5
	@$(MAKE) status

clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

build:
	docker-compose $(PROFILE_FLAGS) build

# Status and health check commands
status:
	@echo "🔍 Checking service status..."
	@docker ps --filter "name=roadtrip" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "🏥 Health checks:"
	@curl -s http://localhost:8000/health 2>/dev/null | jq -r '"Backend: " + .status + " (" + .routing_mode + " mode)"' || echo "Backend: Not responding"
	@curl -s http://localhost:8989/health 2>/dev/null | sed 's/^/GraphHopper: /' || echo "GraphHopper: Not responding"
	@curl -s http://localhost:3500 2>/dev/null >/dev/null && echo "Frontend: Responding" || echo "Frontend: Not responding"

fix-docker:
	@echo "🔧 Running Docker restart fix..."
	@./scripts/fix_docker_restart.sh

hard-restart:
	@echo "🔄 Performing hard restart..."
	docker-compose down --remove-orphans
	docker system prune -f
	$(MAKE) up
	@echo "Hard restart complete!"

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

# GraphHopper selfhost helpers
.PHONY: graphhopper-israel
graphhopper-israel:
	curl -L -o data/graphhopper/map.osm.pbf https://download.geofabrik.de/asia/israel-and-palestine-latest.osm.pbf
	rm -rf data/graphhopper/graph-cache || true
	docker-compose --profile selfhost up -d graphhopper
	@echo "Waiting for GraphHopper health..."
	@until curl -fsS http://localhost:8989/health >/dev/null 2>&1; do echo "."; sleep 3; done
	@echo "GraphHopper is healthy on :8989"

.PHONY: up-selfhost
up-selfhost:
	docker-compose --profile selfhost up -d graphhopper
	@echo "Waiting for GraphHopper health..."
	@until curl -fsS http://localhost:8989/health >/dev/null 2>&1; do echo "."; sleep 3; done
	@echo "GraphHopper is healthy on :8989"

.PHONY: down-selfhost
down-selfhost:
	docker-compose --profile selfhost stop graphhopper || true
	docker-compose --profile selfhost rm -f graphhopper || true

.PHONY: api-e2e
api-e2e:
	@echo "Waiting for backend health..."
	@until curl -fsS http://localhost:8000/health >/dev/null 2>&1; do echo "."; sleep 2; done
	python3 tools/api_full_flow.py --base http://localhost:8000 --out .reports/api_full_flow_latest

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

# Configuration validation
check.config:
	@echo "🔍 Validating application configuration..."
	cd backend && python scripts/check_config.py

# Setup commands for new developers
setup:
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file from .env.example"; fi
	$(MAKE) install
	@echo "Setup complete! Run 'make up' to start the application."