# Seguimiento de licitaciones por fechas — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development o superpowers:executing-plans. Los pasos usan checkbox (`- [ ]`).

**Goal:** Que el CRM vigile la fecha de cierre de las licitaciones abiertas y avise a los 15, 7, 3 y 1 días antes (más un aviso único si la fecha ya pasó y sigue abierta), y que las licitaciones tengan su propio bloque en el reporte semanal en vez de tratarse como negocios estancados.

**Architecture:** Dos campos nuevos en Opportunity (`etapaLicitacion`, `fechaCierreLicitacion`). La lógica de decisión va en funciones puras de `crm_lib.py` (probadas con `unittest`), y `vigia_sla.py` / `reporte_semanal.py` solo las consumen y hacen los efectos. Se reutiliza `hito_a_disparar` (el mismo mecanismo idempotente de las renovaciones), generalizándolo con un parámetro `hitos`.

**Tech Stack:** Python 3.12 (solo stdlib), GraphQL de Twenty (+ /metadata para campos y vistas), cron.

## Global Constraints

- Archivos: `/root/crm-scripts/{crm_lib,vigia_sla,reporte_semanal}.py` + tests. Espejo local en `vps/crm-scripts/`.
- Tests se corren **en el VPS** (no hay Python en el PC): `ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest ... -v'`.
- ⚠️ Las etiquetas de opciones SELECT en Twenty **no pueden contener comas**.
- ⚠️ Los campos DATE exigen valor `YYYY-MM-DD` (no ISO con hora).
- Etapas de licitación (value/label): `ESTUDIO_MERCADO`/"Estudio de mercado" · `ABIERTA`/"Abierta" · `EVALUACION`/"En evaluación" · `ADJUDICADA`/"Adjudicada" · `NO_ADJUDICADA`/"No adjudicada".
- Hitos de aviso: **15, 7, 3, 1** días antes del cierre. Vencido: **un solo aviso** (centinela `-1` en el estado).
- Estado en `/root/crm-scripts/licitacion_seen.json` (ya cubierto por `.gitignore` con `*_seen.json`).
- Opportunity objectMetadataId: `172aabee-dad7-4c72-a89d-251b9d7e97ae`.
- Vista "All Opportunities": `6e590282-8a7f-41e5-a34f-86b4b74eff21`.

---

### Task 1: Crear los dos campos en Opportunity

**Files:** ninguno (metadata API del CRM).

**Interfaces:**
- Produces: campos `etapaLicitacion` (SELECT) y `fechaCierreLicitacion` (DATE) en Opportunity.

- [ ] **Step 1: Crear ambos campos**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -c "
import urllib.request, json, uuid
from crm_lib import token
OPP=\"172aabee-dad7-4c72-a89d-251b9d7e97ae\"
def meta(q,v=None):
    b=json.dumps({\"query\":q,\"variables\":v or {}}).encode()
    r=urllib.request.Request(\"http://localhost:3000/metadata\", b, {\"Authorization\":f\"Bearer {token()}\",\"Content-Type\":\"application/json\"})
    o=json.load(urllib.request.urlopen(r,timeout=120))
    if o.get(\"errors\"): raise SystemExit(json.dumps(o[\"errors\"],ensure_ascii=False)[:400])
    return o[\"data\"]
E=[(\"ESTUDIO_MERCADO\",\"Estudio de mercado\",\"gray\"),(\"ABIERTA\",\"Abierta\",\"yellow\"),
   (\"EVALUACION\",\"En evaluación\",\"blue\"),(\"ADJUDICADA\",\"Adjudicada\",\"green\"),
   (\"NO_ADJUDICADA\",\"No adjudicada\",\"red\")]
opts=[{\"id\":str(uuid.uuid4()),\"value\":v,\"label\":l,\"color\":c,\"position\":i} for i,(v,l,c) in enumerate(E)]
r=meta(\"mutation(\$in: CreateOneFieldMetadataInput!){ createOneField(input:\$in){ id name } }\",
  {\"in\":{\"field\":{\"name\":\"etapaLicitacion\",\"label\":\"Etapa licitación\",\"type\":\"SELECT\",\"objectMetadataId\":OPP,\"icon\":\"IconGavel\",\"options\":opts}}})
print(\"etapaLicitacion:\", r[\"createOneField\"])
r=meta(\"mutation(\$in: CreateOneFieldMetadataInput!){ createOneField(input:\$in){ id name } }\",
  {\"in\":{\"field\":{\"name\":\"fechaCierreLicitacion\",\"label\":\"Fecha de cierre\",\"type\":\"DATE\",\"objectMetadataId\":OPP,\"icon\":\"IconCalendarEvent\"}}})
print(\"fechaCierreLicitacion:\", r[\"createOneField\"])
"'
```
Esperado: imprime los dos campos con su id.

- [ ] **Step 2: Verificar que se pueden consultar**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -c "
from crm_lib import gql
d=gql(\"query{ opportunities(first:1){edges{node{name etapaLicitacion fechaCierreLicitacion}}} }\")
print(d[\"opportunities\"][\"edges\"][0][\"node\"])
"'
```
Esperado: imprime el nodo con ambos campos en `None` (sin error).

---

### Task 2: `hito_a_disparar` generalizado con hitos configurables

**Files:**
- Modify: `vps/crm-scripts/crm_lib.py`
- Test: `vps/crm-scripts/test_crm_lib.py`

**Interfaces:**
- Produces: `hito_a_disparar(dias, ya_vistos, hitos=None)` — si `hitos` es None usa `HITOS` (renovación, `[90,60,30]`). Devuelve `(hito_o_None, lista_actualizada)`.

- [ ] **Step 1: Escribir el test** (agregar a `test_crm_lib.py`)

```python
class TestHitosConfigurables(unittest.TestCase):
    LIC = [15, 7, 3, 1]

    def test_renovacion_sigue_igual_sin_parametro(self):
        self.assertEqual(c.hito_a_disparar(90, []), (90, [90]))
        self.assertEqual(c.hito_a_disparar(59, [90]), (60, [90, 60]))

    def test_licitacion_dispara_15(self):
        self.assertEqual(c.hito_a_disparar(12, [], hitos=self.LIC), (15, [15]))

    def test_licitacion_no_repite(self):
        self.assertEqual(c.hito_a_disparar(10, [15], hitos=self.LIC), (None, [15]))

    def test_licitacion_dispara_7_luego_3(self):
        self.assertEqual(c.hito_a_disparar(5, [15], hitos=self.LIC), (7, [15, 7]))
        self.assertEqual(c.hito_a_disparar(2, [15, 7], hitos=self.LIC), (3, [15, 7, 3]))

    def test_licitacion_lejos_resetea(self):
        self.assertEqual(c.hito_a_disparar(40, [15, 7], hitos=self.LIC), (None, []))
```

- [ ] **Step 2: Correr y ver fallar**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest test_crm_lib.TestHitosConfigurables -v'
```
Esperado: FAIL (`hito_a_disparar() got an unexpected keyword argument 'hitos'`).

- [ ] **Step 3: Implementar** — en `crm_lib.py`, cambiar la firma y la primera línea del cuerpo:

```python
def hito_a_disparar(dias, ya_vistos, hitos=None):
    """Decide si hoy toca avisar de un hito para algo que ocurre en `dias` días,
    dados los hitos ya avisados `ya_vistos`.

    `hitos` por defecto son los de renovación (HITOS = [90, 60, 30]); las licitaciones
    pasan [15, 7, 3, 1]. Devuelve (hito_o_None, lista_actualizada_de_vistos).
    - Dispara SOLO el hito más urgente ya alcanzado, una única vez por hito.
    - Fuera de ventana (dias > el hito mayor) resetea: se re-arma para el próximo ciclo."""
    hitos = HITOS if hitos is None else hitos
    vistos = [int(x) for x in ya_vistos]
    alcanzados = [h for h in hitos if dias <= h]
    if not alcanzados:
        return None, []
    nuevos = sorted(set(vistos) | set(alcanzados), reverse=True)
    target = min(alcanzados)
    if target in vistos:
        return None, nuevos
    return target, nuevos
```

- [ ] **Step 4: Correr y ver pasar**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest test_crm_lib -v 2>&1 | tail -3'
```
Esperado: OK (incluye los tests viejos de renovación, sin regresión).

---

### Task 3: Detección por campo, consulta y clasificación de licitaciones

**Files:**
- Modify: `vps/crm-scripts/crm_lib.py`
- Test: `vps/crm-scripts/test_crm_lib.py`

**Interfaces:**
- Consumes: `hito_a_disparar` (Task 2), campos de Task 1.
- Produces:
  - `es_licitacion(opp)` — acepta el **dict** de la oportunidad (mira `etapaLicitacion`) o un **string** con el nombre (respaldo).
  - `get_open_opportunities()` ahora devuelve además `etapaLicitacion` y `fechaCierreLicitacion`.
  - `clasificar_riesgo(opps, ahora)` **excluye** licitaciones.
  - `clasificar_licitaciones(opps, hoy) -> (abiertas, evaluacion)`; cada abierta es
    `{"id","nombre","dias"(int|None),"fecha"("DD/MM"|None),"sin_fecha"(bool)}`; cada evaluación `{"nombre"}`.
  - `load_licitacion_seen()` / `save_licitacion_seen(d)`; `LICITACION_HITOS = [15, 7, 3, 1]`.

- [ ] **Step 1: Escribir los tests** (agregar a `test_crm_lib.py`)

```python
def _lic(nombre, etapa, dias_al_cierre=None, hoy=None):
    o = {"id": nombre, "name": nombre, "stage": "EN_NEGOCIACION",
         "fechaEntradaEtapa": (AHORA - timedelta(days=60)).isoformat(),
         "createdAt": (AHORA - timedelta(days=60)).isoformat(),
         "amount": {"amountMicros": 0}, "etapaLicitacion": etapa,
         "fechaCierreLicitacion": None}
    if dias_al_cierre is not None:
        o["fechaCierreLicitacion"] = (AHORA.date() + timedelta(days=dias_al_cierre)).isoformat()
    return o


class TestLicitacionCampo(unittest.TestCase):
    def test_detecta_por_campo(self):
        self.assertTrue(c.es_licitacion({"name": "Convenio X", "etapaLicitacion": "ABIERTA"}))
        self.assertFalse(c.es_licitacion({"name": "HC - ACME", "etapaLicitacion": None}))

    def test_respaldo_por_nombre(self):
        self.assertTrue(c.es_licitacion({"name": "Licitación - Banco", "etapaLicitacion": None}))
        self.assertTrue(c.es_licitacion("Licitación - Banco"))     # string suelto

    def test_riesgo_excluye_licitaciones(self):
        opps = [_lic("Licitación - Banco", "ABIERTA", 10),
                _opp("PROPUESTA_ENVIADA", "HC - ACME", 30)]
        _, est = c.clasificar_riesgo(opps, AHORA)
        self.assertEqual([e["nombre"] for e in est], ["HC - ACME"])

    def test_clasificar_licitaciones(self):
        opps = [_lic("Lic A", "ABIERTA", 12), _lic("Lic B", "ABIERTA", 3),
                _lic("Lic C", "ABIERTA"), _lic("Lic D", "EVALUACION"),
                _lic("Lic E", "ADJUDICADA", 5)]
        ab, ev = c.clasificar_licitaciones(opps, AHORA.date())
        self.assertEqual([x["nombre"] for x in ab], ["Lic B", "Lic A", "Lic C"])  # más urgente primero, sin fecha al final
        self.assertEqual(ab[0]["dias"], 3)
        self.assertTrue(ab[2]["sin_fecha"])
        self.assertEqual([x["nombre"] for x in ev], ["Lic D"])
```

- [ ] **Step 2: Correr y ver fallar**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest test_crm_lib.TestLicitacionCampo -v'
```
Esperado: FAIL (`has no attribute 'clasificar_licitaciones'`).

- [ ] **Step 3: Implementar en `crm_lib.py`**

3a) Agregar `date` al import de fecha (línea 4):

```python
from datetime import datetime, timezone, timedelta, date
```

3b) Reemplazar `es_licitacion` y borrar `ACCION_LICITACION` (ya no se usa: las licitaciones salen del bloque de estancados):

```python
def es_licitacion(opp):
    """True si la oportunidad es una licitación o estudio de mercado.
    Acepta el nodo completo (preferido: mira el campo etapaLicitacion) o solo el
    nombre (respaldo, para las que aún no se hayan marcado en el CRM)."""
    if isinstance(opp, dict):
        if opp.get("etapaLicitacion"):
            return True
        nombre = opp.get("name")
    else:
        nombre = opp
    n = (nombre or "").lower()
    return n.startswith("licitación") or n.startswith("licitacion") or "estudio de mercado" in n
```

3c) En `get_open_opportunities()`, agregar los dos campos a la query:

```python
def get_open_opportunities():
    d = gql("""query { opportunities(first: 200,
        filter: { stage: { in: ["LEAD_CAPTURADO", "CALIFICACION_BANT", "DEMO",
                                 "PILOTO_45D", "PROPUESTA_ENVIADA", "EN_NEGOCIACION",
                                 "RENOVACION"] } }) {
      edges { node { id name stage fechaEntradaEtapa createdAt updatedAt
        vencimientoContrato etapaLicitacion fechaCierreLicitacion
        amount { amountMicros } } } } }""")
    return [e["node"] for e in d["opportunities"]["edges"]]
```

3d) En `clasificar_riesgo`, excluir licitaciones y quitar el marcado anterior. El inicio del bucle queda:

```python
    for o in opps:
        if es_licitacion(o):
            continue                      # tienen su propio bloque y sus propias fechas
        etapa = ETAPAS.get(o["stage"])
        if not etapa or not etapa["sla"]:
            continue
```

y el `item` vuelve a la acción de la etapa (sin las claves `licitacion`/`ACCION_LICITACION`):

```python
        item = {
            "id": o["id"],
            "stage": o["stage"],
            "nombre": o["name"],
            "etapa": etapa["nombre"],
            "antiguedad": antiguedad_texto(entrada, ahora),
            "limite": etapa["sla_txt"],
            "valor": pesos(valor) if valor else "",
            "accion": etapa["accion"],
            "_orden": atraso,
        }
```

3e) Agregar al final de la sección de licitaciones:

```python
# --- Licitaciones: hitos de aviso y estado ---
LICITACION_HITOS = [15, 7, 3, 1]
LICITACION_SEEN_FILE = "/root/crm-scripts/licitacion_seen.json"
ETAPAS_LICITACION = {"ESTUDIO_MERCADO": "Estudio de mercado", "ABIERTA": "Abierta",
                     "EVALUACION": "En evaluación", "ADJUDICADA": "Adjudicada",
                     "NO_ADJUDICADA": "No adjudicada"}


def load_licitacion_seen():
    try:
        with open(LICITACION_SEEN_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_licitacion_seen(d):
    with open(LICITACION_SEEN_FILE, "w") as f:
        json.dump(d, f)


def fecha_cierre(opp):
    """date de fechaCierreLicitacion, o None."""
    f = opp.get("fechaCierreLicitacion")
    if not f:
        return None
    return date(int(f[:4]), int(f[5:7]), int(f[8:10]))


def clasificar_licitaciones(opps, hoy):
    """(abiertas, en_evaluacion) para el reporte. Abiertas ordenadas de la más
    urgente a la menos; las que no tienen fecha cargada van al final."""
    abiertas, evaluacion = [], []
    for o in opps:
        et = o.get("etapaLicitacion")
        if et == "ABIERTA":
            f = fecha_cierre(o)
            abiertas.append({
                "id": o["id"], "nombre": o["name"],
                "dias": (f - hoy).days if f else None,
                "fecha": f.strftime("%d/%m") if f else None,
                "sin_fecha": f is None,
            })
        elif et == "EVALUACION":
            evaluacion.append({"nombre": o["name"]})
    abiertas.sort(key=lambda x: (x["dias"] is None, x["dias"] if x["dias"] is not None else 0))
    return abiertas, evaluacion
```

- [ ] **Step 4: Actualizar los tests que asumían el comportamiento anterior**

En `test_crm_lib.py`, la clase `TestLicitacion` tenía `test_riesgo_marca_y_cambia_accion`, que ya no aplica (ahora se excluyen). Reemplazarla por:

```python
    def test_riesgo_ya_no_marca_sino_que_excluye(self):
        opps = [_opp("PROPUESTA_ENVIADA", "Licitación - Banco", 30),
                _opp("PROPUESTA_ENVIADA", "HC - ACME", 30)]
        _, est = c.clasificar_riesgo(opps, AHORA)
        self.assertEqual([e["nombre"] for e in est], ["HC - ACME"])
```

En `test_reporte.py`, `test_licitacion_sin_enlace_y_con_accion_tdr` ya no aplica igual: ahora la licitación no aparece entre estancados. Reemplazarla por:

```python
    def test_licitacion_no_aparece_en_estancados(self):
        allo = [_opp("PROPUESTA_ENVIADA", "Licitación - Banco Agrario", 30)]
        body = r.construir_reporte(allo, allo, AHORA, link_fn=lambda it: "https://x.co/s")
        self.assertNotIn("NEGOCIOS ESTANCADOS", body)
        self.assertNotIn("Enviar recordatorio", body)
```

- [ ] **Step 5: Correr toda la suite y ver pasar**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest test_crm_lib test_reporte test_seguimiento -v 2>&1 | tail -3'
```
Esperado: OK.

---

### Task 4: Alertas de cierre en el Revisor

**Files:**
- Modify: `vps/crm-scripts/vigia_sla.py`

**Interfaces:**
- Consumes: `get_open_opportunities`, `hito_a_disparar(..., hitos=)`, `LICITACION_HITOS`,
  `load_licitacion_seen`, `save_licitacion_seen`, `fecha_cierre`, `find_open_task_by_title`, `create_urgent_task`.
- Produces: `revisar_licitaciones(ahora) -> list[str]` (líneas para el correo resumen).

- [ ] **Step 1: Ampliar el import de `crm_lib` en `vigia_sla.py`**

```python
from crm_lib import (ETAPAS, nombre_etapa, antiguedad_texto, gql,
                     get_open_opportunities, get_renewal_candidates, get_leads,
                     find_open_task_by_title, create_urgent_task, send_notification,
                     now_utc, parse_dt, hito_a_disparar, load_renov_seen, save_renov_seen,
                     hito_agenda, load_agenda_seen, save_agenda_seen, google_access_token,
                     LICITACION_HITOS, load_licitacion_seen, save_licitacion_seen, fecha_cierre)
```

- [ ] **Step 2: Agregar `revisar_licitaciones`** (después de `revisar_renovacion`)

```python
def revisar_licitaciones(ahora):
    """Licitaciones ABIERTAS: avisa a los 15/7/3/1 días del cierre (una vez cada hito).
    Si la fecha ya pasó y sigue abierta, un único aviso para actualizar el estado.
    El centinela -1 en el estado marca 'vencido ya avisado'."""
    nuevos = []
    seen = load_licitacion_seen()
    vivos = set()
    hoy = ahora.date()
    for opp in get_open_opportunities():
        if opp.get("etapaLicitacion") != "ABIERTA":
            continue
        cierre = fecha_cierre(opp)
        if not cierre:
            continue                       # sin fecha no hay nada que vigilar (sale en el reporte)
        oid, nombre = opp["id"], opp["name"]
        vivos.add(oid)
        vistos = [int(x) for x in seen.get(oid, [])]
        dias = (cierre - hoy).days

        if dias < 0:
            if -1 not in vistos:
                title = f"⚠️ Pasó el cierre: {nombre}"
                if not find_open_task_by_title(title):
                    create_urgent_task(
                        title,
                        f"La fecha de cierre de **{nombre}** fue el "
                        f"**{cierre.strftime('%d/%m/%Y')}** (hace {-dias} días) y la licitación "
                        "sigue marcada como **Abierta**.\n\n"
                        "**Acción:** actualiza la etapa de licitación — ¿se entregó? → *En "
                        "evaluación*; ¿no se presentó? → *No adjudicada*.",
                        oid)
                    nuevos.append(f"  • **{nombre}** — pasó el cierre "
                                  f"({cierre.strftime('%d/%m')}); actualiza el estado.")
                vistos.append(-1)
            seen[oid] = sorted(set(vistos))
            continue

        hito, actualizados = hito_a_disparar(dias, [v for v in vistos if v >= 0],
                                             hitos=LICITACION_HITOS)
        seen[oid] = sorted(set(actualizados))
        if hito is None:
            continue
        title = f"📋 Cierre de licitación en {hito} días: {nombre}"
        if find_open_task_by_title(title):
            continue
        create_urgent_task(
            title,
            f"La licitación **{nombre}** cierra el **{cierre.strftime('%d/%m/%Y')}** "
            f"(faltan {dias} días).\n\n"
            "**Acción:** revisar los TDR y preparar la entrega de la propuesta.",
            oid)
        nuevos.append(f"  • **{nombre}** — cierra en {dias} días ({cierre.strftime('%d/%m')}).")
    seen = {k: v for k, v in seen.items() if k in vivos}
    save_licitacion_seen(seen)
    return nuevos
```

- [ ] **Step 3: Engancharlo al modo `sla`** (que es el que corre cada 3 h)

```python
    if modo in ("todo", "sla"):
        nuevos += revisar_sla(ahora)
        nuevos += revisar_agenda(ahora)
        nuevos += revisar_licitaciones(ahora)
```

- [ ] **Step 4: Verificar que importa (sin ejecutar efectos)**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -c "import vigia_sla; print(\"IMPORT OK\")"'
```
Esperado: `IMPORT OK`. **No** correr `vigia_sla.py` aquí: crearía tareas reales (se hace en la Task 7).

---

### Task 5: Bloque de licitaciones en el reporte semanal

**Files:**
- Modify: `vps/crm-scripts/reporte_semanal.py`
- Test: `vps/crm-scripts/test_reporte.py`

**Interfaces:**
- Consumes: `clasificar_licitaciones(opps, hoy)` (Task 3).

- [ ] **Step 1: Escribir el test** (agregar a `test_reporte.py`)

```python
    def test_bloque_licitaciones(self):
        d = (AHORA.date() + timedelta(days=4)).isoformat()
        lic = {"id": "L1", "name": "Licitación - Banco", "stage": "EN_NEGOCIACION",
               "fechaEntradaEtapa": (AHORA - timedelta(days=60)).isoformat(),
               "createdAt": (AHORA - timedelta(days=60)).isoformat(),
               "amount": {"amountMicros": 0},
               "etapaLicitacion": "ABIERTA", "fechaCierreLicitacion": d}
        ev = dict(lic, id="L2", name="Licitación - Alcaldía",
                  etapaLicitacion="EVALUACION", fechaCierreLicitacion=None)
        body = r.construir_reporte([lic, ev], [lic, ev], AHORA)
        self.assertIn("LICITACIONES", body)
        self.assertIn("cierra en 4 días", body)
        self.assertIn("En evaluación", body)
        self.assertIn("Licitación - Alcaldía", body)
```

- [ ] **Step 2: Correr y ver fallar**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest test_reporte.TestReporte.test_bloque_licitaciones -v'
```
Esperado: FAIL (`'LICITACIONES' not found`).

- [ ] **Step 3: Implementar** — en `reporte_semanal.py`, agregar `clasificar_licitaciones` al import de `crm_lib`:

```python
from crm_lib import (ETAPAS, nombre_etapa, pesos, clasificar_riesgo, clasificar_licitaciones,
                     get_all_opportunities, get_open_opportunities,
                     send_notification, now_utc)
```

y insertar el bloque **justo antes** de `── METAS DEL MES ──`:

```python
    abiertas, evaluacion = clasificar_licitaciones(opps_open, ahora.date())
    if abiertas or evaluacion:
        L += ["", f"**── 📋 LICITACIONES ({len(abiertas) + len(evaluacion)}) ──**"]
        if abiertas:
            L.append("Abiertas (ojo con la fecha de cierre):")
            for it in abiertas:
                if it["sin_fecha"]:
                    L.append(f"  • **{it['nombre']}** — ⚠️ sin fecha de cierre cargada")
                elif it["dias"] < 0:
                    L.append(f"  • **{it['nombre']}** — cerró hace {-it['dias']} días "
                             f"({it['fecha']}); actualiza el estado")
                else:
                    L.append(f"  • **{it['nombre']}** — cierra en {it['dias']} días ({it['fecha']})")
        if evaluacion:
            L.append("En evaluación (esperando resultado):")
            for it in evaluacion:
                L.append(f"  • **{it['nombre']}**")
```

- [ ] **Step 4: Correr toda la suite**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest test_crm_lib test_reporte test_seguimiento 2>&1 | tail -3'
```
Esperado: OK.

---

### Task 6: Columnas visibles en la vista de oportunidades

**Files:** ninguno (metadata API de vistas).

- [ ] **Step 1: Hacer visibles los dos campos en "All Opportunities"**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -c "
import urllib.request, json
from crm_lib import token
VIEW=\"6e590282-8a7f-41e5-a34f-86b4b74eff21\"; OPP=\"172aabee-dad7-4c72-a89d-251b9d7e97ae\"
def meta(q,v=None):
    b=json.dumps({\"query\":q,\"variables\":v or {}}).encode()
    r=urllib.request.Request(\"http://localhost:3000/metadata\", b, {\"Authorization\":f\"Bearer {token()}\",\"Content-Type\":\"application/json\"})
    o=json.load(urllib.request.urlopen(r,timeout=90))
    if o.get(\"errors\"): raise SystemExit(json.dumps(o[\"errors\"],ensure_ascii=False)[:400])
    return o[\"data\"]
f=meta(\"query(\$id: UUID!){ object(id:\$id){ fields(paging:{first:200}){edges{node{id name}}} } }\", {\"id\":OPP})
ids={e[\"node\"][\"name\"]: e[\"node\"][\"id\"] for e in f[\"object\"][\"fields\"][\"edges\"]}
vf=meta(\"query(\$v: String!){ getViewFields(viewId:\$v){ id fieldMetadataId isVisible position } }\", {\"v\":VIEW})[\"getViewFields\"]
pos=max((x[\"position\"] for x in vf if x[\"isVisible\"]), default=0)
for name in (\"etapaLicitacion\",\"fechaCierreLicitacion\"):
    fid=ids[name]
    mio=[x for x in vf if x[\"fieldMetadataId\"]==fid]
    if not mio: print(\"sin viewField:\", name); continue
    pos+=1
    r=meta(\"mutation(\$in: UpdateViewFieldInput!){ updateViewField(input:\$in){ id isVisible position } }\",
           {\"in\":{\"id\":mio[0][\"id\"],\"update\":{\"isVisible\":True,\"position\":pos}}})
    print(name, \"->\", r[\"updateViewField\"])
"'
```
Esperado: ambos con `isVisible: True`.

---

### Task 7: Despliegue, verificación en vivo y push

**Files:** despliegue + repo.

- [ ] **Step 1: Desplegar los scripts al VPS**

```bash
cd "C:/Users/USUARIO/Claude/Projects/CRM CarbonBox/vps/crm-scripts" && for f in crm_lib.py test_crm_lib.py reporte_semanal.py test_reporte.py vigia_sla.py; do scp -i ~/.ssh/hostinger_vps "$f" root@72.60.125.170:/root/crm-scripts/; done
```

- [ ] **Step 2: Suite completa sin regresión**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest test_crm_lib test_reporte test_seguimiento test_gtasks_sync 2>&1 | tail -3'
```
Esperado: OK.

- [ ] **Step 3: Marcar las 2 licitaciones existentes** — pedirle a Viviana el estado real de
  "Licitación - Banco Agrario de Colombia" y "Licitación :HC + Huella Hídrica - Superservicios"
  (¿En evaluación? ¿Abierta con nueva fecha?) y cargarlo desde el CRM. **No adivinar**: si están
  en evaluación no generan alertas; si se marcan Abiertas con fecha pasada, dispararán el aviso
  de "pasó el cierre".

- [ ] **Step 4: Dry-run del Revisor de licitaciones** (sin crear tareas)

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -c "
from crm_lib import get_open_opportunities, load_licitacion_seen, hito_a_disparar, LICITACION_HITOS, fecha_cierre, now_utc
hoy=now_utc().date(); seen=load_licitacion_seen()
for o in get_open_opportunities():
    if o.get(\"etapaLicitacion\") != \"ABIERTA\": continue
    f=fecha_cierre(o)
    if not f: print(f\"  {o[\"name\"]}: ABIERTA sin fecha\"); continue
    d=(f-hoy).days
    if d<0: print(f\"  {o[\"name\"]}: vencida hace {-d} d -> aviso de actualizar\")
    else:
        h,_=hito_a_disparar(d,[v for v in seen.get(o[\"id\"],[]) if v>=0],hitos=LICITACION_HITOS)
        print(f\"  {o[\"name\"]}: faltan {d} d -> {(\"tarea hito \"+str(h)) if h else \"nada aun\"}\")
"'
```
Esperado: refleja el estado real cargado en el Step 3; revisar que tenga sentido antes de activar.

- [ ] **Step 5: Corrida real del Revisor** (crea las tareas que corresponda)

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 vigia_sla.py sla'
```
Esperado: imprime `N alertas nuevas` o `sin novedades`, coherente con el dry-run.

- [ ] **Step 6: Reporte con el bloque nuevo**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 reporte_semanal.py 2>&1 | sed -n "/LICITACIONES/,/METAS/p"'
```
Esperado: se ve el bloque `📋 LICITACIONES` y las licitaciones ya **no** aparecen en "negocios estancados".

- [ ] **Step 7: Commit y push** (deploy key ya configurada en el VPS)

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /tmp/cbx-repo 2>/dev/null || git clone -q git@github.com:ViviBohoLo/carbonbox-crm.git /tmp/cbx-repo; cd /tmp/cbx-repo && git pull -q --ff-only; for f in /root/crm-scripts/*.py; do b=$(basename $f); [ "$b" = "test_gtasks_sync.py" ] && continue; cp "$f" crm-scripts/; done; git add -A && git -c user.name="CarbonBox Ops" -c user.email="info@carbonbox.app" commit -q -m "feat(licitaciones): seguimiento por fecha de cierre (avisos 15/7/3/1 y vencido)" && git push -q origin HEAD && git log -1 --format="%h %s"'
```

> ⚠️ Al copiar los `.py` al repo, **no** sobrescribir `test_gtasks_sync.py` (el del repo es más nuevo que el del VPS). El bucle ya lo excluye. Copiar también el spec y este plan desde el PC con `scp` antes de commitear.

---

## Notas de verificación
- El `.gitignore` ya cubre `licitacion_seen.json` con `*_seen.json`.
- Las licitaciones dejan de contar en "negocios estancados": el total de ese bloque bajará (hoy son 2 de 12).
- `es_licitacion` se usa también en `intake_server.py` (página "No aplica"); allí recibe el dict de `cargar_opp`, que **no** trae `etapaLicitacion` → seguirá funcionando por el respaldo del nombre. Si más adelante se quiere precisión, agregar `etapaLicitacion` a la query de `seguimiento.cargar_opp`.
