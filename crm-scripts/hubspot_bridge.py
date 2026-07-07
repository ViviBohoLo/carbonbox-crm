#!/usr/bin/env python3
"""Puente formulario web carbonbox.app → CRM CarbonBox.
Sondea los envíos del formulario (HubSpot Forms API) y crea en Twenty:
Empresa (si no existe) + Contacto (fuente WEB) + Oportunidad + Nota con el mensaje.
El workflow '① Lead nuevo' del CRM dispara solo la tarea de primer contacto.

Estado: /root/crm-scripts/hubspot_seen.json (ids ya procesados).
Token HubSpot: /root/.hubspot_token (app privada, scope forms).
"""
import json, os, sys, time, urllib.request, urllib.parse

sys.path.insert(0, "/root/crm-scripts")
from crm_lib import send_notification
from lead_intake import crear_lead, es_duplicado

FORM_GUID = "64b92eab-d7b8-4d6e-b381-881adf692a4d"
HS_URL = f"https://api.hubapi.com/form-integrations/v1/submissions/forms/{FORM_GUID}?limit=50"
SEEN_FILE = "/root/crm-scripts/hubspot_seen.json"
TOKEN_FILE = "/root/.hubspot_token"


def hs_get(url):
    tk = open(TOKEN_FILE).read().strip()
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tk}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def load_seen():
    try:
        return set(json.load(open(SEEN_FILE)))
    except Exception:
        return set()


def save_seen(seen):
    json.dump(sorted(seen), open(SEEN_FILE, "w"))


def campo(values, *names):
    """Extrae un campo del envío por nombre de propiedad HubSpot."""
    for v in values:
        if v.get("name", "").lower() in [n.lower() for n in names]:
            return (v.get("value") or "").strip()
    return ""


def procesar(sub):
    vals = sub.get("values", [])
    datos = {
        "nombre":    campo(vals, "firstname", "nombre"),
        "apellido":  campo(vals, "lastname", "apellido", "apellidos"),
        "email":     campo(vals, "email", "correo").lower(),
        "tel":       campo(vals, "phone", "mobilephone", "telefono").replace(" ", ""),
        "empresa":   campo(vals, "company", "empresa"),
        "cargo":     campo(vals, "jobtitle", "cargo"),
        "ciudad":    campo(vals, "city", "ciudad"),
        "necesidad": campo(vals, "necesidad", "servicio", "que_necesitas",
                           "what_do_you_need", "message_topic", "0-1/necesidad"),
        "mensaje":   campo(vals, "message", "descripcion", "descripción", "mensaje"),
    }
    return crear_lead(datos)


def main():
    if not os.path.exists(TOKEN_FILE):
        print("falta /root/.hubspot_token"); return
    seen = load_seen()
    data = hs_get(HS_URL)
    subs = data.get("results", [])
    nuevos = []
    for sub in subs:
        sid = str(sub.get("submittedAt", "")) + "|" + campo(sub.get("values", []), "email", "correo")
        if sid in seen:
            continue
        try:
            r = procesar(sub)
            if r:
                nuevos.append(r)
        except Exception as ex:
            if es_duplicado(ex):
                # el contacto ya existe → tratar como procesado (no reintentar)
                print(f"omitido (ya existe) {sid}")
                seen.add(sid)
            else:
                print(f"error procesando {sid}: {ex}")  # transitorio → reintentar luego
            continue
        seen.add(sid)
        time.sleep(1)
    save_seen(seen)
    if nuevos:
        send_notification(
            f"🌐 {len(nuevos)} lead(s) nuevos desde la web",
            "Entraron por el formulario de carbonbox.app y ya están en el CRM "
            "con su oportunidad y tarea de primer contacto:\n\n"
            + "\n".join("• " + n for n in nuevos)
            + "\n\nCRM: http://localhost:3000")
        print(f"{len(nuevos)} leads nuevos")
    else:
        print("sin envíos nuevos")


if __name__ == "__main__":
    main()
