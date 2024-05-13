# queue_star

`queue_star` is a Python-based job queue management system designed to handle the execution of tasks on a machine with a GPU.


## Usage

Navigate to the project directory and run:
```
python src/main.py
```

Then put jobs into `jobs/queue/<subdirs/can/be/used/for/priorities/>todo.xml`:
```xml
<todo>
<job name=job1>
echo "This job will be run as soon as a worker is available, and land in `jobs/running/job1.sh` and then `jobs/success/job1.sh`"
echo "Find logs in `jobs/success/job1.log`"
</job>
<job>
this job will fail and move to `jobs/failed/job2.sh` and `jobs/failed/job2.log`
</job>
<job>
echo "this job will take a while, and land in `jobs/running/job3.sh`"
sleep 20
</job>
</todo>
```
The subdir structure is preserved between stages and since todos are read and worked from in alphabetically sorted order, you can use naming based folders for priorities.



### Cancel

The CLI provides a simple interface to interact with the job queue:

```
# Cancel the currently running job
python src/cli.py cancel
```


## Installation

To set up `queue_star` on your system, follow these steps:


### Installing Dependencies

Clone the repository and install the required Python packages:

```bash
git clone https://github.com/yourusername/queue_star.git
cd queue_star
pip install -r requirements.txt
```

