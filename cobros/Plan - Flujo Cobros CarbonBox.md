# Flujo automático de Cobros — CarbonBox

Diagnóstico, arquitectura y plan de trabajo
Fecha: 2026-07-09

## 1. Objetivo

Automatizar la actualización mensual de la vista **Cobros** en el CRM Twenty, consolidando por cliente:

- **Facturación** — lo que se le facturó en el mes
- **Pagos** — lo que pagó en el mes
- **Saldo** — facturado menos pagado (acumulado)

Hoy esto se hace manual. La meta es que el flujo se dispare una vez al mes (ejecución manual) y complete el CRM automáticamente.

## 2. Las tres fuentes

### Twenty (CRM) — destino  ✅ CONECTADO Y DIAGNOSTICADO
Instancia: `https://crm.carbonbox.app/` — API GraphQL (`/metadata`, `/graphql`) y REST (`/rest`) funcionando con la API key.
Nota: la API no es alcanzable desde el shell (bloqueada por allowlist), así que se opera vía el navegador (extensión Chrome), que sí tiene acceso al mismo origen.

**Hallazgo clave:** "Cobros" NO es un objeto propio; es una **vista sobre el objeto Oportunidades** (Opportunities). No existe un objeto "Cobros" separado. Cada oportunidad = una relación/contrato con un cliente y ya trae los campos de cobro:

- `amount` (CURRENCY) — valor
- `estadoPago` (SELECT) — opciones: **Sin facturar / Facturado / Pagado / Vencido**
- `numeroFactura` (TEXT) — # Factura
- `linkFactura` (LINKS) — enlace a la factura
- `fechaPago` (DATE) — fecha de pago
- `vencimientoContrato` (DATE), `fechaEntradaEtapa` (DATE), `stage` (embudo de ventas)

**Limitación del modelo actual:** cada oportunidad guarda UN solo estado de pago (el último). No hay campo de "saldo" ni de "valor pagado/abono", y no hay histórico mensual: no se puede registrar factura de enero, factura de febrero, etc. sobre la misma oportunidad. → Decisión de diseño pendiente (ver sección 7).

**Piloto localizado:** oportunidad de ejemplo **"Cliente Ejemplo S.A.S. - Nombre del Proyecto"**, amount USD 4.000 (ejemplo), con estadoPago / numeroFactura / fechaPago vacíos.

### Helisa / ELISA (contable) — fuente de PAGOS
Acceso vía terminal remota HTML5 (`terminal22.helisacloud.com/.../html5.html`).
**Hallazgo clave:** no es una web normal, es la aplicación de escritorio de Helisa transmitida como imagen dentro del navegador. Por eso no se puede "leer el HTML"; hay que operar por visión (pantallazo → ubicar → clic) con Claude en Chrome. Es viable pero más lento y frágil, así que conviene documentar la ruta exacta de clics una sola vez y reutilizarla cada mes.
Sin API asequible → navegador es el camino correcto.

### FactorA (facturación) — REVISADO
Hallazgo al revisar el correo:
- `factoa.co` (`noreply@factoa.co`) genera **Documentos de Soporte** (compras a proveedores no obligados a facturar) — NO son los cobros a clientes.
- Las **facturas de venta a clientes** (los cobros) son la serie **FEFA**, emitidas vía Cadena (`notificacion@efacturacadena.com`). Ej.: el PDF de una factura tiene el formato "FEFA 000 Nombre Cliente.pdf", guardado en el correo con asunto "Factura [Cliente]".
- El conector de Gmail no permite descargar el binario del PDF adjunto; para leer el monto exacto hay que abrir el PDF por el navegador o tomarlo de Helisa.

**Insight clave:** Helisa (contable) es la fuente de verdad tanto de facturación (cuentas por cobrar / cartera) como de pagos (recaudos). Un reporte de **cartera / cuentas por cobrar por tercero** en Helisa entrega en un solo lugar: facturado, abonado y saldo por cliente. Esto puede volver innecesaria la extracción por correo para los montos (el correo serviría solo para adjuntar el PDF de la factura si se desea).

## 3. Arquitectura del flujo mensual

1. **Facturación** ← Gmail: buscar facturas de FactorA del mes XY, extraer datos.
2. **Pagos** ← Helisa: entrar a la terminal, abrir el estado de cuenta / reporte de pagos del cliente en el mes, leer valores por visión.
3. **Saldo** = facturado − pagado (calculado).
4. **Escritura** → Twenty vía API: actualizar/crear el registro del cliente en la vista Cobros.
5. **Verificación** → revisar que los valores escritos cuadren con las fuentes.

## 4. Decisiones tomadas

- Actualización de Twenty: **API nativa** (no navegador).
- Facturación FactorA: **desde el correo (Gmail)**.
- Alcance inicial: **piloto con 1 cliente**, validar, luego escalar a toda la cartera.
- Extensión de Claude en Chrome: **instalada** (para Helisa).

## 5. Pendientes para arrancar el piloto

- [ ] URL de la instancia Twenty + API key.
- [ ] Cliente que usaremos como piloto.
- [ ] Confirmar en Gmail el remitente/formato de las facturas de FactorA.
- [ ] Mapear en Helisa el reporte exacto de donde salen los pagos.

## 7. Decisión de diseño pendiente (clave)

El modelo actual (una oportunidad = un estado de pago) sirve para reflejar el **estado actual** de cada contrato, pero no guarda histórico mensual ni saldos parciales. Hay que decidir:

- **Opción A — Estado por oportunidad (usar lo que ya existe):** cada mes se actualiza `estadoPago`, `numeroFactura`, `fechaPago`, `linkFactura` sobre la oportunidad. Simple, sin construir nada nuevo. No conserva histórico ni maneja abonos/saldos numéricos.
- **Opción B — Histórico mensual (nuevo objeto "Facturas/Cobros"):** se crea un objeto nuevo relacionado a Oportunidad/Empresa, con un registro por factura/mes (facturado, pagado, saldo, fecha). Permite histórico y saldos, pero requiere construir el objeto y sus campos.

## 7b. Estructura creada en Twenty ✅

Decisión tomada: modelo con **objeto Pagos** (histórico de abonos, número de pagos ilimitado). Creado por API:

**Oportunidades — campos nuevos:**
- `valorPagado` (CURRENCY) — suma de pagos recibidos
- `saldo` (CURRENCY) — valor del contrato (`amount`) menos `valorPagado`
- `pagos` (RELATION) — lista de pagos asociados

**Objeto nuevo "Pagos"** (`pago` / `pagos`), un registro por abono:
- `valor` (CURRENCY), `fecha` (DATE), `numeroFactura` (TEXT), `factura` (LINKS), `mesCierre` (DATE)
- `oportunidad` (RELATION → Opportunity)

Flujo de cierre mensual por cliente: detectar pagos del mes (Helisa) → crear un registro en Pagos → recalcular `valorPagado` y `saldo`, y ajustar `estadoPago` (Facturado/Pagado/Vencido) en la oportunidad.

## 8. Nota de seguridad

Las credenciales de Helisa están hoy en un .txt en texto plano dentro de la carpeta. Funciona, pero cualquiera con acceso al equipo o a la carpeta las ve. Al montar el flujo definitivo conviene definir un manejo más seguro.
