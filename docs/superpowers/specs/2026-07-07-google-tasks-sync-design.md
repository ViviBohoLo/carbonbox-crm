# Recordatorios de tareas en el celular vía Google Tasks — Diseño

**Fecha:** 2026-07-07
**Estado:** Aprobado (Viviana)
**Contexto:** CRM CarbonBox (Twenty) en `https://crm.carbonbox.app`. Las tareas del funnel
(primer contacto, seguimientos, renovaciones) se crean asignadas a Viviana
(workspaceMember `f38776b9-a83b-47c6-8d84-0b32a662ac84`) pero viven solo en la web del
CRM. Ver [[carbonbox-vps]] y [[funnel-carbonbox-config]].

## Objetivo

Que las tareas del CRM le lleguen a Viviana como **recordatorios en el celular**, vía
**Google Tasks** (se ven en la app Google Tasks, en Gmail y en Google Calendar del
teléfono). Sincronización **en dos vías**: puede marcar hecho en el CRM o en el celular.

Además: los **avisos por correo de leads nuevos** y las **tareas** deben incluir la
**información de contacto de la persona** (nombre, correo, teléfono, empresa, necesidad),
no solo un resumen.

## Limitación conocida (aceptada)

La API de Google Tasks **solo guarda la FECHA de vencimiento, no la hora**. Los
recordatorios son a nivel de día ("vence hoy"), no a la hora exacta. Afecta solo a la
tarea de primer contacto (SLA 60 min), que igual se sincroniza pero como "vence hoy";
el resto (seguimientos en días, renovaciones) queda perfecto. Viviana lo acepta.

## Alcance

### 1. Enriquecer los avisos (rápido, independiente de Google Tasks)
- El correo de "lead nuevo desde la web" (lo envía `intake_server.py` vía el notificador)
  debe listar: **nombre y apellido, correo, teléfono, empresa, cargo, ciudad, necesidad**.
  Hoy solo manda `{nombre} {apellido} <{email}> — {empresa}` (sin teléfono).
- La misma info completa va en la **nota** de la oportunidad (ya incluye necesidad/mensaje;
  agregar teléfono/correo/cargo) para que quede visible desde la tarea.

### 2. Sincronización CRM ↔ Google Tasks (dos vías)
Un proceso en el VPS (cron cada 10 min, como el vigía) que reconcilia:
- **Qué se sincroniza:** todas las tareas **abiertas** (TODO / IN_PROGRESS) **asignadas a
  Viviana** en el CRM. Incluye la de primer contacto (SLA 60 min) → aparece como "vence hoy".
- **Lista destino:** la lista dedicada que Viviana ya creó, **"Llamada Lead-CMR"**
  (id `YUpOX0VGanZ2SE90YnpyVA`) en el Google Tasks de info@carbonbox.app. No ensucia la
  lista personal "My Tasks"; fácil de identificar lo sincronizado.
- **Contenido de cada Google Task:** título de la tarea del CRM; en las notas, la
  **info de la persona para poder llamar** (nombre, correo, **teléfono**, **empresa**,
  cargo, necesidad) + **link a la oportunidad** en el CRM; fecha de vencimiento = `dueAt`
  de la tarea (solo fecha). La empresa es clave: quien llama debe saber quién es y de
  dónde escribió.
- **Reglas de reconciliación (fuente de verdad por estado):**
  - Tarea CRM abierta sin equivalente en Google → crear Google Task, guardar el mapeo.
  - Tarea CRM completada o borrada → completar/borrar su Google Task.
  - Google Task marcada hecha (y la del CRM sigue abierta) → marcar la tarea del CRM `DONE`.
  - Cambió título/fecha en el CRM → actualizar la Google Task.
  - **Conflicto:** "completada gana" — si está hecha en cualquiera de los dos lados, queda
    hecha en ambos.
- **Estado/mapeo:** archivo JSON en el VPS (`gtasks_map.json`): `crmTaskId ↔ {googleTaskId,
  ultimoEstado}`, patrón idempotente igual a `hubspot_seen.json` / `renovacion_seen.json`.

## Componentes

1. **Auth de Google Tasks (una vez):** en el proyecto de Google Cloud "CarbonBox CRM"
   (tipo Interno): habilitar la **Google Tasks API** y crear un **OAuth client tipo
   "Aplicación web"** con redirect `http://localhost:9999/`. Flujo de una sola vez: Claude
   arma la URL de autorización (scope `.../auth/tasks`), Viviana hace clic en "Permitir"
   con info@carbonbox.app, el navegador redirige a localhost (no carga, pero el `code=` queda
   en la barra de direcciones), Viviana copia ese código y Claude lo canjea en el VPS por un
   **refresh token** que se guarda en `/root/.gtasks_token` (perms 600). El cron lo usa para
   sacar access tokens. Nota: token de app Interna no expira salvo revocación o 6 meses sin uso.
2. **`gtasks_sync.py`** (Python stdlib, en `crm-scripts/`): el reconciliador de dos vías.
   Reusa `crm_lib` para el CRM y llama a la Tasks API por HTTPS (urllib).
3. **`gtasks_auth.py`** (one-off, en `scripts-ops/`): el flujo de OAuth para obtener el
   refresh token.
4. **Cron:** `*/10 * * * *` en `/etc/cron.d/carbonbox-crm`, log en `/var/log/crm-gtasks.log`.

## Fuera de alcance (por ahora)
- Enriquecer el **cuerpo de la tarea del CRM** (la crea el workflow WF1; editar su plantilla
  necesita token de usuario). La info de la persona ya queda en la nota y en la Google Task;
  se puede hacer después si Viviana lo pide.
- Recordatorios con hora exacta (limitación de Google Tasks; si hiciera falta, se evaluaría
  Google Calendar como canal complementario).

## Verificación
- Crear una tarea de prueba asignada a Viviana → aparece en la lista "CRM CarbonBox" del
  Google Tasks con la info de la persona y la fecha.
- Marcarla hecha en el celular → en el próximo ciclo la tarea del CRM queda `DONE`.
- Completarla en el CRM → desaparece del celular.
- Enviar un lead de prueba por el formulario → el correo de aviso trae nombre, correo,
  teléfono, empresa, necesidad. (Pruebas de correo solo a direcciones propias.)

## Riesgos / notas
- La Tasks API descarta la hora del `due` → recordatorios a nivel de día.
- Rate limits de la Tasks API son holgados para este volumen (unas pocas tareas).
- El cron de dos vías corre cada 10 min → hay hasta 10 min de latencia entre marcar hecho
  en un lado y verse en el otro. Aceptable.
