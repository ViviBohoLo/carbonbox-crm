# Transcripts de llamadas identificados por empresa — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que las llamadas reservadas por el appointment schedule de Google (`calendar.app.google/AguWzEjfLqgBrSFk6`) queden en el calendario **con el nombre de la empresa**, para que el transcript de Meet nazca identificado (opción B), y que además el transcript terminado se archive en una **carpeta de Drive por empresa** (opción C).

**Architecture:** Dos pasadas dentro de un mismo cron horario en el VPS (`calendar_transcripts.py`). **(B)** Lista los eventos del calendario `info@carbonbox.app` cuyo título sigue siendo el nombre genérico del schedule, cruza el correo del invitado externo contra el CRM (Twenty) para sacar la empresa, y **renombra** el evento a `{Empresa} — Llamada CarbonBox`. Como el título cambia, deja de coincidir → idempotente sin estado. **(C)** Recorre la carpeta "Meet Recordings" del Drive del organizador, y por cada artefacto cuyo nombre empiece por `{Empresa} — Llamada CarbonBox` lo mueve a `CMR/{Empresa}/` (CMR = carpeta existente id `1LljLcmMKs7Yg_sdrQziReNXjWykfAKHQ`), guardando los `fileId` ya movidos en un JSON de estado.

**Tech Stack:** Python 3.12 stdlib (urllib), reusa `crm_lib.py` (Twenty GraphQL) y el mecanismo OAuth ya existente de `gtasks_sync.py` (refresh token en `/root/.gtasks_token`, client "CarbonBox CRM Web" en `/root/twenty/.env`). Google Calendar API v3 + Google Drive API v3. Tests con `unittest` inyectando funciones falsas (mismo patrón que `test_lead_intake.py`).

## Global Constraints

- **Sin dependencias nuevas**: solo stdlib (los scripts del VPS ya son así; no hay pip disponible como norma).
- **No hay Python en el PC de Viviana** → los tests se corren en el VPS: `PYTHONPATH=/tmp/tddcal:/root/crm-scripts python3 -m unittest test_calendar_transcripts`.
- **Idempotencia obligatoria**: el cron corre cada hora; ninguna pasada debe re-renombrar ni re-mover algo ya hecho, ni duplicar carpetas.
- **Código en el repo** `carbonbox-crm/crm-scripts/` (espejo local `C:\Users\USUARIO\Claude\Projects\carbonbox-crm`) y desplegado por `scp` a `/root/crm-scripts/` del VPS `72.60.125.170` (llave `~/.ssh/hostinger_vps`). NO es repo git en el VPS.
- **Calendario objetivo**: `info@carbonbox.app` (organizador de las reservas). **Zona horaria**: `America/Bogota`.
- **Anticipación mínima de reserva = 3h** (config del schedule) → un cron horario siempre renombra antes de la llamada.
- **Formato de título** (configurable): `"{Empresa} — Llamada CarbonBox"`. Si no hay empresa en el CRM, usar el dominio corporativo del correo; si es correo gratuito, el nombre del invitado.
- **Nunca** enviar correos ni tocar contactos reales en este flujo (solo lee CRM y edita calendario/drive).

---

## Prerrequisito MANUAL (Viviana) — Ampliar scopes OAuth ✅ HECHO (2026-07-07)

**Estado: COMPLETADO.** El token `/root/.gtasks_token` ya tiene `tasks + calendar.events + drive`; Calendar y Drive API habilitadas; verificado con llamadas reales. Título del schedule confirmado: **"Hablemos de huellas de carbono"**. Carpeta raíz de Drive confirmada: **"CMR"** (id `1LljLcmMKs7Yg_sdrQziReNXjWykfAKHQ`). El resto de esta sección queda como registro del método.


El token `/root/.gtasks_token` hoy solo tiene el scope de **Tasks**. B necesita **Calendar** y C necesita **Drive (completo**, porque el transcript lo crea Google, no nuestra app → `drive.file` no lo vería). La app OAuth es "Interno", así que los scopes sensibles NO requieren verificación de Google.

Pasos (los guía Claude en vivo al ejecutar; reusa el truco `localhost:9999` del setup de Google Tasks):
1. En Google Cloud → proyecto "CarbonBox CRM" → la Tasks API ya está; **habilitar Google Calendar API y Google Drive API**.
2. Correr el helper `obtener_token_google.py` (Task 1) que abre el consent con los 3 scopes:
   `https://www.googleapis.com/auth/tasks`, `https://www.googleapis.com/auth/calendar.events`, `https://www.googleapis.com/auth/drive`.
3. Viviana aprueba en el navegador **logueada como `info@carbonbox.app`** (el organizador de las reservas y dueño del Drive de "Meet Recordings").
4. Guardar el refresh token nuevo en `/root/.gtasks_token` (perms 600). El mismo `gtasks_sync.py` sigue funcionando (más scopes no rompe Tasks).

**Confirmar con Viviana el título exacto del schedule** (default asumido `"Hablemos de huellas de carbono"`). Se ajusta la constante `TITULO_SCHEDULE` si difiere.

---

## File Structure

- **Create** `crm-scripts/calendar_transcripts.py` — módulo principal: helpers puros (nombre de reunión, parseo de empresa desde nombre de archivo, detección de reserva), wrappers de Calendar/Drive API, CRM lookup, y las dos pasadas `renombrar_reservas` / `archivar_transcripts` + `main`.
- **Create** `crm-scripts/test_calendar_transcripts.py` — tests unittest.
- **Modify** `crm-scripts/crm_lib.py` — extraer `google_access_token()` compartido (hoy vive privado en `gtasks_sync.py:gt_access_token`).
- **Modify** `crm-scripts/gtasks_sync.py:23-36` — usar `crm_lib.google_access_token()` (DRY).
- **Modify** `deploy/cron/carbonbox-crm` (y `/etc/cron.d/carbonbox-crm` en el VPS) — línea horaria nueva.
- **State** `/root/crm-scripts/transcripts_movidos.json` — set de `fileId` ya archivados (no versionado; en `.gitignore` como el resto de `*_seen.json`/estado).

---

### Task 1: `google_access_token()` compartido en crm_lib

**Nota:** el consent OAuth YA se hizo a mano en esta sesión — el token en `/root/.gtasks_token` ya tiene `tasks + calendar.events + drive` (verificado con llamadas reales). Esta task es SOLO el refactor para compartir la obtención del access token entre gtasks y el módulo nuevo. (Se decidió NO crear `obtener_token_google.py`; el método de re-consent quedó documentado en memoria.)

**Files:**
- Modify: `crm-scripts/crm_lib.py` (añadir `google_access_token`)
- Modify: `crm-scripts/gtasks_sync.py:23-36` (delegar en el compartido)

**Interfaces:**
- Produces: `crm_lib.google_access_token(refresh_file="/root/.gtasks_token", env_file="/root/twenty/.env") -> str` (access token Bearer, válido para Tasks/Calendar/Drive). Lee client_id/secret de `/root/twenty/.env` y refresh token de `/root/.gtasks_token`.

- [ ] **Step 1: Añadir `google_access_token()` a `crm_lib.py`** (mover la lógica de `gtasks_sync.gt_access_token`)

```python
# crm_lib.py  (añadir)
def google_access_token(refresh_file="/root/.gtasks_token", env_file="/root/twenty/.env"):
    """Access token Bearer para las APIs de Google (Tasks/Calendar/Drive), a partir del
    refresh token compartido y el client 'CarbonBox CRM Web' de /root/twenty/.env."""
    cid = secret = None
    for line in open(env_file):
        if line.startswith("AUTH_GOOGLE_CLIENT_ID="):
            cid = line.split("=", 1)[1].strip()
        if line.startswith("AUTH_GOOGLE_CLIENT_SECRET="):
            secret = line.split("=", 1)[1].strip()
    rt = open(refresh_file).read().strip()
    data = urllib.parse.urlencode({
        "client_id": cid, "client_secret": secret,
        "refresh_token": rt, "grant_type": "refresh_token"}).encode()
    out = json.load(urllib.request.urlopen(
        urllib.request.Request("https://oauth2.googleapis.com/token", data=data), timeout=30))
    return out["access_token"]
```

Verificar que `crm_lib.py` importa `json, urllib.request, urllib.parse` al tope (añadir los que falten).

- [ ] **Step 2: Refactor `gtasks_sync.py:23-36`** para delegar

```python
# gtasks_sync.py — reemplazar el cuerpo de gt_access_token
def gt_access_token():
    return c.google_access_token()
```

- [ ] **Step 3: Correr los tests de gtasks para no romper nada**

Run: subir `crm_lib.py gtasks_sync.py test_gtasks_sync.py` a `/tmp/tddcal` y `PYTHONPATH=/tmp/tddcal:/root/crm-scripts python3 -m unittest test_gtasks_sync -v`
Expected: PASS (sin regresiones).

- [ ] **Step 4: Commit**

```bash
git add crm-scripts/crm_lib.py crm-scripts/gtasks_sync.py
git commit -m "refactor(google): obtencion de access token compartida en crm_lib"
```

---

### Task 2: Helpers puros de nombres (título de reunión y parseo de empresa)

**Files:**
- Create/Modify: `crm-scripts/calendar_transcripts.py`
- Test: `crm-scripts/test_calendar_transcripts.py`

**Interfaces:**
- Produces:
  - `SUFIJO = " — Llamada CarbonBox"`
  - `nombre_reunion(empresa, nombre=None, dominio=None) -> str`
  - `empresa_de_nombre_archivo(filename) -> str | None` (texto antes de `SUFIJO`, o None si no aplica)

- [ ] **Step 1: Tests que fallan**

```python
class TestNombres(unittest.TestCase):
    def test_titulo_con_empresa(self):
        self.assertEqual(ct.nombre_reunion("ITS"), "ITS — Llamada CarbonBox")

    def test_titulo_cae_a_dominio_si_no_hay_empresa(self):
        self.assertEqual(ct.nombre_reunion("", nombre="Yurany", dominio="itsinfocom.com"),
                         "itsinfocom.com — Llamada CarbonBox")

    def test_titulo_cae_a_nombre_si_correo_gratuito(self):
        self.assertEqual(ct.nombre_reunion("", nombre="Yurany", dominio=None),
                         "Yurany — Llamada CarbonBox")

    def test_parsea_empresa_de_transcript(self):
        fn = "ITS — Llamada CarbonBox (2026-07-10 at 14:00) - Transcript"
        self.assertEqual(ct.empresa_de_nombre_archivo(fn), "ITS")

    def test_archivo_ajeno_devuelve_none(self):
        self.assertIsNone(ct.empresa_de_nombre_archivo("Reunión equipo - Notas"))
```

- [ ] **Step 2: Correr y ver fallar**

Run: `PYTHONPATH=/tmp/tddcal:/root/crm-scripts python3 -m unittest test_calendar_transcripts.TestNombres -v`
Expected: FAIL (`No module named 'calendar_transcripts'`).

- [ ] **Step 3: Implementar el encabezado del módulo + helpers**

```python
#!/usr/bin/env python3
"""Cron horario (VPS): (B) renombra las reservas del appointment schedule con la empresa
del CRM para que el transcript de Meet nazca identificado; (C) archiva los transcripts
terminados en Drive en Transcripts CarbonBox/{Empresa}/. Ver plan 2026-07-07-transcripts-por-empresa."""
import json, os, sys, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, "/root/crm-scripts")
import crm_lib as c

CAL_ID = "info@carbonbox.app"
TITULO_SCHEDULE = "Hablemos de huellas de carbono"   # confirmar con Viviana
SUFIJO = " — Llamada CarbonBox"
CARPETA_RAIZ_ID = "1LljLcmMKs7Yg_sdrQziReNXjWykfAKHQ"   # carpeta "CMR" en el Drive de info@carbonbox.app
ESTADO = "/root/crm-scripts/transcripts_movidos.json"


def nombre_reunion(empresa, nombre=None, dominio=None):
    base = (empresa or "").strip() or (dominio or "").strip() or (nombre or "").strip() or "Lead"
    return base + SUFIJO


def empresa_de_nombre_archivo(filename):
    i = filename.find(SUFIJO)
    return filename[:i].strip() if i > 0 else None
```

- [ ] **Step 4: Correr y ver pasar**

Run: `PYTHONPATH=/tmp/tddcal:/root/crm-scripts python3 -m unittest test_calendar_transcripts.TestNombres -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add crm-scripts/calendar_transcripts.py crm-scripts/test_calendar_transcripts.py
git commit -m "feat(transcripts): helpers de nombre de reunion y parseo de empresa"
```

---

### Task 3: Lookup de empresa en el CRM + detección de reserva

**Files:**
- Modify: `crm-scripts/calendar_transcripts.py`
- Test: `crm-scripts/test_calendar_transcripts.py`

**Interfaces:**
- Consumes: `crm_lib.gql(query, variables)` (ya existe; devuelve dict del GraphQL de Twenty).
- Produces:
  - `invitado_externo(event) -> dict | None` (el attendee cuyo email no es `@carbonbox.app`, con `email` y `displayName`)
  - `empresa_de_correo(email) -> str | None` (nombre de la empresa de la persona en el CRM, por email)
  - `es_reserva_sin_renombrar(event) -> bool` (título == `TITULO_SCHEDULE` y hay invitado externo)

- [ ] **Step 1: Tests que fallan**

```python
class TestDeteccion(unittest.TestCase):
    EV = {"summary": "Hablemos de huellas de carbono",
          "attendees": [{"email": "info@carbonbox.app", "self": True},
                        {"email": "ymartinez03@itsinfocom.com", "displayName": "Yurany"}]}

    def test_invitado_externo(self):
        self.assertEqual(ct.invitado_externo(self.EV)["email"], "ymartinez03@itsinfocom.com")

    def test_es_reserva(self):
        self.assertTrue(ct.es_reserva_sin_renombrar(self.EV))

    def test_ya_renombrado_no_es_reserva(self):
        ev = dict(self.EV, summary="ITS — Llamada CarbonBox")
        self.assertFalse(ct.es_reserva_sin_renombrar(ev))

    def test_sin_invitado_externo_no_es_reserva(self):
        ev = {"summary": "Hablemos de huellas de carbono",
              "attendees": [{"email": "info@carbonbox.app", "self": True}]}
        self.assertFalse(ct.es_reserva_sin_renombrar(ev))

    def test_empresa_de_correo(self):
        def fake_gql(q, v=None):
            return {"people": {"edges": [{"node": {"company": {"name": "ITS"}}}]}}
        ct.c.gql = fake_gql
        self.assertEqual(ct.empresa_de_correo("ymartinez03@itsinfocom.com"), "ITS")

    def test_empresa_de_correo_sin_persona(self):
        ct.c.gql = lambda q, v=None: {"people": {"edges": []}}
        self.assertIsNone(ct.empresa_de_correo("nadie@x.com"))
```

- [ ] **Step 2: Correr y ver fallar**

Run: `PYTHONPATH=/tmp/tddcal:/root/crm-scripts python3 -m unittest test_calendar_transcripts.TestDeteccion -v`
Expected: FAIL (funciones no definidas).

- [ ] **Step 3: Implementar**

```python
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
```

- [ ] **Step 4: Correr y ver pasar**

Run: `PYTHONPATH=/tmp/tddcal:/root/crm-scripts python3 -m unittest test_calendar_transcripts.TestDeteccion -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add crm-scripts/calendar_transcripts.py crm-scripts/test_calendar_transcripts.py
git commit -m "feat(transcripts): deteccion de reserva y lookup de empresa en el CRM"
```

---

### Task 4: Pasada B — renombrar reservas (Calendar API)

**Files:**
- Modify: `crm-scripts/calendar_transcripts.py`
- Test: `crm-scripts/test_calendar_transcripts.py`

**Interfaces:**
- Consumes: `crm_lib.google_access_token()`, `dominio_de_email` de `lead_intake` (reusar el filtro de correos gratuitos).
- Produces:
  - `cal_list_upcoming(at) -> list[dict]` (eventos futuros del calendario)
  - `cal_patch_summary(at, event_id, nuevo) -> None`
  - `renombrar_reservas(at) -> list[tuple]` (devuelve `(event_id, nuevo_titulo)` de los renombrados; para log/test)

- [ ] **Step 1: Test que falla** (lógica de decisión con API inyectada)

```python
class TestRenombrar(unittest.TestCase):
    def setUp(self):
        self.patched = []
        ct.cal_list_upcoming = lambda at: [
            {"id": "ev1", "summary": "Hablemos de huellas de carbono",
             "attendees": [{"email": "info@carbonbox.app", "self": True},
                           {"email": "ymartinez03@itsinfocom.com", "displayName": "Yurany"}]},
            {"id": "ev2", "summary": "ITS — Llamada CarbonBox",   # ya renombrado
             "attendees": [{"email": "x@itsinfocom.com"}]},
            {"id": "ev3", "summary": "Reunión interna",
             "attendees": [{"email": "info@carbonbox.app", "self": True}]},
        ]
        ct.cal_patch_summary = lambda at, eid, nuevo: self.patched.append((eid, nuevo))
        ct.empresa_de_correo = lambda e: "ITS"

    def test_solo_renombra_la_reserva_pendiente(self):
        hechos = ct.renombrar_reservas(at="tok")
        self.assertEqual(self.patched, [("ev1", "ITS — Llamada CarbonBox")])
        self.assertEqual(hechos, [("ev1", "ITS — Llamada CarbonBox")])

    def test_sin_empresa_cae_a_dominio(self):
        ct.empresa_de_correo = lambda e: None
        ct.renombrar_reservas(at="tok")
        self.assertEqual(self.patched, [("ev1", "itsinfocom.com — Llamada CarbonBox")])
```

- [ ] **Step 2: Correr y ver fallar**

Run: `PYTHONPATH=/tmp/tddcal:/root/crm-scripts python3 -m unittest test_calendar_transcripts.TestRenombrar -v`
Expected: FAIL.

- [ ] **Step 3: Implementar** (wrappers reales + orquestación)

```python
from lead_intake import dominio_de_email

CAL_BASE = "https://www.googleapis.com/calendar/v3"


def _api(at, method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Authorization": "Bearer " + at,
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        return json.loads(raw) if raw else {}


def cal_list_upcoming(at):
    from datetime import datetime, timezone            # import local: evita Date.now global
    ahora = datetime.now(timezone.utc).isoformat()
    url = (f"{CAL_BASE}/calendars/{urllib.parse.quote(CAL_ID)}/events"
           f"?singleEvents=true&orderBy=startTime&maxResults=50&timeMin={urllib.parse.quote(ahora)}")
    return _api(at, "GET", url).get("items", [])


def cal_patch_summary(at, event_id, nuevo):
    url = f"{CAL_BASE}/calendars/{urllib.parse.quote(CAL_ID)}/events/{event_id}"
    _api(at, "PATCH", url, {"summary": nuevo})


def renombrar_reservas(at):
    hechos = []
    for ev in cal_list_upcoming(at):
        if not es_reserva_sin_renombrar(ev):
            continue
        inv = invitado_externo(ev)
        email = inv.get("email", "")
        empresa = empresa_de_correo(email)
        nuevo = nombre_reunion(empresa, nombre=inv.get("displayName"),
                               dominio=dominio_de_email(email))
        cal_patch_summary(at, ev["id"], nuevo)
        hechos.append((ev["id"], nuevo))
        print(f"[transcripts] renombrado {ev['id']} -> {nuevo}", flush=True)
    return hechos
```

- [ ] **Step 4: Correr y ver pasar**

Run: `PYTHONPATH=/tmp/tddcal:/root/crm-scripts python3 -m unittest test_calendar_transcripts.TestRenombrar -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add crm-scripts/calendar_transcripts.py crm-scripts/test_calendar_transcripts.py
git commit -m "feat(transcripts): pasada B renombra reservas con la empresa (Calendar API)"
```

---

### Task 5: Pasada C — archivar transcripts en carpeta por empresa (Drive API)

**Files:**
- Modify: `crm-scripts/calendar_transcripts.py`
- Test: `crm-scripts/test_calendar_transcripts.py`

**Interfaces:**
- Consumes: `crm_lib.google_access_token()`, estado en `ESTADO`.
- Produces:
  - `drive_find_folder(at, nombre, parent=None) -> str | None`
  - `drive_ensure_folder(at, nombre, parent=None) -> str` (crea si no existe; idempotente)
  - `drive_meet_recordings_files(at) -> list[dict]` (archivos en "Meet Recordings")
  - `drive_move(at, file_id, nuevo_parent, viejo_parent) -> None`
  - `archivar_transcripts(at, estado:set) -> set` (devuelve el set de fileIds movidos, actualizado)

- [ ] **Step 1: Tests que fallan** (orquestación con Drive inyectado; sin tocar red)

```python
class TestArchivar(unittest.TestCase):
    def setUp(self):
        self.moved = []
        self.folders = {}
        ct.drive_meet_recordings_files = lambda at: [
            {"id": "f1", "name": "ITS — Llamada CarbonBox (2026-07-10) - Transcript",
             "parents": ["MEET"]},
            {"id": "f2", "name": "Reunión equipo - Notas", "parents": ["MEET"]},  # ajeno
        ]
        def ensure(at, nombre, parent=None):
            self.folders[(nombre, parent)] = "FID-" + nombre
            return "FID-" + nombre
        ct.drive_ensure_folder = ensure
        ct.drive_move = lambda at, fid, nuevo, viejo: self.moved.append((fid, nuevo, viejo))

    def test_mueve_solo_transcripts_nuestros_no_movidos(self):
        estado = ct.archivar_transcripts(at="tok", estado=set())
        self.assertEqual(self.moved, [("f1", "FID-ITS", "MEET")])
        self.assertIn("f1", estado)

    def test_no_remueve_lo_ya_movido(self):
        ct.archivar_transcripts(at="tok", estado={"f1"})
        self.assertEqual(self.moved, [])
```

- [ ] **Step 2: Correr y ver fallar**

Run: `PYTHONPATH=/tmp/tddcal:/root/crm-scripts python3 -m unittest test_calendar_transcripts.TestArchivar -v`
Expected: FAIL.

- [ ] **Step 3: Implementar**

```python
DRIVE_BASE = "https://www.googleapis.com/drive/v3"


def _drive_q(at, q, fields="files(id,name,parents)"):
    url = f"{DRIVE_BASE}/files?q={urllib.parse.quote(q)}&fields={urllib.parse.quote(fields)}&pageSize=1000"
    return _api(at, "GET", url).get("files", [])


def drive_find_folder(at, nombre, parent=None):
    nombre_esc = nombre.replace("'", "\\'")
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
    url = (f"{DRIVE_BASE}/files/{file_id}"
           f"?addParents={nuevo_parent}&removeParents={viejo_parent}&fields=id")
    _api(at, "PATCH", url, {})


def archivar_transcripts(at, estado):
    for f in drive_meet_recordings_files(at):
        if f["id"] in estado:
            continue
        empresa = empresa_de_nombre_archivo(f["name"])
        if not empresa:
            continue
        destino = drive_ensure_folder(at, empresa, parent=CARPETA_RAIZ_ID)
        viejo = (f.get("parents") or [None])[0]
        drive_move(at, f["id"], destino, viejo)
        estado.add(f["id"])
        print(f"[transcripts] archivado {f['name']} -> CMR/{empresa}", flush=True)
    return estado
```

- [ ] **Step 4: Correr y ver pasar**

Run: `PYTHONPATH=/tmp/tddcal:/root/crm-scripts python3 -m unittest test_calendar_transcripts.TestArchivar -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add crm-scripts/calendar_transcripts.py crm-scripts/test_calendar_transcripts.py
git commit -m "feat(transcripts): pasada C archiva transcripts en carpeta por empresa (Drive API)"
```

---

### Task 6: `main()` + estado en disco + cron horario

**Files:**
- Modify: `crm-scripts/calendar_transcripts.py` (añadir `cargar_estado`, `guardar_estado`, `main`)
- Modify: `deploy/cron/carbonbox-crm`
- Test: `crm-scripts/test_calendar_transcripts.py`

**Interfaces:**
- Consumes: todo lo anterior.
- Produces: `cargar_estado() -> set`, `guardar_estado(set) -> None`, `main() -> None`.

- [ ] **Step 1: Test que falla** (estado round-trip, sin red)

```python
class TestEstado(unittest.TestCase):
    def test_estado_round_trip(self):
        import tempfile, os
        ruta = os.path.join(tempfile.mkdtemp(), "s.json")
        ct.ESTADO = ruta
        ct.guardar_estado({"a", "b"})
        self.assertEqual(ct.cargar_estado(), {"a", "b"})

    def test_estado_vacio_si_no_existe(self):
        ct.ESTADO = "/tmp/no-existe-xyz.json"
        self.assertEqual(ct.cargar_estado(), set())
```

- [ ] **Step 2: Correr y ver fallar**

Run: `PYTHONPATH=/tmp/tddcal:/root/crm-scripts python3 -m unittest test_calendar_transcripts.TestEstado -v`
Expected: FAIL.

- [ ] **Step 3: Implementar estado + main**

```python
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
    renombrar_reservas(at)                 # B
    estado = archivar_transcripts(at, cargar_estado())   # C
    guardar_estado(estado)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Correr y ver pasar** + suite completa

Run: `PYTHONPATH=/tmp/tddcal:/root/crm-scripts python3 -m unittest test_calendar_transcripts -v`
Expected: PASS (todas las clases).

- [ ] **Step 5: Añadir la línea de cron** en `deploy/cron/carbonbox-crm`

```cron
# Transcripts por empresa: renombra reservas (B) y archiva transcripts (C). Cada hora.
17 * * * * root cd /root/crm-scripts && /usr/bin/python3 calendar_transcripts.py >> /var/log/crm-transcripts.log 2>&1
```

(Minuto 17 para no chocar con los otros crons en el :00.)

- [ ] **Step 6: Commit**

```bash
git add crm-scripts/calendar_transcripts.py crm-scripts/test_calendar_transcripts.py deploy/cron/carbonbox-crm
git commit -m "feat(transcripts): main + estado en disco + cron horario"
```

---

### Task 7: Despliegue al VPS y verificación E2E

**Files:** ninguno nuevo (operación).

- [ ] **Step 1: (Prerrequisito) Confirmar que el token ya tiene los 3 scopes** (Viviana hizo el consent). Probar:

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'python3 -c "
import sys; sys.path.insert(0,\"/root/crm-scripts\")
import crm_lib as c, urllib.request, json
at=c.google_access_token()
info=json.load(urllib.request.urlopen(\"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token=\"+at))
print(info[\"scope\"])"'
```
Expected: la salida incluye `tasks`, `calendar.events` y `drive`.

- [ ] **Step 2: Desplegar los archivos**

```bash
cd "/c/Users/USUARIO/Claude/Projects/carbonbox-crm/crm-scripts"
scp -i ~/.ssh/hostinger_vps crm_lib.py gtasks_sync.py calendar_transcripts.py root@72.60.125.170:/root/crm-scripts/
```

- [ ] **Step 3: Correr una vez a mano y ver el log**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 calendar_transcripts.py; echo "exit $?"'
```
Expected: exit 0. Si hay una reserva pendiente, aparece `[transcripts] renombrado ...`.

- [ ] **Step 4: Verificación E2E controlada** (con Viviana): reservar una cita de prueba desde `calendar.app.google/AguWzEjfLqgBrSFk6` con un correo cuya empresa esté en el CRM → correr el script → confirmar en el calendario que el evento pasó a `{Empresa} — Llamada CarbonBox`. Tras una llamada real de prueba con transcript, correr de nuevo y confirmar que el archivo quedó en `CMR/{Empresa}/` (CMR = carpeta existente id `1LljLcmMKs7Yg_sdrQziReNXjWykfAKHQ`). Limpiar la reserva de prueba.

- [ ] **Step 5: Instalar el cron en el VPS y recargar**

```bash
scp -i ~/.ssh/hostinger_vps "/c/Users/USUARIO/Claude/Projects/carbonbox-crm/deploy/cron/carbonbox-crm" root@72.60.125.170:/etc/cron.d/carbonbox-crm
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'chmod 644 /etc/cron.d/carbonbox-crm && systemctl restart cron && echo ok'
```

- [ ] **Step 6: Push del repo**

```bash
cd "/c/Users/USUARIO/Claude/Projects/carbonbox-crm" && git push origin main
```

---

## Notas de diseño / decisiones

- **Por qué el título es la palanca:** el transcript de Meet se nombra `título + fecha` y siempre cae en "Meet Recordings"; Google no ofrece variables en el título del appointment schedule. Renombrar el evento antes de la llamada resuelve el nombre en origen (B); C solo reorganiza en carpetas.
- **Idempotencia B:** tras renombrar, el título ya no es `TITULO_SCHEDULE` → no se reprocesa. Sin estado en disco para B.
- **Idempotencia C:** set de `fileId` movidos en `transcripts_movidos.json`.
- **Fallbacks de nombre:** empresa del CRM → dominio corporativo → nombre del invitado → "Lead".
- **Scope Drive completo:** obligatorio porque el transcript lo crea Google (no nuestra app); `drive.file` no lo vería. Aceptable por ser app OAuth "Interno".
- **Riesgo menor:** una reserva hecha <1h antes podría no renombrarse a tiempo, pero el mínimo del schedule es 3h → cubierto.
- **Riesgo Drive move:** mover artefactos saca el archivo de "Meet Recordings"; el email automático de Google con el link sigue funcionando (apunta por fileId, no por ruta).
