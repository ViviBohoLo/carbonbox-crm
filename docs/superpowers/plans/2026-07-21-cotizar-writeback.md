# Write-back de cotizaciones — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development o superpowers:executing-plans. Los pasos usan checkbox (`- [ ]`).

**Goal:** Cerrar el ciclo de `/cotizar`: subir el deck a Drive, dejar su link en la oportunidad, y enviar la cotización al cliente desde una página de confirmación (remitente elegible + CC), guardando el link del correo enviado.

**Architecture:** Dos mitades. (A) En el PC de Viviana, la skill sube el deck a `Leads/{Empresa}/` y llama a `registrar-cotizacion.js`, que escribe en el CRM. (B) En el servidor, un módulo nuevo `cotizacion.py` sirve la página `/cotizacion` (misma mecánica que `/seguimiento`) y envía por Gmail API. Las funciones puras se prueban con `unittest`; los efectos viven en `intake_server.py`.

**Tech Stack:** Python 3.12 stdlib (servidor), Node 18+ (script del CRM), GraphQL de Twenty, Gmail API, Caddy.

## Global Constraints

- Servidor: `/root/crm-scripts/` (espejo local en `CRM CarbonBox/vps/crm-scripts/`). Script del CRM: `tools/cotizar/Generadores/` en el repo `carbonbox-crm`.
- Tests de Python **se corren en el VPS** (no hay Python en el PC): `ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest … -v'`. Tests de Node, en el PC: `node --test "Generadores/test/*.test.js"`.
- **Regla de oro:** el correo va a un cliente. El GET solo muestra; **solo el botón envía**.
- Carpeta Drive `Leads` = `13dvWmMahnoyl_xsAZohAGVHoA8vIdX5A`. **Nunca crear carpetas**: si hay 0 o >1 coincidencia, preguntar.
- Remitentes válidos (send-as verificados sobre `info@carbonbox.app`): `viviana.bohorquez@`, `laura.bautista@`, `alejandra.rojas@`, `miguel.romero@`.
- Asunto estándar: `Cotización CarbonBox — {Empresa}` (editable en la página).
- Mapeo de plan → `planCarbonbox`: `esencial`→`ESENCIAL`, `pro`→`PRO`, **`experto`→`PREMIUM`** (decisión de Viviana 2026-07-21).
- Campos LINKS de Twenty son compuestos: `{ primaryLinkUrl, primaryLinkLabel }`.
- Permalink de Gmail: `https://mail.google.com/mail/u/0/#all/{threadId}`.
- Opportunity objectMetadataId: `172aabee-dad7-4c72-a89d-251b9d7e97ae`.

---

### Task 1: Campo `borradorCorreo` en Opportunity

Es el puente entre la skill (que redacta en el PC) y la página (que la sirve el servidor).

**Files:** ninguno (metadata API).

**Interfaces:**
- Produces: campo `borradorCorreo` (TEXT) en Opportunity.

- [ ] **Step 1: Crear el campo**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -c "
import urllib.request, json
from crm_lib import token
OPP=\"172aabee-dad7-4c72-a89d-251b9d7e97ae\"
def meta(q,v=None):
    b=json.dumps({\"query\":q,\"variables\":v or {}}).encode()
    r=urllib.request.Request(\"http://localhost:3000/metadata\", b, {\"Authorization\":f\"Bearer {token()}\",\"Content-Type\":\"application/json\"})
    o=json.load(urllib.request.urlopen(r,timeout=120))
    if o.get(\"errors\"): raise SystemExit(json.dumps(o[\"errors\"],ensure_ascii=False)[:400])
    return o[\"data\"]
r=meta(\"mutation(\$in: CreateOneFieldMetadataInput!){ createOneField(input:\$in){ id name type } }\",
  {\"in\":{\"field\":{\"name\":\"borradorCorreo\",\"label\":\"Borrador de correo\",\"type\":\"TEXT\",\"objectMetadataId\":OPP,\"icon\":\"IconMailCog\",
    \"description\":\"Borrador del correo de cotización que redacta /cotizar. La página de confirmación lo lee y lo limpia al enviar.\"}}})
print(r[\"createOneField\"])
"'
```
Esperado: imprime el campo con su id.

- [ ] **Step 2: Verificar**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -c "
from crm_lib import gql
print(gql(\"query{ opportunities(first:1){edges{node{name borradorCorreo}}} }\")[\"opportunities\"][\"edges\"][0][\"node\"])
"'
```
Esperado: el nodo con `borradorCorreo: None`, sin error.

---

### Task 2: `registrar-cotizacion.js` — llenar plan, link del deck y borrador

**Files:**
- Modify: `tools/cotizar/Generadores/registrar-cotizacion.js`
- Test: `tools/cotizar/Generadores/test/registrar-cotizacion.test.js`

**Interfaces:**
- Produces: flags nuevos `--link-cotizacion <url>` y `--borrador-archivo <ruta>`; función
  `planACodigo(plan) -> "ESENCIAL"|"PRO"|"PREMIUM"|null`.
- El script pasa a escribir en la oportunidad: `planCarbonbox`, `linkCotizacion`, `borradorCorreo`.

> `--borrador-archivo` recibe una **ruta**, no el texto: el borrador es largo y multilínea, y
> pasarlo como argumento de shell se rompe con comillas y saltos de línea.

- [ ] **Step 1: Escribir el test** (agregar a `test/registrar-cotizacion.test.js`)

```js
const { test } = require("node:test");
const assert = require("node:assert");
const { planACodigo } = require("../registrar-cotizacion.js");

test("planACodigo mapea los planes de la calculadora al campo del CRM", () => {
  assert.equal(planACodigo("esencial"), "ESENCIAL");
  assert.equal(planACodigo("Pro"), "PRO");
  assert.equal(planACodigo("PRO"), "PRO");
  // El CRM no tiene "Experto": se guarda como Premium (decisión de Viviana)
  assert.equal(planACodigo("experto"), "PREMIUM");
  assert.equal(planACodigo("Experto"), "PREMIUM");
});

test("planACodigo devuelve null si el plan no se reconoce", () => {
  assert.equal(planACodigo("otro"), null);
  assert.equal(planACodigo(""), null);
  assert.equal(planACodigo(undefined), null);
});
```

- [ ] **Step 2: Correr y ver fallar**

```bash
cd "C:/Users/USUARIO/Claude/Projects/carbonbox-crm/tools/cotizar" && node --test "Generadores/test/registrar-cotizacion.test.js"
```
Esperado: FAIL (`planACodigo is not a function`).

- [ ] **Step 3: Implementar en `registrar-cotizacion.js`**

3a) Agregar el mapa y la función, junto a los otros helpers:

```js
// La calculadora maneja Esencial/Pro/Experto; el campo planCarbonbox del CRM tiene
// ESENCIAL/PRO/PREMIUM/ENTERPRISE/LICITACION. Experto se guarda como PREMIUM.
const PLAN_A_CODIGO = { esencial: "ESENCIAL", pro: "PRO", experto: "PREMIUM" };

function planACodigo(plan) {
  if (!plan) return null;
  return PLAN_A_CODIGO[String(plan).trim().toLowerCase()] || null;
}
```

3b) Cambiar `moverAPropuestaEnviada` para que acepte y escriba los campos nuevos:

```js
async function moverAPropuestaEnviada(oppId, precio, extras = {}) {
  const data = { stage: "PROPUESTA_ENVIADA" };
  if (precio) data.amount = { amountMicros: Math.round(precio * 1_000_000), currencyCode: "USD" };
  const codigo = planACodigo(extras.plan);
  if (codigo) data.planCarbonbox = codigo;
  if (extras.linkCotizacion) {
    data.linkCotizacion = { primaryLinkUrl: extras.linkCotizacion, primaryLinkLabel: "Cotización" };
  }
  if (extras.borrador) data.borradorCorreo = extras.borrador;
  await gql(`mutation($id: UUID!, $data: OpportunityUpdateInput!) {
      updateOpportunity(id:$id, data:$data) { id } }`, { id: oppId, data });
}
```

3c) En `registrarCotizacion`, pasar los extras (y también al crear una oportunidad nueva,
llamando a `moverAPropuestaEnviada` justo después de crearla):

```js
async function registrarCotizacion({ cliente, nit, plan, precio, servicio, nota, linkCotizacion, borrador }) {
  const companyId = await findOrCreateCompany(cliente, nit);
  const existente = await findOpenOpportunity(companyId);
  const extras = { plan, linkCotizacion, borrador };

  let oppId, accion;
  if (existente) {
    oppId = existente.id;
    await moverAPropuestaEnviada(oppId, precio, extras);
    accion = `Oportunidad existente actualizada → Propuesta enviada (${existente.name})`;
  } else {
    oppId = await crearOportunidad(companyId, cliente, servicio, precio);
    await moverAPropuestaEnviada(oppId, precio, extras);
    accion = "Oportunidad nueva creada en Propuesta enviada";
  }
  // …(el bloque de la nota se queda igual)…
```

3d) En `main`, leer los flags nuevos (el borrador se lee de archivo):

```js
  let borrador;
  if (args["borrador-archivo"]) borrador = fs.readFileSync(args["borrador-archivo"], "utf8");
```
y pasar `linkCotizacion: args["link-cotizacion"], borrador` al llamar a `registrarCotizacion`.

3e) Exportar para los tests, al final del archivo:

```js
module.exports = { planACodigo, registrarCotizacion };
```
(si ya hay un `module.exports`, agregar `planACodigo` a lo exportado en vez de duplicarlo).

- [ ] **Step 4: Correr y ver pasar**

```bash
cd "C:/Users/USUARIO/Claude/Projects/carbonbox-crm/tools/cotizar" && node --test "Generadores/test/*.test.js"
```
Esperado: todos PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/cotizar/Generadores/registrar-cotizacion.js tools/cotizar/Generadores/test/registrar-cotizacion.test.js
git commit -m "feat(cotizar): registrar plan, link del deck y borrador de correo en el CRM"
```

---

### Task 3: CC y remitentes en el envío por Gmail

**Files:**
- Modify: `vps/crm-scripts/seguimiento.py`
- Test: `vps/crm-scripts/test_seguimiento.py`

**Interfaces:**
- Produces:
  - `REMITENTES` — dict `clave -> "Nombre <correo>"` con viviana/laura/alejandra/miguel.
  - `enviar_gmail(access_token, para, asunto, html, texto="", remitente=REMITENTE, cc=None)`
    ahora devuelve el **dict** de la API (`{"id", "threadId"}`), no solo el id.
  - `parse_cc(texto) -> list[str]` — separa por coma/punto y coma/espacio y descarta lo que no
    parezca correo.
  - `permalink_gmail(thread_id) -> str`.

- [ ] **Step 1: Escribir el test** (agregar a `test_seguimiento.py`)

```python
class TestRemitentesYCC(unittest.TestCase):
    def test_remitentes_son_los_cuatro(self):
        self.assertEqual(set(s.REMITENTES), {"viviana", "laura", "alejandra", "miguel"})
        self.assertIn("viviana.bohorquez@carbonbox.app", s.REMITENTES["viviana"])
        self.assertIn("Laura", s.REMITENTES["laura"])

    def test_parse_cc_separa_y_limpia(self):
        self.assertEqual(s.parse_cc("a@x.co, b@y.co;c@z.co"), ["a@x.co", "b@y.co", "c@z.co"])
        self.assertEqual(s.parse_cc("  a@x.co  "), ["a@x.co"])
        self.assertEqual(s.parse_cc(""), [])
        self.assertEqual(s.parse_cc(None), [])

    def test_parse_cc_descarta_lo_que_no_es_correo(self):
        self.assertEqual(s.parse_cc("a@x.co, basura, b@y.co"), ["a@x.co", "b@y.co"])

    def test_permalink(self):
        self.assertEqual(s.permalink_gmail("abc123"),
                         "https://mail.google.com/mail/u/0/#all/abc123")
```

- [ ] **Step 2: Correr y ver fallar**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest test_seguimiento.TestRemitentesYCC -v'
```
Esperado: FAIL (`module 'seguimiento' has no attribute 'REMITENTES'`).

- [ ] **Step 3: Implementar en `seguimiento.py`**

3a) Junto a `REMITENTE`, agregar:

```python
# Remitentes válidos: son send-as verificados sobre info@carbonbox.app, así que el
# sistema puede enviar como cualquiera de ellos. La página deja elegir cuál firma.
REMITENTES = {
    "viviana": "Viviana Bohórquez <viviana.bohorquez@carbonbox.app>",
    "laura": "Laura Bautista <laura.bautista@carbonbox.app>",
    "alejandra": "Alejandra Rojas <alejandra.rojas@carbonbox.app>",
    "miguel": "Miguel Romero <miguel.romero@carbonbox.app>",
}


def parse_cc(texto):
    """Lista de correos a partir de un campo libre (coma, punto y coma o espacio)."""
    if not texto:
        return []
    crudos = re.split(r"[,;\s]+", texto.strip())
    return [c for c in crudos if "@" in c and "." in c.split("@")[-1]]


def permalink_gmail(thread_id):
    return f"https://mail.google.com/mail/u/0/#all/{thread_id}"
```
(`re` ya está importado en el módulo; si no, agregarlo al import de arriba.)

3b) Cambiar `enviar_gmail` para aceptar CC y devolver el dict completo:

```python
def enviar_gmail(access_token, para, asunto, html, texto="", remitente=REMITENTE, cc=None):
    """Envía un correo (HTML + texto plano) por la Gmail API.
    Devuelve el dict de la API: {"id": ..., "threadId": ...}.
    Usa EmailMessage para codificar bien las cabeceras con acentos (si no, Gmail
    ignora el alias del remitente y cae al correo por defecto)."""
    msg = EmailMessage()
    msg["To"] = para
    if cc:
        msg["Cc"] = ", ".join(cc) if isinstance(cc, (list, tuple)) else cc
    msg["From"] = remitente
    msg["Subject"] = asunto
    msg.set_content(texto or "Abre este correo en un cliente que muestre HTML.")
    msg.add_alternative(html, subtype="html")
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    body = json.dumps({"raw": raw}).encode()
    req = urllib.request.Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        data=body, headers={"Authorization": f"Bearer {access_token}",
                            "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)
```

- [ ] **Step 4: Correr toda la suite y ver pasar**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest test_crm_lib test_reporte test_seguimiento 2>&1 | tail -3'
```
Esperado: OK. (El único consumidor de `enviar_gmail` es `intake_server._seguimiento_enviar`,
que ignora el valor devuelto, así que el cambio de retorno no rompe nada.)

- [ ] **Step 5: Commit** (espejo local + repo)

```bash
git add vps/crm-scripts/seguimiento.py vps/crm-scripts/test_seguimiento.py
git commit -m "feat(seguimiento): enviar_gmail acepta CC y devuelve threadId; remitentes del equipo"
```

---

### Task 4: Módulo `cotizacion.py` — datos, asunto y página

**Files:**
- Create: `vps/crm-scripts/cotizacion.py`
- Test: `vps/crm-scripts/test_cotizacion.py`

**Interfaces:**
- Consumes: de `seguimiento`: `firmar`, `valida`, `secreto`, `_esc`, `_pagina`, `REMITENTES`,
  `parse_cc`, `permalink_gmail`, `enviar_gmail`, `cuerpo_email_html`. De `crm_lib`: `gql`.
- Produces:
  - `asunto_cotizacion(empresa) -> str`
  - `cargar_opp_cotizacion(opp_id) -> dict|None` (name, stage, borradorCorreo, link del deck,
    company.name, contacto)
  - `datos_cotizacion(opp) -> (nombre, para, empresa, link_deck, borrador)`
  - `pagina_cotizacion(opp_id, sig, nombre, para, empresa, asunto, cuerpo, link_deck) -> str`
  - `registrar_envio_cotizacion(opp_id, permalink)` — escribe `linkCorreoEnviado`, limpia
    `borradorCorreo` y agrega una nota.

- [ ] **Step 1: Escribir el test** (crear `test_cotizacion.py`)

```python
import unittest
import cotizacion as c


OPP = {
    "id": "o1", "name": "HC Organizacional - ACME", "stage": "PROPUESTA_ENVIADA",
    "borradorCorreo": "Hola Ana, te comparto la cotización.",
    "linkCotizacion": {"primaryLinkUrl": "https://drive.google.com/file/d/XYZ/view"},
    "company": {"name": "ACME"},
    "pointOfContact": {"name": {"firstName": "Ana"}, "emails": {"primaryEmail": "ana@acme.co"}},
}


class TestAsunto(unittest.TestCase):
    def test_asunto_estandar(self):
        self.assertEqual(c.asunto_cotizacion("ACME"), "Cotización CarbonBox — ACME")


class TestDatos(unittest.TestCase):
    def test_extrae_todo(self):
        nombre, para, empresa, link, borrador = c.datos_cotizacion(OPP)
        self.assertEqual((nombre, para, empresa), ("Ana", "ana@acme.co", "ACME"))
        self.assertIn("XYZ", link)
        self.assertIn("cotización", borrador)

    def test_sin_contacto_ni_link(self):
        nombre, para, empresa, link, borrador = c.datos_cotizacion(
            {"name": "X", "company": None, "pointOfContact": None,
             "linkCotizacion": None, "borradorCorreo": None})
        self.assertEqual((nombre, para, empresa, link, borrador), ("", "", "", "", ""))


class TestPagina(unittest.TestCase):
    def test_trae_los_campos(self):
        h = c.pagina_cotizacion("o1", "sig123", "Ana", "ana@acme.co", "ACME",
                                "Cotización CarbonBox — ACME", "Hola Ana", "https://drive/x")
        self.assertIn("ana@acme.co", h)
        self.assertIn("name=cc", h)                  # campo de copia
        self.assertIn("name=remitente", h)           # selector de remitente
        self.assertIn("name=asunto", h)
        self.assertIn("<textarea", h)
        self.assertIn("Confirmar y enviar", h)
        for k in ("viviana", "laura", "alejandra", "miguel"):
            self.assertIn(k, h)

    def test_escapa_html(self):
        h = c.pagina_cotizacion("o1", "s", "A", "a@x.co", "<b>ACME</b>", "asunto", "cuerpo", "u")
        self.assertNotIn("<b>ACME</b>", h)
        self.assertIn("&lt;b&gt;ACME&lt;/b&gt;", h)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Correr y ver fallar**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest test_cotizacion -v'
```
Esperado: FAIL (`No module named 'cotizacion'`).

- [ ] **Step 3: Implementar `cotizacion.py`**

```python
#!/usr/bin/env python3
"""Envío de la cotización al cliente desde una página de confirmación.
Reusa la mecánica de seguimiento.py (firma HMAC, envío por Gmail, páginas)."""
from seguimiento import _esc, _pagina, REMITENTES

ASUNTO_BASE = "Cotización CarbonBox"


def asunto_cotizacion(empresa):
    return f"{ASUNTO_BASE} — {empresa}"


def cargar_opp_cotizacion(opp_id):
    from crm_lib import gql
    q = ("query($id: UUID!){ opportunities(first:1, filter:{id:{eq:$id}}) { edges { node { "
         "id name stage borradorCorreo "
         "linkCotizacion { primaryLinkUrl } "
         "pointOfContact { name { firstName } emails { primaryEmail } } "
         "company { name } } } } }")
    edges = gql(q, {"id": opp_id})["opportunities"]["edges"]
    return edges[0]["node"] if edges else None


def datos_cotizacion(opp):
    """(nombre, para, empresa, link_deck, borrador) — cadenas vacías si falta algo."""
    poc = opp.get("pointOfContact") or {}
    nombre = ((poc.get("name") or {}).get("firstName") or "").strip()
    para = ((poc.get("emails") or {}).get("primaryEmail") or "").strip()
    empresa = ((opp.get("company") or {}).get("name") or "").strip()
    link = ((opp.get("linkCotizacion") or {}).get("primaryLinkUrl") or "").strip()
    borrador = (opp.get("borradorCorreo") or "").strip()
    return nombre, para, empresa, link, borrador


def pagina_cotizacion(opp_id, sig, nombre, para, empresa, asunto, cuerpo, link_deck):
    inp = ("width:100%;padding:9px;margin:4px 0 12px;border:1px solid #d3d6f0;"
           "border-radius:8px;font-size:14px;font-family:inherit")
    opciones = "".join(
        f'<option value="{k}">{_esc(v)}</option>' for k, v in REMITENTES.items())
    c = ("<h1>Enviar cotización</h1>"
         f"<p class=muted>Para: <b>{_esc(nombre)}</b> &lt;{_esc(para)}&gt; · "
         f"Empresa: <b>{_esc(empresa)}</b></p>"
         f"<p class=muted>Deck: <a href=\"{_esc(link_deck)}\">{_esc(link_deck)}</a></p>"
         "<form method=post action=\"/cotizacion/enviar\">"
         f"<input type=hidden name=opp value=\"{_esc(opp_id)}\">"
         f"<input type=hidden name=sig value=\"{_esc(sig)}\">"
         "<label class=muted>Enviar como</label>"
         f"<select name=remitente style=\"{inp}\">{opciones}</select>"
         "<label class=muted>Copia (CC) — separa con comas; opcional</label>"
         f"<input name=cc value=\"\" placeholder=\"otro@empresa.com, jefe@empresa.com\" style=\"{inp}\">"
         "<label class=muted>Asunto</label>"
         f"<input name=asunto value=\"{_esc(asunto)}\" style=\"{inp}\">"
         "<label class=muted>Mensaje — puedes editarlo antes de enviar</label>"
         f"<textarea name=cuerpo rows=10 style=\"{inp}\">{_esc(cuerpo)}</textarea>"
         "<div class=muted style=\"margin:0 0 14px\">Se firma automáticamente con la firma de "
         "CarbonBox. El link del deck va dentro del mensaje.</div>"
         "<button type=submit>Confirmar y enviar</button>"
         "<div class=muted style=\"margin-top:10px\">El correo solo se envía al presionar este botón.</div>"
         "</form>")
    return _pagina("Enviar cotización", c)


def registrar_envio_cotizacion(opp_id, permalink):
    from crm_lib import gql
    gql("mutation($id: UUID!, $d: OpportunityUpdateInput!){ updateOpportunity(id:$id, data:$d){ id } }",
        {"id": opp_id, "d": {"linkCorreoEnviado": {"primaryLinkUrl": permalink,
                                                   "primaryLinkLabel": "Correo enviado"},
                             "borradorCorreo": ""}})
    d = gql("mutation($data: NoteCreateInput!){ createNote(data:$data){ id } }",
            {"data": {"title": "📤 Cotización enviada",
                      "bodyV2": {"markdown": f"Se envió la cotización al cliente.\n\n[Ver el correo]({permalink})"}}})
    gql("mutation($data: NoteTargetCreateInput!){ createNoteTarget(data:$data){ id } }",
        {"data": {"noteId": d["createNote"]["id"], "targetOpportunityId": opp_id}})
```

- [ ] **Step 4: Correr y ver pasar**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest test_cotizacion -v'
```
Esperado: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add vps/crm-scripts/cotizacion.py vps/crm-scripts/test_cotizacion.py
git commit -m "feat(cotizacion): modulo de pagina de confirmacion y registro del envio"
```

---

### Task 5: Endpoints `/cotizacion` en `intake_server.py`

**Files:**
- Modify: `vps/crm-scripts/intake_server.py`

**Interfaces:**
- Consumes: `cotizacion` (Task 4), `seguimiento` (Task 3), `crm_lib.google_access_token`.

- [ ] **Step 1: Importar el módulo** (junto a `import seguimiento as seg`)

```python
import cotizacion as cot
```

- [ ] **Step 2: Añadir el GET** — dentro de `do_GET`, antes del `return` de "No encontrado",
cambiar el enrutado para atender ambas rutas:

```python
    def do_GET(self):
        p = urlparse(self.path)
        ruta = p.path.rstrip("/")
        if ruta == "/seguimiento":
            return self._get_seguimiento(p)
        if ruta == "/cotizacion":
            return self._get_cotizacion(p)
        return self._html(404, seg.pagina_mensaje("No encontrado", "Página no encontrada."))
```
y mover el cuerpo actual de `do_GET` a un método `_get_seguimiento(self, p)` (mismo código,
sin cambios). Luego agregar:

```python
    def _get_cotizacion(self, p):
        q = parse_qs(p.query)
        opp_id = (q.get("opp") or [""])[0]
        sig = (q.get("sig") or [""])[0]
        if not seg.valida(opp_id, sig, seg.secreto()):
            return self._html(403, seg.pagina_mensaje("Enlace inválido",
                "Este enlace no es válido.", tono="error"))
        try:
            opp = cot.cargar_opp_cotizacion(opp_id)
        except Exception as ex:
            print(f"[cotizacion] error cargar: {ex}", flush=True)
            return self._html(500, seg.pagina_mensaje("Error", "No se pudo cargar el negocio.", tono="error"))
        if not opp:
            return self._html(404, seg.pagina_mensaje("No encontrado", "El negocio ya no existe."))
        nombre, para, empresa, link, borrador = cot.datos_cotizacion(opp)
        if not para:
            return self._html(400, seg.pagina_mensaje("Sin contacto",
                "Este negocio no tiene un contacto con correo en el CRM.", tono="error"))
        if not link:
            return self._html(400, seg.pagina_mensaje("Sin deck",
                "La oportunidad no tiene el link de la cotización. Corre /cotizar primero.", tono="error"))
        return self._html(200, cot.pagina_cotizacion(
            opp_id, sig, nombre, para, empresa, cot.asunto_cotizacion(empresa), borrador, link))
```

- [ ] **Step 3: Añadir el POST** — en `do_POST`, agregar la ruta antes del chequeo de `/intake`:

```python
        if self.path.rstrip("/") == "/cotizacion/enviar":
            return self._cotizacion_enviar()
```
y el método:

```python
    def _cotizacion_enviar(self):
        n = int(self.headers.get("Content-Length") or 0)
        form = parse_qs(self.rfile.read(n).decode("utf-8"))
        g = lambda k: (form.get(k) or [""])[0].strip()
        opp_id, sig = g("opp"), g("sig")
        if not seg.valida(opp_id, sig, seg.secreto()):
            return self._html(403, seg.pagina_mensaje("Enlace inválido", "Enlace no válido.", tono="error"))
        try:
            opp = cot.cargar_opp_cotizacion(opp_id)
            nombre, para, empresa, link, borrador = cot.datos_cotizacion(opp)
            if not para:
                return self._html(400, seg.pagina_mensaje("Sin contacto", "Sin correo del contacto.", tono="error"))
            asunto = g("asunto") or cot.asunto_cotizacion(empresa)
            cuerpo = g("cuerpo") or borrador
            remitente = seg.REMITENTES.get(g("remitente"), seg.REMITENTE)
            cc = seg.parse_cc(g("cc"))
            r = seg.enviar_gmail(google_access_token(), para, asunto,
                                 seg.cuerpo_email_html(cuerpo), texto=cuerpo,
                                 remitente=remitente, cc=cc)
            permalink = seg.permalink_gmail(r.get("threadId", ""))
            cot.registrar_envio_cotizacion(opp_id, permalink)
            print(f"[cotizacion] enviada a {para} cc={cc} ({opp['name']})", flush=True)
            copia = f" (con copia a {', '.join(cc)})" if cc else ""
            return self._html(200, seg.pagina_mensaje("✅ Cotización enviada",
                f"Se envió a {nombre} ({para}){copia} y quedó registrada en el negocio.", tono="ok"))
        except Exception as ex:
            print(f"[cotizacion] error envio: {ex}", flush=True)
            print(traceback.format_exc(), flush=True)
            return self._html(500, seg.pagina_mensaje("Error", "No se pudo enviar la cotización.", tono="error"))
```

- [ ] **Step 4: Verificar que importa y reiniciar**

```bash
cd "C:/Users/USUARIO/Claude/Projects/CRM CarbonBox/vps/crm-scripts" && for f in seguimiento.py cotizacion.py test_cotizacion.py test_seguimiento.py intake_server.py; do scp -i ~/.ssh/hostinger_vps "$f" root@72.60.125.170:/root/crm-scripts/; done
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -c "import intake_server; print(\"IMPORT OK\")" && systemctl restart carbonbox-intake && systemctl is-active carbonbox-intake'
```
Esperado: `IMPORT OK` y `active`.

---

### Task 6: Ruta `/cotizacion*` en Caddy

**Files:**
- Modify: `/etc/caddy/Caddyfile` (VPS) y su copia `deploy/Caddyfile` en el repo.

- [ ] **Step 1: Agregar el bloque** dentro de `crm.carbonbox.app`, junto al de `/seguimiento`

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'python3 -c "
import shutil
p=\"/etc/caddy/Caddyfile\"; s=open(p).read()
old=\"\thandle /seguimiento* {\n\t\treverse_proxy 127.0.0.1:8088\n\t}\"
new=old+\"\n\thandle /cotizacion* {\n\t\treverse_proxy 127.0.0.1:8088\n\t}\"
if \"handle /cotizacion*\" in s: print(\"ya existe\")
elif old in s:
    shutil.copy(p, p+\".bak.cotizacion\"); open(p,\"w\").write(s.replace(old,new,1)); print(\"agregado\")
else: print(\"NO ENCONTRE el bloque de seguimiento\"); print(repr(s[:400]))
" && caddy validate --config /etc/caddy/Caddyfile 2>&1 | tail -1 && systemctl reload caddy && echo "caddy recargado"'
```
Esperado: `agregado`, `Valid configuration`, `caddy recargado`.

---

### Task 7: La skill — Drive y el cierre del ciclo

**Files:**
- Modify: `tools/cotizar/.claude/skills/cotizar/SKILL.md`

Es documentación (la ejecuta Claude en Cowork con las herramientas de Drive), no código.

- [ ] **Step 1: Reemplazar el paso 8** ("Write-back al CRM = Etapa 2 (no lo hace este skill
todavía)…") por el cierre real del ciclo:

````markdown
8. **Cerrar el ciclo: Drive → CRM → correo.**

   **8.1 Subir el deck a Drive.** Los entregables de clientes viven en la carpeta **`Leads`**
   (`13dvWmMahnoyl_xsAZohAGVHoA8vIdX5A`), con **una subcarpeta por empresa**.
   - Busca la subcarpeta comparando **normalizado** (minúsculas, sin tildes ni puntuación):
     las carpetas no coinciden literal con el CRM ("Fundacion Santa Fe de Bogota" ↔
     "Fundación Santafé de Bogotá").
   - **Si hay exactamente una, úsala. Si hay 0 o más de 1, muéstrale las candidatas a Viviana
     y pregúntale cuál. NUNCA crees carpetas nuevas** — ya existe un duplicado
     ("Hotel Waya" y "Hotel Waya Guajira") y crear más empeora el problema.
   - Sube **los dos archivos**: el `.pdf` (lo que ve el cliente) y el `.pptx` (el editable).
   - Usa el Drive de Composio con la cuenta alias **`carbonbox`** (`info@carbonbox.app`),
     igual que para leer transcripciones.
   - **Revisa qué permiso quedó** en el link del PDF y dile a Viviana si el cliente no va a
     poder abrirlo. **No cambies permisos de compartición por tu cuenta.**

   **8.2 Redactar el correo** para ese cliente (usando el contexto de la reunión): saludo por
   su nombre, qué le estás enviando, el **link del deck**, validez de 60 días y cierre cálido.
   Guárdalo en un archivo temporal fuera del repo, p. ej. `Cotizaciones/<Cliente>/correo.txt`.

   **8.3 Escribir en el CRM:**
   ```bash
   node Generadores/registrar-cotizacion.js --cliente "…" --nit "…" --plan Pro --precio N \
     --link-cotizacion "<link del PDF>" --borrador-archivo "Cotizaciones/<Cliente>/correo.txt"
   ```
   Esto deja la oportunidad en "Propuesta enviada" con el monto, el plan, el link del deck y
   el borrador del correo.

   **8.4 Avisarle a Viviana que ya puede enviarla.** El link de la página va **firmado con el
   secreto del servidor**, así que la skill **no puede construirlo**. No lo intentes ni
   inventes una firma: en la siguiente pasada (máximo 3 h) el **Revisor de seguimientos** crea
   sola una tarea *"📤 Cotización lista para enviar"* con el link correcto, y también aparece
   en su correo de alertas. Dile a Viviana que la busque ahí.

   En esa página ella elige el remitente, agrega copias (CC) si hacen falta, revisa el texto
   y **solo ahí** se envía. Al enviar, el CRM guarda el link del correo.
````

- [ ] **Step 2: Commit**

```bash
git add tools/cotizar/.claude/skills/cotizar/SKILL.md
git commit -m "docs(cotizar): la skill cierra el ciclo (Drive, CRM y pagina de envio)"
```

---

### Task 7b: El Revisor avisa que la cotización está lista para enviar

El link de la página va firmado con el secreto del servidor, así que la skill no puede
construirlo. El Revisor —que sí tiene el secreto— crea la tarea con el link, igual que ya hace
con el recordatorio de agenda.

**Files:**
- Modify: `vps/crm-scripts/vigia_sla.py`

**Interfaces:**
- Consumes: `get_open_opportunities`, `find_open_task_by_title`, `create_urgent_task`,
  `firmar`, `secreto`.
- Produces: `revisar_cotizaciones_listas(ahora) -> list[str]`.

- [ ] **Step 1: Traer los campos nuevos en la consulta** — en `crm_lib.get_open_opportunities()`,
agregar `borradorCorreo` y `linkCorreoEnviado { primaryLinkUrl }` al bloque de campos:

```python
      edges { node { id name stage fechaEntradaEtapa createdAt updatedAt
        vencimientoContrato etapaLicitacion fechaCierreLicitacion
        borradorCorreo linkCorreoEnviado { primaryLinkUrl }
        amount { amountMicros } } } } }""")
```

- [ ] **Step 2: Agregar la función** en `vigia_sla.py` (después de `revisar_licitaciones`)

```python
def revisar_cotizaciones_listas(ahora):
    """Oportunidades con borrador de correo listo y sin correo enviado todavía:
    crea la tarea con el link de la página de confirmación (que va firmado con el
    secreto del servidor, por eso no lo puede armar la skill)."""
    nuevos = []
    sec = secreto()
    for opp in get_open_opportunities():
        if not (opp.get("borradorCorreo") or "").strip():
            continue
        if ((opp.get("linkCorreoEnviado") or {}).get("primaryLinkUrl") or "").strip():
            continue                      # ya se envió
        oid, nombre = opp["id"], opp["name"]
        title = f"📤 Cotización lista para enviar: {nombre}"
        if find_open_task_by_title(title):
            continue
        link = f"{CRM_URL}/cotizacion?opp={oid}&sig={firmar(oid, sec)}"
        create_urgent_task(
            title,
            f"La cotización de **{nombre}** ya está en Drive y registrada en el CRM.\n\n"
            f"**Acción:** revisa y envíala desde aquí:\n[Abrir y enviar la cotización]({link})\n\n"
            "En esa página eliges el remitente, agregas copias (CC) si hacen falta y revisas "
            "el texto. El correo solo sale al presionar el botón.",
            oid)
        nuevos.append(f"  • **{nombre}** — cotización lista para enviar.")
    return nuevos
```

- [ ] **Step 3: Engancharla al modo `sla`**

```python
    if modo in ("todo", "sla"):
        nuevos += revisar_sla(ahora)
        nuevos += revisar_agenda(ahora)
        nuevos += revisar_licitaciones(ahora)
        nuevos += revisar_cotizaciones_listas(ahora)
```

- [ ] **Step 4: Verificar que importa**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -c "import vigia_sla; print(\"IMPORT OK\")"'
```
Esperado: `IMPORT OK`. **No** correr `vigia_sla.py` aquí (crearía tareas reales; se prueba en
la Task 8 con el dato sembrado).

---

### Task 8: Verificación de punta a punta y push

- [ ] **Step 1: Suite completa en el VPS**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest test_crm_lib test_reporte test_seguimiento test_cotizacion test_gtasks_sync 2>&1 | tail -3'
```
Esperado: OK.

- [ ] **Step 2: Prueba de la página SIN enviar** — sembrar datos en una oportunidad de prueba
(no de un cliente real), abrir el GET y confirmar que la página trae todo:

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -c "
from crm_lib import gql
from seguimiento import firmar, secreto
# oportunidad de prueba: la primera en PROPUESTA_ENVIADA
o=gql(\"query{ opportunities(first:1, filter:{stage:{in:[\\\"PROPUESTA_ENVIADA\\\"]}}){edges{node{id name}}} }\")[\"opportunities\"][\"edges\"][0][\"node\"]
gql(\"mutation(\$id: UUID!, \$d: OpportunityUpdateInput!){ updateOpportunity(id:\$id, data:\$d){id} }\",
    {\"id\":o[\"id\"], \"d\":{\"borradorCorreo\":\"Hola, te comparto la cotizacion de prueba.\",
        \"linkCotizacion\":{\"primaryLinkUrl\":\"https://drive.google.com/file/d/PRUEBA/view\",\"primaryLinkLabel\":\"Cotización\"}}})
print(\"sembrado en:\", o[\"name\"])
print(f\"https://crm.carbonbox.app/cotizacion?opp={o[\"id\"]}&sig={firmar(o[\"id\"], secreto())}\")
" > /tmp/lk.txt; cat /tmp/lk.txt; curl -s "$(tail -1 /tmp/lk.txt)" | grep -oE "<h1>[^<]+</h1>|name=cc|name=remitente|name=asunto|<textarea|Confirmar y enviar" | head'
```
Esperado: la página con `<h1>Enviar cotización</h1>`, los campos `cc`, `remitente`, `asunto`,
el textarea y el botón. **No presionar el botón**: enviaría un correo real a ese cliente.

- [ ] **Step 3: Limpiar los datos de prueba**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -c "
from crm_lib import gql
import re
oid=open(\"/tmp/lk.txt\").read().split(\"opp=\")[1].split(\"&\")[0]
gql(\"mutation(\$id: UUID!, \$d: OpportunityUpdateInput!){ updateOpportunity(id:\$id, data:\$d){id} }\",
    {\"id\":oid, \"d\":{\"borradorCorreo\":\"\", \"linkCotizacion\":{\"primaryLinkUrl\":None,\"primaryLinkLabel\":None}}})
print(\"limpiado\", oid)
"'
```
Esperado: `limpiado <id>`.

> La prueba de **envío real** se hace con Viviana, sobre una cotización de verdad, para no
> mandarle un correo de prueba a un cliente.

- [ ] **Step 4: Push** (repo `carbonbox-crm` desde el clon local + espejo de los scripts)

```bash
cd "C:/Users/USUARIO/Claude/Projects/carbonbox-crm" && git add -A && git commit -m "feat(cotizar): write-back completo del ciclo de cotizacion" && git push origin main
```

---

## Notas de verificación
- `borradorCorreo` se limpia al enviar; si se genera una cotización y no se envía, queda el
  texto de esa vez y se sobrescribe en la siguiente corrida.
- El módulo `cotizacion.py` reusa `_pagina`/`_esc` de `seguimiento.py`: si cambia el diseño de
  las páginas, cambian las dos a la vez (es deseable, son el mismo tipo de página).
- Los scripts del servidor viven en `CRM CarbonBox/vps/crm-scripts/` (espejo) y se copian a
  `/root/crm-scripts/`; al pushear el repo, copiarlos también a `crm-scripts/` del repo.
