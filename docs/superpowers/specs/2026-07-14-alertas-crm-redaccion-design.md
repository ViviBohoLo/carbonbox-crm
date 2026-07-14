# Diseño — Redacción de alertas del CRM y documentación del flujo

**Fecha:** 2026-07-14
**Estado:** Propuesta, pendiente de aprobación
**Origen:** Viviana recibió el reporte semanal del pipeline (13/07/2026) y lo encontró
desorganizado y difícil de leer. Quiere (a) documentar bien el flujo del CRM para que no
se vuelva a perder de vista y (b) mejorar la redacción de *todas* las alertas automáticas.

---

## 1. Problema

Las alertas automáticas del CRM (reporte semanal + Vigía SLA) se leen mal:

- Etapas en símbolos crípticos (`④`, `⑤`) en vez de palabras.
- "159.3 días sin avanzar": no dice *desde cuándo*, ni *contra qué límite*, ni *qué hacer*,
  y los decimales se ven descuidados.
- No hay jerarquía: un lead de 4 días y una propuesta de 159 días aparecen igual de "🔴".
- La documentación existente ([guia-funnel-automatizaciones.html](../../../branding/guia-funnel-automatizaciones.html))
  ya describe el flujo, pero quedó **desfasada**: dice que el reporte semanal solo muestra
  el conteo por etapa, cuando el script real ya incluye la sección "En riesgo".

### Bugs y deudas encontradas en los scripts reales (VPS `/root/crm-scripts/`)

1. 🐞 **Link roto:** `reporte_semanal.py` y `vigia_sla.py` apuntan a `http://localhost:3000`.
   Debe ser `https://crm.carbonbox.app`.
2. 🐞 **SLAs duplicados:** definidos por separado en `reporte_semanal.py` (`SLAS_H`, en horas)
   y en `vigia_sla.py` (`SLAS`, timedelta + texto + acción). Pueden desincronizarse. Deben
   salir de un único lugar en `crm_lib.py`.
3. ⚠️ **Ruido de leads:** `LEAD_CAPTURADO` tiene SLA de 60 min, así que todo lead de más de
   una hora aparece como "en riesgo" con los mismos "días" que una propuesta estancada meses.
   Mezcla dos cosas distintas: "lead sin primer contacto" vs. "negocio estancado".
4. ⚠️ **Montos inconsistentes:** $43M en Propuesta enviada vs. $160K en Cerrado ganado sugiere
   monedas/escala mezcladas en Twenty. Es calidad de datos, no de redacción — se deja señalado,
   no se corrige aquí.
5. 🐞 **Markdown literal:** el correo del Vigía SLA usa `**negrita**`, que en el correo de
   texto plano se ve como asteriscos. (Las *tareas* sí renderizan Markdown; el correo no.)

---

## 2. Objetivos y no-objetivos

**Objetivos**
- Documentación del flujo actualizada y fiel a los scripts reales, con un catálogo claro de
  **cuándo se genera cada alerta y qué dice**.
- Alertas con redacción "completa y accionable": etapa en palabras, días vs. límite, valor y
  acción sugerida.
- Corregir los 5 bugs/deudas listados.

**No-objetivos**
- No se rediseña el pipeline ni los SLAs (los tiempos se mantienen; solo se unifican en código).
- No se corrige la calidad de datos de montos (tema aparte).
- No se cambia el canal ni el workflow Notificador: el correo sigue siendo **texto plano**.

---

## 3. Decisiones tomadas (con Viviana)

| Decisión | Elección |
|---|---|
| Dónde vive la documentación | Ampliar la guía HTML existente (`branding/guia-funnel-automatizaciones.html`) |
| Nivel de detalle de cada alerta | Completa y accionable (etapa en palabras + días vs. límite + valor + acción) |
| Formato del correo | Texto plano, pero limpio (sin tocar el workflow Notificador) |
| Renombrar "Vigía SLA" | → **"Revisor de seguimientos"** (y quitar la sigla "SLA" de los mensajes; hablar de "límite") |
| Frecuencia del Revisor | Cada **3 horas** (antes cada 30 min) |
| Frecuencia de renovación | **1 vez al día** (contratos anuales, fecha conocida; no necesita más) |
| Frecuencia del formulario web | Se mantiene en **5 min** (único que necesita inmediatez) |
| Etapas Demo / Piloto 45d | **A futuro** (marcadas con `*`): hoy no se ofrecen demos ni pilotos |
| Diagrama de flujo | **Sí**, agregado a la guía (proceso de venta de 7 pasos + automatizaciones) |
| Botón "correo de seguimiento" | **Se diseña ahora** (Fase 3): enlace en el reporte → página de confirmación → envío |

### Flujo de venta real (confirmado con Viviana 2026-07-14)

1. **Lead capturado** (formulario web) → 2. **Bienvenida** (correo automático que invita a agendar
la llamada) → 3. **Llamada virtual de presentación** (se presenta CarbonBox, se identifican los
dolores, queda el transcript) → 4. **Calificación BANT + cotización** (a partir del transcript) →
5. **Propuesta enviada** → 6. **Negociación** → 7. **Cierre ganado** → renovación anual.
La llamada virtual (paso 3) ya está soportada: el correo de bienvenida enlaza al calendario y el
transcript se archiva por empresa y se enlaza a la oportunidad (`linkTranscripcion`). Lo que faltaba
era hacerla **visible en la documentación** — resuelto con el diagrama de flujo.

---

## 4. Plan en dos fases

### Fase 1 — Documentar (ahora)

Agregar a la guía HTML una sección nueva: **"Las alertas: cuándo se generan y qué dicen"**.
Un catálogo de cada mensaje automático con: qué lo dispara · cada cuánto corre · por dónde
llega · **cómo se ve hoy vs. cómo debería verse** (antes/después lado a lado).

Esto vuelve visible el desfase y sirve de lienzo para afinar la redacción con Viviana antes
de tocar código.

### Fase 2 — Aplicar a los scripts (después, con los textos aprobados)

Llevar la redacción aprobada a los scripts y unificar SLAs en `crm_lib.py`. Todo junto para que
guía y código queden consistentes:
- Redacción nueva de las 4 alertas (reporte semanal, correo y tarea del Revisor, tarea de renovación).
- **Renombrar** "Vigía SLA" → "Revisor de seguimientos" en scripts, logs y comentarios.
- **Frecuencias:** Revisor cada 3 h; renovación 1 vez al día (requiere separar el bloque de
  renovación de `vigia_sla.py` o darle un guardia horario, porque hoy corren juntos cada 30 min);
  formulario web se queda en 5 min.
- **Marcar Demo/Piloto como inactivas** (sin SLA activo) mientras no se ofrezcan.
- Corregir los **5 bugs/deudas** (link localhost, SLAs duplicados, ruido de leads → separar
  "leads sin contactar" de "negocios estancados", markdown literal en el correo; los montos quedan
  señalados como tema de datos).
- Archivos: `reporte_semanal.py`, `vigia_sla.py`, `crm_lib.py`, `/etc/cron.d/carbonbox-crm`.

### Fase 3 — Correo de seguimiento con un clic (feature nueva)

Botón "Enviar recordatorio" en el reporte semanal, por negocio estancado. Ver §8. Es una fase
propia porque agrega una página web y plantillas. Se diseña ahora; se construye tras la Fase 2.

---

## 5. Redacción propuesta (borrador para afinar en Fase 1)

> Todos los textos son borradores. El propósito de la Fase 1 es que Viviana los vea en la
> guía y los ajustemos antes de programarlos.

### 5.1 Reporte semanal (correo, texto plano)

**Asunto:** `📊 Reporte semanal del pipeline — semana del 13/07`

```
REPORTE SEMANAL DEL PIPELINE
Lunes 13 de julio de 2026

26 negocios en el funnel · 14 necesitan atención esta semana.

── NEGOCIOS POR ETAPA ───────────────────────────
  Lead capturado ......  2     $5.853
  Propuesta enviada ... 10     $43.806.832
  En negociación ......  2     $53.000.605
  Cerrado ganado ...... 10     $160.119
  Nurturing ...........  1
  Perdido .............  1     $1.937
  ───────────────────────────────────
  Total ............... 26

── LEADS SIN PRIMER CONTACTO (2) ─────────────────
Un lead nuevo debe contactarse en la 1ª hora; se enfría rápido.

  • Hotel Waya Guajira — capturado hace 4 días
  • PepsiCo (Plan Pro) — capturado hace 5 días
  → Contactar por correo o llamada hoy.

── NEGOCIOS ESTANCADOS (12) ──────────────────────
De la más atrasada a la menos. "Límite" = tiempo máximo que un
negocio debería estar en esa etapa sin avanzar.

 1. HC Organizacional · PC System Colombia         $12.500.000
    Propuesta enviada hace 159 días (límite 7).
    → Llamar: "¿Alcanzó a revisar la propuesta?"
      Si no responde, pasar a Nurturing.

 2. HC Organizacional · Los Cobos Medical Center     $8.000.000
    Propuesta enviada hace 136 días (límite 7).
    → Llamar: "¿Alcanzó a revisar la propuesta?"
      Si no responde, pasar a Nurturing.

 3. HC Organizacional Renovación · Fundación Santafé $XX
    En negociación hace 91 días (límite 21).
    → Si no responde, pasar a Nurturing mensual y documentar.

 … (resto ordenados igual)

── METAS DEL MES ─────────────────────────────────
  25 MQL · 10 demos · 5-6 propuestas · 3-4 cierres

Abrir el CRM → https://crm.carbonbox.app
```

**Cambios frente a hoy:**
- Separa **"Leads sin primer contacto"** de **"Negocios estancados"** (resuelve el ruido #3).
- Etapa en palabras, días enteros (sin `.3`), y "(límite N)" para dar contexto de gravedad.
- Cada estancado trae **valor** y **acción** sugerida (de la tabla "Si se vence…" de la guía).
- Ordenados de más a menos atrasado.
- Link corregido a producción.

### 5.2 Revisor de seguimientos — correo resumen

**Asunto:** `🔴 CarbonBox: 3 negocios necesitan acción hoy`

```
El Revisor de seguimientos revisó el pipeline y creó 3 tareas
urgentes para Viviana:

  • PC System Colombia — Propuesta enviada hace 159 días (límite 7).
    Acción: llamar para confirmar interés.
  • Banco Agrario — En negociación hace 26 días (límite 21).
    Acción: si no responde, pasar a Nurturing mensual.

Las tareas ya están en el CRM, cada una con su acción:
https://crm.carbonbox.app
```

**Cambios:** sin enum crudo ni asteriscos literales; días en vez de horas cuando > 48h;
resumen legible; link corregido.

### 5.3 Revisor de seguimientos — tarea urgente (renderiza Markdown, sí se mantiene formato)

**Título hoy:** `🔴 SLA VENCIDO [PROPUESTA_ENVIADA]: PC System Colombia`
**Título propuesto:** `🔴 Propuesta sin respuesta — PC System Colombia`

**Cuerpo propuesto:**
```
**Lleva 159 días en Propuesta enviada** — el límite de esta etapa es 7 días.

**Acción:** Llamar directamente: "¿Alcanzó a revisar la propuesta?"
Si no responde, pasar a Nurturing.
```

### 5.4 Renovación — tarea (Markdown)

**Título hoy:** `🔄 RENOVACIÓN -90d: {empresa}`
**Título propuesto:** `🔄 Renovación en 90 días — {empresa}`
Cuerpo actual ya es claro; solo se ajusta el título y se confirma el link.

---

## 6. Estructura de la sección nueva en la guía HTML

Ubicación: nueva sección tras "Los vigilantes automáticos", antes de "Del formulario web al CRM".

Contenido:
1. **Tabla-catálogo de alertas** — filas: cada mensaje (Vigía SLA tarea, Vigía SLA correo,
   Renovación, Reporte semanal, + automatizaciones por evento). Columnas: *Qué lo dispara ·
   Cada cuánto · Por dónde llega · Qué contiene*.
2. **Bloques antes/después** — tarjetas con el texto actual (gris) y el propuesto (branding),
   uno por cada alerta de 5.1–5.4.
3. **Nota de mantenimiento** — recordatorio de que los SLAs y las acciones viven en un único
   lugar del código (`crm_lib.py`), para que la guía y los scripts no se vuelvan a desfasar.

Reutiliza los estilos ya existentes de la guía (`.card`, `.auto`, `.sla`, `.pill`, tablas).

---

## 7. Puntos abiertos a confirmar con Viviana

1. **Separar leads de estancados** en el reporte (§5.1): propuesto sí. Confirmar.
2. **Valores en las líneas de riesgo:** ¿mostrar el monto siempre, o solo cuando sea
   > $0? (Muchos negocios podrían no tener monto cargado.)
3. **Redacción exacta de las acciones** por etapa — se afinan sobre la guía en Fase 1.

---

## 8. Fase 3 — Correo de seguimiento con un clic (diseño)

**Objetivo.** Cuando un negocio no responde (propuesta o negociación estancada), Viviana puede
enviar un recordatorio al cliente **desde el reporte semanal, con un clic**, sin salir a redactar
nada — pero **sin romper la regla de oro** (ningún correo a cliente se envía sin su confirmación).

**Flujo.**
1. El reporte semanal, en cada negocio estancado, incluye un enlace **«Enviar recordatorio»**
   apuntando a `https://crm.carbonbox.app/seguimiento?opp=<id>&token=<firma>`.
2. Ese enlace abre una **página de confirmación** (servida por el mismo servicio del formulario,
   `intake_server.py`) que muestra el correo ya redactado con la plantilla de la etapa y los datos
   del cliente (nombre, empresa, negocio).
3. Viviana revisa y presiona **«Confirmar y enviar»** (un POST). Solo entonces se envía el correo
   (vía Gmail, como la bienvenida) y se registra en la oportunidad (nota + campo
   `ultimoSeguimiento`).

**Por qué página de confirmación y no envío directo:** los clientes de correo **precargan** los
enlaces (prefetch), así que un enlace que enviara con solo abrirse podría disparar envíos por
accidente. El GET solo muestra; el envío ocurre en el POST del botón.

**Plantillas por etapa (borrador).**
- *Propuesta enviada:* "Hola {nombre}, ¿alcanzaste a revisar la propuesta que te enviamos? Quedo
  atenta a cualquier duda para ayudarte a avanzar."
- *En negociación:* "Hola {nombre}, ¿cómo vas con la decisión sobre {negocio}? Con gusto reviso
  contigo cualquier ajuste que necesites."

**Piezas técnicas.**
- Nuevo campo en Opportunity: `ultimoSeguimiento` (DATE) para no reenviar de más y verlo en el CRM.
- Endpoint GET `/seguimiento` (confirmación) + POST `/seguimiento/enviar` en `intake_server.py`.
- Token firmado (HMAC con secreto del servidor) para que el enlace no sea adivinable ni reutilizable
  indefinidamente.
- Envío por Gmail reutilizando el mecanismo de la bienvenida (People API / connectedAccount).

**Puntos abiertos Fase 3.** ¿Las plantillas van con la firma de Viviana incrustada (como la
bienvenida)? · ¿Se limita a 1 recordatorio por semana por negocio? · ¿El botón aparece también en
el correo del Revisor, o solo en el reporte semanal?

---

## 9. Recordatorio de "lead sin agendar la llamada" (Fase 3b)

**Origen.** Viviana (2026-07-14): hoy nada avisa si un lead recibió la bienvenida pero **nunca
agendó** la llamada de presentación. Se programa una secuencia de recordatorio.

**Decisiones (2026-07-14):** 2 rondas cada 3 días, luego Nurturing · el correo al lead **pasa por
confirmación** de Viviana (no se envía solo) · la tarea para Viviana se crea **con cada** recordatorio.

**Lógica** (corre dentro del Revisor de seguimientos, cada 3 h, sobre oportunidades en
`LEAD_CAPTURADO`; estado en un `agenda_seen.json` para actuar una vez por ronda):

1. **Detección de "agendó":** consultar el calendario de reservas (el calendario "Viviana"
   `c_82bb1396…@group.calendar.google.com`, el mismo que usa `calendar_transcripts.py`) y ver si
   el **correo del lead** aparece como invitado en algún evento. Si aparece → ya agendó, no hacer nada.
2. **Día 3 (≈72 h desde captura), si no agendó y ronda 1 pendiente:** crear tarea para Viviana
   "🗓️ No ha agendado — {nombre} ({empresa})", con la ficha de contacto y un **enlace «Enviar
   recordatorio de agenda»** (abre la página de confirmación de la Fase 3 con la plantilla "agenda
   tu llamada"). El correo **no** sale hasta que Viviana confirme.
3. **Día 6, ronda 2:** repetir (2.ª tarea + enlace).
4. **Día 9 sin agendar y aún en `LEAD_CAPTURADO`:** mover la oportunidad a `NURTURING`
   automáticamente (y registrar nota del motivo).

**Regla de oro.** El correo al cliente siempre pasa por confirmación. La creación de tareas y el
paso a Nurturing sí son automáticos (no son correos a cliente).

**Dependencia.** Reutiliza la página de confirmación y el envío de la Fase 3 → se construye junto
con ella (por eso "Fase 3b"). La detección por calendario reutiliza el token/acceso de
`calendar_transcripts.py`.

**Plantilla del recordatorio de agenda (borrador):** "Hola {nombre}, nos encantaría conocer los
retos de {empresa} en huella de carbono. ¿Agendamos una llamada corta? Aquí puedes elegir el
horario que mejor te quede: {enlace al calendario}."

**Punto abierto.** ¿Los 1225 contactos importados (fuente OTRO) quedan excluidos de esta secuencia?
(Sí: la secuencia solo aplica a oportunidades en `LEAD_CAPTURADO`, no a contactos sueltos, así que
quedan fuera por diseño — confirmar.)
