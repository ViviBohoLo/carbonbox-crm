import os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","Recursos"))
import cairosvg, math
W,H=1280,720
NAVY="#13245a"; NAVY2="#0f1c49"; MINT="#9fe3bf"; INK3="#7f8bc0"; INK2="#aab2e8"; WHITE="#ffffff"; CARD="#1b2c66"; CARDB="#33457f"
def hexpath(cx,cy,r,rot):
    pts=[(cx+r*math.cos(math.radians(60*k-90+rot)),cy+r*math.sin(math.radians(60*k-90+rot))) for k in range(6)]
    return "M"+" L".join(f"{p[0]:.1f},{p[1]:.1f}" for p in pts)+" Z"
dots=""
for gx in range(150,1140,28):
    for gy in range(300,600,28):
        dots+=f'<circle cx="{gx}" cy="{gy}" r="1" fill="#2c3a78" opacity="0.45"/>'
hexes=""; cx,cy,r=1130,580,250
for i in range(9): hexes+=f'<path d="{hexpath(cx,cy,r,i*7)}" fill="none" stroke="{MINT}" stroke-width="1.3" opacity="0.06"/>'; r*=0.85

# three identical-price year cards
cards=""
cw,ch,gap=270,168,86
x0=(W-(3*cw+2*gap))//2  # center
ys=372
labels=["AÑO 1","AÑO 2","AÑO 3"]
xs=[x0+i*(cw+gap) for i in range(3)]
for i,x in enumerate(xs):
    cards+=f'<rect x="{x}" y="{ys}" width="{cw}" height="{ch}" rx="14" fill="{CARD}" stroke="{CARDB}" stroke-width="1.5"/>'
    cards+=f'<text x="{x+cw/2}" y="{ys+38}" text-anchor="middle" font-family="Poppins" font-size="14" letter-spacing="4" fill="{MINT}">{labels[i]}</text>'
    cards+=f'<text x="{x+cw/2}" y="{ys+100}" text-anchor="middle" font-family="Poppins" font-size="40" font-weight="700" fill="{WHITE}">$ 3.526</text>'
    cards+=f'<text x="{x+cw/2}" y="{ys+134}" text-anchor="middle" font-family="Poppins" font-size="15" fill="{INK2}">USD / año</text>'
# equal signs between
for i in range(2):
    ex=xs[i]+cw+gap/2
    cards+=f'<text x="{ex:.0f}" y="{ys+ch/2+16:.0f}" text-anchor="middle" font-family="Poppins" font-size="40" font-weight="700" fill="{MINT}">=</text>'
# continuation hint
cards+=f'<text x="{xs[-1]+cw+24}" y="{ys+ch/2+8:.0f}" font-family="Poppins" font-size="15" fill="{INK3}">…y se</text>'
cards+=f'<text x="{xs[-1]+cw+24}" y="{ys+ch/2+30:.0f}" font-family="Poppins" font-size="15" fill="{INK3}">mantiene</text>'

# frozen badge centered above cards
bx,by=W/2-150,300
badge=f'''<rect x="{bx}" y="{by}" width="300" height="44" rx="22" fill="{MINT}"/>
<image href="ic_snow_dark.png" x="{bx+18}" y="{by+11}" width="22" height="22"/>
<text x="{bx+52}" y="{by+29}" font-family="Poppins" font-size="15" font-weight="700" letter-spacing="2" fill="#0f2a18">PRECIO CONGELADO</text>'''

svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs><radialGradient id="bg" cx="20%" cy="10%" r="100%"><stop offset="0%" stop-color="#1a2e6b"/><stop offset="60%" stop-color="{NAVY}"/><stop offset="100%" stop-color="{NAVY2}"/></radialGradient></defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
{hexes}{dots}
<text x="90" y="92" font-family="Poppins" font-size="15" font-weight="600" letter-spacing="6" fill="{MINT}">PLAN DE FIDELIZACIÓN</text>
<text x="90" y="156" font-family="Poppins" font-size="40" font-weight="700" fill="{WHITE}">El precio de tu plan anual <tspan fill="{MINT}">no sube</tspan>.</text>
<text x="90" y="196" font-family="Poppins" font-size="17" fill="{INK2}">Mientras tu suscripción siga activa — te premiamos por tu aprendizaje.</text>
{badge}
{cards}
<text x="90" y="612" font-family="Poppins" font-size="15.5" fill="{INK2}">A medida que autogestionas tu huella dependes menos del experto — <tspan fill="{MINT}" font-weight="600">tu aprendizaje es tu ahorro.</tspan></text>
<text x="90" y="668" font-family="Poppins" font-size="11" letter-spacing="3" fill="{INK3}">FIG. 12 · FIDELIZACIÓN — CARBONBOX</text>
<image href="logo_white.png" x="1052" y="62" width="138" height="38" preserveAspectRatio="xMaxYMid meet"/>
</svg>'''
open("fid.svg","w").write(svg)
cairosvg.svg2png(bytestring=svg.encode(),write_to="fid_slide.png",output_width=2560,output_height=1440)
print("rendered")
