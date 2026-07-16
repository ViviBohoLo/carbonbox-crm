const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.defineLayout({ name:"W", width:13.333, height:7.5 });
p.layout = "W";
p.author="CarbonBox"; p.title="Cotización CarbonBox — Astillero";

const P="1E2A78",PD="141D57",ACC="2F6B4A",ACD="1E4A32",INK="0F1535",INK2="4A526E",INK3="7A82A0",
  SOFT="F7F8FC",LINE="E6E8F2",PSOFT="EEF0FB",ASOFT="E8F1EC",MINT="9FE3BF",WHITE="FFFFFF";
const F="Poppins";
const npath=require("path");
const ROOT=npath.join(__dirname,"..");
process.chdir(npath.join(ROOT,"Recursos")); // imágenes/assets en /Recursos
const LOGO_BLUE=ROOT+"/Logos/Logo horizontal azul .png.png";
const LOGO_WHITE=ROOT+"/Logos/Logo horizontal blanco.png.png";
const VLOGO_WHITE=ROOT+"/Logos/Artboard 1 copy 11.png";
const ICON_WHITE=ROOT+"/Logos/icon_blanco.png";
const W=13.333, H=7.5, MX=0.7;

function shadow(){return {type:"outer",color:"0F1535",blur:9,offset:3,angle:135,opacity:0.10};}
function wordmark(s,x,y,color,size){
  // color: "P" => blue header logo; else white cover logo. size = display height in tenths of pt approx -> use fixed heights
  var white = (color===WHITE);
  var path = white?LOGO_WHITE:LOGO_BLUE;
  var ratio = white?(490/136):(1069/324);
  var h = white?0.62:0.42;
  s.addImage({path:path, x:x, y:y, w:h*ratio, h:h});
}
function header(s,num,title,eyebrow){
  wordmark(s,MX,0.40,P,17);
  s.addText(`${num} / 13`,{x:W-2.1,y:0.42,w:1.4,h:0.4,fontFace:"Consolas",fontSize:10,color:INK3,align:"right",valign:"middle"});
  if(eyebrow) s.addText(eyebrow.toUpperCase(),{x:MX,y:1.25,w:11,h:0.3,fontFace:F,fontSize:10.5,bold:true,color:ACC,charSpacing:3});
  s.addText(title,{x:MX,y:1.55,w:12,h:0.8,fontFace:F,fontSize:27,bold:true,color:P});
}
function footer(s){
  s.addShape(p.shapes.LINE,{x:MX,y:H-0.55,w:W-2*MX,h:0,line:{color:LINE,width:1}});
  s.addText("CarbonBox · Cotización",{x:MX,y:H-0.5,w:5,h:0.3,fontFace:F,fontSize:9,color:INK3});
  s.addText([{text:"● ",options:{color:ACC}},{text:"Astillero",options:{color:INK3}}],
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

/* ---------- SLIDE 1 — COVER ---------- */
let s=p.addSlide(); s.background={color:P};
s.addShape(p.shapes.RECTANGLE,{x:0,y:0,w:W,h:H,fill:{color:P}});
wordmark(s,MX,0.5,WHITE,22);
// hexágono saliendo por la esquina superior derecha
s.addImage({path:ICON_WHITE, x:8.7, y:-1.6, w:6.6, h:6.6, transparency:88});
s.addImage({path:ICON_WHITE, x:9.7, y:4.4, w:5.0, h:5.0, transparency:91});
s.addText("COTIZACIÓN COMERCIAL",{x:MX,y:2.0,w:9,h:0.35,fontFace:F,fontSize:12,bold:true,color:MINT,charSpacing:3});
s.addText("Estimación de huella de carbono organizacional",{x:MX,y:2.4,w:8.2,h:1.8,fontFace:F,fontSize:40,bold:true,color:WHITE,lineSpacingMultiple:1.02});
s.addText([{text:"Preparada para ",options:{color:"CDD3F5"}},{text:"[Nombre del astillero]",options:{color:WHITE,bold:true}}],
  {x:MX,y:4.45,w:9,h:0.5,fontFace:F,fontSize:18});
s.addShape(p.shapes.ROUNDED_RECTANGLE,{x:MX,y:5.1,w:1.55,h:0.5,rectRadius:0.25,fill:{color:"2F6B4A"}});
s.addText("PLAN PRO",{x:MX,y:5.1,w:1.55,h:0.5,fontFace:F,fontSize:12,bold:true,color:"0F2A18",align:"center",valign:"middle"});
s.addText("Acompañamiento con experto dedicado y reporte técnico alineado a estándares internacionales (GHG Protocol / ISO 14064-1).",
  {x:MX,y:5.75,w:8.4,h:0.7,fontFace:F,fontSize:13,color:"CDD3F5",lineSpacingMultiple:1.2});
s.addText([{text:"16 de junio de 2026     ·     Validez 60 días     ·     ",options:{color:"AAB2E8"}},
  {text:"www.carbonbox.app",options:{color:"9FE3BF",hyperlink:{url:"https://www.carbonbox.app"}}}],
  {x:MX,y:6.7,w:12,h:0.4,fontFace:"Consolas",fontSize:11});

/* ---------- SLIDE 2 (FUSIÓN 2+3) ---------- */
s=p.addSlide(); header(s,"02","El cliente: contexto y necesidad","El cliente primero");
s.addShape(p.shapes.LINE,{x:W/2,y:2.7,w:0,h:3.4,line:{color:LINE,width:1}});
// izquierda
s.addText("LO QUE SABEMOS",{x:MX,y:2.65,w:5.4,h:0.35,fontFace:F,fontSize:12,bold:true,color:ACC,charSpacing:2});
s.addText("[Nombre del astillero]",{x:MX,y:3.05,w:5.4,h:0.4,fontFace:F,fontSize:17,bold:true,color:P});
s.addText("Astillero en Cartagena, ~200 colaboradores, que fabrica y mantiene embarcaciones de pequeño, mediano y gran calado. El sector naval exige cada vez más datos verificables de emisiones.",
  {x:MX,y:3.55,w:5.3,h:2.4,fontFace:F,fontSize:15,color:INK2,lineSpacingMultiple:1.35});
// derecha
s.addText("LO QUE NECESITA",{x:7.0,y:2.65,w:5.4,h:0.35,fontFace:F,fontSize:12,bold:true,color:ACC,charSpacing:2});
s.addText("Medir su huella hasta alcance 3",{x:7.0,y:3.05,w:5.4,h:0.4,fontFace:F,fontSize:17,bold:true,color:P});
s.addText("Por primera vez y sin verificación por ahora: una plataforma confiable y un experto dedicado que guíe la recolección de datos y entregue un reporte técnico defendible ante clientes y aliados.",
  {x:7.0,y:3.55,w:5.4,h:2.4,fontFace:F,fontSize:15,color:INK2,lineSpacingMultiple:1.35}); footer(s);

/* ---------- SLIDE 4 ---------- */
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
s.addText("Alineado a estándares internacionales:",{x:MX,y:6.4,w:3.4,h:0.3,fontFace:F,fontSize:11,color:INK3,valign:"middle"});
s.addImage({path:"std_ghg.png",x:MX+3.35,y:6.36,w:1.25,h:0.52});
s.addImage({path:"std_iso.png",x:MX+4.8,y:6.32,w:0.58,h:0.56});
s.addImage({path:"s4_hero.png",x:7.05,y:1.85,w:5.35,h:4.8});
footer(s);

/* ---------- SLIDE 5 ---------- */
s=p.addSlide(); header(s,"04","Ventajas de trabajar con nosotros","Nuestra solución");
s.addImage({path:"s5_stars.png",x:MX,y:2.85,w:4.7,h:3.21});
s.addText("Un experto dedicado acompaña tu proceso en todos los planes.",{x:MX,y:6.05,w:4.7,h:0.5,fontFace:F,fontSize:12,italic:true,color:INK3});
const adv5=[["Capacidades en medición, reducción y compensación para ti y tu equipo.","ic_cap.png"],
["Decisiones estratégicas con dashboards claros y accionables.","ic_chart.png"],
["Una herramienta atractiva para presentar ante juntas, inversionistas y clientes.","ic_users.png"],
["Te destacas integrando soluciones innovadoras y tecnológicas.","ic_award.png"]];
adv5.forEach((t,i)=>{let y=2.6+i*0.85; icon(s,5.95,y,0.6,t[1],"FFFFFF");
  s.addText(t[0],{x:6.7,y:y-0.05,w:5.9,h:0.72,fontFace:F,fontSize:13.5,color:INK2,valign:"middle"});});
card(s,5.95,6.05,6.65,0.92,ASOFT,"CFE6DA");
icon(s,6.15,6.27,0.5,"ic_piggy.png","FFFFFF");
s.addText("Año a año serás más autónomo y obtendrás ahorros gestionando tu huella y tu operación.",
  {x:6.8,y:6.12,w:5.65,h:0.78,fontFace:F,fontSize:12,color:INK2,valign:"middle"}); footer(s);

/* ---------- SLIDE 6 ---------- */
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

/* ---------- SLIDE 7 ---------- */
s=p.addSlide(); header(s,"06","Un cliente como tú","Confianza y credenciales");
s.addText("Una empresa líder de manufactura industrial en Colombia medía su huella en Excel: 4 meses de trabajo, propenso a errores y difícil de defender ante su junta. Con CarbonBox lo redujeron a 6 semanas y descubrieron que el 38% de sus emisiones venía de una sola fuente de combustión.",
  {x:MX,y:2.7,w:11.6,h:1.5,fontFace:F,fontSize:15.5,color:INK2,lineSpacingMultiple:1.3});
card(s,MX,4.6,11.75,1.2,PSOFT,"DDE2F5");
s.addShape(p.shapes.RECTANGLE,{x:MX,y:4.6,w:0.07,h:1.2,fill:{color:ACC}});
s.addText("“Por primera vez tenemos un número en el que podemos confiar para presentarle a nuestra junta directiva.”",
  {x:MX+0.35,y:4.6,w:11.1,h:1.2,fontFace:F,fontSize:16,italic:true,bold:true,color:P,valign:"middle"});
s.addText("Llevan 3 años renovando su suscripción anual con CarbonBox.",{x:MX,y:5.95,w:11,h:0.3,fontFace:F,fontSize:12,color:INK3}); footer(s);

/* ---------- SLIDE 8 ---------- */
s=p.addSlide(); header(s,"07","Empresas que han confiado en nosotros","Confianza y credenciales");
const logos=["Siemens","Biomax","Fenavi","Asobancaria","Crepes & Waffles","Estéreo Picnic","Ara","Colgas","Zona Franca Bogotá","Agrosavia","Fundación Santa Fe","EBSA","Elementia","Eternit","Páramo Presenta","Alcaldía de Bogotá","Idartes","Cámara Verde","Colegio Anglo","DNP","Jerónimo Martins","FLP","Atica","Fondo Acción"];
const cols=6, cw=1.92, chh=0.62, gx=0.05, gy=0.18, x0=MX, y0=2.7;
logos.forEach((t,i)=>{let c=i%cols,r=Math.floor(i/cols);let x=x0+c*(cw+gx),y=y0+r*(chh+gy);
  card(s,x,y,cw,chh,SOFT,LINE);
  s.addText(t,{x:x+0.05,y,w:cw-0.1,h:chh,fontFace:F,fontSize:10.5,color:INK2,align:"center",valign:"middle"});}); footer(s);

/* ---------- SLIDE 9 ---------- */
s=p.addSlide(); header(s,"08","Nuestro trabajo hoy","Confianza y credenciales");
s.addImage({path:"s9_map.png",x:MX,y:2.35,w:3.7,h:4.35});
s.addText("Hemos acompañado a 7 sectores de la economía en 6 países de Latinoamérica.",
  {x:4.85,y:2.5,w:7.7,h:0.6,fontFace:F,fontSize:15,color:INK2,lineSpacingMultiple:1.2});
const countries=["Colombia","Ecuador","Paraguay","México","Argentina","Perú"];
countries.forEach((n,i)=>{let cx=4.9+i*1.3; flag(s,cx,3.4,0.9,0.58,n);});
[["54.000","tCO₂e estimadas"],["6.012","tCO₂e reducidas"],["6","países"],["7","sectores"]].forEach((c,i)=>{let x=4.9+(i%2)*3.95,y=4.6+Math.floor(i/2)*1.05;card(s,x,y,3.75,0.92,ASOFT,"CFE6DA");
  s.addText(c[0],{x:x+0.22,y:y,w:1.7,h:0.92,fontFace:F,fontSize:26,bold:true,color:ACD,valign:"middle"});
  s.addText(c[1],{x:x+1.85,y:y,w:1.8,h:0.92,fontFace:F,fontSize:11.5,color:INK2,valign:"middle"});}); footer(s);

/* ---------- SLIDE 10 ---------- */
s=p.addSlide(); header(s,"09","El equipo experto","Confianza y credenciales");
const team=[["t_vivi_sq.png","Viviana Bohórquez","CEO y Co-fundadora","15 años en estimación y reporte de reducciones de GEI. Certificada ISO 14064-1 y 2."],
["t_ale_sq.png","Alejandra Rojas","Líder de proyectos","5 años en inventarios de GEI. Auditora interna de huellas de carbono."],
["t_manu_sq.png","Manuel Rivera","Líder en tecnología","Full Stack, 5 años en apps web y móviles; backend y bases de datos."],
["t_lau_sq.png","Laura Bautista","Profesional en sostenibilidad","3 años en reportes y gestión de la sostenibilidad y medición de impacto."],
["t_migue_sq.png","Miguel Romero","Profesional en sostenibilidad","Ing. ambiental: energías renovables, ACV y sostenibilidad."],
["t_eli_sq.png","Eliezer Mas y Rubí","Experto en tecnología","+4 años en desarrollo web y UI/UX; líder de equipos internacionales."]];
team.forEach((m,i)=>{let x=MX+(i%2)*6.0,y=2.5+Math.floor(i/2)*1.45;card(s,x,y,5.75,1.3,SOFT,LINE);
  s.addImage({path:m[0],x:x+0.24,y:y+0.27,w:0.78,h:0.78,rounding:true,sizing:{type:"cover",w:0.78,h:0.78}});
  s.addText(m[1],{x:x+1.18,y:y+0.16,w:4.5,h:0.32,fontFace:F,fontSize:12.5,bold:true,color:P});
  s.addText(m[2],{x:x+1.18,y:y+0.47,w:4.5,h:0.28,fontFace:F,fontSize:10,bold:true,color:ACC});
  s.addText(m[3],{x:x+1.18,y:y+0.73,w:4.55,h:0.5,fontFace:F,fontSize:9.5,color:INK2,lineSpacingMultiple:1.08});}); footer(s);

/* ---------- SLIDE 11 ---------- */
s=p.addSlide(); header(s,"10","Plan Pro","La oferta · Plan propuesto");
s.addText("Suscripción anual para equipos que necesitan guía técnica y reportes alineados a estándares internacionales — sector industria manufacturera (astillero), ~200 colaboradores.",
  {x:MX,y:2.5,w:11.6,h:0.6,fontFace:F,fontSize:13.5,color:INK2});
const feats=["Calculadora alcances 1, 2 y 3: +14 subcategorías y +6.000 factores de emisión.","Creación de actividades y personalización de fuentes de emisión.","Descarga de resultados y datos de actividad.","Metodologías IPCC y reporte ISO 14064-1 o GHG Protocol.","Carga de información manual, Excel o API.","Tablero de visualización de resultados.","Reporte técnico estandarizado (GHG Protocol / ISO 14064-1).","Experto dedicado con 156 horas de soporte.","Validación y control de errores de datos de entrada.","Recomendaciones generales para reducción de emisiones.","Capacitación del equipo en medición, reducción y neutralidad."];
feats.forEach((t,i)=>{let x=MX+(i%2)*6.0,y=3.25+Math.floor(i/2)*0.62;
  s.addShape(p.shapes.ROUNDED_RECTANGLE,{x,y:y+0.03,w:0.28,h:0.28,rectRadius:0.05,fill:{color:ASOFT}});
  s.addText("✓",{x,y:y+0.03,w:0.28,h:0.28,fontFace:F,fontSize:11,bold:true,color:ACD,align:"center",valign:"middle"});
  s.addText(t,{x:x+0.4,y:y-0.05,w:5.4,h:0.5,fontFace:F,fontSize:11.5,color:INK2,valign:"middle"});}); footer(s);

/* ---------- SLIDE 12 ---------- */
s=p.addSlide(); header(s,"11","Inversión + valor","La oferta · Inversión");
// price card
s.addShape(p.shapes.ROUNDED_RECTANGLE,{x:MX,y:2.7,w:6.7,h:3.4,rectRadius:0.12,fill:{color:P},shadow:shadow()});
s.addShape(p.shapes.ROUNDED_RECTANGLE,{x:MX+0.4,y:3.0,w:2.7,h:0.45,rectRadius:0.22,fill:{color:MINT}});
s.addText("−10% ALIANZA ATICA",{x:MX+0.4,y:3.0,w:2.7,h:0.45,fontFace:F,fontSize:10.5,bold:true,color:ACD,align:"center",valign:"middle"});
s.addText("Estimación de huella de carbono organizacional — Plan Pro · suscripción anual",
  {x:MX+0.4,y:3.6,w:5.9,h:0.5,fontFace:F,fontSize:12.5,color:"CDD3F5"});
s.addText("$ 3.918 USD",{x:MX+0.4,y:4.15,w:3,h:0.4,fontFace:F,fontSize:18,color:"9AA3DA",strike:true});
s.addText([{text:"$ 3.526 ",options:{fontSize:44,bold:true,color:WHITE}},{text:"USD",options:{fontSize:18,bold:true,color:MINT}}],
  {x:MX+0.4,y:4.5,w:5.9,h:0.9,fontFace:F,valign:"middle"});
s.addText([{text:"Equivale a ",options:{color:"CDD3F5"}},{text:"$294 USD/mes",options:{color:WHITE,bold:true}},{text:" por toda la gestión de carbono.",options:{color:"CDD3F5"}}],
  {x:MX+0.4,y:5.5,w:5.9,h:0.5,fontFace:F,fontSize:12});
// side boxes
let sx=MX+7.0, sw=4.75;
card(s,sx,2.7,sw,0.95,SOFT,LINE);
s.addText([{text:"Opciones de pago: ",options:{bold:true,color:P}},{text:"50% al inicio, 50% al final. ¡Servicios exentos de IVA!",options:{color:INK2}}],
  {x:sx+0.2,y:2.78,w:sw-0.4,h:0.8,fontFace:F,fontSize:11.5,valign:"middle"});
card(s,sx,3.8,sw,1.5,ASOFT,"CFE6DA");
s.addText([{text:"Plan de fidelización: ",options:{bold:true,color:ACD}},{text:"tu precio anual no sube mientras tu suscripción siga activa (ver siguiente slide).",options:{color:INK2}}],
  {x:sx+0.2,y:3.9,w:sw-0.4,h:1.3,fontFace:F,fontSize:11.5,valign:"middle"});
card(s,sx,5.45,sw,0.65,SOFT,LINE);
s.addText("No incluye pólizas ni viajes fuera de Bogotá. Pago en pesos: TRM del primer pago. Validez hasta el 15 de agosto de 2026.",
  {x:sx+0.2,y:5.45,w:sw-0.4,h:0.65,fontFace:F,fontSize:9.5,color:INK3,valign:"middle"}); footer(s);

/* ---------- SLIDE 13 — PLAN DE FIDELIZACIÓN (lienzo original) ---------- */
let sf=p.addSlide();
sf.addImage({path:"fid_slide.png", x:0, y:0, w:W, h:H});

/* ---------- SLIDE 14 — CIERRE ---------- */
s=p.addSlide(); header(s,"13","¿Empezamos?","Cierre");
s.addText("Si decides avanzar, así sería el arranque de tu medición de huella de carbono:",
  {x:MX,y:2.5,w:11.5,h:0.5,fontFace:F,fontSize:15,color:INK2});
const tl=[["Semana 1","Kickoff con tu equipo: contexto e identificación de fuentes de emisión."],["Mes 1","Recolección de datos con el experto dedicado. Primer resultado en plataforma."],["Mes 3","Reporte técnico completo + recomendaciones de reducción."]];
tl.forEach((t,i)=>{let y=3.15+i*0.72;
  s.addText(t[0],{x:MX,y,w:1.6,h:0.5,fontFace:"Consolas",fontSize:13,bold:true,color:ACD,valign:"top"});
  s.addText(t[1],{x:MX+1.8,y,w:9.8,h:0.6,fontFace:F,fontSize:13.5,color:INK2});
  if(i<2)s.addShape(p.shapes.LINE,{x:MX,y:y+0.62,w:W-2*MX,h:0,line:{color:LINE,width:1}});});
s.addShape(p.shapes.ROUNDED_RECTANGLE,{x:MX,y:5.65,w:W-2*MX,h:1.05,rectRadius:0.1,fill:{color:P}});
s.addText("Agenda una reunión",{x:MX+0.4,y:5.65,w:6,h:1.05,fontFace:F,fontSize:20,bold:true,color:WHITE,valign:"middle"});
s.addText([{text:"info@carbonbox.app   ·   ",options:{color:"CDD3F5"}},{text:"www.carbonbox.app",options:{color:"9FE3BF",hyperlink:{url:"https://www.carbonbox.app"}}}],
  {x:W-MX-6.2,y:5.65,w:5.8,h:1.05,fontFace:"Consolas",fontSize:12,align:"right",valign:"middle"});

p.writeFile({fileName:npath.join(ROOT,"Cotizaciones","Astillero Cartagena","cotizacion-astillero-cartagena.pptx")}).then(f=>console.log("WROTE",f));
