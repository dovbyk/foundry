from celery import Celery
import asyncio
import os 
from src.graph import run_graph
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select
from src.database import engine
from src.models import Job
import json

# Configure Celery. The broker is Redis, which acts as the message queue.
celery_app = Celery('tasks', broker='redis://localhost:6379/0')

# Create a session maker for the worker
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Define storage paths
UPLOAD_DIR = "/tmp/foundry_uploads"
RESULT_DIR = "/tmp/foundry_results"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

@celery_app.task(bind = True)
def process_dataset_task(self, job_id: int):
    """
    This is the Celery task that will run our async graph in the background.
    """
    async def _process():
        async with AsyncSessionLocal() as session:
            try:
                job_query = await session.execute(select(Job).where(Job.id == job_id))
                job = job_query.scalar_one()
                job.status = "PROCESSING"
                await session.commit()

                # 2. Reconstruct the 'files_to_process' from stored files
                # (This is simplified; in production, you'd store file paths in the DB)
                files_to_process = []
                # Assuming task_id is used as a folder for simplicity
                job_upload_dir = os.path.join(UPLOAD_DIR, job.task_id)
                for filename in os.listdir(job_upload_dir):
                    with open(os.path.join(job_upload_dir, filename), "rb") as f:
                        files_to_process.append({"filename": filename, "content": f.read()})
                
                # 3. Run the LangGraph pipeline
                final_state = await run_graph(files_to_process, job.task_id) # Assuming recipe is stored in task_id for now
                #4. Save the result
                result_filename = f"{job.task_id}.jsonl"
                result_file_path = os.path.join(RESULT_DIR, result_filename)
                with open(result_file_path, "w") as f:
                    for item in final_state.get("generated_data", []):
                        f.write(json.dumps(item) + "\n")

                # 5. Update job status to COMPLETED
                job.status = "COMPLETED"
                job.result_file_path = result_file_path
                await session.commit()
                print(f"--- Job {job_id} ({job.task_id}) COMPLETED ---")
                return {"status": "COMPLETED", "result_path": result_file_path}
            
            except Exception as e:
                print(f"!!! Job {job_id} FAILED: {e} !!!")
                job.status = "FAILED"
                job.error_message = str(e)
                await session.commit()
                # Retry the task up to 3 times, with a 5-minute delay
                raise self.retry(exc=e, countdown=300, max_retries=3)
    
    return asyncio.run(_process())


            
