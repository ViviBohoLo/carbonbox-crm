#!/usr/bin/env python3
"""Cron horario (VPS): (B) renombra las reservas del appointment schedule con la empresa
del CRM para que el transcript de Meet nazca identificado; (C) archiva los transcripts
terminados en Drive en CMR/{Empresa}/. Ver plan 2026-07-07-transcripts-por-empresa."""
import json, os, sys, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, "/root/crm-scripts")
import crm_lib as c

CAL_ID = "info@carbonbox.app"
TITULO_SCHEDULE = "Hablemos de huellas de carbono"   # título exacto del appointment schedule
SUFIJO = " — Llamada CarbonBox"
CARPETA_RAIZ_ID = "1LljLcmMKs7Yg_sdrQziReNXjWykfAKHQ"   # carpeta "CMR" en el Drive de info@carbonbox.app
ESTADO = "/root/crm-scripts/transcripts_movidos.json"


def nombre_reunion(empresa, nombre=None, dominio=None):
    base = (empresa or "").strip() or (dominio or "").strip() or (nombre or "").strip() or "Lead"
    return base + SUFIJO


def empresa_de_nombre_archivo(filename):
    i = filename.find(SUFIJO)
    return filename[:i].strip() if i > 0 else None


def invitado_externo(event):
    for a in event.get("attendees", []):
        email = (a.get("email") or "").lower()
        if email and not email.endswith("@carbonbox.app"):
            return a
    return None


def es_reserva_sin_renombrar(event):
    return event.get("summary", "").strip() == TITULO_SCHEDULE and invitado_externo(event) is not None


def empresa_de_correo(email):
    d = c.gql("""query($e: String!) { people(filter:{emails:{primaryEmail:{eq:$e}}}, first:1) {
        edges { node { company { name } } } } }""", {"e": email.lower()})
    edges = d["people"]["edges"]
    if not edges:
        return None
    comp = edges[0]["node"].get("company")
    return (comp or {}).get("name")
