#!/usr/bin/env python3
"""Serve the three brand books on localhost. Rebuilds on every page load."""
import http.server, socketserver, os, sys, subprocess, html

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8090

BOOKS = [
    ("apex",  "apex.html",  "Apex Paramedics",  "#1D225E", "#2c338e", "#f9ad16",
     "apex-brand-kit", "Navy structure, gold spark"),
    ("royal", "royal.html", "Royal Ambulance",  "#2f193b", "#572e72", "#8260a2",
     "royal-brand-kit", "Purple is the whole palette"),
    ("ce",    "ce.html",    "Collective Edge",  "#000000", "#111111", "#C8C8C8",
     "collective-edge-brand-kit", "No hue of its own, a grey ramp"),
]


def index():
    cards = ""
    for key, f, name, deep, prim, acc, repo, note in BOOKS:
        cards += f"""
    <a class="card" href="/{f}">
      <div class="band" style="background:{deep}">
        <div class="sw"><i style="background:{prim}"></i><i style="background:{acc}"></i></div>
      </div>
      <div class="meta">
        <h2>{html.escape(name)}</h2>
        <p class="note">{html.escape(note)}</p>
        <p class="repo">{html.escape(repo)} · 16 slides</p>
      </div>
    </a>"""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Brand books</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/collective-edge/collective-edge-brand-kit@v1.0/snippets/type-system.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/collective-edge/collective-edge-brand-kit@v1.0/snippets/palette.css">
<style>
  body {{ background: var(--bg-canvas); margin: 0; }}
  .wrap {{ max-width: 1180px; margin: 0 auto; padding: 96px 40px 120px; }}
  h1 {{ margin: 0 0 18px; }}
  .lede {{ color: var(--fg-2); max-width: 58ch; margin: 0 0 64px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(300px,1fr)); gap: 0;
           border: 1px solid var(--border-1); }}
  .card {{ text-decoration: none; color: inherit; border-left: 1px solid var(--border-1);
           display: flex; flex-direction: column; transition: background var(--dur-base) var(--ease-standard); }}
  .card:first-child {{ border-left: 0; }}
  .card:hover {{ background: var(--bg-surface); }}
  .card:focus-visible {{ outline: 2px solid var(--fg-1); outline-offset: -2px; }}
  .band {{ height: 190px; display: flex; align-items: flex-end; padding: 22px; }}
  .sw {{ display: flex; gap: 6px; }}
  .sw i {{ width: 26px; height: 26px; display: block; }}
  .meta {{ padding: 28px 26px 34px; }}
  .meta h2 {{ font-size: var(--fs-h3); font-weight: var(--weight-bold); margin: 0 0 8px;
              letter-spacing: var(--tr-h3); }}
  .note {{ color: var(--fg-2); font-size: var(--fs-body-sm); margin: 0 0 16px; max-width: none; }}
  .repo {{ font-family: var(--font-mono); font-size: 11px; letter-spacing: .08em;
           text-transform: uppercase; color: var(--fg-4); margin: 0; }}
  .foot {{ margin-top: 56px; font-family: var(--font-mono); font-size: 12px; color: var(--fg-4);
           display: flex; justify-content: space-between; flex-wrap: wrap; gap: 14px; }}
</style></head><body>
<div class="wrap">
  <p class="bk-eyebrow">House type system v1.0</p>
  <h1 class="bk-display-md">Brand books.</h1>
  <p class="bk-body-lg lede">One per brand. Each loads the published type system and its own palette
  from the CDN, so these pages are a live test of the system rather than a picture of it.
  Open a book and use Save as PDF for a print-ready file.</p>
  <div class="grid">{cards}</div>
  <div class="foot"><span>rebuilt on every load · port {PORT}</span>
  <span>1600 × 900 · landscape PDF</span></div>
</div></body></html>"""


class H(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        return os.path.join(HERE, path.lstrip("/").split("?")[0] or "index.html")

    def do_GET(self):
        clean = self.path.split("?")[0]
        if clean in ("/", "/index.html"):
            subprocess.run([sys.executable, os.path.join(HERE, "build.py")],
                           capture_output=True)
            b = index().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            return
        if clean.endswith(".html"):
            subprocess.run([sys.executable, os.path.join(HERE, "build.py")],
                           capture_output=True)
        return super().do_GET()

    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass


class Server(socketserver.ThreadingTCPServer):
    """Threaded. The single-threaded version deadlocks the moment a browser
    holds a keep-alive connection open, which every browser does."""
    allow_reuse_address = True
    daemon_threads = True


with Server(("127.0.0.1", PORT), H) as httpd:
    print(f"brand books  ->  http://localhost:{PORT}")
    httpd.serve_forever()
