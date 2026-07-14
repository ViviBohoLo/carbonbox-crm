# Segmentación de contactos por origen y marketing — Diseño

**Fecha:** 2026-07-07
**Estado:** Aprobado (Viviana)
**Contexto:** CRM CarbonBox (Twenty) en producción `https://crm.carbonbox.app`. Ver
memorias `funnel-carbonbox-config` y `carbonbox-vps`.

## Problema

Hoy el workflow de bienvenida (`👋 Contacto nuevo → email de bienvenida`, id
`5a4c0efa-…`) dispara en `person.created` con el único filtro `email IS_NOT_EMPTY`.
Es decir, **cualquier** contacto nuevo con correo recibe el email "gracias por
escribirnos — agenda tu asesoría", sin importar de dónde venga.

Eso es incorrecto: no todas las personas del CRM son leads comerciales. CarbonBox
tendrá listas de asistentes a webinars, contactos de eventos presenciales y contactos
importados que solo quieren recibir información (guías, eventos) y **no** pidieron una
asesoría comercial. Enviarles el "agenda tu cita" es molesto y fuera de lugar.

## Principio central

**Una _Persona_ en el CRM es solo un contacto. Lo que la mete al funnel de ventas es
que exista una _Oportunidad_ asociada.** Esto ya es así hoy: el workflow de primer
contacto (`① Lead nuevo → primer contacto`, id `dd2344c8-…`) dispara en
`opportunity.created`, no en `person.created`.

De ese principio se derivan **tres comportamientos independientes** que le pueden pasar
a un contacto:

1. **Entra al funnel** → existe una Oportunidad → se crea la tarea de primer contacto
   (WF1). Da igual el origen del contacto.
2. **Recibe la bienvenida automática** ("agenda tu asesoría") → **solo si
   `fuenteLead = WEB`** (llenó el formulario comercial de la web; él sí lo pidió).
3. **Recibe marketing** (guías, eventos) → solo si `suscritoMarketing = true`.

Los tres son ortogonales: un asistente a webinar puede estar suscrito a marketing y NO
entrar al funnel; un contacto de evento que marcó "me interesa la huella de carbono"
entra al funnel aunque no venga de la web.

## Modelo de datos (dos ejes en Persona)

- **`fuenteLead`** (SELECT, ya existe con taxonomía completa; id
  `1ccda2a6-1a51-4a9f-a042-15c4345d5292`) — origen del contacto. Opciones que YA
  existen: `WEB` (Web formulario), `WEBINAR`, `FREEMIUM`, `REFERIDO`, `ALIADO_B2B`,
  `LINKEDIN_ABM`, `OTRO`. Los 1225 migrados están en `OTRO`.
  - **No hay que crear WEBINAR ni REFERIDO — ya existen.** El único origen que Viviana
    mencionó y no está es `EVENTO` (evento presencial); es opcional y se agrega en 10s
    desde la UI (Settings → Person → fuenteLead → add option) cuando haga falta.
- **`suscritoMarketing`** (BOOLEAN, nuevo) — ¿recibe correos de marketing?
  - Default del campo: `true` (cubre importados y creación manual).
  - Para leads **WEB**: se setea explícitamente desde el checkbox de consentimiento
    del formulario ("Acepto recibir otras comunicaciones de CarbonBox"), no del default.
    El formulario web ya tiene ese checkbox (2º, opcional); el 1º ("Acepto permitir
    almacenar y procesar mis datos", obligatorio) es el consentimiento de datos que
    habilita el contacto comercial.

## Comportamiento por vía de entrada

| Vía de entrada | `fuenteLead` | ¿Entra al funnel? | Bienvenida auto | Marketing |
|---|---|---|---|---|
| Formulario web comercial | `WEB` | Sí (el intake crea la Oportunidad) | **Sí** | según checkbox 2 del form |
| Formulario webinar/evento *(futuro)* | `WEBINAR`/`EVENTO` | Solo si marca interés comercial | No → tarea a ventas | `true` |
| Manual por el equipo (amigo/referido) | `REFERIDO` | El equipo decide: crea la Oportunidad si aplica | No | a criterio |
| Importados HubSpot | `OTRO` | No | No | `true` (se marca en lote) |

### Caso "amigo referido" (planteado por Viviana)
El equipo crea la **Persona** con sus datos (`fuenteLead = REFERIDO`) → queda como
contacto, sin funnel y sin correo automático. Si quiere que entre al funnel comercial,
le crea una **Oportunidad** (un clic, arrastrándola al pipeline) → dispara la tarea de
primer contacto (WF1) y el equipo lo contacta personalmente. La bienvenida automática
NO le llega (no la pidió). Control total, sin sorpresas.

## Cambios en scope (esta etapa)

1. **Filtro en el workflow de bienvenida** (`5a4c0efa-…`, versión activa `523b1309-…`,
   FILTER step `f9d7c224-…`): agregar una segunda condición en el mismo grupo (AND):
   `fuenteLead` **es exactamente** `WEB`. ⚠️ NO usar operando CONTAINS: `WEBINAR`
   contiene `WEB` → usar match exacto (IS). Tapa el hueco.
   → Requiere token de usuario (30 min) o edición en el builder de la UI.
2. ~~Ampliar opciones de `fuenteLead`~~ **Ya existen** WEBINAR/REFERIDO/etc. (ver arriba).
   Solo opcional: agregar `EVENTO` desde la UI si se necesita.
3. **Nuevo campo `suscritoMarketing`** (boolean, default `true`) en Persona
   (`createOneField`, endpoint `/metadata`, con la API key). Objeto Person id
   `16790c1d-680e-488c-8cef-a69feb631305`.
4. **Marcar en lote los ~1225 contactos existentes** con `suscritoMarketing = true`
   (agregar un campo no rellena registros viejos). → Mutación de datos (token API actual).
5. **`lead_intake.py`**: setear `suscritoMarketing` en el contacto WEB **desde el valor
   del checkbox 2** del formulario (además del `fuenteLead = "WEB"` que ya pone).
   Requiere que el formulario (`carbonbox-web/index.astro`) **envíe ese valor** al
   `/intake` (hoy no lo manda) y que `mapear_form` lo lea. Verificar que el default del
   campo cubra la creación manual sin sorpresas.
6. **Texto del checkbox 2 en la web** *(cambio de copy, lo hace Viviana en `carbonbox-web`)*:
   reemplazar "Acepto recibir otras comunicaciones de CarbonBox." por algo más claro,
   p.ej. "Acepto recibir novedades, guías y contenido de CarbonBox." Opcional para la
   función; mejora la claridad del consentimiento.

## Fuera de scope (etapas futuras)

- Formularios de webinar/evento (endpoints/intake nuevos) que seteen origen +
  suscripción y decidan si crean Oportunidad según interés comercial.
- Motor de envío de marketing (guías, eventos) a los suscritos. Hoy no existe workflow
  ni herramienta de envío masivo; `suscritoMarketing` solo captura el consentimiento.

## Verificación

- Crear un contacto de prueba con `fuenteLead = WEBINAR` → **no** recibe bienvenida.
- Crear un contacto de prueba con `fuenteLead = WEB` → **sí** recibe bienvenida.
- Crear una Oportunidad manual sobre un contacto `REFERIDO` → dispara tarea de primer
  contacto (WF1), **sin** email de bienvenida.
- Confirmar que los 1225 contactos quedan `suscritoMarketing = true`.
- (Todas las pruebas de envío de correo a direcciones controladas — regla: nunca correos
  reales a clientes sin aprobación de Viviana.)

## Riesgos / notas

- El cambio del workflow toca un automatismo que hoy envía correos reales. Probar el
  draft con `runWorkflowVersion` (payload simulado a una dirección propia) antes de
  activar. Ver `twenty-workflow-api`.
- El valor **default** de `fuenteLead` es `null` (verificado 2026-07-07) → un contacto
  cargado a mano en la UI queda sin fuente y NO matchea el filtro `IS WEB` → NO recibe
  bienvenida. Riesgo descartado.
