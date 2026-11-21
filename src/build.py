#!/usr/bin/env python3
"""Lakeside Finnish sauna for Minecraft Java Edition, written as a Structure Block file (.nbt).

Builds the structure block by block, writes
  ../lakeside-sauna.nbt          DataVersion 5023 = Java Edition 26.3 (latest release, November 2026)
  ../lakeside-sauna-1.21.1.nbt   DataVersion 3955 = Java Edition 1.21.1 (same blocks; newer versions upgrade it on load)
then reads both files back and checks them (see check()), and draws the previews with render.py.

Only vanilla blocks that have been in the game since 1.17 or earlier.
Needs: pip install nbtlib pillow        MIT License - DIVELUX, https://diveluxsaunahat.com
"""
import json
import math
import os
import sys
from collections import Counter

import nbtlib
from nbtlib import Compound, Int, List, String

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
SX, SY, SZ = 18, 12, 20                      # x (west -> east), y (up), z (north -> south)
FILES = [("lakeside-sauna.nbt", 5023, "Java Edition 26.3"),
         ("lakeside-sauna-1.21.1.nbt", 3955, "Java Edition 1.21.1")]

W = {}                                       # (x, y, z) -> (name, {props})


def put(x, y, z, name, **props):
    assert 0 <= x < SX and 0 <= y < SY and 0 <= z < SZ, (x, y, z, name)
    W[(x, y, z)] = ("minecraft:" + name, {k: str(v).lower() for k, v in props.items()})


def box(x0, x1, y0, y1, z0, z1, name, **props):
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                put(x, y, z, name, **props)


# ---- terrain: 3 layers of ground and a small pond ------------------------------------------------
def in_pond(x, z):
    return 12 <= z <= 18 and 1 <= x <= 16 and ((x - 8.5) / 8.2) ** 2 + ((z - 15.6) / 4.2) ** 2 <= 1.0


POND = {(x, z) for x in range(SX) for z in range(SZ) if in_pond(x, z)}
for x in range(SX):
    for z in range(SZ):
        if (x, z) in POND:
            put(x, 0, z, "sand")
            put(x, 1, z, "water", level=0)
            put(x, 2, z, "water", level=0)
        else:
            put(x, 0, z, "dirt")
            put(x, 1, z, "dirt")
            near = any((x + dx, z + dz) in POND for dx in (-1, 0, 1) for dz in (-1, 0, 1))
            put(x, 2, z, "sand" if near else "grass_block", snowy=False)

# ---- the cabin: walls x 4..14, z 3..9; changing room x 5..7, sauna x 9..13 ----------------------
X0, X1, Z0, Z1 = 4, 14, 3, 9
box(X0, X1, 2, 2, Z0, Z1, "spruce_planks")                 # floor
box(X0, X1, 2, 2, Z1 + 1, Z1 + 2, "spruce_planks")         # terrace toward the lake
for y in range(3, 7):                                      # log walls, 4 high
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            edge_x, edge_z = x in (X0, X1), z in (Z0, Z1)
            if edge_x and edge_z:
                put(x, y, z, "spruce_log", axis="y")
            elif edge_z:
                put(x, y, z, "spruce_log", axis="x")
            elif edge_x:
                put(x, y, z, "spruce_log", axis="z")
    box(8, 8, y, y, Z0 + 1, Z1 - 1, "spruce_planks")       # wall between the rooms
box(X0, X1, 7, 7, Z0, Z1, "spruce_planks")                 # ceiling

# gable roof of dark oak, 1 block overhang, ridge along x
for x in range(X0 - 1, X1 + 2):
    for k in range(4):
        put(x, 7 + k, Z0 - 1 + k, "dark_oak_stairs", facing="south", half="bottom", shape="straight", waterlogged=False)
        put(x, 7 + k, Z1 + 1 - k, "dark_oak_stairs", facing="north", half="bottom", shape="straight", waterlogged=False)
    put(x, 11, 6, "dark_oak_slab", type="bottom", waterlogged=False)
for x in (X0, X1):                                         # gable ends
    for k, (za, zb) in enumerate([(4, 8), (5, 7), (6, 6)]):
        box(x, x, 8 + k, 8 + k, za, zb, "spruce_planks")


def door(x, z, facing, hinge="left"):
    for half, y in (("lower", 3), ("upper", 4)):
        put(x, y, z, "spruce_door", facing=facing, half=half, hinge=hinge, open=False, powered=False)


door(6, Z1, "north")                                       # front door from the terrace
door(8, 6, "east")                                         # changing room -> sauna
WINDOWS = [(4, 4, 6), (4, 5, 6), (11, 4, 9), (12, 4, 9), (14, 4, 6), (10, 4, 3), (11, 4, 3)]
for x, y, z in WINDOWS:
    put(x, y, z, "glass_pane", waterlogged=False)          # connections are filled in below

# changing room: bench along the west wall, barrel with a towel, a fern, light
for z in (5, 6, 7):
    put(5, 3, z, "spruce_stairs", facing="west", half="bottom", shape="straight", waterlogged=False)
put(7, 3, 4, "barrel", facing="up", open=False)
put(7, 4, 4, "white_carpet")
put(5, 3, 8, "potted_fern")
put(6, 6, 6, "lantern", hanging=True, waterlogged=False)

# sauna: two benches on the north wall, stove with a brick chimney, water bucket, light
for x in range(9, 13):
    put(x, 3, 4, "spruce_planks")
    put(x, 4, 4, "spruce_slab", type="top", waterlogged=False)    # upper bench
    put(x, 3, 5, "spruce_slab", type="top", waterlogged=False)    # lower bench / step
put(13, 3, 8, "blast_furnace", facing="west", lit=False)          # the stove
for y in range(4, 11):
    put(13, y, 8, "bricks")                                       # chimney through ceiling and roof
put(13, 11, 8, "campfire", facing="south", lit=True, signal_fire=False, waterlogged=False)   # smoke on top
put(12, 3, 8, "water_cauldron", level=3)                          # the water bucket
put(11, 6, 6, "lantern", hanging=True, waterlogged=False)

# terrace: bench against the front wall, lanterns on posts
for x in (10, 11, 12):
    put(x, 3, 10, "spruce_stairs", facing="north", half="bottom", shape="straight", waterlogged=False)
for x in (X0, X1):
    put(x, 3, 11, "spruce_fence", waterlogged=False)
    put(x, 4, 11, "lantern", hanging=False, waterlogged=False)

# woodpile on the west side under a lean-to roof
for x in (1, 2):
    for y in (3, 4):
        for z in range(4, 9):
            put(x, y, z, "birch_log" if (x + y + z) % 3 == 0 else "oak_log", axis="z")
for z in (3, 9):
    for y in (3, 4):
        put(1, y, z, "spruce_fence", waterlogged=False)
box(1, 3, 5, 5, 3, 9, "spruce_slab", type="bottom", waterlogged=False)
put(2, 3, 11, "spruce_log", axis="y")                              # chopping stump

# dock: top slabs at ground level over the water, fence posts below
for z in range(12, 16):
    for x in (7, 8):
        if (x, z) in POND:
            put(x, 2, z, "spruce_slab", type="top", waterlogged=True)
            if z in (13, 15):
                put(x, 1, z, "spruce_fence", waterlogged=True)

# a few plants
for x, z in [(13, 15), (4, 16), (11, 17)]:
    assert (x, z) in POND and (x, 2, z) not in [(7, 2, z), (8, 2, z)]
    put(x, 3, z, "lily_pad")
for x, z in [(15, 2), (0, 11), (16, 9), (3, 1)]:
    put(x, 3, z, "fern")
for x, z in [(15, 13), (2, 13), (16, 18)]:                                   # reeds on the beach, next to the water
    assert W[(x, 2, z)][0] == "minecraft:sand" and any((x + d, z) in POND for d in (-1, 1))
    put(x, 3, z, "sugar_cane", age=0)
    put(x, 4, z, "sugar_cane", age=0)

# ---- fence and pane connections (as the game would set them) -------------------------------------
SOLID = {"spruce_log", "spruce_planks", "oak_log", "birch_log", "bricks", "dirt", "sand", "grass_block", "barrel",
         "blast_furnace", "spruce_fence", "glass_pane"}
DIRS = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
for (x, y, z), (name, props) in list(W.items()):
    short = name.split(":")[1]
    if short in ("spruce_fence", "glass_pane"):
        for d, (dx, dz) in DIRS.items():
            nb = W.get((x + dx, y, z + dz), ("minecraft:air", {}))[0].split(":")[1]
            ok = nb in SOLID and (short == "glass_pane" or nb != "glass_pane")
            if short == "glass_pane" and nb == "spruce_fence":
                ok = False
            props[d] = "true" if ok else "false"

# everything else inside the box is air, so the build clears grass and snow where it is placed
for x in range(SX):
    for y in range(SY):
        for z in range(SZ):
            W.setdefault((x, y, z), ("minecraft:air", {}))


# ---- write -----------------------------------------------------------------------------------------
def to_nbt(data_version):
    keys = sorted({(n, tuple(sorted(p.items()))) for n, p in W.values()}, key=lambda k: (k[0] != "minecraft:air", k))
    index = {k: i for i, k in enumerate(keys)}
    palette = List[Compound]([
        Compound({"Name": String(n), **({"Properties": Compound({a: String(b) for a, b in p})} if p else {})})
        for n, p in keys])
    blocks = List[Compound]([
        Compound({"pos": List[Int]([Int(x), Int(y), Int(z)]), "state": Int(index[(n, tuple(sorted(p.items())))])})
        for (x, y, z), (n, p) in sorted(W.items(), key=lambda kv: (kv[0][1], kv[0][2], kv[0][0]))])
    return nbtlib.File({"DataVersion": Int(data_version), "size": List[Int]([Int(SX), Int(SY), Int(SZ)]),
                        "palette": palette, "blocks": blocks, "entities": List[Compound]([])}, root_name="")


def check(path, data_version, blockstates_dir=None):
    """Read the file back and check it. blockstates_dir: the game's assets/minecraft/blockstates folder
    (extracted from the official client jar) to check block names and properties against that version."""
    f = nbtlib.load(path)                     # gzip is detected automatically
    r = []
    assert int(f["DataVersion"]) == data_version
    size = [int(v) for v in f["size"]]
    assert size == [SX, SY, SZ], size
    pal = f["palette"]
    seen = set()
    for b in f["blocks"]:
        p = tuple(int(v) for v in b["pos"])
        assert all(0 <= p[i] < size[i] for i in range(3)), p
        assert p not in seen, ("duplicate", p)
        seen.add(p)
        assert 0 <= int(b["state"]) < len(pal)
    assert len(seen) == SX * SY * SZ
    assert len(f["entities"]) == 0
    counts = Counter(str(pal[int(b["state"])]["Name"]) for b in f["blocks"])
    used = {int(b["state"]) for b in f["blocks"]}
    assert used == set(range(len(pal))), "unused palette entries"
    problems = []
    if blockstates_dir:
        for e in pal:
            name = str(e["Name"]).split(":")[1]
            props = {str(k): str(v) for k, v in e.get("Properties", {}).items()}
            fp = os.path.join(blockstates_dir, name + ".json")
            if name == "air":
                continue
            if not os.path.exists(fp):
                problems.append(f"unknown block {name}")
                continue
            bs = json.load(open(fp))
            if "variants" in bs:
                ok = False
                for key in bs["variants"]:
                    want = dict(kv.split("=") for kv in key.split(",") if kv)
                    if all(props.get(k) == v for k, v in want.items()):
                        ok = True
                if not ok:
                    problems.append(f"{name} {props}: no matching variant")
                # every property the model uses must be set
                keys = {kv.split("=")[0] for key in bs["variants"] for kv in key.split(",") if kv}
                miss = keys - set(props)
                if miss and name not in ("water",):
                    problems.append(f"{name}: properties not set {miss}")
            else:  # multipart (fences, panes): the property names must exist
                names = set()
                for part in bs["multipart"]:
                    w = part.get("when", {})
                    for cond in (w.get("OR") or w.get("AND") or [w]):
                        names |= set(cond)
                extra = set(props) - names - {"waterlogged"}
                if extra:
                    problems.append(f"{name}: unknown properties {extra}")
    solid = sum(n for k, n in counts.items() if k != "minecraft:air")
    r.append(f"{os.path.basename(path)}: DataVersion {data_version}, size {size[0]} x {size[1]} x {size[2]}, "
             f"{len(seen)} positions, {len(pal)} palette states, {len(counts)} block types, {solid} non-air blocks")
    return r, counts, problems


def main():
    bsdir = sys.argv[1] if len(sys.argv) > 1 else None
    lines = []
    for fname, dv, label in FILES:
        path = os.path.join(OUT, fname)
        to_nbt(dv).save(path, gzipped=True)
        r, counts, problems = check(path, dv, bsdir if dv == 5023 else None)
        lines += r
        if problems:
            lines += ["  !! " + p for p in problems]
        elif bsdir and dv == 5023:
            lines.append("  every block name and property checked against the 26.3 client's blockstate files: OK")
    lines.append("")
    lines.append("Blocks (non-air):")
    for k, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        if k != "minecraft:air":
            lines.append(f"  {n:4d}  {k}")
    lines.append(f"  air: {counts['minecraft:air']}")
    print("\n".join(lines))
    json.dump({f"{x},{y},{z}": [n, p] for (x, y, z), (n, p) in W.items() if n != "minecraft:air"},
              open(os.path.join(HERE, "blocks.json"), "w"), indent=0, sort_keys=True)
    return lines


if __name__ == "__main__":
    main()
