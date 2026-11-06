# DispatchHub

DispatchHub is a personal project for exploring dispatch operations, load management, driver assignments, reporting, authentication, and user-specific dashboard preferences.

> **Personal project disclaimer:** This application is not enterprise software and is not currently being used for real-world dispatch operations. It is a learning and portfolio project. The demo accounts, credentials, data, and configuration are intended for local development only.

## Screenshots

### Dashboard

![DispatchHub dashboard](docs/screenshots/dashboard.png)

### Loads

![Load management](docs/screenshots/loads.png)

### Dispatches

![Dispatch management](docs/screenshots/dispatches.png)

### Download report

![Download dispatch report](docs/screenshots/download-report.png)

### Analytics

![Analytics](docs/screenshots/analytics.png)

### User-specific settings

![User-specific theme settings](docs/screenshots/user-settings.png)

Dashboard layouts and themes are stored per authenticated user. For example, one account can use the Ocean theme while another uses Sunset, and each account's preference is restored after logging back in.

## Features

- Dashboard statistics and jobs-by-status visualization
- Load creation, editing, deletion, filtering, assignment, and detail views
- Driver management and availability tracking
- Dispatch assignment, reassignment, and status tracking
- Dispatch and load summary PDF generation
- JWT authentication with hashed passwords
- Admin and dispatcher roles
- Profile and password management
- User-specific dashboard layout and theme preferences

## Technology stack

- Frontend: React, Vite, CSS
- Backend: FastAPI and Python
- Database: PostgreSQL with SQLAlchemy
- Authentication: JWT and hashed passwords
- Migrations: Alembic
- Local database: PostgreSQL running in Docker

## Local setup

### 1. Start PostgreSQL with Docker

Start Docker Desktop, then create the database container:

```powershell
docker run --name dispatchhub-postgres-clean `
  -e POSTGRES_USER=dispatch `
  -e POSTGRES_PASSWORD=dispatch `
  -e POSTGRES_DB=dispatchhub `
  -p 5433:5432 `
  -d postgres:16
```

If the container already exists, start it with:

```powershell
docker start dispatchhub-postgres-clean
```

### 2. Configure environment variables

Create `.env` in the repository root:

```env
DATABASE_URL=postgresql+psycopg://dispatch:dispatch@localhost:5433/dispatchhub
DISPATCH_JWT_SECRET=replace-with-a-long-random-secret
```

`.env.example` is a safe-to-commit template containing placeholder values. You can copy it to create your local `.env`:

```powershell
Copy-Item .env.example .env
```

Do not commit `.env`. Use a private secret for any environment beyond local development.

### 3. Run the backend

```powershell
cd backend
pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

The API documentation is available at <http://localhost:8000/docs>.

### 4. Run the frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL shown by Vite, usually <http://localhost:5173>.

## Demo accounts

These accounts are seeded for local testing only:

```text
Admin:
  Email: admin@dispatchhub.local
  Password: admin123

Dispatcher:
  Email: dispatcher@dispatchhub.local
  Password: dispatch123
```

To verify user-specific preferences:

1. Log in to one account and open Settings.
2. Select a theme and return to the dashboard.
3. Log out and select the other account.
4. Select a different theme and switch between accounts to verify that each preference is retained separately.

## Tests and checks

Run backend tests from the `backend` directory:

```powershell
python -m unittest discover -s tests -v
```

Run frontend checks from the `frontend` directory:

```powershell
npm run lint
npm run build
```

## Project structure

```text
dispatch-hub/
|-- backend/
|   |-- app/                 # FastAPI application and database models
|   |-- alembic/             # Database migrations
|   `-- tests/               # Backend API tests
|-- frontend/
|   |-- src/                 # React application and styles
|   `-- package.json
|-- docs/
|   `-- screenshots/         # Screenshots used by this README
|-- .env.example             # Safe environment variable template
`-- README.md
```

## Current workspaces

- Dashboard: operational overview, widgets, and KPIs
- Loads: create, edit, search, filter, assign, and download summaries
- Drivers: manage availability and assigned-load counts
- Dispatches: reassign drivers, update status, and download dispatch reports
- Analytics: completion and workload metrics
- Settings: profile, password, and per-user themes
