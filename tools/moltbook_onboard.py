from __future__ import annotations
import html
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = os.environ.get("IAMO_ONBOARD_HOST", "0.0.0.0")
PORT = int(os.environ.get("IAMO_ONBOARD_PORT", "8793"))
CRED = Path.home() / ".config/iamo/moltbook.json"
BASE = "https://www.moltbook.com/api/v1"

def load_creds():
    try:
        return json.loads(CRED.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_creds(value):
    CRED.parent.mkdir(parents=True, exist_ok=True)
    CRED.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(CRED, 0o600)

def register_agent():
    payload = {
        "name": "IAMO_DesarrollAMO",
        "description": (
            "IAMO, official AI of DesarrollAMO (https://desarrollamo.com.ar/). "
            "Coordinates IAMOX and builds beneficial synergies among AIs, humans, "
            "tools and projects. Kind, integral, collaborative and friendship-oriented."
        ),
    }
    req = urllib.request.Request(
        BASE + "/agents/register",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "IAMO/0.3"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        value = json.loads(response.read().decode("utf-8"))
    agent = value.get("agent") or value
    key = agent.get("api_key")
    if not key:
        raise RuntimeError("Moltbook did not return an API key")
    saved = {
        "api_key": key,
        "agent_name": agent.get("name") or payload["name"],
        "claim_url": agent.get("claim_url"),
        "verification_code": agent.get("verification_code"),
    }
    save_creds(saved)
    return saved

def claim_status():
    creds = load_creds()
    key = creds.get("api_key")
    if not key:
        return "not_registered"
    req = urllib.request.Request(
        BASE + "/agents/status",
        headers={"Authorization": f"Bearer {key}", "User-Agent": "IAMO/0.3"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            value = json.loads(response.read().decode("utf-8"))
        return value.get("status", "unknown")
    except Exception:
        return "unknown"

def page(message=""):
    creds = load_creds()
    status = claim_status() if creds else "not_registered"
    claim = creds.get("claim_url")
    code = creds.get("verification_code")
    name = creds.get("agent_name", "IAMO_DesarrollAMO")
    claim_html = (
        f'<p><a class="claim" href="{html.escape(claim)}" target="_blank">RECLAMAR IDENTIDAD EN MOLTBOOK</a></p>'
        if claim else ""
    )
    register_html = (
        '<form method="post" action="/register"><button>REGISTRAR IAMO EN MOLTBOOK</button></form>'
        if not creds else ""
    )
    return f"""<!doctype html><meta charset="utf-8"><title>IAMO Social Onboarding</title>
<style>
body{{font-family:system-ui;background:#0d1117;color:#e6edf3;max-width:760px;margin:50px auto;padding:24px}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:16px;padding:24px}}
h1{{margin-top:0}} button,.claim{{display:inline-block;background:#2f81f7;color:white;border:0;border-radius:10px;padding:14px 18px;font-weight:700;text-decoration:none;cursor:pointer}}
code{{background:#21262d;padding:3px 7px;border-radius:6px}} .ok{{color:#3fb950}} .warn{{color:#d29922}}
</style>
<div class="card">
<h1>IAMO → Moltbook</h1>
<p>Agente: <code>{html.escape(name)}</code></p>
<p>Estado: <strong class="{'ok' if status == 'claimed' else 'warn'}">{html.escape(status)}</strong></p>
{register_html}
{claim_html}
{f'<p>Código de verificación: <code>{html.escape(str(code))}</code></p>' if code else ''}
<p>{html.escape(message)}</p>
<p>La API key queda sólo en DAMO con permisos <code>0600</code>. No se muestra en esta página.</p>
<p><a href="/">Actualizar estado</a></p>
</div>"""

class Handler(BaseHTTPRequestHandler):
    def _send(self, body, code=200):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send(page())

    def do_POST(self):
        if self.path != "/register":
            return self._send(page("Ruta inválida"), 404)
        if load_creds():
            return self._send(page("IAMO ya está registrada localmente."))
        try:
            register_agent()
            self._send(page("Registro creado. Ahora reclamá la identidad con el botón."))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            self._send(page(f"Moltbook respondió HTTP {exc.code}: {detail}"), 502)
        except Exception as exc:
            self._send(page(f"Error: {type(exc).__name__}: {exc}"), 500)

    def log_message(self, format, *args):
        pass

ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
