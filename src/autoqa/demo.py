"""Owned deterministic local application; no dependencies or external services."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

PRODUCTS = [("1", "Atlas Notebook", "$12"), ("2", "Orbit Pen", "$4")]


class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        status = 200
        if path == "/":
            content = '<h1>AutoQA Demo Store</h1><p>Deterministic products for local QA.</p><a href="/products">Browse products</a>'
        elif path == "/products":
            content = '<h1>Product Catalog</h1><label for="search">Search products</label><input id="search" type="search" oninput="document.querySelectorAll(\'li\').forEach(e=>e.hidden=!e.textContent.toLowerCase().includes(this.value.toLowerCase()))"><ul>'
            content += (
                "".join(
                    f'<li><a href="/products/{i}">{name}</a> {price}</li>'
                    for i, name, price in PRODUCTS
                )
                + "</ul>"
            )
        elif path.startswith("/products/") and path.rsplit("/", 1)[-1] in {"1", "2"}:
            _, name, price = next(p for p in PRODUCTS if p[0] == path.rsplit("/", 1)[-1])
            content = f'<h1>{name}</h1><p>{price}</p><p>In stock</p><a href="/products">Back to catalog</a>'
        elif path == "/contact":
            content = """<h1>Contact us</h1><form onsubmit="event.preventDefault();document.getElementById('message').textContent='Message validated locally';"><label for="name">Name</label><input id="name" required><label for="email">Email</label><input id="email" type="email" required><button type="submit">Validate message</button></form><p id="message" role="status"></p>"""
        else:
            status, content = 404, "<h1>Page not found</h1>"
        html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>AutoQA Demo</title><style>body{{font:18px system-ui;max-width:900px;margin:3rem auto;padding:1rem;color:#17243a}}nav a{{margin-right:2rem}}input,label,button{{display:block;margin:1rem 0}}a{{color:#1651ab}}</style></head><body><nav aria-label="Main"><a href="/">Home</a><a href="/products">Catalog</a><a href="/contact">Contact</a></nav><main>{content}</main></body></html>"""
        data = html.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args) -> None:
        pass


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    with ThreadingHTTPServer((host, port), DemoHandler) as server:
        server.serve_forever()
