# DispatchHub

DispatchHub is a dispatch dashboard for managing loads, drivers, assignments, reports, and operational settings.

## Stack

- Frontend: React, Vite, Tailwind CSS
- Backend: FastAPI (Python), SQLAlchemy, PostgreSQL
- Authentication: JWT with hashed passwords
- Migrations: Alembic

## PostgreSQL with Docker

Start Docker Desktop, then create the database container:

```powershell
docker run --name dispatchhub-postgres-clean `
  -e POSTGRES_USER=dispatch `
  -e POSTGRES_PASSWORD=dispatch `
  -e POSTGRES_DB=dispatchhub `
  -p 5433:5432 `
  -d postgres:16
```

Create `.env` in the repository root:

```env
DATABASE_URL=postgresql+psycopg://dispatch:dispatch@localhost:5433/dispatchhub
DISPATCH_JWT_SECRET=replace-with-a-long-random-secret
```

## Run the backend

```powershell
cd backend
pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

The application creates and seeds the initial demo records when the database is empty.

API documentation is available at `http://localhost:8000/docs`.

## Run the frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the URL shown by Vite, usually `http://localhost:5173`.

## Demo accounts

```text
Admin:      admin@dispatchhub.local / admin123
Dispatcher: dispatcher@dispatchhub.local / dispatch123
```

## Tests and checks

Run backend tests from the `backend` directory:

```powershell
python -m unittest discover -s tests -v
```

Run frontend checks from the `frontend` directory:

```powershell
npm run build
npm run lint
```

## Main workspaces

- Dashboard: operational overview and KPIs
- Loads: create, edit, search, filter, assign, and download summaries
- Drivers: manage availability and assigned-load counts
- Dispatches: reassign drivers, update status, and download reports
- Reports: completion and workload metrics
- Settings: profile, password, and persisted preferences
