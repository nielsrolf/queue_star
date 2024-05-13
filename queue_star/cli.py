import requests
import sys

API_BASE_URL = "http://localhost:8000"  # Adjust as necessary to point to your API's base URL


def cancel_job():
    response = requests.post(f"{API_BASE_URL}/cancel")
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to cancel job", "status_code": response.status_code}

def main():
    if len(sys.argv) < 2:
        print("Usage: cli.py cancel")
        sys.exit(1)

    command = sys.argv[1]
    if command == "cancel":
        result = cancel_job()
        print(result)
    else:
        print("Invalid command or missing arguments")

if __name__ == "__main__":
    main()
