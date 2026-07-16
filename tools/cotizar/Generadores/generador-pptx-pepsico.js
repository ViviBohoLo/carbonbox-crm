const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.defineLayout({ name:"W", width:13.333, height:7.5 });
p.layout = "W";
p.author="CarbonBox"; p.title="Cotización CarbonBox — PepsiCo Alimentos Colombia";

// Tokens alineados al Sistema de diseño CarbonBox (jun 2026)
const P="1620A4",PD="0D1578",DARK="0D1230",ACC="2F6B4A",ACD="1E4A32",INK="0F1535",INK2="4A526E",INK3="7A82A0",
  SOFT="F7F8FC",LINE="E6E8F2",PSOFT="ECEDFB",P100="D8DBF4",ASOFT="E8F1EC",MINT="7ED3A8",WHITE="FFFFFF";
const F="Poppins";
const FM="JetBrains Mono";
const path=require("path");
const ROOT=path.join(__dirname,"..");
process.chdir(path.join(ROOT,"Recursos")); // imágenes/assets en /Recursos
const BASE=ROOT;                            // Logos en /Logos
const LOGO_BLUE=BASE+"/Logos/Logo horizontal azul .png.png";
const LOGO_WHITE=BASE+"/Logos/Logo horizontal blanco.png.png";
const VLOGO_WHITE=BASE+"/Logos/Artboard 1 copy 11.png";
const ICON_WHITE=BASE+"/Logos/icon_blanco.png";
const W=13.333, H=7.5, MX=0.7;
const CLIENTE="PepsiCo Alimentos Colombia";
const NIT_CLIENTE="900.123.456-7"; // ⚠️ obligatorio desde jul-2026 — lo usa el CRM para seguimiento de envíos
const fs=require("fs");
const exists = pth => { try { return fs.existsSync(pth); } catch(e){ return false; } };

// ── Datos del caso ──────────────────────────────────────────────────────────
// Sector Industria manufacturera (alimentos), 2 plantas: Guarne 550 + Funza 750 = 1.300 colab.
// Plan Pro · alianza ATICA = sí → base $4.557 → $4.101 (−10%) · $342/mes.
const PRECIO_BASE_FMT  = "$ 4.557";
const PRECIO_ANUAL_FMT = "$ 4.101";   // precio anual final (con descuento ATICA)
const PRECIO_MES_FMT   = "$342 USD/mes";
const FECHA_HOY        = "2 de julio de 2026";
const FECHA_LIMITE     = "31 de agosto de 2026";

// Sin servicios adicionales (el correo solo pide la cotización de la plataforma).
const INCLUIR_FASE2        = false;
const INCLUIR_FASE2_PRECIO = false;
const NT = 13 + (INCLUIR_FASE2?1:0) + (INCLUIR_FASE2_PRECIO?1:0);

function shadow(){return {type:"outer",color:"0F1535",blur:9,offset:3,angle:135,opacity:0.10};}
function wordmark(s,x,y,color,size){
  var white = (color===WHITE);
  var path = white?LOGO_WHITE:LOGO_BLUE;
  var ratio = white?(490/136):(1069/324);
  var h = white?0.62:0.42;
  s.addImage({path:path, x:x, y:y, w:h*ratio, h:h});
}
function header(s,num,title,eyebrow){
  wordmark(s,MX,0.40,P,17);
  s.addText(`${num} / ${NT}`,{x:W-2.1,y:0.42,w:1.4,h:0.4,fontFace:FM,fontSize:10,color:INK3,align:"right",valign:"middle"});
  if(eyebrow) s.addText(eyebrow.toUpperCase(),{x:MX,y:1.25,w:11,h:0.3,fontFace:F,fontSize:10.5,bold:true,color:ACC,charSpacing:3});
  s.addText(title,{x:MX,y:1.55,w:12,h:0.8,fontFace:F,fontSize:27,bold:true,color:P});
}
function footer(s){
  s.addShape(p.shapes.LINE,{x:MX,y:H-0.55,w:W-2*MX,h:0,line:{color:LINE,width:1}});
  s.addText("CarbonBox · Cotización",{x:MX,y:H-0.5,w:5,h:0.3,fontFace:F,fontSize:9,color:INK3});
  s.addText([{text:"● ",options:{color:ACC}},{text:CLIENTE,options:{color:INK3}}],
    {x:W-5.7,y:H-0.5,w:5,h:0.3,fontFace:F,fontSize:9,align:"right"});
}
function card(s,x,y,w,h,fill,line){
  s.addShape(p.shapes.ROUNDED_RECTANGLE,{x,y,w,h,rectRadius:0.08,fill:{color:fill},line:{color:line,width:1}});
}
function icon(s,x,y,d,path,fill){ s.addShape(p.shapes.OVAL,{x,y,w:d,h:d,fill:{color:fill||ASOFT},line:{color:"CFE6DA",width:1}}); var pad=d*0.27; s.addImage({path:path,x:x+pad,y:y+pad,w:d-2*pad,h:d-2*pad}); }
function flag(s,cx,cy,w,h,name){
  if(name==="México"||name==="Perú"){ var cols=name==="México"?["006847","FFFFFF","CE1126"]:["D91023","FFFFFF","D91023"];
    cols.forEach((c,i)=>s.addShape(p.shapes.RECTANGLE,{x:cx+i*w/3,y:cy,w:w/3,h:h,fill:{color:c}})); }
  else { var seg={"Colombia":[["FCD116",0.5],["003893",0.25],["CE1126",0.25]],
    "Ecuador":[["FCD116",0.5],["0038A8",0.25],["CE1126",0.25]],
    "Paraguay":[["D52B1E",0.3333],["FFFFFF",0.3334],["0038A8",0.3333]],
    "Argentina":[["74ACDF",0.3333],["FFFFFF",0.3334],["74ACDF",0.3333]]}[name];
    var yy=cy; seg.forEach(b=>{s.addShape(p.shapes.RECTANGLE,{x:cx,y:yy,w:w,h:h*b[1],fill:{color:b[0]}}); yy+=h*b[1];}); }
  s.addShape(p.shapes.RECTANGLE,{x:cx,y:cy,w:w,h:h,fill:{color:"FFFFFF",transparency:100},line:{color:"C9CEE0",width:1}});
  s.addText(name,{x:cx-0.35,y:cy+h+0.06,w:w+0.7,h:0.3,fontFace:F,fontSize:11,color:INK2,align:"center"});
}
function imgSize(path){
  try{ const b=fs.readFileSync(path);
    if(b.length>24 && b[0]===0x89 && b[1]===0x50){ return {w:b.readUInt32BE(16), h:b.readUInt32BE(20)}; } // PNG
    if(b[0]===0xFF && b[1]===0xD8){ let o=2; // JPEG
      while(o<b.length){ if(b[o]!==0xFF){o++;continue;} const m=b[o+1];
        if(m>=0xC0 && m<=0xCF && m!==0xC4 && m!==0xC8 && m!==0xCC){ return {h:b.readUInt16BE(o+5), w:b.readUInt16BE(o+7)}; }
        o += 2 + b.readUInt16BE(o+2); } }
  }catch(e){}
  return null;
}
function fitImage(s,path,boxX,boxY,boxW,boxH){
  const sz=imgSize(path);
  if(!sz){ s.addImage({path:path,x:boxX,y:boxY,w:boxW,h:boxH,sizing:{type:"contain",w:boxW,h:boxH}}); return; }
  const r=sz.w/sz.h; let w=boxW, h=boxW/r;
  if(h>boxH){ h=boxH; w=boxH*r; }
  s.addImage({path:path,x:boxX+(boxW-w)/2,y:boxY+(boxH-h)/2,w:w,h:h});
}

/* ---------- SLIDE 1 — COVER ---------- */
let s=p.addSlide(); s.background={color:DARK};
const hasCoverBg = exists("cover_bg.png");
if(hasCoverBg){
  s.addImage({path:"cover_bg.png", x:0, y:0, w:W, h:H});
} else {
  s.addShape(p.shapes.RECTANGLE,{x:0,y:0,w:W,h:H,fill:{color:DARK}});
  s.addImage({path:ICON_WHITE, x:8.7, y:-1.6, w:6.6, h:6.6, transparency:88});
  s.addImage({path:ICON_WHITE, x:9.7, y:4.4, w:5.0, h:5.0, transparency:91});
}
wordmark(s,MX,0.5,WHITE,22);
s.addText("COTIZACIÓN COMERCIAL",{x:MX,y:2.0,w:9,h:0.35,fontFace:F,fontSize:12,bold:true,color:MINT,charSpacing:3});
s.addText("Estimación de huella de carbono organizacional",{x:MX,y:2.4,w:8.2,h:1.8,fontFace:F,fontSize:40,bold:true,color:WHITE,lineSpacingMultiple:1.02});
s.addText([{text:"Preparada para ",options:{color:"CDD3F5"}},{text:CLIENTE,options:{color:WHITE,bold:true}}],
  {x:MX,y:4.45,w:9,h:0.5,fontFace:F,fontSize:18});
s.addText("NIT "+NIT_CLIENTE,{x:MX,y:4.85,w:9,h:0.3,fontFace:FM,fontSize:11,color:"AAB2E8"});
s.addShape(p.shapes.ROUNDED_RECTANGLE,{x:MX,y:5.25,w:1.6,h:0.5,rectRadius:0.25,fill:{color:"2F6B4A"}});
s.addText("PLAN PRO",{x:MX,y:5.25,w:1.6,h:0.5,fontFace:F,fontSize:12,bold:true,color:WHITE,charSpacing:1,align:"center",valign:"middle"});
s.addText("Acompañamiento con experto dedicado, seguimiento continuo y reporte técnico alineado a estándares internacionales (GHG Protocol / ISO 14064-1). Incluye las dos plantas en Colombia.",
  {x:MX,y:5.88,w:8.4,h:0.65,fontFace:F,fontSize:13,color:"CDD3F5",lineSpacingMultiple:1.2});
s.addText([{text:FECHA_HOY+"     ·     Validez 60 días     ·     ",options:{color:"AAB2E8"}},
  {text:"www.carbonbox.app",options:{color:MINT,hyperlink:{url:"https://www.carbonbox.app"}}}],
  {x:MX,y:6.75,w:12,h:0.4,fontFace:FM,fontSize:11});

/* ---------- SLIDE 2 — CLIENTE: CONTEXTO + NECESIDAD (fusionado) ---------- */
s=p.addSlide(); header(s,"02","El cliente: contexto y necesidad","El cliente primero");
s.addShape(p.shapes.LINE,{x:6.67,y:2.7,w:0,h:3.4,line:{color:LINE,width:1}});
// izquierda — LO QUE SABEMOS
s.addText("LO QUE SABEMOS",{x:MX,y:2.65,w:5.4,h:0.35,fontFace:F,fontSize:12,bold:true,color:ACC,charSpacing:2});
s.addText("PepsiCo Alimentos Colombia",{x:MX,y:3.05,w:5.4,h:0.4,fontFace:F,fontSize:17,bold:true,color:P});
s.addText("Multinacional de alimentos con dos plantas de producción en Colombia: Planta Guarne (Antioquia, elaboración de alimentos, ~550 colaboradores) y Planta Funza (Cundinamarca, productos de panadería, ~750 colaboradores). El sector de alimentos enfrenta creciente presión de reportar sus emisiones ante casa matriz, clientes y regulación.",
  {x:MX,y:3.5,w:5.35,h:2.5,fontFace:F,fontSize:13.5,color:INK2,lineSpacingMultiple:1.25});
// derecha — LO QUE NECESITA
s.addText("LO QUE NECESITA",{x:7.0,y:2.65,w:5.4,h:0.35,fontFace:F,fontSize:12,bold:true,color:ACC,charSpacing:2});
s.addText("Medir la huella de sus dos plantas",{x:7.0,y:3.05,w:5.4,h:0.4,fontFace:F,fontSize:17,bold:true,color:P});
s.addText("Estimar la huella de carbono organizacional (alcances 1, 2 y 3) de sus operaciones en Colombia sobre una plataforma confiable, con un experto dedicado que guíe la recolección de datos y entregue un reporte técnico defendible ante casa matriz, clientes y aliados. Llega referida por la alianza ATICA–CarbonBox.",
  {x:7.0,y:3.5,w:5.4,h:2.5,fontFace:F,fontSize:13.5,color:INK2,lineSpacingMultiple:1.25}); footer(s);

/* ---------- SLIDE 3 — QUÉ ES CARBONBOX ---------- */
s=p.addSlide(); header(s,"03","Qué es CarbonBox","Nuestra solución");
s.addText("Una plataforma que mide, reduce y compensa la huella de carbono de tu empresa — con tecnología y un experto dedicado.",
  {x:MX,y:2.4,w:5.8,h:0.9,fontFace:F,fontSize:16,color:INK2,lineSpacingMultiple:1.25});
const f4=[["Medición de CO₂","Alcances 1, 2 y 3 con datos confiables.","ic_measure.png"],
["Reducción de CO₂","Acciones priorizadas con costo-beneficio.","ic_reduce.png"],
["Compensación de CO₂","Metas de neutralidad y descarbonización.","ic_offset.png"]];
f4.forEach((c,i)=>{let y=3.45+i*0.8; icon(s,MX,y,0.6,c[2],"FFFFFF");
  s.addText(c[0],{x:MX+0.8,y:y-0.02,w:5.0,h:0.32,fontFace:F,fontSize:14,bold:true,color:P});
  s.addText(c[1],{x:MX+0.8,y:y+0.3,w:5.0,h:0.32,fontFace:F,fontSize:11.5,color:INK2});});
s.addText("30% menos tiempo de gestión  ·  40% más productividad",{x:MX,y:5.95,w:5.8,h:0.35,fontFace:F,fontSize:13,bold:true,color:ACD});
s.addImage({path:"s4_hero.png",x:7.05,y:1.7,w:5.2,h:4.45});
s.addText("Alineado a estándares internacionales:",{x:7.05,y:6.32,w:3.3,h:0.3,fontFace:F,fontSize:10.5,color:INK3,valign:"middle"});
s.addImage({path:"std_ghg.png",x:10.4,y:6.28,w:1.15,h:0.48});
s.addImage({path:"std_iso.png",x:11.65,y:6.25,w:0.5,h:0.5});
footer(s);

/* ---------- SLIDE 4 — VENTAJAS ---------- */
s=p.addSlide(); header(s,"04","Ventajas de trabajar con nosotros","Nuestra solución");
s.addImage({path:"s5_stars.png",x:MX,y:2.85,w:4.7,h:3.21});
s.addText("Un experto dedicado acompaña tu proceso en todos los planes.",{x:MX,y:6.05,w:4.7,h:0.5,fontFace:F,fontSize:12,italic:true,color:INK3});
const adv5=[["Capacidades en medición, reducción y compensación para ti y tu equipo.","ic_cap.png"],
["Decisiones estratégicas con dashboards claros y accionables.","ic_chart.png"],
["Una herramienta atractiva para presentar ante tu casa matriz, clientes y aliados comerciales.","ic_users.png"],
["Te destacas integrando soluciones innovadoras y tecnológicas.","ic_award.png"]];
adv5.forEach((t,i)=>{let y=2.6+i*0.85; icon(s,5.95,y,0.6,t[1],"FFFFFF");
  s.addText(t[0],{x:6.7,y:y-0.05,w:5.9,h:0.72,fontFace:F,fontSize:13.5,color:INK2,valign:"middle"});});
card(s,5.95,6.05,6.65,0.92,ASOFT,"CFE6DA");
icon(s,6.15,6.27,0.5,"ic_piggy.png","FFFFFF");
s.addText("Año a año serás más autónomo y obtendrás ahorros gestionando tu huella y tu operación.",
  {x:6.8,y:6.12,w:5.65,h:0.78,fontFace:F,fontSize:12,color:INK2,valign:"middle"}); footer(s);

/* ---------- SLIDE 5 — SOLUCIONES ---------- */
s=p.addSlide(); header(s,"05","Nuestras soluciones tecnológicas","Nuestra solución");
s.addText("Accede por un año a los módulos que necesitas para gestionar la huella de carbono de tu empresa.",
  {x:MX,y:2.4,w:11.5,h:0.5,fontFace:F,fontSize:15,color:INK2});
const mods=[["s6_ill1.png","Estimación de huella","Mide tus emisiones por actividad — alcances 1, 2 y 3."],
["s6_ill2.png","Reducciones","Simula escenarios y traza tu ruta de reducción."],
["s6_ill3.png","Compensaciones","Compensa lo restante y alcanza la carbono neutralidad."]];
mods.forEach((c,i)=>{let x=MX+i*4.0;
  s.addImage({path:c[0],x:x,y:3.0,w:3.78,h:2.58});
  s.addText(c[1],{x:x+0.05,y:5.68,w:3.7,h:0.4,fontFace:F,fontSize:16,bold:true,color:P});
  s.addText(c[2],{x:x+0.05,y:6.08,w:3.75,h:0.8,fontFace:F,fontSize:11.5,color:INK2,lineSpacingMultiple:1.15});}); footer(s);

/* ---------- SLIDE 6 — CASO DE ÉXITO (MANUFACTURA / MULTIPLANTA) ---------- */
s=p.addSlide(); header(s,"06","Un cliente como tú","Confianza y credenciales");
s.addText("Una empresa líder de manufactura industrial en Colombia medía su huella en Excel con apoyo externo: 4 meses de trabajo, propenso a errores y difícil de defender ante su junta directiva. Con CarbonBox implementaron la medición de alcances 1, 2 y 3 para sus tres plantas en una sola plataforma. Redujeron el proceso a 6 semanas y descubrieron que el 38% de sus emisiones venía de una sola fuente de combustión.",
  {x:MX,y:2.7,w:11.6,h:1.5,fontFace:F,fontSize:15.5,color:INK2,lineSpacingMultiple:1.3});
card(s,MX,4.6,11.75,1.2,PSOFT,P100);
s.addShape(p.shapes.RECTANGLE,{x:MX,y:4.6,w:0.07,h:1.2,fill:{color:ACC}});
s.addText("“Por primera vez tenemos un número en el que podemos confiar para presentarle a nuestra junta directiva.”",
  {x:MX+0.35,y:4.6,w:11.1,h:1.2,fontFace:F,fontSize:16,italic:true,bold:true,color:P,valign:"middle"});
s.addText("Llevan 3 años renovando su suscripción anual con CarbonBox. (Caso afín a tu operación multiplanta de alimentos.)",{x:MX,y:5.95,w:11.5,h:0.3,fontFace:F,fontSize:12,color:INK3}); footer(s);

/* ---------- SLIDE 7 — LOGOS ---------- */
s=p.addSlide(); header(s,"07","Empresas que han confiado en nosotros","Confianza y credenciales");
if(exists("s7_logos.png")){
  fitImage(s,"s7_logos.png",MX,2.55,W-2*MX,4.0);
} else {
  const logos=["Siemens","Biomax","Fenavi","Asobancaria","Crepes & Waffles","Estéreo Picnic","Ara","Colgas","Zona Franca Bogotá","Agrosavia","Fundación Santa Fe","EBSA","Elementia","Eternit","Páramo Presenta","Alcaldía de Bogotá","Idartes","Cámara Verde","Colegio Anglo","DNP","Jerónimo Martins","FLP","Atica","Fondo Acción"];
  const cols=6, cw=1.92, chh=0.62, gx=0.05, gy=0.18, x0=MX, y0=2.7;
  logos.forEach((t,i)=>{let c=i%cols,r=Math.floor(i/cols);let x=x0+c*(cw+gx),y=y0+r*(chh+gy);
    card(s,x,y,cw,chh,SOFT,LINE);
    s.addText(t,{x:x+0.05,y,w:cw-0.1,h:chh,fontFace:F,fontSize:10.5,color:INK2,align:"center",valign:"middle"});});
}
footer(s);

/* ---------- SLIDE 8 — NUESTRO TRABAJO HOY ---------- */
s=p.addSlide(); header(s,"08","Nuestro trabajo hoy","Confianza y credenciales");
s.addImage({path:"s9_map.png",x:MX,y:2.35,w:3.7,h:4.35});
s.addText("Hemos acompañado a 10 sectores de la economía en 6 países de Latinoamérica.",
  {x:4.85,y:2.5,w:7.7,h:0.6,fontFace:F,fontSize:15,color:INK2,lineSpacingMultiple:1.2});
const countries=["Colombia","Ecuador","Paraguay","México","Argentina","Perú"];
countries.forEach((n,i)=>{let cx=4.9+i*1.3; flag(s,cx,3.4,0.9,0.58,n);});
[[">150.000","tCO₂e estimadas"],["~36.456","tCO₂ reducidas por nuestros clientes"],["6","países de LATAM"],["10","sectores de la economía"]].forEach((c,i)=>{let x=4.9+(i%2)*3.95,y=4.55+Math.floor(i/2)*1.08;card(s,x,y,3.75,0.96,ASOFT,"CFE6DA");
  s.addText(c[0],{x:x+0.2,y:y+0.07,w:3.4,h:0.42,fontFace:F,fontSize:21,bold:true,color:ACD,valign:"middle"});
  s.addText(c[1],{x:x+0.2,y:y+0.5,w:3.45,h:0.4,fontFace:F,fontSize:10.5,color:INK2,valign:"middle",lineSpacingMultiple:0.95});}); footer(s);

/* ---------- SLIDE 9 — EQUIPO ---------- */
s=p.addSlide(); header(s,"09","El equipo experto","Confianza y credenciales");
const team=[["t_vivi_sq.png","Viviana Bohórquez","CEO y Co-fundadora","15 años en estimación y reporte de reducciones de GEI. Certificada ISO 14064-1 y 2."],
["t_ale_sq.png","Alejandra Rojas","Líder de proyectos","5 años en inventarios de GEI. Auditora interna de huellas de carbono y gestión de reducción y compensación."],
["t_manu_sq.png","Manuel Rivera","Líder en tecnología","Full Stack, 5 años en apps web y móviles; backend y bases de datos."],
["t_lau_sq.png","Laura Bautista","Profesional en sostenibilidad","3 años en reportes y gestión de la sostenibilidad y medición de impacto."],
["t_migue_sq.png","Miguel Romero","Profesional en sostenibilidad","+4 años como ing. ambiental con énfasis en energías renovables y sostenibilidad; experiencia en el sector de alimentos y saneamiento ambiental."],
["t_eli_sq.png","Eliezer Mas y Rubí","Experto en tecnología","+4 años en desarrollo web y UI/UX; líder de equipos internacionales."]];
function initials(name){return name.split(/\s+/).slice(0,2).map(w=>w[0]).join("").toUpperCase();}
team.forEach((m,i)=>{let x=MX+(i%2)*6.0,y=2.5+Math.floor(i/2)*1.45;card(s,x,y,5.75,1.3,SOFT,LINE);
  if(exists(m[0])){
    s.addImage({path:m[0],x:x+0.24,y:y+0.27,w:0.78,h:0.78,rounding:true,sizing:{type:"cover",w:0.78,h:0.78}});
  } else {
    s.addShape(p.shapes.OVAL,{x:x+0.24,y:y+0.27,w:0.78,h:0.78,fill:{color:PSOFT},line:{color:P100,width:1}});
    s.addText(initials(m[1]),{x:x+0.24,y:y+0.27,w:0.78,h:0.78,fontFace:F,fontSize:16,bold:true,color:P,align:"center",valign:"middle"});
  }
  s.addText(m[1],{x:x+1.18,y:y+0.16,w:4.5,h:0.32,fontFace:F,fontSize:12.5,bold:true,color:P});
  s.addText(m[2],{x:x+1.18,y:y+0.47,w:4.5,h:0.28,fontFace:F,fontSize:10,bold:true,color:ACC});
  s.addText(m[3],{x:x+1.18,y:y+0.73,w:4.55,h:0.5,fontFace:F,fontSize:9.5,color:INK2,lineSpacingMultiple:1.08});}); footer(s);

/* ---------- SLIDE 10 — PLAN PRO ---------- */
s=p.addSlide(); header(s,"10","Plan Pro","La oferta · Plan propuesto");
s.addText("Suscripción anual para equipos que necesitan guía técnica y reportes alineados a estándares internacionales — sector industria manufacturera (alimentos), ~1.300 colaboradores (Planta Guarne + Planta Funza).",
  {x:MX,y:2.5,w:11.6,h:0.7,fontFace:F,fontSize:13,color:INK2,lineSpacingMultiple:1.15});
const feats=["Calculadora alcances 1, 2 y 3 para los datos de un (1) año: +14 subcategorías y +6.000 factores de emisión.","Creación de actividades y personalización de fuentes por planta y por proceso.","Descarga de resultados y datos de actividad.","Metodologías IPCC y reporte ISO 14064-1 o GHG Protocol.","Carga de información manual, Excel o API.","Tablero de visualización de resultados para las dos plantas.","Reporte técnico estandarizado (GHG Protocol / ISO 14064-1).","Experto dedicado con 156 horas de soporte.","Validación y control de errores de datos de entrada.","Recomendaciones generales para reducción de emisiones.","Capacitación del equipo en medición, reducción y neutralidad."];
feats.forEach((t,i)=>{let x=MX+(i%2)*6.0,y=3.35+Math.floor(i/2)*0.6;
  s.addShape(p.shapes.ROUNDED_RECTANGLE,{x,y:y+0.03,w:0.28,h:0.28,rectRadius:0.05,fill:{color:ASOFT}});
  s.addText("✓",{x,y:y+0.03,w:0.28,h:0.28,fontFace:F,fontSize:11,bold:true,color:ACD,align:"center",valign:"middle"});
  s.addText(t,{x:x+0.4,y:y-0.05,w:5.4,h:0.5,fontFace:F,fontSize:11.5,color:INK2,valign:"middle"});}); footer(s);

/* ---------- SLIDE 11 — INVERSIÓN (CON ATICA) ---------- */
s=p.addSlide(); header(s,"11","Inversión + valor","La oferta · Inversión");
s.addShape(p.shapes.ROUNDED_RECTANGLE,{x:MX,y:2.7,w:6.7,h:3.4,rectRadius:0.12,fill:{color:P},shadow:shadow()});
s.addShape(p.shapes.ROUNDED_RECTANGLE,{x:MX+0.4,y:3.0,w:2.9,h:0.45,rectRadius:0.22,fill:{color:MINT}});
s.addText("−10% ALIANZA ATICA",{x:MX+0.4,y:3.0,w:2.9,h:0.45,fontFace:F,fontSize:10.5,bold:true,color:ACD,align:"center",valign:"middle"});
s.addText([
  {text:"Estimación de huella de carbono organizacional — Plan Pro · suscripción anual (2 plantas en Colombia)",options:{fontSize:12,color:"CDD3F5",breakLine:true}},
  {text:CLIENTE+"  ·  NIT "+NIT_CLIENTE,options:{fontSize:9.5,color:"9AA3DA"}}
],{x:MX+0.4,y:3.55,w:5.9,h:0.7,fontFace:F,lineSpacingMultiple:1.15});
s.addText(PRECIO_BASE_FMT+" USD",{x:MX+0.4,y:4.3,w:3,h:0.35,fontFace:F,fontSize:18,color:"9AA3DA",strike:true});
s.addText([{text:PRECIO_ANUAL_FMT+" ",options:{fontSize:44,bold:true,color:WHITE}},{text:"USD",options:{fontSize:18,bold:true,color:MINT}}],
  {x:MX+0.4,y:4.7,w:5.9,h:0.85,fontFace:F,valign:"middle"});
s.addText([{text:"Equivale a ",options:{color:"CDD3F5"}},{text:PRECIO_MES_FMT,options:{color:WHITE,bold:true}},{text:" por toda la gestión de carbono.",options:{color:"CDD3F5"}}],
  {x:MX+0.4,y:5.6,w:5.9,h:0.45,fontFace:F,fontSize:12});
let sx=MX+7.0, sw=4.75;
card(s,sx,2.7,sw,0.95,SOFT,LINE);
s.addText([{text:"Opciones de pago: ",options:{bold:true,color:P}},{text:"50% al inicio, 50% al final. ¡Servicios exentos de IVA!",options:{color:INK2}}],
  {x:sx+0.2,y:2.78,w:sw-0.4,h:0.8,fontFace:F,fontSize:11.5,valign:"middle"});
card(s,sx,3.8,sw,1.5,ASOFT,"CFE6DA");
s.addText([{text:"Plan de fidelización: ",options:{bold:true,color:ACD}},{text:"tu precio anual no sube mientras tu suscripción siga activa (ver siguiente slide).",options:{color:INK2}}],
  {x:sx+0.2,y:3.9,w:sw-0.4,h:1.3,fontFace:F,fontSize:11.5,valign:"middle"});
card(s,sx,5.45,sw,0.65,SOFT,LINE);
s.addText("Precio por un (1) año de datos y por las dos plantas. No incluye pólizas ni viajes fuera de Bogotá. Pago en pesos: TRM del primer pago. Validez hasta el "+FECHA_LIMITE+".",
  {x:sx+0.2,y:5.42,w:sw-0.4,h:0.7,fontFace:F,fontSize:9,color:INK3,valign:"middle"}); footer(s);

/* ---------- SLIDE 12 — PLAN DE FIDELIZACIÓN ---------- */
let sf=p.addSlide(); sf.background={color:DARK};
if(exists("cover_bg.png")){ sf.addImage({path:"cover_bg.png",x:0,y:0,w:W,h:H}); }
else { sf.addShape(p.shapes.RECTANGLE,{x:0,y:0,w:W,h:H,fill:{color:DARK}}); sf.addImage({path:ICON_WHITE,x:9.6,y:3.6,w:5.6,h:5.6,transparency:92}); }
sf.addText("12 / "+NT,{x:W-2.1,y:0.45,w:1.4,h:0.4,fontFace:FM,fontSize:10,color:"6B74A8",align:"right",valign:"middle"});
sf.addText("PLAN DE FIDELIZACIÓN",{x:MX,y:0.95,w:9,h:0.35,fontFace:F,fontSize:13,bold:true,color:MINT,charSpacing:4});
sf.addText([{text:"El precio de tu plan anual ",options:{color:WHITE}},{text:"no sube",options:{color:MINT}},{text:".",options:{color:WHITE}}],
  {x:MX,y:1.35,w:11.5,h:0.9,fontFace:F,fontSize:40,bold:true});
sf.addText("Mientras tu suscripción siga activa — te premiamos por tu aprendizaje.",
  {x:MX,y:2.45,w:11.5,h:0.5,fontFace:F,fontSize:16,color:"CDD3F5"});
sf.addShape(p.shapes.ROUNDED_RECTANGLE,{x:4.9,y:3.2,w:2.6,h:0.52,rectRadius:0.26,fill:{color:MINT}});
sf.addText("PRECIO CONGELADO",{x:4.9,y:3.2,w:2.6,h:0.52,fontFace:F,fontSize:11,bold:true,color:ACD,align:"center",valign:"middle",charSpacing:2});
let cy=3.95, chh=1.8, cwd=3.3;
let cxs=[MX, MX+3.85, MX+7.7];
["AÑO 1","AÑO 2","AÑO 3"].forEach((yr,i)=>{ let x=cxs[i];
  sf.addShape(p.shapes.ROUNDED_RECTANGLE,{x:x,y:cy,w:cwd,h:chh,rectRadius:0.1,fill:{color:"222E66"},line:{color:"3D4894",width:1}});
  sf.addText(yr,{x:x,y:cy+0.22,w:cwd,h:0.3,fontFace:F,fontSize:12,bold:true,color:"9FB0E8",align:"center",charSpacing:2});
  sf.addText(PRECIO_ANUAL_FMT,{x:x,y:cy+0.58,w:cwd,h:0.7,fontFace:F,fontSize:30,bold:true,color:WHITE,align:"center",valign:"middle"});
  sf.addText("USD / año",{x:x,y:cy+1.33,w:cwd,h:0.3,fontFace:F,fontSize:12,color:"9FB0E8",align:"center"});
});
sf.addText("=",{x:cxs[0]+cwd,y:cy,w:0.55,h:chh,fontFace:F,fontSize:30,bold:true,color:MINT,align:"center",valign:"middle"});
sf.addText("=",{x:cxs[1]+cwd,y:cy,w:0.55,h:chh,fontFace:F,fontSize:30,bold:true,color:MINT,align:"center",valign:"middle"});
sf.addText("…y se mantiene",{x:cxs[2]+cwd+0.05,y:cy,w:1.25,h:chh,fontFace:F,fontSize:11,italic:true,color:"9FB0E8",valign:"middle"});
sf.addText([{text:"A medida que autogestionas tu huella dependes menos del experto — ",options:{color:"CDD3F5"}},{text:"tu aprendizaje es tu ahorro.",options:{color:MINT,bold:true}}],
  {x:MX,y:6.2,w:11.9,h:0.5,fontFace:F,fontSize:14});
sf.addText("FIDELIZACIÓN · CARBONBOX",{x:MX,y:H-0.45,w:6,h:0.3,fontFace:F,fontSize:9,color:"6B74A8",charSpacing:2});

/* ---------- SLIDE 13 — CIERRE ---------- */
s=p.addSlide(); header(s,String(NT).padStart(2,"0"),"¿Empezamos?","Cierre");
s.addText("Si decides avanzar, así sería el arranque de la medición de huella de carbono de tus dos plantas:",
  {x:MX,y:2.5,w:11.5,h:0.5,fontFace:F,fontSize:15,color:INK2});
const tl=[["Semana 1","Kickoff con los equipos de Guarne y Funza: contexto de cambio climático e identificación de fuentes de emisión."],["Mes 1","Recolección de datos con el experto dedicado. Primer resultado disponible en plataforma."],["Mes 3","Reporte técnico completo + recomendaciones de reducción para ambas plantas."]];
tl.forEach((t,i)=>{let y=3.15+i*0.72;
  s.addText(t[0],{x:MX,y,w:1.6,h:0.5,fontFace:FM,fontSize:13,bold:true,color:ACD,valign:"top"});
  s.addText(t[1],{x:MX+1.8,y,w:9.8,h:0.6,fontFace:F,fontSize:13.5,color:INK2});
  if(i<2)s.addShape(p.shapes.LINE,{x:MX,y:y+0.62,w:W-2*MX,h:0,line:{color:LINE,width:1}});});
s.addShape(p.shapes.ROUNDED_RECTANGLE,{x:MX,y:5.65,w:W-2*MX,h:1.05,rectRadius:0.1,fill:{color:P}});
s.addText("Agenda una reunión",{x:MX+0.4,y:5.65,w:6,h:1.05,fontFace:F,fontSize:20,bold:true,color:WHITE,valign:"middle"});
s.addText([{text:"info@carbonbox.app  -  ",options:{color:"CDD3F5"}},{text:"www.carbonbox.app/#contacto",options:{color:MINT,hyperlink:{url:"https://www.carbonbox.app/#contacto"}}}],
  {x:W-MX-6.2,y:5.65,w:5.8,h:1.05,fontFace:FM,fontSize:12,align:"right",valign:"middle"});

p.writeFile({fileName:path.join(ROOT,"Cotizaciones","PepsiCo Colombia","cotizacion-PepsiCo-Colombia.pptx")}).then(f=>console.log("WROTE",f));
