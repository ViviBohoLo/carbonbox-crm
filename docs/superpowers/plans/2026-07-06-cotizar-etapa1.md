# Cotizaciones asistidas — Etapa 1 (skill `/cotizar`) — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generar el deck de cotización (13 slides `.pptx`/`.pdf`) a partir de un `contenido.yml`, con un motor estable, el precio determinístico, y un skill `/cotizar` que lo orquesta leyendo la oportunidad del CRM + la transcripción del Drive.

**Architecture:** Se separa **contenido** (`contenido.yml` por cotización) de **render** (`render.js` + `lib/layouts.js` con un layout por tipo de slide, portados del generador pepsico) y de **textos fijos** (`lib/textos.js` que parsea `Insumos/*.md`). El precio sale de `calcular-precio.py --json`. El skill (Claude en Cowork) arma el YAML y llama al motor.

**Tech Stack:** Node ≥18 (`pptxgenjs`, `js-yaml`, `node:test` nativo), Python 3 (`calcular-precio.py`, `unittest`), LibreOffice (`soffice`).

## Global Constraints

- Raíz del proyecto: `C:\Users\USUARIO\Claude\Projects\Automatización de cotizaciones CarbonBox` (rutas abajo son relativas a esa raíz). Contiene espacios → citar rutas en shell.
- **Fuente de verdad = `Insumos/`** (`instrucciones.md`, `textos-fijos.md`, `casos-exito.md`, `reglas-precio.md`). El código los LEE; no duplica su contenido.
- **No inventar datos:** campo faltante → literal `[⚠️ PENDIENTE: ...]` (regla de `instrucciones.md`).
- Precio: NO cambiar la lógica de `calcular-precio.py`; solo añadir salida `--json`.
- 13 tipos de slide (de `instrucciones.md`, tabla del spec) + `fase2-servicios`/`fase2-valor` opcionales.
- Sin frameworks de test nuevos: Node usa `node:test`; Python usa `unittest` (stdlib).
- Diseño/tokens y assets: reusar los del generador actual (`generador-pptx-pepsico.js`: colores `P=1620A4`, `ACC=2F6B4A`, fuente Poppins; logos en `/Logos`, imágenes en `/Recursos`). No rediseñar.

---

### Task 1: `calcular-precio.py --json`

**Files:**
- Modify: `Generadores/calcular-precio.py`
- Create: `Generadores/test/test_calcular_precio_json.py`

**Interfaces:**
- Produces: `calcular-precio.py --sector S --empleados N --plan P --json` → imprime una línea JSON: `{"precio_final":int,"precio_mensual":int,"precio_atica":int,"precio_mensual_atica":int,"plan":str,"sector":str,"tamano":str}`. Si hay error (sector/tamaño inválido, >2000) → `{"error":"..."}` y exit code 1.

- [ ] **Step 1: Test que falla**

```python
# Generadores/test/test_calcular_precio_json.py
import json, subprocess, sys, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(args):
    r = subprocess.run([sys.executable, os.path.join(BASE, "calcular-precio.py")] + args,
                       capture_output=True, text=True)
    return r

def test_json_ok():
    r = run(["--sector", "Industria manufacturera", "--empleados", "100", "--plan", "pro", "--json"])
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    assert set(["precio_final","precio_mensual","precio_atica","precio_mensual_atica","plan","sector","tamano"]) <= set(d)
    assert isinstance(d["precio_final"], int) and d["precio_final"] > 0
    assert d["precio_atica"] == round(d["precio_final"] * 0.90)

def test_json_error_exit1():
    r = run(["--sector", "Sector Inexistente", "--empleados", "100", "--plan", "pro", "--json"])
    assert r.returncode == 1
    assert "error" in json.loads(r.stdout)

if __name__ == "__main__":
    test_json_ok(); test_json_error_exit1(); print("OK")
```

- [ ] **Step 2: Correr — FALLA**

Run: `cd "…/Automatización de cotizaciones CarbonBox" && python3 -m unittest Generadores.test.test_calcular_precio_json 2>&1 | tail -5`
(o `python3 Generadores/test/test_calcular_precio_json.py`)
Expected: falla (aún no existe `--json`; hoy imprime tabla).

- [ ] **Step 3: Implementar `--json`** en `calcular-precio.py`

Añadir el arg y la rama de salida. En el `argparse` (junto a los otros `add_argument`):
```python
    parser.add_argument("--json", action="store_true", help="Salida JSON (una línea) para consumir desde otros scripts")
```
Y al inicio de la lógica de resolución (antes de imprimir tablas), cuando hay sector + (tamano o empleados) + plan + `--json`:
```python
    import json as _json
    if args.json:
        tamano = args.tamano or (normalizar_tamano(args.empleados) if args.empleados else None)
        if not (args.sector and tamano and args.plan):
            print(_json.dumps({"error": "faltan --sector, --plan y --tamano/--empleados"})); sys.exit(1)
        r = calcular_precio(args.plan, args.sector, tamano)
        if "error" in r:
            print(_json.dumps({"error": r["error"]}, ensure_ascii=False)); sys.exit(1)
        print(_json.dumps({
            "precio_final": r["precio_final"], "precio_mensual": r["precio_mensual"],
            "precio_atica": r["precio_atica"], "precio_mensual_atica": r["precio_mensual_atica"],
            "plan": r["plan"], "sector": r["sector"], "tamano": r["tamano"],
        }, ensure_ascii=False)); sys.exit(0)
```
(requiere `import sys` arriba — ya se usa; si no, añadirlo.)

- [ ] **Step 4: Correr — PASA**

Run: `python3 Generadores/test/test_calcular_precio_json.py`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add Generadores/calcular-precio.py Generadores/test/test_calcular_precio_json.py 2>/dev/null || echo "sin git"
```

---

### Task 2: Formato `contenido.yml` + ejemplo

**Files:**
- Create: `Cotizaciones/_Plantilla/contenido.ejemplo.yml`

**Interfaces:**
- Produces: el contrato de datos que consume `render.js` (Task 4). Encabezado (cliente, sector, num_empleados, tipo_servicio, plan, atica, fecha_envio, precios) + `slides:` lista ordenada de `{tipo, ...campos}`.

- [ ] **Step 1: Escribir el ejemplo** (cliente ficticio; ilustra el formato, NO es plantilla de negocio)

```yaml
# contenido.ejemplo.yml — formato del archivo de contenido de una cotización
cliente: "Ejemplo Demo S.A.S."
sector: "Industria manufacturera"      # uno de los 19 de reglas-precio.md
num_empleados: 100
tipo_servicio: organizacional          # organizacional|producto|evento|certificacion
plan: Pro                              # Essential|Pro|Expert
atica: false
fecha_envio: "2026-04-30"
# precios: los inyecta el skill desde calcular-precio.py --json
precio_final: 1918
precio_mensual: 160
precio_atica: 1726
precio_mensual_atica: 144
slides:
  - tipo: portada
  - tipo: contexto-necesidad
    sabemos: "[párrafo IA ≤80 palabras sobre el cliente]"
    necesita: "[párrafo IA ≤80 palabras sobre su necesidad]"
  - tipo: que-es-carbonbox
  - tipo: ventajas
  - tipo: soluciones
  - tipo: caso-exito
  - tipo: logos
  - tipo: trabajo-hoy
  - tipo: equipo
  - tipo: plan
    descripcion_necesidad_corta: "[una línea]"
  - tipo: inversion
  - tipo: fidelizacion
  - tipo: proximos-pasos
  # opcional Fase 2: - tipo: fase2-servicios / - tipo: fase2-valor
```

- [ ] **Step 2: Commit**

```bash
git add "Cotizaciones/_Plantilla/contenido.ejemplo.yml" 2>/dev/null || echo "sin git"
```

---

### Task 3: Loaders de textos fijos — `lib/textos.js`

**Files:**
- Create: `Generadores/lib/textos.js`
- Create: `Generadores/test/textos.test.js`

**Interfaces:**
- Produces:
  - `cargarTextosFijos() -> { [seccion:string]: string }` — parsea `Insumos/textos-fijos.md`; claves = encabezados `## slide_XX` y `### subseccion` (ej. `slide_04`, `ventajas_pro`, `modulos_organizacional`, `funcionalidades_expert`, `slide_09`); valor = el markdown bajo ese encabezado.
  - `cargarCasos() -> { [sector_key:string]: string }` — parsea `Insumos/casos-exito.md`; claves = `## sector_X`.
  - `casoPorSector(sectorCliente:string) -> string` — mapea el sector del cliente a la clave (`instrucciones.md` slide 6/7) con fallback `sector_generico_latam`.

- [ ] **Step 1: Test que falla**

```javascript
// Generadores/test/textos.test.js
const { test } = require("node:test");
const assert = require("node:assert");
const t = require("../lib/textos");

test("carga secciones de textos-fijos", () => {
  const fijos = t.cargarTextosFijos();
  assert.ok(fijos["slide_04"] && fijos["slide_04"].length > 0);
  assert.ok(fijos["ventajas_pro"]);
  assert.ok(fijos["funcionalidades_expert"]);
});

test("carga casos por sector con fallback", () => {
  const casos = t.cargarCasos();
  assert.ok(casos["sector_manufactura"]);
  assert.equal(t.casoPorSector("Industria manufacturera"), "sector_manufactura");
  assert.equal(t.casoPorSector("Sector raro sin match"), "sector_generico_latam");
});
```

- [ ] **Step 2: Correr — FALLA**

Run: `node --test Generadores/test/textos.test.js`
Expected: FALLA (`Cannot find module '../lib/textos'`).

- [ ] **Step 3: Implementar `lib/textos.js`**

```javascript
const fs = require("fs");
const path = require("path");
const INSUMOS = path.join(__dirname, "..", "..", "Insumos");

// Parser genérico: divide por encabezados markdown ## y ### y devuelve {clave: cuerpo}.
function parseSecciones(md) {
  const out = {};
  const lineas = md.split(/\r?\n/);
  let clave = null, buf = [];
  const flush = () => { if (clave) out[clave] = buf.join("\n").trim(); buf = []; };
  for (const ln of lineas) {
    const m = ln.match(/^#{2,3}\s+([A-Za-z0-9_]+)/);   // ## slide_04 / ### ventajas_pro
    if (m) { flush(); clave = m[1]; } else if (clave) { buf.push(ln); }
  }
  flush();
  return out;
}

function cargarTextosFijos() {
  return parseSecciones(fs.readFileSync(path.join(INSUMOS, "textos-fijos.md"), "utf8"));
}
function cargarCasos() {
  return parseSecciones(fs.readFileSync(path.join(INSUMOS, "casos-exito.md"), "utf8"));
}

// Mapa sector cliente -> clave de caso (instrucciones.md slide 6/7).
const MAPA_SECTOR = [
  [/(manufactura|industri|energ)/i, "sector_manufactura"],
  [/(salud|fundaci|ong)/i, "sector_salud"],
  [/(evento|entreten|festiv)/i, "sector_eventos"],
  [/(financ|gremio|gobierno|seguro|p[uú]blic)/i, "sector_financiero"],
  [/(agro|aliment)/i, "sector_agroindustria"],
  [/(retail|moda|consumo|e-?commerce|distribuidor)/i, "sector_retail_moda"],
];
function casoPorSector(sectorCliente) {
  const s = sectorCliente || "";
  for (const [re, clave] of MAPA_SECTOR) if (re.test(s)) return clave;
  return "sector_generico_latam";
}

module.exports = { cargarTextosFijos, cargarCasos, casoPorSector, parseSecciones };
```

- [ ] **Step 4: Correr — PASA**

Run: `node --test Generadores/test/textos.test.js`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add Generadores/lib/textos.js Generadores/test/textos.test.js 2>/dev/null || echo "sin git"
```

---

### Task 4: Motor `render.js` — carga YAML, dispatch por tipo, y layout `portada`

**Files:**
- Create: `Generadores/render.js`
- Create: `Generadores/lib/layouts.js`
- Create: `Generadores/lib/base.js`  (setup pptxgen + tokens + helpers compartidos)
- Create: `Generadores/test/render.test.js`

**Interfaces:**
- Consumes: `lib/textos.js` (Task 3), `contenido.yml` (Task 2).
- Produces:
  - `lib/base.js`: exporta `crearPptx()`, tokens (`P,ACC,DARK,INK,INK2,INK3,SOFT,LINE,MINT,WHITE,F,FM,W,H,MX`), y helpers `header(s,num,title,eyebrow)`, `footer(s,cliente)`, `card`, `icon`, `fitImage`, `wordmark` (portados de `generador-pptx-pepsico.js` líneas 1–90).
  - `lib/layouts.js`: `const LAYOUTS = { portada: fn, ... }` donde cada `fn(p, slide, ctx)` agrega la diapo. `ctx = {cliente, plan, sector, tipo_servicio, atica, fecha_envio, precios, fijos, casos, NT, idx}`.
  - `render.js`: CLI `node render.js <contenido.yml> [salida.pptx]` → carga YAML, valida tipos, itera `slides`, llama `LAYOUTS[tipo]`, guarda `.pptx`. Sale con error claro si un `tipo` no existe.

- [ ] **Step 1: Test que falla** (smoke: renderiza el ejemplo, produce pptx; tipo inválido → error)

```javascript
// Generadores/test/render.test.js
const { test } = require("node:test");
const assert = require("node:assert");
const { execFileSync } = require("node:child_process");
const fs = require("fs"); const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
const OUT = path.join(__dirname, "_out_test.pptx");

test("render del ejemplo produce un .pptx no vacío", () => {
  if (fs.existsSync(OUT)) fs.unlinkSync(OUT);
  execFileSync("node", [path.join(ROOT, "Generadores", "render.js"),
    path.join(ROOT, "Cotizaciones", "_Plantilla", "contenido.ejemplo.yml"), OUT], { stdio: "pipe" });
  assert.ok(fs.existsSync(OUT) && fs.statSync(OUT).size > 5000);
  fs.unlinkSync(OUT);
});

test("tipo desconocido falla con mensaje claro", () => {
  const bad = path.join(__dirname, "_bad.yml");
  fs.writeFileSync(bad, "cliente: X\nslides:\n  - tipo: no-existe\n");
  assert.throws(() => execFileSync("node",
    [path.join(ROOT, "Generadores", "render.js"), bad], { stdio: "pipe" }),
    /tipo.*no-existe|desconocido/i);
  fs.unlinkSync(bad);
});
```

- [ ] **Step 2: Correr — FALLA**

Run: `node --test Generadores/test/render.test.js`
Expected: FALLA (no existe `render.js`).

- [ ] **Step 3: Crear `lib/base.js`** — portar setup + helpers (líneas 1–90 de `generador-pptx-pepsico.js`), parametrizando `crearPptx()` y exportando tokens/helpers. (Copia literal de esas funciones `shadow, wordmark, header, footer, card, icon, flag, imgSize, fitImage`; cambiar `CLIENTE` por parámetro y no fijar datos del caso.)

```javascript
const pptxgen = require("pptxgenjs");
const path = require("path");
const fs = require("fs");
const ROOT = path.join(__dirname, "..", "..");
const P="1620A4",PD="0D1578",DARK="0D1230",ACC="2F6B4A",ACD="1E4A32",INK="0F1535",INK2="4A526E",INK3="7A82A0",
  SOFT="F7F8FC",LINE="E6E8F2",PSOFT="ECEDFB",P100="D8DBF4",ASOFT="E8F1EC",MINT="7ED3A8",WHITE="FFFFFF";
const F="Poppins", FM="JetBrains Mono", W=13.333, H=7.5, MX=0.7;
const LOGO_BLUE=ROOT+"/Logos/Logo horizontal azul .png.png";
const LOGO_WHITE=ROOT+"/Logos/Logo horizontal blanco.png.png";
const ICON_WHITE=ROOT+"/Logos/icon_blanco.png";

function crearPptx() {
  const p = new pptxgen();
  p.defineLayout({ name:"W", width:W, height:H }); p.layout = "W";
  p.author = "CarbonBox";
  process.chdir(path.join(ROOT, "Recursos"));   // assets relativos
  return p;
}
// ... portar aquí shadow(), wordmark(), header(), footer(cliente), card(), icon(), flag(), fitImage()
// exactamente como en generador-pptx-pepsico.js (líneas 39–90), tomando `cliente` como parámetro en footer.
module.exports = { crearPptx, P,PD,DARK,ACC,ACD,INK,INK2,INK3,SOFT,LINE,PSOFT,P100,ASOFT,MINT,WHITE,F,FM,W,H,MX,
  LOGO_BLUE,LOGO_WHITE,ICON_WHITE, /* + helpers exportados */ };
```

- [ ] **Step 4: Crear `lib/layouts.js` con `portada` (patrón)** — portar la SLIDE 1 (líneas 92–113 del generador), leyendo de `ctx` en vez de constantes:

```javascript
const B = require("./base");
function portada(p, slide, ctx) {
  const s = p.addSlide(); s.background = { color: B.DARK };
  // ...portar el cuerpo de la SLIDE 1 (cover) de generador-pptx-pepsico.js líneas 92–113,
  //   reemplazando: CLIENTE -> ctx.cliente ; "PLAN PRO" -> ctx.plan ;
  //   el párrafo -> (slide.descripcion || ctx.fijos.portada_desc || "") ;
  //   FECHA_HOY -> ctx.fecha_envio_fmt ; tipo de servicio -> ctx.tipo_servicio_fmt
  return s;
}
const LAYOUTS = { portada };   // se completan en Task 5
module.exports = { LAYOUTS };
```

- [ ] **Step 5: Crear `render.js`** (CLI + dispatch)

```javascript
const fs = require("fs"); const path = require("path"); const yaml = require("js-yaml");
const B = require("./lib/base");
const { LAYOUTS } = require("./lib/layouts");
const textos = require("./lib/textos");

function fmtFecha(iso) { /* "2026-04-30" -> "30 de abril de 2026" */
  const M=["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"];
  const [y,m,d]=(iso||"").split("-"); return d? `${+d} de ${M[+m-1]} de ${y}` : (iso||"");
}
function tipoServicioFmt(t){return ({organizacional:"Estimación de huella de carbono organizacional",
  producto:"Medición de huella de carbono de producto",evento:"Medición de huella de carbono de evento",
  certificacion:"Medición de huella de carbono y certificación de carbono neutralidad"})[t]||t;}

function main() {
  const [,, yamlPath, outArg] = process.argv;
  if (!yamlPath) { console.error("uso: node render.js <contenido.yml> [salida.pptx]"); process.exit(2); }
  const doc = yaml.load(fs.readFileSync(yamlPath, "utf8"));
  const ctx = {
    cliente: doc.cliente, plan: doc.plan, sector: doc.sector, tipo_servicio: doc.tipo_servicio,
    atica: !!doc.atica, fecha_envio_fmt: fmtFecha(doc.fecha_envio), tipo_servicio_fmt: tipoServicioFmt(doc.tipo_servicio),
    precios: { final: doc.precio_final, mensual: doc.precio_mensual, atica: doc.precio_atica, mensual_atica: doc.precio_mensual_atica },
    fijos: textos.cargarTextosFijos(), casos: textos.cargarCasos(),
    NT: (doc.slides||[]).length,
  };
  const p = B.crearPptx();
  (doc.slides||[]).forEach((slide, idx) => {
    const fn = LAYOUTS[slide.tipo];
    if (!fn) { console.error(`Error: tipo de slide desconocido: '${slide.tipo}' (slide #${idx+1})`); process.exit(1); }
    fn(p, { ...slide, idx: idx+1 }, { ...ctx, idx: idx+1 });
  });
  const out = outArg || path.join(path.dirname(yamlPath), `${(doc.cliente||"cotizacion").replace(/[^\w]+/g,"_")}.pptx`);
  return p.writeFile({ fileName: out }).then(() => console.log("OK:", out));
}
main();
```

- [ ] **Step 6: Instalar `js-yaml`**

Run: `cd "…/Automatización de cotizaciones CarbonBox" && npm install js-yaml`
Expected: agrega `js-yaml` a `package.json`.

- [ ] **Step 7: Correr el test** — el smoke pasará parcialmente: con solo `portada` en LAYOUTS, los demás `tipo` darán "desconocido". Ajuste temporal: el smoke usa un YAML mínimo de una sola slide `portada` hasta completar Task 5. Reescribir el primer test para usar `- tipo: portada` únicamente y verificar pptx>5000; el test de "tipo desconocido" ya pasa.

Run: `node --test Generadores/test/render.test.js`
Expected: PASS (2 tests, con el smoke sobre portada).

- [ ] **Step 8: Commit**

```bash
git add Generadores/render.js Generadores/lib/ Generadores/test/render.test.js package.json package-lock.json 2>/dev/null || echo "sin git"
```

---

### Task 5: Portar las 12 layouts restantes a `lib/layouts.js`

**Files:**
- Modify: `Generadores/lib/layouts.js`
- Modify: `Generadores/test/render.test.js` (smoke sobre el ejemplo completo de 13 slides)

**Interfaces:**
- Produces: `LAYOUTS` completo con las 13 claves + `fase2-servicios`/`fase2-valor`.

**Receta de portado (mecánica — el código YA existe y funciona en `generador-pptx-pepsico.js`):** para cada tipo, copiar el bloque de su SLIDE en el generador y reemplazar el contenido incrustado por lecturas de `ctx`/`slide`/`ctx.fijos`/`ctx.casos`. Mapa tipo → fuente y origen del texto:

| `tipo` | SLIDE en generador (aprox. líneas) | Contenido |
|--------|-----------------------------------|-----------|
| `contexto-necesidad` | 115–127 | `slide.sabemos` / `slide.necesita` (IA) |
| `que-es-carbonbox` | 129–144 | `ctx.fijos.slide_04` |
| `ventajas` | 146–159 | `ctx.fijos["ventajas_"+plan.toLowerCase()]` |
| `soluciones` | 161–171 | `ctx.fijos["modulos_"+tipo_servicio]` |
| `caso-exito` | 173–181 | `ctx.casos[textos.casoPorSector(ctx.sector)]` |
| `logos` | 183–194 | `ctx.fijos.slide_08` (grid de logos, imágenes de /Recursos) |
| `trabajo-hoy` | 196–210 | `ctx.fijos.slide_09` (cifras oficiales) |
| `equipo` | (SLIDE 10) | `ctx.fijos.slide_10` |
| `plan` | (SLIDE 11) | `ctx.fijos["funcionalidades_"+plan.toLowerCase()]` + `slide.descripcion_necesidad_corta` |
| `inversion` | (SLIDE 12) | `ctx.precios` + condicional `ctx.atica` (plantillas de `instrucciones.md` SLIDE 12) |
| `fidelizacion` | (SLIDE 13 fidelización) | `ctx.fijos.slide_13` + `ctx.precios` |
| `proximos-pasos` | (SLIDE final) | cronograma por `plan`+`tipo_servicio` (`instrucciones.md` SLIDE 13) |
| `fase2-servicios`,`fase2-valor` | reglas de plantilla (diseño verde) | `slide.*` (solo si se agregan) |

Reglas al portar (de `instrucciones.md`): usar `[⚠️ PENDIENTE: ...]` si falta un dato; "exentos" (no "excentos"); fecha límite = `fecha_envio` + 60 días; cifras oficiales fijas en `trabajo-hoy`.

- [ ] **Step 1: Portar `contexto-necesidad` y `que-es-carbonbox`**, agregarlas a `LAYOUTS`. Verificar que `render.js` sobre un YAML con esas 3 slides (portada + estas 2) produce pptx sin error: `node render.js <yaml_3slides> /tmp/x.pptx`.

- [ ] **Step 2: Portar `ventajas`, `soluciones`, `caso-exito`.** Verificar render incremental (pptx sin error).

- [ ] **Step 3: Portar `logos`, `trabajo-hoy`, `equipo`.** Verificar render incremental.

- [ ] **Step 4: Portar `plan`, `inversion` (con condicional ATICA), `fidelizacion`, `proximos-pasos`.** Verificar render incremental.

- [ ] **Step 5: Portar `fase2-servicios` y `fase2-valor`** (diseño verde; solo se usan si el YAML las incluye).

- [ ] **Step 6: Actualizar el smoke test** para renderizar `contenido.ejemplo.yml` completo (13 slides) y assert pptx > 20000 bytes.

Run: `node --test Generadores/test/render.test.js`
Expected: PASS (renderiza las 13 slides sin error).

- [ ] **Step 7: Commit**

```bash
git add Generadores/lib/layouts.js Generadores/test/render.test.js 2>/dev/null || echo "sin git"
```

---

### Task 6: Export a PDF + verificación visual del ejemplo

**Files:**
- Create: `Generadores/render-pdf.sh`

**Interfaces:**
- Produces: `render-pdf.sh <cotizacion.pptx>` → genera el `.pdf` junto al `.pptx` vía LibreOffice.

- [ ] **Step 1: Crear el script**

```bash
#!/bin/bash
# render-pdf.sh <archivo.pptx> — exporta a PDF con LibreOffice en la misma carpeta
set -e
PPTX="$1"; DIR="$(dirname "$PPTX")"
soffice --headless --convert-to pdf --outdir "$DIR" "$PPTX"
echo "PDF: ${PPTX%.pptx}.pdf"
```

- [ ] **Step 2: Prueba manual E2E** — renderizar el ejemplo y exportar a PDF; abrir el PDF y revisar visualmente las 13 slides (QA humano):
```bash
node Generadores/render.js "Cotizaciones/_Plantilla/contenido.ejemplo.yml" "/tmp/demo.pptx"
bash Generadores/render-pdf.sh "/tmp/demo.pptx"
```
Expected: `/tmp/demo.pdf` con 13 slides bien formadas. (Comparar visualmente contra `Cotizaciones/PepsiCo Colombia/` como referencia de diseño.)

- [ ] **Step 3: Commit**

```bash
git add Generadores/render-pdf.sh 2>/dev/null || echo "sin git"
```

---

### Task 7: Campo `linkTranscripcion` en la Opportunity del CRM (una vez)

**Files:**
- Create: `Generadores/_setup/crear-campo-transcripcion.md` (registro del paso; el cambio se hace vía API de Twenty en el VPS)

**Interfaces:**
- Produces: un custom field `linkTranscripcion` (tipo TEXT) en el objeto Opportunity de Twenty, legible por el skill.

- [ ] **Step 1: Crear el campo vía API de metadata de Twenty** (token de usuario, 30min — patrón de [[twenty-workflow-api]]). Documentar el comando exacto en el `.md` y ejecutarlo una vez contra `https://crm.carbonbox.app`. Verificar:
```bash
ssh -i ~/.ssh/hostinger_vps root@72.60.125.170 'TK=$(cat /root/.twenty_api_token); curl -s -H "Authorization: Bearer $TK" "http://localhost:3000/rest/metadata/fields?filter=name[eq]:linkTranscripcion" | head -c 300'
```
Expected: el campo aparece en la metadata de Opportunity.

- [ ] **Step 2: Commit** del registro `.md`.

---

### Task 8: Skill `/cotizar`

**Files:**
- Create: `.claude/skills/cotizar/SKILL.md`

**Interfaces:**
- Consumes: `render.js`, `render-pdf.sh`, `calcular-precio.py --json`, `lib/textos.js`, API de Twenty, conector Drive.

- [ ] **Step 1: Escribir `SKILL.md`** con el flujo (frontmatter `name: cotizar`, `description: genera una cotización desde una oportunidad del CRM`), instruyendo a Claude para:
  1. Recibir la referencia de la oportunidad (nombre/ID). Consultar Twenty (GraphQL en `https://crm.carbonbox.app`) → empresa, sector, `planCarbonbox`, país, contacto, `linkTranscripcion`.
  2. Si falta `linkTranscripcion` → pedirlo en el chat. Leer la transcripción del Drive (conector Drive) desde el link.
  3. Extraer los campos de `instrucciones.md` (num_empleados, tipo_servicio, atica, motivación, decisor, contexto, necesidad) de la transcripción; lo que falte → `[⚠️ PENDIENTE]` o preguntar. NO inventar.
  4. Redactar `contexto` y `necesidad` (≤80 palabras c/u) por las reglas de `instrucciones.md`.
  5. Correr `python3 Generadores/calcular-precio.py --sector "<sector>" --empleados <n> --plan <plan> --json`.
  6. Escribir `Cotizaciones/<Cliente>/contenido.yml` (formato de Task 2) y correr `node Generadores/render.js <yml>` + `bash Generadores/render-pdf.sh <pptx>`.
  7. Mostrar el resultado y el checklist de calidad de `instrucciones.md`; iterar por chat (editar el YAML → re-render).
  8. Anotar que el write-back al CRM/Drive/correo es Etapa 2 (no lo hace aún).

- [ ] **Step 2: Prueba E2E asistida** — correr `/cotizar` sobre una oportunidad de prueba con un `linkTranscripcion` a un transcript de ejemplo; revisar el deck. Limpiar datos de prueba del CRM.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/cotizar/SKILL.md 2>/dev/null || echo "sin git"
```

---

## Notas de ejecución

- **Portado de layouts (Task 4–5):** es refactor de código EXISTENTE (`generador-pptx-pepsico.js`), no diseño nuevo. Mantener idénticos los tokens/posiciones; solo cambiar contenido incrustado → lecturas de `ctx`/`slide`/`fijos`/`casos`.
- **QA visual:** ninguna prueba compara el binario del pptx; la validación de diseño la hace un humano viendo el PDF (referencia: `Cotizaciones/PepsiCo Colombia/`).
- **Fuente de verdad:** si `instrucciones.md`/`textos-fijos.md` cambian, el motor los relee — no hay que tocar código.
- **Datos de prueba (Task 7–8):** si se crea una oportunidad de prueba en el CRM real, borrarla al final.
