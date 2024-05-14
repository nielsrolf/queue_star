import threading
from api import app
from worker import worker_loop, handle_interrupt
import signal


if __name__ == "__main__":
    # Start the worker thread
    signal.signal(signal.SIGINT, handle_interrupt)
    signal.signal(signal.SIGTERM, handle_interrupt)
    worker_thread = threading.Thread(target=worker_loop)
    worker_thread.start()

    # Start the FastAPI server
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
