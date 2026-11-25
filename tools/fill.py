#!/usr/bin/python3
"""Post-process the generated PCB: add the NEPAMesh logo (back silkscreen) and fill copper zones.
Needs KiCad's pcbnew bindings; run with /usr/bin/python3."""
import json, os, sys
sys.path.insert(0, "/usr/lib/python3/dist-packages")
import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_CX, LOGO_CY, LOGO_H = 100.0, 127.0, 17.5      # board coords (mm), logo height (mm)
path = sys.argv[1]
b = pcbnew.LoadBoard(path)

lj = os.path.join(ROOT, "lib", "nepamesh_logo.json")
if os.path.exists(lj):
    d = json.load(open(lj))
    mm = pcbnew.FromMM
    P = lambda p: (mm(LOGO_CX - p[0] * LOGO_H), mm(LOGO_CY + p[1] * LOGO_H))   # x mirrored: back side
    n = 0
    for poly in d["polys"]:
        sps = pcbnew.SHAPE_POLY_SET()
        o = sps.NewOutline()
        for p in poly["outline"]:
            sps.Append(*P(p), o, -1)
        for h in poly["holes"]:
            hi = sps.NewHole(o)
            for p in h:
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
        s.SetLayer(pcbnew.B_SilkS)
        b.Add(s)
        n += 1
    print("logo:", n, "polygons on B.SilkS")

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(path, b)
print("filled", len(list(b.Zones())), "zone(s)")
