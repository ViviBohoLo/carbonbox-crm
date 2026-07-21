// lib/base.js — setup de pptxgen + tokens + helpers compartidos.
// Portado de generador-pptx-pepsico.js (líneas 1–90), parametrizando `cliente`
// y sin fijar datos del caso. NO rediseñar: mismos tokens/posiciones.
const pptxgen = require("pptxgenjs");
const path = require("path");
const fs = require("fs");
const ROOT = path.join(__dirname, "..", "..");

const P = "1620A4", PD = "0D1578", DARK = "0D1230", ACC = "2F6B4A", ACD = "1E4A32",
  INK = "0F1535", INK2 = "4A526E", INK3 = "7A82A0", SOFT = "F7F8FC", LINE = "E6E8F2",
  PSOFT = "ECEDFB", P100 = "D8DBF4", ASOFT = "E8F1EC", MINT = "7ED3A8", WHITE = "FFFFFF";
const F = "Poppins", FM = "JetBrains Mono", W = 13.333, H = 7.5, MX = 0.7;

const LOGO_BLUE = ROOT + "/Logos/Logo horizontal azul .png.png";
const LOGO_WHITE = ROOT + "/Logos/Logo horizontal blanco.png.png";
const ICON_WHITE = ROOT + "/Logos/icon_blanco.png";

let P_REF = null; // referencia al pptx activo (para p.shapes en helpers)

function crearPptx() {
  const p = new pptxgen();
  p.defineLayout({ name: "W", width: W, height: H });
  p.layout = "W";
  p.author = "CarbonBox";
  process.chdir(path.join(ROOT, "Recursos")); // assets relativos (imágenes en /Recursos)
  P_REF = p;
  return p;
}

const exists = pth => { try { return fs.existsSync(pth); } catch (e) { return false; } };

function shadow() { return { type: "outer", color: "0F1535", blur: 9, offset: 3, angle: 135, opacity: 0.10 }; }

function wordmark(s, x, y, color) {
  const white = (color === WHITE);
  const pth = white ? LOGO_WHITE : LOGO_BLUE;
  const ratio = white ? (490 / 136) : (1069 / 324);
  const h = white ? 0.62 : 0.42;
  s.addImage({ path: pth, x, y, w: h * ratio, h });
}

function header(s, num, title, eyebrow, NT) {
  const p = P_REF;
  wordmark(s, MX, 0.40, P);
  s.addText(`${num} / ${NT}`, { x: W - 2.1, y: 0.42, w: 1.4, h: 0.4, fontFace: FM, fontSize: 10, color: INK3, align: "right", valign: "middle" });
  if (eyebrow) s.addText(eyebrow.toUpperCase(), { x: MX, y: 1.25, w: 11, h: 0.3, fontFace: F, fontSize: 10.5, bold: true, color: ACC, charSpacing: 3 });
  s.addText(title, { x: MX, y: 1.55, w: 12, h: 0.8, fontFace: F, fontSize: 27, bold: true, color: P });
}

function footer(s, cliente) {
  const p = P_REF;
  s.addShape(p.shapes.LINE, { x: MX, y: H - 0.55, w: W - 2 * MX, h: 0, line: { color: LINE, width: 1 } });
  s.addText("CarbonBox · Cotización", { x: MX, y: H - 0.5, w: 5, h: 0.3, fontFace: F, fontSize: 9, color: INK3 });
  s.addText([{ text: "● ", options: { color: ACC } }, { text: cliente || "", options: { color: INK3 } }],
    { x: W - 5.7, y: H - 0.5, w: 5, h: 0.3, fontFace: F, fontSize: 9, align: "right" });
}

function card(s, x, y, w, h, fill, line) {
  const p = P_REF;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: line, width: 1 } });
}

function icon(s, x, y, d, pth, fill) {
  const p = P_REF;
  s.addShape(p.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill || ASOFT }, line: { color: "CFE6DA", width: 1 } });
  const pad = d * 0.27;
  s.addImage({ path: pth, x: x + pad, y: y + pad, w: d - 2 * pad, h: d - 2 * pad });
}

function flag(s, cx, cy, w, h, name) {
  const p = P_REF;
  if (name === "México" || name === "Perú") {
    const cols = name === "México" ? ["006847", "FFFFFF", "CE1126"] : ["D91023", "FFFFFF", "D91023"];
    cols.forEach((c, i) => s.addShape(p.shapes.RECTANGLE, { x: cx + i * w / 3, y: cy, w: w / 3, h, fill: { color: c } }));
  } else {
    const seg = {
      "Colombia": [["FCD116", 0.5], ["003893", 0.25], ["CE1126", 0.25]],
      "Ecuador": [["FCD116", 0.5], ["0038A8", 0.25], ["CE1126", 0.25]],
      "Paraguay": [["D52B1E", 0.3333], ["FFFFFF", 0.3334], ["0038A8", 0.3333]],
      "Argentina": [["74ACDF", 0.3333], ["FFFFFF", 0.3334], ["74ACDF", 0.3333]]
    }[name];
    let yy = cy; seg.forEach(b => { s.addShape(p.shapes.RECTANGLE, { x: cx, y: yy, w, h: h * b[1], fill: { color: b[0] } }); yy += h * b[1]; });
  }
  s.addShape(p.shapes.RECTANGLE, { x: cx, y: cy, w, h, fill: { color: "FFFFFF", transparency: 100 }, line: { color: "C9CEE0", width: 1 } });
  s.addText(name, { x: cx - 0.35, y: cy + h + 0.06, w: w + 0.7, h: 0.3, fontFace: F, fontSize: 11, color: INK2, align: "center" });
}

function imgSize(pth) {
  try {
    const b = fs.readFileSync(pth);
    if (b.length > 24 && b[0] === 0x89 && b[1] === 0x50) { return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; } // PNG
    if (b[0] === 0xFF && b[1] === 0xD8) { // JPEG
      let o = 2;
      while (o < b.length) {
        if (b[o] !== 0xFF) { o++; continue; }
        const m = b[o + 1];
        if (m >= 0xC0 && m <= 0xCF && m !== 0xC4 && m !== 0xC8 && m !== 0xCC) { return { h: b.readUInt16BE(o + 5), w: b.readUInt16BE(o + 7) }; }
        o += 2 + b.readUInt16BE(o + 2);
      }
    }
  } catch (e) { }
  return null;
}

function fitImage(s, pth, boxX, boxY, boxW, boxH) {
  const sz = imgSize(pth);
  if (!sz) { s.addImage({ path: pth, x: boxX, y: boxY, w: boxW, h: boxH, sizing: { type: "contain", w: boxW, h: boxH } }); return; }
  const r = sz.w / sz.h; let w = boxW, h = boxW / r;
  if (h > boxH) { h = boxH; w = boxH * r; }
  s.addImage({ path: pth, x: boxX + (boxW - w) / 2, y: boxY + (boxH - h) / 2, w, h });
}

module.exports = {
  crearPptx, exists, shadow, wordmark, header, footer, card, icon, flag, imgSize, fitImage,
  P, PD, DARK, ACC, ACD, INK, INK2, INK3, SOFT, LINE, PSOFT, P100, ASOFT, MINT, WHITE,
  F, FM, W, H, MX, LOGO_BLUE, LOGO_WHITE, ICON_WHITE,
};
