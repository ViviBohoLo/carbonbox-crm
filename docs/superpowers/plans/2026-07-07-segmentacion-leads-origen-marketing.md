# Segmentación de contactos por origen y marketing — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que la bienvenida automática ("agenda tu asesoría") solo se envíe a leads del formulario web comercial, y capturar la suscripción de marketing por contacto — sin que webinar/evento/importados entren al funnel ni reciban ese correo.

**Architecture:** Dos ejes en Persona: `fuenteLead` (origen, SELECT ya existente) y `suscritoMarketing` (boolean nuevo). La membresía al funnel la define la existencia de una Oportunidad (ya es así: WF1 dispara en `opportunity.created`). Se agrega un filtro `fuenteLead = WEB` al workflow de bienvenida (dispara en `person.created`). El intake del formulario setea `suscritoMarketing` desde el checkbox de consentimiento.

**Tech Stack:** Twenty CRM (GraphQL core `:3000/graphql` + metadata `:3000/metadata`), Python stdlib (`crm_lib.py`), tests `unittest`. Ejecución operativa por SSH en el VPS (`root@72.60.125.170`, llave `~/.ssh/hostinger_vps`). Frontend del formulario: Astro (`carbonbox-web/index.astro`, deploy por `vercel`).

## Global Constraints

- **Regla de oro:** NUNCA enviar correos reales a clientes sin aprobación de Viviana. Toda prueba de envío va a `info@carbonbox.app` (dirección propia).
- Token API de datos/metadata: `/root/.twenty_api_token` en el VPS (lo lee `crm_lib.token()`). Sirve para datos y `/metadata`, **NO** para el builder de workflows.
- Editar workflows exige **token de usuario** (UserAuthGuard, expira 30 min): en el navegador con sesión de Viviana, `JSON.parse(localStorage.getItem('tokenPairState')).accessOrWorkspaceAgnosticToken.token`.
- Rate limit del API Twenty: 100 req/min → en lotes usar pausa ~0.72 s y reintento en `LIMIT_REACHED`.
- IDs fijos: Person object `16790c1d-680e-488c-8cef-a69feb631305`; campo `fuenteLead` `1ccda2a6-1a51-4a9f-a042-15c4345d5292`; workflow bienvenida `5a4c0efa-d69a-41e9-8edc-3c2782f3510e`, versión activa `523b1309-5fd5-4962-b7fe-e7bec7b5e6a7`, FILTER step `f9d7c224-372f-44d2-8c6a-388c01908400`, grupo de filtro `e795c924-7e71-4651-b6e9-977463bcbebc`.
- Opciones de `fuenteLead` que YA existen: WEB, WEBINAR, FREEMIUM, REFERIDO, ALIADO_B2B, LINKEDIN_ABM, OTRO. No recrearlas.
- El código fuente de los scripts vive en el repo `carbonbox-crm` (espejo local `C:\Users\USUARIO\Claude\Projects\carbonbox-crm\crm-scripts\`); al VPS se despliega por `scp` a `/root/crm-scripts/`.

---

## Task 1: Crear el campo `suscritoMarketing` (boolean) en Persona

**Files:**
- Create (efímero, scratchpad + scp): `crear_campo_suscrito.py`

**Interfaces:**
- Produces: campo `suscritoMarketing` (BOOLEAN, default `true`) en el objeto Person, consumible por Tasks 2, 3 y por la UI.

- [ ] **Step 1: Escribir el script de creación del campo**

```python
#!/usr/bin/env python3
"""Crea el campo booleano suscritoMarketing en Persona (una sola vez)."""
import json, urllib.request, sys
sys.path.insert(0, "/root/crm-scripts")
import crm_lib as c

META = "http://localhost:3000/metadata"
PERSON_OBJ = "16790c1d-680e-488c-8cef-a69feb631305"

def meta(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(META, data=body, headers={
        "Authorization": f"Bearer {c.token()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.load(r)
    if out.get("errors"):
        raise RuntimeError(json.dumps(out["errors"], ensure_ascii=False)[:400])
    return out["data"]

d = meta("""
mutation($input: CreateOneFieldMetadataInput!) {
  createOneField(input: $input) { id name type }
}""", {"input": {"field": {
    "name": "suscritoMarketing",
    "label": "Suscrito a marketing",
    "description": "Recibe correos de marketing (guías, eventos). Consentimiento del contacto.",
    "type": "BOOLEAN",
    "icon": "IconMailStar",
    "objectMetadataId": PERSON_OBJ,
    "defaultValue": True,
}}})
print("Campo creado:", json.dumps(d["createOneField"], ensure_ascii=False))
```

- [ ] **Step 2: Desplegar y ejecutar en el VPS**

Run:
```bash
SP="$SCRATCH/crear_campo_suscrito.py"   # ruta local del script
scp -i ~/.ssh/hostinger_vps "$SP" root@72.60.125.170:/tmp/crear_campo_suscrito.py
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'python3 /tmp/crear_campo_suscrito.py && rm /tmp/crear_campo_suscrito.py'
```
Expected: `Campo creado: {"id": "...", "name": "suscritoMarketing", "type": "BOOLEAN"}`

- [ ] **Step 3: Verificar que el campo existe y su default**

Run:
```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -c "
import crm_lib as c
d=c.gql(\"query{ people(first:1){ edges{ node{ id suscritoMarketing } } } }\")
print(d[\"people\"][\"edges\"][0][\"node\"])
"'
```
Expected: imprime un nodo con la clave `suscritoMarketing` (valor `None` o `False` en registros viejos — se corrige en Task 2). Si la query no falla por campo inexistente, el campo quedó creado.

- [ ] **Step 4: Commit (documentar el script en el repo)**

Guardar el script en `carbonbox-crm/scripts-ops/crear_campo_suscrito.py` (carpeta nueva para scripts operativos de una sola vez) y commitear.
```bash
cd C:/Users/USUARIO/Claude/Projects/carbonbox-crm
git add scripts-ops/crear_campo_suscrito.py
git commit -m "ops: script para crear campo suscritoMarketing en Persona"
```

---

## Task 2: Marcar los contactos existentes como suscritos a marketing

**Files:**
- Create (efímero + repo): `scripts-ops/backfill_suscrito.py`

**Interfaces:**
- Consumes: campo `suscritoMarketing` (Task 1).
- Produces: todos los contactos actuales con `suscritoMarketing = true`.

- [ ] **Step 1: Escribir el script de backfill (paginado + rate limit)**

```python
#!/usr/bin/env python3
"""Marca suscritoMarketing=true en todos los contactos existentes (una sola vez).
Paginado por cursor, con pausa por el rate limit (100 req/min) y reintento."""
import sys, time
sys.path.insert(0, "/root/crm-scripts")
import crm_lib as c

def update_person(pid):
    for intento in range(4):
        try:
            c.gql("""mutation($id: UUID!, $data: PersonUpdateInput!) {
                updatePerson(id: $id, data: $data) { id } }""",
                {"id": pid, "data": {"suscritoMarketing": True}})
            return True
        except RuntimeError as ex:
            if "LIMIT_REACHED" in str(ex) or "rate" in str(ex).lower():
                time.sleep(2 * (intento + 1)); continue
            raise
    return False

cursor = None
total = 0
while True:
    after = f', after: "{cursor}"' if cursor else ""
    d = c.gql("""query { people(first: 60%s) {
        pageInfo { hasNextPage endCursor }
        edges { node { id suscritoMarketing } } } }""" % after)
    edges = d["people"]["edges"]
    for e in edges:
        n = e["node"]
        if n.get("suscritoMarketing") is True:
            continue  # idempotente: ya marcado
        if update_person(n["id"]):
            total += 1
        time.sleep(0.72)
    pi = d["people"]["pageInfo"]
    if not pi["hasNextPage"]:
        break
    cursor = pi["endCursor"]
print(f"Actualizados: {total}")
```

- [ ] **Step 2: Ejecutar en el VPS**

Run:
```bash
scp -i ~/.ssh/hostinger_vps "$SCRATCH/backfill_suscrito.py" root@72.60.125.170:/tmp/backfill_suscrito.py
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'python3 /tmp/backfill_suscrito.py'
```
Expected: `Actualizados: ~1225` (tarda ~15 min por el rate limit; es un one-off).

- [ ] **Step 3: Verificar el conteo por valor**

Run:
```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -c "
import crm_lib as c
t=c.gql(\"query{ people(first:1){ totalCount } }\")[\"people\"][\"totalCount\"]
s=c.gql(\"query{ people(first:1, filter:{suscritoMarketing:{eq:true}}){ totalCount } }\")[\"people\"][\"totalCount\"]
print(f\"total={t}  suscritos={s}\")
"'
```
Expected: `total` y `suscritos` iguales (todos marcados).

- [ ] **Step 4: Commit**

```bash
cd C:/Users/USUARIO/Claude/Projects/carbonbox-crm
git add scripts-ops/backfill_suscrito.py && rm /tmp/backfill_suscrito.py 2>/dev/null
git commit -m "ops: backfill suscritoMarketing=true en contactos existentes"
```

---

## Task 3: El intake del formulario setea `suscritoMarketing` desde el checkbox

**Files:**
- Modify: `crm-scripts/lead_intake.py` (funciones `mapear_form` y `crear_lead`)
- Test: `crm-scripts/test_lead_intake.py`

**Interfaces:**
- Consumes: campo `suscritoMarketing` (Task 1); payload del formulario con nueva clave `acepta_marketing`.
- Produces: personas WEB con `suscritoMarketing` = valor del checkbox (True si marcó, False si no).

- [ ] **Step 1: Escribir el test que falla**

El test file usa `import lead_intake as li` y mockea reasignando `li.gql`. Seguir ese
patrón. En la clase `TestMapeoForm` de `crm-scripts/test_lead_intake.py`, agregar:

```python
    def test_marketing_marcado(self):
        d = li.mapear_form({"firstname": "Ana", "email": "a@x.com",
                            "acepta_marketing": "true"})
        self.assertTrue(d["acepta_marketing"])

    def test_marketing_no_marcado(self):
        d = li.mapear_form({"firstname": "Ana", "email": "a@x.com"})
        self.assertFalse(d["acepta_marketing"])

    def test_marketing_valores_checkbox(self):
        for v in ("true", "on", "1", "yes"):
            self.assertTrue(li.mapear_form({"acepta_marketing": v})["acepta_marketing"], v)
        for v in ("", "false", "0", "off"):
            self.assertFalse(li.mapear_form({"acepta_marketing": v})["acepta_marketing"], v)
```

- [ ] **Step 2: Correr el test y verlo fallar**

Run: `cd C:/Users/USUARIO/Claude/Projects/carbonbox-crm/crm-scripts && python -m unittest test_lead_intake -v`
Expected: FAIL — `KeyError: 'acepta_marketing'` (mapear_form aún no devuelve esa clave).

- [ ] **Step 3: Implementar en `mapear_form`**

En `lead_intake.py`, dentro de `mapear_form`, agregar al dict devuelto:

```python
        "acepta_marketing": (payload.get("acepta_marketing") or "").strip().lower()
                            in ("true", "on", "1", "yes"),
```

- [ ] **Step 4: Correr el test y verlo pasar**

Run: `cd C:/Users/USUARIO/Claude/Projects/carbonbox-crm/crm-scripts && python -m unittest test_lead_intake -v`
Expected: PASS (los 3 tests nuevos + los existentes).

- [ ] **Step 5: Escribir el test de `crear_lead` que setea el campo**

La clase `TestCrearLead` ya tiene un `setUp` que mockea `li.gql` (guardando llamadas en
`self.calls`) y un helper `self._person_input()` que devuelve el `data` del `createPerson`.
Reusarlo. Agregar dentro de `TestCrearLead`:

```python
    def test_setea_suscrito_marketing_true(self):
        li.crear_lead({"nombre": "Ana", "email": "ana@acme.com", "empresa": "Acme",
                       "acepta_marketing": True})
        self.assertTrue(self._person_input()["suscritoMarketing"])

    def test_setea_suscrito_marketing_false(self):
        li.crear_lead({"nombre": "Ana", "email": "ana@acme.com", "empresa": "Acme",
                       "acepta_marketing": False})
        self.assertFalse(self._person_input()["suscritoMarketing"])
```

- [ ] **Step 6: Correr y verlo fallar**

Run: `python -m unittest test_lead_intake -v`
Expected: FAIL — `KeyError: 'suscritoMarketing'` (crear_lead aún no lo setea).

- [ ] **Step 7: Implementar en `crear_lead`**

En `lead_intake.py`, donde se arma `pdata` (tras la línea `"fuenteLead": "WEB"`), incluir el valor:

```python
    pdata = {"name": {"firstName": nombre or "(sin nombre)", "lastName": apellido},
             "fuenteLead": "WEB",
             "suscritoMarketing": bool(datos.get("acepta_marketing"))}
```

- [ ] **Step 8: Correr los tests y verlos pasar**

Run: `python -m unittest test_lead_intake -v`
Expected: PASS (todos).

- [ ] **Step 9: Desplegar al VPS y reiniciar el servicio de intake**

Run:
```bash
scp -i ~/.ssh/hostinger_vps "C:/Users/USUARIO/Claude/Projects/carbonbox-crm/crm-scripts/lead_intake.py" root@72.60.125.170:/root/crm-scripts/lead_intake.py
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'systemctl restart carbonbox-intake && systemctl is-active carbonbox-intake'
```
Expected: `active`.

- [ ] **Step 10: Commit**

```bash
cd C:/Users/USUARIO/Claude/Projects/carbonbox-crm
git add crm-scripts/lead_intake.py crm-scripts/test_lead_intake.py
git commit -m "feat(intake): setear suscritoMarketing desde el checkbox del formulario"
```

---

## Task 4: El formulario web envía el valor del checkbox de marketing

> **Coordinar con Viviana:** el formulario vive en `carbonbox-web/index.astro`, su rediseño WIP sin commitear. NO tocar sin permiso; darle el snippet y que ella lo aplique + `vercel deploy --prod`, o hacerlo con su OK.

**Files:**
- Modify: `Documents/CarbonBox/carbonbox-web/…/index.astro` (el `<form>` que postea a `https://crm.carbonbox.app/intake`)

**Interfaces:**
- Produces: el POST a `/intake` incluye el campo `acepta_marketing` (consumido por Task 3).

- [ ] **Step 1: Localizar el checkbox y el submit en el form**

Run (buscar el checkbox de marketing y cómo se arma el body del POST):
```bash
cd "C:/Users/USUARIO/Documents/CarbonBox/carbonbox-web"
grep -rn "otras comunicaciones\|/intake\|acepta\|checkbox\|FormData\|body:" src 2>/dev/null | head -30
```
Expected: ubica el `<input type="checkbox">` de marketing y el fetch/POST a `/intake`.

- [ ] **Step 2: Darle al checkbox un `name` y enviarlo**

Asegurar que el checkbox de marketing tenga `name="acepta_marketing"`. Si el POST arma el cuerpo manualmente (no con `FormData` del form completo), agregar la clave. Ejemplo si usa objeto JS:

```js
body.acepta_marketing = form.querySelector('[name="acepta_marketing"]').checked ? "true" : "";
```

(Si usa `FormData(form)`, con solo poner el `name` ya viaja; un checkbox no marcado no envía la clave → Task 3 lo interpreta como `false`.)

- [ ] **Step 3: (Opcional, copy) mejorar el texto del checkbox**

Reemplazar "Acepto recibir otras comunicaciones de CarbonBox." por "Acepto recibir novedades, guías y contenido de CarbonBox." Decisión de Viviana.

- [ ] **Step 4: Desplegar y verificar E2E**

Viviana: `vercel deploy --prod` desde `carbonbox-web`. Luego, enviar el formulario en producción con el checkbox **marcado** usando un correo propio de prueba (p.ej. `info+test@carbonbox.app`), y verificar en el CRM que el contacto quedó con `suscritoMarketing = true`; repetir **sin** marcar → `false`. Limpiar los contactos de prueba al terminar (borrar Persona/Empresa/Oportunidad/Nota como en la limpieza del 2026-07-07).

---

## Task 5: Filtrar la bienvenida por `fuenteLead = WEB` (tapa el hueco)

> **Es el arreglo de seguridad.** Puede hacerse primero e independiente de las demás tasks. Requiere **token de usuario** (pedírselo a Viviana justo antes; expira en 30 min).

**Files:**
- Create (efímero): `filtrar_bienvenida.py`

**Interfaces:**
- Consumes: versión activa `523b1309-…` del workflow bienvenida y su FILTER step `f9d7c224-…`.
- Produces: la bienvenida solo dispara cuando `fuenteLead = WEB` **y** hay email.

- [ ] **Step 1: Obtener token de usuario de Viviana**

Pedirle que, con sesión abierta en `https://crm.carbonbox.app`, ejecute en la consola del navegador:
`JSON.parse(localStorage.getItem('tokenPairState')).accessOrWorkspaceAgnosticToken.token` y pegue el token. Guardarlo en el VPS en `/tmp/user_token` (perms 600), efímero.

- [ ] **Step 2: Crear el draft y agregar la condición al FILTER step**

Script `filtrar_bienvenida.py` (usa el token de usuario, NO la API key):

```python
#!/usr/bin/env python3
import json, urllib.request
TOKEN = open("/tmp/user_token").read().strip()
CORE = "http://localhost:3000/graphql"
WF = "5a4c0efa-d69a-41e9-8edc-3c2782f3510e"
VER_ACTIVA = "523b1309-5fd5-4962-b7fe-e7bec7b5e6a7"
GROUP = "e795c924-7e71-4651-b6e9-977463bcbebc"

def gql(q, v=None):
    body = json.dumps({"query": q, "variables": v or {}}).encode()
    r = urllib.request.Request(CORE, data=body, headers={
        "Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=30) as x:
        out = json.load(x)
    if out.get("errors"):
        raise RuntimeError(json.dumps(out["errors"], ensure_ascii=False)[:500])
    return out["data"]

# 1) draft desde la versión activa
d = gql("""mutation($i: CreateDraftFromWorkflowVersionInput!) {
  createDraftFromWorkflowVersion(input: $i) { id } }""",
  {"i": {"workflowId": WF, "workflowVersionIdToCopy": VER_ACTIVA}})
draft = d["createDraftFromWorkflowVersion"]["id"]
print("draft:", draft)

# 2) leer el FILTER step del draft (los ids de step se conservan en la copia)
d = gql("""query($id: UUID!){ workflowVersion(id:$id){ id steps } }""", {"id": draft})
steps = d["workflowVersion"]["steps"]
filt = next(s for s in steps if s["type"] == "FILTER")

# 3) agregar la condición fuenteLead IS WEB al mismo grupo (AND)
import uuid
filt["settings"]["input"]["stepFilters"].append({
    "id": str(uuid.uuid4()),
    "type": "text",
    "value": "WEB",
    "operand": "IS",   # match EXACTO (no CONTAINS: WEBINAR contiene WEB)
    "stepOutputKey": "{{trigger.properties.after.fuenteLead}}",
    "stepFilterGroupId": GROUP,
})

# 4) guardar el step completo
gql("""mutation($i: UpdateWorkflowVersionStepInput!) {
  updateWorkflowVersionStep(input: $i) { id } }""",
  {"i": {"workflowVersionId": draft, "step": filt}})
print("filtro agregado al draft")
print("DRAFT_ID=" + draft)
```

Run:
```bash
scp -i ~/.ssh/hostinger_vps "$SCRATCH/filtrar_bienvenida.py" root@72.60.125.170:/tmp/filtrar_bienvenida.py
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'python3 /tmp/filtrar_bienvenida.py'
```
Expected: imprime `draft: <id>`, `filtro agregado al draft`, `DRAFT_ID=<id>`. Anotar el DRAFT_ID.

- [ ] **Step 3: Probar el draft SIN activarlo (a la propia bandeja)**

Correr el draft con dos payloads simulados (envía correos DE VERDAD, por eso a `info@carbonbox.app`):

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'python3 - <<PY
import json, urllib.request
TOKEN=open("/tmp/user_token").read().strip()
DRAFT="<DRAFT_ID>"   # reemplazar
def run(fuente):
    payload={"properties":{"after":{"name":{"firstName":"Prueba"},
             "emails":{"primaryEmail":"info@carbonbox.app"},"fuenteLead":fuente}}}
    q="""mutation(\$i: RunWorkflowVersionInput!){ runWorkflowVersion(input:\$i){ workflowRunId } }"""
    body=json.dumps({"query":q,"variables":{"i":{"workflowVersionId":DRAFT,"payload":payload}}}).encode()
    r=urllib.request.Request("http://localhost:3000/graphql",data=body,
      headers={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"})
    print(fuente, "->", json.load(urllib.request.urlopen(r,timeout=60)))
run("WEB")       # debe ENVIAR
run("WEBINAR")   # NO debe enviar (filtro SKIP)
PY'
```
Expected: `WEB` devuelve un `workflowRunId` y llega el correo a info@carbonbox.app; `WEBINAR` devuelve `workflowRunId` pero NO llega correo. Verificar en `workflowRuns.state.stepInfos` que en el caso WEBINAR el FILTER quedó `SKIPPED`/`matchesFilter=false` y el SEND_EMAIL no corrió. Si `operand:"IS"` no filtra bien, revisar operandos válidos en el runInfo e iterar (sin activar).

- [ ] **Step 4: Activar el draft**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'python3 - <<PY
import json, urllib.request
TOKEN=open("/tmp/user_token").read().strip()
DRAFT="<DRAFT_ID>"
q="mutation{ activateWorkflowVersion(workflowVersionId:\"%s\") }" % DRAFT
body=json.dumps({"query":q}).encode()
r=urllib.request.Request("http://localhost:3000/graphql",data=body,
  headers={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"})
print(json.load(urllib.request.urlopen(r,timeout=30)))
PY'
```
Expected: `{"data": {"activateWorkflowVersion": true}}`.

- [ ] **Step 5: Verificar el listener y limpiar el token**

Run:
```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -c "
import crm_lib as c, json
d=c.gql(\"query{ workflowVersions(first:5, filter:{workflowId:{eq:\\\"5a4c0efa-d69a-41e9-8edc-3c2782f3510e\\\"}, status:{eq:ACTIVE}}){ edges{ node{ id steps } } } }\")
n=d[\"workflowVersions\"][\"edges\"][0][\"node\"]
f=[s for s in n[\"steps\"] if s[\"type\"]==\"FILTER\"][0]
print(json.dumps(f[\"settings\"][\"input\"][\"stepFilters\"], ensure_ascii=False))
"; rm -f /tmp/user_token /tmp/filtrar_bienvenida.py'
```
Expected: la versión ACTIVA muestra dos stepFilters (email IS_NOT_EMPTY + fuenteLead IS WEB). Token borrado.

- [ ] **Step 6: Commit del script**

```bash
cd C:/Users/USUARIO/Claude/Projects/carbonbox-crm
git add scripts-ops/filtrar_bienvenida.py
git commit -m "ops: filtrar workflow bienvenida por fuenteLead=WEB"
```

---

## Notas de ejecución

- **Orden sugerido:** Task 5 primero si Viviana puede dar el token ahora (es el arreglo de seguridad). Luego 1 → 2 → 3, y 4 coordinada con Viviana. Tasks 1–3 no necesitan token de usuario.
- **Opcional, sin task:** agregar la opción `EVENTO` a `fuenteLead` desde la UI (Settings → Person → fuenteLead → add option) cuando Viviana haga un evento presencial.
- **Verificación final del sistema:** crear un contacto de prueba `fuenteLead=WEBINAR` (por API, a una dirección propia) → NO recibe bienvenida; uno `WEB` → sí. Borrar los de prueba al terminar.
