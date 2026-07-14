# Sección "Las alertas" en la guía del funnel — Plan de implementación (Fase 1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar a la guía HTML del funnel una sección nueva —"Las alertas: cuándo se generan y qué dicen"— con un catálogo de cada mensaje automático y bloques antes/después de la redacción propuesta, y corregir dos descripciones desfasadas de la guía.

**Architecture:** Se edita un único archivo, `branding/guia-funnel-automatizaciones.html`. Se reutilizan las clases de estilo existentes (`.card`, `.auto`, `.sla`, `.pill`, `.note`, tablas) y se agrega un bloque CSS pequeño para el catálogo y las tarjetas antes/después. La sección nueva va entre "Los vigilantes automáticos" (#crons) y "Del formulario web al CRM" (#puente).

**Tech Stack:** HTML + CSS embebido (sin build). Verificación visual en navegador.

## Global Constraints

- Archivo único a tocar: `branding/guia-funnel-automatizaciones.html`. No crear archivos nuevos.
- Español, tono de la guía (claro, para usuario de negocio, no técnico).
- Reutilizar clases existentes; el CSS nuevo va junto a `.auto`/`.pill`, antes de `</style>` (línea ~114).
- Los montos en los ejemplos son ilustrativos y deben rotularse como "ejemplo".
- Link del CRM en todos los textos: `https://crm.carbonbox.app` (nunca `localhost`).
- Etapas siempre en palabras; días enteros (sin decimales); nada de `④`/`⑤` en los textos propuestos.
- Fuente de los SLAs y acciones: la tabla §2 de la propia guía (Lead 60 min · BANT 72 h · Demo 7 d · Propuesta 7 d · Negociación 21 d).

---

### Task 1: Corregir descripciones desfasadas y añadir el CSS + entrada de TOC

Prepara el terreno: corrige los dos textos que quedaron desfasados, agrega la entrada en la
tabla de contenido y el CSS que usarán las tareas 2 y 3.

**Files:**
- Modify: `branding/guia-funnel-automatizaciones.html`

- [ ] **Step 1: Añadir el CSS del catálogo y antes/después**

Insertar justo antes de `</style>` (línea ~114, después del bloque `@media print`):

```css
  /* Catálogo de alertas + antes/después */
  .ba{display:grid; grid-template-columns:1fr 1fr; gap:14px; margin:14px 0;}
  .ba .col{border:1px solid var(--line); border-radius:12px; overflow:hidden;}
  .ba .col h4{margin:0; padding:9px 14px; font-size:12px; text-transform:uppercase; letter-spacing:.05em;}
  .ba .antes h4{background:#f3f4f6; color:var(--muted);}
  .ba .despues h4{background:var(--indigo-soft); color:var(--indigo);}
  .ba pre{margin:0; padding:14px; font-size:12px; line-height:1.5; white-space:pre-wrap; word-break:break-word;
          font-family:'SFMono-Regular',Consolas,monospace; background:var(--card);}
  .ba .antes pre{color:var(--muted);}
  .ba .despues pre{color:var(--ink);}
  .ba-lbl{font-size:13px; font-weight:600; color:var(--indigo); margin:20px 0 4px;}
  @media (max-width:680px){ .ba{grid-template-columns:1fr;} }
```

- [ ] **Step 2: Añadir la entrada en la tabla de contenido**

En el `<ol>` de la `nav.toc` (líneas 130-134), tras la línea de `#crons`
(`<li><a href="#crons">Los vigilantes automáticos</a></li>`), insertar:

```html
      <li><a href="#alertas">Las alertas: cuándo salen y qué dicen</a></li>
```

- [ ] **Step 3: Corregir la descripción desfasada del Reporte semanal**

En la tarjeta "Reporte semanal" (línea 292), reemplazar el `<p>` actual:

```html
        <p>Envía por correo un resumen del pipeline: cuántas oportunidades hay en cada etapa. Foto rápida del estado comercial.</p>
```

por:

```html
        <p>Envía por correo un resumen del pipeline: el conteo y valor por etapa, los leads sin primer contacto y los negocios estancados (con su acción sugerida). Foto rápida del estado comercial. Detalle en la sección «Las alertas».</p>
```

- [ ] **Step 4: Corregir "Dónde vive" en Notas de operación**

En la nota de la línea 361, reemplazar:

```html
      <b>Dónde vive.</b> El CRM corre en tu PC (dentro de WSL2 + Docker), accesible en <code>http://localhost:3000</code>. Los contenedores se reinician solos tras reiniciar el equipo.
```

por:

```html
      <b>Dónde vive.</b> El CRM corre en el servidor (VPS Hostinger), en producción en <code>https://crm.carbonbox.app</code>. Los servicios se reinician solos tras un reinicio del servidor.
```

- [ ] **Step 5: Actualizar la fecha del encabezado**

En la línea 123, cambiar `Actualizado: 6 de julio de 2026` por `Actualizado: 14 de julio de 2026`.

- [ ] **Step 6: Verificar en el navegador**

Abrir `branding/guia-funnel-automatizaciones.html` en el navegador.
Esperado: la guía carga sin errores; en el índice aparece "Las alertas: cuándo salen y qué dicen";
la tarjeta del Reporte semanal y la nota "Dónde vive" muestran el texto corregido; la fecha dice 14 de julio.

---

### Task 2: Sección nueva "Las alertas" con el catálogo

Crea la sección y su tabla-catálogo de todos los mensajes automáticos.

**Files:**
- Modify: `branding/guia-funnel-automatizaciones.html`

**Interfaces:**
- Consumes: el CSS de Task 1 (`.ba`, `.ba-lbl`); clases existentes `.card`, `table`, `.note`.
- Produces: el elemento `<section id="alertas">` con la tabla, cerrado con `</section>`.
  Task 3 insertará las tarjetas antes/después **dentro** de esta sección, antes de `</section>`.

- [ ] **Step 1: Insertar la sección con el catálogo**

Insertar entre el cierre de la sección #crons (línea 304, `</section>`) y el comentario
`<!-- 5. PUENTE -->` (línea 306):

```html

  <!-- 4b. ALERTAS -->
  <section id="alertas">
    <h2 class="sec"><span class="n">4b</span>Las alertas: cuándo salen y qué dicen</h2>
    <p class="lead">Todos los mensajes que el CRM genera solo — tareas y correos. Aquí ves qué dispara cada uno, cada cuánto, por dónde llega y qué contiene. Abajo, cómo se redacta cada alerta.</p>

    <div class="card">
      <table>
        <tr><th>Alerta</th><th>Qué la dispara</th><th>Cada cuánto</th><th>Por dónde llega</th><th>Qué contiene</th></tr>
        <tr><td><b>Primer contacto</b></td><td>Se captura un lead nuevo</td><td>Al instante</td><td>Tarea en el CRM (Viviana)</td><td>Recordatorio de contactar en la 1.ª hora.</td></tr>
        <tr><td><b>Correo de bienvenida</b></td><td>Se crea un contacto</td><td>Al instante</td><td>Email al contacto</td><td>Saludo de bienvenida (plantilla aprobada).</td></tr>
        <tr><td><b>Tarea Vigía SLA</b></td><td>Una oportunidad pasó el límite de su etapa</td><td>Cada 30 min</td><td>Tarea urgente en el CRM</td><td>Etapa, días vs. límite y la acción a tomar.</td></tr>
        <tr><td><b>Correo Vigía SLA</b></td><td>El Vigía creó tareas nuevas en esa pasada</td><td>Cada 30 min</td><td>Email a info@carbonbox.app</td><td>Resumen de lo que venció y ya tiene tarea.</td></tr>
        <tr><td><b>Renovación</b></td><td>Un contrato ganado llega a −90 / −60 / −30 días de vencer</td><td>Cada 30 min</td><td>Tarea urgente en el CRM</td><td>El hito y la acción de renovación de ese hito.</td></tr>
        <tr><td><b>Reporte semanal</b></td><td>Inicio de semana</td><td>Lunes 8:00 am</td><td>Email a info@carbonbox.app</td><td>Conteo/valor por etapa + leads sin contactar + negocios estancados.</td></tr>
      </table>
    </div>

  </section>
```

- [ ] **Step 2: Verificar en el navegador**

Recargar el archivo. Esperado: aparece la sección "4b · Las alertas" con una tabla de 6 filas,
bien alineada y con los estilos de tabla de la guía; el índice enlaza a ella.

---

### Task 3: Bloques antes/después de las 4 alertas redactadas

Añade, dentro de la sección #alertas, las cuatro tarjetas antes/después con la redacción propuesta.

**Files:**
- Modify: `branding/guia-funnel-automatizaciones.html`

**Interfaces:**
- Consumes: CSS `.ba`/`.ba-lbl` (Task 1) y la `<section id="alertas">` (Task 2).

- [ ] **Step 1: Insertar los cuatro bloques antes de cerrar la sección**

Insertar justo antes del `</section>` de #alertas (el que se creó en Task 2, tras la `</div>` de la tarjeta del catálogo):

```html
    <p class="lead" style="margin-top:26px;">Cómo se ve hoy cada alerta y cómo debería verse. Los montos son de ejemplo.</p>

    <!-- Reporte semanal -->
    <div class="ba-lbl">1 · Reporte semanal (correo)</div>
    <div class="ba">
      <div class="col antes"><h4>Hoy</h4><pre>🔴 HC Organizacional - PC System Colombia — ④ Propuesta Enviada, 159.3 días sin avanzar</pre></div>
      <div class="col despues"><h4>Propuesto</h4><pre>── NEGOCIOS ESTANCADOS (12) ──
De la más atrasada a la menos. "Límite" = tiempo
máximo en esa etapa sin avanzar.

 1. HC Organizacional · PC System Colombia   $12.500.000
    Propuesta enviada hace 159 días (límite 7).
    → Llamar: "¿Alcanzó a revisar la propuesta?"
      Si no responde, pasar a Nurturing.

Los leads recién capturados van en su propio
bloque: «LEADS SIN PRIMER CONTACTO».</pre></div>
    </div>

    <!-- Correo Vigía SLA -->
    <div class="ba-lbl">2 · Vigía SLA (correo resumen)</div>
    <div class="ba">
      <div class="col antes"><h4>Hoy</h4><pre>El vigía del funnel encontró estos vencimientos y ya creó las tareas en el CRM:
• PC System Colombia — PROPUESTA_ENVIADA vencido (3816.0h, SLA 7 días)
Entra a http://localhost:3000 para gestionarlos.</pre></div>
      <div class="col despues"><h4>Propuesto</h4><pre>El vigía del funnel revisó el pipeline y creó
3 tareas urgentes para Viviana:

  • PC System Colombia — Propuesta enviada hace
    159 días (límite 7). Acción: llamar para
    confirmar interés.

Las tareas ya están en el CRM, cada una con su
acción: https://crm.carbonbox.app</pre></div>
    </div>

    <!-- Tarea Vigía SLA -->
    <div class="ba-lbl">3 · Vigía SLA (tarea en el CRM)</div>
    <div class="ba">
      <div class="col antes"><h4>Hoy</h4><pre>Título: 🔴 SLA VENCIDO [PROPUESTA_ENVIADA]: PC System Colombia
Cuerpo: **SLA de la etapa:** 7 días — lleva **3816.0h** sin avanzar.
**Acción:** Llamar directamente...</pre></div>
      <div class="col despues"><h4>Propuesto</h4><pre>Título: 🔴 Propuesta sin respuesta — PC System Colombia
Cuerpo:
Lleva 159 días en Propuesta enviada — el límite
de esta etapa es 7 días.

Acción: Llamar: "¿Alcanzó a revisar la propuesta?"
Si no responde, pasar a Nurturing.</pre></div>
    </div>

    <!-- Renovación -->
    <div class="ba-lbl">4 · Renovación (tarea en el CRM)</div>
    <div class="ba">
      <div class="col antes"><h4>Hoy</h4><pre>Título: 🔄 RENOVACIÓN -90d: Fundación Santafé</pre></div>
      <div class="col despues"><h4>Propuesto</h4><pre>Título: 🔄 Renovación en 90 días — Fundación Santafé
(el cuerpo ya es claro; solo cambia el título)</pre></div>
    </div>

    <div class="note"><b>Que no se vuelva a desfasar.</b> Los límites (SLA) de cada etapa y la acción sugerida vivirán en un solo lugar del código (<code>crm_lib.py</code>), y de ahí los toman el Vigía SLA y el Reporte semanal. Así esta guía y los mensajes siempre dicen lo mismo.</div>
```

- [ ] **Step 2: Verificar en el navegador**

Recargar el archivo. Esperado: dentro de "Las alertas" aparecen 4 bloques a dos columnas
(Hoy en gris / Propuesto en índigo), legibles; en móvil (angosto) las columnas se apilan;
al final, la nota "Que no se vuelva a desfasar". Ningún texto propuesto contiene `localhost`,
`④`, ni decimales en los días.

---

## Notas para la Fase 2 (no se ejecuta en este plan)

Cuando Viviana apruebe los textos sobre la guía, la Fase 2 los lleva a los scripts del VPS
(`reporte_semanal.py`, `vigia_sla.py`), unifica los SLAs/acciones en `crm_lib.py` y corrige
los 5 bugs (link localhost, SLAs duplicados, ruido de leads → separar en dos grupos, montos,
markdown literal en el correo). Ver el spec: `docs/superpowers/specs/2026-07-14-alertas-crm-redaccion-design.md`.
