#!/usr/bin/env python3
"""Correo post-webinar (E6): agradecimiento + grabación de YouTube.

Se dispara cuando la ficha del webinar ya tiene el video de YouTube y el evento
ya pasó. Envía a TODOS los inscritos (asistieron o no) una sola vez.

Puede correr por cron (cada hora, no hace nada hasta que haya youtube + evento
pasado) o invocarse a mano tras subir la grabación:
    python3 webinar_post.py <slug>
"""
import traceback

import sys
sys.path.insert(0, "/root/crm-scripts")
import webinar_lib as wl
from crm_lib import google_access_token, now_utc


def procesar_webinar(slug, cfg, token, ahora):
    if not (cfg.get("youtube_id") or cfg.get("youtube_url")):
        return  # aún no hay grabación
    try:
        if wl.fecha_inicio(cfg) > ahora:
            return  # el webinar todavía no ocurre
    except Exception:
        pass  # sin fecha válida, permitimos el envío manual

    estado = wl.cargar_estado(slug)
    inscritos = [e for e, etapas in estado.items() if "intake" in etapas]
    enviados = 0
    for email in inscritos:
        if wl.ya_enviado(estado, email, "E6"):
            continue
        try:
            asunto, html, texto = wl.email_post(cfg, "")
            wl.enviar(email, asunto, html, texto, token=token)
            wl.marcar_enviado(estado, email, "E6")
            enviados += 1
        except Exception as ex:
            print(f"[webinar-post] {slug}: fallo E6 {email}: {ex}", flush=True)
    if enviados:
        wl.guardar_estado(slug, estado)
        print(f"[webinar-post] {slug}: {enviados} correo(s) post enviados", flush=True)


def main(slug_pedido=None):
    token = google_access_token()
    ahora = now_utc()
    for slug, cfg in wl.listar_webinars(activos_solo=True):
        if slug_pedido and slug != slug_pedido:
            continue
        try:
            procesar_webinar(slug, cfg, token, ahora)
        except Exception as ex:
            print(f"[webinar-post] {slug}: error: {ex}", flush=True)
            print(traceback.format_exc(), flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
