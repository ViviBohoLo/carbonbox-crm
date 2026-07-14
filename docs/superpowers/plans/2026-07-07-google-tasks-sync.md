# Recordatorios de tareas vía Google Tasks — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development o superpowers:executing-plans. Los pasos usan checkbox (`- [ ]`).

**Goal:** Que las tareas del CRM asignadas a Viviana lleguen a su celular por Google Tasks (lista "Llamada Lead-CMR"), con sync en dos vías, y que el aviso por correo/nota traiga la info de contacto de la persona.

**Architecture:** Un cron en el VPS cada 10 min corre `gtasks_sync.py`, que lee las tareas abiertas de Viviana (con la persona vinculada), lee la lista de Google Tasks, y **reconcilia** con una función pura contra un mapeo persistido (`gtasks_map.json`). Aparte, se enriquecen el correo y la nota del intake con la ficha de la persona.

**Tech Stack:** Python stdlib (urllib), `crm_lib` (GraphQL Twenty), Google Tasks API REST. Tests `unittest` corridos en el VPS (no hay Python en el PC).

## Global Constraints

- Regla de oro: correos de prueba solo a direcciones propias (info@carbonbox.app).
- Tests se corren en el VPS: `PYTHONPATH=/tmp/tddX:/root/crm-scripts python3 -m unittest ...`.
- Google Tasks API: base `https://tasks.googleapis.com/tasks/v1`; token endpoint `https://oauth2.googleapis.com/token`.
- Refresh token en `/root/.gtasks_token`; client_id/secret en `/root/twenty/.env` (`AUTH_GOOGLE_CLIENT_ID`/`_SECRET`). **No** rotar ese secreto (lo comparte el login del CRM).
- Lista destino Google Tasks: **"Llamada Lead-CMR"**, id `YUpOX0VGanZ2SE90YnpyVA`.
- workspaceMember de Viviana (assignee): `f38776b9-a83b-47c6-8d84-0b32a662ac84`.
- La API de Google Tasks **descarta la hora** del `due` → usar solo fecha (`YYYY-MM-DDT00:00:00.000Z`).
- Código fuente en el repo `carbonbox-crm/crm-scripts/`; deploy por `scp` a `/root/crm-scripts/`.

---

## Task 1: Ficha de la persona en el correo de aviso y en la nota

**Files:**
- Modify: `crm-scripts/lead_intake.py` (nuevo `ficha_persona`, `resumen_lead`; `crear_lead` los usa)
- Modify: `crm-scripts/intake_server.py` (el correo usa la ficha)
- Test: `crm-scripts/test_lead_intake.py`

**Interfaces:**
- Produces: `ficha_persona(datos: dict) -> str` (bloque multilínea con nombre, empresa, teléfono, correo, cargo, ciudad, necesidad); `resumen_lead(datos) -> str` (una línea con lo clave para bullets/log).

- [ ] **Step 1: Test de `ficha_persona` y `resumen_lead`**

En `test_lead_intake.py`, clase nueva:
```python
class TestFicha(unittest.TestCase):
    DATOS = {"nombre": "Ana", "apellido": "Ruiz", "email": "ana@acme.com",
             "tel": "+573001234567", "empresa": "Acme", "cargo": "CEO",
             "ciudad": "Bogotá", "necesidad": "Huella", "mensaje": "Hola"}

    def test_ficha_incluye_todo(self):
        f = li.ficha_persona(self.DATOS)
        for esperado in ["Ana Ruiz", "Acme", "+573001234567", "ana@acme.com", "CEO", "Bogotá", "Huella"]:
            self.assertIn(esperado, f)

    def test_resumen_incluye_empresa_y_telefono(self):
        r = li.resumen_lead(self.DATOS)
        self.assertIn("Acme", r)
        self.assertIn("+573001234567", r)
        self.assertIn("Ana Ruiz", r)
```

- [ ] **Step 2: Correr y ver fallar**

Run: `ssh ... 'cd /tmp/tddX && PYTHONPATH=... python3 -m unittest test_lead_intake -v'` (ver flujo VPS abajo).
Expected: FAIL — `AttributeError: module 'lead_intake' has no attribute 'ficha_persona'`.

- [ ] **Step 3: Implementar en `lead_intake.py`** (antes de `crear_lead`)

```python
def resumen_lead(datos):
    p = " ".join(x for x in [datos.get("nombre"), datos.get("apellido")] if x).strip()
    partes = [p or "(sin nombre)"]
    if datos.get("empresa"):
        partes.append(datos["empresa"])
    linea = " — ".join(partes)
    extra = []
    if datos.get("tel"):
        extra.append(f"📞 {datos['tel']}")
    if datos.get("email"):
        extra.append(f"📧 {datos['email']}")
    return linea + ("  ·  " + "  ·  ".join(extra) if extra else "")


def ficha_persona(datos):
    def campo(etq, val):
        return f"{etq}: {val}" if val else None
    cargo_ciudad = " · ".join(x for x in [datos.get("cargo"), datos.get("ciudad")] if x)
    lineas = [
        campo("Nombre", " ".join(x for x in [datos.get("nombre"), datos.get("apellido")] if x).strip()),
        campo("Empresa", datos.get("empresa")),
        campo("Teléfono", datos.get("tel")),
        campo("Correo", datos.get("email")),
        campo("Cargo", cargo_ciudad),
        campo("Necesidad", datos.get("necesidad")),
    ]
    if datos.get("mensaje"):
        lineas.append(f"Mensaje: {datos['mensaje']}")
    return "\n".join(l for l in lineas if l)
```

- [ ] **Step 4: Usar la ficha en la NOTA dentro de `crear_lead`**

Reemplazar el bloque que arma `cuerpo` de la nota por:
```python
    cuerpo = [ficha_persona(datos), "", "_Origen: formulario web carbonbox.app_"]
    d = gql("""mutation($data: NoteCreateInput!) { createNote(data:$data) { id } }""",
            {"data": {"title": "Formulario web", "bodyV2": {"markdown": "\n".join(cuerpo)}}})
```
Y cambiar el `return` final de `crear_lead` por: `return resumen_lead(datos)`.

- [ ] **Step 5: Correo del intake usa la ficha** — en `intake_server.py`, donde arma `send_notification`:

```python
                send_notification(
                    "🌐 1 lead nuevo desde la web",
                    "Entró por el formulario de carbonbox.app y ya está en el CRM "
                    "con su oportunidad y tarea de primer contacto:\n\n"
                    + ficha_persona(datos)
                    + "\n\nCRM: https://crm.carbonbox.app")
```
Agregar `ficha_persona` al import: `from lead_intake import mapear_form, es_bot, crear_lead, RateLimiter, origen_cors, ficha_persona`.

- [ ] **Step 6: Correr tests → PASS**; luego los tests de `crear_lead` existentes (deben seguir OK porque `resumen_lead` mantiene "Ana Ruiz").

- [ ] **Step 7: Deploy + commit**

```bash
scp -i ~/.ssh/hostinger_vps crm-scripts/lead_intake.py crm-scripts/intake_server.py root@72.60.125.170:/root/crm-scripts/
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'systemctl restart carbonbox-intake && systemctl is-active carbonbox-intake'
git add crm-scripts/lead_intake.py crm-scripts/intake_server.py crm-scripts/test_lead_intake.py
git commit -m "feat(intake): ficha completa de la persona en correo y nota"
```

---

## Task 2: Helpers de Google Tasks (auth + CRUD)

**Files:**
- Create: `crm-scripts/gtasks_sync.py` (por ahora solo los helpers)
- Test: verificación en vivo contra la API (no unit; requiere token real)

**Interfaces:**
- Produces: `gt_access_token() -> str`; `gt_list_tasks(at) -> list[dict]`; `gt_create(at, title, notes, due) -> str` (id); `gt_patch(at, gid, campos: dict) -> None`; `gt_complete(at, gid)`; `LISTA` (const id).

- [ ] **Step 1: Escribir los helpers en `gtasks_sync.py`**

```python
#!/usr/bin/env python3
"""Sincroniza en dos vías las tareas del CRM (asignadas a Viviana) con Google Tasks."""
import json, os, sys, urllib.request, urllib.parse, urllib.error
sys.path.insert(0, "/root/crm-scripts")
import crm_lib as c

LISTA = "YUpOX0VGanZ2SE90YnpyVA"                  # lista "Llamada Lead-CMR"
BASE = "https://tasks.googleapis.com/tasks/v1"
MEMBER = "f38776b9-a83b-47c6-8d84-0b32a662ac84"   # Viviana (assignee)
MAP_FILE = "/root/crm-scripts/gtasks_map.json"


def gt_access_token():
    cid = secret = None
    for line in open("/root/twenty/.env"):
        if line.startswith("AUTH_GOOGLE_CLIENT_ID="):
            cid = line.split("=", 1)[1].strip()
        if line.startswith("AUTH_GOOGLE_CLIENT_SECRET="):
            secret = line.split("=", 1)[1].strip()
    rt = open("/root/.gtasks_token").read().strip()
    data = urllib.parse.urlencode({
        "client_id": cid, "client_secret": secret,
        "refresh_token": rt, "grant_type": "refresh_token"}).encode()
    out = json.load(urllib.request.urlopen(
        urllib.request.Request("https://oauth2.googleapis.com/token", data=data), timeout=30))
    return out["access_token"]


def _api(at, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Authorization": "Bearer " + at,
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        txt = r.read()
    return json.loads(txt) if txt else {}


def gt_list_tasks(at):
    out = _api(at, "GET", f"/lists/{LISTA}/tasks?showCompleted=true&showHidden=true&maxResults=100")
    return out.get("items", [])


def gt_create(at, title, notes, due):
    body = {"title": title, "notes": notes}
    if due:
        body["due"] = due
    return _api(at, "POST", f"/lists/{LISTA}/tasks", body)["id"]


def gt_patch(at, gid, campos):
    _api(at, "PATCH", f"/lists/{LISTA}/tasks/{gid}", campos)


def gt_complete(at, gid):
    _api(at, "PATCH", f"/lists/{LISTA}/tasks/{gid}", {"status": "completed"})
```

- [ ] **Step 2: Verificar en vivo (crear → listar → completar → verificar)**

Desplegar y correr un chequeo puntual en el VPS:
```bash
scp -i ~/.ssh/hostinger_vps crm-scripts/gtasks_sync.py root@72.60.125.170:/root/crm-scripts/
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -c "
import gtasks_sync as g
at=g.gt_access_token()
gid=g.gt_create(at,\"PRUEBA sync\",\"ficha de prueba\",\"2026-07-10T00:00:00.000Z\")
print(\"creada\", gid)
print(\"listadas\", [(t[\"title\"],t[\"status\"]) for t in g.gt_list_tasks(at)])
g.gt_complete(at, gid)
print(\"completada; ahora:\", [(t[\"title\"],t[\"status\"]) for t in g.gt_list_tasks(at)])
import urllib.request
urllib.request.urlopen(urllib.request.Request(g.BASE+f\"/lists/{g.LISTA}/tasks/{gid}\", method=\"DELETE\", headers={\"Authorization\":\"Bearer \"+at})).read()
print(\"borrada la de prueba\")
"'
```
Expected: "creada <id>", la lista incluye "PRUEBA sync" needsAction, luego completed, y se borra al final.

- [ ] **Step 3: Commit**
```bash
git add crm-scripts/gtasks_sync.py && git commit -m "feat(gtasks): helpers de auth y CRUD de Google Tasks"
```

---

## Task 3: Función pura de reconciliación (dos vías)

**Files:**
- Modify: `crm-scripts/gtasks_sync.py` (agregar `plan_sync`)
- Test: `crm-scripts/test_gtasks_sync.py`

**Interfaces:**
- Consumes: nada externo (función pura).
- Produces: `plan_sync(crm_tasks: dict, google_by_id: dict, mapping: dict) -> (acciones: list[dict], nuevo_mapping: dict)`.
  - `crm_tasks`: `{crmId: {"title","notes","due"}}` solo ABIERTAS.
  - `google_by_id`: `{googleId: {"status","title","notes","due"}}`.
  - `mapping`: `{crmId: googleId}`.
  - `acciones`: dicts `{"op": "create"|"update"|"complete_google"|"complete_crm", ...}`:
    `{"op":"create","crm":cid,"data":{...}}`, `{"op":"update","g":gid,"data":{...}}`,
    `{"op":"complete_google","g":gid}`, `{"op":"complete_crm","crm":cid}`.

- [ ] **Step 1: Tests de `plan_sync`** en `crm-scripts/test_gtasks_sync.py`

```python
import unittest
import gtasks_sync as g

T = {"title": "Llamar a Ana", "notes": "ficha", "due": "2026-07-10T00:00:00.000Z"}

class TestPlanSync(unittest.TestCase):
    def test_crea_tarea_nueva(self):
        acc, nuevo = g.plan_sync({"c1": T}, {}, {})
        self.assertEqual(acc, [{"op": "create", "crm": "c1", "data": T}])

    def test_google_completada_marca_crm_done(self):
        gmap = {"c1": "g1"}
        gb = {"g1": {"status": "completed", "title": "Llamar a Ana", "notes": "ficha", "due": T["due"]}}
        acc, nuevo = g.plan_sync({"c1": T}, gb, gmap)
        self.assertIn({"op": "complete_crm", "crm": "c1"}, acc)
        self.assertNotIn("c1", nuevo)

    def test_crm_cerrada_completa_google(self):
        gmap = {"c1": "g1"}
        gb = {"g1": {"status": "needsAction", "title": "Llamar a Ana", "notes": "ficha", "due": T["due"]}}
        acc, nuevo = g.plan_sync({}, gb, gmap)   # c1 ya no está abierta en el CRM
        self.assertIn({"op": "complete_google", "g": "g1"}, acc)
        self.assertNotIn("c1", nuevo)

    def test_sin_cambios_no_hace_nada(self):
        gmap = {"c1": "g1"}
        gb = {"g1": {"status": "needsAction", "title": T["title"], "notes": T["notes"], "due": T["due"]}}
        acc, nuevo = g.plan_sync({"c1": T}, gb, gmap)
        self.assertEqual(acc, [])

    def test_cambio_de_titulo_actualiza(self):
        gmap = {"c1": "g1"}
        gb = {"g1": {"status": "needsAction", "title": "viejo", "notes": T["notes"], "due": T["due"]}}
        acc, nuevo = g.plan_sync({"c1": T}, gb, gmap)
        self.assertEqual(acc, [{"op": "update", "g": "g1", "data": T}])

    def test_google_borrada_se_recrea(self):
        gmap = {"c1": "g1"}                        # mapeada pero ya no existe en google
        acc, nuevo = g.plan_sync({"c1": T}, {}, gmap)
        self.assertEqual(acc, [{"op": "create", "crm": "c1", "data": T}])
```

- [ ] **Step 2: Correr → FAIL** (`plan_sync` no existe).

- [ ] **Step 3: Implementar `plan_sync`** en `gtasks_sync.py`

```python
def plan_sync(crm_tasks, google_by_id, mapping):
    acciones = []
    nuevo = dict(mapping)
    crm_ids = set(crm_tasks)
    # 1) tareas CRM abiertas
    for cid, t in crm_tasks.items():
        gid = mapping.get(cid)
        gt = google_by_id.get(gid) if gid else None
        if gt is None:
            acciones.append({"op": "create", "crm": cid, "data": t})     # nueva o google borrada -> crear
        elif gt.get("status") == "completed":
            acciones.append({"op": "complete_crm", "crm": cid})          # completada en el celular
            nuevo.pop(cid, None)
        elif (gt.get("title"), gt.get("notes"), gt.get("due")) != (t["title"], t["notes"], t["due"]):
            acciones.append({"op": "update", "g": gid, "data": t})       # cambió en el CRM
    # 2) mapeadas que ya NO están abiertas en el CRM -> completadas/borradas en el CRM
    for cid, gid in mapping.items():
        if cid not in crm_ids:
            gt = google_by_id.get(gid)
            if gt is not None and gt.get("status") != "completed":
                acciones.append({"op": "complete_google", "g": gid})
            nuevo.pop(cid, None)
    return acciones, nuevo
```

- [ ] **Step 4: Correr → PASS** (los 6 tests).

- [ ] **Step 5: Commit**
```bash
git add crm-scripts/gtasks_sync.py crm-scripts/test_gtasks_sync.py
git commit -m "feat(gtasks): reconciliación pura de dos vías (plan_sync) + tests"
```

---

## Task 4: main() del sync + formato de la Google Task + cron + E2E

**Files:**
- Modify: `crm-scripts/gtasks_sync.py` (lectura CRM, `titulo_y_notas`, `main`)
- Modify: `deploy/cron/carbonbox-crm` (línea del cron)
- Test: E2E en vivo

**Interfaces:**
- Consumes: `plan_sync`, helpers de Google (Task 2/3), `crm_lib.gql`.

- [ ] **Step 1: Lectura de tareas del CRM con la persona, y formato**

En `gtasks_sync.py`:
```python
def crm_tareas_abiertas():
    """{crmId: {'title','notes','due','_status_prev'}} de las tareas abiertas de Viviana."""
    q = """query($m: UUID!){ tasks(first:100, filter:{assigneeId:{eq:$m},
        status:{in:["TODO","IN_PROGRESS"]}}) { edges { node { id title dueAt
        taskTargets { edges { node { opportunity { name company { name }
          pointOfContact { name{firstName lastName} jobTitle
            emails{primaryEmail} phones{primaryPhoneNumber primaryPhoneCallingCode} } } } } } } } } }"""
    d = c.gql(q, {"m": MEMBER})
    out = {}
    for e in d["tasks"]["edges"]:
        n = e["node"]
        out[n["id"]] = {"title": n["title"], "notes": _notas(n), "due": _due(n.get("dueAt"))}
    return out


def _due(dueAt):
    if not dueAt:
        return ""
    return dueAt[:10] + "T00:00:00.000Z"   # la API descarta la hora


def _notas(node):
    linea = []
    tt = node.get("taskTargets", {}).get("edges", [])
    opp = tt[0]["node"]["opportunity"] if tt and tt[0]["node"].get("opportunity") else None
    if opp:
        p = opp.get("pointOfContact") or {}
        nm = (p.get("name") or {})
        nombre = " ".join(x for x in [nm.get("firstName"), nm.get("lastName")] if x)
        tel = ""
        ph = p.get("phones") or {}
        if ph.get("primaryPhoneNumber"):
            tel = (ph.get("primaryPhoneCallingCode") or "") + ph["primaryPhoneNumber"]
        emails = (p.get("emails") or {})
        for etq, val in [("Nombre", nombre), ("Empresa", (opp.get("company") or {}).get("name")),
                         ("Teléfono", tel), ("Correo", emails.get("primaryEmail")),
                         ("Cargo", p.get("jobTitle"))]:
            if val:
                linea.append(f"{etq}: {val}")
    return "\n".join(linea)
```

- [ ] **Step 2: `main()` que aplica las acciones**

```python
def load_map():
    try:
        return json.load(open(MAP_FILE))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_map(m):
    json.dump(m, open(MAP_FILE, "w"))


def main():
    at = gt_access_token()
    crm_tasks = crm_tareas_abiertas()
    google_by_id = {t["id"]: t for t in gt_list_tasks(at)}
    mapping = load_map()
    acciones, nuevo = plan_sync(crm_tasks, google_by_id, mapping)
    for a in acciones:
        if a["op"] == "create":
            t = a["data"]
            gid = gt_create(at, t["title"], t["notes"], t["due"])
            nuevo[a["crm"]] = gid
        elif a["op"] == "update":
            t = a["data"]
            gt_patch(at, a["g"], {"title": t["title"], "notes": t["notes"],
                                  **({"due": t["due"]} if t["due"] else {})})
        elif a["op"] == "complete_google":
            gt_complete(at, a["g"])
        elif a["op"] == "complete_crm":
            c.gql("""mutation($id: UUID!){ updateTask(id:$id, data:{status:"DONE"}){ id } }""",
                  {"id": a["crm"]})
    save_map(nuevo)
    print(f"sync: {len(acciones)} acciones, {len(nuevo)} tareas mapeadas")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Deploy + E2E**

```bash
scp -i ~/.ssh/hostinger_vps crm-scripts/gtasks_sync.py root@72.60.125.170:/root/crm-scripts/
```
E2E en el VPS:
1. Crear una tarea CRM asignada a Viviana vinculada a una oportunidad de prueba (con persona que tenga teléfono/empresa).
2. `python3 /root/crm-scripts/gtasks_sync.py` → debe crear la Google Task; verificar con `gt_list_tasks` que trae título + notas con teléfono/empresa/correo + due.
3. Completar la Google Task (PATCH status completed) → correr el sync → la tarea del CRM queda `DONE`.
4. Crear otra tarea, completarla en el CRM (updateTask DONE) → correr el sync → su Google Task queda completed.
5. Limpiar la oportunidad/persona/tareas de prueba con `destroyPerson`/`destroyOpportunity` (HARD, no soft; ver memoria).

- [ ] **Step 4: Instalar el cron** — agregar a `deploy/cron/carbonbox-crm` y desplegar:

```
# Sync de tareas CRM <-> Google Tasks - cada 10 min
*/10 * * * * root /usr/bin/python3 /root/crm-scripts/gtasks_sync.py >> /var/log/crm-gtasks.log 2>&1
```
```bash
scp -i ~/.ssh/hostinger_vps deploy/cron/carbonbox-crm root@72.60.125.170:/etc/cron.d/carbonbox-crm
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'chmod 644 /etc/cron.d/carbonbox-crm && systemctl restart cron 2>/dev/null; grep gtasks /etc/cron.d/carbonbox-crm'
```

- [ ] **Step 5: Commit**
```bash
git add crm-scripts/gtasks_sync.py deploy/cron/carbonbox-crm
git commit -m "feat(gtasks): sync CRM<->Google Tasks (main + cron cada 10 min)"
```

---

## Notas de ejecución
- Orden: Task 1 → 2 → 3 → 4. Tasks 1 y 3 son TDD; 2 y 4 se verifican en vivo contra la API.
- El `gtasks_map.json` es estado de runtime (ya está en `.gitignore` por el patrón `*_seen.json`? NO — agregar `gtasks_map.json` al `.gitignore`).
- Latencia: hasta 10 min entre marcar hecho en un lado y verse en el otro.
