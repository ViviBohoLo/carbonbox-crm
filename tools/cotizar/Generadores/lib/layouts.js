// lib/layouts.js — un layout por tipo de slide. Cada fn(p, slide, ctx) agrega la diapo.
// Portado de generador-pptx-pepsico.js; las partes fijas (marca) quedan iguales y las
// variables se leen de ctx/slide/ctx.fijos/ctx.casos. NO rediseñar: mismos tokens/posiciones.
const B = require("./base");
const textos = require("./textos");

function anchoChip(label) { return Math.max(1.4, 0.55 + 0.12 * label.length); }
function planKey(plan) {
  const s = String(plan || "").toLowerCase();
  if (s.startsWith("ese") || s.startsWith("ess")) return "essential";
  if (s.startsWith("exp")) return "expert";
  return "pro";
}
function fmtMiles(n) {
  if (n == null) return "";
  return "$ " + Math.round(Number(n)).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}
function pesosMes(n) { return "$" + Math.round(Number(n)).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".") + " USD/mes"; }
function itemsDe(md) {
  return (md || "").split(/\r?\n/)
    .filter(l => /^\s*(?:\d+\.|[-*✓])\s+/.test(l))
    .map(l => l.replace(/^\s*(?:\d+\.|[-*✓])\s+/, "").trim());
}

/* ---------- SLIDE 1 — PORTADA ---------- */
function portada(p, slide, ctx) {
  const s = p.addSlide(); s.background = { color: B.DARK };
  if (B.exists("cover_bg.png")) {
    s.addImage({ path: "cover_bg.png", x: 0, y: 0, w: B.W, h: B.H });
  } else {
    s.addShape(p.shapes.RECTANGLE, { x: 0, y: 0, w: B.W, h: B.H, fill: { color: B.DARK } });
    s.addImage({ path: B.ICON_WHITE, x: 8.7, y: -1.6, w: 6.6, h: 6.6, transparency: 88 });
    s.addImage({ path: B.ICON_WHITE, x: 9.7, y: 4.4, w: 5.0, h: 5.0, transparency: 91 });
  }
  B.wordmark(s, B.MX, 0.5, B.WHITE);
  s.addText("COTIZACIÓN COMERCIAL", { x: B.MX, y: 2.0, w: 9, h: 0.35, fontFace: B.F, fontSize: 12, bold: true, color: B.MINT, charSpacing: 3 });
  s.addText(ctx.tipo_servicio_fmt || "", { x: B.MX, y: 2.4, w: 8.2, h: 1.8, fontFace: B.F, fontSize: 40, bold: true, color: B.WHITE, lineSpacingMultiple: 1.02 });
  s.addText([{ text: "Preparada para ", options: { color: "CDD3F5" } }, { text: ctx.cliente || "", options: { color: B.WHITE, bold: true } }],
    { x: B.MX, y: 4.45, w: 9, h: 0.5, fontFace: B.F, fontSize: 18 });
  if (ctx.nit) s.addText("NIT " + ctx.nit, { x: B.MX, y: 4.85, w: 9, h: 0.3, fontFace: B.FM, fontSize: 11, color: "AAB2E8" });
  const chip = "PLAN " + String(ctx.plan || "").toUpperCase();
  const cw = anchoChip(chip);
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: B.MX, y: 5.25, w: cw, h: 0.5, rectRadius: 0.25, fill: { color: "2F6B4A" } });
  s.addText(chip, { x: B.MX, y: 5.25, w: cw, h: 0.5, fontFace: B.F, fontSize: 12, bold: true, color: B.WHITE, charSpacing: 1, align: "center", valign: "middle" });
  const desc = slide.descripcion || ctx.fijos.portada_desc || "";
  if (desc) s.addText(desc, { x: B.MX, y: 5.88, w: 8.4, h: 0.65, fontFace: B.F, fontSize: 13, color: "CDD3F5", lineSpacingMultiple: 1.2 });
  s.addText([{ text: (ctx.fecha_envio_fmt || "") + "     ·     Validez 60 días     ·     ", options: { color: "AAB2E8" } },
    { text: "www.carbonbox.app", options: { color: B.MINT, hyperlink: { url: "https://www.carbonbox.app" } } }],
    { x: B.MX, y: 6.75, w: 12, h: 0.4, fontFace: B.FM, fontSize: 11 });
  return s;
}

/* ---------- SLIDE 2 — CONTEXTO + NECESIDAD ---------- */
function contextoNecesidad(p, slide, ctx) {
  const s = p.addSlide();
  B.header(s, String(ctx.idx).padStart(2, "0"), "El cliente: contexto y necesidad", "El cliente primero", ctx.NT);
  s.addShape(p.shapes.LINE, { x: 6.67, y: 2.7, w: 0, h: 3.4, line: { color: B.LINE, width: 1 } });
  s.addText("LO QUE SABEMOS", { x: B.MX, y: 2.65, w: 5.4, h: 0.35, fontFace: B.F, fontSize: 12, bold: true, color: B.ACC, charSpacing: 2 });
  s.addText(ctx.cliente || "", { x: B.MX, y: 3.05, w: 5.4, h: 0.4, fontFace: B.F, fontSize: 17, bold: true, color: B.P });
  s.addText(slide.sabemos || "[⚠️ PENDIENTE: contexto del cliente]", { x: B.MX, y: 3.5, w: 5.35, h: 2.5, fontFace: B.F, fontSize: 13.5, color: B.INK2, lineSpacingMultiple: 1.25 });
  s.addText("LO QUE NECESITA", { x: 7.0, y: 2.65, w: 5.4, h: 0.35, fontFace: B.F, fontSize: 12, bold: true, color: B.ACC, charSpacing: 2 });
  s.addText(slide.titulo_necesidad || "Su necesidad", { x: 7.0, y: 3.05, w: 5.4, h: 0.4, fontFace: B.F, fontSize: 17, bold: true, color: B.P });
  s.addText(slide.necesita || "[⚠️ PENDIENTE: necesidad del cliente]", { x: 7.0, y: 3.5, w: 5.4, h: 2.5, fontFace: B.F, fontSize: 13.5, color: B.INK2, lineSpacingMultiple: 1.25 });
  B.footer(s, ctx.cliente);
  return s;
}

/* ---------- SLIDE 3 — QUÉ ES CARBONBOX ---------- */
function queEsCarbonbox(p, slide, ctx) {
  const s = p.addSlide();
  B.header(s, String(ctx.idx).padStart(2, "0"), "Qué es CarbonBox", "Nuestra solución", ctx.NT);
  s.addText("Una plataforma que mide, reduce y compensa la huella de carbono de tu empresa — con tecnología y un experto dedicado.",
    { x: B.MX, y: 2.4, w: 5.8, h: 0.9, fontFace: B.F, fontSize: 16, color: B.INK2, lineSpacingMultiple: 1.25 });
  const f4 = [["Medición de CO₂", "Alcances 1, 2 y 3 con datos confiables.", "ic_measure.png"],
  ["Reducción de CO₂", "Acciones priorizadas con costo-beneficio.", "ic_reduce.png"],
  ["Compensación de CO₂", "Metas de neutralidad y descarbonización.", "ic_offset.png"]];
  f4.forEach((c, i) => {
    const y = 3.45 + i * 0.8; B.icon(s, B.MX, y, 0.6, c[2], "FFFFFF");
    s.addText(c[0], { x: B.MX + 0.8, y: y - 0.02, w: 5.0, h: 0.32, fontFace: B.F, fontSize: 14, bold: true, color: B.P });
    s.addText(c[1], { x: B.MX + 0.8, y: y + 0.3, w: 5.0, h: 0.32, fontFace: B.F, fontSize: 11.5, color: B.INK2 });
  });
  s.addText("30% menos tiempo de gestión  ·  40% más productividad", { x: B.MX, y: 5.95, w: 5.8, h: 0.35, fontFace: B.F, fontSize: 13, bold: true, color: B.ACD });
  if (B.exists("s4_hero.png")) s.addImage({ path: "s4_hero.png", x: 7.05, y: 1.7, w: 5.2, h: 4.45 });
  s.addText("Alineado a estándares internacionales:", { x: 7.05, y: 6.32, w: 3.3, h: 0.3, fontFace: B.F, fontSize: 10.5, color: B.INK3, valign: "middle" });
  if (B.exists("std_ghg.png")) s.addImage({ path: "std_ghg.png", x: 10.4, y: 6.28, w: 1.15, h: 0.48 });
  if (B.exists("std_iso.png")) s.addImage({ path: "std_iso.png", x: 11.65, y: 6.25, w: 0.5, h: 0.5 });
  B.footer(s, ctx.cliente);
  return s;
}

/* ---------- SLIDE 4 — VENTAJAS ---------- */
const VENTAJAS_ICONOS = ["ic_cap.png", "ic_chart.png", "ic_users.png", "ic_award.png"];
function ventajas(p, slide, ctx) {
  const s = p.addSlide();
  B.header(s, String(ctx.idx).padStart(2, "0"), "Ventajas de trabajar con nosotros", "Nuestra solución", ctx.NT);
  if (B.exists("s5_stars.png")) s.addImage({ path: "s5_stars.png", x: B.MX, y: 2.85, w: 4.7, h: 3.21 });
  s.addText("Un experto dedicado acompaña tu proceso en todos los planes.", { x: B.MX, y: 6.05, w: 4.7, h: 0.5, fontFace: B.F, fontSize: 12, italic: true, color: B.INK3 });
  const stake = ctx.stakeholders || "Juntas Directivas, Inversionistas y Clientes";
  const adv = [
    "Capacidades en medición, reducción y compensación para ti y tu equipo.",
    "Decisiones estratégicas con dashboards claros y accionables.",
    `Una herramienta atractiva para presentar ante ${stake}.`,
    "Te destacas integrando soluciones innovadoras y tecnológicas.",
  ];
  adv.forEach((t, i) => {
    const y = 2.6 + i * 0.85; B.icon(s, 5.95, y, 0.6, VENTAJAS_ICONOS[i], "FFFFFF");
    s.addText(t, { x: 6.7, y: y - 0.05, w: 5.9, h: 0.72, fontFace: B.F, fontSize: 13.5, color: B.INK2, valign: "middle" });
  });
  B.card(s, 5.95, 6.05, 6.65, 0.92, B.ASOFT, "CFE6DA");
  B.icon(s, 6.15, 6.27, 0.5, "ic_piggy.png", "FFFFFF");
  s.addText("Año a año serás más autónomo y obtendrás ahorros gestionando tu huella y tu operación.",
    { x: 6.8, y: 6.12, w: 5.65, h: 0.78, fontFace: B.F, fontSize: 12, color: B.INK2, valign: "middle" });
  B.footer(s, ctx.cliente);
  return s;
}

/* ---------- SLIDE 5 — SOLUCIONES ---------- */
const MODULOS = {
  organizacional: [["s6_ill1.png", "Estimación de huella", "Mide tus emisiones por actividad — alcances 1, 2 y 3."],
  ["s6_ill2.png", "Reducciones", "Simula escenarios y traza tu ruta de reducción."],
  ["s6_ill3.png", "Compensaciones", "Compensa lo restante y alcanza la carbono neutralidad."]],
  evento: [["s6_ill1.png", "Estimación del evento", "Mide la huella del evento en todo su ciclo de vida."],
  ["s6_ill2.png", "Reducciones", "Simula escenarios y traza tu ruta de reducción."],
  ["s6_ill3.png", "Compensaciones", "Compensa lo restante y comunica un evento carbono neutro."]],
  producto: [["s6_ill1.png", "Medición de impacto (ACV)", "Analiza el ciclo de vida completo de tu producto."]],
};
function soluciones(p, slide, ctx) {
  const s = p.addSlide();
  B.header(s, String(ctx.idx).padStart(2, "0"), "Nuestras soluciones tecnológicas", "Nuestra solución", ctx.NT);
  s.addText("Accede por un año a los módulos que necesitas para gestionar la huella de carbono de tu empresa.",
    { x: B.MX, y: 2.4, w: 11.5, h: 0.5, fontFace: B.F, fontSize: 15, color: B.INK2 });
  const mods = MODULOS[ctx.tipo_servicio] || MODULOS.organizacional;
  const single = mods.length === 1;
  mods.forEach((c, i) => {
    const x = single ? (B.W - 3.78) / 2 : B.MX + i * 4.0;
    if (B.exists(c[0])) s.addImage({ path: c[0], x, y: 3.0, w: 3.78, h: 2.58 });
    s.addText(c[1], { x: x + 0.05, y: 5.68, w: 3.7, h: 0.4, fontFace: B.F, fontSize: 16, bold: true, color: B.P });
    s.addText(c[2], { x: x + 0.05, y: 6.08, w: 3.75, h: 0.8, fontFace: B.F, fontSize: 11.5, color: B.INK2, lineSpacingMultiple: 1.15 });
  });
  B.footer(s, ctx.cliente);
  return s;
}

/* ---------- SLIDE 6 — CASO DE ÉXITO (por sector) ---------- */
function parseCaso(md) {
  const lineas = (md || "").split(/\r?\n/);
  let titulo = "", quote = "", cierre = "", cuerpo = [];
  for (const ln of lineas) {
    const t = ln.trim(); if (!t) continue;
    if (/^[-–—]{2,}$/.test(t)) continue;   // separador markdown "---" → ignorar
    if (/^Sectores?\s*:/i.test(t)) continue;  // metadato de enrutamiento, no es texto de la slide
    const mQ = t.match(/^\*"?(.+?)"?\*$/);
    if (/^\*\*(.+)\*\*$/.test(t) && !titulo) { titulo = t.replace(/\*\*/g, ""); }
    else if (mQ) { quote = mQ[1].replace(/^"|"$/g, ""); }
    else if (quote && !cierre) { cierre = t; }
    else { cuerpo.push(t); }
  }
  return { titulo, cuerpo: cuerpo.join(" "), quote, cierre };
}
function casoExito(p, slide, ctx) {
  const s = p.addSlide();
  B.header(s, String(ctx.idx).padStart(2, "0"), "Un cliente como tú", "Confianza y credenciales", ctx.NT);
  const clave = textos.casoPorSector(ctx.sector);
  const caso = parseCaso(ctx.casos[clave] || ctx.casos["sector_generico_latam"] || "");
  const parrafo = (caso.titulo ? caso.titulo + ". " : "") + caso.cuerpo;
  s.addText(parrafo || "[⚠️ PENDIENTE: caso de éxito]", { x: B.MX, y: 2.7, w: 11.6, h: 1.5, fontFace: B.F, fontSize: 15.5, color: B.INK2, lineSpacingMultiple: 1.3 });
  // Sin cita no se dibuja la tarjeta: antes salía un “” vacío (p. ej. con
  // sector_generico_latam, que es el único caso de Insumos/casos-exito.md sin cita).
  if (caso.quote) {
    B.card(s, B.MX, 4.6, 11.75, 1.2, B.PSOFT, B.P100);
    s.addShape(p.shapes.RECTANGLE, { x: B.MX, y: 4.6, w: 0.07, h: 1.2, fill: { color: B.ACC } });
    s.addText("“" + caso.quote + "”", { x: B.MX + 0.35, y: 4.6, w: 11.1, h: 1.2, fontFace: B.F, fontSize: 16, italic: true, bold: true, color: B.P, valign: "middle" });
  }
  if (caso.cierre) s.addText(caso.cierre, { x: B.MX, y: 5.95, w: 11.5, h: 0.3, fontFace: B.F, fontSize: 12, color: B.INK3 });
  B.footer(s, ctx.cliente);
  return s;
}

/* ---------- SLIDE 7 — LOGOS ---------- */
function logos(p, slide, ctx) {
  const s = p.addSlide();
  B.header(s, String(ctx.idx).padStart(2, "0"), "Empresas que han confiado en nosotros", "Confianza y credenciales", ctx.NT);
  if (B.exists("s7_logos.png")) {
    B.fitImage(s, "s7_logos.png", B.MX, 2.55, B.W - 2 * B.MX, 4.0);
  } else {
    const ls = ["Siemens", "Biomax", "Fenavi", "Asobancaria", "Crepes & Waffles", "Estéreo Picnic", "Ara", "Colgas", "Zona Franca Bogotá", "Agrosavia", "Fundación Santa Fe", "EBSA", "Elementia", "Eternit", "Páramo Presenta", "Alcaldía de Bogotá", "Idartes", "Cámara Verde", "Colegio Anglo", "DNP", "Jerónimo Martins", "FLP", "Atica", "Fondo Acción"];
    const cols = 6, cw = 1.92, chh = 0.62, gx = 0.05, gy = 0.18, x0 = B.MX, y0 = 2.7;
    ls.forEach((t, i) => {
      const c = i % cols, r = Math.floor(i / cols); const x = x0 + c * (cw + gx), y = y0 + r * (chh + gy);
      B.card(s, x, y, cw, chh, B.SOFT, B.LINE);
      s.addText(t, { x: x + 0.05, y, w: cw - 0.1, h: chh, fontFace: B.F, fontSize: 10.5, color: B.INK2, align: "center", valign: "middle" });
    });
  }
  B.footer(s, ctx.cliente);
  return s;
}

/* ---------- SLIDE 8 — NUESTRO TRABAJO HOY (cifras oficiales) ---------- */
function trabajoHoy(p, slide, ctx) {
  const s = p.addSlide();
  B.header(s, String(ctx.idx).padStart(2, "0"), "Nuestro trabajo hoy", "Confianza y credenciales", ctx.NT);
  if (B.exists("s9_map.png")) s.addImage({ path: "s9_map.png", x: B.MX, y: 2.35, w: 3.7, h: 4.35 });
  s.addText("Hemos acompañado a 10 sectores de la economía en 6 países de Latinoamérica.",
    { x: 4.85, y: 2.5, w: 7.7, h: 0.6, fontFace: B.F, fontSize: 15, color: B.INK2, lineSpacingMultiple: 1.2 });
  const countries = ["Colombia", "Ecuador", "Paraguay", "México", "Argentina", "Perú"];
  countries.forEach((n, i) => { const cx = 4.9 + i * 1.3; B.flag(s, cx, 3.4, 0.9, 0.58, n); });
  [[">150.000", "tCO₂e estimadas"], ["~36.456", "tCO₂ reducidas por nuestros clientes"], ["6", "países de LATAM"], ["10", "sectores de la economía"]]
    .forEach((c, i) => {
      const x = 4.9 + (i % 2) * 3.95, y = 4.55 + Math.floor(i / 2) * 1.08; B.card(s, x, y, 3.75, 0.96, B.ASOFT, "CFE6DA");
      s.addText(c[0], { x: x + 0.2, y: y + 0.07, w: 3.4, h: 0.42, fontFace: B.F, fontSize: 21, bold: true, color: B.ACD, valign: "middle" });
      s.addText(c[1], { x: x + 0.2, y: y + 0.5, w: 3.45, h: 0.4, fontFace: B.F, fontSize: 10.5, color: B.INK2, valign: "middle", lineSpacingMultiple: 0.95 });
    });
  B.footer(s, ctx.cliente);
  return s;
}

/* ---------- SLIDE 9 — EQUIPO ---------- */
const TEAM = [["t_vivi_sq.png", "Viviana Bohórquez", "CEO y Co-fundadora", "15 años en estimación y reporte de reducciones de GEI. Certificada ISO 14064-1 y 2."],
["t_ale_sq.png", "Alejandra Rojas", "Líder de proyectos", "5 años en inventarios de GEI. Auditora interna de huellas de carbono y gestión de reducción y compensación."],
["t_manu_sq.png", "Manuel Rivera", "Líder en tecnología", "Full Stack, 5 años en apps web y móviles; backend y bases de datos."],
["t_lau_sq.png", "Laura Bautista", "Profesional en sostenibilidad", "3 años en reportes y gestión de la sostenibilidad y medición de impacto."],
["t_migue_sq.png", "Miguel Romero", "Profesional en sostenibilidad", "+4 años como ing. ambiental con énfasis en energías renovables y sostenibilidad; experiencia en el sector de alimentos."],
["t_eli_sq.png", "Eliezer Mas y Rubí", "Experto en tecnología", "+4 años en desarrollo web y UI/UX; líder de equipos internacionales."]];
function inicial(name) { return name.split(/\s+/).slice(0, 2).map(w => w[0]).join("").toUpperCase(); }
function equipo(p, slide, ctx) {
  const s = p.addSlide();
  B.header(s, String(ctx.idx).padStart(2, "0"), "El equipo experto", "Confianza y credenciales", ctx.NT);
  TEAM.forEach((m, i) => {
    const x = B.MX + (i % 2) * 6.0, y = 2.5 + Math.floor(i / 2) * 1.45; B.card(s, x, y, 5.75, 1.3, B.SOFT, B.LINE);
    if (B.exists(m[0])) {
      s.addImage({ path: m[0], x: x + 0.24, y: y + 0.27, w: 0.78, h: 0.78, rounding: true, sizing: { type: "cover", w: 0.78, h: 0.78 } });
    } else {
      s.addShape(p.shapes.OVAL, { x: x + 0.24, y: y + 0.27, w: 0.78, h: 0.78, fill: { color: B.PSOFT }, line: { color: B.P100, width: 1 } });
      s.addText(inicial(m[1]), { x: x + 0.24, y: y + 0.27, w: 0.78, h: 0.78, fontFace: B.F, fontSize: 16, bold: true, color: B.P, align: "center", valign: "middle" });
    }
    s.addText(m[1], { x: x + 1.18, y: y + 0.16, w: 4.5, h: 0.32, fontFace: B.F, fontSize: 12.5, bold: true, color: B.P });
    s.addText(m[2], { x: x + 1.18, y: y + 0.47, w: 4.5, h: 0.28, fontFace: B.F, fontSize: 10, bold: true, color: B.ACC });
    s.addText(m[3], { x: x + 1.18, y: y + 0.73, w: 4.55, h: 0.5, fontFace: B.F, fontSize: 9.5, color: B.INK2, lineSpacingMultiple: 1.08 });
  });
  B.footer(s, ctx.cliente);
  return s;
}

/* ---------- SLIDE 10 — PLAN (funcionalidades por plan) ---------- */
function plan(p, slide, ctx) {
  const s = p.addSlide();
  B.header(s, String(ctx.idx).padStart(2, "0"), "Plan " + (ctx.plan || ""), "La oferta · Plan propuesto", ctx.NT);
  const desc = slide.descripcion_necesidad_corta ||
    "Suscripción anual para equipos que necesitan guía técnica y reportes alineados a estándares internacionales.";
  s.addText(desc, { x: B.MX, y: 2.5, w: 11.6, h: 0.7, fontFace: B.F, fontSize: 13, color: B.INK2, lineSpacingMultiple: 1.15 });
  let feats = itemsDe(ctx.fijos["funcionalidades_" + planKey(ctx.plan)] || "");
  if (!feats.length) feats = ["[⚠️ PENDIENTE: funcionalidades del plan]"];
  feats.forEach((t, i) => {
    const x = B.MX + (i % 2) * 6.0, y = 3.35 + Math.floor(i / 2) * 0.6;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: y + 0.03, w: 0.28, h: 0.28, rectRadius: 0.05, fill: { color: B.ASOFT } });
    s.addText("✓", { x, y: y + 0.03, w: 0.28, h: 0.28, fontFace: B.F, fontSize: 11, bold: true, color: B.ACD, align: "center", valign: "middle" });
    s.addText(t, { x: x + 0.4, y: y - 0.05, w: 5.4, h: 0.5, fontFace: B.F, fontSize: 11.5, color: B.INK2, valign: "middle" });
  });
  B.footer(s, ctx.cliente);
  return s;
}

/* ---------- SLIDE 11 — INVERSIÓN (condicional ATICA) ---------- */
function inversion(p, slide, ctx) {
  const s = p.addSlide();
  B.header(s, String(ctx.idx).padStart(2, "0"), "Inversión + valor", "La oferta · Inversión", ctx.NT);
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: B.MX, y: 2.7, w: 6.7, h: 3.4, rectRadius: 0.12, fill: { color: B.P }, shadow: B.shadow() });
  const pr = ctx.precios;
  const precioFinal = ctx.atica ? pr.atica : pr.final;
  const precioMes = ctx.atica ? pr.mensual_atica : pr.mensual;
  let yTitulo;
  if (ctx.atica) {
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: B.MX + 0.4, y: 3.0, w: 2.9, h: 0.45, rectRadius: 0.22, fill: { color: B.MINT } });
    s.addText("−10% ALIANZA ATICA", { x: B.MX + 0.4, y: 3.0, w: 2.9, h: 0.45, fontFace: B.F, fontSize: 10.5, bold: true, color: B.ACD, align: "center", valign: "middle" });
    yTitulo = 3.6;
  } else { yTitulo = 3.1; }
  s.addText([
    { text: `${ctx.tipo_servicio_fmt} — Plan ${ctx.plan} · suscripción anual`, options: { fontSize: 12, color: "CDD3F5", breakLine: true } },
    { text: ctx.cliente + (ctx.nit ? "  ·  NIT " + ctx.nit : ""), options: { fontSize: 9.5, color: "9AA3DA" } }
  ], { x: B.MX + 0.4, y: yTitulo, w: 5.9, h: 0.7, fontFace: B.F, lineSpacingMultiple: 1.15 });
  const yPrecio = ctx.atica ? 4.3 : 4.0;
  if (ctx.atica) s.addText(fmtMiles(pr.final) + " USD", { x: B.MX + 0.4, y: yPrecio, w: 3, h: 0.35, fontFace: B.F, fontSize: 18, color: "9AA3DA", strike: true });
  s.addText([{ text: fmtMiles(precioFinal) + " ", options: { fontSize: 44, bold: true, color: B.WHITE } }, { text: "USD", options: { fontSize: 18, bold: true, color: B.MINT } }],
    { x: B.MX + 0.4, y: ctx.atica ? 4.7 : 4.45, w: 5.9, h: 0.85, fontFace: B.F, valign: "middle" });
  s.addText([{ text: "Equivale a ", options: { color: "CDD3F5" } }, { text: pesosMes(precioMes), options: { color: B.WHITE, bold: true } }, { text: " por toda la gestión de carbono.", options: { color: "CDD3F5" } }],
    { x: B.MX + 0.4, y: ctx.atica ? 5.6 : 5.45, w: 5.9, h: 0.45, fontFace: B.F, fontSize: 12 });
  const sx = B.MX + 7.0, sw = 4.75;
  B.card(s, sx, 2.7, sw, 0.95, B.SOFT, B.LINE);
  s.addText([{ text: "Opciones de pago: ", options: { bold: true, color: B.P } }, { text: "50% al inicio, 50% al final. ¡Servicios exentos de IVA!", options: { color: B.INK2 } }],
    { x: sx + 0.2, y: 2.78, w: sw - 0.4, h: 0.8, fontFace: B.F, fontSize: 11.5, valign: "middle" });
  B.card(s, sx, 3.8, sw, 1.5, B.ASOFT, "CFE6DA");
  s.addText([{ text: "Plan de fidelización: ", options: { bold: true, color: B.ACD } }, { text: "tu precio anual no sube mientras tu suscripción siga activa (ver siguiente slide).", options: { color: B.INK2 } }],
    { x: sx + 0.2, y: 3.9, w: sw - 0.4, h: 1.3, fontFace: B.F, fontSize: 11.5, valign: "middle" });
  B.card(s, sx, 5.45, sw, 0.65, B.SOFT, B.LINE);
  s.addText("Precio por un (1) año de datos. No incluye pólizas ni viajes fuera de Bogotá. Pago en pesos: TRM del primer pago. Validez hasta el " + (ctx.fecha_limite_fmt || "") + ".",
    { x: sx + 0.2, y: 5.42, w: sw - 0.4, h: 0.7, fontFace: B.F, fontSize: 9, color: B.INK3, valign: "middle" });
  B.footer(s, ctx.cliente);
  return s;
}

/* ---------- SLIDE 12 — FIDELIZACIÓN ---------- */
function fidelizacion(p, slide, ctx) {
  const sf = p.addSlide(); sf.background = { color: B.DARK };
  if (B.exists("cover_bg.png")) { sf.addImage({ path: "cover_bg.png", x: 0, y: 0, w: B.W, h: B.H }); }
  else { sf.addShape(p.shapes.RECTANGLE, { x: 0, y: 0, w: B.W, h: B.H, fill: { color: B.DARK } }); if (B.exists(B.ICON_WHITE)) sf.addImage({ path: B.ICON_WHITE, x: 9.6, y: 3.6, w: 5.6, h: 5.6, transparency: 92 }); }
  sf.addText(String(ctx.idx).padStart(2, "0") + " / " + ctx.NT, { x: B.W - 2.1, y: 0.45, w: 1.4, h: 0.4, fontFace: B.FM, fontSize: 10, color: "6B74A8", align: "right", valign: "middle" });
  sf.addText("PLAN DE FIDELIZACIÓN", { x: B.MX, y: 0.95, w: 9, h: 0.35, fontFace: B.F, fontSize: 13, bold: true, color: B.MINT, charSpacing: 4 });
  sf.addText([{ text: "El precio de tu plan anual ", options: { color: B.WHITE } }, { text: "no sube", options: { color: B.MINT } }, { text: ".", options: { color: B.WHITE } }],
    { x: B.MX, y: 1.35, w: 11.5, h: 0.9, fontFace: B.F, fontSize: 40, bold: true });
  sf.addText("Mientras tu suscripción siga activa — te premiamos por tu aprendizaje.", { x: B.MX, y: 2.45, w: 11.5, h: 0.5, fontFace: B.F, fontSize: 16, color: "CDD3F5" });
  sf.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 4.9, y: 3.2, w: 2.6, h: 0.52, rectRadius: 0.26, fill: { color: B.MINT } });
  sf.addText("PRECIO CONGELADO", { x: 4.9, y: 3.2, w: 2.6, h: 0.52, fontFace: B.F, fontSize: 11, bold: true, color: B.ACD, align: "center", valign: "middle", charSpacing: 2 });
  const cy = 3.95, chh = 1.8, cwd = 3.3, cxs = [B.MX, B.MX + 3.85, B.MX + 7.7];
  const precioMostrar = fmtMiles(ctx.atica ? ctx.precios.atica : ctx.precios.final);
  ["AÑO 1", "AÑO 2", "AÑO 3"].forEach((yr, i) => {
    const x = cxs[i];
    sf.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: cy, w: cwd, h: chh, rectRadius: 0.1, fill: { color: "222E66" }, line: { color: "3D4894", width: 1 } });
    sf.addText(yr, { x, y: cy + 0.22, w: cwd, h: 0.3, fontFace: B.F, fontSize: 12, bold: true, color: "9FB0E8", align: "center", charSpacing: 2 });
    sf.addText(precioMostrar, { x, y: cy + 0.58, w: cwd, h: 0.7, fontFace: B.F, fontSize: 30, bold: true, color: B.WHITE, align: "center", valign: "middle" });
    sf.addText("USD / año", { x, y: cy + 1.33, w: cwd, h: 0.3, fontFace: B.F, fontSize: 12, color: "9FB0E8", align: "center" });
  });
  sf.addText("=", { x: cxs[0] + cwd, y: cy, w: 0.55, h: chh, fontFace: B.F, fontSize: 30, bold: true, color: B.MINT, align: "center", valign: "middle" });
  sf.addText("=", { x: cxs[1] + cwd, y: cy, w: 0.55, h: chh, fontFace: B.F, fontSize: 30, bold: true, color: B.MINT, align: "center", valign: "middle" });
  sf.addText("…y se mantiene", { x: cxs[2] + cwd + 0.05, y: cy, w: 1.25, h: chh, fontFace: B.F, fontSize: 11, italic: true, color: "9FB0E8", valign: "middle" });
  sf.addText([{ text: "A medida que autogestionas tu huella dependes menos del experto — ", options: { color: "CDD3F5" } }, { text: "tu aprendizaje es tu ahorro.", options: { color: B.MINT, bold: true } }],
    { x: B.MX, y: 6.2, w: 11.9, h: 0.5, fontFace: B.F, fontSize: 14 });
  sf.addText("FIDELIZACIÓN · CARBONBOX", { x: B.MX, y: B.H - 0.45, w: 6, h: 0.3, fontFace: B.F, fontSize: 9, color: "6B74A8", charSpacing: 2 });
  return sf;
}

/* ---------- SLIDE 13 — PRÓXIMOS PASOS ---------- */
const CRONOGRAMAS = {
  essential: [["Semana 1", "Acceso a la plataforma + onboarding de tu equipo."],
  ["Semanas 2–6", "Carga de datos en la plataforma (autogestión con soporte online)."],
  ["Mes 2", "Primeros resultados en el dashboard."],
  ["Mes 3", "Descarga del reporte técnico."]],
  pro: [["Semana 1", "Kickoff con tu equipo: contexto de cambio climático e identificación de fuentes de emisión."],
  ["Mes 1", "Recolección de datos con el experto dedicado. Primer resultado disponible en plataforma."],
  ["Mes 3", "Reporte técnico completo + recomendaciones de reducción."]],
  expert: [["Semana 1", "Kickoff con tu equipo: contexto de cambio climático e identificación de fuentes de emisión."],
  ["Mes 1", "Recolección de datos con el experto dedicado. Primer resultado disponible en plataforma."],
  ["Mes 3", "Reporte técnico completo + análisis de acciones de reducción."],
  ["Mes 4–6", "Proceso de certificación de carbono neutralidad."]],
};
function proximosPasos(p, slide, ctx) {
  const s = p.addSlide();
  B.header(s, String(ctx.idx).padStart(2, "0"), "¿Empezamos?", "Cierre", ctx.NT);
  s.addText("Si decides avanzar, así sería el arranque de la medición de tu huella de carbono:",
    { x: B.MX, y: 2.5, w: 11.5, h: 0.5, fontFace: B.F, fontSize: 15, color: B.INK2 });
  let tl = CRONOGRAMAS[planKey(ctx.plan)] || CRONOGRAMAS.pro;
  if (ctx.tipo_servicio === "certificacion" && planKey(ctx.plan) !== "expert") tl = CRONOGRAMAS.expert;
  tl.forEach((t, i) => {
    const y = 3.15 + i * 0.72;
    s.addText(t[0], { x: B.MX, y, w: 1.7, h: 0.5, fontFace: B.FM, fontSize: 13, bold: true, color: B.ACD, valign: "top" });
    s.addText(t[1], { x: B.MX + 1.9, y, w: 9.7, h: 0.6, fontFace: B.F, fontSize: 13.5, color: B.INK2 });
    if (i < tl.length - 1) s.addShape(p.shapes.LINE, { x: B.MX, y: y + 0.62, w: B.W - 2 * B.MX, h: 0, line: { color: B.LINE, width: 1 } });
  });
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: B.MX, y: 5.9, w: B.W - 2 * B.MX, h: 1.05, rectRadius: 0.1, fill: { color: B.P } });
  s.addText("Agenda una reunión", { x: B.MX + 0.4, y: 5.9, w: 6, h: 1.05, fontFace: B.F, fontSize: 20, bold: true, color: B.WHITE, valign: "middle" });
  s.addText([{ text: "info@carbonbox.app  ·  ", options: { color: "CDD3F5" } }, { text: "www.carbonbox.app/#contacto", options: { color: B.MINT, hyperlink: { url: "https://www.carbonbox.app/#contacto" } } }],
    { x: B.W - B.MX - 6.2, y: 5.9, w: 5.8, h: 1.05, fontFace: B.FM, fontSize: 12, align: "right", valign: "middle" });
  return s;
}

/* ---------- FASE 2 (opcional) ---------- */
function fase2Servicios(p, slide, ctx) {
  const s = p.addSlide();
  B.header(s, String(ctx.idx).padStart(2, "0"), "Fase 2 — Servicios estratégicos", "Opcional · A cotizar aparte", ctx.NT);
  s.addText("Para materializar, comunicar y monetizar tu sostenibilidad —más allá de medir— proponemos una fase de consultoría a cotizar según el alcance que definas:",
    { x: B.MX, y: 2.5, w: 11.6, h: 0.7, fontFace: B.F, fontSize: 13.5, color: B.INK2, lineSpacingMultiple: 1.2 });
  const items = slide.items || [
    ["ic_arrowup.png", "Hoja de ruta climática", "Metas de reducción y ruta a carbono neutralidad."],
    ["ic_chart.png", "Indicadores y reportes gerenciales", "Tableros e informes periódicos para dirección."],
    ["ic_users.png", "Estrategia de comunicación", "Tus resultados contados para clientes y aliados."],
    ["ic_leaf.png", "Programa de eventos sostenibles", "Eventos con huella medida para grupos empresariales."],
    ["ic_award.png", "Materiales para el área comercial", "La sostenibilidad como argumento de venta."],
    ["ic_offset.png", "Estrategia de compensación", "Portafolios de compensación y carbono neutralidad."]];
  items.forEach((c, i) => {
    const x = B.MX + (i % 2) * 6.0, y = 3.35 + Math.floor(i / 2) * 1.12; B.card(s, x, y, 5.75, 1.0, B.SOFT, B.LINE);
    B.icon(s, x + 0.2, y + 0.25, 0.5, c[0], "FFFFFF");
    s.addText(c[1], { x: x + 0.9, y: y + 0.12, w: 4.7, h: 0.32, fontFace: B.F, fontSize: 12.5, bold: true, color: B.P });
    s.addText(c[2], { x: x + 0.9, y: y + 0.44, w: 4.75, h: 0.52, fontFace: B.F, fontSize: 9.8, color: B.INK2, lineSpacingMultiple: 1.05 });
  });
  B.footer(s, ctx.cliente);
  return s;
}
function fase2Valor(p, slide, ctx) {
  const s = p.addSlide();
  B.header(s, String(ctx.idx).padStart(2, "0"), "Inversión — Fase 2 estratégica", "Servicios adicionales · complementario", ctx.NT);
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: B.MX, y: 2.7, w: 6.7, h: 3.4, rectRadius: 0.12, fill: { color: B.ACC }, shadow: B.shadow() });
  s.addText("PAQUETE COMPLEMENTARIO AL SOFTWARE", { x: B.MX + 0.4, y: 3.05, w: 5.9, h: 0.4, fontFace: B.F, fontSize: 11, bold: true, color: B.MINT, charSpacing: 2 });
  s.addText(slide.descripcion || "Servicios estratégicos de consultoría, complementarios a la plataforma.", { x: B.MX + 0.4, y: 3.5, w: 5.9, h: 0.7, fontFace: B.F, fontSize: 12, color: "E8F1EC", lineSpacingMultiple: 1.15 });
  const valor = slide.valor || "[Valor a definir]";
  s.addText(valor, { x: B.MX + 0.4, y: 4.4, w: 5.9, h: 0.9, fontFace: B.F, fontSize: 40, bold: true, color: B.WHITE, valign: "middle" });
  B.card(s, B.MX + 7.0, 2.7, 4.75, 3.4, B.SOFT, B.LINE);
  s.addText("Se cotiza según el alcance que definas. Cuéntanos cuáles de estos servicios te interesan y armamos una propuesta a tu medida.",
    { x: B.MX + 7.2, y: 3.0, w: 4.35, h: 2.8, fontFace: B.F, fontSize: 12.5, color: B.INK2, lineSpacingMultiple: 1.25 });
  B.footer(s, ctx.cliente);
  return s;
}

const LAYOUTS = {
  portada, "contexto-necesidad": contextoNecesidad, "que-es-carbonbox": queEsCarbonbox,
  ventajas, soluciones, "caso-exito": casoExito, logos, "trabajo-hoy": trabajoHoy,
  equipo, plan, inversion, fidelizacion, "proximos-pasos": proximosPasos,
  "fase2-servicios": fase2Servicios, "fase2-valor": fase2Valor,
};
module.exports = { LAYOUTS };
