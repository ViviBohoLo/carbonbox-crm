# Diseño — Seguimiento de licitaciones por fechas del proceso

**Fecha:** 2026-07-21
**Estado:** Diseño aprobado por Viviana, pendiente de plan e implementación
**Origen:** Al excluir las licitaciones del seguimiento comercial (commit `a400992`) quedó el
hueco: hoy no hay nada que vigile sus fechas. Una licitación que se pasa de la fecha de cierre
se pierde sin remedio.

---

## 1. El proceso real (según Viviana)

No es estándar, pero normalmente:

**Estudio de mercado** → **Licitación abierta** (aquí está la **fecha de cierre de propuesta**,
la crítica) → **Evaluación** → **Adjudicación**

La única fecha que necesita vigilancia activa es el **cierre de propuesta**. Después del cierre,
la entidad evalúa en sus propios tiempos (impredecibles) y Viviana solo necesita **registrar el
estado**, sin alertas.

## 2. Decisiones (Viviana, 2026-07-21)

| Tema | Decisión |
|---|---|
| Modelo | **Campos nuevos en la oportunidad** (no etapas de pipeline ni objeto aparte) |
| Avisos antes del cierre | **Escalonados: 15, 7, 3 y 1 días antes** |
| Después del cierre | **Solo registrar el estado**, sin alertas |
| Aviso de cierre vencido | **Sí** — evita que queden licitaciones eternamente "abiertas" |

**Por qué campos y no etapas de pipeline:** Twenty no soporta pipelines separados; meter etapas
de licitación en `stage` revolvería el Kanban comercial. Un objeto aparte sería más limpio pero
las desconectaría del funnel, los reportes y las cotizaciones que ya funcionan.

---

## 3. Modelo de datos

Dos campos nuevos en **Opportunity**:

| Campo | Tipo | Valores / uso |
|---|---|---|
| `etapaLicitacion` | SELECT | Estudio de mercado · Abierta · En evaluación · Adjudicada · No adjudicada |
| `fechaCierreLicitacion` | DATE | Fecha límite de entrega de la propuesta |

⚠️ Las etiquetas de opciones SELECT en Twenty **no pueden contener comas**.

**Detección de licitación (mejora sobre lo actual):** hoy `es_licitacion()` se basa en el nombre.
Pasa a ser: *es licitación si `etapaLicitacion` tiene valor*; el nombre queda como **respaldo**
para las que aún no se hayan marcado. Así deja de depender de cómo se escriba el título.

---

## 4. Alertas (dentro del Revisor de seguimientos, cada 3 h)

Solo actúan cuando `etapaLicitacion = Abierta` y hay `fechaCierreLicitacion`:

- **Hitos −15 / −7 / −3 / −1 días:** una tarea urgente por hito, una sola vez cada uno
  (idempotente y a prueba de apagones, igual que las renovaciones).
  - Título: `📋 Cierre de licitación en {N} días: {nombre}`
  - Cuerpo: fecha exacta de cierre, entidad y recordatorio de revisar los TDR.
- **Cierre vencido:** si la fecha ya pasó y sigue en "Abierta", **un aviso único**:
  `⚠️ Pasó el cierre: {nombre}` → "actualiza el estado (¿se entregó? ¿pasa a evaluación?)".
- **Estudio de mercado / En evaluación / Adjudicada / No adjudicada:** **sin alertas**.

Las alertas nuevas entran al correo resumen del Revisor, igual que las demás.

**Estado:** `licitacion_seen.json` (patrón de `renovacion_seen.json`; ya cubierto por el
`.gitignore` con `*_seen.json`). Se poda cuando la licitación deja de estar "Abierta".

**Reutilización:** `hito_a_disparar(dias, ya_vistos)` en `crm_lib.py` ya implementa exactamente
esta lógica (dispara el hito alcanzado más urgente, una vez cada uno) pero con la constante
`HITOS=[90,60,30]`. Se generaliza con un parámetro opcional `hitos=HITOS` — cambio compatible
hacia atrás, sin tocar la renovación.

---

## 5. Reporte semanal

Bloque propio, en vez de aparecer como "negocios estancados":

```
── 📋 LICITACIONES (3) ──
Abiertas (ojo con la fecha de cierre):
  • Licitación - Banco Agrario — cierra en 12 días (26/07)
  • Licitación :HC - Superservicios — cierra en 3 días (17/07)
En evaluación (sin acción, esperando resultado):
  • Licitación - Alcaldía X — entregada el 02/07
```

Las licitaciones **salen del bloque de "negocios estancados"** (ya no se les mide el SLA
comercial, que no aplica).

## 6. Visibilidad en el CRM

Agregar `etapaLicitacion` y `fechaCierreLicitacion` como **columnas visibles** en la vista
"All Opportunities" (mismo procedimiento usado para `ultimoSeguimiento`).

---

## 7. Fuera de alcance (YAGNI)

- Fechas de publicación del TDR, límite de preguntas y respuestas: Viviana pidió mantenerlo
  simple; solo el cierre necesita vigilancia.
- Fecha estimada de adjudicación y recordatorios post-cierre: descartados explícitamente.
- Prórrogas: si la entidad corre la fecha, Viviana edita `fechaCierreLicitacion` y los hitos
  se recalculan solos (los ya avisados no se repiten salvo que la nueva fecha reabra hitos).

## 8. Riesgos y notas

- **Dato manual:** las alertas dependen de que Viviana cargue la fecha de cierre. Si no la
  carga, no hay aviso. Mitigación: la etapa "Abierta" sin fecha aparece en el reporte marcada
  como *"sin fecha de cierre cargada"*.
- **Cambio de detección:** al pasar de nombre a campo, las 2 licitaciones actuales (Banco
  Agrario y Superservicios) deben marcarse con su `etapaLicitacion` para no perder el
  tratamiento especial; mientras tanto el respaldo por nombre las cubre.
