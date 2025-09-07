#!/usr/bin/env python3
"""
Main application launcher for AI-Assess.
This script starts both the backend (FastAPI) and frontend (Streamlit) processes.
"""

import subprocess
import sys
import os
import time
from threading import Thread


def start_backend():
    """Start the FastAPI backend server."""
    print("Starting backend server...")
    try:
        # Change to backend directory
        backend_path = os.path.join(os.path.dirname(__file__), "backend")
        # Start the FastAPI server
        backend_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=backend_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Backend server started on http://localhost:8000")
        return backend_process
    except Exception as e:
        print(f"Error starting backend: {e}")
        return None


def start_frontend():
    """Start the Streamlit frontend."""
    print("Starting frontend...")
    try:
        # Change to frontend directory
        frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
        # Start Streamlit app
        frontend_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"],
            cwd=frontend_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Frontend started on http://localhost:8501")
        return frontend_process
    except Exception as e:
        print(f"Error starting frontend: {e}")
        return None


def monitor_process(process, name):
    """Monitor a process and print its output."""
    if process:
        try:
            while True:
                output = process.stdout.readline()
                if output:
                    print(f"[{name}] {output.decode().strip()}")
                if process.poll() is not None:
                    break
        except Exception as e:
            print(f"Error monitoring {name}: {e}")


def main():
    """Main function to start both backend and frontend."""
    print("Starting AI-Assess application...")
    
    # Start backend
    backend_process = start_backend()
    
    # Wait a moment for backend to start
    time.sleep(2)
    
    # Start frontend
    frontend_process = start_frontend()
    
    if backend_process and frontend_process:
        print("\nAI-Assess is running!")
        print("Backend: http://localhost:8000")
        print("Frontend: http://localhost:8501")
        print("Press Ctrl+C to stop both servers.")
        
        # Monitor both processes
        backend_thread = Thread(target=monitor_process, args=(backend_process, "Backend"))
        frontend_thread = Thread(target=monitor_process, args=(frontend_process, "Frontend"))
        
        backend_thread.daemon = True
        frontend_thread.daemon = True
        
        backend_thread.start()
        frontend_thread.start()
        
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down servers...")
            backend_process.terminate()
            frontend_process.terminate()
            print("Servers stopped.")
    else:
        print("Failed to start one or both servers.")
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()


if __name__ == "__main__":
    main()