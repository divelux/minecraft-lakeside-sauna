#!/usr/bin/env python3
"""Draws isometric previews and a layer-by-layer plan of the sauna build from src/blocks.json (written by build.py).
Simple voxel drawing with Pillow: every block is one or a few boxes, painted back to front. Not the game's textures.
MIT License - DIVELUX, https://diveluxsaunahat.com
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
FONTS = os.path.join(HERE, "..", "..", "..", "_fonts")
SX, SY, SZ = 18, 12, 20

# (top, side) colours
COL = {
    "grass_block": ("#7aa54f", "#8b6a45"), "dirt": ("#8b6a45", "#7a5b3a"), "sand": ("#e4d3a2", "#d6c28d"),
    "water": ("#5f95c9", "#4f84b8"), "spruce_planks": ("#9b7148", "#8a6440"), "spruce_log": ("#6b4e2f", "#5a3f25"),
    "dark_oak_stairs": ("#4a3420", "#3d2b1a"), "dark_oak_slab": ("#4a3420", "#3d2b1a"),
    "spruce_slab": ("#a57a4f", "#8f6843"), "spruce_stairs": ("#a57a4f", "#8f6843"), "spruce_door": ("#7d5a37", "#6d4e30"),
    "spruce_fence": ("#8a6440", "#7a5838"), "glass_pane": ("#cfe6ee", "#b9d8e4"), "bricks": ("#a3533d", "#8f4633"),
    "blast_furnace": ("#5b5b60", "#48484d"), "water_cauldron": ("#4e9be0", "#4a4a4f"), "barrel": ("#8a6239", "#77542f"),
    "white_carpet": ("#f2f2ee", "#e2e2dd"), "lantern": ("#f5b14a", "#3b3b40"), "campfire": ("#5a3f25", "#4a3420"),
    "oak_log": ("#b89462", "#6e5434"), "birch_log": ("#d8cfa9", "#e6e2d6"), "lily_pad": ("#3f7f35", "#3f7f35"),
    "fern": ("#4f8a3a", "#447a32"), "sugar_cane": ("#9cc66a", "#8ab55b"), "potted_fern": ("#4f8a3a", "#9a5a3a"),
}


def boxes(name, p):
    """Shapes as (x0, x1, y0, y1, z0, z1, colour key, top override)."""
    full = [(0, 1, 0, 1, 0, 1, name, None)]
    if name in ("dark_oak_slab", "spruce_slab"):
        return [(0, 1, .5, 1, 0, 1, name, None)] if p.get("type") == "top" else [(0, 1, 0, .5, 0, 1, name, None)]
    if name.endswith("_stairs"):
        f = p["facing"]
        back = {"south": (0, 1, .5, 1), "north": (0, 1, 0, .5), "east": (.5, 1, 0, 1), "west": (0, .5, 0, 1)}[f]
        return [(0, 1, 0, .5, 0, 1, name, None), (back[0], back[1], .5, 1, back[2], back[3], name, None)]
    if name == "spruce_door":
        f = p["facing"]
        t = .19
        return [{"north": (0, 1, 0, 1, 1 - t, 1), "south": (0, 1, 0, 1, 0, t), "east": (0, t, 0, 1, 0, 1),
                 "west": (1 - t, 1, 0, 1, 0, 1)}[f] + (name, None)]
    if name == "glass_pane":
        if p.get("east") == "true" or p.get("west") == "true":
            return [(0, 1, 0, 1, .44, .56, name, None)]
        return [(.44, .56, 0, 1, 0, 1, name, None)]
    if name == "spruce_fence":
        out = [(.375, .625, 0, 1, .375, .625, name, None)]
        for d, b in {"north": (.44, .56, 0, .375), "south": (.44, .56, .625, 1), "west": (0, .375, .44, .56),
                     "east": (.625, 1, .44, .56)}.items():
            if p.get(d) == "true":
                out.append((b[0], b[1], .4, .9, b[2], b[3], name, None))
        return out
    if name == "lantern":
        y0 = .25 if p.get("hanging") == "true" else 0
        return [(.32, .68, y0, y0 + .5, .32, .68, name, None)]
    if name == "campfire":
        return [(0, 1, 0, .4, 0, 1, name, None), (.3, .7, .4, .85, .3, .7, "lantern", None)]
    if name in ("lily_pad", "white_carpet"):
        return [(0, 1, 0, .07, 0, 1, name, None)] if name == "white_carpet" else [(.1, .9, 0, .05, .1, .9, name, None)]
    if name == "fern":
        return [(.2, .8, 0, .75, .2, .8, name, None)]
    if name == "sugar_cane":
        return [(.3, .7, 0, 1, .3, .7, name, None)]
    if name == "potted_fern":
        return [(.31, .69, 0, .38, .31, .69, "barrel", None), (.25, .75, .38, .9, .25, .75, "fern", None)]
    if name == "water":
        return [(0, 1, 0, .88, 0, 1, name, None)]
    if name.endswith("_log"):
        return [(0, 1, 0, 1, 0, 1, name + "|" + p.get("axis", "y"), None)]
    return full


END = {"oak_log": "#c9a56e", "birch_log": "#d9c28f", "spruce_log": "#b58b5a"}


def colours(c):
    """(top, south, east) colours; log ends show end grain on the faces their axis points to."""
    if "|" in c:
        n, ax = c.split("|")
        top, side = COL[n]
        e = END[n]
        return (e if ax == "y" else top, e if ax == "z" else side, e if ax == "x" else side)
    top, side = COL.get(c, ("#ff00ff", "#ff00ff"))
    return top, side, side


def shade(hexc, k):
    h = hexc.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return (int(r * k), int(g * k), int(b * k))


def load(skip_y=None):
    d = json.load(open(os.path.join(HERE, "blocks.json")))
    out = []
    for k, (n, p) in d.items():
        x, y, z = map(int, k.split(","))
        if skip_y is not None and y >= skip_y:
            continue
        nm = n.split(":")[1]
        if nm == "water" and d.get(f"{x},{y + 1},{z}", [""])[0] == "minecraft:water":
            hb = [(0, 1, 0, 1, 0, 1, "water", None)]
        else:
            hb = boxes(nm, p)
        for i, b in enumerate(hb):
            out.append((x + b[0], x + b[1], y + b[2], y + b[3], z + b[4], z + b[5], b[6], (x, y, z, i)))
    return out


def render(bx, a=22, flip=False, smoke=None):
    """Isometric view from the south-east (flip=True: from the north-west)."""
    if flip:
        bx = [(SX - x1, SX - x0, y0, y1, SZ - z1, SZ - z0, c, (SX - 1 - k[0], k[1], SZ - 1 - k[2], k[3]))
              for x0, x1, y0, y1, z0, z1, c, k in bx]
    hb = a * 1.22

    def P(x, y, z):
        return ((x - z) * a, (x + z) * a * .5 - y * hb)

    pts = [P(x, y, z) for x in (0, SX) for y in (0, SY + 1.6) for z in (0, SZ)]
    minx, maxx = min(p[0] for p in pts), max(p[0] for p in pts)
    miny, maxy = min(p[1] for p in pts), max(p[1] for p in pts)
    pad = 20
    W, H = int(maxx - minx + 2 * pad), int(maxy - miny + 2 * pad)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)

    def Q(x, y, z):
        u, v = P(x, y, z)
        return (u - minx + pad, v - miny + pad)

    # painter's order by block cell (x + y + z), the parts of one block in their own order
    for x0, x1, y0, y1, z0, z1, c, k in sorted(bx, key=lambda b: (b[7][0] + b[7][1] + b[7][2], b[7][1], b[7][3])):
        top, south, east = colours(c)
        faces = [
            ([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], shade(top, 1.0)),
            ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], shade(south, .86)),
            ([(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)], shade(east, .68)),
        ]
        for poly, col in faces:
            dr.polygon([Q(*p) for p in poly], fill=col, outline=shade("#%02x%02x%02x" % col, .82))
    if smoke:
        sx, sy, sz = smoke if not flip else (SX - smoke[0], smoke[1], SZ - smoke[2])
        for i, r in enumerate((.22, .3, .38, .46)):
            u, v = Q(sx + .1 * i, sy + .9 + i * .75, sz - .1 * i)
            g = 205 + i * 10
            dr.ellipse([u - r * a, v - r * a, u + r * a, v + r * a], fill=(g, g, g, 230 - i * 40))
    return im.crop(im.getbbox())


def font(kind, size):
    return ImageFont.truetype(os.path.join(FONTS, {"d": "BricolageGrotesque-Bold.ttf", "t": "Inter-Regular.ttf",
                                                   "s": "Inter-SemiBold.ttf"}[kind]), size)


INK, MUTED, PAPER = (27, 21, 18), (111, 101, 92), (246, 243, 238)


def fit(im, w, h):
    k = min(w / im.width, h / im.height)
    return im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)


def preview():
    smoke = (13.5, 11.2, 8.5)
    ext = render(load(), smoke=smoke)
    cut = render(load(skip_y=5))
    nw = render(load(), flip=True, smoke=smoke)
    W, H = 2000, 1240
    c = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(c)
    d.text((70, 52), "Lakeside Sauna", font=font("d", 76), fill=INK)
    d.text((72, 148), "Minecraft Java Edition structure (.nbt) · 18 × 12 × 20 blocks · vanilla blocks only",
           font=font("t", 30), fill=MUTED)
    big = fit(ext, 1180, 960)
    c.paste(big, (60, 230 + (960 - big.height) // 2), big)
    s1 = fit(cut, 680, 450)
    s2 = fit(nw, 680, 450)
    x2 = 1270
    c.paste(s1, (x2 + (680 - s1.width) // 2, 230), s1)
    d.text((x2, 690), "Cut away: changing room, sauna benches, stove", font=font("s", 24), fill=INK)
    c.paste(s2, (x2 + (680 - s2.width) // 2, 740), s2)
    d.text((x2, 1180 - 4), "From the north-west: the woodpile", font=font("s", 24), fill=INK)
    d.text((70, 1176), "Made by DIVELUX, makers of wool sauna hats · diveluxsaunahat.com · CC BY 4.0", font=font("t", 24),
           fill=MUTED)
    d.text((70, 1206), "Not an official Minecraft product. Not approved by or associated with Mojang or Microsoft.",
           font=font("t", 20), fill=MUTED)
    c.save(os.path.join(OUT, "preview.png"), optimize=True)
    # bigger single views for the listing
    for nm, im in (("view-outside.png", ext), ("view-inside.png", cut), ("view-woodpile.png", nw)):
        bg = Image.new("RGB", (im.width + 80, im.height + 80), PAPER)
        bg.paste(im, (40, 40), im)
        bg.save(os.path.join(OUT, nm), optimize=True)


CODE = {"dirt": "D", "sand": "Sa", "water": "~", "grass_block": "G", "spruce_planks": "P", "spruce_log": "L",
        "dark_oak_stairs": "R", "dark_oak_slab": "Rs", "spruce_slab": "S", "spruce_stairs": "St", "spruce_door": "Dr",
        "spruce_fence": "F", "glass_pane": "Gl", "bricks": "B", "blast_furnace": "Fu", "water_cauldron": "C",
        "barrel": "Ba", "white_carpet": "Ca", "lantern": "Ln", "campfire": "Cf", "oak_log": "O", "birch_log": "Bi",
        "lily_pad": "Li", "fern": "Fe", "sugar_cane": "Sc", "potted_fern": "Pf"}


def layers():
    """Top-down plan of every layer, for building by hand in survival."""
    d = json.load(open(os.path.join(HERE, "blocks.json")))
    cell = 22
    cols = 4
    lw, lh = SX * cell, SZ * cell
    gap, top = 36, 150
    rows = -(-SY // cols)
    W = cols * lw + (cols + 1) * gap
    used = set()
    H = top + rows * (lh + 60) + 360
    c = Image.new("RGB", (W, H), PAPER)
    dr = ImageDraw.Draw(c)
    small = font("s", 10)
    dr.text((gap, 34), "Lakeside Sauna: layer by layer", font=font("d", 44), fill=INK)
    dr.text((gap, 96), "Seen from above, north at the top. Layer 0 is the bottom. One square = one block. Slab halves and the "
            "way stairs and doors face are in the .nbt file and the previews.",
            font=font("t", 20), fill=MUTED)
    for y in range(SY):
        ox = gap + (y % cols) * (lw + gap)
        oy = top + (y // cols) * (lh + 60)
        dr.text((ox, oy), f"Layer {y}", font=font("s", 20), fill=INK)
        oy += 30
        for x in range(SX):
            for z in range(SZ):
                n = d.get(f"{x},{y},{z}")
                r = [ox + x * cell, oy + z * cell, ox + (x + 1) * cell - 1, oy + (z + 1) * cell - 1]
                if not n:
                    dr.rectangle(r, fill=(252, 250, 246), outline=(228, 222, 212))
                    continue
                nm = n[0].split(":")[1]
                used.add(nm)
                dr.rectangle(r, fill=COL[nm][0], outline=(120, 110, 100))
                fc = COL[nm][0].lstrip("#")
                lum = sum(int(fc[i:i + 2], 16) * w for i, w in ((0, .3), (2, .59), (4, .11)))
                dr.text((r[0] + cell / 2, r[1] + cell / 2), CODE[nm], font=small, anchor="mm",
                        fill=(255, 255, 255) if lum < 120 else INK)
    # legend
    ly = top + rows * (lh + 60) + 10
    dr.text((gap, ly), "Key", font=font("s", 22), fill=INK)
    names = sorted(used)
    per = 4
    for i, nm in enumerate(names):
        x = gap + (i % per) * ((W - 2 * gap) // per)
        y = ly + 40 + (i // per) * 34
        dr.rectangle([x, y, x + 26, y + 26], fill=COL[nm][0], outline=(120, 110, 100))
        fc = COL[nm][0].lstrip("#")
        lum = sum(int(fc[i:i + 2], 16) * w for i, w in ((0, .3), (2, .59), (4, .11)))
        dr.text((x + 13, y + 13), CODE[nm], font=font("s", 12), anchor="mm", fill=(255, 255, 255) if lum < 120 else INK)
        dr.text((x + 36, y + 2), nm.replace("_", " "), font=font("t", 19), fill=INK)
    bottom = ly + 40 + (-(-len(names) // per)) * 34 + 20
    dr.text((gap, bottom), "DIVELUX · diveluxsaunahat.com · CC BY 4.0 · Not an official Minecraft product. "
            "Not approved by or associated with Mojang or Microsoft.", font=font("t", 16), fill=MUTED)
    c = c.crop((0, 0, W, bottom + 44))
    c.save(os.path.join(OUT, "layers.png"), optimize=True)


if __name__ == "__main__":
    preview()
    layers()
