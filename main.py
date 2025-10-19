from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import AsyncSessionLocal
from src.models import Job
from worker import process_dataset_task
import os
import uuid 

app = FastAPI(title="Dataset Foundry API")

# Dependency to get a DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Define storage paths (must match worker)
UPLOAD_DIR = "/tmp/src_uploads"
RESULT_DIR = "/tmp/src_results"

@app.post("/create-dataset")
async def create_dataset_endpoint(
    recipe: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    task_id = str(uuid.uuid4())
    job = Job(task_id=task_id, status="PENDING")
    
    # Save uploaded file(s) to a temporary directory named after the task_id
    job_upload_dir = os.path.join(UPLOAD_DIR, task_id)
    os.makedirs(job_upload_dir, exist_ok=True)
    
    # (Simplified: assumes single file upload for now, zip logic can be re-added)
    file_path = os.path.join(job_upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Save job to DB and send to worker
    db.add(job)
    await db.commit()
    await db.refresh(job)

    process_dataset_task.delay(job_id=job.id) #This dispatches the request to the Celery worker 
    
    return {"message": "Dataset generation has started.", "task_id": task_id, "job_id": job.id}

@app.get("/jobs/status/{task_id}")
async def get_job_status(task_id: str, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Job).where(Job.task_id == task_id))
    job = query.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"task_id": job.task_id, "status": job.status, "error": job.error_message}

@app.get("/download/{task_id}")
async def download_dataset(task_id: str, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Job).where(Job.task_id == task_id))
    job = query.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "COMPLETED" or not job.result_file_path:
        raise HTTPException(status_code=400, detail="Dataset not ready or generation failed.")
    
    return FileResponse(path=job.result_file_path, filename=os.path.basename(job.result_file_path))
