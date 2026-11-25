#!/usr/bin/env python3
"""Assemble a viewable 3D model of the populated board: KiCad's board export plus simple
component bodies (supermini on its header spacers, Wio-SX1262, JST, fuse, MOSFET, caps).
Needs build123d, trimesh, numpy and kicad-cli: python3 tools/build_3d.py ; view with `f3d 3d/nepamesh_lorasupermini_assembled.glb`.
Component bodies are approximate visual stand-ins, not manufacturer models."""
import os, subprocess
import numpy as np
import trimesh
from build123d import Box, Cylinder, Pos, Rot, Align, SlotOverall, extrude, Plane

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, "nepamesh_lorasupermini.kicad_pcb")
OUT_DIR = os.path.join(ROOT, "3d")
os.makedirs(OUT_DIR, exist_ok=True)
BARE = os.path.join(OUT_DIR, "nepamesh_lorasupermini.glb")
subprocess.run(["kicad-cli", "pcb", "export", "glb", PCB, "--include-tracks", "--include-pads", "--include-zones",
                "--include-silkscreen", "--include-soldermask", "-o", BARE], check=True, capture_output=True)

scene = trimesh.load(BARE)
TOP = 1.6                                   # board top surface, mm
U1 = (100.0, 100.0); U2 = (100.0, 126.0)    # footprint origins, KiCad coords (mm)
ROW, PITCH = 15.24, 2.54

COL = dict(black=(30, 30, 34), pcb=(40, 44, 54), gold=(225, 185, 60), silver=(205, 208, 214), cream=(236, 228, 205),
           white=(225, 225, 225), tan=(170, 130, 80), grey=(120, 120, 125), green=(30, 120, 80))
n = 0

def add(solid, color, name, gloss=0.4, metal=0.0):
    metal = 0.0   # f3d has no environment map by default, so metallic surfaces render black
    """solid is a build123d shape in KiCad mm coords (x, y as on the board, z up).  glb axes: x, z-up -> y, y -> z, metres."""
    global n
    verts, tris = solid.tessellate(0.02)
    v = np.array([[p.X, p.Y, p.Z] for p in verts], dtype=float)
    v = np.column_stack([v[:, 0], v[:, 2], v[:, 1]]) / 1000.0
    m = trimesh.Trimesh(vertices=v, faces=np.array(tris), process=False)
    m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
        baseColorFactor=list(COL[color]) + [255], metallicFactor=metal, roughnessFactor=1 - gloss))
    scene.add_geometry(m, geom_name=f"{name}_{n}"); n += 1

def box(cx, cy, z0, w, d, h, color, name, **kw):
    add(Pos(cx, cy, z0 + h / 2) * Box(w, d, h), color, name, **kw)

# ---- supermini on 2.5 mm header spacers (component side up, USB toward -y)
SP_H, SM_T = 2.5, 1.2
z_sm = TOP + SP_H
for sx in (-ROW / 2, ROW / 2):
    box(U1[0] + sx, U1[1], TOP, 2.54, 13 * PITCH, SP_H, "black", "header_spacer")
    for i in range(13):
        y = U1[1] - 6 * PITCH + i * PITCH
        add(Pos(U1[0] + sx, y, TOP + (SP_H + SM_T + 0.9 - 0) / 2 + 0.0) * Box(0.64, 0.64, SP_H + SM_T + 0.9), "gold", "pin", gloss=0.8, metal=1.0)
box(U1[0], U1[1], z_sm, 18.0, 33.0, SM_T, "pcb", "supermini_pcb", gloss=0.6)
# USB-C receptacle overhanging the north edge
shell = Pos(U1[0], U1[1] - 14.15, z_sm + SM_T + 1.63) * Rot(90, 0, 0) * extrude(SlotOverall(8.94, 3.26), 7.3 / 2, both=True)
add(shell, "silver", "usb_c", gloss=0.8, metal=1.0)
box(U1[0], U1[1] - 1.0, z_sm + SM_T, 6.0, 6.0, 0.9, "black", "nrf52840")
box(U1[0] - 3.2, U1[1] - 8.6, z_sm + SM_T, 3.2, 2.5, 0.8, "silver", "crystal", metal=1.0)
for dx in (-4.2, 4.2):
    box(U1[0] + dx, U1[1] - 9.5, z_sm + SM_T, 1.6, 2.9, 1.0, "black", "sot23")

# ---- Wio-SX1262 (SMD, shield can) rotated 180 deg; IPEX connector ends up bottom-left
box(U2[0], U2[1], TOP, 11.6, 11.0, 1.0, "green", "wio_pcb")
box(U2[0] - 0.4, U2[1] + 0.2, TOP + 1.0, 9.2, 8.2, 1.95, "silver", "wio_shield", gloss=0.7, metal=0.9)
box(U2[0] - 4.2, U2[1] + 3.6, TOP + 1.0, 2.6, 2.6, 1.2, "gold", "ipex", gloss=0.7, metal=0.8)

# ---- power section
box(113.0, 94.5, TOP, 4.5, 6.0, 6.0, "cream", "jst_ph")            # J1, 2-pin JST-PH
box(113.0, 88.4, TOP, 1.6, 3.2, 0.9, "tan", "polyfuse")           # F1 1206
box(112.06, 83.81, TOP, 1.3, 2.9, 1.0, "black", "pfet_sot23")     # Q1
box(91.4, 120.8, TOP, 3.2, 1.6, 1.6, "tan", "c1_22uF")            # C1
box(91.4, 124.6, TOP, 2.0, 1.25, 1.0, "tan", "c2_100nF")          # C2

out = os.path.join(OUT_DIR, "nepamesh_lorasupermini_assembled.glb")
scene.export(out)
print("wrote", out, "geometries:", len(scene.geometry))
