import os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","Recursos"))
import json
A=json.load(open("assets_b64.json"))
def d(k): return "data:image/png;base64,"+A[k]

# web image URLs (carbonbox.app / wixstatic)
W={
"plat":"https://static.wixstatic.com/media/9d6db3_81fad12e51d64983b09e3d179ede9d74~mv2.png",
"red":"https://static.wixstatic.com/media/9d6db3_e2144fd0c481411daadcb71977f6a1e8~mv2.png",
"comp":"https://static.wixstatic.com/media/9d6db3_d91898c01abe48a78d3112da02e50c55~mv2.png",
"map":"https://static.wixstatic.com/media/9d6db3_6e369fcdd23648938834cd8e6acc50e0~mv2.png",
"vivi":"https://static.wixstatic.com/media/9d6db3_3a237fd03061432789b71399c4bb9e45~mv2.jpg",
"ale":"https://static.wixstatic.com/media/9d6db3_425b06cd385749dbba3173703b1c2080~mv2.png",
"manu":"https://static.wixstatic.com/media/9d6db3_98a4d9a135be40bf9a3c2b56cef5ce0a~mv2.png",
"lau":"https://static.wixstatic.com/media/9d6db3_0252d619c4274543b6a7e457969b2553~mv2.png",
"migue":"https://static.wixstatic.com/media/9d6db3_14d06adb9b794c7994c95ee42156b60f~mv2.png",
"eli":"https://static.wixstatic.com/media/9d6db3_a30b87ffaeb846b8be8ced2d649449a4~mv2.png",
}

CSS = """
:root{--primary:#1e2a78;--primary-deep:#141d57;--primary-soft:#eef0fb;--primary-100:#dde2f5;--accent:#2f6b4a;--accent-soft:#e8f1ec;--accent-deep:#1e4a32;--ink:#0f1535;--ink-2:#4a526e;--ink-3:#7a82a0;--bg:#fff;--bg-soft:#f7f8fc;--line:#e6e8f2;--radius:14px;--radius-lg:22px;--shadow-md:0 4px 14px rgba(15,21,53,.08),0 18px 40px -10px rgba(15,21,53,.10);--shadow-lg:0 30px 80px -20px rgba(15,21,53,.25);--fd:'Poppins',system-ui,sans-serif;--fm:'JetBrains Mono',ui-monospace,monospace;}
*{box-sizing:border-box;}html,body{margin:0;padding:0;}img{max-width:100%;}
body{font-family:var(--fd);color:var(--ink);background:var(--bg-soft);-webkit-font-smoothing:antialiased;}
.deck{max-width:1180px;margin:0 auto;padding:28px 20px 120px;}
.slide{position:relative;background:#fff;border:1px solid var(--line);border-radius:var(--radius-lg);box-shadow:var(--shadow-md);width:100%;margin:0 0 30px;overflow:hidden;display:flex;flex-direction:column;}
.pad{padding:46px 56px;display:flex;flex-direction:column;min-height:598px;}
.eyebrow{font-size:12px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin:0 0 12px;}
.h2{font-weight:700;font-size:33px;line-height:1.1;letter-spacing:-.02em;margin:0;color:var(--primary);}
.lead{font-size:18px;line-height:1.55;color:var(--ink-2);max-width:62ch;}
.body{font-size:15px;line-height:1.55;color:var(--ink-2);}
.muted{color:var(--ink-3);}
.head{display:flex;align-items:center;justify-content:space-between;margin-bottom:22px;}
.head img{height:25px;}
.num{font-family:var(--fm);font-size:11px;color:var(--ink-3);}
.foot{display:flex;align-items:center;justify-content:space-between;font-size:11px;color:var(--ink-3);border-top:1px solid var(--line);padding:12px 56px;}
.foot .dot{color:var(--accent);}
/* cover */
.cover{background:#14275C;border:none;color:#fff;}
.cover .pad{justify-content:space-between;position:relative;z-index:1;}
.cover .eyebrow{color:#9fe3bf;}
.cover-title{font-weight:700;font-size:50px;line-height:1.05;letter-spacing:-.025em;margin:0;max-width:18ch;color:#fff;}
.cover-for{font-size:19px;color:#cdd3f5;margin-top:16px;}
.chip-plan{display:inline-block;background:var(--accent);color:#fff;border-radius:999px;padding:7px 18px;font-size:12px;font-weight:700;letter-spacing:.04em;margin-top:16px;}
.cover-desc{font-size:14px;color:#cdd3f5;max-width:60ch;margin:12px 0 0;line-height:1.5;}
.cover-meta{font-family:var(--fm);font-size:13px;color:#aab2e8;}
.cover-meta a{color:#9fe3bf;}
.hex{position:absolute;width:480px;opacity:.14;pointer-events:none;z-index:0;}
.hex.tr{top:-120px;right:-130px;}
.hex.br{bottom:-150px;right:-110px;width:380px;opacity:.10;}
.ph{background:rgba(255,255,255,.15);color:#fff;border:1px dashed rgba(255,255,255,.5);border-radius:6px;padding:1px 8px;font-weight:600;font-size:.9em;}
/* cards / grid */
.grid{display:grid;gap:16px;}
.c2{grid-template-columns:1fr 1fr;}.c3{grid-template-columns:repeat(3,1fr);}
.card{background:var(--bg-soft);border:1px solid var(--line);border-radius:var(--radius);padding:18px;}
.card h3{font-size:16px;margin:0 0 6px;color:var(--primary);font-weight:600;}
.card p{margin:0;font-size:13px;line-height:1.5;color:var(--ink-2);}
.ico{width:46px;height:46px;border-radius:50%;background:#fff;border:1px solid #cfe6da;display:grid;place-items:center;margin-bottom:10px;}
.ico img{width:24px;height:24px;}
.adv{display:flex;align-items:center;gap:14px;background:var(--bg-soft);border:1px solid var(--line);border-radius:var(--radius);padding:14px 16px;}
.adv .ico{flex-shrink:0;margin:0;width:42px;height:42px;}
.adv p{margin:0;font-size:13px;color:var(--ink-2);line-height:1.4;}
.stat{background:var(--accent-soft);border:1px solid #cfe6da;border-radius:var(--radius);padding:18px;text-align:center;}
.stat .n{font-weight:800;font-size:34px;color:var(--accent-deep);line-height:1;}
.stat .l{font-size:12px;color:var(--ink-2);margin-top:6px;}
.shot{width:100%;border-radius:12px;border:1px solid var(--line);box-shadow:var(--shadow-md);display:block;}
.quote{background:linear-gradient(135deg,var(--primary-soft),#fff);border-left:4px solid var(--accent);border-radius:var(--radius);padding:20px 24px;font-size:18px;line-height:1.45;color:var(--primary);font-weight:500;font-style:italic;}
.logos{display:flex;flex-wrap:wrap;gap:9px;}
.logos span{background:var(--bg-soft);border:1px solid var(--line);border-radius:8px;padding:8px 13px;font-size:12.5px;color:var(--ink-2);font-weight:500;}
/* flags */
.flags{display:flex;gap:10px;flex-wrap:wrap;}
.fl{text-align:center;}
.fl .fg{width:74px;height:48px;border:1px solid #c9cee0;border-radius:4px;overflow:hidden;display:flex;flex-direction:column;}
.fl .fg.v{flex-direction:row;}
.fl .fg span{flex:1;}
.fl .lb{font-size:11px;color:var(--ink-2);margin-top:5px;}
/* team */
.team{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;}
.mem{background:var(--bg-soft);border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;}
.mem img{width:100%;height:150px;object-fit:cover;object-position:top;display:block;background:#dde2f5;}
.mem .b{padding:10px 12px;}
.mem .nm{font-weight:700;color:var(--primary);font-size:14px;}
.mem .rl{font-size:11px;color:var(--accent);font-weight:600;margin:2px 0 4px;}
.mem .ds{font-size:10.5px;color:var(--ink-2);line-height:1.35;}
/* flist */
.flist{list-style:none;padding:0;margin:10px 0 0;display:grid;grid-template-columns:1fr 1fr;gap:8px 26px;}
.flist li{position:relative;padding-left:26px;font-size:13.5px;line-height:1.4;color:var(--ink-2);}
.flist li::before{content:"";position:absolute;left:0;top:2px;width:17px;height:17px;border-radius:5px;background:var(--accent-soft);}
.flist li::after{content:"\\2713";position:absolute;left:4px;top:1px;font-size:11px;color:var(--accent-deep);font-weight:700;}
/* price */
.pwrap{display:grid;grid-template-columns:1.2fr .8fr;gap:22px;margin-top:14px;}
.pcard{background:radial-gradient(120% 120% at 90% 0%,#26328c,var(--primary) 45%,var(--primary-deep));color:#fff;border-radius:var(--radius-lg);padding:26px 28px;box-shadow:var(--shadow-lg);}
.badge{display:inline-block;background:#9fe3bf;color:var(--accent-deep);font-weight:700;font-size:11px;letter-spacing:.04em;border-radius:999px;padding:5px 12px;text-transform:uppercase;}
.pold{font-size:20px;color:#9aa3da;text-decoration:line-through;margin-top:10px;}
.pnew{font-weight:800;font-size:46px;letter-spacing:-.02em;line-height:1;margin-top:2px;}
.pnew small{font-size:18px;font-weight:600;color:#9fe3bf;}
.pmo{margin-top:8px;font-size:13px;color:#cdd3f5;}
.sbox{background:var(--bg-soft);border:1px solid var(--line);border-radius:var(--radius);padding:14px 16px;font-size:12.5px;color:var(--ink-2);line-height:1.45;margin-bottom:10px;}
.sbox b{color:var(--primary);}
.fbox{background:var(--accent-soft);border:1px solid #cfe6da;border-radius:var(--radius);padding:14px 16px;font-size:12.5px;color:var(--ink-2);line-height:1.45;margin-bottom:10px;}
.fbox b{color:var(--accent-deep);}
/* fidelizacion slide */
.fid{background:#1e2a78;color:#fff;border:none;}
.fid .pad{justify-content:flex-start;}
.fid h2{color:#fff;font-size:30px;font-weight:700;margin:0;}
.hl{background:var(--accent);color:#fff;padding:0 .15em;border-radius:3px;}
.fidwrap{display:grid;grid-template-columns:.7fr 1fr;gap:30px;align-items:center;margin-top:26px;}
.bars{display:flex;align-items:flex-end;gap:14px;height:170px;position:relative;padding-left:10px;}
.bars .bar{width:46px;border-radius:6px 6px 0 0;}
.bars .arrow{position:absolute;left:6px;bottom:30px;width:170px;height:3px;background:#7aa8ff;transform:rotate(-32deg);transform-origin:left;}
.bars .arrow:after{content:"";position:absolute;right:-2px;top:-5px;border:7px solid transparent;border-left-color:#7aa8ff;}
.fidtxt p{color:#cdd3f5;font-size:15px;line-height:1.5;}
.fidtxt .big{color:#fff;font-weight:700;font-size:17px;line-height:1.2;margin-top:16px;}
/* timeline */
.tl{display:grid;grid-template-columns:120px 1fr;gap:16px;padding:14px 0;border-bottom:1px solid var(--line);}
.tl:last-child{border-bottom:none;}
.tl .w{font-family:var(--fm);font-size:13px;color:var(--accent-deep);font-weight:600;}
.tl .t{font-size:14px;color:var(--ink-2);}
.cta{margin-top:auto;background:linear-gradient(135deg,var(--primary),var(--primary-deep));color:#fff;border-radius:var(--radius);padding:20px 26px;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;}
.cta .t{font-weight:700;font-size:20px;}
.cta .c{font-family:var(--fm);font-size:13px;color:#cdd3f5;}
.cta a{color:#9fe3bf;}
.toolbar{position:fixed;right:20px;bottom:20px;display:flex;gap:10px;z-index:50;}
.btn{font-weight:600;font-size:14px;border:none;border-radius:999px;padding:11px 18px;cursor:pointer;box-shadow:var(--shadow-md);}
.btn-p{background:var(--primary);color:#fff;}.btn-g{background:#fff;color:var(--primary);border:1px solid var(--line);}
@media print{@page{size:1280px 720px;margin:0;}body{background:#fff;}.toolbar{display:none!important;}.deck{max-width:none;margin:0;padding:0;}.slide{margin:0;border:none;border-radius:0;box-shadow:none;width:1280px;height:720px;aspect-ratio:auto;page-break-after:always;}.slide:last-child{page-break-after:auto;}}
"""

def head(n): return f'<div class="head"><img src="{d("BL")}" alt="CarbonBox"><span class="num">{n} / 14</span></div>'
def foot(): return '<div class="foot"><span>CarbonBox · Cotización</span><span><span class="dot">●</span> Astillero</span></div>'

S=[]
# 1 COVER
S.append(f'''<section class="slide cover">
<img class="hex tr" src="{d("IC")}"><img class="hex br" src="{d("IC")}">
<div class="pad">
<img src="{d("WH")}" alt="CarbonBox" style="height:34px;align-self:flex-start">
<div>
<p class="eyebrow">Cotización comercial</p>
<h1 class="cover-title">Estimación de huella de carbono organizacional</h1>
<p class="cover-for">Preparada para <span class="ph">[Nombre del astillero]</span></p>
<div><span class="chip-plan">PLAN PRO</span></div>
<p class="cover-desc">Acompañamiento con experto dedicado y reporte técnico alineado a estándares internacionales (GHG Protocol / ISO 14064-1).</p>
</div>
<div class="cover-meta">16 de junio de 2026 &nbsp;·&nbsp; Validez 60 días &nbsp;·&nbsp; <a href="https://www.carbonbox.app">www.carbonbox.app</a></div>
</div></section>''')

# 2 contexto
S.append(f'''<section class="slide"><div class="pad">{head("02")}
<p class="eyebrow">El cliente primero</p><h2 class="h2">Lo que sabemos de <span class="ph" style="background:#fff7d6;color:#7a5b00;border-color:#e2c14a">[Nombre del astillero]</span></h2>
<p class="lead" style="margin-top:16px">Eres un astillero en Cartagena con cerca de <b>200 colaboradores</b>, dedicado a la fabricación y al mantenimiento de embarcaciones de pequeño, mediano y gran calado. El sector naval e industrial enfrenta una presión creciente: navieras, clientes internacionales y la normativa marítima exigen cada vez más datos verificables de emisiones. Medir tu huella hoy te posiciona un paso adelante de tus competidores y fortalece tu relación con los clientes que ya empiezan a pedir esta información.</p>
</div>{foot()}</section>''')

# 3 necesidad
S.append(f'''<section class="slide"><div class="pad">{head("03")}
<p class="eyebrow">El cliente primero</p><h2 class="h2">Su necesidad</h2>
<p class="lead" style="margin-top:16px">Quieres medir la huella de carbono de tu operación <b>hasta alcance 3</b>, conociendo de dónde provienen realmente tus emisiones. Por ahora el foco es la medición —no la verificación—, un primer paso sólido hacia la gestión ambiental de tu astillero. Para hacerlo bien la primera vez, necesitas una plataforma confiable y el acompañamiento de un experto que guíe la recolección de datos y entregue un reporte técnico defendible ante tus clientes y aliados.</p>
</div>{foot()}</section>''')

# 4 que es + platform
S.append(f'''<section class="slide"><div class="pad">{head("04")}
<p class="eyebrow">Nuestra solución</p><h2 class="h2">Qué es CarbonBox</h2>
<p class="body" style="margin:8px 0 14px">Una plataforma que te ayuda a gestionar la huella de carbono de tu empresa, evento o producto, con tecnología y un experto dedicado.</p>
<div class="grid" style="grid-template-columns:1fr 1.1fr;gap:20px;align-items:center">
<div class="grid" style="gap:10px">
<div class="card"><div style="display:flex;gap:12px;align-items:center"><div class="ico" style="margin:0"><img src="{d("ic_measure")}"></div><div><h3 style="margin:0">Medición de CO₂</h3><p>Alcances 1, 2 y 3 con datos confiables.</p></div></div></div>
<div class="card"><div style="display:flex;gap:12px;align-items:center"><div class="ico" style="margin:0"><img src="{d("ic_reduce")}"></div><div><h3 style="margin:0">Reducción de CO₂</h3><p>Prioriza acciones con análisis costo-beneficio.</p></div></div></div>
<div class="card"><div style="display:flex;gap:12px;align-items:center"><div class="ico" style="margin:0"><img src="{d("ic_offset")}"></div><div><h3 style="margin:0">Compensación de CO₂</h3><p>Metas de neutralidad y descarbonización.</p></div></div></div>
</div>
<img class="shot" src="{W["plat"]}" alt="Plataforma CarbonBox">
</div>
<div class="grid c2" style="margin-top:14px"><div class="stat" style="display:flex;align-items:center;gap:16px;text-align:left"><div class="n">30%</div><div class="l" style="margin:0">Ahorro de tiempo en la gestión</div></div><div class="stat" style="display:flex;align-items:center;gap:16px;text-align:left"><div class="n">40%</div><div class="l" style="margin:0">Mejora en productividad</div></div></div>
</div>{foot()}</section>''')

# 5 ventajas
advs=[("ic_cap","Capacidades en medición, reducción y compensación de huella de carbono para ti y tu equipo."),
("ic_chart","Decisiones estratégicas con dashboards claros para reducir y compensar tu huella."),
("ic_users","Una herramienta atractiva para presentar ante juntas directivas, inversionistas y clientes."),
("ic_award","Te destacas en tu sector integrando soluciones innovadoras y tecnológicas.")]
advcards="".join(f'<div class="adv"><div class="ico"><img src="{d(i)}"></div><p>{t}</p></div>' for i,t in advs)
S.append(f'''<section class="slide"><div class="pad">{head("05")}
<p class="eyebrow">Nuestra solución</p><h2 class="h2">Ventajas de trabajar con nosotros</h2>
<div class="grid c2" style="margin-top:16px">{advcards}</div>
<div class="adv" style="margin-top:14px;background:var(--accent-soft);border-color:#cfe6da"><div class="ico"><img src="{d("ic_piggy")}"></div><p>El trabajo año a año con CarbonBox te hará <b>autónomo</b> y obtendrás ahorros al gestionar más eficientemente tu huella de carbono y tu operación.</p></div>
</div>{foot()}</section>''')

# 6 servicios con imagenes
mods=[("ic_calc","Estimación de huella","Cálculo de alcances 1, 2 y 3, personalización de fuentes, carga masiva y tablero de analítica. Reportes ISO 14064-1 / GHG Protocol.",W["plat"]),
("ic_reduce","Reducciones","Simulación de escenarios, análisis costo-beneficio, plan de reducción y seguimiento a las acciones.",W["red"]),
("ic_offset","Compensaciones","Escenarios SBTi y neto cero, portafolio de compensaciones y plan de descarbonización.",W["comp"])]
modcards="".join(f'<div class="card" style="padding:0;overflow:hidden"><img src="{img}" style="width:100%;height:120px;object-fit:cover;display:block"><div style="padding:14px 16px"><div class="ico" style="width:40px;height:40px;margin:-34px 0 8px"><img src="{d(ic)}"></div><h3>{t}</h3><p>{ds}</p></div></div>' for ic,t,ds,img in mods)
S.append(f'''<section class="slide"><div class="pad">{head("06")}
<p class="eyebrow">Nuestra solución</p><h2 class="h2">Nuestras soluciones tecnológicas</h2>
<p class="body" style="margin:8px 0 14px">Accede por un año a los módulos que necesitas para gestionar la huella de carbono de tu empresa.</p>
<div class="grid c3">{modcards}</div>
</div>{foot()}</section>''')

# 7 caso
S.append(f'''<section class="slide"><div class="pad">{head("07")}
<p class="eyebrow">Confianza y credenciales</p><h2 class="h2">Un cliente como tú</h2>
<p class="body" style="margin:12px 0 0;max-width:74ch">Una empresa líder de manufactura industrial en Colombia medía su huella en Excel: 4 meses de trabajo, propenso a errores y difícil de defender ante su junta. Con CarbonBox lo redujeron a <b>6 semanas</b> y descubrieron que el <b>38%</b> de sus emisiones venía de una sola fuente de combustión.</p>
<div class="quote" style="margin-top:18px">“Por primera vez tenemos un número en el que podemos confiar para presentarle a nuestra junta directiva.”</div>
<p class="muted" style="margin-top:12px;font-size:13px">Llevan 3 años renovando su suscripción anual con CarbonBox.</p>
</div>{foot()}</section>''')

# 8 logos
logos=["Siemens","Asobancaria","Biomax","Colgas","EBSA","DNP","Alcaldía de Bogotá","Estéreo Picnic","Fenavi","Agrosavia","Crepes & Waffles","Eternit","Fondo Acción","Zona Franca Bogotá","Cámara Verde","Páramo Presenta","Idartes","Colegio Anglo","Jerónimo Martins","FLP","Atica","Cleantech Hub","Comfama","Equilibria"]
S.append(f'''<section class="slide"><div class="pad">{head("08")}
<p class="eyebrow">Confianza y credenciales</p><h2 class="h2">Empresas que han confiado en nosotros</h2>
<div class="logos" style="margin-top:18px">{"".join(f"<span>{l}</span>" for l in logos)}</div>
</div>{foot()}</section>''')

# 9 mapa + flags + impacto
def flag(name):
    seg={"Colombia":[("#FCD116","50%"),("#003893","25%"),("#CE1126","25%")],
    "Ecuador":[("#FCD116","50%"),("#0038A8","25%"),("#CE1126","25%")],
    "Paraguay":[("#D52B1E","33.33%"),("#fff","33.34%"),("#0038A8","33.33%")],
    "Argentina":[("#74ACDF","33.33%"),("#fff","33.34%"),("#74ACDF","33.33%")]}
    if name in ("México","Perú"):
        cols=["#006847","#fff","#CE1126"] if name=="México" else ["#D91023","#fff","#D91023"]
        bands="".join(f'<span style="background:{c}"></span>' for c in cols)
        return f'<div class="fl"><div class="fg v">{bands}</div><div class="lb">{name}</div></div>'
    bands="".join(f'<span style="background:{c};flex:0 0 {h}"></span>' for c,h in seg[name])
    return f'<div class="fl"><div class="fg">{bands}</div><div class="lb">{name}</div></div>'
flags="".join(flag(n) for n in ["Colombia","Ecuador","Paraguay","México","Argentina","Perú"])
S.append(f'''<section class="slide"><div class="pad">{head("09")}
<p class="eyebrow">Confianza y credenciales</p><h2 class="h2">Nuestro trabajo hoy</h2>
<div class="grid" style="grid-template-columns:.8fr 1.2fr;gap:24px;align-items:center;margin-top:10px">
<img src="{W["map"]}" alt="Mapa LATAM" style="width:100%;max-height:340px;object-fit:contain">
<div>
<p class="body" style="margin:0 0 14px">Hemos acompañado a 7 sectores de la economía en 6 países de Latinoamérica.</p>
<div class="flags">{flags}</div>
<div class="grid c2" style="margin-top:18px">
<div class="stat"><div class="n">54.000</div><div class="l">tCO₂e estimadas</div></div>
<div class="stat"><div class="n">6.012</div><div class="l">tCO₂e reducidas</div></div>
</div></div></div>
</div>{foot()}</section>''')

# 10 equipo
team=[("vivi","Viviana Bohórquez","CEO y Co-fundadora","15 años en estimación y reporte de reducciones de GEI. Certificada ISO 14064-1 y 2."),
("ale","Alejandra Rojas","Líder de proyectos","5 años en inventarios de GEI. Auditora interna de huellas de carbono."),
("manu","Manuel Rivera","Líder en tecnología","Full Stack, 5 años en apps web y móviles; backend y bases de datos."),
("lau","Laura Bautista","Profesional en sostenibilidad","3 años en reportes y gestión de la sostenibilidad y medición de impacto."),
("migue","Miguel Romero","Profesional en sostenibilidad","Ing. ambiental: energías renovables, ACV y sostenibilidad."),
("eli","Eliezer Mas y Rubí","Experto en tecnología","+4 años en desarrollo web y UI/UX; líder de equipos internacionales.")]
memc="".join(f'<div class="mem"><img src="{W[k]}" alt="{nm}"><div class="b"><div class="nm">{nm}</div><div class="rl">{rl}</div><div class="ds">{ds}</div></div></div>' for k,nm,rl,ds in team)
S.append(f'''<section class="slide"><div class="pad">{head("10")}
<p class="eyebrow">Confianza y credenciales</p><h2 class="h2">El equipo experto</h2>
<div class="team" style="margin-top:14px">{memc}</div>
</div>{foot()}</section>''')

# 11 plan pro
feats=["Calculadora alcances 1, 2 y 3: +14 subcategorías y +6.000 factores.","Creación de actividades y personalización de fuentes.","Descarga de resultados y datos de actividad.","Metodologías IPCC y reporte ISO 14064-1 o GHG Protocol.","Carga manual, Excel o API.","Tablero de visualización de resultados.","Reporte técnico estandarizado (GHG / ISO 14064-1).","Experto dedicado con 156 horas de soporte.","Validación y control de errores de datos.","Recomendaciones para reducción de emisiones.","Capacitación del equipo en medición y reducción."]
S.append(f'''<section class="slide"><div class="pad">{head("11")}
<p class="eyebrow">La oferta · Plan propuesto</p><h2 class="h2">Plan Pro</h2>
<p class="body" style="margin:8px 0 0;max-width:80ch">Suscripción anual para equipos que necesitan guía técnica y reportes alineados a estándares internacionales — sector industria manufacturera (astillero), ~200 colaboradores.</p>
<ul class="flist">{"".join(f"<li>{f}</li>" for f in feats)}</ul>
</div>{foot()}</section>''')

# 12 inversion
S.append(f'''<section class="slide"><div class="pad">{head("12")}
<p class="eyebrow">La oferta · Inversión</p><h2 class="h2">Inversión + valor</h2>
<div class="pwrap">
<div class="pcard"><span class="badge">−10% alianza ATICA</span>
<div style="font-size:14px;color:#cdd3f5;margin-top:12px">Estimación de huella de carbono organizacional — Plan Pro · suscripción anual</div>
<div class="pold">$ 3.918 USD</div><div class="pnew">$ 3.526 <small>USD</small></div>
<div class="pmo">Equivale a <b style="color:#fff">$294 USD/mes</b> por toda la gestión de carbono de tu empresa.</div></div>
<div><div class="sbox"><b>Opciones de pago:</b> 50% al inicio, 50% al final. ¡Servicios <b>exentos de IVA</b>!</div>
<div class="fbox"><b>Plan de fidelización:</b> tu precio anual no sube mientras tu suscripción siga activa (ver siguiente slide).</div>
<div class="sbox" style="font-size:11px;color:var(--ink-3)">No incluye pólizas ni viajes fuera de Bogotá. Pago en pesos: TRM del primer pago. Validez hasta el 15 de agosto de 2026.</div></div>
</div></div>{foot()}</section>''')

# 13 fidelizacion
S.append(f'''<section class="slide fid"><img class="hex tr" src="{d("IC")}" style="opacity:.12">
<div class="pad">
<div style="display:flex;justify-content:space-between;align-items:center"><img src="{d("WH")}" style="height:25px"><span class="num" style="color:#8c97d6">13 / 14</span></div>
<h2 style="margin-top:26px">PLAN DE FIDELIZACIÓN DE CLIENTES</h2>
<p style="font-size:19px;font-weight:700;margin-top:14px">¡Queremos premiarte por <span class="hl">tu aprendizaje</span>!</p>
<div class="fidwrap">
<div class="bars"><div class="arrow"></div><div class="bar" style="height:42%;background:#e2655e"></div><div class="bar" style="height:66%;background:#f2c14e"></div><div class="bar" style="height:95%;background:#2f6b4a"></div></div>
<div class="fidtxt"><p>Si durante el trabajo juntos demuestras que tu huella de carbono puede ser autogestionada y necesitas cada año menos asesoría del Experto dedicado:</p>
<p class="big">EL PRECIO DE TU SUSCRIPCIÓN ANUAL NO SUBIRÁ, MIENTRAS TU SUSCRIPCIÓN SIGA ACTIVA.</p></div>
</div></div></section>''')

# 14 cierre
S.append(f'''<section class="slide"><div class="pad">{head("14")}
<p class="eyebrow">Cierre</p><h2 class="h2">¿Empezamos?</h2>
<p class="body" style="margin:10px 0 6px">Si decides avanzar, así sería el arranque de tu medición de huella de carbono:</p>
<div class="tl"><div class="w">Semana 1</div><div class="t">Kickoff con tu equipo: contexto e identificación de fuentes de emisión.</div></div>
<div class="tl"><div class="w">Mes 1</div><div class="t">Recolección de datos con el experto dedicado. Primer resultado en plataforma.</div></div>
<div class="tl"><div class="w">Mes 3</div><div class="t">Reporte técnico completo + recomendaciones de reducción.</div></div>
<div class="cta"><div class="t">Agenda una reunión</div><div class="c">info@carbonbox.app · <a href="https://www.carbonbox.app">www.carbonbox.app</a></div></div>
</div></section>''')

html=f'''<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cotización CarbonBox — Astillero</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><div class="deck">
{"".join(S)}
</div>
<div class="toolbar"><button class="btn btn-g" onclick="if(document.documentElement.requestFullscreen)document.documentElement.requestFullscreen()">⛶ Pantalla completa</button><button class="btn btn-p" onclick="window.print()">⬇ Descargar PDF</button></div>
<script>
var sl=[].slice.call(document.querySelectorAll('.slide'));var idx=0;
function go(i){{idx=Math.max(0,Math.min(sl.length-1,i));sl[idx].scrollIntoView({{behavior:'smooth',block:'start'}});}}
document.addEventListener('keydown',function(e){{if(e.key==='ArrowRight'||e.key==='PageDown'){{e.preventDefault();go(idx+1);}}if(e.key==='ArrowLeft'||e.key==='PageUp'){{e.preventDefault();go(idx-1);}}}});
</script></body></html>'''

open(os.path.join("..","Cotizaciones","Astillero Cartagena","cotizacion-astillero-cartagena.html"),"w",encoding="utf-8").write(html)
print("HTML escrito. tamaño KB:", len(html.encode())//1024, "| slides:", len(S))
