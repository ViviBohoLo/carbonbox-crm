# Diseño — Inscripción a webinars → CRM (Fase B)

Fecha: 2026-07-14
Estado: propuesto (código de referencia escrito; falta desplegar y probar en el VPS)

## Contexto

Automatización del flujo de webinars de CarbonBox. Esta fase cubre la captura de
inscritos y su entrada al CRM, más el correo de confirmación. Se eligió la vía
**Google Forms + Google Sheet + puente al CRM** (Opción A) por rapidez y porque
reutiliza el patrón ya probado de `hubspot_bridge.py` (sondear una fuente externa
y dar de alta leads).

Decisiones tomadas:
- Inscritos entran como `fuenteLead=WEBINAR`, `suscritoMarketing` según checkbox,
  **sin** oportunidad (no entran al pipeline de ventas; solo contacto + marketing).
- El **Google Sheet de respuestas es la fuente de verdad** de inscritos por webinar
  (vive en la carpeta del invitado en Drive). El CRM solo copia los contactos.
- Correos por Gmail API, reutilizando `seguimiento.enviar_gmail` (remitente Viviana).

## Arquitectura

```
Google Form  ──►  Google Sheet (en Drive, carpeta del invitado)
                        │  (cron cada ~5 min)
                        ▼
                webinar_intake.py ──► alta_inscrito() en CRM (fuenteLead=WEBINAR, sin Opp)
                        │
                        └──► correo de confirmación E2 (Gmail API)

webinar_recordatorios.py  (cron horario)  ──► E3 (T-7d) / E4 (T-1d) / E5 (T-1h)
webinar_post.py           (cron horario o manual)  ──► E6 (agradecimiento + YouTube)
```

Cada webinar se describe con una **ficha JSON** en `crm-scripts/webinars/<slug>.json`
(ver `webinars/yauto-sas.example.json`). El estado de envíos se guarda en
`crm-scripts/webinars/state/<slug>.json` (email → etapas ya enviadas), idempotente
como `renovacion_seen.json`.

## Archivos nuevos

- `webinar_lib.py` — librería: cargar fichas, leer el Sheet (Sheets API), mapear
  filas → `datos`, `alta_inscrito()` (Persona sin Opp), estado, y render de los
  correos E2–E6. Funciones puras probadas en `test_webinar_lib.py` (15 tests, verdes).
- `webinar_intake.py` — cron: Sheet → CRM + confirmación E2.
- `webinar_recordatorios.py` — cron: E3/E4/E5 por umbral de tiempo.
- `webinar_post.py` — E6 cuando la ficha ya tiene el YouTube y el evento pasó.
- `webinars/yauto-sas.example.json` — plantilla de ficha.
- `test_webinar_lib.py` — pruebas de las funciones puras.

Ningún archivo existente se modifica. `alta_inscrito()` es una función nueva
(no toca `crear_lead`, que sigue sirviendo al formulario web y al puente de HubSpot).

## Modelo de datos

`alta_inscrito(datos)`:
- Si el email ya existe: no duplica; si aceptó marketing y no estaba suscrito,
  actualiza `suscritoMarketing=true`. Devuelve `'actualizado'` o `'existe'`.
- Si no existe: crea Empresa (dedup por nombre/dominio) + Persona con
  `fuenteLead=WEBINAR` y el consentimiento. **No** crea Opportunity. Devuelve `'creado'`.

Segmentación resultante (coherente con la spec 2026-07-07): el inscrito recibe
marketing pero **no** entra al funnel ni recibe la bienvenida comercial (ese
workflow filtra `fuenteLead=WEB`). Solo se crea Opportunity si más adelante pide demo.

## Correos del ciclo

- **E2 Confirmación** — inmediato al ingerir del Sheet. Incluye link de Meet y
  "añadir al calendario" (si están en la ficha).
- **E3/E4/E5 Recordatorios** — T-7d / T-1d / T-1h, por umbral: cada correo se envía
  una sola vez por inscrito, sin importar cuándo se inscribió ni la cadencia del cron.
  No se envían si la ficha aún no tiene `meet_link`.
- **E6 Post-webinar** — agradecimiento + grabación de YouTube, a todos los inscritos.

Todos usan la cabecera de marca CarbonBox y la firma de Viviana.

## Cron (añadir a `/etc/cron.d/carbonbox-crm`)

```
# Webinars: intake del Sheet cada 5 min; recordatorios y post cada hora.
*/5 * * * *  root  /usr/bin/python3 /root/crm-scripts/webinar_intake.py        >> /var/log/carbonbox-crm.log 2>&1
7   * * * *  root  /usr/bin/python3 /root/crm-scripts/webinar_recordatorios.py >> /var/log/carbonbox-crm.log 2>&1
9   * * * *  root  /usr/bin/python3 /root/crm-scripts/webinar_post.py          >> /var/log/carbonbox-crm.log 2>&1
```

## Pasos para poner en marcha (por webinar)

1. Confirmar fecha con el invitado (reunión de alineación).
2. Crear el evento de Google Calendar con Meet (Claude lo genera al dar la fecha) →
   copiar `meet_link` y `add_to_calendar_link` a la ficha.
3. Crear el Google Form de inscripción y ubicar su Sheet en la carpeta del invitado
   en Drive → copiar `sheet_id` y ajustar `columnas` con los títulos EXACTOS de las
   preguntas del Form.
4. Copiar `yauto-sas.example.json` a `<slug>.json`, poner `activo: true`.
5. Desplegar los scripts al VPS (`/root/crm-scripts/`) y añadir las líneas de cron.

## Requisitos / verificación en el VPS

- **Scope de Sheets: NO hace falta re-consentir** (verificado 2026-07-14). El token
  del VPS ya tiene `https://www.googleapis.com/auth/drive` completo, que la Sheets API
  acepta para lectura. El bloqueante real es OTRO: **la Google Sheets API está
  DESHABILITADA en el proyecto de Google Cloud** (326592234016). Hay que habilitarla
  (1 clic en la consola, mismo patrón que Calendar/Drive/Tasks):
  https://console.cloud.google.com/apis/library/sheets.googleapis.com?project=326592234016
  Mientras esté deshabilitada, `leer_sheet` devuelve HTTP 403 (SERVICE_DISABLED).
- Ejecutar `python3 -m unittest test_webinar_lib` en el VPS (debe dar 15 OK).
- Prueba de humo: con un Sheet de pruebas y `activo:true`, correr `webinar_intake.py`
  a mano y confirmar en el CRM el contacto `fuenteLead=WEBINAR` y la llegada de E2.
- Confirmar que los títulos de columna del Form casan con `columnas` (si no, esos
  campos llegan vacíos; el email es obligatorio y filtra las filas sin correo).

## Fuera de alcance (fases siguientes)

- **E1 aviso masivo a toda la lista de marketing:** no hay motor de envío masivo.
  En evaluación: usar HubSpot (motor de email marketing propio) o Brevo/Mailchimp.
- **Nurturing (E7).**
- Migración futura a landing en Astro con endpoint `/intake/webinar` (Opción B).
- Registro de asistencia real (quién asistió) para segmentar E6.
