# Consolidación en `carbonbox-ops`

**Fecha:** 2026-07-16
**Estado:** Diseño aprobado, pendiente de plan de implementación

## Problema

El trabajo de CarbonBox está repartido en cuatro carpetas locales. Ninguna de ellas es autoritativa por sí sola, y dos de ellas contienen trabajo real sin ningún respaldo.

| Carpeta | Git | Último cambio | Contenido |
|---|---|---|---|
| `CRM CarbonBox` | ❌ No | 2026-07-14 | Scripts del VPS (webinars, Fases 2/3), planes, specs, branding |
| `carbonbox-crm` | ✅ Sí | 2026-07-07 | Repo formal de ops: deploy, rebrand, scripts, README |
| `Cobros CMR CarbonBox` | ❌ No | 2026-07-09 | SOP de cobros Helisa → Twenty (solo documentos) |
| `Automatización de cotizaciones CarbonBox` | ❌ No | 2026-07-16 | Generador de decks de cotización (Node + Python) |

### Causa raíz

`CRM CarbonBox` y `carbonbox-crm` son el mismo proyecto duplicado. Se separaron porque **la documentación de cada carpeta señala a la otra como la carpeta de desarrollo**:

- `CRM CarbonBox/docs/.../2026-07-14-fase2-alertas-scripts.md:13` — "En el repo GitHub `ViviBohoLo/carbonbox-crm` viven bajo `crm-scripts/` — commitear ahí y desplegar al VPS"
- `carbonbox-crm/docs/.../2026-07-06-form-intake-webhook.md:18` — "Se desarrollan en el espejo local `CRM CarbonBox/vps/crm-scripts/`"

El flujo de trabajo es conversacional: la usuaria comparte una carpeta con el agente y describe el cambio. El agente lee los docs de esa carpeta para saber dónde trabajar. Como los docs se contradicen, el agente trabajó en una u otra según cuál se le compartiera. **El drift lo causó la documentación, no un error de operación.**

Consecuencia directa, en palabras de la usuaria: *"cuando le dije que revisara la carpeta del cmr, no supe cuál compartirle."*

### Riesgos concretos

1. **Sin respaldo:** el código desplegado en el VPS (14-jul: webinars, seguimiento, Fases 2/3) existe únicamente en un disco local y en el servidor. Sin historial ni remoto.
2. **Sin respaldo:** 73 MB de cotizaciones reales (PepsiCo, WOM, Imprenta Nacional, Hotel Waya) sin versionar.
3. **Credenciales en claro:** `Cobros CMR CarbonBox/terminal Helisa.txt` contiene usuarios y contraseñas del portal Helisa Cloud en texto plano.
4. **Drift bidireccional:** ninguna de las dos carpetas del CRM es superconjunto de la otra.

## Objetivo

Una sola carpeta local, respaldada en GitHub, donde el agente no tenga a dónde equivocarse.

## Diseño

### Estructura destino

```
carbonbox-ops/
├── CLAUDE.md           # Fuente única de verdad para el agente
├── crm-scripts/        # Scripts que corren en el VPS (incluye crm_lib.py)
├── tools/cotizar/      # Generadores, Insumos, sistema de diseño
├── cobros/             # SOP de Helisa → Twenty
├── deploy/             # Docker Compose, Caddy, systemd, cron
├── rebrand/            # Parche Twenty → CarbonBox
├── scripts-ops/        # Operaciones puntuales
├── branding/
└── docs/               # Planes y specs (historia, no instrucciones)
```

De cuatro carpetas a una.

### Decisiones y justificación

**El repo base es `carbonbox-crm`, renombrado a `carbonbox-ops`.**
Sobrevive esta carpeta porque ya tiene git, remoto configurado (`ViviBohoLo/carbonbox-crm`) y un `.gitignore` que bloquea secretos. Se renombra porque el nombre se queda corto: adentro habrá cotizaciones y cobros, que no son CRM. `ops` describe lo que realmente es — la operación de CarbonBox. El renombrado aplica en local y en GitHub.

**Cotizar entra como `tools/cotizar/`, no como repo aparte.**
Hoy ese proyecto tiene acoplamiento cero con el CRM: entra Markdown, sale un `.pptx`, sin red. Pero la Etapa 1 de su propio plan (`2026-07-06-cotizar-etapa1.md`) requiere leer una oportunidad de Twenty vía GraphQL — algo que `crm-scripts/crm_lib.py` ya sabe hacer, y que el spec de cotizar reconoce explícitamente ("mismo patrón y token del proyecto CRM"). En repos separados habría que duplicar `crm_lib.py`, reproduciendo exactamente la enfermedad que esta consolidación cura.

**Cobros entra como `cobros/`.**
Son cinco archivos de texto que describen escrituras al mismo Twenty que administra el resto del repo. Un repo propio sería ceremonia sin beneficio.

**El `CLAUDE.md` es la pieza que impide la recaída.**
Debe declarar sin ambigüedad: dónde vive el código, cómo llega al VPS, qué se versiona y qué no. Los planes y specs existentes pasan a `docs/` como registro histórico — **son ellos los que hoy se contradicen**, y deben dejar de leerse como instrucciones vigentes.

**Los binarios quedan fuera de git, no fuera del disco.**
`Cotizaciones/`, `Recursos/` y `Logos/` (≈70 MB de PPTX y PNG, de crecimiento ilimitado) permanecen en la carpeta local pero se excluyen vía `.gitignore`. El spec de cotizar ya contempla Drive como destino de los decks. Se versiona el código, `Insumos/`, `docs/`, `branding/` y el sistema de diseño: pocos MB, y es lo irreemplazable.

### Alternativas descartadas

- **Dos repos (CRM + herramientas):** devuelve el problema del `crm_lib.py` duplicado y le da al agente dos carpetas donde dudar.
- **Fusionar solo el CRM, dejar Cobros y cotizar aparte:** considerada y descartada por la usuaria durante el diseño. Dejaba en pie la pregunta "¿cuál carpeta le comparto?", que es el problema a resolver.

## Plan de migración

El orden es parte del diseño: hay pasos irreversibles.

### 0. Sacar las credenciales de Helisa — BLOQUEANTE

`Cobros CMR CarbonBox/terminal Helisa.txt` (dos juegos de usuario/contraseña de Helisa Cloud) se traslada a un gestor de contraseñas y se elimina del disco.

**Debe ocurrir antes de que `cobros/` toque git.** Una vez en el historial, borrar el archivo no lo saca: queda en los commits para siempre.

### 1. Copia de seguridad

Copiar las cuatro carpetas completas a un destino externo antes de mover un solo archivo. Red de seguridad para todo lo que sigue.

### 2. Renombrar el repo

`carbonbox-crm` → `carbonbox-ops`, en local y en GitHub. Actualizar el remoto.

### 3. Fusionar los scripts del CRM — paso delicado

Siete archivos divergieron en ambos sentidos:

| Archivo | `CRM CarbonBox` (07-14) | `carbonbox-crm` (07-07) |
|---|---|---|
| `crm_lib.py` | 12.1 KB | 6.0 KB |
| `intake_server.py` | 8.6 KB | 4.2 KB |
| `vigia_sla.py` | 7.2 KB | 4.1 KB |
| `calendar_transcripts.py` | 10.1 KB | 9.2 KB |
| `reporte_semanal.py` | 3.4 KB | 2.6 KB |
| `hubspot_bridge.py` | divergente | divergente |
| `cron/carbonbox-crm` | 1.0 KB | 0.8 KB |

Solo en `CRM CarbonBox`: `seguimiento.py`, `webinar_intake.py`, `webinar_lib.py`, `webinar_post.py`, `webinar_recordatorios.py`, tests asociados, 6 planes y 4 specs.

Solo en `carbonbox-crm`: `gtasks_sync.py`, `hs_peek.py`, tests asociados, `deploy/`, `rebrand/`, `scripts-ops/`.

**Criterio de resolución:** las versiones del 14-jul son las candidatas ganadoras porque son las desplegadas en el VPS — pero **se verifica contra el VPS (`72.60.125.170:/root/crm-scripts/`) antes de decidir, archivo por archivo.** El servidor tiene la última palabra sobre qué está en producción. No se asume.

Al terminar: correr los tests (`python3 -m unittest`) antes de commitear.

### 4. Incorporar cotizar y cobros

Mudanza directa: hoy ninguno de los dos habla con el CRM. Configurar `.gitignore` para excluir `tools/cotizar/Cotizaciones/`, `tools/cotizar/Recursos/` y `tools/cotizar/Logos/`. Arreglar `package.json` de cotizar (hoy sin `name` ni `scripts`).

### 5. Escribir el `CLAUDE.md` y subir a GitHub

### 6. Marcar las carpetas viejas, no borrarlas

Renombrar con prefijo `_VIEJO_`. Permanecen hasta que la usuaria confirme que todo funciona. **El borrado es decisión suya, no de la migración.**

### 7. Limpieza

- `CRM CarbonBox/nul` — artefacto de un `> nul` en shell POSIX; rompe herramientas que recorren el árbol.
- `__pycache__/` en `CRM CarbonBox`.
- `.playwright-mcp/` — snapshots de una sesión de depuración del 06-jul.
- `Cotizaciones/Imprenta Nacional de Colombia/lu536y5c0.tmp` y `.~lock....pdf#` — temporales de LibreOffice.

## Criterios de éxito

1. Existe una sola carpeta `carbonbox-ops`, respaldada en GitHub.
2. El código del 14-jul está versionado y coincide con lo desplegado en el VPS.
3. Los tests pasan.
4. `terminal Helisa.txt` no existe en disco ni en el historial de git.
5. `CLAUDE.md` responde sin ambigüedad dónde va el código y cómo se despliega.
6. Ningún doc vigente contradice a otro sobre la carpeta de desarrollo.
7. El repo no contiene binarios de crecimiento ilimitado.
8. Las carpetas viejas siguen en disco, marcadas.

## Fuera de alcance

**Conectar `/cotizar` con el CRM.** Es el siguiente proyecto y ya tiene plan escrito (`2026-07-06-cotizar-etapa1.md`, 8 tareas, ninguna ejecutada).

Al retomarlo, tener presente: hoy el patrón es **duplicar un generador de ~26 KB por cliente** (existen 3 copias con ~90% de código idéntico). El plan del 6-jul ya propone separar contenido (`contenido.yml`) de render (`render.js`). El skill `/cotizar` es la tarea 8 de ese plan, no la primera: montarlo sobre el patrón de copy-paste automatizaría el desorden en vez de resolverlo.

**Renombrar "CMR" → "CRM"** en artefactos externos (carpeta de Drive). La transposición está fosilizada en nombres reales fuera de este repo.
