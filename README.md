# Brightloop Subscription Management System

A unified subscription management platform
for managing products, plans, customers,
subscriptions, recurring billing, invoices
and payments.

## Tech Stack

### Frontend
- React
- Vite
- Tailwind CSS

### Backend
- Python
- FastAPI
- SQLAlchemy
- Alembic

### Database
- PostgreSQL

### DevOps
- Docker
- Docker Compose

## Core Modules

- Authentication and RBAC
- Customer Management
- Product Management
- Subscription Plans
- Quotation Management
- Subscription Lifecycle
- Recurring Billing
- Invoice Management
- Tax and Discount Management
- Payment Management
- Dashboard and Analytics

## Project Structure

- frontend/ - React application
- backend/ - FastAPI application
- docs/ - Architecture and API documentation

## Local Setup

### Quick Start with Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sarj29/subscription-management-system.git
   cd subscription-management-system
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   *(Update `.env` if you wish to customize credentials or secret keys).*

3. **Build and start all services:**
   ```bash
   docker compose up --build
   ```
   This single command starts the entire 3-tier application:
   - **PostgreSQL** (`brightloop-postgres`): Running on port `5432` with persistent data in the `postgres_data` volume.
   - **FastAPI Backend** (`brightloop-backend`): Waits for PostgreSQL to be healthy, automatically applies database migrations (`alembic upgrade head`), and serves the API on port `8000`.
   - **React Frontend** (`brightloop-frontend`): Waits for backend readiness, compiles the Vite application, and serves the UI on port `3000` with an integrated proxy to the backend API.

4. **Access the application:**
   - **Frontend Web UI:** [http://localhost:3000](http://localhost:3000)
   - **Backend Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
   - **Interactive API Docs (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Alternative Docs (ReDoc):** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Useful Docker Commands

- **Run in detached mode (background):**
  ```bash
  docker compose up --build -d
  ```
- **View live service logs:**
  ```bash
  docker compose logs -f frontend
  docker compose logs -f backend
  docker compose logs -f db
  ```
- **Check service health and status:**
  ```bash
  docker compose ps
  ```
- **Run the backend test suite inside the container:**
  ```bash
  docker compose exec backend pytest
  ```
- **Stop all services (safely preserves database data):**
  ```bash
  docker compose down
  ```

## Contributors

- Sreya
- Merin
- Neha
- Tahseen
