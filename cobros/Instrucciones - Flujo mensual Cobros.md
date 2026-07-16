# Instrucciones — Flujo mensual de Cobros (CarbonBox / KIMSA)

SOP para actualizar la vista **Cobros** en Twenty cada mes con datos de Helisa (pagos/cartera) y facturación.
Última actualización: 2026-07-09

---

## PASO 0.A — Verificar accesos de CarbonBox vía Composio (1 min, no saltarse)

Las cuentas de CarbonBox (info@carbonbox.app) están conectadas por **Composio** y persisten entre sesiones: Drive alias `carbonbox` (account `googledrive_toxin-indone`) y Gmail alias `carbonbox` (account `gmail_hostel-bois`).
1. Ejecutar `COMPOSIO_MANAGE_CONNECTIONS` acción **list** para `googledrive` y `gmail` → ambos alias `carbonbox` deben estar **active**.
2. Si alguna está caída: acción **add** (alias `carbonbox`) → Claude entrega un link → Viviana lo abre y autoriza con **info@carbonbox.app**.
3. Estas conexiones NO se borran (ni en el panel de Composio ni en los conectores de Claude); el paso de facturas/PDFs del flujo depende de ellas.

## PASO 0.B — Conectar el navegador correcto (IMPORTANTE, no saltarse)

Problema conocido: si hay **varias ventanas/instancias de Chrome** abiertas, la sesión de Claude se ata a una ventana que a veces queda **fuera de la vista** de Viviana (off-screen), y no coincide con la que ella ve. Síntoma: Claude ve una pantalla y Viviana ve otra; "no aparece el navegador".

**Procedimiento que SÍ funciona:**
1. Cerrar TODAS las ventanas de Chrome. Dejar una sola ventana de Chrome abierta y visible, con la extensión de Claude activa.
2. Claude lanza `switch_browser` (envía una solicitud de conexión a cada Chrome con la extensión).
3. En la ventana de Chrome que Viviana **sí ve**, aparece el aviso de la extensión → hacer clic en **"Connect"** (se le puede poner nombre, ej. "browser kimsa"). Hay ~2 minutos para hacerlo.
4. A partir de ahí, la sesión queda atada a esa ventana visible y Claude controla esa misma pestaña.

Regla de seguridad: **Claude no escribe contraseñas**. El login de Helisa (terminal + ADMINISTRADOR) lo hace siempre Viviana en la pestaña que Claude abre/controla.

---

## PASO 1 — Entrar a Helisa (lo hace Viviana)

1. Claude abre `https://terminal22.helisacloud.com/software/html5.html` en la pestaña que controla.
2. Viviana ingresa **Usuario de terminal** (Brinez.User1) y su clave → Ingresar.
3. Viviana ingresa el login **ADMINISTRADOR** dentro del software.
4. En "Aplicaciones", se abre **HELISA NIIF** (la app remota corre en su propia pestaña `html5.html`).

Nota técnica: Helisa es una **terminal remota HTML5** (imagen transmitida, no web). Claude opera por visión (pantallazo → clic). La ventana se re-escala sola, así que el filtrado fino por celda es frágil; ver el atajo del Paso 2.

---

## PASO 2 — Sacar la cartera del mes en Helisa

1. Empresa activa: **KIMSA - CLIMA, CONSERVACIÓN Y DESARROLLO S.A.S** (con K). KIMSA opera a CarbonBox; hay terceros que no son de CarbonBox, por eso hay que ubicar el cliente exacto.
2. Módulo **Cuentas por Cobrar** → **Informes de Cuentas por Cobrar** → **Movimiento por Deudor**.
3. En el cuadro de configuración:
   - Pestaña **Medio de salida**: Enviar a = **Pantalla**.
   - Pestaña **Clasificación**: marcar la casilla **"Todas las carteras"** (o Clientes) en el árbol de la izquierda. (El filtro por Nombre = cliente en la grilla es inestable en el canvas remoto; es más confiable generar todo y ubicar al cliente en el resultado.)
   - **Aceptar**.
4. Se genera **"Movimiento por deudor (01/MES/AAAA a 30/MES/AAAA)"**. Buscar el bloque del cliente.

Cada bloque de cliente trae: SALDO INICIAL, las **FV** (facturas de venta), **NC** (notas crédito, anulan facturas), **RC** (recibos de caja = pagos), y **SALDO FINAL**.

---

## PASO 3 — Interpretar (clave para no cometer errores)

- **FV** = factura emitida (facturación del mes).
- **NC** = nota crédito → **anula** una factura (NO es un pago; reduce lo facturado).
- **RC** = recibo de caja → **pago real** recibido del cliente.
- **SALDO FINAL** = lo que el cliente aún debe al cierre del mes.

---

## Configuración de la vista "💰 Cobros" (ya aplicada)
- **Filtro:** Stage IS [Cerrado Ganado, Renovación] → solo clientes ganados/facturables (excluye perdidos y en negociación).
- **Columnas visibles:** Name, Stage, ID corporativo o tributario, Estado de pago, Amount (contrato), Saldo, Valor pagado, Pagos (tarjeta de facturas).
- **Un solo lugar:** el detalle de cada factura (n°, USD/COP/TRM, fecha, estado, pago) vive en el objeto **Facturas** (columna Pagos), NO duplicado en la oportunidad. Se ocultaron de la vista los campos # Factura / Fecha de pago / Factura de la oportunidad.

## PASO 4 — Escribir en Twenty (por API, lo hace Claude)

**Llave de cruce:** SIEMPRE por **ID corporativo o tributario** (campo `idTributario` en Oportunidades), nunca por nombre. Ej. Cliente Ejemplo S.A.S. = NIT 900.000.000-0. Si el ID no cuadra → validación humana.

**Estructura en Twenty:**

Oportunidad (el contrato/cliente):
- `amount` = **valor del contrato en USD** (viene de la cotización aprobada; es lo proyectado, NO lo facturado).
- `idTributario` = NIT/RUC/Tax ID (llave).
- `valorPagado` (USD) y `saldo` (USD = saldo de cartera / facturado pendiente, según Helisa).
- `estadoPago` = Sin facturar / Facturado / Pagado / Vencido.

Objeto **Facturas** (un registro por factura/cuota):
- `numeroFactura` (ej. FEFA000), `fecha` (emisión), `moneda` (COP/USD).
- `valor` (Valor COP), `valorUsd` (Valor USD), `trm` (tasa) — **la TRM y el USD vienen escritos en la propia factura**.
- `estado` (Facturado/Pagado/Vencido/Anulado), `fechaPago`, `factura` (PDF), `mesCierre`, `oportunidad` (relación).

**Multi-moneda:**
- Clientes nacionales (ej. Cliente Ejemplo S.A.S.): se factura en **COP**; la factura indica el USD equivalente y la TRM. → moneda=COP, se llenan valor(COP)+valorUsd+trm.
- Clientes internacionales (ej. un cliente con sede en el extranjero): se factura **directo en USD**. → moneda=USD, se llena valorUsd (valor COP opcional/contable).

Reglas de escritura por mes:
- Cada **factura** emitida → registro en Facturas (estado Facturado).
- Cada **RC** (pago) → marcar la factura como Pagado + fechaPago; recalcular `valorPagado` y `saldo` en la oportunidad.
- **NC** (nota crédito) → marcar la factura Anulado (reduce lo facturado, no es pago).

---

## EJEMPLO — cómo leer un bloque de Movimiento por Deudor (genérico)

Cliente en Helisa: **Cliente Ejemplo S.A.S.** (moneda COP).
- SALDO INICIAL: $ 5.000.000
- FV 00000200 · 17/MES/AAAA · $ 700.000 (facturado)
- FV 00000201 · 18/MES/AAAA · $ 500.000 (facturado)
- NC 00000050 · 18/MES/AAAA · −$ 700.000 (anula FV200)
- RC 00000080 · 23/MES/AAAA · −$ 500.000 (**pago** de FV201)
- SALDO FINAL: $ 5.000.000

Lectura: en el mes se facturó $1.200.000; de eso, $700.000 se anuló con NC y $500.000 se pagó (RC). El saldo quedó igual porque el neto del mes fue 0.

### Ejemplo de resultado cargado en Twenty
- Oportunidad "Cliente Ejemplo S.A.S. - Nombre del Proyecto": idTributario 900.000.000-0, contrato USD 4.000, saldo USD 1.350, estado Facturado.
- Factura FEFA000 (Pago 1, 33%): moneda COP, Valor COP 5.000.000, Valor USD 1.350, TRM 3.700, estado Facturado, fecha AAAA-MM-DD.

### EJEMPLO — cliente internacional (caso USD)
- Un cliente facturado en dólares puede NO aparecer en la cartera en pesos (Movimiento por Deudor). Los clientes facturados en dólares se llevan en Helisa en un módulo aparte: **Cuentas por Cobrar › Otras Monedas**. Ahí está su cartera en USD.
- Procedimiento: entrar a "Otras Monedas" para sacar facturado/pagado/saldo del cliente en USD + su ID tributario, y cargar en Twenty (moneda=USD).
- Si "Otras Monedas" muestra "Total clientes sin movimiento .00" para un cliente → no tiene cartera en dólares pendiente; sus facturas previas ya están pagadas. Nada por cargar como saldo; si se quiere el histórico, correr el informe con el periodo correspondiente.

**Nota para el flujo:** el barrido mensual debe cubrir DOS carteras en Helisa → (1) Cuentas por Cobrar en pesos, informe **Movimiento por Deudor** (clientes nacionales) y (2) Cuentas por Cobrar › Otras Monedas, informe **Movimiento por Cliente** (clientes internacionales en USD).

**Importante para la automatización:** el informe por defecto trae **el mes en curso**, así que el flujo mensual NO necesita editar el campo de fecha (ese control es frágil en el canvas remoto). Solo se edita la fecha si se busca un mes histórico.

**Truco útil en el visor de informes:** para moverse entre páginas usar las flechas rojas ◀ ▶ de la barra (el scroll del mouse no avanza; el scroll SÍ funciona para bajar dentro de la misma página). Hay también un campo "Buscar".

**Aprendizajes de procedimiento (de corridas mensuales anteriores):**
- **Cambiar de empresa a KIMSA**: en la pantalla inicial, dos clics seguidos sobre el nombre (el doble clic a veces abre "Asentar Libros" por accidente → Escape y seguir). El encabezado debe decir "KIMSA…, Mes de AAAA".
- El **periodo activo de la empresa** define el rango por defecto de todos los informes (si la empresa quedó en el mes anterior, los informes salen sin tocar fechas). Verificar el mes del encabezado antes de correr.
- **NITs**: el informe "Directorio de Clientes" (Clasificación → Todas las carteras) lista NOMBRE + Identidad de todos los terceros; es la fuente para poblar idTributario.
- **Ojo con razones sociales distintas al nombre comercial:** algunos clientes aparecen en Helisa bajo una razón social legal distinta a la marca conocida (ej. la matriz corporativa), o facturan a través de un tercero intermediario con su propio NIT. Verificar bien por Directorio de Clientes antes de dar por "sin movimiento" a un cliente que no aparece por su nombre comercial.
- Los informes solo listan clientes CON movimiento; para saldos globales usar **Estado de Cartera → Estado General Corriente**.
- **Fuente de los PDFs de factura (CORREGIDO):** las FEFA se envían a los clientes desde el **Gmail de CarbonBox (info@carbonbox.app y cuentas @carbonbox.app)** — NO llegan a info@kimsa.co (ahí solo llegan facturas de proveedores). Buscar en SENT del correo CarbonBox por nombre del cliente o "factura".
- **Accesos vía Composio** (quedan activos entre sesiones): Google Drive "carbonbox" (info@carbonbox.app; carpeta Leads `13dvWmMahnoyl_xsAZohAGVHoA8vIdX5A`, una carpeta por cliente) y Gmail "carbonbox" (info@carbonbox.app). PASO NUEVO del flujo mensual: tras correr Helisa, buscar en ese Gmail las FEFA del mes, subir el PDF a la carpeta del cliente en Drive (GOOGLEDRIVE_UPLOAD_FROM_URL) y pegar el link en el campo factura de Twenty.
- **La numeración interna de Helisa coincide con las FEFA** (ej. FV 00000XXX = FEFAXXX) → el cruce factura Helisa↔FEFA es directo.
- Las facturas de clientes que facturan en **COP puro** NO traen USD/TRM impreso; solo las de contratos pactados en **USD** lo traen (el USD/TRM viene impreso directamente en esa factura).

## Notas de decisiones (resueltas)
- Llave = ID corporativo o tributario (no nombre). Nombre neutro para clientes de otros países.
- Contrato (USD, proyectado) vive en la oportunidad; Helisa solo tiene lo facturado y su saldo.
- TRM y USD salen de la propia factura (no se calculan).

## Documentos de factura (PDF) y Google Drive
- El **PDF vive en Google Drive**, en la carpeta del cliente (repositorio de documentos). NO se suben binarios al CRM.
- En Twenty, el campo **"PDF factura"** (objeto Facturas, tipo enlace) guarda el **link de Drive** a esa factura → conexión con un clic, sin duplicar.
- Estructura sugerida: dentro de la carpeta de cada cliente en Drive, una subcarpeta **"Facturas"**. Opcional: guardar en la oportunidad el link a la carpeta del cliente.
- No hace falta crear una rama/directorio de clientes en el CRM: Empresas/Oportunidades ya son los clientes; Drive es el archivador.
- **Pendiente de acceso:** la carpeta de Drive `13dvWmMahnoyl_xsAZohAGVHoA8vIdX5A` no es accesible desde la cuenta conectada (info@kimsa.co) — "no encontrada". Para que el agente enlace/lea PDFs en el flujo mensual, **compartir esa carpeta con info@kimsa.co**.
