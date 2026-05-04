# backend/app/render.py
import os, re, math, io, base64
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import List, Optional, Tuple

def _font(ruta: str, tam: int, neg: bool, cur: bool):
    stem = os.path.splitext(ruta)[0]
    cands = []
    if neg and cur: 
        cands += [stem+"-BoldItalic.ttf", stem+"-BoldOblique.ttf"]
    elif neg:       
        cands += [stem+"-Bold.ttf"]
    elif cur:       
        cands += [stem+"-Italic.ttf", stem+"-Oblique.ttf"]
    cands.append(ruta)
    for c in cands:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, tam)
            except (OSError, IOError):
                pass
    try:
        return ImageFont.truetype(ruta, tam)
    except (OSError, IOError):
        return ImageFont.load_default()

def render_texto(capa, W, H, ruta_fuente, color_auto, blur, opa):
    lineas = (capa.get("texto") or "").split("\n")
    tmp_d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    fb = _font(ruta_fuente, max(6, int(capa["tamano"] * capa["escala"])), 
               capa["negrita"], capa["cursiva"])
    bb0 = tmp_d.textbbox((0, 0), "Ag", font=fb)
    alto_l = int((bb0[3]-bb0[1]) * capa["interlineado"])

    def tok_info(p):
        est = capa.get("estilos_token", {}).get(p, {})
        neg = est.get("negrita") if est.get("negrita") is not None else capa["negrita"]
        cur = est.get("cursiva") if est.get("cursiva") is not None else capa["cursiva"]
        tam = max(6, int((est.get("tamano") or capa["tamano"]) * capa["escala"]))
        col = est.get("color") or capa.get("color") or color_auto
        sub = est.get("subrayado") if est.get("subrayado") is not None else capa["subrayado"]
        f = _font(ruta_fuente, tam, neg, cur)
        return f, col, sub

    rows = []
    for linea in lineas:
        partes = re.split(r"(\s+)", linea)
        fila = []
        for p in partes:
            if not p: 
                continue
            if p.strip() == "":
                bb = tmp_d.textbbox((0, 0), p, font=fb)
                fila.append((p, fb, color_auto, False, bb[2]-bb[0]))
            else:
                f, col, sub = tok_info(p)
                bb = tmp_d.textbbox((0, 0), p, font=f)
                fila.append((p, f, col, sub, bb[2]-bb[0]))
        rows.append(fila)

    anchos = [sum(t[4] for t in r) for r in rows]
    ancho_max = max(anchos) if anchos else 0
    alto_tot = alto_l * len(rows)

    pad = max(W, H) * 2
    ci = Image.new("RGBA", (ancho_max+pad, alto_tot+pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(ci)
    ox, oy = pad//2, pad//2

    for i, fila in enumerate(rows):
        bw = anchos[i]
        if capa["alineacion"] == "left":  
            x = ox
        elif capa["alineacion"] == "right": 
            x = ox + ancho_max - bw
        else:                            
            x = ox + (ancho_max - bw)//2
        y = oy + i * alto_l
        for (tok, f, col, sub, tw) in fila:
            d.text((x, y), tok, font=f, fill=col)
            if sub:
                bb = d.textbbox((x, y), tok, font=f)
                uy = bb[3]+1
                d.line([(x, uy), (x+tw, uy)], fill=col, width=max(1, capa["tamano"]//20))
            x += tw

    if capa["rotacion"]:
        ci = ci.rotate(-capa["rotacion"], expand=True, resample=Image.BICUBIC)
    if blur > 0:
        ci = ci.filter(ImageFilter.GaussianBlur(blur))
    if opa < 1.0:
        a = ci.split()[3].point(lambda p: int(p*opa))
        ci.putalpha(a)

    cx = int(capa["nx"]*W) - ci.width//2
    cy = int(capa["ny"]*H) - ci.height//2
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(ci, (cx, cy), ci)
    return out

def render_imagen(capa, W, H, blur, opa):
    ruta = capa["ruta"]
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"Imagen no encontrada: {ruta}")
    src = Image.open(ruta).convert("RGBA").copy()
    nw = max(1, int(src.width * capa["escala"]))
    nh = max(1, int(src.height * capa["escala"]))
    src = src.resize((nw, nh), Image.Resampling.LANCZOS)
    if capa["rotacion"]:
        src = src.rotate(-capa["rotacion"], expand=True, resample=Image.BICUBIC)
    if blur > 0:
        src = src.filter(ImageFilter.GaussianBlur(blur))
    if opa < 1.0:
        a = src.split()[3].point(lambda p: int(p*opa))
        src.putalpha(a)
    cx = int(capa["nx"]*W) - src.width//2
    cy = int(capa["ny"]*H) - src.height//2
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(src, (cx, cy), src)
    return out

def renderizar_todo(remera_path, capas, ruta_fuente, blur, opa, W=480, H=500):
    base = Image.open(remera_path).convert("RGBA")
    base = base.resize((W, H), Image.Resampling.LANCZOS)
    color_auto = (0, 0, 0, 255) if "blanca" in remera_path else (255, 255, 255, 255)
    res = base.copy()
    for c in capas:
        if not c.get("visible", True):
            continue
        if c["tipo"] == "texto":
            ov = render_texto(c, W, H, ruta_fuente, color_auto, blur, opa)
        else:
            ov = render_imagen(c, W, H, blur, opa)
        res = Image.alpha_composite(res, ov)
    return res

def image_to_base64(img: Image.Image, format: str = "PNG") -> str:
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode()