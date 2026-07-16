import cairosvg, math, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","Recursos")) # leer/escribir en /Recursos
# CarbonBox category palette + brand
# Paleta data-viz Sistema CarbonBox: emisiones en índigo/neutros, verde reservado para lo positivo
VEH="#1620a4"; TEC="#5e6de0"; EDI="#b6bbe8"; MAN="#7a82a0"; OTR="#c2c8db"
NAVY="#1620a4"; INK="#4a526e"; INK3="#7a82a0"; LINE="#e6e8f2"; GRID="#eef1f4"
MENTA="#2f6b4a"; GREEN="#2f6b4a"; MENTAL="#e8f1ec"; WHITE="#ffffff"
Wc,Hc=820,560
SHADOW='<filter id="sh" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="10" stdDeviation="18" flood-color="#0f1535" flood-opacity="0.10"/></filter>'
def card_open(title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{Wc}" height="{Hc}" viewBox="0 0 {Wc} {Hc}">'
    f'<defs>{SHADOW}</defs><rect x="20" y="20" width="{Wc-40}" height="{Hc-40}" rx="26" fill="{WHITE}" stroke="{LINE}" stroke-width="2" filter="url(#sh)"/>'
    f'<text x="58" y="86" font-family="Poppins" font-size="30" font-weight="700" fill="{NAVY}">{title}</text>')
def legend(items,x,y,gap=34):
    s=""
    for i,(c,l) in enumerate(items):
        yy=y+i*gap
        s+=f'<circle cx="{x}" cy="{yy-5}" r="6" fill="{c}"/><text x="{x+16}" y="{yy}" font-family="Poppins" font-size="17" fill="{INK}">{l}</text>'
    return s

# ---------- ILL 1: Huella por actividad (stacked bars) ----------
cats=[("Vehículos",VEH),("Tecnología",TEC),("Edificios",EDI),("Manufactura",MAN),("Otros",OTR)]
# 5 bars, each fractions (top->bottom order matches cats), heights vary
data=[[0.34,0.16,0.18,0.27,0.05],[0.30,0.18,0.20,0.27,0.05],[0.40,0.14,0.16,0.25,0.05],[0.33,0.20,0.18,0.24,0.05],[0.28,0.22,0.20,0.25,0.05]]
years=["2021","2022","2023","2024","2025"]
bx0,bw,gapb=92,64,52; baseY=470; maxH=300
# light gridlines
g=""
for k in range(4):
    yy=baseY-(k+1)*maxH/4
    g+=f'<line x1="80" y1="{yy:.0f}" x2="560" y2="{yy:.0f}" stroke="{GRID}" stroke-width="2"/>'
bars=""
for i,col in enumerate(data):
    x=bx0+i*(bw+gapb); tot=sum(col); h=maxH*(0.72+0.28*(tot/max(sum(c) for c in data)))
    yy=baseY
    # but col sums ~1.0 all; scale heights with a per-bar factor for variation
    factor=[0.86,0.80,1.0,0.83,0.74][i]; H=maxH*factor; yy=baseY
    for f,(_,c) in zip(col,cats):
        seg=H*f; yy-=seg
        bars+=f'<rect x="{x}" y="{yy:.1f}" width="{bw}" height="{seg:.1f}" fill="{c}"/>'
    bars+=f'<text x="{x+bw/2}" y="{baseY+26}" text-anchor="middle" font-family="Poppins" font-size="15" fill="{INK3}">{years[i]}</text>'
ill1=card_open("Huella de carbono por actividad")+g+bars+legend([(c,n) for (n,c) in cats],600,150)+'</svg>'
open("s6_ill1.svg","w").write(ill1)

# ---------- ILL 2: Reducción en el tiempo ----------
yrs=["2025","2026","2027","2028","2029"]
n=len(yrs); x0,x1=110,560; baseY=470; topY=150
xs=[x0+(x1-x0)*i/(n-1) for i in range(n)]
def yv(v,vmin=0,vmax=100): return baseY-(baseY-topY)*((v-vmin)/(vmax-vmin))
trend=[100,98,97,96,95]      # sin acción (flat-ish, gray dashed)
withcb=[100,82,64,48,36]     # con CarbonBox (descending green)
g2=""
for k in range(4):
    yy=baseY-(k+1)*(baseY-topY)/4
    g2+=f'<line x1="{x0}" y1="{yy:.0f}" x2="{x1}" y2="{yy:.0f}" stroke="{GRID}" stroke-width="2"/>'
areapts=" ".join(f"{xs[i]:.1f},{yv(withcb[i]):.1f}" for i in range(n))
area=f'<polygon points="{x0},{baseY} {areapts} {x1},{baseY}" fill="{MENTAL}"/>'
trendp="M"+" L".join(f"{xs[i]:.1f},{yv(trend[i]):.1f}" for i in range(n))
cbp="M"+" L".join(f"{xs[i]:.1f},{yv(withcb[i]):.1f}" for i in range(n))
dots="".join(f'<circle cx="{xs[i]:.1f}" cy="{yv(withcb[i]):.1f}" r="6" fill="{GREEN}"/>' for i in range(n))
xlab="".join(f'<text x="{xs[i]:.1f}" y="{baseY+26}" text-anchor="middle" font-family="Poppins" font-size="15" fill="{INK3}">{yrs[i]}</text>' for i in range(n))
tag=f'<rect x="600" y="150" width="150" height="64" rx="12" fill="{MENTAL}"/><text x="675" y="190" text-anchor="middle" font-family="Poppins" font-size="28" font-weight="700" fill="{MENTA}">−64%</text><text x="675" y="252" text-anchor="middle" font-family="Poppins" font-size="15" fill="{INK}">emisiones</text><text x="675" y="274" text-anchor="middle" font-family="Poppins" font-size="15" fill="{INK}">proyectadas</text>'
leg2=legend([(INK3,"Sin acción"),(GREEN,"Con CarbonBox")],600,330)
ill2=card_open("Reducción de emisiones")+g2+area+f'<path d="{trendp}" fill="none" stroke="{INK3}" stroke-width="3" stroke-dasharray="3 7"/>'+f'<path d="{cbp}" fill="none" stroke="{GREEN}" stroke-width="4"/>'+dots+xlab+tag+leg2+'</svg>'
open("s6_ill2.svg","w").write(ill2)

# ---------- ILL 3: Compensación -> neto cero ----------
yrs3=["2025","2026","2027","2028"]
n3=len(yrs3); x0,x1=110,540; baseY=470; topY=160
xs3=[x0+(x1-x0)*i/(n3-1) for i in range(n3)]
emis=[100,72,48,26]   # net emissions descending
def yv3(v): return baseY-(baseY-topY)*(v/100)
g3=""
for k in range(4):
    yy=baseY-(k+1)*(baseY-topY)/4
    g3+=f'<line x1="{x0}" y1="{yy:.0f}" x2="{x1}" y2="{yy:.0f}" stroke="{GRID}" stroke-width="2"/>'
# bars: remaining emissions (colored) shrinking, green compensation filling the rest to 100
bars3=""
bw3=58
for i in range(n3):
    x=xs3[i]-bw3/2
    eH=(baseY-topY)*(emis[i]/100); 
    # compensation portion (from top of emission up to full)
    compH=(baseY-topY)-eH
    # emission bar (bottom, colored gradient via VEH/MAN mix -> use VEH)
    bars3+=f'<rect x="{x:.1f}" y="{baseY-eH:.1f}" width="{bw3}" height="{eH:.1f}" rx="4" fill="{VEH}" opacity="0.85"/>'
    bars3+=f'<rect x="{x:.1f}" y="{topY:.1f}" width="{bw3}" height="{compH:.1f}" rx="4" fill="{GREEN}" opacity="0.9"/>'
    bars3+=f'<text x="{xs3[i]:.1f}" y="{baseY+26}" text-anchor="middle" font-family="Poppins" font-size="15" fill="{INK3}">{yrs3[i]}</text>'
# neutral line at top
neutral=f'<line x1="{x0-8}" y1="{topY}" x2="{x1+8}" y2="{topY}" stroke="{NAVY}" stroke-width="2" stroke-dasharray="6 6"/><text x="{x1+16}" y="{topY+6}" font-family="Poppins" font-size="14" fill="{NAVY}">neto 0</text>'
# check badge
badge=f'<circle cx="660" cy="300" r="46" fill="{GREEN}"/><path d="M638,300 l16,16 l30,-34" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/><text x="660" y="378" text-anchor="middle" font-family="Poppins" font-size="20" font-weight="700" fill="{NAVY}">Carbono</text><text x="660" y="404" text-anchor="middle" font-family="Poppins" font-size="20" font-weight="700" fill="{NAVY}">neutral</text>'
leg3=legend([(VEH,"Emisiones netas"),(GREEN,"Compensaciones")],600,150)
ill3=card_open("Camino a carbono neutral")+g3+bars3+neutral+leg3+badge+'</svg>'
open("s6_ill3.svg","w").write(ill3)

for name in ["s6_ill1","s6_ill2","s6_ill3"]:
    cairosvg.svg2png(url=name+".svg",write_to=name+".png",output_width=1640,output_height=1120)
print("3 illustrations rendered")
