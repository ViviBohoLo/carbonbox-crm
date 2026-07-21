const fs = require("fs");
const path = require("path");
const INSUMOS = path.join(__dirname, "..", "..", "Insumos");

// Parser genérico: divide por encabezados markdown ## y ### y devuelve {clave: cuerpo}.
// La clave es el primer token [A-Za-z0-9_] tras el encabezado (ej: "## slide_04 — ..." -> "slide_04").
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
