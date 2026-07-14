#!/usr/bin/env python3
"""Puente Google Sheet (respuestas del Form) -> CRM + correo de confirmación.

Corre por cron cada pocos minutos. Por cada webinar activo:
  1. lee las respuestas nuevas del Sheet,
  2. da de alta al inscrito en el CRM (fuenteLead=WEBINAR, sin oportunidad),
  3. le envía el correo de confirmación (E2),
  4. marca el email como procesado ('intake') para no repetir.

Mismo patrón que hubspot_bridge.py (sondeo de una fuente externa -> crear_lead),
pero para inscripciones a webinar. Idempotente vía el estado por webinar."""
import traceback

import sys
sys.path.insert(0, "/root/crm-scripts")
import webinar_lib as wl
from crm_lib import google_access_token, send_notification


def procesar_webinar(slug, cfg, token):
    sheet_id = cfg.get("sheet_id")
    if not sheet_id:
        print(f"[webinar-intake] {slug}: sin sheet_id, omitido", flush=True)
        return
    rango = cfg.get("sheet_rango", "A:Z")
    columnas = cfg.get("columnas", {})
    valores = wl.leer_sheet(sheet_id, rango, token)
    inscritos = wl.filas_inscritos(valores, columnas)

    estado = wl.cargar_estado(slug)
    nuevos = 0
    for datos in inscritos:
        email = datos["email"]
        if wl.ya_enviado(estado, email, "intake"):
            continue
        try:
            wl.alta_inscrito(datos)
        except Exception as ex:
            print(f"[webinar-intake] {slug}: error alta {email}: {ex}", flush=True)
            print(traceback.format_exc(), flush=True)
            continue  # no marcar; se reintenta en la próxima corrida
        # Correo de confirmación (E2)
        try:
            asunto, html, texto = wl.email_confirmacion(cfg, datos.get("nombre", ""))
            wl.enviar(email, asunto, html, texto, token=token)
        except Exception as ex:
            print(f"[webinar-intake] {slug}: alta OK pero fallo E2 {email}: {ex}", flush=True)
            # el alta ya ocurrió: marcamos igual para no duplicar el contacto;
            # el recordatorio siguiente cubre a la persona.
        wl.marcar_enviado(estado, email, "intake")
        nuevos += 1

    if nuevos:
        wl.guardar_estado(slug, estado)
        print(f"[webinar-intake] {slug}: {nuevos} inscrito(s) nuevo(s)", flush=True)
        try:
            send_notification(
                f"🎫 {nuevos} inscrito(s) nuevo(s) al webinar «{cfg.get('titulo', slug)}»",
                f"<p>Entraron por el formulario y ya están en el CRM como "
                f"<b>fuenteLead=WEBINAR</b>.</p>"
                '<p><a href="https://crm.carbonbox.app">Abrir el CRM</a></p>',
                html=True)
        except Exception as ex:
            print(f"[webinar-intake] aviso fallo: {ex}", flush=True)


def main():
    token = google_access_token()
    for slug, cfg in wl.listar_webinars(activos_solo=True):
        try:
            procesar_webinar(slug, cfg, token)
        except Exception as ex:
            print(f"[webinar-intake] {slug}: error: {ex}", flush=True)
            print(traceback.format_exc(), flush=True)


if __name__ == "__main__":
    main()
