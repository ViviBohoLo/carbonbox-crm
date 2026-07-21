// Tests de registrar-cotizacion.js — el único componente que escribe en el CRM.
// NO tocan el CRM real: se simula global.fetch y se verifica qué mutaciones se envían.
const { test } = require("node:test");
const assert = require("node:assert");

// El token se lee en cada request; con la variable de entorno no se toca ningún archivo.
process.env.TWENTY_API_TOKEN = "token-de-prueba";

const R = require("../registrar-cotizacion");

test("planACodigo mapea los planes de la calculadora al campo del CRM", () => {
  assert.equal(R.planACodigo("esencial"), "ESENCIAL");
  assert.equal(R.planACodigo("Pro"), "PRO");
  assert.equal(R.planACodigo("PRO"), "PRO");
  // El CRM no tiene "Experto": se guarda como Premium (decisión de Viviana 2026-07-21)
  assert.equal(R.planACodigo("experto"), "PREMIUM");
  assert.equal(R.planACodigo("Experto"), "PREMIUM");
});

test("planACodigo devuelve null si el plan no se reconoce", () => {
  assert.equal(R.planACodigo("otro"), null);
  assert.equal(R.planACodigo(""), null);
  assert.equal(R.planACodigo(undefined), null);
});

// CRM falso. `empresa` y `oportunidad` definen qué "ya existe" en el CRM.
// Devuelve las llamadas registradas para poder afirmar sobre ellas.
function crmFalso({ empresa = null, oportunidad = null } = {}) {
  const llamadas = [];
  global.fetch = async (_url, opts) => {
    const { query, variables } = JSON.parse(opts.body);
    llamadas.push({ query, variables });
    let data;
    if (query.includes("createCompany")) data = { createCompany: { id: "comp-nueva" } };
    else if (query.includes("updateCompany")) data = { updateCompany: { id: variables.id } };
    else if (query.includes("companies(")) data = { companies: { edges: empresa ? [{ node: empresa }] : [] } };
    else if (query.includes("createOpportunity")) data = { createOpportunity: { id: "opp-nueva" } };
    else if (query.includes("updateOpportunity")) data = { updateOpportunity: { id: variables.id } };
    else if (query.includes("opportunities(")) data = { opportunities: { edges: oportunidad ? [{ node: oportunidad }] : [] } };
    else if (query.includes("createNoteTarget")) data = { createNoteTarget: { id: "nt-1" } };
    else if (query.includes("createNote")) data = { createNote: { id: "nota-1" } };
    else throw new Error("query inesperada en el CRM falso: " + query.slice(0, 80));
    return { json: async () => ({ data }) };
  };
  return llamadas;
}

const buscar = (llamadas, frag) => llamadas.filter(l => l.query.includes(frag));
const BASE = { cliente: "Acme S.A.S.", nit: "900123456-7", plan: "Pro", precio: 1937, servicio: "Huella organizacional", nota: null };

test("empresa nueva: se crea con el NIT", async () => {
  const llamadas = crmFalso();
  await R.registrarCotizacion(BASE);
  const [creacion] = buscar(llamadas, "createCompany");
  assert.ok(creacion, "no se creó la empresa");
  assert.equal(creacion.variables.data.name, "Acme S.A.S.");
  assert.equal(creacion.variables.data.nit, "900123456-7");
});

test("empresa existente sin NIT: se rellena", async () => {
  const llamadas = crmFalso({ empresa: { id: "comp-1", name: "Acme S.A.S.", nit: "" } });
  await R.registrarCotizacion(BASE);
  assert.equal(buscar(llamadas, "createCompany").length, 0, "no debía crear una empresa nueva");
  const [update] = buscar(llamadas, "updateCompany");
  assert.ok(update, "no se rellenó el NIT");
  assert.equal(update.variables.data.nit, "900123456-7");
});

test("empresa existente CON NIT: no se pisa", async () => {
  const llamadas = crmFalso({ empresa: { id: "comp-1", name: "Acme S.A.S.", nit: "901999999-9" } });
  await R.registrarCotizacion(BASE);
  assert.equal(buscar(llamadas, "updateCompany").length, 0, "no debía tocar el NIT existente");
});

test("con oportunidad abierta: la mueve, no crea otra", async () => {
  const llamadas = crmFalso({
    empresa: { id: "comp-1", name: "Acme S.A.S.", nit: "900123456-7" },
    oportunidad: { id: "opp-1", name: "Acme — HC", stage: "DEMO" },
  });
  const r = await R.registrarCotizacion(BASE);
  assert.equal(buscar(llamadas, "createOpportunity").length, 0, "no debía crear otra oportunidad");
  const [mov] = buscar(llamadas, "updateOpportunity");
  assert.ok(mov, "no movió la oportunidad");
  assert.equal(mov.variables.data.stage, "PROPUESTA_ENVIADA");
  assert.equal(r.oppId, "opp-1");
});

test("sin oportunidad abierta: crea una en Propuesta enviada", async () => {
  const llamadas = crmFalso({ empresa: { id: "comp-1", name: "Acme S.A.S.", nit: "900123456-7" } });
  const r = await R.registrarCotizacion(BASE);
  const [creacion] = buscar(llamadas, "createOpportunity");
  assert.ok(creacion, "no creó la oportunidad");
  assert.equal(creacion.variables.data.stage, "PROPUESTA_ENVIADA");
  assert.equal(creacion.variables.data.companyId, "comp-1");
  assert.equal(creacion.variables.data.amount.amountMicros, 1937 * 1e6);
  assert.equal(r.oppId, "opp-nueva");
});

test("la nota lleva servicio, plan, NIT y precio, y queda vinculada", async () => {
  const llamadas = crmFalso();
  const r = await R.registrarCotizacion({ ...BASE, nota: "Enviada por correo." });
  const [nota] = buscar(llamadas, "createNote");
  const md = nota.variables.data.bodyV2.markdown;
  assert.match(md, /\*\*Servicio:\*\* Huella organizacional/);
  assert.match(md, /\*\*Plan:\*\* Pro/);
  assert.match(md, /\*\*NIT:\*\* 900123456-7/);
  assert.match(md, /1,937 USD/);
  assert.match(md, /Enviada por correo\./);
  const [vinculo] = buscar(llamadas, "createNoteTarget");
  assert.equal(vinculo.variables.data.targetOpportunityId, r.oppId);
});

test("sin precio no se manda amount ni línea de precio", async () => {
  const llamadas = crmFalso();
  await R.registrarCotizacion({ ...BASE, precio: null });
  const [creacion] = buscar(llamadas, "createOpportunity");
  assert.equal(creacion.variables.data.amount, undefined);
  const [nota] = buscar(llamadas, "createNote");
  assert.ok(!/\*\*Precio:\*\*/.test(nota.variables.data.bodyV2.markdown));
});

test("solo busca oportunidades abiertas (no PERDIDO ni CERRADO_GANADO)", async () => {
  const llamadas = crmFalso({ empresa: { id: "comp-1", name: "Acme S.A.S.", nit: "900123456-7" } });
  await R.registrarCotizacion(BASE);
  const [consulta] = buscar(llamadas, "opportunities(");
  assert.ok(!consulta.query.includes("PERDIDO"), "no debe reactivar oportunidades perdidas");
  assert.ok(!consulta.query.includes("CERRADO_GANADO"), "no debe tocar negocios ya cerrados");
  assert.ok(consulta.query.includes("PROPUESTA_ENVIADA"));
});

test("parseArgs lee los argumentos de la línea de comandos", () => {
  const a = R.parseArgs(["--cliente", "Acme S.A.S.", "--nit", "900123456-7", "--plan", "Pro"]);
  assert.deepEqual(a, { cliente: "Acme S.A.S.", nit: "900123456-7", plan: "Pro" });
});
