# Diseño — Write-back de cotizaciones al CRM (Etapa 2)

**Fecha:** 2026-07-21
**Estado:** Diseño aprobado por Viviana, pendiente de plan e implementación
**Contexto:** La Etapa 1 de `/cotizar` ya genera el deck. Falta cerrar el ciclo: que al enviar
la cotización queden en la oportunidad el **link del deck** y el **link del correo enviado**,
sin que nadie tenga que acordarse de pegarlos.

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
| Quién envía | Viviana **o el encargado del cliente** (Laura, Alejandra, Miguel) |
| Desde dónde | **Todos desde el buzón `info@carbonbox.app`**, eligiendo su nombre como remitente (*send-as* verificados) → el correo enviado queda en `info@`, que el token del servidor **sí puede leer** (`gmail.readonly`) |
| Cómo llega el deck | **Link de Drive en el correo** (no adjunto) |
| Dónde se archiva | Carpeta **`Leads`** (`13dvWmMahnoyl_xsAZohAGVHoA8vIdX5A`), con **una subcarpeta por empresa** (ya hay 25) |
| Carpeta no encontrada | **Preguntar cuál usar. NUNCA crear carpetas nuevas.** |

Notas del terreno:
- Los nombres de carpeta **no coinciden literalmente** con el CRM: "Fundacion Santa Fe de Bogota"
  vs "Fundación Santafé de Bogotá", "Area Andina" vs "Área Andina" → hay que normalizar.
- Ya existe un **duplicado**: "Hotel Waya" y "Hotel Waya Guajira". Por eso la regla de preguntar.
- Los **transcripts** se archivan en otro árbol (`CMR/{Empresa}/`), no en `Leads/`. El material
  de un cliente queda partido en dos sitios; se acepta por ahora (unificarlo es otro trabajo).

---

## 3. Componente A — Deck a Drive y al CRM (en la skill `/cotizar`)

Corre en el PC de Viviana al aprobar la cotización, que es donde está el archivo y donde ya
hay acceso a Drive.

1. **Ubicar la carpeta** de la empresa dentro de `Leads/`:
   - Comparar normalizando (minúsculas, sin tildes, sin puntuación).
   - **Exactamente 1 coincidencia** → usarla.
   - **0 o más de 1** → mostrarle a Viviana las candidatas y **preguntar cuál usar**.
     No crear carpetas bajo ninguna circunstancia.
2. **Subir el PDF** del deck a esa carpeta y obtener su link.
3. **Escribir en el CRM** llamando a `registrar-cotizacion.js` con un flag nuevo
   `--link-cotizacion <url>`; el script pasa a llenar además:
   - `linkCotizacion` ← link del deck (label: `Cotización`)
   - `planCarbonbox` ← el plan (hueco actual)
   - y lo que ya hacía: etapa, monto y nota.

## 4. Componente B — Capturar el correo enviado (automático, en el servidor)

Como el correo lo manda una persona a mano, el sistema lo busca después. Corre **dentro del
Revisor de seguimientos** (cada 3 h), como una pasada más.

Para cada oportunidad en `PROPUESTA_ENVIADA`, con `linkCorreoEnviado` vacío y `linkCotizacion`
lleno:

1. Buscar en el buzón `info@` mensajes **enviados** (`in:sent`) al correo del contacto **que
   contengan el link del deck** en el cuerpo.
2. Si aparece exactamente uno (o varios: tomar el más antiguo, que es el envío original) →
   guardar el permalink `https://mail.google.com/mail/u/0/#all/<threadId>` en `linkCorreoEnviado`
   (label: `Correo enviado`).
3. Si no aparece → **no escribir nada** y reintentar en la siguiente pasada.

**Por qué emparejar por el link del deck y no por destinatario:** a ese mismo contacto también
se le envían los **recordatorios de seguimiento** desde el mismo buzón. Buscar "el último correo
a este cliente" guardaría el recordatorio en vez de la cotización. El link del deck identifica
el correo correcto sin ambigüedad.

**Límite aceptado:** depende de que el deck viaje como **link de Drive**. Si alguna vez se manda
como adjunto, no habrá con qué emparejar y el campo quedará vacío — el sistema no adivina.

---

## 5. Fuera de alcance (YAGNI)

- Que el sistema **envíe** el correo de cotización: lo manda una persona, y así se queda.
- Versiones v2/v3 del deck y su historial.
- Unificar los árboles `Leads/` y `CMR/` de Drive.
- Asociar automáticamente los correos a los contactos dentro de Twenty (limitación conocida
  del sync de Gmail; es un trabajo aparte).

## 6. Riesgos

- **Emparejar empresa ↔ carpeta**: los nombres difieren y hay duplicados. Mitigado preguntando
  y no creando carpetas.
- **Falso positivo del correo**: mitigado emparejando por el link del deck, no por destinatario.
- **Token local**: `registrar-cotizacion.js` usa un token en disco (`token crm.txt` / `.env`);
  no debe entrar al repo ni pegarse en el chat. Ya está en `.gitignore`.
