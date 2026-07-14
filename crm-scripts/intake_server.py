#!/usr/bin/env python3
"""Servidor de intake del formulario web -> CRM CarbonBox.
Escucha en 127.0.0.1:8088; Caddy lo expone en https://crm.carbonbox.app/intake."""
import json, time, traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import sys
sys.path.insert(0, "/root/crm-scripts")
from lead_intake import mapear_form, es_bot, crear_lead, RateLimiter, origen_cors, ficha_persona_html
from crm_lib import send_notification, google_access_token, now_utc
import seguimiento as seg

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

    def _html(self, code, html):
        body = html.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = urlparse(self.path)
        if p.path.rstrip("/") != "/seguimiento":
            return self._html(404, seg.pagina_mensaje("No encontrado", "Página no encontrada."))
        q = parse_qs(p.query)
        opp_id = (q.get("opp") or [""])[0]
        sig = (q.get("sig") or [""])[0]
        if not seg.valida(opp_id, sig, seg.secreto()):
            return self._html(403, seg.pagina_mensaje("Enlace inválido",
                "Este enlace no es válido. Vuelve a abrirlo desde el reporte.", tono="error"))
        try:
            opp = seg.cargar_opp(opp_id)
        except Exception as ex:
            print(f"[seguimiento] error cargar: {ex}", flush=True)
            return self._html(500, seg.pagina_mensaje("Error", "No se pudo cargar el negocio.", tono="error"))
        if not opp:
            return self._html(404, seg.pagina_mensaje("No encontrado", "El negocio ya no existe."))
        nombre, para, empresa = seg.datos_contacto(opp)
        pl = seg.plantilla(opp["stage"], nombre=nombre, empresa=empresa, negocio=opp["name"])
        if not pl or not para:
            return self._html(400, seg.pagina_mensaje("No disponible",
                "Este negocio no tiene un contacto con correo, o su etapa no admite recordatorio."))
        if seg.aplica_limite_semana(opp["stage"]):
            dias = seg.dias_desde(opp.get("ultimoSeguimiento"), now_utc().date())
            if dias is not None and dias < 7:
                return self._html(200, seg.pagina_mensaje("Ya enviado",
                    f"Ya se envió un recordatorio a este negocio hace {dias} día(s). "
                    "Espera al menos una semana entre recordatorios.", tono="info"))
        asunto, cuerpo = pl
        return self._html(200, seg.pagina_confirmacion(
            opp_id, sig, nombre, para, empresa, opp["name"], asunto, cuerpo))

    def _seguimiento_enviar(self):
        n = int(self.headers.get("Content-Length") or 0)
        form = parse_qs(self.rfile.read(n).decode("utf-8"))
        opp_id = (form.get("opp") or [""])[0]
        sig = (form.get("sig") or [""])[0]
        asunto_f = (form.get("asunto") or [""])[0].strip()
        cuerpo_f = (form.get("cuerpo") or [""])[0].strip()
        if not seg.valida(opp_id, sig, seg.secreto()):
            return self._html(403, seg.pagina_mensaje("Enlace inválido", "Enlace no válido.", tono="error"))
        try:
            opp = seg.cargar_opp(opp_id)
            nombre, para, empresa = seg.datos_contacto(opp)
            pl = seg.plantilla(opp["stage"], nombre=nombre, empresa=empresa, negocio=opp["name"])
            if not pl or not para:
                return self._html(400, seg.pagina_mensaje("No disponible", "Sin contacto o etapa no válida."))
            if seg.aplica_limite_semana(opp["stage"]):
                dias = seg.dias_desde(opp.get("ultimoSeguimiento"), now_utc().date())
                if dias is not None and dias < 7:
                    return self._html(200, seg.pagina_mensaje("Ya enviado", f"Ya se envió hace {dias} día(s).", tono="info"))
            asunto, cuerpo = pl
            asunto = asunto_f or asunto          # usa lo editado en la página; si viene vacío, la plantilla
            cuerpo = cuerpo_f or cuerpo
            seg.enviar_gmail(google_access_token(), para, asunto, seg.cuerpo_email_html(cuerpo), texto=cuerpo)
            seg.registrar_envio(opp_id, now_utc().isoformat(), para)
            print(f"[seguimiento] enviado a {para} ({opp['name']})", flush=True)
            return self._html(200, seg.pagina_mensaje("Enviado",
                f"El recordatorio se envió a {nombre} ({para}) y quedó registrado en el negocio.",
                tono="ok"))
        except Exception as ex:
            print(f"[seguimiento] error envio: {ex}", flush=True)
            print(traceback.format_exc(), flush=True)
            return self._html(500, seg.pagina_mensaje("Error", "No se pudo enviar el recordatorio.", tono="error"))

    def do_POST(self):
        if self.path.rstrip("/") == "/seguimiento/enviar":
            return self._seguimiento_enviar()
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
                    "<p>Entró por el formulario de carbonbox.app y ya está en el CRM "
                    "con su oportunidad y tarea de primer contacto:</p>\n"
                    "<p>" + ficha_persona_html(datos) + "</p>\n"
                    '<p><a href="https://crm.carbonbox.app">Abrir el CRM</a></p>',
                    html=True)
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
