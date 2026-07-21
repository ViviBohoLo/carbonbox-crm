#!/usr/bin/env node
/**
 * Registra en el CRM (Twenty, crm.carbonbox.app) que se envió una cotización.
 *
 * Busca o crea la Empresa + Oportunidad del cliente y la mueve a la etapa
 * "Propuesta enviada" (PROPUESTA_ENVIADA), con una nota con plan, precio y NIT.
 * Replica los patrones de crm-scripts/crm_lib.py y lead_intake.py del repo
 * carbonbox-crm (solo como referencia — este script vive en tools/cotizar,
 * NO modifica los scripts de infraestructura del CRM).
 *
 * ⚠️ REQUIERE UN TOKEN LOCAL — nunca lo pegues en el chat con Claude.
 * Ya debe existir en esta carpeta como "token crm.txt" (o un archivo .env
 * con la línea TWENTY_API_TOKEN=...). Ese archivo es local, no lo subas al repo.
 *
 * Uso (desde esta carpeta, en PowerShell o cmd):
 *   node registrar-cotizacion.js --cliente "Hotel Waya Guajira" --nit "900.123.456-7" --plan Pro --precio 4101 --servicio "Estimación de huella de carbono organizacional" --nota "Cotización enviada por correo el 16 de julio de 2026"
 *
 * Nota: el mapeo de campos/mutaciones GraphQL sigue el patrón observado en
 * crm_lib.py y lead_intake.py del repo. Primera corrida: verifica que la
 * oportunidad y la nota queden bien en crm.carbonbox.app.
 */

const fs = require("fs");
const path = require("path");

const CORE = "https://crm.carbonbox.app/graphql";
const HERE = __dirname;
const ENV_FILE = path.join(HERE, ".env");
const TOKEN_FILE_ALT = path.join(HERE, "token crm.txt"); // formato simple: solo el token

function cargarToken() {
  if (process.env.TWENTY_API_TOKEN) return process.env.TWENTY_API_TOKEN.trim();
  if (fs.existsSync(ENV_FILE)) {
    const txt = fs.readFileSync(ENV_FILE, "utf8");
    const m = txt.split(/\r?\n/).find(l => l.trim().startsWith("TWENTY_API_TOKEN="));
    if (m) return m.trim().split("=").slice(1).join("=").trim();
  }
  if (fs.existsSync(TOKEN_FILE_ALT)) {
    const tok = fs.readFileSync(TOKEN_FILE_ALT, "utf8").trim();
    if (tok) return tok;
  }
  console.error("❌ No encontré el token de Twenty.");
  console.error(`   Crea el archivo ${ENV_FILE} con la línea: TWENTY_API_TOKEN=tu_token_aqui`);
  console.error(`   (o un archivo ${TOKEN_FILE_ALT} con solo el token)`);
  process.exit(1);
}

async function gql(query, variables = {}) {
  if (typeof fetch === "undefined") {
    console.error("❌ Tu versión de Node no tiene fetch incorporado (necesitas Node 18+).");
    console.error("   Dime qué versión tienes (node --version) y lo adapto.");
    process.exit(1);
  }
  const token = cargarToken();
  const res = await fetch(CORE, {
    method: "POST",
    headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ query, variables })
  });
  const out = await res.json();
  if (out.errors) {
    throw new Error(JSON.stringify(out.errors).slice(0, 800));
  }
  return out.data;
}

// El NIT se guarda en Company.nit, que es de donde lo lee el flujo /cotizar al preparar
// la siguiente cotización. Antes solo quedaba escrito dentro del texto de la nota, así que
// una empresa creada por este script quedaba sin NIT utilizable.
async function findOrCreateCompany(nombre, nit) {
  let d = await gql(`query($n: String!) { companies(filter:{name:{ilike:$n}}, first:1) {
      edges { node { id name nit } } } }`, { n: nombre });
  if (d.companies.edges.length) {
    const c = d.companies.edges[0].node;
    // Si ya tiene NIT no lo pisamos: el del CRM manda sobre el que venga por argumento.
    if (nit && !c.nit) {
      await gql(`mutation($id: UUID!, $data: CompanyUpdateInput!) {
          updateCompany(id:$id, data:$data) { id } }`, { id: c.id, data: { nit } });
    }
    return c.id;
  }
  const data = { name: nombre };
  if (nit) data.nit = nit;
  d = await gql(`mutation($data: CompanyCreateInput!) { createCompany(data:$data) { id } }`, { data });
  return d.createCompany.id;
}

async function findOpenOpportunity(companyId) {
  const d = await gql(`query($cid: UUID!) { opportunities(
      filter: { companyId: { eq: $cid },
                stage: { in: ["LEAD_CAPTURADO","CALIFICACION_BANT","DEMO",
                               "PILOTO_45D","PROPUESTA_ENVIADA","EN_NEGOCIACION",
                               "RENOVACION","NURTURING"] } }, first: 1) {
      edges { node { id name stage } } } }`, { cid: companyId });
  const edges = d.opportunities.edges;
  return edges.length ? edges[0].node : null;
}

async function crearOportunidad(companyId, nombreCliente, servicio, precio) {
  const odata = { name: `${nombreCliente} — ${servicio}`, stage: "PROPUESTA_ENVIADA", companyId };
  if (precio) odata.amount = { amountMicros: Math.round(precio * 1_000_000), currencyCode: "USD" };
  const d = await gql(`mutation($data: OpportunityCreateInput!) { createOpportunity(data:$data) { id } }`,
    { data: odata });
  return d.createOpportunity.id;
}

// La calculadora maneja Esencial/Pro/Experto; el campo planCarbonbox del CRM tiene
// ESENCIAL/PRO/PREMIUM/ENTERPRISE/LICITACION. "Experto" se guarda como PREMIUM.
const PLAN_A_CODIGO = { esencial: "ESENCIAL", pro: "PRO", experto: "PREMIUM" };

function planACodigo(plan) {
  if (!plan) return null;
  return PLAN_A_CODIGO[String(plan).trim().toLowerCase()] || null;
}

async function moverAPropuestaEnviada(oppId, precio, extras = {}) {
  const data = { stage: "PROPUESTA_ENVIADA" };
  if (precio) data.amount = { amountMicros: Math.round(precio * 1_000_000), currencyCode: "USD" };
  const codigo = planACodigo(extras.plan);
  if (codigo) data.planCarbonbox = codigo;
  if (extras.linkCotizacion) {
    data.linkCotizacion = { primaryLinkUrl: extras.linkCotizacion, primaryLinkLabel: "Cotización" };
  }
  if (extras.borrador) data.borradorCorreo = extras.borrador;
  await gql(`mutation($id: UUID!, $data: OpportunityUpdateInput!) {
      updateOpportunity(id:$id, data:$data) { id } }`, { id: oppId, data });
}

async function agregarNota(oppId, texto) {
  const d = await gql(`mutation($data: NoteCreateInput!) { createNote(data:$data) { id } }`,
    { data: { title: "Cotización enviada", bodyV2: { markdown: texto } } });
  const noteId = d.createNote.id;
  await gql(`mutation($data: NoteTargetCreateInput!) { createNoteTarget(data:$data) { id } }`,
    { data: { noteId, targetOpportunityId: oppId } });
}

async function registrarCotizacion({ cliente, nit, plan, precio, servicio, nota, linkCotizacion, borrador }) {
  const companyId = await findOrCreateCompany(cliente, nit);
  const existente = await findOpenOpportunity(companyId);
  const extras = { plan, linkCotizacion, borrador };

  let oppId, accion;
  if (existente) {
    oppId = existente.id;
    await moverAPropuestaEnviada(oppId, precio, extras);
    accion = `Oportunidad existente actualizada → Propuesta enviada (${existente.name})`;
  } else {
    oppId = await crearOportunidad(companyId, cliente, servicio, precio);
    await moverAPropuestaEnviada(oppId, precio, extras);
    accion = "Oportunidad nueva creada en Propuesta enviada";
  }

  const fecha = new Date().toLocaleDateString("es-CO", { day: "numeric", month: "long", year: "numeric" });
  let texto = `**Servicio:** ${servicio}\n**Plan:** ${plan}\n**NIT:** ${nit}\n`;
  if (precio) texto += `**Precio:** $${Number(precio).toLocaleString("en-US")} USD\n`;
  texto += `**Fecha de envío:** ${fecha}\n`;
  if (nota) texto += `\n${nota}`;
  await agregarNota(oppId, texto);
  return { oppId, accion, texto };
}

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith("--")) {
      const key = argv[i].slice(2);
      const val = argv[i + 1];
      out[key] = val;
      i++;
    }
  }
  return out;
}

// Solo corre como CLI. Al importarlo (los tests) no ejecuta nada contra el CRM.
if (require.main === module) {
  const args = parseArgs(process.argv.slice(2));
  if (!args.cliente || !args.nit || !args.plan) {
    console.error("Uso: node registrar-cotizacion.js --cliente \"Nombre\" --nit \"900...\" --plan Pro [--precio 4101] [--servicio \"...\"] [--nota \"...\"]");
    process.exit(1);
  }

  // El borrador se pasa por ARCHIVO, no por argumento: es largo y multilínea, y como
  // argumento de shell se rompe con las comillas y los saltos de línea.
  let borrador = null;
  if (args["borrador-archivo"]) borrador = fs.readFileSync(args["borrador-archivo"], "utf8");

  registrarCotizacion({
    cliente: args.cliente,
    nit: args.nit,
    plan: args.plan,
    precio: args.precio ? parseFloat(args.precio) : null,
    servicio: args.servicio || "Estimación de huella de carbono",
    nota: args.nota || null,
    linkCotizacion: args["link-cotizacion"] || null,
    borrador
  }).then(({ oppId, accion }) => {
    console.log(`✅ ${accion}`);
    console.log(`   Oportunidad: ${oppId}`);
    console.log(`   CRM: https://crm.carbonbox.app/object/opportunity/${oppId}`);
  }).catch(e => { console.error("ERROR:", e.message); process.exit(1); });
}

module.exports = {
  registrarCotizacion, findOrCreateCompany, findOpenOpportunity,
  crearOportunidad, moverAPropuestaEnviada, agregarNota, parseArgs, planACodigo,
};
