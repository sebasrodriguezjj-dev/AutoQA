"""Independent owned supply application, with controlled fault injection for verification."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

SUPPLIES = [
    {"sku": "moss", "name": "Moss Journal", "category": "Paper", "price": 18},
    {"sku": "cedar", "name": "Cedar Pencil", "category": "Writing", "price": 3},
    {"sku": "slate", "name": "Slate Marker", "category": "Writing", "price": 7},
]


class SupplyHandler(BaseHTTPRequestHandler):
    regression = ""

    def do_GET(self):
        path = urlsplit(self.path).path
        status = 200
        if path in {"/", "/inventory"}:
            cards = "".join(
                f'<article aria-label="{s["name"]}"><a data-testid="stock-name" href="/supply/{s["sku"]}">{s["name"]}</a><span data-testid="stock-price">${s["price"]}</span><span>{s["category"]}</span></article>'
                for s in SUPPLIES
            )
            content = f"""<h1>Supply inventory</h1>
<label for="query">Find supplies</label><input id="query" type="search">
<label for="category">Category filter</label><select id="category"><option value="all">All supplies</option><option value="Paper">Paper</option><option value="Writing">Writing</option></select>
<label for="ordering">Sort by price</label><select id="ordering"><option value="original">Original order</option><option value="low">Lowest price</option><option value="high">Highest price</option></select>
<section aria-label="Available supplies" id="cards">{cards}</section><p data-testid="stock-empty" role="status" hidden>No supplies match</p>
<script>
const supplies={json.dumps(SUPPLIES)}; const broken={json.dumps(self.regression)};
function refresh(){{
 const query=document.getElementById('query').value.toLowerCase();
 const category=document.getElementById('category').value;
 let rows=supplies.filter(s=>(broken==='search'||s.name.toLowerCase().includes(query))&&(broken==='filter'||category==='all'||s.category===category));
 const sort=document.getElementById('ordering').value;
 if(broken!=='sorting'&&sort!=='original') rows.sort((a,b)=>sort==='low'?a.price-b.price:b.price-a.price);
 document.getElementById('cards').replaceChildren(...rows.map(s=>{{const card=document.createElement('article');card.setAttribute('aria-label',s.name);const a=document.createElement('a');a.dataset.testid='stock-name';a.href='/supply/'+s.sku;a.textContent=s.name;const price=document.createElement('span');price.dataset.testid='stock-price';price.textContent='$'+s.price;const category=document.createElement('span');category.textContent=s.category;card.append(a,price,category);return card;}}));
 document.querySelector('[data-testid="stock-empty"]').hidden=rows.length>0;
}}
document.getElementById('query').addEventListener('input',refresh);
document.getElementById('category').addEventListener('change',refresh);
document.getElementById('ordering').addEventListener('change',refresh);
</script>"""
        elif path.startswith("/supply/") and path.rsplit("/", 1)[-1] in {
            s["sku"] for s in SUPPLIES
        }:
            item = next(s for s in SUPPLIES if s["sku"] == path.rsplit("/", 1)[-1])
            content = f'<h1>{item["name"]}</h1><p>Category: {item["category"]}</p><p>${item["price"]}</p><a href="/inventory">Return to inventory</a>'
        elif path == "/request":
            content = """<h1>Request a sample</h1><form aria-label="Sample request" onsubmit="event.preventDefault();document.querySelector('[data-testid=request-status]').textContent='Sample request validated';">
<label for="person">Contact name</label><input id="person" required>
<label for="work-email">Work email</label><input id="work-email" type="email" required>
<label for="quantity">Sample quantity</label><input id="quantity" type="number" min="1" max="5" required>
<button>Validate sample request</button></form><p role="status" data-testid="request-status"></p>"""
        else:
            status, content = 404, "<h1>Supply not found</h1>"
        html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Supply Lab</title><style>body{{font:18px system-ui;max-width:960px;margin:40px auto;padding:20px;color:#193a36}}nav a{{margin-right:25px}}article{{border:1px solid #b7ccc4;padding:20px;margin:12px 0;display:flex;gap:30px}}label,input,select,button{{display:block;margin:12px 0}}[hidden]{{display:none!important}}</style></head><body><nav aria-label="Supply navigation"><a href="/inventory">Inventory</a><a href="/request">Request sample</a></nav><main>{content}</main></body></html>"""
        payload = html.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        pass


def serve(host="127.0.0.1", port=8001):
    with ThreadingHTTPServer((host, port), SupplyHandler) as server:
        server.serve_forever()
