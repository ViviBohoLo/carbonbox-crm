# Webhook directo del formulario web → CRM — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** El formulario de `carbonbox.app` crea el lead directo en el CRM en tiempo real vía un endpoint propio en el VPS, jubilando el sondeo a HubSpot.

**Architecture:** Se extrae la lógica de creación de `hubspot_bridge.py` a un módulo reutilizable `lead_intake.py`. Un servicio HTTP (`intake_server.py`, stdlib, systemd, `127.0.0.1:8088`) expuesto por Caddy en `/intake` (con CORS) recibe el POST del formulario y llama a esa lógica. El formulario Astro envía al endpoint nuevo (en paralelo con HubSpot durante la transición).

**Tech Stack:** Python 3.12 (stdlib `http.server`, `unittest`), Caddy, systemd, Astro (Vercel).

## Global Constraints

- Sin dependencias Python nuevas: solo stdlib (`http.server`, `json`, `urllib`, `unittest`). Copiado del patrón de los scripts existentes que usan `urllib`.
- El token del CRM (`/root/.twenty_api_token`) NUNCA se expone al navegador; solo lo usa el servidor.
- El servicio escucha SOLO en `127.0.0.1:8088`; la exposición pública la da Caddy.
- CORS: `Access-Control-Allow-Origin: https://carbonbox.app`.
- Fuente del lead: `Person.fuenteLead = "WEB"`, `Opportunity.stage = "LEAD_CAPTURADO"`.
- Los scripts viven en el VPS en `/root/crm-scripts/`. Se desarrollan en el espejo local `CRM CarbonBox/vps/crm-scripts/` y se despliegan por `scp`.
- Tests con stdlib `unittest` (sin pip install). Se corren en WSL: `wsl -d Ubuntu-24.04 -u root -- python3 -m unittest ...`.
- Idempotencia: dedupe de contacto por email (no crear si ya existe).

## File Structure

- Create: `vps/crm-scripts/lead_intake.py` — helpers puros + `crear_lead(datos)` reutilizable.
- Create: `vps/crm-scripts/intake_server.py` — servidor HTTP `/intake` + CORS + honeypot + rate limit.
- Create: `vps/crm-scripts/test_lead_intake.py` — tests unitarios (unittest).
- Modify: `vps/crm-scripts/hubspot_bridge.py` — usar `lead_intake.crear_lead`.
- Create: `vps/carbonbox-intake.service` — unit systemd.
- Modify (VPS): `/etc/caddy/Caddyfile` — ruta `/intake`.
- Modify: `carbonbox-web/src/pages/index.astro` — honeypot + envío al endpoint nuevo.

**Nota de seed:** el espejo local se siembra copiando los scripts actuales del VPS:
`scp -i ~/.ssh/hostinger_vps -r root@72.60.125.170:/root/crm-scripts "CRM CarbonBox/vps/"` (ya existen copias en el scratchpad de la sesión; usar cualquiera de las dos como base).

---

### Task 1: Espejo local + extraer helpers puros a `lead_intake.py`

**Files:**
- Create: `vps/crm-scripts/lead_intake.py`
- Create: `vps/crm-scripts/test_lead_intake.py`
- Seed: `vps/crm-scripts/{crm_lib.py,hubspot_bridge.py}` (copiados del VPS)

**Interfaces:**
- Produces: `dominio_de_email(email) -> str|None`, `pais_de_telefono(tel) -> str|None`, constantes `DOMINIOS_GRATIS: set[str]`, `PAIS_POR_INDICATIVO: dict[str,str]`.

- [ ] **Step 1: Sembrar el espejo local**

```bash
mkdir -p "vps/crm-scripts"
scp -i ~/.ssh/hostinger_vps -o StrictHostKeyChecking=no \
  root@72.60.125.170:/root/crm-scripts/crm_lib.py \
  root@72.60.125.170:/root/crm-scripts/hubspot_bridge.py \
  "vps/crm-scripts/"
```

- [ ] **Step 2: Escribir el test que falla** (`vps/crm-scripts/test_lead_intake.py`)

```python
import unittest
import lead_intake as li

class TestHelpers(unittest.TestCase):
    def test_dominio_corporativo(self):
        self.assertEqual(li.dominio_de_email("ana@acme.com"), "acme.com")
    def test_dominio_gratuito_es_none(self):
        self.assertIsNone(li.dominio_de_email("ana@gmail.com"))
    def test_dominio_sin_arroba(self):
        self.assertIsNone(li.dominio_de_email("noesunemail"))
    def test_pais_por_indicativo(self):
        self.assertEqual(li.pais_de_telefono("+573001234567"), "COLOMBIA")
        self.assertEqual(li.pais_de_telefono("+521234567890"), "MEXICO")
    def test_pais_desconocido(self):
        self.assertIsNone(li.pais_de_telefono("3001234567"))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Correr el test — debe FALLAR**

Run: `wsl -d Ubuntu-24.04 -u root -- bash -c "cd /mnt/c/Users/USUARIO/Claude/Projects/'CRM CarbonBox'/vps/crm-scripts && python3 -m unittest test_lead_intake -v"`
Expected: FAIL — `ModuleNotFoundError: No module named 'lead_intake'`

- [ ] **Step 4: Crear `lead_intake.py` con los helpers** (movidos verbatim de `hubspot_bridge.py`)

```python
#!/usr/bin/env python3
"""Lógica reutilizable de alta de leads en el CRM CarbonBox.
La usan el puente de HubSpot (transición) y el servidor de intake del formulario."""
import sys
sys.path.insert(0, "/root/crm-scripts")
from crm_lib import gql, send_notification

DOMINIOS_GRATIS = {"gmail.com", "hotmail.com", "outlook.com", "yahoo.com",
                   "icloud.com", "live.com", "aol.com", "proton.me",
                   "protonmail.com", "yahoo.es", "hotmail.es", "outlook.es"}

PAIS_POR_INDICATIVO = {"+57": "COLOMBIA", "+52": "MEXICO", "+54": "ARGENTINA",
                       "+56": "CHILE", "+51": "PERU"}


def dominio_de_email(email):
    if not email or "@" not in email:
        return None
    dom = email.split("@")[1].lower()
    return None if dom in DOMINIOS_GRATIS else dom


def pais_de_telefono(tel):
    for ind, p in PAIS_POR_INDICATIVO.items():
        if tel.startswith(ind):
            return p
    return None
```

- [ ] **Step 5: Correr el test — debe PASAR**

Run: `wsl -d Ubuntu-24.04 -u root -- bash -c "cd /mnt/c/Users/USUARIO/Claude/Projects/'CRM CarbonBox'/vps/crm-scripts && python3 -m unittest test_lead_intake -v"`
Expected: PASS (5 tests)

- [ ] **Step 6: Commit** (en el repo donde vivan los specs/plan; si el proyecto CRM no es git, omitir y anotar)

```bash
git add vps/crm-scripts/lead_intake.py vps/crm-scripts/test_lead_intake.py 2>/dev/null || echo "proyecto CRM sin git; archivos guardados en disco"
```

---

### Task 2: `crear_lead(datos)` + refactor de `hubspot_bridge.py`

**Files:**
- Modify: `vps/crm-scripts/lead_intake.py`
- Modify: `vps/crm-scripts/hubspot_bridge.py`
- Modify: `vps/crm-scripts/test_lead_intake.py`

**Interfaces:**
- Produces: `crear_lead(datos: dict) -> str|None`. `datos` = `{nombre, apellido, email, tel, empresa, cargo, ciudad, necesidad, mensaje}` (strings; faltantes = `""`). Devuelve resumen `"Nombre Apellido <email> — Empresa"` o `None` si se omite (contacto duplicado por email o sin datos mínimos). Crea Empresa(dedup)+Contacto(WEB)+Oportunidad(LEAD_CAPTURADO)+Nota.
- Consumes: `gql` (de crm_lib, parcheable en tests).

- [ ] **Step 1: Test que falla — mapeo del contacto** (añadir a `test_lead_intake.py`)

```python
class TestCrearLead(unittest.TestCase):
    def setUp(self):
        self.calls = []
        # gql falso: registra (query, variables) y devuelve ids segun la mutacion
        def fake_gql(query, variables=None):
            self.calls.append((query, variables or {}))
            if "people(filter" in query:
                return {"people": {"edges": []}}          # no existe -> no dup
            if "companies(filter" in query:
                return {"companies": {"edges": []}}        # no existe
            if "createCompany" in query:
                return {"createCompany": {"id": "co-1"}}
            if "createPerson" in query:
                return {"createPerson": {"id": "pe-1"}}
            if "createOpportunity" in query:
                return {"createOpportunity": {"id": "op-1"}}
            if "createNote" in query and "Target" not in query:
                return {"createNote": {"id": "no-1"}}
            if "createNoteTarget" in query:
                return {"createNoteTarget": {"id": "nt-1"}}
            return {}
        li.gql = fake_gql

    def _person_input(self):
        for q, v in self.calls:
            if "createPerson" in q:
                return v["data"]
        return None

    def test_persona_fuente_web_y_stage(self):
        datos = {"nombre": "Ana", "apellido": "Ruiz", "email": "ana@acme.com",
                 "tel": "+573001234567", "empresa": "Acme", "cargo": "CEO",
                 "ciudad": "Bogotá", "necesidad": "Huella", "mensaje": "Hola"}
        r = li.crear_lead(datos)
        self.assertIn("Ana Ruiz", r)
        self.assertEqual(self._person_input()["fuenteLead"], "WEB")
        # se creó una oportunidad en LEAD_CAPTURADO
        self.assertTrue(any("createOpportunity" in q and v["data"]["stage"] == "LEAD_CAPTURADO"
                            for q, v in self.calls))

    def test_dedupe_email_existente(self):
        li.gql = lambda q, v=None: {"people": {"edges": [{"node": {"id": "x"}}]}} \
            if "people(filter" in q else {}
        r = li.crear_lead({"nombre": "Ya", "apellido": "Existe",
                           "email": "dup@acme.com", "tel": "", "empresa": "",
                           "cargo": "", "ciudad": "", "necesidad": "", "mensaje": ""})
        self.assertIsNone(r)
```

- [ ] **Step 2: Correr — debe FALLAR**

Run: `wsl -d Ubuntu-24.04 -u root -- bash -c "cd /mnt/c/Users/USUARIO/Claude/Projects/'CRM CarbonBox'/vps/crm-scripts && python3 -m unittest test_lead_intake -v"`
Expected: FAIL — `AttributeError: module 'lead_intake' has no attribute 'crear_lead'`

- [ ] **Step 3: Añadir `find_or_create_company` y `crear_lead` a `lead_intake.py`** (lógica movida de `hubspot_bridge.procesar`)

```python
def find_or_create_company(nombre, dominio=None, pais=None, ciudad=None):
    if not nombre:
        return None
    d = gql("""query($n: String!) { companies(filter:{name:{ilike:$n}}, first:1) {
        edges { node { id } } } }""", {"n": nombre})
    edges = d["companies"]["edges"]
    if edges:
        return edges[0]["node"]["id"]
    data = {"name": nombre}
    if dominio:
        data["domainName"] = {"primaryLinkUrl": f"https://{dominio}"}
    if pais:
        data["pais"] = pais
    if ciudad:
        data["address"] = {"addressCity": ciudad}
    d = gql("""mutation($data: CompanyCreateInput!) { createCompany(data:$data) { id } }""",
            {"data": data})
    return d["createCompany"]["id"]


def crear_lead(datos):
    """Crea Empresa(dedup)+Contacto(WEB)+Oportunidad(LEAD_CAPTURADO)+Nota.
    Devuelve resumen o None si se omite (dup por email o sin datos minimos)."""
    nombre = (datos.get("nombre") or "").strip()
    apellido = (datos.get("apellido") or "").strip()
    email = (datos.get("email") or "").strip().lower()
    tel = (datos.get("tel") or "").replace(" ", "")
    empresa = (datos.get("empresa") or "").strip()
    cargo = (datos.get("cargo") or "").strip()
    ciudad = (datos.get("ciudad") or "").strip()
    necesidad = (datos.get("necesidad") or "").strip()
    mensaje = (datos.get("mensaje") or "").strip()

    if not email and not (nombre or apellido):
        return None
    if email:
        d = gql("""query($e: String!) { people(filter:{emails:{primaryEmail:{eq:$e}}}, first:1) {
            edges { node { id } } } }""", {"e": email})
        if d["people"]["edges"]:
            return None

    company_id = find_or_create_company(
        empresa,
        dominio=dominio_de_email(email),
        pais=pais_de_telefono(tel) or ("COLOMBIA" if tel and not tel.startswith("+") else None),
        ciudad=ciudad or None)

    pdata = {"name": {"firstName": nombre or "(sin nombre)", "lastName": apellido},
             "fuenteLead": "WEB"}
    if email:
        pdata["emails"] = {"primaryEmail": email}
    if tel:
        pdata["phones"] = ({"primaryPhoneNumber": tel.lstrip("+"),
                            "primaryPhoneCallingCode": "+" + tel.lstrip("+")[:2],
                            "primaryPhoneCountryCode": "CO"} if tel.startswith("+")
                           else {"primaryPhoneNumber": tel,
                                 "primaryPhoneCallingCode": "+57",
                                 "primaryPhoneCountryCode": "CO"})
    if cargo:
        pdata["jobTitle"] = cargo[:120]
    if company_id:
        pdata["companyId"] = company_id
    d = gql("""mutation($data: PersonCreateInput!) { createPerson(data:$data) { id } }""",
            {"data": pdata})
    person_id = d["createPerson"]["id"]

    opp_name = f"{empresa or (nombre + ' ' + apellido).strip()} — web"
    odata = {"name": opp_name, "stage": "LEAD_CAPTURADO", "pointOfContactId": person_id}
    if company_id:
        odata["companyId"] = company_id
    d = gql("""mutation($data: OpportunityCreateInput!) { createOpportunity(data:$data) { id } }""",
            {"data": odata})
    opp_id = d["createOpportunity"]["id"]

    cuerpo = []
    if necesidad:
        cuerpo.append(f"**Necesidad:** {necesidad}")
    if mensaje:
        cuerpo.append(f"**Mensaje:** {mensaje}")
    cuerpo.append("_Origen: formulario web carbonbox.app_")
    d = gql("""mutation($data: NoteCreateInput!) { createNote(data:$data) { id } }""",
            {"data": {"title": "Formulario web", "bodyV2": {"markdown": "\n\n".join(cuerpo)}}})
    note_id = d["createNote"]["id"]
    gql("""mutation($data: NoteTargetCreateInput!) { createNoteTarget(data:$data) { id } }""",
        {"data": {"noteId": note_id, "targetOpportunityId": opp_id}})

    return f"{nombre} {apellido} <{email}> — {empresa}"
```

- [ ] **Step 4: Correr — debe PASAR**

Run: `wsl -d Ubuntu-24.04 -u root -- bash -c "cd /mnt/c/Users/USUARIO/Claude/Projects/'CRM CarbonBox'/vps/crm-scripts && python3 -m unittest test_lead_intake -v"`
Expected: PASS (todos)

- [ ] **Step 5: Refactor `hubspot_bridge.py`** — que `procesar` reutilice `crear_lead`

Reemplazar en `hubspot_bridge.py`: borrar `DOMINIOS_GRATIS`, `PAIS_POR_INDICATIVO`, `dominio_de_email`, `pais_de_telefono`, `find_or_create_company` y el cuerpo de creación de `procesar`. La cabecera de imports pasa a:

```python
import json, os, sys, time, urllib.request, urllib.parse
sys.path.insert(0, "/root/crm-scripts")
from crm_lib import send_notification
from lead_intake import crear_lead
```

Y `procesar` queda solo como parser HubSpot → `datos` → `crear_lead`:

```python
def procesar(sub):
    vals = sub.get("values", [])
    datos = {
        "nombre":   campo(vals, "firstname", "nombre"),
        "apellido": campo(vals, "lastname", "apellido", "apellidos"),
        "email":    campo(vals, "email", "correo").lower(),
        "tel":      campo(vals, "phone", "mobilephone", "telefono").replace(" ", ""),
        "empresa":  campo(vals, "company", "empresa"),
        "cargo":    campo(vals, "jobtitle", "cargo"),
        "ciudad":   campo(vals, "city", "ciudad"),
        "necesidad": campo(vals, "necesidad", "servicio", "que_necesitas",
                           "what_do_you_need", "message_topic", "0-1/necesidad"),
        "mensaje":  campo(vals, "message", "descripcion", "descripción", "mensaje"),
    }
    return crear_lead(datos)
```

- [ ] **Step 6: Verificar que `hubspot_bridge.py` compila**

Run: `wsl -d Ubuntu-24.04 -u root -- bash -c "cd /mnt/c/Users/USUARIO/Claude/Projects/'CRM CarbonBox'/vps/crm-scripts && python3 -c 'import ast; ast.parse(open(\"hubspot_bridge.py\").read()); print(\"OK sintaxis\")'"`
Expected: `OK sintaxis`

- [ ] **Step 7: Commit**

```bash
git add vps/crm-scripts/ 2>/dev/null || echo "sin git; guardado en disco"
```

---

### Task 3: Mapeo del formulario + honeypot

**Files:**
- Modify: `vps/crm-scripts/lead_intake.py`
- Modify: `vps/crm-scripts/test_lead_intake.py`

**Interfaces:**
- Produces: `mapear_form(payload: dict) -> dict` (payload del form → `datos`). `es_bot(payload) -> bool` (True si el honeypot `website` viene lleno).

- [ ] **Step 1: Test que falla**

```python
class TestMapeoForm(unittest.TestCase):
    def test_mapea_campos(self):
        payload = {"firstname": "Ana", "lastname": "Ruiz", "email": "ANA@Acme.com",
                   "mobilephone": "+57 300 123 4567", "company": "Acme",
                   "jobtitle": "CEO", "city": "Bogotá", "necesidad": "Huella",
                   "describenos_cual_es_tu_necesidad": "Hola"}
        d = li.mapear_form(payload)
        self.assertEqual(d["nombre"], "Ana")
        self.assertEqual(d["email"], "ana@acme.com")
        self.assertEqual(d["tel"], "+573001234567")
        self.assertEqual(d["mensaje"], "Hola")
    def test_honeypot(self):
        self.assertTrue(li.es_bot({"website": "http://spam"}))
        self.assertFalse(li.es_bot({"website": ""}))
        self.assertFalse(li.es_bot({}))
```

- [ ] **Step 2: Correr — FALLA** (`AttributeError: ... 'mapear_form'`)

Run: `wsl -d Ubuntu-24.04 -u root -- bash -c "cd /mnt/c/Users/USUARIO/Claude/Projects/'CRM CarbonBox'/vps/crm-scripts && python3 -m unittest test_lead_intake -v"`

- [ ] **Step 3: Implementar en `lead_intake.py`**

```python
def es_bot(payload):
    """Honeypot: los bots rellenan el campo oculto 'website'."""
    return bool((payload.get("website") or "").strip())


def mapear_form(payload):
    """Payload plano del formulario web -> dict `datos` de crear_lead."""
    def g(k):
        return (payload.get(k) or "").strip()
    return {
        "nombre": g("firstname"),
        "apellido": g("lastname"),
        "email": g("email").lower(),
        "tel": g("mobilephone").replace(" ", ""),
        "empresa": g("company"),
        "cargo": g("jobtitle"),
        "ciudad": g("city"),
        "necesidad": g("necesidad"),
        "mensaje": g("describenos_cual_es_tu_necesidad"),
    }
```

- [ ] **Step 4: Correr — PASA**

Run: `wsl -d Ubuntu-24.04 -u root -- bash -c "cd /mnt/c/Users/USUARIO/Claude/Projects/'CRM CarbonBox'/vps/crm-scripts && python3 -m unittest test_lead_intake -v"`

- [ ] **Step 5: Commit**

```bash
git add vps/crm-scripts/ 2>/dev/null || echo "sin git"
```

---

### Task 4: Rate limiter por IP

**Files:**
- Modify: `vps/crm-scripts/lead_intake.py`
- Modify: `vps/crm-scripts/test_lead_intake.py`

**Interfaces:**
- Produces: `RateLimiter(max_por_hora=5)` con método `permite(ip: str, ahora: float) -> bool`. `ahora` es epoch segundos (inyectable para test).

- [ ] **Step 1: Test que falla**

```python
class TestRateLimiter(unittest.TestCase):
    def test_bloquea_tras_el_limite(self):
        rl = li.RateLimiter(max_por_hora=3)
        t = 1000.0
        self.assertTrue(rl.permite("1.1.1.1", t))
        self.assertTrue(rl.permite("1.1.1.1", t))
        self.assertTrue(rl.permite("1.1.1.1", t))
        self.assertFalse(rl.permite("1.1.1.1", t))          # 4to en la misma hora
    def test_otra_ip_no_afecta(self):
        rl = li.RateLimiter(max_por_hora=1)
        t = 1000.0
        self.assertTrue(rl.permite("1.1.1.1", t))
        self.assertTrue(rl.permite("2.2.2.2", t))
    def test_ventana_se_libera(self):
        rl = li.RateLimiter(max_por_hora=1)
        self.assertTrue(rl.permite("1.1.1.1", 1000.0))
        self.assertFalse(rl.permite("1.1.1.1", 1000.0))
        self.assertTrue(rl.permite("1.1.1.1", 1000.0 + 3601))  # pasó 1h
```

- [ ] **Step 2: Correr — FALLA**

Run: `wsl -d Ubuntu-24.04 -u root -- bash -c "cd /mnt/c/Users/USUARIO/Claude/Projects/'CRM CarbonBox'/vps/crm-scripts && python3 -m unittest test_lead_intake -v"`

- [ ] **Step 3: Implementar en `lead_intake.py`**

```python
class RateLimiter:
    """Límite simple en memoria: N envíos por IP por hora (ventana deslizante)."""
    def __init__(self, max_por_hora=5):
        self.max = max_por_hora
        self._hist = {}  # ip -> [timestamps]

    def permite(self, ip, ahora):
        h = [t for t in self._hist.get(ip, []) if ahora - t < 3600]
        if len(h) >= self.max:
            self._hist[ip] = h
            return False
        h.append(ahora)
        self._hist[ip] = h
        return True
```

- [ ] **Step 4: Correr — PASA**

Run: `wsl -d Ubuntu-24.04 -u root -- bash -c "cd /mnt/c/Users/USUARIO/Claude/Projects/'CRM CarbonBox'/vps/crm-scripts && python3 -m unittest test_lead_intake -v"`

- [ ] **Step 5: Commit**

```bash
git add vps/crm-scripts/ 2>/dev/null || echo "sin git"
```

---

### Task 5: Servidor HTTP `intake_server.py`

**Files:**
- Create: `vps/crm-scripts/intake_server.py`

**Interfaces:**
- Consumes: `lead_intake.{mapear_form, es_bot, crear_lead, RateLimiter, send_notification}`.
- Produces: proceso que escucha en `127.0.0.1:8088`, maneja `POST /intake` y `OPTIONS /intake`.

- [ ] **Step 1: Crear `intake_server.py`**

```python
#!/usr/bin/env python3
"""Servidor de intake del formulario web -> CRM CarbonBox.
Escucha en 127.0.0.1:8088; Caddy lo expone en https://crm.carbonbox.app/intake."""
import json, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys
sys.path.insert(0, "/root/crm-scripts")
from lead_intake import mapear_form, es_bot, crear_lead, RateLimiter
from crm_lib import send_notification

HOST, PORT = "127.0.0.1", 8088
ORIGIN = "https://carbonbox.app"
LIMITER = RateLimiter(max_por_hora=5)


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self._cors()
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
        if not LIMITER.permite(ip, time.time()):
            return self._json(429, {"ok": False, "error": "rate limit"})
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
            print(f"[intake] error CRM: {ex}", flush=True)
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
```

- [ ] **Step 2: Verificar sintaxis**

Run: `wsl -d Ubuntu-24.04 -u root -- bash -c "cd /mnt/c/Users/USUARIO/Claude/Projects/'CRM CarbonBox'/vps/crm-scripts && python3 -c 'import ast; ast.parse(open(\"intake_server.py\").read()); print(\"OK\")'"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add vps/crm-scripts/intake_server.py 2>/dev/null || echo "sin git"
```

---

### Task 6: Desplegar en el VPS (systemd + Caddy) y verificar por curl

**Files:**
- Create: `vps/carbonbox-intake.service`
- Modify (VPS): `/etc/caddy/Caddyfile`

**Interfaces:**
- Consumes: los scripts de `vps/crm-scripts/` desplegados a `/root/crm-scripts/`.

- [ ] **Step 1: Crear el unit systemd** (`vps/carbonbox-intake.service`)

```ini
[Unit]
Description=CarbonBox intake del formulario web
After=docker.service
Wants=docker.service

[Service]
ExecStart=/usr/bin/python3 /root/crm-scripts/intake_server.py
Restart=always
RestartSec=3
User=root
StandardOutput=append:/var/log/carbonbox-intake.log
StandardError=append:/var/log/carbonbox-intake.log

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 2: Desplegar scripts + unit al VPS**

```bash
SP="vps"
scp -i ~/.ssh/hostinger_vps -o StrictHostKeyChecking=no \
  "$SP/crm-scripts/lead_intake.py" "$SP/crm-scripts/intake_server.py" \
  "$SP/crm-scripts/hubspot_bridge.py" \
  root@72.60.125.170:/root/crm-scripts/
scp -i ~/.ssh/hostinger_vps "$SP/carbonbox-intake.service" \
  root@72.60.125.170:/etc/systemd/system/carbonbox-intake.service
```

- [ ] **Step 3: Arrancar el servicio**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'systemctl daemon-reload && systemctl enable --now carbonbox-intake && sleep 2 && systemctl is-active carbonbox-intake && ss -tlnp | grep 8088'
```
Expected: `active` y un listener en `127.0.0.1:8088`.

- [ ] **Step 4: Actualizar el Caddyfile** (en el VPS) con la ruta `/intake`

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cat > /etc/caddy/Caddyfile <<EOF
crm.carbonbox.app {
	handle /intake* {
		reverse_proxy 127.0.0.1:8088
	}
	handle {
		reverse_proxy localhost:3000
	}
}
EOF
caddy validate --config /etc/caddy/Caddyfile && systemctl reload caddy && echo RELOADED'
```
Expected: `RELOADED`.

- [ ] **Step 5: Prueba de integración — honeypot (NO crea)**

```bash
curl -s -w "\n%{http_code}\n" -X POST https://crm.carbonbox.app/intake \
  -H "Content-Type: application/json" \
  -d '{"firstname":"Bot","email":"bot@x.com","website":"http://spam"}'
```
Expected: `{"ok": true}` y `200`, y en el CRM NO aparece "Bot" (honeypot descarta). Verificar en el log: `ssh ... 'tail -3 /var/log/carbonbox-intake.log'` no debe decir "lead creado".

- [ ] **Step 6: Prueba de integración — lead real de prueba (crea, luego se borra)**

```bash
curl -s -w "\n%{http_code}\n" -X POST https://crm.carbonbox.app/intake \
  -H "Content-Type: application/json" \
  -d '{"firstname":"Prueba","lastname":"Intake","email":"prueba.intake@ejemplo-test.com","mobilephone":"+573001112233","company":"Ejemplo Test SAS","jobtitle":"QA","city":"Bogotá","necesidad":"Cálculo de huella","describenos_cual_es_tu_necesidad":"Lead de prueba del endpoint /intake"}'
```
Expected: `{"ok": true}` y `200`. Verificar en el CRM (por API) que existan el contacto y la oportunidad:
```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'TK=$(cat /root/.twenty_api_token); curl -s -H "Authorization: Bearer $TK" "http://localhost:3000/rest/people?filter=emails.primaryEmail[eq]:prueba.intake@ejemplo-test.com" | head -c 300; echo'
```
Expected: el contacto de prueba aparece con `fuenteLead: WEB`.

- [ ] **Step 7: Limpiar el lead de prueba** (borrar contacto+empresa+oportunidad de prueba en el CRM UI, o dejar anotado para que Viviana lo borre). Registrar en el log de ejecución que se creó `prueba.intake@ejemplo-test.com`.

- [ ] **Step 8: Prueba CORS preflight**

```bash
curl -s -i -X OPTIONS https://crm.carbonbox.app/intake -H "Origin: https://carbonbox.app" -H "Access-Control-Request-Method: POST" | grep -i "access-control-allow-origin"
```
Expected: `Access-Control-Allow-Origin: https://carbonbox.app`.

- [ ] **Step 9: Commit**

```bash
git add vps/carbonbox-intake.service 2>/dev/null || echo "sin git"
```

---

### Task 7: Cambiar el formulario (`index.astro`) — honeypot + envío al endpoint (paralelo con HubSpot)

**Files:**
- Modify: `carbonbox-web/src/pages/index.astro`

**Interfaces:**
- Consumes: endpoint `https://crm.carbonbox.app/intake` (Task 6).

- [ ] **Step 1: Añadir el campo honeypot oculto** dentro del `<form id="cb-contact-form">` (ej. después de la etiqueta `<form ...>`, línea ~623). Debe ser invisible y no enfocarse:

```html
<input type="text" name="website" tabindex="-1" autocomplete="off"
       style="position:absolute;left:-9999px;width:1px;height:1px;opacity:0;" aria-hidden="true" />
```

- [ ] **Step 2: Modificar el `<script>` de envío** (líneas ~664-712). Nueva lógica: enviar al endpoint del CRM (principal) y a HubSpot en paralelo (best-effort), redirigir a `/gracias` si el CRM responde OK:

```javascript
  const form = document.getElementById("cb-contact-form");
  const statusEl = document.getElementById("cb-contact-status");
  const btn = document.getElementById("cb-contact-submit");
  const CRM_ENDPOINT = "https://crm.carbonbox.app/intake";
  const HUBSPOT_ENDPOINT = "https://api.hsforms.com/submissions/v3/integration/submit/23967833/64b92eab-d7b8-4d6e-b381-881adf692a4d";

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!form.reportValidity()) return;
    const fd = new FormData(form);
    const names = ["firstname","lastname","email","mobilephone","company","jobtitle","city","necesidad","describenos_cual_es_tu_necesidad"];
    const flat = {};
    names.forEach((n) => { flat[n] = (fd.get(n) || "").toString(); });
    flat.website = (fd.get("website") || "").toString(); // honeypot

    btn.disabled = true; btn.style.opacity = "0.6"; btn.textContent = "Enviando…";
    statusEl.style.color = "var(--ink-3)"; statusEl.textContent = "Enviando…";

    // HubSpot en paralelo (best-effort, transición); no bloquea
    const commsOptIn = document.getElementById("cb-consent-comms")?.checked || false;
    const hsPayload = {
      fields: names.map((n) => ({ name: n, value: flat[n] })),
      context: { pageUri: location.href, pageName: document.title },
      legalConsentOptions: { consent: { consentToProcess: true,
        text: "Acepto permitir a CarbonBox almacenar y procesar mis datos personales",
        communications: [{ value: commsOptIn, subscriptionTypeId: 75448251, text: "Acepto recibir otras comunicaciones de CarbonBox" }] } },
    };
    fetch(HUBSPOT_ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(hsPayload) }).catch(() => {});

    try {
      const res = await fetch(CRM_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(flat),
      });
      if (res.ok) {
        window.location.href = "/gracias";
      } else {
        statusEl.style.color = "#c0392b";
        statusEl.textContent = "No pudimos enviar el formulario. Escríbenos a info@carbonbox.app o inténtalo de nuevo.";
        btn.disabled = false; btn.style.opacity = "1"; btn.textContent = "Enviar mensaje →";
      }
    } catch (err) {
      console.error(err);
      statusEl.style.color = "#c0392b";
      statusEl.textContent = "Error de conexión. Escríbenos a info@carbonbox.app o inténtalo de nuevo.";
      btn.disabled = false; btn.style.opacity = "1"; btn.textContent = "Enviar mensaje →";
    }
  });
```

- [ ] **Step 3: Build local del sitio**

Run: `cd "C:/Users/USUARIO/Documents/CarbonBox/carbonbox-web" && npm run build`
Expected: build sin errores.

- [ ] **Step 4: Desplegar preview a Vercel**

Run: `cd "C:/Users/USUARIO/Documents/CarbonBox/carbonbox-web" && npx vercel deploy` (preview URL). Si pide login/link, seguir el flujo o pedir a Viviana.
Expected: una URL de preview.

- [ ] **Step 5: Prueba E2E en el preview** — abrir el preview, enviar el formulario con datos de prueba (email `prueba.e2e@ejemplo-test.com`), confirmar redirección a `/gracias` y que el lead aparece en el CRM (`crm.carbonbox.app`) con la tarea de primer contacto (WF1). Anotar el lead de prueba para limpieza.

- [ ] **Step 6: Commit + promover a producción**

```bash
cd "C:/Users/USUARIO/Documents/CarbonBox/carbonbox-web"
git add src/pages/index.astro
git commit -m "feat: formulario envia directo al CRM (intake) + honeypot; HubSpot en paralelo"
npx vercel deploy --prod
```

---

### Task 8: Cutover final — quitar HubSpot y apagar el puente (tras días en paralelo sin fallos)

**Files:**
- Modify: `carbonbox-web/src/pages/index.astro`
- Modify (VPS): `/etc/cron.d/carbonbox-crm`

> Ejecutar SOLO tras un periodo en paralelo verificado (ej. 1-2 semanas o varios leads reales OK). Es una tarea separada en el tiempo.

- [ ] **Step 1: Quitar HubSpot del formulario** — en `index.astro`, borrar la constante `HUBSPOT_ENDPOINT` y la línea `fetch(HUBSPOT_ENDPOINT, ...)`. Dejar solo el envío al CRM.

- [ ] **Step 2: Build + deploy prod**

```bash
cd "C:/Users/USUARIO/Documents/CarbonBox/carbonbox-web" && npm run build && git add src/pages/index.astro && git commit -m "chore: quitar HubSpot del formulario (cutover a CRM directo)" && npx vercel deploy --prod
```

- [ ] **Step 3: Desactivar el cron del puente HubSpot en el VPS** — comentar solo la línea del bridge:

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 "sed -i 's|^\*/5 \* \* \* \* root /usr/bin/python3 /root/crm-scripts/hubspot_bridge.py|# (jubilado, cutover intake) &|' /etc/cron.d/carbonbox-crm && grep hubspot_bridge /etc/cron.d/carbonbox-crm"
```
Expected: la línea del bridge queda comentada (`# (jubilado...)`).

- [ ] **Step 4: Verificar** que el vigía y el reporte siguen activos (no se tocaron) y que un envío real sigue creando el lead vía `/intake`.

- [ ] **Step 5: Commit / anotar cierre** en la memoria del proyecto (actualizar `carbonbox-vps.md` y `funnel-carbonbox-config.md`: formulario ya por webhook directo, HubSpot jubilado).

---

## Notas de ejecución

- **Datos de prueba a limpiar:** los leads `prueba.intake@ejemplo-test.com` y `prueba.e2e@ejemplo-test.com` (+ empresa "Ejemplo Test SAS") se crean en el CRM real durante las pruebas; borrarlos al final (o pedir a Viviana).
- **Rollback rápido del formulario:** como HubSpot sigue en paralelo hasta la Task 8, si `/intake` falla los leads no se pierden (quedan en HubSpot y el cron del puente los recoge). Para revertir el form, `git revert` del commit de la Task 7 + `vercel deploy --prod`.
- **Rollback del servicio:** `systemctl stop carbonbox-intake` y restaurar el Caddyfile anterior (`crm.carbonbox.app { reverse_proxy localhost:3000 }`) + `systemctl reload caddy`.
