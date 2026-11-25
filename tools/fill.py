#!/usr/bin/python3
"""Post-process the generated PCB: add the NEPAMesh logo (back silkscreen, plus two small front ones) and fill copper zones.
Needs KiCad's pcbnew bindings; run with /usr/bin/python3."""
import json, os, sys
sys.path.insert(0, "/usr/lib/python3/dist-packages")
import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_CX, LOGO_CY, LOGO_H = 100.0, 127.0, 17.5      # board coords (mm), logo height (mm)
path = sys.argv[1]
b = pcbnew.LoadBoard(path)

mm = pcbnew.FromMM

def add_logo(json_name, cx, cy, h, layer, mirror):
    """Add the traced logo as filled polygons.  mirror=True for the back side."""
    lj = os.path.join(ROOT, "lib", json_name)
    if not os.path.exists(lj):
        return
    d = json.load(open(lj))
    sx = -1 if mirror else 1
    P = lambda p: (mm(cx + sx * p[0] * h), mm(cy + p[1] * h))
    n = 0
    for poly in d["polys"]:
        sps = pcbnew.SHAPE_POLY_SET()
        o = sps.NewOutline()
        for p in poly["outline"]:
            sps.Append(*P(p), o, -1)
        for hl in poly["holes"]:
            hi = sps.NewHole(o)
            for p in hl:
                sps.Append(*P(p), o, hi)
        try:
            sps.Fracture()
        except TypeError:
            sps.Fracture(pcbnew.SHAPE_POLY_SET.PM_FAST)
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_POLY)
        s.SetPolyShape(sps)
        s.SetFilled(True)
        s.SetWidth(0)
        s.SetLayer(layer)
        b.Add(s)
        n += 1
    print("logo:", n, "polygons on", b.GetLayerName(layer))

add_logo("nepamesh_logo.json", LOGO_CX, LOGO_CY, LOGO_H, pcbnew.B_SilkS, True)
# Front: two small logos in the free pour strips beside the supermini header rows (simplified trace, thin strokes dropped).
add_logo("nepamesh_logo_front.json", 87.4, 107.5, 5.8, pcbnew.F_SilkS, False)   # left strip, between H1 and H3
add_logo("nepamesh_logo_front.json", 112.5, 119.5, 5.8, pcbnew.F_SilkS, False)  # right strip, between H2 and H4

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(path, b)
print("filled", len(list(b.Zones())), "zone(s)")
