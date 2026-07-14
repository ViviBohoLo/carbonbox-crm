# Fase 2 — Redacción de alertas en los scripts del CRM — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Llevar a los scripts del VPS la redacción "completa y accionable" aprobada, con un único origen de SLAs/acciones, renombrar "Vigía SLA" → "Revisor de seguimientos", aplicar las frecuencias (Revisor cada 3 h / renovación diaria) y corregir los 5 bugs.

**Architecture:** Toda la lógica de decisión y de armado de texto se factoriza en **funciones puras** en `crm_lib.py` (probadas con `unittest`), y los scripts `reporte_semanal.py` / `vigia_sla.py` solo las llaman y hacen los efectos (GraphQL, email). Mismo patrón que `hito_a_disparar` y `plan_sync`.

**Tech Stack:** Python 3.12 (solo stdlib), GraphQL de Twenty, cron. **No hay Python en el PC** → los tests se corren en el VPS por ssh.

## Global Constraints

- Archivos: `/root/crm-scripts/crm_lib.py`, `reporte_semanal.py`, `vigia_sla.py`, `/etc/cron.d/carbonbox-crm`. En el repo GitHub `ViviBohoLo/carbonbox-crm` viven bajo `crm-scripts/` — commitear ahí y desplegar al VPS.
- Link del CRM SIEMPRE `https://crm.carbonbox.app` (nunca localhost).
- Etapas en palabras (nunca `④`); días enteros (nunca `.3`); nunca la sigla "SLA" en mensajes al usuario (usar "límite").
- El **nombre del archivo** `vigia_sla.py` NO cambia (evita tocar imports/cron de más); solo cambian los textos visibles.
- SLAs/acciones/nombres de etapa viven SOLO en `crm_lib.ETAPAS`.
- Ejecutar tests en el VPS: `ssh … 'cd /root/crm-scripts && python3 -m unittest test_crm_lib -v'`.
- Montos en formato colombiano (punto de miles): `$43.806.832`. Mostrar monto solo si es > 0.
- Zona horaria de las fechas mostradas: no aplica aquí (solo se muestran días relativos y la fecha del reporte en UTC→ya se venía usando `now_utc`).

---

### Task 1: `crm_lib.py` — origen único de etapas + helpers de formato

**Files:**
- Modify: `crm-scripts/crm_lib.py`
- Test: `crm-scripts/test_crm_lib.py` (crear)

**Interfaces:**
- Produces: `ETAPAS` (dict con `nombre`, `sla` timedelta|None, `sla_txt` str|None, `accion`), `nombre_etapa(stage)->str`, `antiguedad_texto(entrada, ahora)->str` (sin "hace"), `pesos(v)->str`.

- [ ] **Step 1: Escribir el test (crear `test_crm_lib.py`)**

```python
import unittest
from datetime import datetime, timezone, timedelta
import crm_lib as c

AHORA = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)


class TestFormato(unittest.TestCase):
    def test_pesos_formato_colombiano(self):
        self.assertEqual(c.pesos(43806832), "$43.806.832")
        self.assertEqual(c.pesos(0), "$0")

    def test_antiguedad_dias(self):
        self.assertEqual(c.antiguedad_texto(AHORA - timedelta(days=159, hours=7), AHORA), "159 días")

    def test_antiguedad_horas(self):
        self.assertEqual(c.antiguedad_texto(AHORA - timedelta(hours=5), AHORA), "5 horas")

    def test_antiguedad_singular(self):
        self.assertEqual(c.antiguedad_texto(AHORA - timedelta(days=1, hours=1), AHORA), "1 día")

    def test_antiguedad_minutos(self):
        self.assertEqual(c.antiguedad_texto(AHORA - timedelta(minutes=40), AHORA), "40 minutos")

    def test_etapas_nombre_y_limite_texto(self):
        self.assertEqual(c.ETAPAS["PROPUESTA_ENVIADA"]["nombre"], "Propuesta enviada")
        self.assertEqual(c.ETAPAS["PROPUESTA_ENVIADA"]["sla_txt"], "7 días")
        self.assertEqual(c.ETAPAS["LEAD_CAPTURADO"]["sla_txt"], "60 minutos")
        self.assertIsNone(c.ETAPAS["DEMO"]["sla"])          # Demo a futuro: no genera alertas
        self.assertEqual(c.ETAPAS["EN_NEGOCIACION"]["sla"], timedelta(days=21))

    def test_nombre_etapa_desconocida(self):
        self.assertEqual(c.nombre_etapa("RARO"), "RARO")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Correr el test en el VPS y verlo fallar**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest test_crm_lib -v'
```
Esperado: FAIL (`AttributeError: module 'crm_lib' has no attribute 'pesos'`).

- [ ] **Step 3: Implementar en `crm_lib.py`**

Agregar `from datetime import timedelta` al import de arriba (queda `from datetime import datetime, timezone, timedelta`) y añadir, tras `parse_dt`:

```python
# --- Origen único de etapas: nombre, límite (para el cálculo y para mostrar) y acción ---
# 'sla' es el timedelta para comparar; 'sla_txt' es el texto que se muestra (evita
# ambigüedades tipo 60 min == 1 h, 72 h == 3 días). Deben coincidir con la guía HTML.
ETAPAS = {
    "LEAD_CAPTURADO":    {"nombre": "Lead capturado",    "sla": timedelta(minutes=60), "sla_txt": "60 minutos",
                          "accion": "Contactar hoy por correo o llamada; un lead nuevo se enfría rápido."},
    "CALIFICACION_BANT": {"nombre": "Calificación BANT",  "sla": timedelta(hours=72),   "sla_txt": "72 horas",
                          "accion": "Intentar un último contacto; si no responde, pasar a Nurturing."},
    "DEMO":              {"nombre": "Demo",               "sla": None, "sla_txt": None, "accion": ""},   # a futuro
    "PILOTO_45D":        {"nombre": "Piloto 45d",         "sla": None, "sla_txt": None, "accion": ""},   # a futuro
    "PROPUESTA_ENVIADA": {"nombre": "Propuesta enviada",  "sla": timedelta(days=7),  "sla_txt": "7 días",
                          "accion": "Llamar: «¿Alcanzó a revisar la propuesta?». Si no responde, pasar a Nurturing."},
    "EN_NEGOCIACION":    {"nombre": "En negociación",     "sla": timedelta(days=21), "sla_txt": "21 días",
                          "accion": "Si no responde, pasar a Nurturing mensual y documentar."},
    "CERRADO_GANADO":    {"nombre": "Cerrado ganado",     "sla": None, "sla_txt": None, "accion": ""},
    "RENOVACION":        {"nombre": "Renovación",         "sla": None, "sla_txt": None, "accion": ""},
    "NURTURING":         {"nombre": "Nurturing",          "sla": None, "sla_txt": None, "accion": ""},
    "PERDIDO":           {"nombre": "Perdido",            "sla": None, "sla_txt": None, "accion": ""},
}


def nombre_etapa(stage):
    e = ETAPAS.get(stage)
    return e["nombre"] if e else stage


def pesos(v):
    return "$" + f"{int(round(v)):,}".replace(",", ".")


def antiguedad_texto(entrada, ahora):
    """Tiempo transcurrido, en la unidad más grande y con plural correcto:
    '159 días' / '1 día' / '5 horas' / '40 minutos'. Sin la palabra 'hace'."""
    seg = (ahora - entrada).total_seconds()
    if seg >= 86400:
        n = int(round(seg / 86400)); return f"{n} día" if n == 1 else f"{n} días"
    if seg >= 3600:
        n = int(round(seg / 3600)); return f"{n} hora" if n == 1 else f"{n} horas"
    n = int(round(seg / 60)); return f"{n} minuto" if n == 1 else f"{n} minutos"
```

- [ ] **Step 4: Correr el test y verlo pasar**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest test_crm_lib -v'
```
Esperado: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add crm-scripts/crm_lib.py crm-scripts/test_crm_lib.py
git commit -m "feat(crm): origen único de etapas (ETAPAS) + helpers de formato"
```

---

### Task 2: `crm_lib.py` — clasificación de riesgo (leads vs estancados)

Función pura que separa los negocios en riesgo en dos grupos y arma los datos de cada línea.

**Files:**
- Modify: `crm-scripts/crm_lib.py`
- Test: `crm-scripts/test_crm_lib.py`

**Interfaces:**
- Consumes: `ETAPAS`, `parse_dt`, `antiguedad_texto`, `pesos` (Task 1).
- Produces: `clasificar_riesgo(opps, ahora) -> (leads, estancados)`. Cada item es dict:
  `{"nombre", "etapa", "antiguedad", "limite", "valor", "accion", "_orden"}`.
  `antiguedad` va SIN "hace" (ej. "159 días"); `limite` es el `sla_txt` (ej. "7 días").

- [ ] **Step 1: Escribir el test**

Agregar a `test_crm_lib.py`:

```python
def _opp(stage, name, dias, micros=0):
    return {"id": name, "name": name, "stage": stage,
            "fechaEntradaEtapa": (AHORA - timedelta(days=dias)).isoformat(),
            "createdAt": (AHORA - timedelta(days=dias)).isoformat(),
            "amount": {"amountMicros": micros}}


class TestRiesgo(unittest.TestCase):
    def test_separa_leads_de_estancados_y_ordena(self):
        opps = [
            _opp("LEAD_CAPTURADO", "Waya", 4),
            _opp("PROPUESTA_ENVIADA", "PC System", 159, 12_500_000_000_000),
            _opp("PROPUESTA_ENVIADA", "Los Cobos", 136),
            _opp("EN_NEGOCIACION", "Banco", 5),          # 5 días < límite 21 → NO en riesgo
        ]
        leads, estancados = c.clasificar_riesgo(opps, AHORA)
        self.assertEqual([l["nombre"] for l in leads], ["Waya"])
        self.assertEqual([e["nombre"] for e in estancados], ["PC System", "Los Cobos"])  # más atrasado primero
        self.assertEqual(estancados[0]["antiguedad"], "159 días")
        self.assertEqual(estancados[0]["limite"], "7 días")
        self.assertEqual(estancados[0]["valor"], "$12.500.000")

    def test_demo_no_entra_en_riesgo(self):
        leads, estancados = c.clasificar_riesgo([_opp("DEMO", "X", 99)], AHORA)
        self.assertEqual((leads, estancados), ([], []))
```

- [ ] **Step 2: Correr el test y verlo fallar**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest test_crm_lib -v'
```
Esperado: FAIL (`has no attribute 'clasificar_riesgo'`).

- [ ] **Step 3: Implementar en `crm_lib.py`** (tras `humaniza_antiguedad`)

```python
def clasificar_riesgo(opps, ahora):
    """Separa las oportunidades vencidas en (leads_sin_contacto, negocios_estancados).
    Un item entra si su etapa tiene límite y ya lo superó. LEAD_CAPTURADO va a 'leads';
    el resto a 'estancados', ordenados del más atrasado al menos."""
    leads, estancados = [], []
    for o in opps:
        etapa = ETAPAS.get(o["stage"])
        if not etapa or not etapa["sla"]:
            continue
        entrada = parse_dt(o.get("fechaEntradaEtapa")) or parse_dt(o.get("createdAt"))
        if not entrada:
            continue
        atraso = (ahora - entrada).total_seconds() - etapa["sla"].total_seconds()
        if atraso <= 0:
            continue
        micros = (o.get("amount") or {}).get("amountMicros") or 0
        valor = int(micros) / 1_000_000 if micros else 0
        item = {
            "nombre": o["name"],
            "etapa": etapa["nombre"],
            "antiguedad": antiguedad_texto(entrada, ahora),
            "limite": etapa["sla_txt"],
            "valor": pesos(valor) if valor else "",
            "accion": etapa["accion"],
            "_orden": atraso,
        }
        (leads if o["stage"] == "LEAD_CAPTURADO" else estancados).append(item)
    estancados.sort(key=lambda x: x["_orden"], reverse=True)
    leads.sort(key=lambda x: x["_orden"], reverse=True)
    return leads, estancados
```

- [ ] **Step 4: Correr el test y verlo pasar**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest test_crm_lib -v'
```
Esperado: PASS (8 tests).

- [ ] **Step 5: Commit**

```bash
git add crm-scripts/crm_lib.py crm-scripts/test_crm_lib.py
git commit -m "feat(crm): clasificar_riesgo separa leads sin contacto de negocios estancados"
```

---

### Task 3: `reporte_semanal.py` — reporte nuevo (texto plano limpio)

**Files:**
- Modify: `crm-scripts/reporte_semanal.py` (reescritura)
- Test: `crm-scripts/test_reporte.py` (crear)

**Interfaces:**
- Consumes: `ETAPAS`, `nombre_etapa`, `pesos`, `clasificar_riesgo`, `get_all_opportunities`, `get_open_opportunities`, `send_notification`, `now_utc`.
- Produces: `construir_reporte(opps_all, opps_open, ahora) -> str` (cuerpo del correo, puro).

- [ ] **Step 1: Escribir el test (crear `test_reporte.py`)**

```python
import unittest
from datetime import datetime, timezone, timedelta
import reporte_semanal as r

AHORA = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)


def _opp(stage, name, dias=0, micros=0):
    d = (AHORA - timedelta(days=dias)).isoformat()
    return {"id": name, "name": name, "stage": stage,
            "fechaEntradaEtapa": d, "createdAt": d, "amount": {"amountMicros": micros}}


class TestReporte(unittest.TestCase):
    def test_estructura_y_contenido(self):
        allo = [_opp("PROPUESTA_ENVIADA", "PC System", 159, 12_500_000_000_000),
                _opp("LEAD_CAPTURADO", "Waya", 4)]
        openo = allo
        body = r.construir_reporte(allo, openo, AHORA)
        self.assertIn("REPORTE SEMANAL DEL PIPELINE", body)
        self.assertIn("Propuesta enviada", body)          # etapa en palabras
        self.assertIn("LEADS SIN PRIMER CONTACTO (1)", body)
        self.assertIn("NEGOCIOS ESTANCADOS (1)", body)
        self.assertIn("hace 159 días (límite 7 días)", body)
        self.assertIn("https://crm.carbonbox.app", body)
        self.assertNotIn("localhost", body)
        self.assertNotIn("④", body)

    def test_sin_riesgo_muestra_ok(self):
        allo = [_opp("CERRADO_GANADO", "Ganado", 3, 1_000_000)]
        body = r.construir_reporte(allo, [], AHORA)
        self.assertIn("Sin negocios en riesgo", body)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Correr y ver fallar**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest test_reporte -v'
```
Esperado: FAIL (`has no attribute 'construir_reporte'`).

- [ ] **Step 3: Reescribir `reporte_semanal.py`**

```python
#!/usr/bin/env python3
"""Reporte semanal del pipeline — lunes 8:00 am por cron.
Conteo/valor por etapa + leads sin contactar + negocios estancados, por email."""
import sys
sys.path.insert(0, "/root/crm-scripts")
from crm_lib import (ETAPAS, nombre_etapa, pesos, clasificar_riesgo,
                     get_all_opportunities, get_open_opportunities,
                     send_notification, now_utc)

ORDEN = ["LEAD_CAPTURADO", "CALIFICACION_BANT", "DEMO", "PILOTO_45D",
         "PROPUESTA_ENVIADA", "EN_NEGOCIACION", "CERRADO_GANADO",
         "RENOVACION", "NURTURING", "PERDIDO"]
CRM_URL = "https://crm.carbonbox.app"


def construir_reporte(opps_all, opps_open, ahora):
    conteo, valor = {}, {}
    for o in opps_all:
        s = o["stage"]
        conteo[s] = conteo.get(s, 0) + 1
        micros = (o.get("amount") or {}).get("amountMicros") or 0
        valor[s] = valor.get(s, 0) + (int(micros) / 1_000_000 if micros else 0)

    leads, estancados = clasificar_riesgo(opps_open, ahora)
    total = sum(conteo.values())
    en_riesgo = len(leads) + len(estancados)

    L = ["REPORTE SEMANAL DEL PIPELINE", ahora.strftime("%d/%m/%Y"), ""]
    aten = f" · {en_riesgo} necesitan atención esta semana" if en_riesgo else ""
    L.append(f"{total} negocios en el funnel{aten}.")
    L += ["", "── NEGOCIOS POR ETAPA ──"]
    for s in ORDEN:
        if conteo.get(s):
            v = f" · {pesos(valor[s])}" if valor.get(s) else ""
            L.append(f"  {nombre_etapa(s)}: {conteo[s]}{v}")
    L.append(f"  Total: {total} negocios")

    if leads:
        L += ["", f"── LEADS SIN PRIMER CONTACTO ({len(leads)}) ──",
              "Un lead nuevo debe contactarse en la 1.ª hora; se enfría rápido."]
        for it in leads:
            L.append(f"  • {it['nombre']} — capturado hace {it['antiguedad']}")
        L.append("  → Contactar hoy por correo o llamada.")

    if estancados:
        L += ["", f"── NEGOCIOS ESTANCADOS ({len(estancados)}) ──",
              "Del más atrasado al menos. «Límite» = tiempo máximo en esa etapa sin avanzar."]
        for i, it in enumerate(estancados, 1):
            val = f"   {it['valor']}" if it['valor'] else ""
            L.append(f"")
            L.append(f" {i}. {it['nombre']}{val}")
            L.append(f"    {it['etapa']} hace {it['antiguedad']} (límite {it['limite']}).")
            if it['accion']:
                L.append(f"    → {it['accion']}")

    if not en_riesgo:
        L += ["", "✅ Sin negocios en riesgo esta semana."]

    L += ["", "── METAS DEL MES ──",
          "  25 MQL · 10 demos · 5-6 propuestas · 3-4 cierres",
          "", f"Abrir el CRM → {CRM_URL}"]
    return "\n".join(L)


if __name__ == "__main__":
    ahora = now_utc()
    body = construir_reporte(get_all_opportunities(), get_open_opportunities(), ahora)
    ok = send_notification(f"📊 Pipeline CarbonBox — semana del {ahora.strftime('%d/%m')}", body)
    print("reporte enviado" if ok else "reporte NO enviado")
    print(body)
```

- [ ] **Step 4: Correr y ver pasar**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest test_reporte -v'
```
Esperado: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add crm-scripts/reporte_semanal.py crm-scripts/test_reporte.py
git commit -m "feat(reporte): reporte semanal claro (leads vs estancados, acción, link prod)"
```

---

### Task 4: `vigia_sla.py` — Revisor de seguimientos (renombrar, formato, split renovación)

**Files:**
- Modify: `crm-scripts/vigia_sla.py` (reescritura)

**Interfaces:**
- Consumes: `ETAPAS`, `nombre_etapa`, `sla_texto`, `humaniza_antiguedad`, `parse_dt`, y las funciones de tarea/renovación existentes.
- CLI: `vigia_sla.py [sla|renovacion|todo]` (default `todo`).

- [ ] **Step 1: Reescribir `vigia_sla.py`**

```python
#!/usr/bin/env python3
"""Revisor de seguimientos del funnel CarbonBox.
Uso: vigia_sla.py [sla|renovacion|todo]  (default: todo)
- sla: crea tareas urgentes por negocios que pasaron el límite de su etapa (cron cada 3 h).
- renovacion: avisa hitos -90/-60/-30 de contratos ganados (cron 1 vez al día)."""
import sys
sys.path.insert(0, "/root/crm-scripts")
from crm_lib import (ETAPAS, nombre_etapa, antiguedad_texto,
                     get_open_opportunities, get_renewal_candidates,
                     find_open_task_by_title, create_urgent_task, send_notification,
                     now_utc, parse_dt, hito_a_disparar, load_renov_seen, save_renov_seen)

CRM_URL = "https://crm.carbonbox.app"
ACCION_HITO = {
    90: "Enviar **propuesta anticipada** de renovación (10% dto si renueva antes de -60 días).",
    60: "Enviar el **contrato** de renovación.",
    30: "**Llamada** + plan de fidelización.",
}


def revisar_sla(ahora):
    nuevos = []
    for opp in get_open_opportunities():
        etapa = ETAPAS.get(opp["stage"])
        if not etapa or not etapa["sla"]:
            continue
        entrada = parse_dt(opp.get("fechaEntradaEtapa")) or parse_dt(opp["createdAt"])
        if not entrada or (ahora - entrada) <= etapa["sla"]:
            continue
        nombre = opp["name"]
        antig = antiguedad_texto(entrada, ahora)
        limite = etapa["sla_txt"]
        title = f"🔴 Sin avanzar: {nombre} — {etapa['nombre']}"
        if find_open_task_by_title(title):
            continue
        create_urgent_task(
            title,
            f"**Lleva {antig} en {etapa['nombre']}** — el límite de esta etapa es "
            f"{limite}.\n\n**Acción:** {etapa['accion']}",
            opp["id"])
        nuevos.append(f"  • {nombre} — {etapa['nombre']} hace {antig} (límite {limite}).")
    return nuevos


def revisar_renovacion(ahora):
    nuevos = []
    seen = load_renov_seen()
    vivos = set()
    for opp in get_renewal_candidates():
        vence = parse_dt(opp.get("vencimientoContrato"))
        if not vence:
            continue
        oid = opp["id"]
        vivos.add(oid)
        dias = (vence.date() - ahora.date()).days
        hito, nuevos_vistos = hito_a_disparar(dias, seen.get(oid, []))
        seen[oid] = nuevos_vistos
        if hito is None:
            continue
        nombre = opp["name"]
        title = f"🔄 Renovación en {hito} días: {nombre}"
        if find_open_task_by_title(title):
            continue
        create_urgent_task(
            title,
            f"El contrato **vence en {dias} días** (hito -{hito}).\n\n"
            f"**Acción de este hito:** {ACCION_HITO[hito]}\n\n"
            "**Ruta completa:** -90 propuesta anticipada (10% dto si renueva antes de -60) · "
            "-60 enviar contrato · -30 llamada + plan de fidelización.",
            oid)
        nuevos.append(f"  • {nombre} — renovación hito -{hito} (vence en {dias} días).")
    seen = {k: v for k, v in seen.items() if k in vivos}
    save_renov_seen(seen)
    return nuevos


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "todo"
    ahora = now_utc()
    nuevos = []
    if modo in ("todo", "sla"):
        nuevos += revisar_sla(ahora)
    if modo in ("todo", "renovacion"):
        nuevos += revisar_renovacion(ahora)

    if nuevos:
        send_notification(
            f"🔴 CarbonBox: {len(nuevos)} negocio(s) necesitan acción",
            "El Revisor de seguimientos revisó el pipeline y creó estas tareas "
            "urgentes para Viviana:\n\n" + "\n".join(nuevos)
            + f"\n\nLas tareas ya están en el CRM, cada una con su acción:\n{CRM_URL}")
        print(f"{len(nuevos)} alertas nuevas")
    else:
        print("sin novedades")
```

- [ ] **Step 2: Verificar que importa sin errores y corre en seco (modo sin efectos previsibles)**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -c "import vigia_sla" && echo IMPORT_OK'
```
Esperado: `IMPORT_OK` (no ejecuta `__main__`, solo valida sintaxis/imports).

> ⚠️ NO correr `python3 vigia_sla.py` en esta verificación: crearía tareas reales. Se prueba en el smoke test controlado de la Task 6.

- [ ] **Step 3: Commit**

```bash
git add crm-scripts/vigia_sla.py
git commit -m "feat(vigia): Revisor de seguimientos (renombrado, días legibles, split sla/renovacion, link prod)"
```

---

### Task 5: cron — frecuencias nuevas

**Files:**
- Modify: `/etc/cron.d/carbonbox-crm` (en el VPS; copia en repo `crm-scripts/cron/carbonbox-crm` si existe)

- [ ] **Step 1: Reemplazar las dos primeras líneas del cron**

Cambiar la línea del Vigía (cada 30 min) por dos líneas, dejando las demás (reporte, bridge, gtasks, transcripts) intactas:

```cron
# Revisor de seguimientos (límite de etapas) - cada 3 horas
0 */3 * * * root /usr/bin/python3 /root/crm-scripts/vigia_sla.py sla >> /var/log/crm-vigia.log 2>&1
# Avisos de renovación - 1 vez al día (8:30 am)
30 8 * * * root /usr/bin/python3 /root/crm-scripts/vigia_sla.py renovacion >> /var/log/crm-vigia.log 2>&1
```

- [ ] **Step 2: Verificar que cron recargó**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cat /etc/cron.d/carbonbox-crm | head -6'
```
Esperado: se ven las dos líneas nuevas; el resto sin cambios.

- [ ] **Step 3: Commit** (si hay copia en repo)

```bash
git add crm-scripts/cron/carbonbox-crm
git commit -m "chore(cron): Revisor cada 3h + renovación diaria"
```

---

### Task 6: Despliegue y smoke test controlado

**Files:** ninguno nuevo (despliegue).

- [ ] **Step 1: Desplegar los scripts al VPS** (si se editó en repo local; si se editó directo en el VPS, saltar)

```bash
scp -i ~/.ssh/hostinger_vps crm-scripts/crm_lib.py crm-scripts/reporte_semanal.py crm-scripts/vigia_sla.py root@72.60.125.170:/root/crm-scripts/
```

- [ ] **Step 2: Suite completa de tests en el VPS**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 -m unittest test_crm_lib test_reporte test_gtasks_sync -v'
```
Esperado: todo PASS (sin regresión en gtasks).

- [ ] **Step 3: Smoke test del reporte (NO envía tareas; el reporte solo manda 1 correo)**

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'cd /root/crm-scripts && python3 reporte_semanal.py'
```
Esperado: imprime el reporte con el formato nuevo; llega un correo a info@carbonbox.app. Revisar que la redacción sea la aprobada, sin `localhost` ni `④`.

- [ ] **Step 4: Verificar el Revisor sin crear ruido**

El Revisor crea tareas reales. Para validarlo sin ensuciar, revisar el log tras la próxima corrida automática (cada 3 h) o inspeccionar que las tareas nuevas tengan el título/‌cuerpo nuevo:

```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'tail -20 /var/log/crm-vigia.log'
```
Esperado: en la próxima corrida, "N alertas nuevas" o "sin novedades"; las tareas creadas usan los títulos nuevos ("🔴 Sin avanzar: …").

> Nota de transición: las tareas del Vigía viejo ("🔴 SLA VENCIDO […]") quedan abiertas con el título anterior; el Revisor nuevo no las deduplicará y podría crear una equivalente con el título nuevo en la primera corrida. Viviana cierra las viejas una vez. Documentarlo al entregar.

- [ ] **Step 5: Commit final / push**

```bash
git push origin main
```
