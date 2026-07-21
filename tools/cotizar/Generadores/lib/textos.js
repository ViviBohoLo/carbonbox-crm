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
//
// Los sectores de cada caso NO viven aquí: se declaran en Insumos/casos-exito.md con una
// línea "Sectores: a, b, c" dentro de la sección. Así se agrega un sector nuevo editando
// solo texto, sin tocar código. Gana la primera sección que coincida, en orden del archivo;
// si ninguna coincide se usa el genérico.
const CLAVE_FALLBACK = "sector_generico_latam";
const RE_SECTORES = /^[ \t]*Sectores?[ \t]*:[ \t]*(.+)$/im;

// minúsculas y sin tildes, para que "Energía" y "energia" coincidan igual.
function normalizar(s) {
  return (s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
}

// [[clave, [palabras]], ...] en el orden en que aparecen las secciones del .md.
function mapaSectores(casos) {
  const out = [];
  for (const [clave, cuerpo] of Object.entries(casos || {})) {
    const m = (cuerpo || "").match(RE_SECTORES);
    if (!m) continue;
    const palabras = m[1].split(",").map(normalizar).filter(Boolean);
    if (palabras.length) out.push([clave, palabras]);
  }
  return out;
}

function casoPorSector(sectorCliente, casos) {
  const s = normalizar(sectorCliente);
  if (!s) return CLAVE_FALLBACK;
  for (const [clave, palabras] of mapaSectores(casos || cargarCasos())) {
    if (palabras.some(p => s.includes(p))) return clave;
  }
  return CLAVE_FALLBACK;
}

module.exports = { cargarTextosFijos, cargarCasos, casoPorSector, mapaSectores, parseSecciones };
