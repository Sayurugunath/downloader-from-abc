import sys
import os
import socket
import threading
import time
import webbrowser
import uvicorn
from pathlib import Path

# Add backend directory to sys.path to find server.py and downloader.py when running from PyInstaller
sys.path.insert(0, str(Path(__file__).resolve().parent))

from server import app

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def find_free_port(start_port: int = 8000, max_attempts: int = 100) -> int:
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return start_port

def open_browser(url: str):
    time.sleep(1.2)
    webbrowser.open(url)

def main():
    port = find_free_port(8000)
    url = f"http://127.0.0.1:{port}/"
    print("=" * 60)
    print(f"Starting Downloader from ABC backend on {url}")
    print("Developed by Sayuru Gunathilaka")
    print("Minimize or keep this window open while using the application.")
    print("Close this window or press Ctrl+C in this console to exit.")
    print("=" * 60)
    
    # Start browser-opening thread
    threading.Thread(target=open_browser, args=(url,), daemon=True).start()
    
    # Run uvicorn server programmatically
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    main()
