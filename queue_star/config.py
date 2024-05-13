from threading import Event
from pathlib import Path

# This is the event used for signaling a job cancellation
cancel_job = Event()

jobs_dir = Path("./jobs")
worker_state_file = Path("worker.json")
