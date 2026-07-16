# Consolidación en `carbonbox-ops`

**Fecha:** 2026-07-16
**Estado:** Diseño aprobado, pendiente de plan de implementación

> **Nota de revisión (2026-07-16):** la primera versión de este spec se escribió sin consultar el remoto de GitHub y partía de tres premisas falsas: que el código del 14-jul no estaba versionado, que había drift bidireccional entre las dos carpetas del CRM, y que fusionarlas era un paso delicado. Ninguna resultó cierta. Ver "Corrección de premisas" al final.

## Problema

El trabajo de CarbonBox está repartido en cuatro carpetas locales, y el agente no tiene forma de saber cuál compartir.

| Carpeta | Git | Estado real | Contenido |
|---|---|---|---|
| `CRM CarbonBox` | ❌ No | Espejo obsoleto — **sin código propio** | Copia vieja de los scripts + datos sueltos |
| `carbonbox-crm` | ✅ Sí | **Autoritativa y al día** (tras sincronizar) | Repo de ops completo |
| `Cobros CMR CarbonBox` | ❌ No | Solo documentos | SOP de cobros Helisa → Twenty |
| `Automatización de cotizaciones CarbonBox` | ❌ No | **Activa y sin respaldo** | Generador de decks (Node + Python) |

### Causa raíz

El flujo de trabajo es conversacional: la usuaria comparte una carpeta con el agente y describe el cambio. El agente lee los docs de esa carpeta para saber dónde trabajar. **La documentación de cada carpeta señala a la otra como la carpeta de desarrollo:**

- `CRM CarbonBox/docs/.../2026-07-14-fase2-alertas-scripts.md:13` — "En el repo GitHub `ViviBohoLo/carbonbox-crm` viven bajo `crm-scripts/` — commitear ahí y desplegar al VPS"
- `carbonbox-crm/docs/.../2026-07-06-form-intake-webhook.md:18` — "Se desarrollan en el espejo local `CRM CarbonBox/vps/crm-scripts/`"

En palabras de la usuaria: *"cuando le dije que revisara la carpeta del cmr, no supe cuál compartirle."*

El daño real no fue pérdida de trabajo — el trabajo se commiteó correctamente a GitHub. Fue **una carpeta local que se quedó atrás sin que nadie lo notara**, y la ilusión resultante de que había trabajo sin respaldo. Cuatro carpetas para un solo proyecto obligan a tomar una decisión que nadie puede tomar bien.

### Riesgos concretos, en orden

1. **`Automatización de cotizaciones` no tiene git.** 73 MB con las cotizaciones reales de PepsiCo, WOM, Imprenta Nacional y Hotel Waya, más los generadores y los Insumos. Sin historial ni remoto. **Es el único trabajo realmente sin respaldo, y es la carpeta más activa (tocada hoy).**
2. **Credenciales en claro:** `Cobros CMR CarbonBox/terminal Helisa.txt` contiene dos juegos de usuario/contraseña del portal Helisa Cloud en texto plano.
3. **Carpetas locales que se quedan atrás en silencio.** `carbonbox-crm` llevaba 2 commits de retraso; nada avisó.
4. **Ambigüedad para el agente.** Sin fuente única de verdad, cada sesión puede elegir distinto.

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
Ya tiene git, remoto (`ViviBohoLo/carbonbox-crm`), un `.gitignore` que bloquea secretos, y — verificado — **es superconjunto de `CRM CarbonBox` en todo el código**. Se renombra porque el nombre se queda corto: adentro habrá cotizaciones y cobros, que no son CRM. `ops` describe lo que es: la operación de CarbonBox. El renombrado aplica en local y en GitHub.

**Cotizar entra como `tools/cotizar/`, no como repo aparte.**
Hoy tiene acoplamiento cero con el CRM: entra Markdown, sale un `.pptx`, sin red. Pero la Etapa 1 de su propio plan (`2026-07-06-cotizar-etapa1.md`) requiere leer una oportunidad de Twenty vía GraphQL — algo que `crm-scripts/crm_lib.py` ya sabe hacer, y que el spec de cotizar reconoce explícitamente ("mismo patrón y token del proyecto CRM"). En repos separados habría que duplicar `crm_lib.py`, reproduciendo la enfermedad que esta consolidación cura.

**Cobros entra como `cobros/`.**
Cinco archivos de texto que describen escrituras al mismo Twenty que administra el resto del repo. Un repo propio sería ceremonia sin beneficio.

**El `CLAUDE.md` es la pieza que impide la recaída.**
Debe declarar sin ambigüedad: dónde vive el código, cómo llega al VPS, **cómo se sincroniza con GitHub antes de empezar a trabajar** (el fallo que causó el desfase), y qué se versiona y qué no. Los planes y specs existentes pasan a `docs/` como registro histórico — **son ellos los que se contradicen**, y deben dejar de leerse como instrucciones vigentes.

**Los binarios quedan fuera de git, no fuera del disco.**
`Cotizaciones/`, `Recursos/` y `Logos/` (≈70 MB de PPTX y PNG, crecimiento ilimitado) permanecen en la carpeta local, excluidos vía `.gitignore`. El spec de cotizar ya contempla Drive como destino de los decks. Se versiona el código, `Insumos/`, `docs/`, `branding/` y el sistema de diseño: pocos MB, y es lo irreemplazable.

**Los datos de clientes no entran a git.**
El README del repo declara: "no contiene datos de clientes ni secretos". `CRM CarbonBox/Archivos Hubspot/` (2 CSV export de HubSpot, 2.3 MB de contactos y empresas) y `transcripción video de youtube.docx` respetan esa línea: se conservan en disco o en Drive, fuera del repo.

### Alternativas descartadas

- **Dos repos (CRM + herramientas):** devuelve el problema del `crm_lib.py` duplicado y le da al agente dos carpetas donde dudar.
- **Fusionar solo el CRM, dejar Cobros y cotizar aparte:** considerada y descartada por la usuaria durante el diseño. Dejaba en pie la pregunta "¿cuál carpeta le comparto?", que es el problema a resolver.

## Plan de migración

El orden es parte del diseño: hay pasos irreversibles.

### 0. Sacar las credenciales de Helisa — BLOQUEANTE

`Cobros CMR CarbonBox/terminal Helisa.txt` (dos juegos de usuario/contraseña de Helisa Cloud) se traslada a un gestor de contraseñas y se elimina del disco.

**Debe ocurrir antes de que `cobros/` toque git.** Una vez en el historial, borrar el archivo no lo saca: queda en los commits para siempre.

### 1. Copia de seguridad

Copiar las cuatro carpetas completas a un destino externo antes de mover un solo archivo.

### 2. Poner cotizar a salvo — PRIORIDAD

Es el único trabajo sin respaldo. Entra al repo como `tools/cotizar/` con su `.gitignore` configurado antes del primer commit, para que los 70 MB de binarios nunca entren al historial. Arreglar `package.json` (hoy sin `name` ni `scripts`).

Se hace temprano y no al final: cada día que pasa es un día de exposición.

### 3. Renombrar el repo

`carbonbox-crm` → `carbonbox-ops`, en local y en GitHub. Actualizar el remoto.

### 4. Verificar el repo contra el VPS

El repo es autoritativo frente a `CRM CarbonBox` — verificado por diff. Falta confirmar que **coincide con lo que realmente corre en el VPS** (`72.60.125.170:/root/crm-scripts/`). Es una comprobación, no una fusión: si hay diferencia, se investiga antes de tocar nada.

Correr los tests (`python3 -m unittest`) como línea base.

### 5. Retirar `CRM CarbonBox`

No tiene código propio. Antes de archivarla, rescatar lo único que no está en el repo y decidir su destino **fuera de git** (son datos de clientes):
- `Archivos Hubspot/` — 2 CSV export de HubSpot (2.3 MB)
- `transcripción video de youtube.docx` (184 KB)

Descartar: `.playwright-mcp/` (snapshots de depuración del 06-jul), `__pycache__/`, `nul` (artefacto de un `> nul` en shell POSIX; rompe herramientas que recorren el árbol).

### 6. Incorporar cobros

Mudanza directa, una vez hecho el paso 0.

### 7. Escribir el `CLAUDE.md` y subir a GitHub

Debe incluir la regla de sincronizar antes de trabajar. Commitear también `.superpowers/` o excluirlo explícitamente (hoy está sin trackear).

### 8. Marcar las carpetas viejas, no borrarlas

Renombrar con prefijo `_VIEJO_`. Permanecen hasta que la usuaria confirme que todo funciona. **El borrado es decisión suya, no de la migración.**

Limpieza menor: `Cotizaciones/Imprenta Nacional de Colombia/lu536y5c0.tmp` y `.~lock....pdf#` — temporales de LibreOffice.

## Criterios de éxito

1. Existe una sola carpeta `carbonbox-ops`, respaldada en GitHub.
2. El código de cotizar está versionado; sus 70 MB de binarios no.
3. El repo coincide con lo desplegado en el VPS.
4. Los tests pasan.
5. `terminal Helisa.txt` no existe en disco ni en el historial de git.
6. `CLAUDE.md` responde sin ambigüedad dónde va el código, cómo se despliega y cómo sincronizar.
7. Ningún doc vigente contradice a otro sobre la carpeta de desarrollo.
8. El repo no contiene datos de clientes ni binarios de crecimiento ilimitado.
9. Las carpetas viejas siguen en disco, marcadas.

## Fuera de alcance

**Conectar `/cotizar` con el CRM.** Es el siguiente proyecto y ya tiene plan escrito (`2026-07-06-cotizar-etapa1.md`, 8 tareas, ninguna ejecutada).

Al retomarlo, tener presente: hoy el patrón es **duplicar un generador de ~26 KB por cliente** (3 copias con ~90% de código idéntico). El plan del 6-jul ya propone separar contenido (`contenido.yml`) de render (`render.js`). El skill `/cotizar` es la tarea 8 de ese plan, no la primera: montarlo sobre el patrón de copy-paste automatizaría el desorden en vez de resolverlo.

**Renombrar "CMR" → "CRM"** en artefactos externos (carpeta de Drive). La transposición está fosilizada en nombres reales fuera de este repo.

## Corrección de premisas

Registro de lo que la primera versión de este spec afirmaba y la verificación contra GitHub desmintió. Se conserva porque el error es instructivo: **se diagnosticó el estado de un repo mirando solo la copia local.**

| Premisa original | Realidad verificada |
|---|---|
| El código del 14-jul (webinars, Fases 2/3) existe solo en un disco y en el VPS | Está en GitHub desde el 14-jul: commits `8033521` y `e542f40`, 5.091 líneas, autor "CarbonBox Ops" |
| Siete archivos con drift bidireccional; ninguna carpeta es superconjunto | Tras sincronizar, `carbonbox-crm` es superconjunto en **todo** el código. `CRM CarbonBox` no aporta un solo archivo propio |
| Las versiones del 14-jul en `CRM CarbonBox` deberían ganar | Pierden todas. En los dos archivos que diferían (`hubspot_bridge.py`, `test_lead_intake.py`) el repo tiene la versión posterior y más completa; el cron del repo incluye las líneas de webinars que faltan en la copia |
| Fusionar los scripts es el paso delicado de la migración | No hay nada que fusionar. `CRM CarbonBox` se archiva tras rescatar dos artefactos que no son código |

Lo que causó el error: `carbonbox-crm` local llevaba 2 commits de retraso y se leyó su fecha (07-jul) como el estado del proyecto. Un `git fetch` al inicio lo habría evitado — de ahí que el `CLAUDE.md` deba exigir sincronizar antes de trabajar.
