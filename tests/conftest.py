import threading
from http.server import ThreadingHTTPServer

import pytest

from autoqa.core import initialize
from autoqa.demo import DemoHandler


@pytest.fixture
def project(tmp_path):
    return initialize("client-a", tmp_path / "projects")


@pytest.fixture
def demo_server():
    class Handler(DemoHandler):
        broken = False
        hits = []

        def do_GET(self):
            self.hits.append(self.path)
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "http://127.0.0.1:1/private")
                self.end_headers()
            elif self.broken:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Changed application baseline</h1>")
            else:
                super().do_GET()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", Handler
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
