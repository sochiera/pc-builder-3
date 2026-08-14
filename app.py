#!/usr/bin/env python3
"""Minimal vertical slice for the PC builder."""

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


CPUS = {
    "ryzen-5-7600": {"name": "AMD Ryzen 5 7600", "socket": "AM5", "price": 799},
    "core-i5-14600k": {"name": "Intel Core i5-14600K", "socket": "LGA1700", "price": 1249},
}

MOTHERBOARDS = {
    "b650": {"name": "MSI B650 Gaming Plus WiFi", "socket": "AM5", "price": 699},
    "z790": {"name": "ASUS Prime Z790-P", "socket": "LGA1700", "price": 849},
}


def analyse(cpu_id: str, motherboard_id: str) -> dict:
    """Return the build summary used by both the browser and the HTTP test."""
    cpu = CPUS[cpu_id]
    motherboard = MOTHERBOARDS[motherboard_id]
    issues = []
    if cpu["socket"] != motherboard["socket"]:
        issues.append({
            "level": "blocker",
            "message": f"Procesor wymaga socketu {cpu['socket']}, a plyta ma {motherboard['socket']}.",
        })
    return {
        "cpu": cpu,
        "motherboard": motherboard,
        "total": cpu["price"] + motherboard["price"],
        "status": "blocked" if issues else "compatible",
        "issues": issues,
    }


PAGE = """<!doctype html>
<html lang='pl'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>Buduj PC</title>
  <style>
    :root { color-scheme: dark; font-family: system-ui, sans-serif; background: #101418; color: #edf2f5; }
    body { max-width: 760px; margin: 4rem auto; padding: 0 1.25rem; }
    header { border-left: 4px solid #62e3a0; padding-left: 1rem; margin-bottom: 2rem; }
    h1 { margin: 0; } .lead { color: #a9b6be; }
    main { display: grid; gap: 1rem; } label, .summary { background: #1a2228; border-radius: .5rem; padding: 1rem; }
    select { display: block; width: 100%; margin-top: .5rem; padding: .65rem; border-radius: .3rem; }
    .summary { border: 1px solid #2d3a42; } .ok { color: #62e3a0; } .blocked { color: #ff8d7a; }
  </style>
</head>
<body>
  <header><h1>Buduj PC</h1><p class='lead'>Sprawdz kompatybilnosc zestawu na biezaco.</p></header>
  <main>
    <label>Procesor<select id='cpu'>
      <option value='ryzen-5-7600'>AMD Ryzen 5 7600 - 799 PLN</option>
      <option value='core-i5-14600k'>Intel Core i5-14600K - 1249 PLN</option>
    </select></label>
    <label>Plyta glowna<select id='motherboard'>
      <option value='b650'>MSI B650 Gaming Plus WiFi - 699 PLN</option>
      <option value='z790'>ASUS Prime Z790-P - 849 PLN</option>
    </select></label>
    <section class='summary' aria-live='polite'><strong id='status'>Analizowanie...</strong><p id='total'></p><p id='issue'></p></section>
  </main>
  <script>
    const cpu = document.querySelector('#cpu');
    const motherboard = document.querySelector('#motherboard');
    async function refresh() {
      const response = await fetch(`/api/analyse?cpu=${cpu.value}&motherboard=${motherboard.value}`);
      const build = await response.json();
      const status = document.querySelector('#status');
      status.textContent = build.status === 'compatible' ? 'Kompatybilny zestaw' : 'Konfiguracja zablokowana';
      status.className = build.status === 'compatible' ? 'ok' : 'blocked';
      document.querySelector('#total').textContent = `Suma: ${build.total} PLN`;
      document.querySelector('#issue').textContent = build.issues.map(issue => issue.message).join(' ');
    }
    cpu.addEventListener('change', refresh); motherboard.addEventListener('change', refresh); refresh();
  </script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        request = urlparse(self.path)
        if request.path == "/":
            self.respond(HTTPStatus.OK, "text/html; charset=utf-8", PAGE.encode())
            return
        if request.path == "/api/analyse":
            query = parse_qs(request.query)
            try:
                result = analyse(query["cpu"][0], query["motherboard"][0])
            except (KeyError, IndexError):
                self.respond(HTTPStatus.BAD_REQUEST, "application/json", b'{"error":"unknown component"}')
                return
            self.respond(HTTPStatus.OK, "application/json", json.dumps(result).encode())
            return
        self.respond(HTTPStatus.NOT_FOUND, "text/plain", b"Not found")

    def respond(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Buduj PC: http://127.0.0.1:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
