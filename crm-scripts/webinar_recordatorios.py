#!/usr/bin/env python3
"""Recordatorios del webinar (E3: T-7d, E4: T-1d, E5: T-1h).

Corre por cron cada hora. Por cada webinar activo calcula qué recordatorios ya
vencieron (enfoque por umbral) y los envía a los inscritos que aún no lo recibieron.
El destinatario sale del estado del webinar (los que ya pasaron por el intake)."""
import traceback

import sys
sys.path.insert(0, "/root/crm-scripts")
import webinar_lib as wl
from crm_lib import google_access_token, now_utc


def procesar_webinar(slug, cfg, token, ahora):
    try:
        inicio = wl.fecha_inicio(cfg)
    except Exception as ex:
        print(f"[webinar-record] {slug}: fecha_hora inválida ({ex}), omitido", flush=True)
        return
    debidos = wl.recordatorios_debidos(inicio, ahora)
    if not debidos:
        return
    if not cfg.get("meet_link"):
        print(f"[webinar-record] {slug}: hay recordatorios debidos pero falta meet_link; "
              "no se envía hasta tener el enlace", flush=True)
        return

    estado = wl.cargar_estado(slug)
    # Los inscritos son los que ya pasaron por el intake (tienen 'intake' en el estado).
    inscritos = [e for e, etapas in estado.items() if "intake" in etapas]
    # nombre no se guarda en el estado; los correos usan saludo genérico si no hay nombre.
    enviados = 0
    for etapa in debidos:
        for email in inscritos:
            if wl.ya_enviado(estado, email, etapa):
                continue
            try:
                asunto, html, texto = wl.email_recordatorio(cfg, "", etapa)
                wl.enviar(email, asunto, html, texto, token=token)
                wl.marcar_enviado(estado, email, etapa)
                enviados += 1
            except Exception as ex:
                print(f"[webinar-record] {slug}: fallo {etapa} {email}: {ex}", flush=True)
    if enviados:
        wl.guardar_estado(slug, estado)
        print(f"[webinar-record] {slug}: {enviados} recordatorio(s) enviado(s) "
              f"({','.join(debidos)})", flush=True)


def main():
    token = google_access_token()
    ahora = now_utc()
    for slug, cfg in wl.listar_webinars(activos_solo=True):
        try:
            procesar_webinar(slug, cfg, token, ahora)
        except Exception as ex:
            print(f"[webinar-record] {slug}: error: {ex}", flush=True)
            print(traceback.format_exc(), flush=True)


if __name__ == "__main__":
    main()
