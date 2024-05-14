from threading import Event
from pathlib import Path
import os

# This is the event used for signaling a job cancellation
cancel_job = Event()

jobs_dir = Path(os.environ.get("JOBS_DIR", "~/jobs")).expanduser()

def ensure_directories():
    os.makedirs(jobs_dir / 'running', exist_ok=True)
    os.makedirs(jobs_dir / 'canceled', exist_ok=True)
    os.makedirs(jobs_dir / 'success', exist_ok=True)
    os.makedirs(jobs_dir / 'config', exist_ok=True)

ensure_directories()
