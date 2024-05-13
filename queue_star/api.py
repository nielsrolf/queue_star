from fastapi import FastAPI, HTTPException
from pathlib import Path
import shutil
from config import cancel_job

app = FastAPI()

jobs_dir = Path("./jobs")


@app.post("/cancel")
def cancel_current_job():
    cancel_job.set()
    return {"message": "Cancellation signal sent"}
