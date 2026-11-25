#!/usr/bin/env python3
"""Case for NEPAMesh LoraSupermini: PCB bay + 18650 bay, base + lid.  build123d.

Run:  ~/.venvs/cad/bin/python case/build_case.py       (writes case/out/*.stl, *.step, report.json)

Frame: x east, y north (USB end = +y), z up from the underside of the base.
PCB coordinates come from the KiCad board: kicad (kx, ky) -> case x = PCB_CX + kx, y = PCB_CY + (8.75 - ky).
The 18650 bay is my own design from standard 18650 dimensions (not derived from any third-party model).
All dimensions in mm.
"""
import json, os, math
from build123d import *

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ parameters
T = 2.4                 # outer wall
FLOOR = 3.0
H_INT = 19.5            # interior height above floor
LID_T = 2.0
LIP_H, LIP_T, LIP_GAP = 2.0, 1.2, 0.3
PCB_W, PCB_L, PCB_T = 32.0, 55.5, 1.6
PCB_CLR = 0.5
STANDOFF_H, STANDOFF_D = 4.0, 6.4
INSERT_D, INSERT_DEPTH = 3.2, 4.0         # M2 heat-set insert pocket
SCREW_CLR_D = 2.4                          # M2 clearance
DIV = 2.4
BAY_W = 22.0
CELL_D, CELL_USABLE = 18.6, 76.0           # usable length between contact faces: cell (<=70 protected) + spring/plate
BUTT = 3.5                                 # contact buttress thickness
CORRIDOR = 2.4                             # wire corridor beside the cell
CRADLE_DEPTH = 1.0
SMA_D, SMA_FLAT = 6.5, 5.9                 # D-flat bulkhead hole
USB_W, USB_H = 14.0, 8.5                   # through opening (plug overmold must pass)

ZONE_W = PCB_W + 2 * PCB_CLR
W_INT = ZONE_W + DIV + BAY_W
L_INT = CELL_USABLE + 2 * BUTT
W_OUT, L_OUT = W_INT + 2 * T, L_INT + 2 * T
X0 = -W_INT / 2                             # interior west face
PCB_X0 = X0 + PCB_CLR                       # PCB west edge
PCB_CX = PCB_X0 + PCB_W / 2
Y_N = L_INT / 2                             # interior north face
PCB_Y_N = Y_N - PCB_CLR
DIV_X0 = X0 + ZONE_W
BAY_X0 = DIV_X0 + DIV
BAY_X1 = W_INT / 2
CELL_CX = BAY_X0 + CORRIDOR + CELL_D / 2
Z_FLOOR = FLOOR
Z_BASE_TOP = FLOOR + H_INT
Z_PCB_BOT = FLOOR + STANDOFF_H
Z0 = Z_PCB_BOT + PCB_T                     # carrier top surface
CELL_ZC = FLOOR - CRADLE_DEPTH + CELL_D / 2


def kx(kx_, ky_):
    """KiCad board coords (mm, relative to supermini centre) -> case xy"""
    return (PCB_CX + kx_, PCB_CY + (8.75 - ky_))


# PCB outline in kicad coords is x[-16,16], y[-19,36.5]  -> PCB_CY chosen so ky=-19 maps to PCB_Y_N
PCB_CY = PCB_Y_N - (8.75 + 19.0)

HOLES = {n: kx(*p) for n, p in {"H1": (-13.0, -8.0), "H2": (13.5, 6.0), "H3": (-13.0, 33.0), "H4": (13.5, 33.0)}.items()}
BOSSES = [(BAY_X1 - 2.0, Y_N - 2.0), (BAY_X1 - 2.0, -(Y_N - 2.0)),
          (X0 + 2.0, -(Y_N - 2.0)), (DIV_X0 - 1.8, -(Y_N - 2.0))]   # overlap the walls (no tangent faces)
BOSS_D = 6.2
USB_X, USB_Z = kx(0, 0)[0], Z0 + 5.3
SMA_X, SMA_Z = PCB_CX, Z0 + 6.4
J1_XY = kx(13.0, -6.5)

# ------------------------------------------------------------------ helpers
def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def cyl_z(x, y, z0, z1, d):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(d / 2, z1 - z0)


def rrect_xz(w, h, r, x, y, z, depth):
    """rounded-rect hole through a wall facing +/-y, centred (x,y,z), total thickness depth"""
    s = extrude(RectangleRounded(w, h, r), amount=depth / 2, both=True)
    return Pos(x, y, z) * Rot(90, 0, 0) * s


# ------------------------------------------------------------------ base
outer = extrude(RectangleRounded(W_OUT, L_OUT, 3.0), amount=Z_BASE_TOP)
inner = Pos(0, 0, FLOOR) * extrude(RectangleRounded(W_INT, L_INT, 0.8), amount=H_INT + 1)
base = outer - inner

# PCB standoffs (M2 insert pockets)
for n, (hx, hy) in HOLES.items():
    base += cyl_z(hx, hy, FLOOR - 0.2, Z_PCB_BOT, STANDOFF_D)
for n, (hx, hy) in HOLES.items():
    base -= cyl_z(hx, hy, Z_PCB_BOT - INSERT_DEPTH, Z_PCB_BOT + 0.01, INSERT_D)

# divider (top stays below the lid lip so nothing interferes)
div = box(DIV_X0, DIV_X0 + DIV, -Y_N + 0.2, Y_N - 0.2, FLOOR - 0.2, Z_BASE_TOP - LIP_H - 0.6)
# wire window through the divider at J1
win_y = J1_XY[1]
div -= box(DIV_X0 - 0.5, DIV_X0 + DIV + 0.5, win_y - 4.0, win_y + 4.0, Z0 + 1.0, Z0 + 6.4)
base += div

# contact buttresses (north +, south -), with plate recess and wire groove to the corridor
for sgn in (+1, -1):
    y_in = sgn * (Y_N - BUTT)
    y_out = sgn * (Y_N + 0.2)
    b = box(BAY_X0, BAY_X1, min(y_in, y_out), max(y_in, y_out), FLOOR - 0.2, FLOOR + 14.0)
    # plate recess in inner face: 10.8 wide x 1.2 deep x 11 tall, centred on the cell axis
    rec = box(CELL_CX - 5.0, CELL_CX + 5.0, *sorted((y_in + (-sgn) * 0.01, y_in + sgn * 1.2)), FLOOR - 0.5, FLOOR + 11.0)
    b -= rec
    # wire groove (2.6 wide) from the recess to the corridor at floor level, cut into the inner face
    grv = box(BAY_X0, CELL_CX - 5.0, *sorted((y_in - sgn * 0.01, y_in + sgn * 1.6)), FLOOR, FLOOR + 2.6)
    b -= grv
    base += b

# 18650 cradle trough (cylinder along y)
cradle = Pos(CELL_CX, 0, CELL_ZC) * Rot(90, 0, 0) * Cylinder(CELL_D / 2 + 0.3, CELL_USABLE)
base -= cradle

# lid screw bosses
for (bx, by) in BOSSES:
    base += cyl_z(bx, by, FLOOR - 0.2, Z_BASE_TOP, BOSS_D)
    base -= cyl_z(bx, by, Z_BASE_TOP - INSERT_DEPTH - 1.0, Z_BASE_TOP + 0.01, INSERT_D)

# USB opening (north wall) + shallow plug recess outside
base -= rrect_xz(USB_W, USB_H, 1.5, USB_X, Y_N + T / 2, USB_Z, T + 2.0)
base -= rrect_xz(USB_W + 3.0, USB_H + 3.0, 2.2, USB_X, Y_N + T, USB_Z, 2.0)

# SMA bulkhead hole (south wall), D-flat: round hole intersected with a box = flats on the x sides
y_w = -(Y_N + T / 2)
sma_c = Pos(SMA_X, y_w, SMA_Z) * Rot(90, 0, 0) * Cylinder(SMA_D / 2, T + 2.0)
base -= sma_c & (Pos(SMA_X, y_w, SMA_Z) * Box(SMA_FLAT, T + 2.0, SMA_D + 2))

# ------------------------------------------------------------------ lid (built in assembly position, flipped for export)
lid_plate = Pos(0, 0, Z_BASE_TOP) * extrude(RectangleRounded(W_OUT, L_OUT, 3.0), amount=LID_T)
lip_out = Pos(0, 0, Z_BASE_TOP - LIP_H) * extrude(RectangleRounded(W_INT - 2 * LIP_GAP, L_INT - 2 * LIP_GAP, 0.8), amount=LIP_H + 0.01)
lip_in = Pos(0, 0, Z_BASE_TOP - LIP_H - 0.1) * extrude(
    RectangleRounded(W_INT - 2 * (LIP_GAP + LIP_T), L_INT - 2 * (LIP_GAP + LIP_T), 0.5), amount=LIP_H + 0.2)
lid_asm = lid_plate + (lip_out - lip_in)
for (bx, by) in BOSSES:                       # lip notches around the bosses, screw holes, countersinks
    lid_asm -= cyl_z(bx, by, Z_BASE_TOP - LIP_H - 0.1, Z_BASE_TOP, BOSS_D + 1.6)
    lid_asm -= cyl_z(bx, by, Z_BASE_TOP - 0.1, Z_BASE_TOP + LID_T + 0.1, SCREW_CLR_D)
    lid_asm -= Pos(bx, by, Z_BASE_TOP + LID_T) * Cone(bottom_radius=SCREW_CLR_D / 2, top_radius=2.3, height=1.1,
                                                        align=(Align.CENTER, Align.CENTER, Align.MAX))

# ------------------------------------------------------------------ NEPAMesh logo, engraved in the lid's outer face
LOGO_H, LOGO_DEPTH, LOGO_CX, LOGO_CY = 40.0, 0.5, 0.0, 0.0
def _logo_cut():
    d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib", "nepamesh_logo.json")))
    z0 = Z_BASE_TOP + LID_T - LOGO_DEPTH
    cut = None
    for q in d["polys"]:
        pts = [(LOGO_CX + x * LOGO_H, LOGO_CY + y * LOGO_H) for x, y in q["outline"]]
        with BuildSketch() as sk:
            with BuildLine():
                Polyline(*pts, close=True)
            make_face()
            for h in q["holes"]:
                with BuildLine():
                    Polyline(*[(LOGO_CX + x * LOGO_H, LOGO_CY + y * LOGO_H) for x, y in h], close=True)
                make_face(mode=Mode.SUBTRACT)
        if sk.sketch.area < 0.05:
            continue
        sol = Pos(0, 0, z0) * extrude(sk.sketch, amount=LOGO_DEPTH + 0.5)
        cut = sol if cut is None else cut + sol
    return cut
lid_asm -= _logo_cut()
lid = Pos(0, 0, Z_BASE_TOP + LID_T) * Rot(180, 0, 0) * lid_asm      # print orientation: plate on the bed, lip up

# ------------------------------------------------------------------ clearance ghosts (not exported)
ghosts = {}
ghosts["cell"] = Pos(CELL_CX, 0, CELL_ZC) * Rot(90, 0, 0) * Cylinder(CELL_D / 2, 70.0)
x_sm, y_sm = kx(0, 0)
ghosts["supermini+header"] = box(x_sm - 9.2, x_sm + 9.2, y_sm - 16.8, y_sm + 16.8, Z0, Z0 + 7.0)
ghosts["pcb"] = box(PCB_X0, PCB_X0 + PCB_W, PCB_Y_N - PCB_L, PCB_Y_N, Z_PCB_BOT, Z0)
xm, ym = kx(0, 26.0)
ghosts["wio module"] = box(xm - 5.8, xm + 5.8, ym - 5.5, ym + 5.5, Z0, Z0 + 3.0)
ghosts["jst + plug"] = box(J1_XY[0] - 3.2, J1_XY[0] + 3.2, J1_XY[1] - 4.5, J1_XY[1] + 4.5, Z0, Z0 + 9.5)
ghosts["usb plug"] = box(USB_X - 6.0, USB_X + 6.0, y_sm + 16.0, Y_N + T + 12.0, USB_Z - 3.2, USB_Z + 3.2)
ghosts["sma nut"] = Pos(SMA_X, -(Y_N - 3.0), SMA_Z) * Rot(90, 0, 0) * Cylinder(4.7, 6.0)

# lid placed in assembled position for interference check

report = {"outer_mm": [round(W_OUT, 2), round(L_OUT, 2), round(Z_BASE_TOP + LID_T, 2)],
          "interior_mm": [round(W_INT, 2), round(L_INT, 2), H_INT],
          "pcb_cx_cy": [round(PCB_CX, 2), round(PCB_CY, 2)], "z0_carrier_top": round(Z0, 2),
          "standoffs": {k: [round(v[0], 2), round(v[1], 2)] for k, v in HOLES.items()},
          "bosses": [[round(a, 2), round(b, 2)] for a, b in BOSSES],
          "usb_xz": [round(USB_X, 2), round(USB_Z, 2)], "sma_xz": [round(SMA_X, 2), round(SMA_Z, 2)],
          "cell_axis_xz": [round(CELL_CX, 2), round(CELL_ZC, 2)], "j1_xy": [round(J1_XY[0], 2), round(J1_XY[1], 2)]}

# interference: ghost volume that overlaps the printed parts (must be ~0, except the cell/trough and the plug/opening)
chk = {}
for n, g in ghosts.items():
    ov = (base & g).volume
    chk[n] = round(ov, 3)
report["ghost_overlap_mm3_with_base"] = chk
report["lid_vs_base_overlap_mm3"] = round((base & lid_asm).volume, 3)

# ------------------------------------------------------------------ export
export_stl(base, os.path.join(OUT, "case_base.stl"))
export_stl(lid, os.path.join(OUT, "case_lid.stl"))
export_step(base, os.path.join(OUT, "case_base.step"))
export_step(lid, os.path.join(OUT, "case_lid.step"))
json.dump(report, open(os.path.join(OUT, "report.json"), "w"), indent=2)
print(json.dumps(report, indent=2))

if os.environ.get("DEBUG_OVERLAP"):
    ov = base & lid_asm
    for s in ov.solids():
        bb = s.bounding_box()
        print("OVERLAP", round(s.volume, 3), [round(v, 2) for v in (bb.min.X, bb.min.Y, bb.min.Z)], [round(v, 2) for v in (bb.max.X, bb.max.Y, bb.max.Z)])
