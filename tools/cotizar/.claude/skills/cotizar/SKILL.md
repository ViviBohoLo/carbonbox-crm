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
       company { name nit sectorCarbonbox numEmpleados sector pais }
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

3. **Extraer campos** de `Insumos/instrucciones.md` (num_empleados —solo si el CRM no lo
   trae, ver paso 5—, tipo_servicio, atica,
   motivación, decisor, stakeholders, contexto, necesidad) desde la transcripción. Lo que
   falte → `[⚠️ PENDIENTE]` o pregunta. **No inventar datos.**

4. **Redactar** `contexto` (LO QUE SABEMOS) y `necesidad` (LO QUE NECESITA), ≤80 palabras
   cada uno, tono consultivo y cálido, tuteo. Reglas en `instrucciones.md`.

5. **Calcular precio** (determinístico, NO estimar):
   - Organizacional: `python3 Generadores/calcular-precio.py --sector "<sector>" --empleados <n> --plan <esencial|pro|experto> --json`
   - Evento: `python3 Generadores/calcular-precio-eventos.py --tipo-evento "<tipo>" --num-asistentes <n> --plan <...> --json` *(si aún no tiene --json, usar la salida normal)*
   El JSON trae `precio_final`, `precio_mensual`, `precio_atica`, `precio_mensual_atica`.

   **Sector y empleados salen del CRM — no los traduzcas a mano.**

   - **Sector:** usa `Company.sectorCarbonbox`, que ya guarda una de las 20 categorías de la
     calculadora. Pásale el **código tal cual** (`--sector MINERIA`, `--sector TRANSPORTE`…):
     `calcular-precio.py` lo resuelve con su tabla `SECTOR_CRM`. **No uses `Company.sector`**
     (ese es el vocabulario viejo de HubSpot, texto libre, y traducirlo a ojo cambiaba el
     precio en silencio). Tampoco copies la *etiqueta* del CRM: Twenty no admite comas, así
     que 6 etiquetas no son idénticas al nombre interno — por eso se pasa el código.
     Si `sectorCarbonbox` está vacío, **pregunta a Viviana cuál corresponde** y pídele que lo
     cargue en la empresa; no lo adivines a partir de `Company.sector`.
   - **Empleados:** usa `Company.numEmpleados` (número real; la calculadora lo normaliza sola
     a su categoría). Si está vacío, sácalo de la transcripción y **avísale a Viviana para que
     quede cargado** en la empresa, así la próxima cotización es repetible.

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
   powershell -File Generadores/render-pdf.ps1 "Cotizaciones/<Cliente>/<archivo>.pptx" -Png
   ```
   **En la máquina de Viviana no hay LibreOffice**, así que `render-pdf.sh` no corre; usa
   el `.ps1`, que exporta con PowerPoint. El flag `-Png` deja cada slide como imagen en
   `_png/` — **ábrelas y revisa el diseño de verdad** antes de dar la cotización por lista:
   desbordes de texto, tipografías sustituidas, imágenes fuera de lugar. Verificar el texto
   por dentro del `.pptx` no sustituye ver la slide renderizada.

7. **Mostrar el resultado** (.pptx + .pdf) y repasar el **checklist de calidad** de
   `instrucciones.md` (NIT presente, fecha completa, precio USD confirmado, "exentos" bien
   escrito, mensual = precio÷12, fecha límite = envío+60 días, cronograma acorde al plan).
   Iterar por chat: editar el YAML → re-render.

8. **Cerrar el ciclo: Drive → CRM → correo.**

   **8.1 Subir el deck a Drive.** Los entregables de clientes viven en la carpeta **`Leads`**
   (`13dvWmMahnoyl_xsAZohAGVHoA8vIdX5A`), con **una subcarpeta por empresa**.
   - Busca la subcarpeta comparando **normalizado** (minúsculas, sin tildes ni puntuación):
     las carpetas no coinciden literal con el CRM ("Fundacion Santa Fe de Bogota" ↔
     "Fundación Santafé de Bogotá", "Area Andina" ↔ "Área Andina").
   - **Si hay exactamente una, úsala. Si hay 0 o más de 1, muéstrale las candidatas a Viviana
     y pregúntale cuál usar. NUNCA crees carpetas nuevas** — ya existe un duplicado
     ("Hotel Waya" y "Hotel Waya Guajira") y crear más empeora el problema.
   - Sube **los dos archivos**: el `.pdf` (lo que ve el cliente) y el `.pptx` (el editable,
     para poder retomarlo después).
   - Usa el Drive de Composio con la cuenta alias **`carbonbox`** (`info@carbonbox.app`),
     igual que para leer transcripciones.
   - **Revisa qué permiso quedó** en el link del PDF y avísale a Viviana si el cliente no va a
     poder abrirlo. **No cambies permisos de compartición por tu cuenta**: puedes exponer
     material de otros clientes sin querer.

   **8.2 Redactar el correo** para ese cliente con el contexto de la reunión: saludo por su
   nombre, qué le estás enviando, el **link del deck**, validez de 60 días y cierre cálido.
   Guárdalo en `Cotizaciones/<Cliente>/correo.txt` (esa carpeta está fuera de git).

   **8.3 Escribir en el CRM:**
   ```bash
   node Generadores/registrar-cotizacion.js --cliente "…" --nit "…" --plan Pro --precio N \
     --link-cotizacion "<link del PDF>" --borrador-archivo "Cotizaciones/<Cliente>/correo.txt"
   ```
   Deja la oportunidad en "Propuesta enviada" con el monto, el plan (`experto` se guarda como
   `PREMIUM`), el link del deck y el borrador del correo.

   **8.4 Avisarle a Viviana que ya puede enviarla.** El link de la página de envío va **firmado
   con el secreto del servidor**, así que **no lo construyas ni inventes una firma**. En la
   siguiente pasada (máximo 3 h) el **Revisor de seguimientos** crea sola la tarea
   *"📤 Cotización lista para enviar"* con el link correcto, y también aparece en el correo de
   alertas. Dile a Viviana que la busque ahí.

   En esa página ella elige el remitente (Viviana, Laura, Alejandra o Miguel), agrega copias
   (CC) para quienes no estén en el CRM, revisa el texto y **solo ahí** se envía. Al enviar, el
   CRM guarda el link del correo en la oportunidad.

## Notas

- El motor relee `Insumos/*.md` en cada corrida: si cambian los textos fijos o reglas, no hay
  que tocar código.
- No rediseñar slides: tokens/posiciones vienen del motor (`lib/base.js`, `lib/layouts.js`).
- Si el cliente pide servicios extra (comunicación, hoja de ruta, eventos), agregar
  `- tipo: fase2-servicios` y `- tipo: fase2-valor` al YAML (diseño verde, valor `[Valor a definir]`
  si no está confirmado).
