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
   `Generadores/registrar-cotizacion.js` para el patrón de auth; NUNCA pedir el token por chat)
   y extrae: empresa, **NIT**, sector, plan recomendado, país/ciudad, contacto, y
   `linkTranscripcion`. Si el campo `linkTranscripcion` no existe aún, ver
   `Generadores/_setup/crear-campo-transcripcion.md`.

2. **Transcripción.** Si falta `linkTranscripcion`, pídelo por chat. Con el link, lee la
   transcripción desde Drive (conector Drive).

3. **Extraer campos** de `Insumos/instrucciones.md` (num_empleados, tipo_servicio, atica,
   motivación, decisor, stakeholders, contexto, necesidad) desde la transcripción. Lo que
   falte → `[⚠️ PENDIENTE]` o pregunta. **No inventar datos.**

4. **Redactar** `contexto` (LO QUE SABEMOS) y `necesidad` (LO QUE NECESITA), ≤80 palabras
   cada uno, tono consultivo y cálido, tuteo. Reglas en `instrucciones.md`.

5. **Calcular precio** (determinístico, NO estimar):
   - Organizacional: `python3 Generadores/calcular-precio.py --sector "<sector>" --empleados <n> --plan <esencial|pro|experto> --json`
   - Evento: `python3 Generadores/calcular-precio-eventos.py --tipo-evento "<tipo>" --num-asistentes <n> --plan <...> --json` *(si aún no tiene --json, usar la salida normal)*
   El JSON trae `precio_final`, `precio_mensual`, `precio_atica`, `precio_mensual_atica`.

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
