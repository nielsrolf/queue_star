# queue_star

`queue_star` is a Python-based job queue management system designed to handle the execution of tasks on a machine with a GPU. The system supports job prioritization, manages job executions, and allows easy interaction via a CLI and a REST API.


## Installation

To set up `queue_star` on your system, follow these steps:

### Prerequisites

- Python 3.7 or newer
- pip for Python 3

### Installing Dependencies

Clone the repository and install the required Python packages:

```bash
git clone https://github.com/yourusername/queue_star.git
cd queue_star
pip install -r requirements.txt
```
## Usage

### Starting the API Server
Navigate to the project directory and run:

```
python src/main.py
```
This command starts the FastAPI server, which listens for job management requests.

### Using the CLI

The CLI provides a simple interface to interact with the job queue:

```
# List all jobs
python src/cli.py list

# Add a job
python src/cli.py add your_job.sh

# Delete a job
python src/cli.py delete your_job.sh

# Cancel the currently running job
python src/cli.py cancel
```

### API Endpoints
The following endpoints are available:

    POST /jobs/{job_name}: Add a job to the queue.
    DELETE /jobs/{job_name}: Remove a job from the queue.
    POST /cancel: Cancel the currently running job.

