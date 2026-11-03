from datetime import date, datetime, timedelta
from io import BytesIO
import os
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from pwdlib import PasswordHash
import jwt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


JobStatus = Literal["Pending", "Active", "Completed"]
JobPriority = Literal["Low", "Medium", "High"]
DriverAvailability = Literal["Available", "On a job", "Offline"]
JWT_SECRET = os.getenv("DISPATCH_JWT_SECRET", "development-only-change-me")
password_hash = PasswordHash.recommended()


class Job(BaseModel):
    id: str
    customer: str
    pickup: str
    delivery: str
    date: date
    status: JobStatus
    priority: JobPriority
    driver: str | None = None


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


class JobAssignment(BaseModel):
    driver_id: str


class LoginRequest(BaseModel):
    email: str
    password: str


class User(BaseModel):
    id: str
    name: str
    email: str
    role: Literal["admin", "dispatcher"]


app = FastAPI(title="Dispatch Dashboard API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

today = date.today()
jobs: list[Job] = [
    Job(id="JOB-1048", customer="Acme Logistics", pickup="Dallas, TX", delivery="Austin, TX", date=today, status="Active", priority="High", driver="Marcus Johnson"),
    Job(id="JOB-1047", customer="Northstar Retail", pickup="Fort Worth, TX", delivery="Houston, TX", date=today, status="Pending", priority="Medium"),
    Job(id="JOB-1046", customer="Greenline Foods", pickup="Plano, TX", delivery="Waco, TX", date=today - timedelta(days=1), status="Completed", priority="Low", driver="Sarah Williams"),
    Job(id="JOB-1045", customer="Summit Medical", pickup="Irving, TX", delivery="San Antonio, TX", date=today - timedelta(days=1), status="Active", priority="High", driver="David Chen"),
    Job(id="JOB-1044", customer="Bluebird Commerce", pickup="Arlington, TX", delivery="Denton, TX", date=today - timedelta(days=2), status="Completed", priority="Medium", driver="Marcus Johnson"),
    Job(id="JOB-1043", customer="Oak & Pine Co.", pickup="Garland, TX", delivery="Tyler, TX", date=today - timedelta(days=2), status="Pending", priority="Low"),
]
drivers: list[Driver] = [
    Driver(id="DRV-001", name="Marcus Johnson", phone="(214) 555-0182", availability="On a job", assigned_jobs=2),
    Driver(id="DRV-002", name="Sarah Williams", phone="(469) 555-0137", availability="Available", assigned_jobs=1),
    Driver(id="DRV-003", name="David Chen", phone="(972) 555-0164", availability="On a job", assigned_jobs=1),
    Driver(id="DRV-004", name="Emily Rodriguez", phone="(817) 555-0191", availability="Available", assigned_jobs=0),
    Driver(id="DRV-005", name="James Wilson", phone="(214) 555-0116", availability="Offline", assigned_jobs=0),
]
users = {
    "admin@dispatchhub.local": {"id": "USR-001", "name": "Jordan Davis", "role": "admin", "password": password_hash.hash("admin123")},
    "dispatcher@dispatchhub.local": {"id": "USR-002", "name": "Taylor Morgan", "role": "dispatcher", "password": password_hash.hash("dispatch123")},
}


@app.get("/")
def root():
    return {"message": "Dispatch Dashboard API is running!"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/api/auth/login")
def login(payload: LoginRequest):
    account = users.get(payload.email.lower())
    if not account or not password_hash.verify(payload.password, account["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user = User(id=account["id"], name=account["name"], email=payload.email.lower(), role=account["role"])
    token = jwt.encode(user.model_dump() | {"exp": datetime.utcnow() + timedelta(hours=8)}, JWT_SECRET, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer", "user": user}


@app.get("/api/jobs", response_model=list[Job])
def list_jobs(search: str | None = Query(default=None), status: JobStatus | None = Query(default=None)):
    result = jobs
    if search:
        term = search.lower()
        result = [job for job in result if term in f"{job.id} {job.customer} {job.pickup} {job.delivery}".lower()]
    if status:
        result = [job for job in result if job.status == status]
    return result


@app.get("/api/dashboard")
def dashboard_summary():
    return {
        "total": len(jobs),
        "pending": sum(job.status == "Pending" for job in jobs),
        "active": sum(job.status == "Active" for job in jobs),
        "completed": sum(job.status == "Completed" for job in jobs),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }


@app.get("/api/drivers", response_model=list[Driver])
def list_drivers(availability: DriverAvailability | None = Query(default=None)):
    if availability:
        return [driver for driver in drivers if driver.availability == availability]
    return drivers


@app.post("/api/jobs/{job_id}/assign", response_model=Job)
def assign_job(job_id: str, assignment: JobAssignment):
    job_index = next((index for index, job in enumerate(jobs) if job.id == job_id), None)
    driver_index = next((index for index, driver in enumerate(drivers) if driver.id == assignment.driver_id), None)
    if job_index is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if driver_index is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    driver = drivers[driver_index]
    if driver.availability != "Available":
        raise HTTPException(status_code=409, detail="Driver is not available")
    job = jobs[job_index]
    if job.driver:
        raise HTTPException(status_code=409, detail="Job is already assigned")
    jobs[job_index] = job.model_copy(update={"driver": driver.name, "status": "Active"})
    drivers[driver_index] = driver.model_copy(update={"availability": "On a job", "assigned_jobs": driver.assigned_jobs + 1})
    return jobs[job_index]


@app.get("/api/dispatches", response_model=list[Job])
def list_dispatches(status: JobStatus | None = Query(default=None)):
    dispatches = [job for job in jobs if job.driver]
    if status:
        dispatches = [job for job in dispatches if job.status == status]
    return dispatches


@app.get("/api/loads/{job_id}/summary.pdf")
def download_load_summary(job_id: str):
    job = next((item for item in jobs if item.id == job_id), None)
    if job is None:
        raise HTTPException(status_code=404, detail="Load not found")
    pdf = BytesIO()
    document = canvas.Canvas(pdf, pagesize=letter)
    document.setTitle(f"{job.id} load summary")
    document.setFont("Helvetica-Bold", 18)
    document.drawString(54, 740, "DispatchHub load summary")
    document.setFont("Helvetica", 11)
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


@app.post("/api/jobs", response_model=Job, status_code=201)
def create_job(payload: JobCreate):
    job = Job(id=f"JOB-{1049 + len(jobs)}", status="Pending", **payload.model_dump())
    jobs.insert(0, job)
    return job


@app.put("/api/jobs/{job_id}", response_model=Job)
def update_job(job_id: str, payload: JobUpdate):
    for index, job in enumerate(jobs):
        if job.id == job_id:
            updated_job = Job(id=job.id, **payload.model_dump())
            jobs[index] = updated_job
            return updated_job
    raise HTTPException(status_code=404, detail="Job not found")


@app.delete("/api/jobs/{job_id}", status_code=204)
def delete_job(job_id: str):
    for index, job in enumerate(jobs):
        if job.id == job_id:
            jobs.pop(index)
            return
    raise HTTPException(status_code=404, detail="Job not found")
