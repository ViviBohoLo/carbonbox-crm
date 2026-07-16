#!/usr/bin/env python3
"""
Generador del fondo de portada (cover_bg.png) — CarbonBox.

Reconstruye el degradado navy de la portada (bilineal entre las 4 esquinas del
diseño original, con un glow suave arriba-derecha) y superpone el ISOTIPO
(Hexágono PNG.png) GIRADO — no recto — saliendo por el borde derecho, grande y
muy tenue ("como si girara"), según la guía de marca.

Uso:
    python3 generador-cover.py
    -> escribe Recursos/cover_bg.png (respalda el anterior en Recursos/_backup/)

Para ajustar la inclinación o la opacidad del isotipo, editar ROT_* y OP_* abajo.
"""
import os
from PIL import Image

RECURSOS = os.path.join(os.path.dirname(__file__), "..", "Recursos")
W, H = 2560, 1440

# Colores de las 4 esquinas muestreados del diseño original (RGB).
TL = (13, 17, 47)     # arriba-izquierda (navy profundo)
TR = (24, 34, 118)    # arriba-derecha
BL = (15, 23, 97)     # abajo-izquierda
BR = (22, 32, 164)    # abajo-derecha (indigo brillante)

# Glow suave arriba-derecha (centro, radio en px, color e intensidad)
GLOW_CX, GLOW_CY, GLOW_R = int(W*0.80), int(H*0.26), int(W*0.42)
GLOW_ADD = (18, 20, 28)   # se suma en el centro del glow y decae a 0

# Isotipo girado (bleed por la derecha)
HEX_FILE = "Hexágono PNG.png"
HEX1 = dict(scale=1.35, rot=-24, op=0.10, cx=0.86, cy=0.30)  # grande, arriba-der
HEX2 = dict(scale=0.85, rot=-24, op=0.06, cx=0.96, cy=0.82)  # menor, abajo-der


def bilinear(x, y):
    fx, fy = x/(W-1), y/(H-1)
    top = tuple(TL[i]*(1-fx) + TR[i]*fx for i in range(3))
    bot = tuple(BL[i]*(1-fx) + BR[i]*fx for i in range(3))
    return tuple(int(round(top[i]*(1-fy) + bot[i]*fy)) for i in range(3))


def build_gradient():
    # Construir por filas para rapidez razonable
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        fy = y/(H-1)
        for x in range(W):
            fx = x/(W-1)
            r = TL[0]*(1-fx)*(1-fy) + TR[0]*fx*(1-fy) + BL[0]*(1-fx)*fy + BR[0]*fx*fy
            g = TL[1]*(1-fx)*(1-fy) + TR[1]*fx*(1-fy) + BL[1]*(1-fx)*fy + BR[1]*fx*fy
            b = TL[2]*(1-fx)*(1-fy) + TR[2]*fx*(1-fy) + BL[2]*(1-fx)*fy + BR[2]*fx*fy
            # glow radial
            d = ((x-GLOW_CX)**2 + (y-GLOW_CY)**2) ** 0.5
            t = max(0.0, 1 - d/GLOW_R)
            t = t*t
            r += GLOW_ADD[0]*t; g += GLOW_ADD[1]*t; b += GLOW_ADD[2]*t
            px[x, y] = (min(255, int(r)), min(255, int(g)), min(255, int(b)))
    return img


def paste_hex(base, spec):
    hx = Image.open(os.path.join(RECURSOS, HEX_FILE)).convert("RGBA")
    # recortar al contenido real
    bbox = hx.split()[-1].getbbox()
    if bbox:
        hx = hx.crop(bbox)
    # escalar respecto a la altura del lienzo
    target_h = int(H * spec["scale"])
    ratio = hx.width / hx.height
    hx = hx.resize((int(target_h*ratio), target_h), Image.LANCZOS)
    # girar (expand para no recortar)
    hx = hx.rotate(spec["rot"], expand=True, resample=Image.BICUBIC)
    # aplicar opacidad
    r, g, b, a = hx.split()
    a = a.point(lambda v: int(v * spec["op"]))
    hx = Image.merge("RGBA", (r, g, b, a))
    # posicionar por centro relativo (permite bleed fuera del lienzo)
    cx, cy = int(W*spec["cx"]), int(H*spec["cy"])
    base.alpha_composite(hx, (cx - hx.width//2, cy - hx.height//2))


def main():
    grad = build_gradient().convert("RGBA")
    paste_hex(grad, HEX1)
    paste_hex(grad, HEX2)
    out = grad.convert("RGB")

    dst = os.path.join(RECURSOS, "cover_bg.png")
    bkp_dir = os.path.join(RECURSOS, "_backup")
    os.makedirs(bkp_dir, exist_ok=True)
    if os.path.exists(dst) and not os.path.exists(os.path.join(bkp_dir, "cover_bg_original.png")):
        Image.open(dst).save(os.path.join(bkp_dir, "cover_bg_original.png"))
    out.save(dst)
    print("WROTE", dst, out.size)


if __name__ == "__main__":
    main()
