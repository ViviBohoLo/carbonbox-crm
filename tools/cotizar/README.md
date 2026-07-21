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

El flujo lo conduce la skill **`/cotizar`** (`.claude/skills/cotizar/SKILL.md`), que arranca
desde una oportunidad del CRM. Estos son los pasos y los comandos que ejecuta.

**Ya no se duplica un generador por cliente.** El motor es genérico: lee un `contenido.yml`
y relee `Insumos/*.md` en cada corrida, así que cambiar textos fijos o reglas de precio no
toca código. Los `generador-<cliente>.js` sueltos son del flujo anterior.

1. Confirmar el tipo de huella: **organizacional** (empresa) o **evento** — son calculadoras
   distintas. Reglas y estructura en `Insumos/instrucciones.md`.
2. Leer la oportunidad en el CRM (empresa, NIT, sector, plan, `linkTranscripcion`) y, con ese
   link, la transcripción de la reunión en Drive. Si el campo no existe, ver
   `Generadores/_setup/crear-campo-transcripcion.md`.
3. Calcular el precio — **determinístico, no estimar**:
   - Organizacional: `python3 Generadores/calcular-precio.py --sector "…" --empleados N --plan pro --json`
   - Evento: `python3 Generadores/calcular-precio-eventos.py --tipo-evento "…" --num-asistentes N --plan pro --json`
4. Escribir `Cotizaciones/<Cliente>/contenido.yml` con los datos y los 4 precios del JSON.
   Formato de referencia: `Cotizaciones/_Plantilla/contenido.ejemplo.yml`.
5. Renderizar:
   ```bash
   node Generadores/render.js "Cotizaciones/<Cliente>/contenido.yml"
   ```
   El `.pptx` queda junto al `.yml`. Un 2º argumento opcional elige otra ruta de salida.

   Y a PDF, según lo que tengas instalado:
   ```bash
   # Windows con Office (no requiere instalar nada):
   powershell -File Generadores/render-pdf.ps1 "Cotizaciones/<Cliente>/<archivo>.pptx" -Png
   # Linux/Mac o Windows con LibreOffice:
   bash Generadores/render-pdf.sh "Cotizaciones/<Cliente>/<archivo>.pptx"
   ```
   El flag `-Png` exporta además cada slide como imagen a `_png/`, para revisar el diseño
   (desbordes de texto, tipografías) sin abrir Office.
6. QA con el checklist de `Insumos/instrucciones.md` (NIT presente, fecha completa, precio USD,
   "exentos" bien escrito, mensual = precio÷12, fecha límite = envío + 60 días, cronograma
   acorde al plan). Iterar editando el YAML y volviendo a renderizar.
7. Al enviar, registrar en el CRM: `node Generadores/registrar-cotizacion.js --cliente "…"
   --nit "…" --plan Pro --precio N` — mueve o crea la oportunidad en "Propuesta enviada" en
   crm.carbonbox.app. Requiere un token local; ver la cabecera del script. **Nunca pegues el
   token en el chat.**

Detalle completo del diseño y del flujo: **`Insumos/NOTAS-DISENO-Y-PLANTILLA.md`** (secciones 0 y 11–14).

## Tests

```bash
node --test "Generadores/test/*.test.js"
```

## Requisitos

- Node 18+ (`npm install` en la raíz). El 18+ es obligatorio: `registrar-cotizacion.js` usa `fetch` incorporado.
- Python + Pillow (`pip install pillow`) para `generador-cover.py`.
- Para el PDF: **PowerPoint** (vía `render-pdf.ps1`, en Windows) **o** LibreOffice
  (`soffice`, vía `render-pdf.sh`). Basta con uno de los dos.
