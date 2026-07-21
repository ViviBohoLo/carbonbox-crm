---
name: cotizar
description: Genera una cotización comercial de CarbonBox (deck de 13 slides .pptx + .pdf) a partir de una oportunidad del CRM y la transcripción de la reunión. Úsalo cuando Viviana diga "cotizar", "generar cotización", "hacer una propuesta para [cliente]", "arma el deck de [empresa]", o dé el nombre/ID de una oportunidad para cotizar.
---

# Skill: /cotizar — Cotización asistida CarbonBox (Etapa 1)

Genera el deck de cotización de 13 slides a partir de: (1) la **oportunidad del CRM**
(empresa, sector, plan, contacto, NIT, link de transcripción) y (2) la **transcripción**
de la reunión de ventas en Drive. Arma un `contenido.yml` y lo renderiza con el motor
(`render.js`), sin rediseñar nada.

**Raíz del proyecto:** `tools/cotizar/` dentro del repo carbonbox-crm.
**Fuente de verdad de textos y reglas:** `Insumos/` (no inventar; campo faltante → `[⚠️ PENDIENTE: ...]`).

## Antes de empezar — pregunta obligatoria

Confirma el **tipo de huella**: **organizacional** (empresa, por sector+empleados) o
**evento** (congreso/festival, por asistentes). Son calculadoras distintas
(`calcular-precio.py` vs `calcular-precio-eventos.py`). Ver `Insumos/instrucciones.md`.

## Flujo

1. **Leer la oportunidad del CRM.** Recibe el nombre o ID de la oportunidad. Consulta Twenty
   (GraphQL en `https://crm.carbonbox.app/graphql`, token local — ver
   `Generadores/registrar-cotizacion.js` para el patrón de auth; NUNCA pedir el token por chat).

   **El NIT y el sector viven en la EMPRESA, no en la oportunidad.** El campo
   `Opportunity.idTributario` existe pero está vacío; el NIT real es `Company.nit`.
   `linkTranscripcion` es de tipo `Links`: hay que pedir sus subcampos o la query falla.
   Query verificada (2026-07-21):

   ```graphql
   opportunities(filter: { name: { ilike: "%<cliente>%" } }, first: 3) {
     edges { node {
       id name stage planCarbonbox paisNegocio
       amount { amountMicros currencyCode }
       linkTranscripcion { primaryLinkUrl }
       company { name nit sector pais }
       pointOfContact { name { firstName lastName } emails { primaryEmail } }
     } } }
   ```

   Si el campo `linkTranscripcion` no existe, ver `Generadores/_setup/crear-campo-transcripcion.md`.

2. **Transcripción.** Si falta `linkTranscripcion`, pídelo por chat. Con el link, lee la
   transcripción desde Drive.

   **Usa el Drive de Composio**, toolkit `googledrive`, cuenta con alias **`carbonbox`**
   (`info@carbonbox.app`) — es la dueña de los documentos. El conector de Drive integrado
   apunta a otra cuenta (`info@kimsa.co`) y **no ve estos archivos**: da "Requested entity
   was not found", que parece un link roto pero es un problema de permisos.

   Para un Google Doc: `GOOGLEDRIVE_DOWNLOAD_FILE` con `mime_type: "text/plain"` (el toolkit
   `googledocs` no tiene conexión activa). Devuelve una `s3url` temporal; descárgala enseguida.
   **La transcripción es dato de cliente: guárdala fuera del repo, nunca la commitees.**

   ⚠️ Si el documento son "Notas de Gemini", **el resumen del comienzo no es confiable** —
   lee la transcripción literal. Caso real: el resumen de WOM afirmaba "Plan Pro por un valor
   de 1000 dólares" cuando en la reunión "1000" era la *categoría de tamaño de empresa*, no
   el precio. Cotizar desde el resumen habría producido una cotización con el precio errado.

3. **Extraer campos** de `Insumos/instrucciones.md` (num_empleados, tipo_servicio, atica,
   motivación, decisor, stakeholders, contexto, necesidad) desde la transcripción. Lo que
   falte → `[⚠️ PENDIENTE]` o pregunta. **No inventar datos.**

4. **Redactar** `contexto` (LO QUE SABEMOS) y `necesidad` (LO QUE NECESITA), ≤80 palabras
   cada uno, tono consultivo y cálido, tuteo. Reglas en `instrucciones.md`.

5. **Calcular precio** (determinístico, NO estimar):
   - Organizacional: `python3 Generadores/calcular-precio.py --sector "<sector>" --empleados <n> --plan <esencial|pro|experto> --json`
   - Evento: `python3 Generadores/calcular-precio-eventos.py --tipo-evento "<tipo>" --num-asistentes <n> --plan <...> --json` *(si aún no tiene --json, usar la salida normal)*
   El JSON trae `precio_final`, `precio_mensual`, `precio_atica`, `precio_mensual_atica`.

   **El sector del CRM no es el de la calculadora.** `Company.sector` usa el vocabulario del
   CRM (p. ej. "Telecomunicaciones"); la calculadora espera una de las categorías de
   `Insumos/reglas-precio.md` (ahí "Telecomunicaciones" → **"Comunicaciones"**, de la fila
   "Comunicaciones / Financiero y seguros"). **Verifica el mapeo contra `reglas-precio.md`
   antes de calcular**; si ninguna categoría encaja claramente, pregunta. Un mapeo errado
   cambia el precio en silencio.

   ⚠️ **Precio ya prometido al cliente = manda sobre la calculadora.** Si en la reunión se
   pactó un valor o una categoría distinta a la que sale por número de empleados, **usa lo
   pactado** y escribe la razón en el `contenido.yml` (con la cita y el timestamp de la
   transcripción). Recalcular a ciegas produce una cotización que contradice lo que el
   cliente ya oyó. Caso real: a WOM (1.072 empleados → categoría 1500, $2.282) se le cotizó
   a propósito en la categoría 1000 ($1.937) — *"para no subirte a 1500, digamos hagámoslo
   en 1000"* (00:36:22). Ante cualquier diferencia entre lo pactado y lo calculado,
   **muéstrale ambos números a Viviana y deja que ella decida.**

6. **Escribir `Cotizaciones/<Cliente>/contenido.yml`** (formato de
   `Cotizaciones/_Plantilla/contenido.ejemplo.yml`) con encabezado (cliente, **nit**, sector,
   num_empleados, tipo_servicio, plan, atica, fecha_envio, los 4 precios) y las `slides:`.
   Luego:
   ```
   node Generadores/render.js "Cotizaciones/<Cliente>/contenido.yml"
   bash Generadores/render-pdf.sh "Cotizaciones/<Cliente>/<archivo>.pptx"
   ```

7. **Mostrar el resultado** (.pptx + .pdf) y repasar el **checklist de calidad** de
   `instrucciones.md` (NIT presente, fecha completa, precio USD confirmado, "exentos" bien
   escrito, mensual = precio÷12, fecha límite = envío+60 días, cronograma acorde al plan).
   Iterar por chat: editar el YAML → re-render.

8. **Write-back al CRM = Etapa 2 (no lo hace este skill todavía).** Cuando se envíe la
   cotización, mover la oportunidad a "Propuesta enviada" se hace aparte con
   `Generadores/registrar-cotizacion.js` (ya existe, requiere token local). Integrarlo al
   flujo del skill es trabajo de Etapa 2.

## Notas

- El motor relee `Insumos/*.md` en cada corrida: si cambian los textos fijos o reglas, no hay
  que tocar código.
- No rediseñar slides: tokens/posiciones vienen del motor (`lib/base.js`, `lib/layouts.js`).
- Si el cliente pide servicios extra (comunicación, hoja de ruta, eventos), agregar
  `- tipo: fase2-servicios` y `- tipo: fase2-valor` al YAML (diseño verde, valor `[Valor a definir]`
  si no está confirmado).
