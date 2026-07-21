const { test } = require("node:test");
const assert = require("node:assert");
const { execFileSync } = require("node:child_process");
const fs = require("fs"); const path = require("path"); const os = require("os");
const ROOT = path.join(__dirname, "..", "..");
const GEN = path.join(ROOT, "Generadores");
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), "cotizar-"));

test("render de una portada produce un .pptx no vacío", () => {
  const out = path.join(TMP, "_portada.pptx");
  const yml = path.join(TMP, "_portada.yml");
  fs.writeFileSync(yml,
    "cliente: Demo\nnit: \"900.000.000-0\"\ntipo_servicio: organizacional\nplan: Pro\nfecha_envio: \"2026-04-30\"\nslides:\n  - tipo: portada\n");
  execFileSync("node", [path.join(GEN, "render.js"), yml, out], { stdio: "pipe" });
  assert.ok(fs.existsSync(out) && fs.statSync(out).size > 5000);
});

test("render del ejemplo completo (13 slides) produce un .pptx", () => {
  const out = path.join(TMP, "_demo.pptx");
  const yml = path.join(ROOT, "Cotizaciones", "_Plantilla", "contenido.ejemplo.yml");
  execFileSync("node", [path.join(GEN, "render.js"), yml, out], { stdio: "pipe" });
  assert.ok(fs.existsSync(out) && fs.statSync(out).size > 20000);
});

// Regresión: sin 2º argumento, el .pptx debe quedar junto al .yml. crearPptx() hace
// chdir a Recursos/, así que una salida relativa se escribía allí por error.
test("sin ruta de salida, el .pptx queda junto al contenido.yml", () => {
  const dir = fs.mkdtempSync(path.join(TMP, "default-"));
  const yml = path.join(dir, "contenido.yml");
  fs.writeFileSync(yml,
    "cliente: Demo Salida\nnit: \"900.000.000-0\"\ntipo_servicio: organizacional\nplan: Pro\nfecha_envio: \"2026-04-30\"\nslides:\n  - tipo: portada\n");
  execFileSync("node", [path.join(GEN, "render.js"), yml], { stdio: "pipe" });
  const esperado = path.join(dir, "Demo_Salida.pptx");
  assert.ok(fs.existsSync(esperado), `no se escribió en ${esperado}`);
  assert.ok(!fs.existsSync(path.join(ROOT, "Recursos", "contenido.pptx")),
    "no debe escribir dentro de Recursos/");
});

// Regresión: sector_generico_latam no tiene cita en casos-exito.md, y el layout
// dibujaba la tarjeta igual → salía un “” vacío en el deck de un cliente.
test("caso de éxito sin cita no deja comillas vacías", async () => {
  const JSZip = require("jszip");   // viene con pptxgenjs; el .pptx es un zip
  const out = path.join(TMP, "_caso.pptx");
  const yml = path.join(TMP, "_caso.yml");
  // "Comunicaciones" no matchea ningún sector del mapa → cae en el genérico, que no tiene cita.
  fs.writeFileSync(yml,
    "cliente: Demo\nsector: Comunicaciones\ntipo_servicio: organizacional\nplan: Pro\nfecha_envio: \"2026-04-30\"\nslides:\n  - tipo: caso-exito\n");
  execFileSync("node", [path.join(GEN, "render.js"), yml, out], { stdio: "pipe" });
  const zip = await JSZip.loadAsync(fs.readFileSync(out));
  const xml = await zip.file("ppt/slides/slide1.xml").async("string");
  assert.ok(!/<a:t>\s*[“"]\s*[”"]\s*<\/a:t>/.test(xml), "quedaron comillas vacías en la slide");
});

test("tipo desconocido falla con mensaje claro", () => {
  const bad = path.join(TMP, "_bad.yml");
  fs.writeFileSync(bad, "cliente: X\nslides:\n  - tipo: no-existe\n");
  assert.throws(() => execFileSync("node",
    [path.join(GEN, "render.js"), bad], { stdio: "pipe" }),
    /tipo.*no-existe|desconocido/i);
});
