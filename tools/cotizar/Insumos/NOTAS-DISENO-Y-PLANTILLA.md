# Plantilla de cotizaciones CarbonBox — memoria de diseño (VERSIÓN VIGENTE)

> Última actualización: 22 de junio de 2026 — **paleta y fuentes alineadas al Sistema de diseño CarbonBox (v2)** y carpeta reorganizada. Referencia para reproducir la cotización SIEMPRE igual.
> Estado: versión aceptable; se irá ajustando con el tiempo.

---

## 0. Estructura de carpetas (reorganizada · 2 jul 2026)

```
Automatización de cotizaciones CarbonBox/
├── Cotizaciones/                 ← SALIDAS (entregables), una carpeta por cliente
│   ├── <Cliente>/                    cada uno: .pptx + .pdf + .md
│   └── _Plantilla/                   plantilla base (cotizacion-plantilla.pptx)
├── Generadores/                  ← scripts ACTIVOS del flujo (correr DESDE aquí)
│   ├── calcular-precio.py             precio por sector/tamaño/plan (+ATICA)
│   ├── generador-cover.py            fondo de portada (isotipo GIRADO)
│   ├── generador-ilustraciones-servicios.py   ilustraciones s6_ill*.png
│   ├── generador-pptx-pepsico.js     ⭐ generador VIGENTE / plantilla de referencia
│   ├── generador-pptx-waya.js        referencia para casos CON Fase 2
│   └── _legado/                       scripts obsoletos (NO usar)
├── Insumos/                      ← instrucciones, reglas de precio, textos fijos,
│                                    casos de éxito, intake, filosofía, ESTA memoria
├── Logos/                        ← logos oficiales (no redibujar)
├── Recursos/                     ← imágenes/íconos/ilustraciones/fotos equipo ACTIVAS
│   ├── _backup/                      respaldos (cover_bg_original.png)
│   └── _legado/                      variantes de imagen no usadas por el flujo
├── Sistema de diseño CarbonBox/  ← guía de marca (HTML + guidelines)
└── package.json · package-lock.json · node_modules/ · .claude/
```

Los generadores resuelven solos sus rutas (`Recursos/`, `Logos/`) y escriben en `Cotizaciones/<Cliente>/`. Correr **desde `Generadores/`**.

### Mapa del flujo — qué archivo necesito y para qué

| Paso | Archivo(s) | Para qué |
|------|-----------|----------|
| 1. Reglas y contenido | `Insumos/instrucciones.md`, `reglas-precio.md`, `textos-fijos.md`, `casos-exito.md` | Estructura de las 13 slides, precios y textos por plan/sector |
| 2. Calcular precio | `Generadores/calcular-precio.py` | `--sector … --empleados … [--plan …]` → precio + ATICA |
| 3. Fondo de portada | `Generadores/generador-cover.py` → `Recursos/cover_bg.png` | Solo si hay que regenerar el fondo (isotipo girado) |
| 4. Ilustraciones | `Generadores/generador-ilustraciones-servicios.py` → `Recursos/s6_ill*.png` | Solo si cambian las ilustraciones de "soluciones" |
| 5. Generar deck | `Generadores/generador-pptx-pepsico.js` (copiar y adaptar datos del cliente) | Produce el `.pptx` en `Cotizaciones/<Cliente>/` |
| 6. QA visual | LibreOffice `soffice --convert-to pdf` + `pdftoppm` | Revisar antes de entregar |

**Para una cotización nueva:** duplicar `generador-pptx-pepsico.js`, cambiar el bloque "Datos del caso" (CLIENTE, precios, fechas, plan) y los textos de las slides 2/10/11/13; si el cliente pide servicios adicionales, mirar el patrón de Fase 2 en `generador-pptx-waya.js`.


## 1. Identidad visual — "Moderna (opción 2)"

Tomada de la variante 2 del rediseño web (`Downloads/CarbonBox Home (standalone).html`).

**Paleta (hex) — alineada al Sistema de diseño CarbonBox** (ver `Sistema de diseño CarbonBox/`):
- Primary índigo `#1620A4` · deep `#0D1578` · glow `#5E6DE0`
- Surface oscura (portada/hero) `#0D1230`
- Primary soft `#ECEDFB` · 100 `#D8DBF4` · 200 `#B6BBE8`
- Accent verde bosque `#2F6B4A` · deep `#1E4A32` · accent-light/menta `#7ED3A8` · accent-soft `#E8F1EC`
- Tinta `#0F1535` · tinta-2 `#4A526E` · tinta-3 `#7A82A0`
- Fondo `#FFFFFF` · fondo-soft `#F7F8FC` · línea `#E6E8F2`
- Semánticos: success `#2F6B4A` · warning `#B9772A` · danger `#C0453F` · info `#1620A4`
- Data-viz emisiones: Energía `#1620A4` · Transporte `#2F6B4A` · Procesos `#7A82A0` · Residuos `#C2C8DB` (escala charts: `#1620A4 · #5E6DE0 · #B6BBE8 · #7A82A0 · #C2C8DB`)

**Tipografía:** Poppins (títulos y cuerpo); **JetBrains Mono** para cifras/metadatos. Títulos en azul primary (no negro). Wordmark: "Carbon" 400 + "Box" 700.

⛔ **No usar** el verde neón `#33C97A` ni el azul viejo `#1E2A78`/`#141D57`/`#14275C` (reemplazados por `#1620A4` / `#0D1578` / `#0D1230`). En gráficas, las emisiones van en índigo/neutros y el **verde se reserva para lo positivo** (reducción/compensación).

---

## 2. Logo (regla clave)

**Nunca redibujar el logo como vector** (a tamaño chico se empasta). Usar SIEMPRE los archivos reales de `logos/`:
- `Logo horizontal azul .png.png` → encabezados de slides (fondo claro).
- `Logo horizontal blanco.png.png` → portada y fondos navy (incl. slide 13).
- `Artboard 1 copy 11.png` → lockup vertical blanco. `icon_blanco.png` → solo el ícono (vórtice) para decoración.

**Ícono hexagonal:** sale por las **esquinas** (la portada lleva DOS: superior derecha e inferior derecha), grande y muy tenue (transparency ~88–91), "como si girara".

---

## 3. Diseño slide por slide (vigente — 13 slides; la 2 y 3 YA están fusionadas)

1. **Portada** — fondo navy; logo horizontal **blanco** arriba-izq; eyebrow "COTIZACIÓN COMERCIAL" (menta); título en **caja normal** (no mayúsculas); "Preparada para [Nombre del cliente]"; **NIT del cliente** en línea pequeña justo debajo (obligatorio desde jul-2026, lo usa el CRM para seguimiento); chip **PLAN PRO** verde bosque `#2F6B4A` con **texto blanco en negrita** (NO texto verde oscuro sobre verde — bajo contraste, no resalta) + línea de descripción del plan; meta abajo = fecha · validez 60 días · **enlace a la web** (SIN ciudad, trabajan remoto); **dos hexágonos** tenues a la derecha. ⛔ Nada de título en mayúsculas ni resaltado verde en el título.
2. **El cliente: contexto y necesidad** (FUSIÓN de las antiguas 2 y 3) — dos columnas "LO QUE SABEMOS" / "LO QUE NECESITA", con divisor vertical, texto corto. (Esto ya es oficial en `generador-pptx.js`.)
3. **Qué es CarbonBox** — héroe plataforma (`s4_hero.png` = "compu servicios") + 3 capacidades con iconos (Medición/Reducción/Compensación) + "30% menos tiempo · 40% más productividad" + logos **GHG Protocol** e **ISO 14064**.
4. **Ventajas** — imagen experto (`s5_stars.png`) + 4 ventajas con iconos + nota de autonomía/ahorro en tarjeta verde-soft.
5. **Soluciones tecnológicas** — **3 ilustraciones propias** (no capturas): (1) huella por actividad en barras, (2) reducción en el tiempo (línea verde descendente, −64%), (3) camino a carbono neutral (emisiones índigo + compensación verde + check). Generadas por `generador-ilustraciones-servicios.py`. Paleta de §1.
6. **Caso de éxito** — texto corto + cita destacada (sector manufactura).
7. **Empresas que confían** — por ahora chips de texto (grandes primero). Hay logos reales en `6. Página Web/.../Logos clientes/` para incrustar después.
8. **Nuestro trabajo hoy** — **mapa real** (`s9_map.png` = "Croquis America") + banderas (Colombia, Ecuador, Paraguay, México, **Argentina**, Perú — Guatemala se cambió por Argentina) + impacto (>150.000 / ~36.456 / 6 países / 10 sectores) en tarjetas verde-soft.
9. **Equipo experto** — **6 personas con fotos reales** (avatares circulares): Viviana Bohórquez (CEO y Co-fundadora), Alejandra Rojas (Líder de proyectos), Manuel Rivera (Líder en tecnología), Laura Bautista (Prof. sostenibilidad), Miguel Romero (Prof. sostenibilidad), Eliezer Mas y Rubí (Experto en tecnología).
10. **Plan Pro** — título = nombre del plan; lista de funcionalidades.
11. **Inversión + valor** — tarjeta de precio (tachado `$3.918` → **`$3.526 USD`**, badge "−10% alianza ATICA", "$294 USD/mes") + cajas laterales (pago 50/50, exento IVA, puntero a fidelización, notas al pie).
12. **Plan de Fidelización** — **lienzo original a sangre completa** (`fid_slide.png`, generado por `generador-fidelizacion.py`; filosofía en `fidelizacion-filosofia.md`). Mensaje **explícito**: "El precio de tu plan anual **no sube**", badge "PRECIO CONGELADO", mismo precio repetido Año 1 = 2 = 3 "…y se mantiene", logo blanco real arriba-der. (No copiar la referencia de la clienta; es diseño propio.)
13. **Cierre** — "¿Empezamos?" enmarcado como propuesta (NO como si ya compraron) + timeline corto + CTA "Agenda una reunión".

Encabezados de slides de contenido: logo azul (izq) + "NN / 13" (der). Pie: "CarbonBox · Cotización" / "● [cliente]".

---

## 4. Imágenes — fuente correcta

**Usar archivos LOCALES** de `C:\Users\USUARIO\Documents\CarbonBox\6. Página Web\Página web 2025\` (subcarpetas `Fotos equipo`, `Logos clientes`, `Página web 2`, `SErvicios`). El PPTX **sí** puede incrustar imágenes locales.
⛔ El entorno **no** puede descargar imágenes de internet (wixstatic bloqueado), así que NO depender de URLs para el PPTX.

Imágenes (en `Recursos/`): `s4_hero.png`, `s5_stars.png`, `std_ghg.png`, `std_iso.png`, `s9_map.png`, `t_vivi_sq.png … t_eli_sq.png` (equipo), `s6_ill1/2/3.png` (ilustraciones), `fid_slide.png`, `ic_*.png` (iconos), `cover_bg.png`.

---

## 5. Cómo se genera (automatización)

Scripts en `Generadores/` (leen de `Recursos/` y `Logos/`; escriben el PPTX en `Cotizaciones/<Cliente>/`):
- `generador-pptx-waya.js` — **deck VIGENTE** (Hotel Waya, v2 alineado). Requiere `npm install pptxgenjs`.
- `generador-pptx.js` — deck astillero (mismas rutas; **pendiente alinear colores a v2**).
- `generador-ilustraciones-servicios.py` — ilustraciones de la slide "soluciones" (requiere `cairosvg` + Poppins). Escribe `s6_ill*.png` en `Recursos/`.
- `generador-fidelizacion.py` y `generador-html.py` — **LEGADO**: incompletos (faltan `assets_b64.json`, `logo_white.png`, `ic_snow_dark.png`). En el deck Waya la fidelización se dibuja nativa.

**Build + QA (desde `Generadores/`):** `python3 generador-ilustraciones-servicios.py` → `node generador-pptx-waya.js` → PDF con LibreOffice (`soffice`) → `pdftoppm` para revisar.

---

## 6. Gotchas (errores que ya nos pasaron)

- **PowerPoint abierto bloquea el `.pptx`** → al guardar da "permiso denegado". Pedir cerrarlo, o guardar con otro nombre.
- **No usar dimensiones negativas** en shapes (p. ej. `LINE` con `h` negativo) → corrompe el archivo (PowerPoint pide "Reparar"). Para flechas usar iconos/imágenes.
- **La herramienta Write se trunca ~28.5 KB** → para HTML grande con base64, escribir/editar por shell (Python).
- **HTML no verificable aquí** (no hay navegador): construirlo con slides de altura según contenido (sin `aspect-ratio` fijo + `overflow:hidden`, que recorta).

---

## 7. Datos del caso actual (astillero Cartagena)

- Astillero en Cartagena (referido por José Manotas vía Jaime Casallas). **Nombre de la empresa: PENDIENTE** (placeholder "[Nombre del astillero]").
- ~200 empleados · huella organizacional alcances 1-3, sin verificación · sector **Industria manufacturera** (base $1.599).
- **Plan Pro** · alianza **ATICA = sí** → $3.918 → **$3.526 USD** (−10%) · $294/mes · validez **15 ago 2026**.

Precios: `files_ chatClaude/reglas-precio.md` + `calcular-precio.py`. Fórmula: `round(base × (1 + pct_empleados + pct_componentes))`; ATICA ×0.90; mensual /12; validez envío+60 días.

---

## 8. Pendientes

- [ ] Nombre real del astillero (reemplazar placeholder en portada y slide 2).
- [x] Fusión 2+3 → HECHA y oficial en `generador-pptx.js` (deck de 13 slides).
- [ ] Slide 7: incrustar logos reales de clientes (carpeta `Logos clientes/`), grandes primero.
- [ ] Compartir con cliente: recomendado **PDF en Google Drive**; **DocSend/Pitch** si se quiere analítica de apertura.
- [ ] Parametrizar para generar cualquier cotización cambiando solo datos del cliente (nombre, sector, empleados, plan, ATICA).

---

## 11. Reglas confirmadas (feedback Viviana — 18 jun 2026)

Aplicadas en `generador-pptx-waya.js`. Mantener en futuras cotizaciones.

**Estructura del deck**
- **Slides 2 y 3 (contexto + necesidad) van FUSIONADOS en UNA sola diapo** a dos columnas: "Lo que sabemos" (izq) y "Lo que necesita" (der) con divisor vertical. (Referencia: `cotizacion-PROPUESTA-2y3.pptx`.)
- **Paginación dinámica:** el contador `NT` se calcula según los flags de Fase 2; el cierre siempre lleva el número = `NT`. No hardcodear el número del cierre.

**Fase 2 — servicios adicionales (cuando el cliente pide algo más que la plataforma)**
- Controlado por flags al inicio del script: `INCLUIR_FASE2` (detalle de servicios) e `INCLUIR_FASE2_PRECIO` (valor).
- La **diapo de VALOR de la Fase 2 va justo DESPUÉS de la de servicios** y **solo se incluye cuando aplica**.
- Debe tener un **diseño distinto al del software**: tarjeta **VERDE** (no azul) + badge "PAQUETE COMPLEMENTARIO AL SOFTWARE", para que se entienda como algo adicional.
- El precio se pone en `FASE2_PRECIO`. **No inventar**: si no hay dato, dejar `"[Valor a definir]"`.

**Portada**
- Fondo configurable: si existe `cover_bg.png` en la carpeta del proyecto, se usa como fondo de portada (y se omiten los hexágonos). Si no, fondo azul + hexágonos. → Subir aquí la imagen de fondo definitiva para que todas las cotizaciones queden iguales.

**Slide "Qué es CarbonBox"**
- El texto "Alineado a estándares internacionales:" + logos GHG/ISO van **justo debajo de la imagen del computador** (no en la columna izquierda).

**Slide "Empresas que han confiado"**
- Si existe `s7_logos.png` se usa esa imagen; si no, grilla de nombres como respaldo. → Subir la imagen con ese nombre exacto.
- La imagen **NO debe traer su propio título** (el encabezado estándar de la slide ya pone "Empresas que han confiado en nosotros"; si la imagen también lo trae, se duplica).
- Se inserta con la función `fitImage()` que **lee los píxeles reales** y calcula el tamaño exacto conservando la relación de aspecto. (LibreOffice ignora `sizing:contain` y estiraba la imagen → por eso los logos se veían "anchos".)
- **Tamaño recomendado de la imagen:** PNG horizontal, mínimo ~1600 px de ancho (la actual 1920×792 va perfecta). Para que los logos ocupen TODO el ancho usar relación ~2.9:1 (ej. 2400×820 px); con relación más cuadrada queda centrada con márgenes laterales. Fondo blanco o transparente.

**Plan / medición (slide 11) — regla de negocio**
- ⚠️ **CarbonBox se vende por año**: la calculadora/medición es por **un (1) año de datos**. El primer ítem del plan lo dice explícito ("…para los datos de un (1) año…"). Varios años = varias mediciones/suscripciones. Evitar dar a entender que un precio cubre todo el histórico.

**Slide de cierre**
- El link de la franja azul es hipervínculo a **https://www.carbonbox.app/#contacto**.

**Slide de fidelización (NATIVA — ya no es imagen)**
- Diseño aprobado: título "El precio de tu plan anual **no sube**" + pastilla "PRECIO CONGELADO" + **3 tarjetas (Año 1 = Año 2 = Año 3)** con el precio, y la línea "tu aprendizaje es tu ahorro". Fondo azul, hexágono tenue, paginación y pie. Ya **no** se usa `fid_slide.png`.
- **El precio de las 3 tarjetas es dinámico:** sale de la variable `PRECIO_ANUAL_FMT` (única fuente, debe coincidir con la slide de Inversión). Cambiar SOLO esa variable para otro cliente.
- Usa el **mismo fondo de la portada** (`cover_bg.png`) para mantener coherencia visual.

**Imágenes a subir a la carpeta del proyecto (nombres exactos):**
- `cover_bg.png` → fondo de portada.
- `s7_logos.png` → logos de clientes (slide de confianza).


---

## 12. Portada: fondo con isotipo GIRADO (jul 2026)

- El fondo de portada `Recursos/cover_bg.png` se **genera** con `Generadores/generador-cover.py` (Python + Pillow). NO editar el PNG a mano.
- Reconstruye el degradado navy original (bilineal entre las 4 esquinas + glow arriba-derecha) y superpone el **isotipo** (`Recursos/Hexágono PNG.png` = hexágono en espiral) **GIRADO** (`rot=-24`), grande y muy tenue, saliendo por el borde derecho — "como si girara". Nunca recto.
- Parámetros ajustables al inicio del script: `HEX1`/`HEX2` (escala, rotación `rot`, opacidad `op`, posición `cx`/`cy`).
- El original recto quedó respaldado en `Recursos/_backup/cover_bg_original.png`.
- Regenerar: `cd Generadores && python3 generador-cover.py` (requiere `pip install pillow`). Luego re-correr el generador de la cotización.

## 13. Fotos del equipo (jul 2026)

- Las fotos van en `Recursos/` con estos nombres exactos (cuadradas): `t_vivi_sq.png`, `t_ale_sq.png`, `t_manu_sq.png`, `t_lau_sq.png`, `t_migue_sq.png`, `t_eli_sq.png`.
- Si falta alguna, el generador dibuja un avatar circular con las iniciales (fallback), no falla.
- **Descriptores de experiencia oficiales** (web) — versión corta usada en la slide de equipo:
  - Viviana Bohórquez — CEO y Co-fundadora — 15 años en estimación y reporte de reducciones de GEI; certificada ISO 14064-1 y 2.
  - Alejandra Rojas — Líder de proyectos — 5 años en inventarios de GEI; auditora interna de huellas de carbono y gestión de reducción y compensación.
  - Manuel Rivera — Líder en tecnología — Full Stack, 5 años en apps web y móviles; backend y bases de datos.
  - Laura Bautista — Profesional en sostenibilidad — 3 años en reportes y gestión de la sostenibilidad y medición de impacto.
  - Miguel Romero — Profesional en sostenibilidad — +4 años como ing. ambiental con énfasis en energías renovables y sostenibilidad; experiencia en el sector de alimentos y saneamiento ambiental.
  - Eliezer Mas y Rubí — Experto en tecnología — +4 años en desarrollo web y UI/UX; líder de equipos internacionales.

## 14. Caso PepsiCo (jul 2026)

- Generador: `Generadores/generador-pptx-pepsico.js`. Cliente "PepsiCo Alimentos Colombia" (2 plantas: Guarne 550 + Funza 750 = 1.300 colab. combinados, a solicitud de la clienta).
- Sector Industria manufacturera (alimentos), Plan Pro, alianza ATICA = sí → base $4.557 → **$4.101 USD** (−10%), $342/mes, validez 31 ago 2026. Sin Fase 2.
- Slide de inversión usa la variante CON descuento ATICA (precio base tachado + badge −10%).

## Gotcha adicional
- **PowerPoint abierto bloquea el `.pptx`** (aparece `~$archivo.pptx` y da EACCES al regenerar). Cerrar PowerPoint o generar con sufijo `-v2` y consolidar después.
