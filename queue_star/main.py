import threading
from api import app
from worker import worker_loop

if __name__ == "__main__":
    # Start the worker thread
    worker_thread = threading.Thread(target=worker_loop)
    worker_thread.start()

    # Start the FastAPI server
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
