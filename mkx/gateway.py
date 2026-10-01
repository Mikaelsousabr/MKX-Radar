"""MKX local UI gateway. All scraping/API work stays in the upstream engine."""
import http.client
import json
import csv
import io
import re
import crm
import mimetypes
import os
from pathlib import Path
import signal
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlencode, urlsplit

ROOT = Path(__file__).resolve().parent
ENGINE_PORT = 8090
ERRORS = {
    "invalid max time": "Tempo inválido. Use 10m para minutos ou 1h para uma hora.",
    "max time must be more than 3m": "Use um tempo máximo de pelo menos 3m.",
    "invalid zoom": "Informe um zoom válido, de 0 a 21.",
    "invalid radius": "Informe um raio válido em metros.",
    "invalid depth": "Informe uma profundidade válida.",
    "invalid lang": "Idioma inválido. Use pt para português (não pt-BR).",
    "missing lang": "Selecione o idioma dos resultados.",
    "missing keywords": "Informe pelo menos uma busca.",
    "missing name": "Informe um nome para a busca.",
    "missing depth": "Informe uma profundidade maior que zero.",
    "missing max time": "Informe o tempo máximo, por exemplo 10m.",
    "missing geo coordinates": "O modo rápido exige latitude e longitude.",
}


def transform_html(data):
    text = data.decode("utf-8")
    replacements = {
        '>View</button>': '>Ver mapa</button>',
        '>Download</a>': '>Baixar CSV</a>',
        '>Delete</button>': '>Excluir</button>',
        'Are you sure you want to delete this job?': 'Excluir esta busca e seus resultados?',
        '>Previous</button>': '>Anterior</button>',
        '>Next</button>': '>Próxima</button>',
        '0 results': 'Nenhuma busca ainda. Crie sua primeira busca ao lado.',
        '>Places</h2>': '>Empresas encontradas</h2>',
        'aria-label="Close"': 'aria-label="Fechar"',
        'View on Google Maps': 'Abrir no Google Maps',
        'No places with coordinates were found for this job.': 'Nenhuma empresa com coordenadas foi encontrada nesta busca.',
        'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css': '/mkx-static/vendor/leaflet.css',
        'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js': '/mkx-static/vendor/leaflet.js',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    for status, label in [('ok', 'Concluída'), ('pending', 'Na fila'), ('working', 'Coletando'), ('failed', 'Falhou')]:
        text = text.replace(f'status-{status}">{status}</span>', f'status-{status}">{label}</span>')
    # Add direct actions only to completed jobs; leave collecting jobs inert.
    def enrich(match):
        row = match.group(0)
        if 'status-ok' not in row:
            return row
        found = re.search(r'href="/download\?id=([a-zA-Z0-9_-]+)"', row)
        if not found:
            return row
        job = found.group(1)
        actions = f'<a class="button analyze-button" href="/empresas?job={job}&amp;view=analysis">Analisar ↗</a><a class="button" href="/empresas?job={job}&amp;view=map">Mapa</a>'
        return row.replace('<button type="button" class="button view-button"', actions + '<button type="button" class="button view-button legacy-map"', 1) if 'view-button' in row else row.replace('<a href="/download', actions + '<a href="/download', 1)
    text = re.sub(r'<tr\b[^>]*>.*?</tr>', enrich, text, flags=re.S)
    return text.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.dispatch()

    def do_POST(self):
        self.dispatch()

    def do_DELETE(self):
        self.dispatch()

    def do_OPTIONS(self):
        self.dispatch()

    def dispatch(self):
        path = urlsplit(self.path).path
        if path.startswith("/mkx-api/"):
            return self.crm_dispatch(path)
        if self.command == "GET" and path == "/empresas":
            return self.serve_file(ROOT / "crm.html")
        if self.command == "GET" and path == "/":
            return self.serve_file(ROOT / "index.html")
        if self.command == "GET" and path.startswith("/mkx-static/"):
            target = (ROOT / "static" / path.removeprefix("/mkx-static/")).resolve()
            if not target.is_relative_to((ROOT / "static").resolve()):
                return self.send_error(403)
            return self.serve_file(target)
        length = int(self.headers.get("Content-Length", "0"))
        if length > 2_000_000:
            return self.send_error(413)
        body = self.rfile.read(length) if length else None
        if path == "/scrape" and self.command == "POST" and body:
            fields = parse_qsl(body.decode("utf-8"), keep_blank_values=True)
            fields = [(key, value.strip().lower().split("-")[0] if key == "lang" else value) for key, value in fields]
            body = urlencode(fields).encode()
        headers = {key: value for key, value in self.headers.items() if key.lower() not in {"host", "content-length", "connection", "accept-encoding"}}
        headers["Host"] = f"127.0.0.1:{ENGINE_PORT}"
        connection = http.client.HTTPConnection("127.0.0.1", ENGINE_PORT, timeout=60)
        target_path = self.path
        if path == "/original/":
            target_path = "/"
        try:
            connection.request(self.command, target_path, body, headers)
            response = connection.getresponse()
            data = response.read()
            content_type = response.getheader("Content-Type", "application/octet-stream")
            if path in {"/jobs", "/scrape", "/view", "/delete"} and response.status < 400:
                data = transform_html(data)
                content_type = "text/html; charset=utf-8"
            if path == "/scrape" and response.status >= 400:
                error = data.decode("utf-8", errors="replace").strip()
                data = ERRORS.get(error, f"Não foi possível criar a busca: {error}").encode()
                content_type = "text/plain; charset=utf-8"
            self.send_response(response.status)
            for key, value in response.getheaders():
                if key.lower() not in {"content-length", "connection", "transfer-encoding", "content-type"}:
                    self.send_header(key, value)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except (OSError, http.client.HTTPException):
            self.send_error(502, "Motor indisponivel. Verifique os logs do Docker.")
        finally:
            connection.close()

    def crm_dispatch(self, path):
        try:
            host = self.headers.get("Host", "").split(":")[0].lower()
            if host not in {"localhost", "127.0.0.1"}:
                return self.send_error(403)
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 10_000_000:
                return self.send_error(413)
            # Reject cross-site writes to this local application.
            if self.command == "POST":
                origin = self.headers.get("Origin")
                if origin and origin != "http://" + self.headers.get("Host", ""):
                    return self.send_error(403)
            raw = self.rfile.read(length) if length else b""
            body = json.loads(raw) if raw and path != "/mkx-api/import-csv" else {}
            if path == "/mkx-api/prospects" and self.command == "GET":
                result = {"items": crm.list_all(), "stages": crm.STAGES}
            elif path == "/mkx-api/import-csv" and self.command == "POST":
                result = crm.import_csv(raw, "Importação manual")
            elif path == "/mkx-api/import-job" and self.command == "POST":
                job = str(body.get("id", ""))
                if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", job):
                    raise ValueError("ID de busca inválido.")
                conn = http.client.HTTPConnection("127.0.0.1", ENGINE_PORT, timeout=30)
                try:
                    conn.request("GET", "/download?id=" + job)
                    resp = conn.getresponse()
                    payload = resp.read(10_000_001)
                    if resp.status != 200 or len(payload) > 10_000_000:
                        raise ValueError("CSV indisponível ou maior que 10 MB. Aguarde a conclusão da busca.")
                    result = crm.import_csv(payload, job)
                finally:
                    conn.close()
            elif path.startswith("/mkx-api/prospect/"):
                pieces = path.removeprefix("/mkx-api/prospect/").split("/")
                pid = pieces[0]
                if not re.fullmatch(r"[a-f0-9]{24}", pid):
                    raise ValueError("Empresa inválida.")
                action = pieces[1] if len(pieces) == 2 else ""
                if self.command == "GET" and not action:
                    result = crm.get(pid)
                elif self.command == "POST" and action == "save":
                    result = crm.update(pid, body)
                elif self.command == "POST" and action == "audit":
                    result = crm.audit(pid)
                elif self.command == "POST" and action == "verify":
                    result = crm.verify_site(pid)
                elif self.command == "POST" and action == "ai":
                    result = crm.analyze_ai(pid)
                elif self.command == "POST" and action == "draft":
                    result = crm.draft(pid)
                else:
                    return self.send_error(404)
            elif path == "/mkx-api/export" and self.command == "GET":
                out = io.StringIO()
                writer = csv.writer(out)
                writer.writerow(["Empresa", "Endereço", "Site", "Telefone", "E-mails", "Etapa", "Bloqueado", "Notas"])
                for item in crm.list_all():
                    data = item["data"]
                    cells = [data.get(k, "") for k in ("title", "address", "website", "phone", "emails")] + [item["stage"], str(item["blocked"]), item["notes"]]
                    writer.writerow(["'" + str(v) if str(v).lstrip().startswith(("=", "+", "-", "@")) else str(v) for v in cells])
                payload = ("\ufeff" + out.getvalue()).encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", 'attachment; filename="MKX-empresas.csv"')
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                return self.wfile.write(payload)
            else:
                return self.send_error(404)
            status = 200
        except (ValueError, UnicodeError) as exc:
            result, status = {"error": str(exc)}, 400
        except Exception:
            result, status = {"error": "Falha no banco local. Consulte os logs e confira a pasta gmapsdata."}, 500
            import traceback
            traceback.print_exc()
        payload = json.dumps(result, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def serve_file(self, path):
        if not path.is_file():
            return self.send_error(404)
        data = path.read_bytes()
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {"application/javascript"}:
            content_type += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    engine = subprocess.Popen(["google-maps-scraper", "-web", "-addr", f"127.0.0.1:{ENGINE_PORT}", "-data-folder", "/gmapsdata", "-c", os.getenv("MKX_CONCURRENCY", "2")])
    server = ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
    def stop(signum, frame):
        engine.terminate()
        threading.Thread(target=server.shutdown, daemon=True).start()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    def monitor():
        engine.wait()
        server.shutdown()
    threading.Thread(target=monitor, daemon=True).start()
    print("MKX Radar: painel em :8080. Motor local iniciado.", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        if engine.poll() is None:
            engine.terminate()
        try:
            engine.wait(timeout=15)
        except subprocess.TimeoutExpired:
            engine.kill()
            engine.wait()
    if engine.returncode not in (0, -15):
        raise SystemExit(engine.returncode or 1)

if __name__ == "__main__":
    main()
