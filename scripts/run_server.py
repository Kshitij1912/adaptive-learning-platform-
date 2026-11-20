"""
Bulletproof Launcher for the Adaptive Learning Platform Web Server.
Automatically detects port availability, prevents WinError 10048 socket collisions,
and launches the browser automatically on the active port.
"""

import os
import sys
import socket
import threading
import time
import webbrowser
import uvicorn

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def find_available_port(preferred_port: int = 8000, max_attempts: int = 20) -> int:
    """Finds the first available port starting from preferred_port."""
    for port in range(preferred_port, preferred_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return preferred_port


def open_browser_delayed(url: str, delay_seconds: float = 1.2):
    """Opens browser after server has started up."""
    def _open():
        time.sleep(delay_seconds)
        try:
            webbrowser.open(url)
        except Exception:
            pass
    t = threading.Thread(target=_open, daemon=True)
    t.start()


def start(port: int = None):
    # Determine port
    if port is None:
        port = find_available_port(8000)

    url_localhost = f"http://localhost:{port}"
    url_ip = f"http://127.0.0.1:{port}"

    print("\n" + "=" * 76)
    print("      ADAPTIVE LEARNING PLATFORM - LOCALHOST SERVER ACTIVE       ")
    print("=" * 76)
    print(f"  - Main Website (Browser): {url_localhost}")
    print(f"  - Alternate Direct IP:   {url_ip}")
    print(f"  - Swagger REST API Docs: {url_localhost}/docs")
    print("=" * 76)
    print("  [INFO] Press Ctrl+C in this terminal to stop the server.\n")

    # Auto-open browser
    open_browser_delayed(url_localhost)

    # Launch Uvicorn bound to 0.0.0.0 so localhost, 127.0.0.1, and ::1 all work
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    requested_port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None
    start(requested_port)
