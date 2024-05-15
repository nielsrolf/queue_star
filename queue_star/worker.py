import os
import subprocess
import time
import threading
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from config import cancel_job, jobs_dir
import logging
import signal
import sys

# Setup logger
logger = logging.getLogger('job_runner')
logger.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)

# Global variables
current_job_path = None
current_proc = None


def get_next_job():
    all_todo_files = list(jobs_dir.glob("queued/**/todo.*")) + list(jobs_dir.glob("queued/todo.*")) + list(jobs_dir.glob("queued/**/*.sh")) + list(jobs_dir.glob("queued/*.sh"))
    all_todo_files.sort()  # Alphabetic order of paths
    for todo_file in all_todo_files:
        if todo_file.suffix == '.sh':
            job_name = todo_file.stem
            relative_path = todo_file.relative_to(jobs_dir / 'queued')
            subdir = relative_path.parent
            running_dir = jobs_dir / 'running' / subdir
            os.makedirs(running_dir, exist_ok=True)
            script_file = running_dir / f"{job_name}.sh"
            todo_file.rename(script_file)
            return script_file
        else:
            tree = ET.parse(todo_file)
            root = tree.getroot()
            job_element = root.find('job')
            if job_element is not None:
                script_content = job_element.text.strip()
                job_name = job_element.get('name', datetime.now().strftime('%Y%m%d%H%M%S'))
                relative_path = todo_file.relative_to(jobs_dir / 'queued')
                subdir = relative_path.parent
                running_dir = jobs_dir / 'running' / subdir
                os.makedirs(running_dir, exist_ok=True)
                script_file = running_dir / f"{job_name}.sh"
                with open(script_file, 'w') as file:
                    file.write(script_content)
                root.remove(job_element)
                tree.write(todo_file)
                return script_file
    return None


def run_job(job_path):
    global current_job_path, current_proc
    current_job_path = job_path  # Set the current job path
    try:
        relative_path = job_path.parent.relative_to(jobs_dir / 'running')
        subdir = relative_path
        output = []
        canceled = False

        # Set the file handler to the specific job log file
        log_path = job_path.with_suffix('.log')
        job_log_handler = logging.FileHandler(log_path)
        job_log_handler.setFormatter(formatter)
        logger.addHandler(job_log_handler)

        with subprocess.Popen(["bash", str(job_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as proc:
            current_proc = proc
            while True:
                out = proc.stdout.readline()
                if out == '' and proc.poll() is not None:
                    break
                if out:
                    output.append(out)
                    logger.info(out.strip())
                err = proc.stderr.readline()
                if err.strip() != '':
                    output.append(err)
                    logger.error(err.strip())
                if cancel_job.is_set():
                    canceled = True
                    proc.terminate()
                    cancel_job.clear()

            for line in proc.stdout.readlines():
                output.append(line)
                logger.info(line.strip())

            for line in proc.stderr.readlines():
                output.append(line)
                logger.error(line.strip())

        final_status = "failed" if proc.returncode != 0 else "success" if not canceled else "canceled"
        target_dir = jobs_dir / f"{final_status}/{subdir}"
        os.makedirs(target_dir, exist_ok=True)
        job_path.rename(target_dir / job_path.name)
        with open(log_path, 'w') as f:
            f.writelines(output)
        log_path.rename(target_dir / log_path.name)

        logger.removeHandler(job_log_handler)

    except Exception as e:
        logger.error("An error occurred", exc_info=True)
        final_status = "failed"
        if current_job_path:
            relative_path = current_job_path.parent.relative_to(jobs_dir / 'running')
            subdir = relative_path
            target_dir = jobs_dir / f"{final_status}/{subdir}"
            os.makedirs(target_dir, exist_ok=True)
            current_job_path.rename(target_dir / current_job_path.name)
            log_path = current_job_path.with_suffix('.log')
            if log_path.exists():
                log_path.rename(target_dir / log_path.name)


def worker_loop():
    print("Worker started")
    while True:
        try:
            next_job = get_next_job()
        except Exception as e:
            import traceback
            traceback.print_exc()
            next_job = None
        if next_job:
            print(f"Running {next_job}")
            run_job(next_job)
        else:
            print("No jobs found, waiting for 5 seconds.")
            time.sleep(5)


def handle_interrupt(signal, frame):
    global current_job_path, current_proc
    if current_job_path and current_proc:
        current_proc.terminate()
        try:
            relative_path = current_job_path.parent.relative_to(jobs_dir / 'running')
            subdir = relative_path
            target_dir = jobs_dir / f"failed/{subdir}"
            os.makedirs(target_dir, exist_ok=True)
            current_job_path.rename(target_dir / current_job_path.name)
            log_path = current_job_path.with_suffix('.log')
            if log_path.exists():
                log_path.rename(target_dir / log_path.name)
        except Exception as e:
            logger.error("An error occurred while moving the job to failed directory", exc_info=True)
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_interrupt)
    signal.signal(signal.SIGTERM, handle_interrupt)
    worker_loop()
