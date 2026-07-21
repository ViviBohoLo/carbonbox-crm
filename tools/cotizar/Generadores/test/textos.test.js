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
