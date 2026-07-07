#!/usr/bin/env python3
"""Servidor de intake del formulario web -> CRM CarbonBox.
Escucha en 127.0.0.1:8088; Caddy lo expone en https://crm.carbonbox.app/intake."""
import json, time, traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys
sys.path.insert(0, "/root/crm-scripts")
from lead_intake import mapear_form, es_bot, crear_lead, RateLimiter, origen_cors
from crm_lib import send_notification

HOST, PORT = "127.0.0.1", 8088
# Ventana corta por IP con holgura para absorber los reintentos del cliente.
LIMITER = RateLimiter(max_peticiones=10, ventana_seg=300)


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", origen_cors(self.headers.get("Origin")))
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        # que el JS del navegador (cross-origin) pueda leer Retry-After
        self.send_header("Access-Control-Expose-Headers", "Retry-After")

    def _json(self, code, obj, extra_headers=None):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self._cors()
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path.rstrip("/") != "/intake":
            return self._json(404, {"ok": False, "error": "not found"})
        ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
        ahora = time.time()
        if not LIMITER.permite(ip, ahora):
            return self._json(429, {"ok": False, "error": "rate limit"},
                              extra_headers={"Retry-After": str(LIMITER.retry_after(ip, ahora))})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._json(400, {"ok": False, "error": "json invalido"})
        if es_bot(payload):
            return self._json(200, {"ok": True})  # bot: fingir exito, no crear
        datos = mapear_form(payload)
        if not datos["email"] and not (datos["nombre"] or datos["apellido"]):
            return self._json(400, {"ok": False, "error": "faltan datos"})
        try:
            resumen = crear_lead(datos)
        except Exception as ex:
            # crear_lead ya trata los duplicados como benignos (devuelve None); aquí solo
            # caen errores inesperados. Logear el detalle real para diagnosticar.
            detalle = str(ex)
            if hasattr(ex, "code") and hasattr(ex, "read"):  # urllib.error.HTTPError
                try:
                    detalle = f"{ex.code} {ex.read().decode('utf-8', 'replace')}"
                except Exception:
                    pass
            print(f"[intake] error CRM: {detalle}", flush=True)
            print(traceback.format_exc(), flush=True)
            return self._json(500, {"ok": False, "error": "crm"})
        if resumen:
            try:
                send_notification(
                    "🌐 1 lead nuevo desde la web",
                    "Entró por el formulario de carbonbox.app y ya está en el CRM "
                    f"con su oportunidad y tarea de primer contacto:\n\n• {resumen}"
                    "\n\nCRM: https://crm.carbonbox.app")
            except Exception as ex:
                print(f"[intake] aviso email fallo: {ex}", flush=True)
            print(f"[intake] lead creado: {resumen}", flush=True)
        else:
            print("[intake] omitido (duplicado o sin datos)", flush=True)
        return self._json(200, {"ok": True})

    def log_message(self, *a):
        pass  # silenciar el log por defecto


if __name__ == "__main__":
    print(f"[intake] escuchando en {HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
