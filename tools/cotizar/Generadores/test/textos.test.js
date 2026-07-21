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

// El mapa de sectores se declara en casos-exito.md ("Sectores: a, b"), no en el código.
test("el mapa de sectores sale del .md", () => {
  const mapa = t.mapaSectores(t.cargarCasos());
  assert.ok(mapa.length >= 6, "deberían mapearse al menos 6 casos");
  const manu = mapa.find(([clave]) => clave === "sector_manufactura");
  assert.ok(manu && manu[1].includes("manufactura"));
  // El genérico es el fallback: no declara sectores.
  assert.ok(!mapa.some(([clave]) => clave === "sector_generico_latam"));
});

test("solo hay secciones de caso reales (el ejemplo del encabezado no cuenta)", () => {
  const claves = Object.keys(t.cargarCasos());
  assert.ok(claves.every(k => k.startsWith("sector_")), `claves inesperadas: ${claves}`);
  assert.ok(!claves.includes("sector_ejemplo"), "el ejemplo del encabezado se coló como caso");
});

// Regresión: "agroindustria" contiene "industri", así que caía en sector_manufactura.
// Se resuelve con el orden del archivo: el caso más específico va primero.
test("agroindustria no cae en manufactura", () => {
  assert.equal(t.casoPorSector("Agroindustria"), "sector_agroindustria");
  assert.equal(t.casoPorSector("Sector agroindustrial"), "sector_agroindustria");
  assert.equal(t.casoPorSector("Industria manufacturera"), "sector_manufactura");
});

test("el sector se compara sin tildes ni mayúsculas", () => {
  assert.equal(t.casoPorSector("ENERGÍA"), "sector_manufactura");
  assert.equal(t.casoPorSector("energia"), "sector_manufactura");
  assert.equal(t.casoPorSector("Público"), "sector_financiero");
});
