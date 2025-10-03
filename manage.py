import os
import sys
import threading
import time
import requests
import subprocess

from django.core.management import execute_from_command_line
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel

from http.server import BaseHTTPRequestHandler, HTTPServer

import signal
import psutil

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MANAGE_PATH = os.path.join(BASE_DIR, "manage.py")

stop_event = threading.Event()
chromium_process = None  # Store Chromium process globally

class OfflineWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("MULTI CHANNEL SYSTEM")
        self.setGeometry(100, 100, 400, 200)
        layout = QVBoxLayout()

        label = QLabel("Offline Web UI Loaded.")
        shutdown_btn = QPushButton("Shutdown")

        shutdown_btn.clicked.connect(self.shutdown)

        layout.addWidget(label)
        layout.addWidget(shutdown_btn)
        self.setLayout(layout)

    def shutdown(self):
        print("Shutdown requested from PySide6 window!")
        shutdown_everything()



def shutdown_everything():
    global chromium_process
    stop_event.set()

    # Terminate Chromium browser
    if chromium_process and chromium_process.poll() is None:
        chromium_process.terminate()
        chromium_process.wait()

    # Kill Django server (it runs in the same process group)
    parent = psutil.Process(os.getpid())
    for child in parent.children(recursive=True):
        try:
            child.terminate()
        except psutil.NoSuchProcess:
            continue

    # Force kill remaining child processes
    gone, alive = psutil.wait_procs(parent.children(), timeout=3)
    for p in alive:
        try:
            p.kill()
        except psutil.NoSuchProcess:
            pass

    # Optional: close ports like 8000 and 9999 if still held (normally they are freed with process kill)
    subprocess.call(["fuser", "-k", "8000/tcp"])
    subprocess.call(["fuser", "-k", "9999/tcp"])

    time.sleep(0.5)
    print("Shutting down everything and exiting.")
    os._exit(0)  # Force exit entire process including threads



def migrate_database():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mini_soft.settings")
    os.chdir(BASE_DIR)
    sys.argv = [MANAGE_PATH, "makemigrations"]
    execute_from_command_line(sys.argv)
    sys.argv = [MANAGE_PATH, "migrate"]
    execute_from_command_line(sys.argv)

def start_django_server():
    migrate_database()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mini_soft.settings")
    os.chdir(BASE_DIR)
    sys.argv = [MANAGE_PATH, "runserver", "--noreload"]

    while not stop_event.is_set():
        try:
            execute_from_command_line(sys.argv)
        except SystemExit:
            break

def wait_for_server():
    url = "http://127.0.0.1:8000/"
    print("Waiting for Django server to start...")
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Django server is running.")
                break
        except requests.ConnectionError:
            pass
        time.sleep(1)

def launch_chromium_kiosk():
    global chromium_process
    chromium_process = subprocess.Popen([
        "chromium-browser",
        "--kiosk",
        "--app=http://127.0.0.1:8000/"
    ])

import socket

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0

def run_shutdown_server(window_ref):
    if is_port_in_use(9999):
        print("⚠️ Port 9999 is already in use. Skipping shutdown server startup.")
        return

    class ShutdownHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path == "/shutdown/":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Shutting down app...")
                print("Shutdown requested from browser!")
                shutdown_everything()

            elif self.path == "/switchoff/":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Switching off Raspberry Pi...")
                print("System shutdown requested!")
                subprocess.run(["sudo", "shutdown", "-h", "now"])

            elif self.path == "/reboot/":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Rebooting Raspberry Pi...")
                print("System reboot requested!")
                subprocess.run(["sudo", "reboot"])

            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Unknown request path.")

        def log_message(self, format, *args):
            # Optional: suppress default logging
            return

    try:
        server = HTTPServer(("127.0.0.1", 9999), ShutdownHandler)
        print("🟢 Shutdown server running on port 9999")
        server.serve_forever()
    except OSError as e:
        print(f"❌ Failed to start shutdown server: {e}")




if __name__ == "__main__":
    django_thread = threading.Thread(target=start_django_server)
    django_thread.daemon = True
    django_thread.start()

    wait_for_server()
    launch_chromium_kiosk()

    app = QApplication([])
    window = OfflineWindow()

    shutdown_thread = threading.Thread(target=run_shutdown_server, args=(window,))
    shutdown_thread.daemon = True
    shutdown_thread.start()

    window.show()
    app.exec()