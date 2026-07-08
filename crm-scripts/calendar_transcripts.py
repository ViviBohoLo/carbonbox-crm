#!/usr/bin/env python3
"""Cron horario (VPS): (B) renombra las reservas del appointment schedule con la empresa
del CRM para que el transcript de Meet nazca identificado; (C) archiva los transcripts
terminados en Drive en CMR/{Empresa}/. Ver plan 2026-07-07-transcripts-por-empresa."""
import json, os, sys, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, "/root/crm-scripts")
import crm_lib as c
from lead_intake import dominio_de_email

# Las reservas del appointment schedule caen en el calendario secundario "Viviana",
# no en info@carbonbox.app (verificado con una reserva real 2026-07-07).
CAL_ID = "c_82bb139624394ed888e1230ed865b3a186e89bc0188db1c21d543459c34feaec@group.calendar.google.com"
CAL_BASE = "https://www.googleapis.com/calendar/v3"
# Google titula las reservas "<título del schedule> (<nombre de quien reserva>)",
# por eso se compara por PREFIJO, no por igualdad.
TITULO_SCHEDULE = "Hablemos de huellas de carbono con CarbonBox"
SUFIJO = " — Hablemos de huellas de carbono"
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
    return (event.get("summary", "").strip().startswith(TITULO_SCHEDULE)
            and invitado_externo(event) is not None)


def empresa_de_correo(email):
    d = c.gql("""query($e: String!) { people(filter:{emails:{primaryEmail:{eq:$e}}}, first:1) {
        edges { node { company { name } } } } }""", {"e": email.lower()})
    edges = d["people"]["edges"]
    if not edges:
        return None
    comp = edges[0]["node"].get("company")
    return (comp or {}).get("name")


def _api(at, method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Authorization": "Bearer " + at,
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        return json.loads(raw) if raw else {}


def cal_list_upcoming(at):
    from datetime import datetime, timezone
    ahora = datetime.now(timezone.utc).isoformat()
    url = (f"{CAL_BASE}/calendars/{urllib.parse.quote(CAL_ID)}/events"
           f"?singleEvents=true&orderBy=startTime&maxResults=50&timeMin={urllib.parse.quote(ahora)}")
    return _api(at, "GET", url).get("items", [])


def cal_patch_summary(at, event_id, nuevo):
    url = f"{CAL_BASE}/calendars/{urllib.parse.quote(CAL_ID)}/events/{event_id}?sendUpdates=none"
    _api(at, "PATCH", url, {"summary": nuevo})


def renombrar_reservas(at):
    hechos = []
    for ev in cal_list_upcoming(at):
        if not es_reserva_sin_renombrar(ev):
            continue
        try:
            inv = invitado_externo(ev)
            email = inv.get("email", "")
            empresa = empresa_de_correo(email)
            nuevo = nombre_reunion(empresa, nombre=inv.get("displayName"),
                                   dominio=dominio_de_email(email))
            cal_patch_summary(at, ev["id"], nuevo)
            hechos.append((ev["id"], nuevo))
            print(f"[transcripts] renombrado {ev['id']} -> {nuevo}", flush=True)
        except Exception as ex:
            print(f"[transcripts] error renombrando {ev.get('id')}: {ex}", flush=True)
    return hechos


DRIVE_BASE = "https://www.googleapis.com/drive/v3"


def _drive_q(at, q, fields="files(id,name,parents)"):
    url = f"{DRIVE_BASE}/files?q={urllib.parse.quote(q)}&fields={urllib.parse.quote(fields)}&pageSize=1000"
    return _api(at, "GET", url).get("files", [])


def drive_find_folder(at, nombre, parent=None):
    nombre_esc = nombre.replace("\\", "\\\\").replace("'", "\\'")
    q = (f"mimeType='application/vnd.google-apps.folder' and name='{nombre_esc}' and trashed=false")
    if parent:
        q += f" and '{parent}' in parents"
    hits = _drive_q(at, q, fields="files(id,name)")
    return hits[0]["id"] if hits else None


def drive_ensure_folder(at, nombre, parent=None):
    fid = drive_find_folder(at, nombre, parent)
    if fid:
        return fid
    body = {"name": nombre, "mimeType": "application/vnd.google-apps.folder"}
    if parent:
        body["parents"] = [parent]
    return _api(at, "POST", f"{DRIVE_BASE}/files", body)["id"]


def drive_meet_recordings_files(at):
    carpeta = drive_find_folder(at, "Meet Recordings")
    if not carpeta:
        return []
    return _drive_q(at, f"'{carpeta}' in parents and trashed=false")


def drive_move(at, file_id, nuevo_parent, viejo_parent):
    url = f"{DRIVE_BASE}/files/{file_id}?addParents={nuevo_parent}&fields=id"
    if viejo_parent:                       # si el archivo no traía parent, solo lo añadimos
        url += f"&removeParents={viejo_parent}"
    _api(at, "PATCH", url, {})


def archivar_transcripts(at, estado):
    for f in drive_meet_recordings_files(at):
        if f["id"] in estado:
            continue
        empresa = empresa_de_nombre_archivo(f["name"])
        if not empresa:
            continue
        try:
            destino = drive_ensure_folder(at, empresa, parent=CARPETA_RAIZ_ID)
            viejo = (f.get("parents") or [None])[0]
            drive_move(at, f["id"], destino, viejo)
            estado.add(f["id"])
            print(f"[transcripts] archivado {f['name']} -> CMR/{empresa}", flush=True)
        except Exception as ex:
            print(f"[transcripts] error archivando {f.get('id')} ({f.get('name')}): {ex}", flush=True)
    return estado


def cargar_estado():
    try:
        with open(ESTADO) as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def guardar_estado(estado):
    with open(ESTADO, "w") as f:
        json.dump(sorted(estado), f)


def main():
    at = c.google_access_token()
    try:
        renombrar_reservas(at)                                 # B
    except Exception as ex:
        print(f"[transcripts] pasada B fallo: {ex}", flush=True)
    try:
        estado = archivar_transcripts(at, cargar_estado())     # C
        guardar_estado(estado)
    except Exception as ex:
        print(f"[transcripts] pasada C fallo: {ex}", flush=True)


if __name__ == "__main__":
    main()
