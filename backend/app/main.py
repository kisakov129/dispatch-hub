from datetime import date, datetime, timedelta
from io import BytesIO
import os
from typing import Generator, Literal

import jwt
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import Date, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from dotenv import load_dotenv


JobStatus = Literal["Pending", "Active", "Completed"]
JobPriority = Literal["Low", "Medium", "High"]
DriverAvailability = Literal["Available", "On a job", "Offline"]
load_dotenv()
JWT_SECRET = os.getenv("DISPATCH_JWT_SECRET", "development-only-change-me")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://dispatch:dispatch@localhost:5432/dispatchhub")
password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)


class Base(DeclarativeBase):
    pass


class JobRecord(Base):
    __tablename__ = "loads"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    customer: Mapped[str] = mapped_column(String(160))
    pickup: Mapped[str] = mapped_column(String(160))
    delivery: Mapped[str] = mapped_column(String(160))
    date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="Pending")
    priority: Mapped[str] = mapped_column(String(20), default="Medium")
    driver: Mapped[str | None] = mapped_column(String(160), nullable=True)


class DriverRecord(Base):
    __tablename__ = "drivers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    phone: Mapped[str] = mapped_column(String(40))
    availability: Mapped[str] = mapped_column(String(20), default="Available")
    assigned_jobs: Mapped[int] = mapped_column(Integer, default=0)


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(30), default="dispatcher")
    password_hash: Mapped[str] = mapped_column(String(255))


class Job(BaseModel):
    id: str
    customer: str
    pickup: str
    delivery: str
    date: date
    status: JobStatus
    priority: JobPriority
    driver: str | None = None

    model_config = {"from_attributes": True}


class JobCreate(BaseModel):
    customer: str = Field(min_length=2)
    pickup: str = Field(min_length=2)
    delivery: str = Field(min_length=2)
    date: date
    priority: JobPriority = "Medium"
    driver: str | None = None


class JobUpdate(JobCreate):
    status: JobStatus = "Pending"


class Driver(BaseModel):
    id: str
    name: str
    phone: str
    availability: DriverAvailability
    assigned_jobs: int = 0

    model_config = {"from_attributes": True}


class DriverCreate(BaseModel):
    name: str = Field(min_length=2)
    phone: str = Field(min_length=7)
    availability: DriverAvailability = "Available"


class JobAssignment(BaseModel):
    driver_id: str


class DispatchStatusUpdate(BaseModel):
    status: JobStatus


class LoginRequest(BaseModel):
    email: str
    password: str


class User(BaseModel):
    id: str
    name: str
    email: str
    role: Literal["admin", "dispatcher"]


try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
except Exception as error:
    raise RuntimeError("Invalid DATABASE_URL configuration") from error


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_database() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if not db.scalar(select(UserRecord).limit(1)):
            db.add_all([
                UserRecord(id="USR-001", name="Jordan Davis", email="admin@dispatchhub.local", role="admin", password_hash=password_hash.hash("admin123")),
                UserRecord(id="USR-002", name="Taylor Morgan", email="dispatcher@dispatchhub.local", role="dispatcher", password_hash=password_hash.hash("dispatch123")),
            ])
        if not db.scalar(select(DriverRecord).limit(1)):
            db.add_all([
                DriverRecord(id="DRV-001", name="Marcus Johnson", phone="(214) 555-0182", availability="On a job", assigned_jobs=2),
                DriverRecord(id="DRV-002", name="Sarah Williams", phone="(469) 555-0137", availability="Available", assigned_jobs=1),
                DriverRecord(id="DRV-003", name="David Chen", phone="(972) 555-0164", availability="On a job", assigned_jobs=1),
                DriverRecord(id="DRV-004", name="Emily Rodriguez", phone="(817) 555-0191", availability="Available", assigned_jobs=0),
                DriverRecord(id="DRV-005", name="James Wilson", phone="(214) 555-0116", availability="Offline", assigned_jobs=0),
            ])
        if not db.scalar(select(JobRecord).limit(1)):
            today = date.today()
            db.add_all([
                JobRecord(id="JOB-1048", customer="Acme Logistics", pickup="Dallas, TX", delivery="Austin, TX", date=today, status="Active", priority="High", driver="Marcus Johnson"),
                JobRecord(id="JOB-1047", customer="Northstar Retail", pickup="Fort Worth, TX", delivery="Houston, TX", date=today, status="Pending", priority="Medium"),
                JobRecord(id="JOB-1046", customer="Greenline Foods", pickup="Plano, TX", delivery="Waco, TX", date=today - timedelta(days=1), status="Completed", priority="Low", driver="Sarah Williams"),
                JobRecord(id="JOB-1045", customer="Summit Medical", pickup="Irving, TX", delivery="San Antonio, TX", date=today - timedelta(days=1), status="Active", priority="High", driver="David Chen"),
                JobRecord(id="JOB-1044", customer="Bluebird Commerce", pickup="Arlington, TX", delivery="Denton, TX", date=today - timedelta(days=2), status="Completed", priority="Medium", driver="Marcus Johnson"),
                JobRecord(id="JOB-1043", customer="Oak & Pine Co.", pickup="Garland, TX", delivery="Tyler, TX", date=today - timedelta(days=2), status="Pending", priority="Low"),
            ])
        db.commit()


app = FastAPI(title="Dispatch Dashboard API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def startup() -> None:
    seed_database()


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme), db: Session = Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        claims = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        account = db.get(UserRecord, claims.get("id"))
        if not account:
            raise HTTPException(status_code=401, detail="User no longer exists")
        return User.model_validate(account, from_attributes=True)
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token") from None


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user


@app.get("/")
def root():
    return {"message": "Dispatch Dashboard API is running!"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/api/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    account = db.scalar(select(UserRecord).where(UserRecord.email == payload.email.lower()))
    if not account or not password_hash.verify(payload.password, account.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user = User.model_validate(account, from_attributes=True)
    token = jwt.encode(user.model_dump() | {"exp": datetime.utcnow() + timedelta(hours=8)}, JWT_SECRET, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer", "user": user}


@app.get("/api/jobs", response_model=list[Job])
def list_jobs(search: str | None = Query(default=None), status: JobStatus | None = Query(default=None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    query = select(JobRecord).order_by(JobRecord.date.desc(), JobRecord.id.desc())
    if status:
        query = query.where(JobRecord.status == status)
    records = list(db.scalars(query))
    if search:
        term = search.lower()
        records = [job for job in records if term in f"{job.id} {job.customer} {job.pickup} {job.delivery}".lower()]
    return records


@app.get("/api/dashboard")
def dashboard_summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    records = list(db.scalars(select(JobRecord)))
    return {"total": len(records), "pending": sum(job.status == "Pending" for job in records), "active": sum(job.status == "Active" for job in records), "completed": sum(job.status == "Completed" for job in records), "updated_at": datetime.now().isoformat(timespec="seconds")}


@app.get("/api/drivers", response_model=list[Driver])
def list_drivers(availability: DriverAvailability | None = Query(default=None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    query = select(DriverRecord).order_by(DriverRecord.name)
    if availability:
        query = query.where(DriverRecord.availability == availability)
    return list(db.scalars(query))


@app.post("/api/drivers", response_model=Driver, status_code=201)
def create_driver(payload: DriverCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    existing_ids = [int(driver.id.split("-")[1]) for driver in db.scalars(select(DriverRecord)) if driver.id.startswith("DRV-")]
    driver = DriverRecord(id=f"DRV-{max(existing_ids, default=0) + 1:03d}", **payload.model_dump())
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver


@app.put("/api/drivers/{driver_id}", response_model=Driver)
def update_driver(driver_id: str, payload: DriverCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    driver = db.get(DriverRecord, driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    for key, value in payload.model_dump().items():
        setattr(driver, key, value)
    db.commit()
    db.refresh(driver)
    return driver


@app.delete("/api/drivers/{driver_id}", status_code=204)
def delete_driver(driver_id: str, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    driver = db.get(DriverRecord, driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if driver.assigned_jobs:
        raise HTTPException(status_code=409, detail="Driver has assigned loads and cannot be deleted")
    db.delete(driver)
    db.commit()


@app.post("/api/jobs", response_model=Job, status_code=201)
def create_job(payload: JobCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    numbers = [int(record.id.split("-")[1]) for record in db.scalars(select(JobRecord)) if record.id.startswith("JOB-")]
    job = JobRecord(id=f"JOB-{max(numbers, default=1048) + 1}", **payload.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@app.put("/api/jobs/{job_id}", response_model=Job)
def update_job(job_id: str, payload: JobUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    job = db.get(JobRecord, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    for key, value in payload.model_dump().items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job


@app.post("/api/jobs/{job_id}/assign", response_model=Job)
def assign_job(job_id: str, assignment: JobAssignment, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    job = db.get(JobRecord, job_id)
    driver = db.get(DriverRecord, assignment.driver_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if driver.availability != "Available":
        raise HTTPException(status_code=409, detail="Driver is not available")
    if job.driver:
        raise HTTPException(status_code=409, detail="Job is already assigned")
    job.driver = driver.name
    job.status = "Active"
    driver.availability = "On a job"
    driver.assigned_jobs += 1
    db.commit()
    db.refresh(job)
    return job


@app.get("/api/dispatches", response_model=list[Job])
def list_dispatches(status: JobStatus | None = Query(default=None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    query = select(JobRecord).where(JobRecord.driver.is_not(None)).order_by(JobRecord.date.desc())
    if status:
        query = query.where(JobRecord.status == status)
    return list(db.scalars(query))


@app.put("/api/dispatches/{job_id}/assignment", response_model=Job)
def reassign_dispatch(job_id: str, assignment: JobAssignment, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    job = db.get(JobRecord, job_id)
    new_driver = db.get(DriverRecord, assignment.driver_id)
    if not job or not job.driver:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    if not new_driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if new_driver.availability != "Available" and new_driver.name != job.driver:
        raise HTTPException(status_code=409, detail="Driver is not available")
    old_driver = db.scalar(select(DriverRecord).where(DriverRecord.name == job.driver))
    if old_driver and old_driver.id != new_driver.id:
        old_driver.assigned_jobs = max(0, old_driver.assigned_jobs - 1)
        old_driver.availability = "Available"
        new_driver.assigned_jobs += 1
        new_driver.availability = "On a job"
    job.driver = new_driver.name
    job.status = "Active"
    db.commit()
    db.refresh(job)
    return job


@app.put("/api/dispatches/{job_id}/status", response_model=Job)
def update_dispatch_status(job_id: str, payload: DispatchStatusUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    job = db.get(JobRecord, job_id)
    if not job or not job.driver:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    driver = db.scalar(select(DriverRecord).where(DriverRecord.name == job.driver))
    if payload.status == "Completed" and job.status != "Completed" and driver:
        driver.assigned_jobs = max(0, driver.assigned_jobs - 1)
        driver.availability = "Available"
    if payload.status == "Active" and job.status == "Completed" and driver:
        driver.assigned_jobs += 1
        driver.availability = "On a job"
    job.status = payload.status
    db.commit()
    db.refresh(job)
    return job


@app.get("/api/loads/{job_id}/summary.pdf")
def download_load_summary(job_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    job = db.get(JobRecord, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Load not found")
    pdf = BytesIO()
    document = canvas.Canvas(pdf, pagesize=letter)
    document.setTitle(f"{job.id} load summary")
    document.setFont("Helvetica-Bold", 18)
    document.drawString(54, 740, "DispatchHub load summary")
    details = [("Load ID", job.id), ("Customer", job.customer), ("Pickup", job.pickup), ("Delivery", job.delivery), ("Scheduled date", job.date.isoformat()), ("Priority", job.priority), ("Status", job.status), ("Driver", job.driver or "Unassigned")]
    for index, (label, value) in enumerate(details):
        y = 695 - (index * 30)
        document.setFont("Helvetica-Bold", 10)
        document.drawString(54, y, f"{label}:")
        document.setFont("Helvetica", 10)
        document.drawString(150, y, value)
    document.save()
    pdf.seek(0)
    return StreamingResponse(pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{job.id}-summary.pdf"'})


@app.delete("/api/jobs/{job_id}", status_code=204)
def delete_job(job_id: str, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    job = db.get(JobRecord, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
