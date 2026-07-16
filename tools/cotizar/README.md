# Automatización de cotizaciones CarbonBox

Flujo para generar cotizaciones comerciales (deck de 13 slides) de CarbonBox.

## Carpetas

- **Cotizaciones/** — entregables, una carpeta por cliente (`.pptx` + `.pdf` + `.md`). `_Plantilla/` = base.
- **Generadores/** — scripts activos del flujo. Correr **desde aquí**. Los obsoletos están en `Generadores/_legado/`.
- **Insumos/** — instrucciones, reglas de precio, textos fijos, casos de éxito, intake y la memoria de diseño.
- **Logos/** — logos oficiales (no redibujar).
- **Recursos/** — imágenes, íconos, ilustraciones y fotos del equipo que usa el flujo. `_backup/` y `_legado/` = respaldos y variantes no usadas.
- **Sistema de diseño CarbonBox/** — guía de marca.

## Cómo generar una cotización

1. Leer `Insumos/instrucciones.md` (estructura y reglas). Primero confirmar si es huella **organizacional** (empresa) o de **evento** — son calculadoras distintas.
2. Calcular precio:
   - Organizacional: `Insumos/reglas-precio.md` → `cd Generadores && python3 calcular-precio.py --sector "…" --empleados N [--plan pro]`
   - Evento: `Insumos/reglas-precio-eventos.md` → `cd Generadores && python3 calcular-precio-eventos.py --tipo-evento "…" --num-asistentes N [--plan pro]`
3. Duplicar `Generadores/generador-pptx-pepsico.js` (generador vigente), ajustar el bloque **Datos del caso** y los textos del cliente.
4. Generar: `node generador-<cliente>.js` → escribe el `.pptx` en `Cotizaciones/<Cliente>/`.
5. QA: `soffice --headless --convert-to pdf <archivo>.pptx` y revisar.

Detalle completo del diseño y del flujo: **`Insumos/NOTAS-DISENO-Y-PLANTILLA.md`** (secciones 0 y 11–14).

## Requisitos

- Node + `pptxgenjs` (`npm install` en la raíz).
- Python + Pillow (`pip install pillow`) para `generador-cover.py`.
- LibreOffice (`soffice`) para exportar a PDF.
