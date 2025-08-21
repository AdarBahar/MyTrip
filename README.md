# RoadTrip Planner

A production-ready road trip planning application with route optimization, collaborative trip planning, and interactive maps.

## Features

- 🗺️ Interactive route planning with MapTiler maps
- 🚗 Multiple routing profiles (car, motorcycle, bike)
- 👥 Collaborative trip planning with team members
- 📍 Custom pins and waypoints
- 🔄 Route alternatives and optimization
- 📱 Responsive design for mobile and desktop
- 🌍 Support for GraphHopper Cloud and self-hosted routing

## Tech Stack

### Backend
- **Python 3.11** with FastAPI
- **MySQL 8.0+** database
- **SQLAlchemy 2** with Alembic migrations
- **Pydantic v2** for data validation
- **PyMySQL** for database connectivity

### Frontend
- **Next.js 14** with App Router and TypeScript
- **TailwindCSS** with shadcn/ui components
- **TanStack Query** for server state management
- **Zustand** for client state management
- **MapTiler SDK JS** for interactive maps

### Infrastructure
- **Docker Compose** for local development
- **MySQL** database (external)
- **GraphHopper** (cloud or self-hosted) for routing
- **MapTiler** for map tiles and geocoding

## Quick Start

### Automated Setup (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd roadtrip-planner

# Run the setup script
./setup.sh
```

The setup script will:
- Create `.env` file from template
- Optionally download OSM data for self-hosted routing
- Install pre-commit hooks
- Build and start all services
- Run database migrations
- Seed with demo data

### Manual Setup

1. **Environment setup:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration:
   # - Database connection (DB_HOST, DB_USER, DB_PASSWORD, etc.)
   # - GRAPHHOPPER_API_KEY (for cloud routing)
   # - MAPTILER_API_KEY (for maps)
   ```

2. **Start services:**
   ```bash
   make up
   ```

3. **Initialize database:**
   ```bash
   make db.migrate
   make db.seed
   ```

### Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: External MySQL server (configured in .env)

## Development Commands

```bash
# Start all services
make up

# Stop all services
make down

# View logs
make logs

# Run database migrations
make db.migrate

# Seed database with demo data
make db.seed

# Run tests
make test

# Backend development (without Docker)
cd backend
uvicorn app.main:app --reload

# Frontend development (without Docker)
cd frontend
pnpm dev
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

- **Database**: PostgreSQL connection settings
- **GraphHopper**: API key for cloud or self-hosted URL
- **MapTiler**: API key for maps and geocoding
- **App**: Secret keys and CORS settings

## Project Structure

```
roadtrip-planner/
├── backend/           # FastAPI backend application
├── frontend/          # Next.js frontend application
├── infrastructure/    # Docker, deployment configs
├── docs/             # Documentation and guides
├── .env.example      # Environment variables template
├── docker-compose.yml
├── Makefile
└── README.md
```

## API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

## Contributing

1. Install pre-commit hooks: `pre-commit install`
2. Follow the coding standards (enforced by hooks)
3. Write tests for new features
4. Update documentation as needed

## License

MIT License - see LICENSE file for details.