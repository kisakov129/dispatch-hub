from datetime import date, datetime, timedelta
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


JobStatus = Literal["Pending", "Active", "Completed"]
JobPriority = Literal["Low", "Medium", "High"]


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


@app.get("/")
def root():
    return {"message": "Dispatch Dashboard API is running!"}


@app.get("/health")
def health():
    return {"status": "healthy"}


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
