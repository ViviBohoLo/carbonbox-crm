// render.js — motor de cotización. Carga contenido.yml, hace dispatch por tipo
// de slide a lib/layouts.js, y guarda el .pptx.
// Uso: node render.js <contenido.yml> [salida.pptx]
const fs = require("fs");
const path = require("path");
const yaml = require("js-yaml");
const B = require("./lib/base");
const { LAYOUTS } = require("./lib/layouts");
const textos = require("./lib/textos");

const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
  "agosto", "septiembre", "octubre", "noviembre", "diciembre"];

function fmtFecha(iso) {
  const [y, m, d] = (iso || "").split("-");
  return d ? `${+d} de ${MESES[+m - 1]} de ${y}` : (iso || "");
}

function fechaLimite(iso, dias = 60) {
  if (!iso) return "";
  const dt = new Date(iso + "T00:00:00Z");
  dt.setUTCDate(dt.getUTCDate() + dias);
  return `${dt.getUTCDate()} de ${MESES[dt.getUTCMonth()]} de ${dt.getUTCFullYear()}`;
}

function tipoServicioFmt(t) {
  return ({
    organizacional: "Estimación de huella de carbono organizacional",
    producto: "Medición de huella de carbono de producto",
    evento: "Medición de huella de carbono de evento",
    certificacion: "Medición de huella de carbono y certificación de carbono neutralidad",
  })[t] || t;
}

function main() {
  const [, , yamlPath, outArg] = process.argv;
  if (!yamlPath) { console.error("uso: node render.js <contenido.yml> [salida.pptx]"); process.exit(2); }
  const doc = yaml.load(fs.readFileSync(yamlPath, "utf8"));
  const slides = doc.slides || [];
  // La ruta de salida se resuelve ANTES de crearPptx(): esa función hace chdir a
  // Recursos/ (las imágenes se cargan por ruta relativa), y una salida relativa
  // terminaría escrita dentro de Recursos/ en vez de la carpeta del cliente.
  const out = path.resolve(outArg || path.join(path.dirname(yamlPath),
    `${(doc.cliente || "cotizacion").replace(/[^\w]+/g, "_")}.pptx`));
  const ctx = {
    cliente: doc.cliente, nit: doc.nit, plan: doc.plan, sector: doc.sector,
    tipo_servicio: doc.tipo_servicio, tipo_servicio_fmt: tipoServicioFmt(doc.tipo_servicio),
    atica: !!doc.atica,
    fecha_envio: doc.fecha_envio, fecha_envio_fmt: fmtFecha(doc.fecha_envio),
    fecha_limite_fmt: fechaLimite(doc.fecha_envio, 60),
    num_empleados: doc.num_empleados,
    precios: {
      final: doc.precio_final, mensual: doc.precio_mensual,
      atica: doc.precio_atica, mensual_atica: doc.precio_mensual_atica,
    },
    fijos: textos.cargarTextosFijos(), casos: textos.cargarCasos(),
    NT: slides.length,
  };
  const p = B.crearPptx();
  slides.forEach((slide, idx) => {
    const fn = LAYOUTS[slide.tipo];
    if (!fn) { console.error(`Error: tipo de slide desconocido: '${slide.tipo}' (slide #${idx + 1})`); process.exit(1); }
    fn(p, { ...slide, idx: idx + 1 }, { ...ctx, idx: idx + 1 });
  });
  return p.writeFile({ fileName: out }).then(() => console.log("OK:", out));
}

main();
