# Diseño: Webhook directo del formulario web → CRM CarbonBox

**Fecha:** 2026-07-06
**Estado:** Aprobado (diseño)
**Autor:** Claude + Viviana

## Objetivo

Que el formulario de contacto de `carbonbox.app` cree el lead **directo** en el CRM
(Twenty, en `https://crm.carbonbox.app`) en tiempo real, **jubilando HubSpot** del flujo.
Hoy el formulario postea a HubSpot y un cron (`hubspot_bridge.py`) sondea cada 5 min.

## Estado actual

- **Formulario:** `carbonbox-web/src/pages/index.astro` (Astro, desplegado en Vercel).
  Un `<script>` intercepta el submit y hace `fetch` POST (JSON) a la API de HubSpot Forms
  (`api.hsforms.com/submissions/v3/integration/submit/23967833/64b92eab-...`).
  Campos: `firstname, lastname, email, mobilephone, company, jobtitle, city, necesidad,
  describenos_cual_es_tu_necesidad` + opt-in de comunicaciones. Al éxito redirige a `/gracias`.
- **Puente actual:** `/root/crm-scripts/hubspot_bridge.py` en el VPS (cron cada 5 min). Crea
  Empresa (dedup) + Contacto (fuente WEB) + Oportunidad (LEAD_CAPTURADO) + Nota con el mensaje.
  Enriquecimiento: dominio desde email corporativo, país por indicativo telefónico (default CO),
  ciudad → dirección de la empresa. El WF1 del CRM crea la tarea de primer contacto; el
  notificador avisa por email.

## Enfoque elegido

**Endpoint propio en el VPS que reutiliza la lógica ya probada del puente.** No se reescribe
la lógica de creación/enriquecimiento; se refactoriza `hubspot_bridge.py` para separar:
(a) la obtención del lead (hoy: sondeo HubSpot) de (b) la creación en el CRM (reutilizable).
El endpoint nuevo llama a (b) con el payload del formulario.

Alternativas descartadas:
- **Workflow nativo de Twenty (webhook trigger):** reimplementar dedup + enriquecimiento en el
  builder no-code de Twenty es frágil; además CORS del webhook es incierto.
- **Función serverless en Vercel:** obligaría a reescribir el enriquecimiento en JS. Se evita.

## Componentes

### 1. Servicio de intake (VPS)
- Servicio HTTP pequeño en Python (stdlib `http.server`, sin dependencias nuevas), escucha en
  `127.0.0.1:8088`. Corre como servicio **systemd** (`carbonbox-intake`), arranque automático.
- Recibe `POST /intake` con el JSON del formulario. Valida campos requeridos.
- Reutiliza `crm_lib.py` + la función de creación extraída de `hubspot_bridge.py` para crear
  Empresa + Contacto (fuente WEB) + Oportunidad (LEAD_CAPTURADO) + Nota.
- El token del CRM se lee de `/root/.twenty_api_token` (server-side; nunca va al navegador).
- Responde `200 {ok:true}` en éxito, `4xx` en validación, `5xx` en fallo de CRM.

### 2. Exposición vía Caddy
- Ruta en el Caddyfile: `handle /intake*` → `reverse_proxy 127.0.0.1:8088`.
- Cabeceras **CORS**: `Access-Control-Allow-Origin: https://carbonbox.app` (+ manejo de
  preflight `OPTIONS`). El resto del sitio del CRM sigue igual.

### 3. Anti-spam (reponer lo que daba HubSpot)
- **Honeypot:** campo oculto (ej. `website`) en el form; si viene lleno → descartar (bot).
- **Rate limit** simple por IP en el servicio (ej. máx N envíos/hora por IP).
- Sin captcha (mantiene la UX limpia; volumen B2B bajo).

### 4. Cambio en el formulario (`index.astro`)
- Agregar el campo honeypot oculto.
- Cambiar el `ENDPOINT`/lógica del `fetch`: enviar el payload del formulario a
  `https://crm.carbonbox.app/intake`.
- **Rollout en paralelo:** durante la transición, enviar TAMBIÉN a HubSpot (best-effort, sin
  bloquear la redirección a `/gracias`). Tras verificar, quitar HubSpot.
- Conservar diseño, validación (`reportValidity`), estados del botón y redirección a `/gracias`.

## Flujo de datos

```
Navegador (carbonbox.app)
  --POST JSON /intake-->  Caddy (crm.carbonbox.app, CORS)
                            --> servicio intake (127.0.0.1)
                                  --> valida + honeypot + rate limit
                                  --> crm_lib: Empresa+Contacto+Oportunidad+Nota (Twenty API)
                                  <-- 200 {ok:true}
  <-- 200 --  redirige a /gracias
(en paralelo, transición) Navegador --POST--> HubSpot (best-effort)
```

## Mapeo de campos (form → CRM)

| Form | CRM |
|------|-----|
| firstname, lastname | Person.name |
| email | Person.email (+ dominio → Company si corporativo) |
| mobilephone | Person.phone (+ país por indicativo, default CO) |
| company | Company.name (dedup por nombre/dominio) |
| jobtitle | Person.jobTitle |
| city | Company address (ciudad) |
| necesidad | Nota (primera línea: "Necesidad: …") |
| describenos... | Nota (cuerpo del mensaje) |
| (implícito) | Person.fuenteLead = WEB; Opportunity.stage = LEAD_CAPTURADO |

## Manejo de errores

- Validación/honeypot fallidos → `400`, sin crear nada; el form muestra el mensaje de error existente.
- Fallo al crear en el CRM → `500`; **durante el paralelo**, HubSpot queda como respaldo del lead.
  Log en el VPS (`/var/log/carbonbox-intake.log`) para diagnóstico.
- CORS preflight (`OPTIONS`) respondido correctamente.

## Pruebas

- Unidad: función de creación con payload de ejemplo (dedup, país, dominio) — sin tocar datos reales
  (usar un email/empresa de prueba y luego limpiar, o mock del API).
- Integración: `curl` al endpoint con payload válido → verifica Empresa+Contacto+Oportunidad+Nota
  creados en el CRM; honeypot lleno → descartado; campos faltantes → 400.
- E2E: envío real desde el formulario en preview de Vercel → lead aparece en el CRM; WF1 crea tarea.

## Rollout / cutover

1. Desplegar el servicio intake + ruta Caddy en el VPS; probar con `curl`.
2. Cambiar el form a enviar a AMBOS (CRM + HubSpot); desplegar preview en Vercel.
3. Envío de prueba real → confirmar lead en el CRM.
4. Promover a producción (Vercel).
5. Tras días en paralelo sin fallos: quitar HubSpot del form; **desactivar el cron
   `hubspot_bridge.py`** en el VPS (renombrar la línea del cron).

## Fuera de alcance (YAGNI)

- Captcha / reCAPTCHA (solo si el spam lo amerita después).
- Reescribir el formulario o su diseño.
- Migrar históricos de HubSpot (ya se hizo la migración inicial).
- Webhook nativo de Twenty.

## Dependencias / notas

- El servicio intake corre junto a los contenedores del CRM en el VPS (mismo `localhost:3000`).
- Requiere que `carbonbox-web` se despliegue a Vercel (repo git local con acceso).
- Puerto interno del intake: `127.0.0.1:8088` (solo local; Caddy lo expone hacia afuera).
