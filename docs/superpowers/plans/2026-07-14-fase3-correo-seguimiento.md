# Fase 3 — Correo de seguimiento con un clic — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development o executing-plans. Pasos con checkbox.

**Goal:** Que Viviana pueda enviar un recordatorio a un cliente estancado desde el reporte semanal, con un clic → página de confirmación → envío, respetando la regla de oro (nada se envía sin su confirmación).

**Architecture:** El reporte semanal agrega, por negocio estancado, un enlace firmado (HMAC) a `https://crm.carbonbox.app/seguimiento?opp=<id>&sig=<hmac>`. Caddy enruta `/seguimiento*` al `intake_server` (127.0.0.1:8088). El GET muestra una página de confirmación con el correo ya redactado; el POST envía por Gmail API (como Viviana) y registra en la oportunidad. Estado en el campo `ultimoSeguimiento`.

**Tech Stack:** Python stdlib (http.server, hmac, base64, email.mime), Gmail API (`gmail.send`, token de `info@carbonbox.app`), Twenty GraphQL + metadata API, Caddy.

## Decisiones (Viviana 2026-07-14)
- Remitente: **como Viviana** (viviana.bohorquez@carbonbox.app) con firma incrustada.
- Frecuencia: **máx. 1 recordatorio por semana** por negocio (bloquea si `ultimoSeguimiento` < 7 días).
- Botón: **solo en el reporte semanal**.

## Global Constraints
- Regla de oro: el correo al cliente SOLO se envía en el POST del botón "Confirmar y enviar". El GET solo muestra.
- Enlace firmado con HMAC-SHA256 (secreto en `/root/.seguimiento_secret`, 600) → no adivinable.
- Plantillas SOLO para `PROPUESTA_ENVIADA` y `EN_NEGOCIACION` (las etapas estancables). Otras etapas: sin enlace.
- Firma de Viviana igual a la de la bienvenida (nombre, info@carbonbox.app, www.carbonbox.app, WhatsApp wa.me/573208675567).
- Tests en el VPS (no hay Python en el PC). Gmail se prueba primero a info@carbonbox.app (interno), nunca a un cliente real en pruebas.

---

### Task 1: Campo `ultimoSeguimiento` en Opportunity

- [ ] **Step 1: Crear el campo (metadata API)**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -c "
import urllib.request, json
from crm_lib import token
def meta(q, v=None):
    body=json.dumps({\"query\":q,\"variables\":v or {}}).encode()
    r=urllib.request.Request(\"http://localhost:3000/metadata\", body, {\"Authorization\":f\"Bearer {token()}\",\"Content-Type\":\"application/json\"})
    return json.load(urllib.request.urlopen(r, timeout=90))
print(meta(\"\"\"mutation { createOneField(input:{field:{
  name:\\\"ultimoSeguimiento\\\", label:\\\"Último seguimiento\\\", type:DATE_TIME,
  objectMetadataId:\\\"172aabee-...\\\"}}) { id name } }\"\"\"))
"'
```
> Confirmar antes el objectMetadataId real de Opportunity (memoria: `172aabee`) con una query `objects`. Usar DATE si existe; si no, DATE_TIME. Verificar por existencia (la migración puede exceder 30s pero completa).

- [ ] **Step 2: Verificar**

```bash
ssh ... 'cd /root/crm-scripts && python3 -c "from crm_lib import gql; print([e[\"node\"][\"ultimoSeguimiento\"] for e in gql(\"query{opportunities(first:1){edges{node{ultimoSeguimiento}}}}\")[\"opportunities\"][\"edges\"]])"'
```
Esperado: no error (campo existe, valor None).

---

### Task 2: `cuerpo_html` soporta enlaces `[texto](url)`

Para que el reporte muestre "Enviar recordatorio" como enlace y no como URL cruda.

- [ ] **Step 1: Test (añadir a test_crm_lib.py)**

```python
    def test_enlace_markdown(self):
        h = c.cuerpo_html("ver [Enviar recordatorio](https://x.co/s?a=1&b=2)")
        self.assertIn('<a href="https://x.co/s?a=1&amp;b=2">Enviar recordatorio</a>', h)
```

- [ ] **Step 2: Verlo fallar**, luego implementar en `cuerpo_html` (tras la conversión de negritas):

```python
    esc = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', esc)
```

- [ ] **Step 3: Correr test → PASS. Commit.**

---

### Task 3: Firma HMAC + plantillas (módulo `seguimiento.py`)

Funciones puras, testeables, sin efectos.

- [ ] **Step 1: Tests (crear `test_seguimiento.py`)**

```python
import unittest, seguimiento as s

class TestFirma(unittest.TestCase):
    def test_firma_y_valida(self):
        sig = s.firmar("opp-123", secreto="clave")
        self.assertTrue(s.valida("opp-123", sig, secreto="clave"))
        self.assertFalse(s.valida("opp-123", "malo", secreto="clave"))
        self.assertFalse(s.valida("otro", sig, secreto="clave"))

class TestPlantilla(unittest.TestCase):
    def test_propuesta(self):
        asunto, cuerpo = s.plantilla("PROPUESTA_ENVIADA", nombre="Ana", empresa="ACME", negocio="HC ACME")
        self.assertIn("Ana", cuerpo); self.assertIn("propuesta", cuerpo.lower())
    def test_etapa_sin_plantilla(self):
        self.assertIsNone(s.plantilla("CERRADO_GANADO", nombre="x", empresa="y", negocio="z"))
```

- [ ] **Step 2: Implementar `seguimiento.py`**

```python
import hmac, hashlib

FIRMA_VIVIANA = (
    '<br><br>—<br><b>Viviana Bohórquez</b><br>CarbonBox · '
    '<a href="mailto:info@carbonbox.app">info@carbonbox.app</a><br>'
    '<a href="https://www.carbonbox.app">www.carbonbox.app</a> · '
    '<a href="https://wa.me/573208675567">WhatsApp</a>')

PLANTILLAS = {
    "PROPUESTA_ENVIADA": (
        "Sobre la propuesta de CarbonBox",
        "Hola {nombre}, ¿alcanzaste a revisar la propuesta que te compartimos para "
        "{empresa}? Quedo atenta a cualquier duda o ajuste para ayudarte a avanzar."),
    "EN_NEGOCIACION": (
        "¿Cómo vamos con {negocio}?",
        "Hola {nombre}, ¿cómo vas con la decisión sobre {negocio}? Con gusto reviso "
        "contigo cualquier detalle o ajuste que necesites."),
}

def firmar(opp_id, secreto):
    return hmac.new(secreto.encode(), opp_id.encode(), hashlib.sha256).hexdigest()

def valida(opp_id, sig, secreto):
    return hmac.compare_digest(firmar(opp_id, secreto), sig or "")

def plantilla(stage, nombre, empresa, negocio):
    t = PLANTILLAS.get(stage)
    if not t:
        return None
    asunto, cuerpo = t
    ctx = {"nombre": nombre, "empresa": empresa, "negocio": negocio}
    return asunto.format(**ctx), cuerpo.format(**ctx)

def cuerpo_email_html(cuerpo_texto):
    return "<p>" + cuerpo_texto + "</p><p>Un abrazo,</p>" + FIRMA_VIVIANA
```

- [ ] **Step 3: Tests → PASS. Commit.**

---

### Task 4: Envío por Gmail API (`enviar_gmail` en seguimiento.py)

- [ ] **Step 1: Implementar** (usa `google_access_token` de crm_lib):

```python
import base64, json, urllib.request
from email.mime.text import MIMEText

def enviar_gmail(access_token, para, asunto, html):
    msg = MIMEText(html, "html", "utf-8")
    msg["To"] = para
    msg["From"] = "Viviana Bohórquez <viviana.bohorquez@carbonbox.app>"
    msg["Subject"] = asunto
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    body = json.dumps({"raw": raw}).encode()
    req = urllib.request.Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        data=body, headers={"Authorization": f"Bearer {access_token}",
                            "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r).get("id")
```

- [ ] **Step 2: Prueba de envío INTERNO** (a info@carbonbox.app, NO a un cliente):

```bash
ssh ... 'cd /root/crm-scripts && python3 -c "
from crm_lib import google_access_token
from seguimiento import enviar_gmail, cuerpo_email_html
mid = enviar_gmail(google_access_token(), \"info@carbonbox.app\", \"[PRUEBA] Seguimiento\", cuerpo_email_html(\"Hola, esto es una prueba del correo de seguimiento.\"))
print(\"enviado id:\", mid)
"'
```
Esperado: `enviado id: <...>`; llega a info@carbonbox.app como Viviana con firma. Si el alias From es rechazado, fallback: `From = info@carbonbox.app` y anotarlo.

---

### Task 5: Endpoints `/seguimiento` (GET confirmación) y `/seguimiento/enviar` (POST) en intake_server.py

**Consumes:** seguimiento (firma/plantilla/enviar), crm_lib (gql, google_access_token, now_utc).

- [ ] **Step 1: Query de la oportunidad + contacto** (helper en seguimiento.py o intake): `opportunity(filter id) { name stage ultimoSeguimiento pointOfContact { name{firstName} emails{primaryEmail} } company{name} }`. Verificar el schema real de Twenty antes.
- [ ] **Step 2: `do_GET`** para `/seguimiento`: validar sig → cargar opp → si `ultimoSeguimiento` < 7 días, página "ya enviado hace N días" (sin botón) → si no, página con el correo redactado + `<form method=post action="/seguimiento/enviar">` con opp+sig ocultos y botón "Confirmar y enviar".
- [ ] **Step 3: `do_POST`** para `/seguimiento/enviar`: validar sig → re-chequear 7 días → `enviar_gmail(...)` → set `ultimoSeguimiento=hoy` (updateOpportunity) + nota "✉️ Recordatorio enviado" → página "✅ Enviado".
- [ ] **Step 4: Rate limit** por IP ya existe (LIMITER); reutilizar para estos paths.
- [ ] **Step 5: Verificar import + reiniciar servicio**: `python3 -c "import intake_server"` → `systemctl restart carbonbox-intake`.

---

### Task 6: Caddy enruta `/seguimiento*`

- [ ] **Step 1: Agregar bloque** en el Caddyfile, dentro de `crm.carbonbox.app`, antes del `handle` por defecto:

```
	handle /seguimiento* {
		reverse_proxy 127.0.0.1:8088
	}
```

- [ ] **Step 2: Recargar Caddy**: `systemctl reload caddy` y verificar `curl -sI https://crm.carbonbox.app/seguimiento?opp=x&sig=y` → responde el intake (no Twenty).

---

### Task 7: El reporte semanal agrega el enlace por negocio estancado

- [ ] **Step 1:** `clasificar_riesgo` incluye `id` en cada item (para armar el enlace).
- [ ] **Step 2:** `construir_reporte(opps_all, opps_open, ahora, link_fn=None)`: si `link_fn` y la etapa tiene plantilla, agrega bajo el negocio: `    ✉️ [Enviar recordatorio]({link_fn(id)})`.
- [ ] **Step 3:** En `main`, `link_fn = lambda oid: f"{CRM_URL}/seguimiento?opp={oid}&sig={firmar(oid, SECRETO)}"` (solo para etapas con plantilla).
- [ ] **Step 4:** Tests del reporte con `link_fn` stub → el enlace aparece. Smoke test → correo a info@ con enlaces. Commit.

---

## Puntos a verificar en el build
- objectMetadataId real de Opportunity y tipo DATE vs DATE_TIME.
- Schema real de `pointOfContact` / `emails.primaryEmail` / `company.name` en esta versión de Twenty.
- Que Gmail acepte el From alias de Viviana (si no, fallback a info@ y avisar).
- Que Caddy haga match de `/seguimiento*` antes del handle por defecto.
