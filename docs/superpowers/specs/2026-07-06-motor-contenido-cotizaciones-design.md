# Diseño: Cotizaciones asistidas desde el CRM (skill `/cotizar`) — Etapa 1

**Fecha:** 2026-07-06
**Estado:** En revisión (diseño)
**Proyecto:** Automatización de cotizaciones CarbonBox (Cowork/local)

## Objetivo

Que un humano en Cowork pida `/cotizar <oportunidad>` y obtenga un **deck de cotización sólido y repetible** (13 slides `.pptx`/`.pdf`), armado leyendo la **oportunidad del CRM** + la **transcripción de la reunión (Drive)**, con Claude extrayendo los datos y redactando las slides de IA, calculando el precio determinístico, y dejándolo **editable por chat**. Es la **Etapa 1** de la visión completa (abajo).

## Visión completa (contexto — se construye por etapas)

```
1. Lead entra por el formulario → oportunidad en el CRM            ✅ ya funciona
2. Tarea de primer contacto (SLA)                                  ✅ ya funciona
3. Se agenda y sucede la llamada
4. Gemini deja el transcript en Drive
5. El humano pega el link del transcript en la oportunidad          (campo nuevo)
   (campo "Link de transcripción")
6. Humano en Cowork: "/cotizar cliente X"
7. Cowork lee oportunidad + transcript → extrae datos → redacta      ◄── ETAPA 1
   contexto/necesidad → calcula precio → arma y renderiza el deck
8. En el chat se revisa y ajusta → "aprobado"
9. Al aprobar: guarda el deck en la carpeta del cliente en Drive →   ◄── ETAPA 2
   link → escribe en la oportunidad (precio, plan, # empleados,
   etapa "Propuesta enviada", link) → (opcional) correo
10. Negociación: v2, v3… cada versión guarda su link                 ◄── ETAPA 2
11. El CRM queda poblado con los datos → trazabilidad de la compra   ◄── ETAPA 2
```

**Este spec cubre solo la Etapa 1 (pasos 5–8).** La Etapa 2 (write-back al CRM, Drive, correo, versiones) es su propio spec.

## Fuente de verdad (NO se duplica)

Reglas y textos canónicos en `Insumos/`:
- `instrucciones.md` — estructura de 13 slides, tipos, modelo de campos, reglas (no inventar → `[⚠️ PENDIENTE]`, "un año", ATICA −10%, fecha límite +60d, "exentos", cifras oficiales, Fase 2, ≤80 palabras en slides IA).
- `textos-fijos.md` — textos fijos y por plan / tipo de servicio.
- `casos-exito.md` — casos por sector.
- `NOTAS-DISENO-Y-PLANTILLA.md` — diseño/layout de la plantilla.
- `reglas-precio.md` + `calcular-precio.py` — precio.

El skill y el motor **leen** estos archivos; no re-implementan su contenido. Las cotizaciones en `Cotizaciones/` son **instancias ya generadas**, no plantillas.

## Arquitectura

### 1. El skill `/cotizar` (orquestador — es Claude en Cowork)
Un skill del proyecto (`.claude/skills/cotizar/SKILL.md`) que instruye a Claude para, dado el nombre/ID de una oportunidad:
1. **Leer la oportunidad del CRM** (API de Twenty en el VPS): nombre de empresa, sector, plan (`planCarbonbox`), país, contacto, y el **`Link de transcripción`**.
2. **Leer la transcripción** del Drive (conector Drive) desde ese link.
3. **Extraer los datos** de la cotización de la transcripción (# empleados, tipo_servicio, ATICA, motivación, decisor, contexto, necesidad…) siguiendo `instrucciones.md`. Lo que no esté ni en el CRM ni en la transcripción → `[⚠️ PENDIENTE]` (no inventar) o se pregunta en el chat.
4. **Redactar** las slides de IA (contexto/necesidad, ≤80 palabras c/u) por las reglas de `instrucciones.md`.
5. **Calcular el precio:** `calcular-precio.py --json` con sector+empleados+plan.
6. **Armar el `contenido.yml`** (datos + selecciones + textos IA + precio) y **renderizar** con `render.js` → `.pptx` → `.pdf`.
7. **Mostrar el resultado** en el chat e **iterar**: "agrega una slide de Fase 2", "cambia el mensaje de la portada" → edita el YAML → re-renderiza.

### 2. Motor / renderer — `Generadores/render.js`
- Estable; no se edita por cliente. Depende de `pptxgenjs`.
- **Librería de tipos de slide** (layouts extraídos del generador actual): `layout_<tipo>(slide, datos, fijos)`.
- Lee `contenido.yml`, recorre la lista de slides en orden, y por cada una llama al layout de su `tipo`, jalando el texto fijo/por-plan/por-sector desde `textos-fijos.md`/`casos-exito.md`.
- Escribe el `.pptx` en `Cotizaciones/<Cliente>/`.

**Tipos de slide** (según `instrucciones.md`; `tipo` = clave en el YAML):
| # | `tipo` | Origen del contenido |
|---|--------|----------------------|
| 1 | `portada` | variables (cliente, tipo_servicio, fecha) |
| 2 | `contexto-necesidad` | IA (párrafos "sabemos"/"necesita"), 1 diapo a 2 columnas |
| 3 | `que-es-carbonbox` | fijo (`textos-fijos.md`) |
| 4 | `ventajas` | por plan |
| 5 | `soluciones` | por tipo_servicio |
| 6 | `caso-exito` | por sector (`casos-exito.md`) |
| 7 | `logos` | fijo |
| 8 | `trabajo-hoy` | fijo + cifras oficiales |
| 9 | `equipo` | fijo |
| 10 | `plan` | variables + por plan |
| 11 | `inversion` | variables + condicional ATICA + precio |
| 12 | `fidelizacion` | variables por precio (precio congelado) |
| 13 | `proximos-pasos` | por plan + tipo_servicio |
| (opc) | `fase2-servicios` / `fase2-valor` | Fase 2 (diseño verde), solo si aplica |

### 3. Archivo de contenido — `Cotizaciones/<Cliente>/contenido.yml`
Encabezado con datos del cliente + lista ordenada de slides (cada una `tipo` + campos variables). Fijas solo declaran su `tipo`. Reordenar/agregar/quitar = editar la lista. (Ejemplo de formato en el anexo del proyecto; cliente ficticio, no plantilla.)

### 4. Precio — `calcular-precio.py --json`
Nueva flag `--json`: imprime `{"precio_final","precio_mensual","precio_atica","precio_mensual_atica","plan","sector","tamano"}`. No cambia ninguna lógica de cálculo; solo añade salida.

### 5. Lectura del CRM (API de Twenty)
El skill consulta la oportunidad + su empresa/contacto vía GraphQL de Twenty (mismo patrón y token del proyecto CRM: `https://crm.carbonbox.app/graphql`, token de API). Campos usados: `company.name`, `company.sector`, `company.pais`, `opportunity.planCarbonbox`, contacto, y el custom field **`linkTranscripcion`**.

### 6. Campo nuevo en el CRM: `Link de transcripción`
Se agrega un campo custom **`linkTranscripcion`** (texto/URL) a la Opportunity de Twenty (vía API/metadata, una sola vez). El humano pega ahí el link de Gemini/Drive tras la llamada (paso 5). Es el ancla transcript↔oportunidad.

## Flujo de datos (Etapa 1)

```
/cotizar <oportunidad>
  → CRM (Twenty API): datos de la oportunidad + linkTranscripcion
  → Drive: transcripción desde ese link
  → Claude: extrae datos (→ PENDIENTE lo que falte) + redacta contexto/necesidad
  → calcular-precio.py --json
  → contenido.yml  → render.js (+ textos-fijos/casos-exito) → <Cliente>.pptx
  → soffice → <Cliente>.pdf
  → se muestra en el chat → iteración (editar YAML → re-render)
```

## Manejo de errores / datos faltantes
- Campo obligatorio ausente (ni en CRM ni transcripción) → `[⚠️ PENDIENTE: ...]` en el YAML/deck y se pregunta en el chat; nunca se inventa (regla de `instrucciones.md`).
- Sin `linkTranscripcion` en la oportunidad → el skill lo pide en el chat (o acepta que le peguen el texto directo).
- Sector del CRM que no mapea a los 19 sectores de precio → el skill lo mapea al más cercano y lo confirma en el chat; caso de éxito sin match → `sector_generico_latam`.
- `>2000` empleados → `calcular-precio.py` devuelve "cotización personalizada" → precio PENDIENTE.
- `tipo` desconocido en el YAML → `render.js` falla con mensaje claro (slide + tipo inválido).

## Pruebas
- **Unitaria (Python):** `calcular-precio.py --json` devuelve el JSON correcto para casos conocidos (contra los valores de la tabla actual).
- **Unitarias (Node) de `render.js`:** dado un `contenido.yml` de ejemplo, renderiza sin error, produce un `.pptx` con el nº de slides esperado, y falla claro ante un `tipo` inválido. (No se compara el binario; QA visual del PDF lo hace el humano.)
- **Prueba E2E asistida:** correr `/cotizar` sobre una oportunidad real de prueba con un transcript de ejemplo → revisar el deck resultante (humano). Limpiar datos de prueba.

## Fuera de alcance (Etapa 2 y más)
- Write-back al CRM al aprobar (precio, plan, # empleados, etapa "Propuesta enviada", link del deck).
- Guardar el deck en la carpeta del cliente en Drive + generar link.
- Correo con la cotización.
- Versiones v2/v3 en negociación (cada una con su link) + poblar el CRM para trazabilidad.
- Auto-emparejar transcript↔oportunidad (vigía del Drive). Fragil; solo si molesta hacerlo a mano.
- No se rediseña la plantilla visual ni se cambia la lógica de precio.

## Dependencias / notas
- Node + `pptxgenjs` (ya en el proyecto) + `js-yaml`. Python 3 (`calcular-precio.py`). LibreOffice (`soffice`) para el PDF.
- Conector Drive (leer transcript) y API de Twenty (leer oportunidad) — ambos disponibles en Cowork.
- Corre en Cowork/local con humano en el loop (no en el VPS): el valor es la revisión conversacional.
- Los generadores actuales (`generador-pptx-*.js`) pasan a `Generadores/_legado/` cuando el motor cubra sus casos.
