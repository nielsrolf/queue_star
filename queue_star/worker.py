import os
import subprocess
import time
import threading
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from config import cancel_job, jobs_dir


def get_next_job():
    all_todo_files = list(jobs_dir.glob("queued/**/todo.*")) + list(jobs_dir.glob("queued/todo.*"))
    all_todo_files.sort()  # Alphabetic order of paths
    for todo_file in all_todo_files:
        tree = ET.parse(todo_file)
        root = tree.getroot()
        # Assuming there are no namespaces or the job tag is directly under the root.
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
    try:
        relative_path = job_path.parent.relative_to(jobs_dir / 'running')
        subdir = relative_path
        output = []
        canceled = False
        with subprocess.Popen(["bash", str(job_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as proc:
            while True:
                out = proc.stdout.readline()
                if out == '' and proc.poll() is not None:
                    break
                if out:
                    output.append(out)
                err = proc.stderr.readline()
                if err:
                    output.append(err)
                if cancel_job.is_set():
                    canceled = True
                    proc.terminate()
                    cancel_job.clear()
                

            output.extend(proc.stdout.readlines())
            output.extend(proc.stderr.readlines())

        final_status = "failed" if proc.returncode != 0 else "success" if not canceled else "canceled"
        target_dir = jobs_dir / f"{final_status}/{subdir}"
        os.makedirs(target_dir, exist_ok=True)
        job_path.rename(target_dir / job_path.name)
        log_path = job_path.with_suffix('.log')
        with open(log_path, 'w') as f:
            f.writelines(output)
        log_path.rename(target_dir / log_path.name)
    except Exception as e:
        # Display error and go on
        import traceback
        traceback.print_exc()
        final_status = "failed"
        

    return f"Job {final_status}: completed or cancelled."

def worker_loop():
    while True:
        try:
            next_job = get_next_job()
        except Exception as e:
            import traceback
            traceback.print_exc()
            next_job = None
        if next_job:
            print(f"Running {next_job}")
            output = run_job(next_job)
            print(output)
        else:
            print("No jobs found, waiting for 5 seconds.")
            time.sleep(5)
                

if __name__ == "__main__":
    worker_loop()
