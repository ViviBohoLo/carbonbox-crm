# Diseño — Write-back de cotizaciones al CRM (Etapa 2)

**Fecha:** 2026-07-21
**Estado:** Diseño aprobado por Viviana, pendiente de plan e implementación
**Contexto:** La Etapa 1 de `/cotizar` ya genera el deck. Falta cerrar el ciclo: subir el deck,
enviar la cotización al cliente y dejar en la oportunidad el **link del deck** y el **link del
correo enviado**, sin que nadie tenga que acordarse de pegarlos.

---

## 1. Estado actual

`tools/cotizar/Generadores/registrar-cotizacion.js` (corre en el PC de Viviana, con token local
contra `crm.carbonbox.app/graphql`) hoy hace:

- busca o crea la **Empresa** (y le guarda el `nit`),
- busca una oportunidad abierta de esa empresa o crea una nueva,
- la mueve a **`PROPUESTA_ENVIADA`** y le pone el `amount`,
- agrega una **nota** con servicio, plan, NIT, precio y fecha.

**Lo que falta:** no llena `linkCotizacion`, no llena `linkCorreoEnviado`, y **tampoco llena
`planCarbonbox`** — el plan solo queda escrito en el texto de la nota, no en el campo. Además
no está integrado a la skill: es un comando aparte que hay que acordarse de correr.

Campos destino (ya existen en Opportunity): `linkCotizacion` (LINKS, id `a4bc4596`),
`linkCorreoEnviado` (LINKS, id `4f6e24bd`), `planCarbonbox` (SELECT).
⚠️ Los campos LINKS de Twenty son compuestos: se escriben como
`{ primaryLinkUrl: "…", primaryLinkLabel: "…" }`.

## 2. Cómo trabaja el equipo (confirmado con Viviana, 2026-07-21)

| Tema | Realidad |
|---|---|
| Quién firma el envío | Viviana **o el encargado del cliente** (Laura, Alejandra, Miguel) |
| Buzón | Todos operan sobre `info@carbonbox.app`; los cuatro nombres son *send-as* verificados, así que el sistema puede enviar **como cualquiera de ellos** |
| Cómo llega el deck | **Link de Drive en el correo** (no adjunto) |
| Dónde se archiva | Carpeta **`Leads`** (`13dvWmMahnoyl_xsAZohAGVHoA8vIdX5A`), con **una subcarpeta por empresa** (ya hay 25) |
| Carpeta no encontrada | **Preguntar cuál usar. NUNCA crear carpetas nuevas.** |

Notas del terreno:
- Los nombres de carpeta **no coinciden literalmente** con el CRM: "Fundacion Santa Fe de Bogota"
  vs "Fundación Santafé de Bogotá", "Area Andina" vs "Área Andina" → hay que normalizar.
- Ya existe un **duplicado**: "Hotel Waya" y "Hotel Waya Guajira". De ahí la regla de preguntar.
- Los **transcripts** se archivan en otro árbol (`CMR/{Empresa}/`), no en `Leads/`. El material
  de un cliente queda partido en dos sitios; se acepta por ahora.

---

## 3. Componente A — Deck a Drive y al CRM (en la skill `/cotizar`)

Corre en el PC de Viviana al aprobar la cotización, que es donde está el archivo y donde ya
hay acceso a Drive.

1. **Ubicar la carpeta** de la empresa dentro de `Leads/`:
   - Comparar normalizando (minúsculas, sin tildes, sin puntuación).
   - **Exactamente 1 coincidencia** → usarla.
   - **0 o más de 1** → mostrar las candidatas y **preguntarle a Viviana cuál usar**.
     No crear carpetas bajo ninguna circunstancia.
2. **Subir los dos archivos** a esa carpeta: el **PDF** (lo que ve el cliente) y el **PPTX**
   (el editable, para poder retomarlo después).
3. **Escribir en el CRM** vía `registrar-cotizacion.js` ampliado:
   - `linkCotizacion` ← link del **PDF** (label `Cotización`)
   - `planCarbonbox` ← el plan (hueco actual)
   - y lo que ya hacía: etapa `PROPUESTA_ENVIADA`, monto y nota.
4. **Redactar el correo** para ese cliente (usando el contexto de la reunión) y guardarlo en el
   campo nuevo **`borradorCorreo`** (TEXT) de la oportunidad.
5. **Entregarle a Viviana el link** de la página de confirmación (firmado con HMAC, igual que
   los recordatorios de seguimiento).

**Por qué un campo para el borrador:** la skill redacta en el PC de Viviana, pero la página la
sirve el servidor. El campo es el puente: la skill ya tiene permiso de escritura en el CRM, no
hace falta endpoint nuevo ni compartir secretos, y de paso el borrador queda visible en el CRM.

## 4. Componente B — Enviar la cotización (página de confirmación)

Misma mecánica que los recordatorios de seguimiento (`/seguimiento`), en el mismo servidor
(`intake_server.py`, expuesto por Caddy). Ruta nueva: `/cotizacion`.

La página muestra:

| Elemento | Detalle |
|---|---|
| **Para** | El contacto de la oportunidad (del CRM), no editable |
| **CC** | Campo libre, para sumar personas que no están en el CRM |
| **Remitente** | Lista para elegir: Viviana · Laura · Alejandra · Miguel |
| **Asunto** | Estándar y limpio: `Cotización CarbonBox — {Empresa}` (editable) |
| **Mensaje** | El borrador que redactó la skill, **editable** |
| **Botón** | «Confirmar y enviar» — lo único que envía |

Al confirmar:
1. Envía por Gmail API como el remitente elegido (con copia a los CC).
2. Guarda en `linkCorreoEnviado` el permalink del mensaje enviado
   (`https://mail.google.com/mail/u/0/#all/<threadId>`, label `Correo enviado`).
3. Limpia `borradorCorreo` (ya se usó).

**Regla de oro:** este correo va a un cliente. El GET solo muestra; **nada se envía sin el
botón**. Mismo criterio que los recordatorios de seguimiento.

**Por qué enviar y no buscar:** la alternativa era que una persona lo enviara a mano y el
sistema lo buscara después en el buzón. Se descartó: al mismo contacto también se le mandan
recordatorios de seguimiento desde el mismo buzón, así que emparejar "el último correo a este
cliente" podía guardar el recordatorio en vez de la cotización. Enviándolo nosotros, el link es
exacto por construcción.

---

## 5. Fuera de alcance (YAGNI)

- Versiones v2/v3 del deck y su historial.
- Unificar los árboles `Leads/` y `CMR/` de Drive.
- Asociar automáticamente los correos a los contactos dentro de Twenty (limitación conocida
  del sync de Gmail; trabajo aparte).
- Adjuntar el PDF al correo: va como link de Drive.

## 6. Riesgos

- **Emparejar empresa ↔ carpeta**: los nombres difieren y hay duplicados. Mitigado preguntando
  y no creando carpetas.
- **Permisos del link de Drive**: si la carpeta no es visible para el cliente, el link no le
  sirve. El flujo debe **avisar** qué permiso quedó y dejar que Viviana lo ajuste; no cambiar
  permisos de compartición automáticamente.
- **Token local**: `registrar-cotizacion.js` usa un token en disco (`token crm.txt` / `.env`);
  no debe entrar al repo ni pegarse en el chat. Ya está en `.gitignore`.
- **Borrador viejo**: si se genera una cotización y no se envía, `borradorCorreo` queda con
  texto de esa vez. Se sobrescribe en la siguiente corrida y se limpia al enviar.
