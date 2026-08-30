"""
server.py - Zero-Dependency Real-Time Web Display Server
Uses Python standard library (http.server + Server-Sent Events / SSE) with zero external packages.
"""

import os
import json
import time
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any

OVERLAY_DIR = os.path.join(os.path.dirname(__file__), "overlay")
os.makedirs(OVERLAY_DIR, exist_ok=True)

# Global shared state
current_display_state: Dict[str, Any] = {
    "state": "IDLE",
    "time_left": 60.0,
    "stability_hp": 100.0,
    "score": 0,
    "combo": 0,
    "current_round": 0,
    "sensors": {
        "gate_angle": 20.0,
        "is_blowing": False,
        "light_pct": 50.0,
        "switch_on": False,
        "is_voice_active": False
    },
    "active_incident": None,
    "reaction_text": ""
}
_state_lock = threading.Lock()


class DisplayHTTPHandler(SimpleHTTPRequestHandler):
    """Handles static file serving and Server-Sent Events (SSE) live push."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=OVERLAY_DIR, **kwargs)

    def do_GET(self):
        # 1. Server-Sent Events stream for 30Hz live push to projector
        if self.path == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            try:
                while True:
                    with _state_lock:
                        payload = json.dumps(current_display_state)
                    self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    time.sleep(0.033)  # 30 Hz push
            except (ConnectionResetError, BrokenPipeError):
                return

        # 2. REST API State Snapshot
        elif self.path == "/api/state":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            with _state_lock:
                self.wfile.write(json.dumps(current_display_state).encode("utf-8"))
            return

        # 3. Static Files (index.html, style.css, app.js)
        elif self.path == "/" or self.path == "/index.html":
            self.path = "/index.html"
            return super().do_GET()
        elif self.path.startswith("/static/"):
            self.path = self.path[7:]  # Strip /static prefix
            return super().do_GET()
        else:
            return super().do_GET()

    def do_POST(self):
        # Handle live browser speech recognition triggers
        if self.path == "/api/voice_action":
            try:
                content_len = int(self.headers.get('Content-Length', 0))
                post_body = self.rfile.read(content_len).decode('utf-8')
                data = json.loads(post_body)
                transcript = data.get("transcript", "")
                
                # Forward to registered voice callback
                if voice_action_callback:
                    voice_action_callback(transcript)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            except Exception as e:
                self.send_response(400)
                self.end_headers()
            return
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silence routine HTTP access logs
        return


voice_action_callback = None

def set_voice_action_callback(cb):
    global voice_action_callback
    voice_action_callback = cb


class DisplayServer:
    """Zero-dependency threaded display server."""
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self.server = ThreadingHTTPServer((self.host, self.port), DisplayHTTPHandler)
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True, name="DisplayServerThread")
        self._thread.start()
        print(f"[DisplayServer] Zero-dependency Web Server active at: http://localhost:{self.port}")

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None


def broadcast_state_sync(new_state: Dict[str, Any]):
    """Thread-safe update of current display state for SSE broadcast."""
    with _state_lock:
        current_display_state.update(new_state)


async def broadcast_state(new_state: Dict[str, Any]):
    """Async wrapper for broadcast."""
    broadcast_state_sync(new_state)
