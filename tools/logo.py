#!/usr/bin/env python3
"""Trace assets/nepamesh_logo.png (alpha channel) into polygons -> lib/nepamesh_logo.json.
Needs OpenCV (conda python). Output coords are in units of logo height, origin at logo centre, y down."""
import json, os, sys
import cv2
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
im = cv2.imread(os.path.join(ROOT, "assets", "nepamesh_logo.png"), cv2.IMREAD_UNCHANGED)
a = im[:, :, 3]
K = 6
a = cv2.resize(a, None, fx=K, fy=K, interpolation=cv2.INTER_CUBIC)
_, bw = cv2.threshold(a, 110, 255, cv2.THRESH_BINARY)
ys, xs = bw.nonzero()
x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
H = float(y1 - y0); cx = (x0 + x1) / 2; cy = (y0 + y1) / 2
cs, hier = cv2.findContours(bw, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
def pts(c):
    c = cv2.approxPolyDP(c, 0.6, True)
    return [[round((p[0][0] - cx) / H, 5), round((p[0][1] - cy) / H, 5)] for p in c]
polys = []
for i, c in enumerate(cs):
    if hier[0][i][3] != -1 or len(c) < 3 or cv2.contourArea(c) < 4:
        continue
    holes = []
    j = hier[0][i][2]
    while j != -1:
        if len(cs[j]) >= 3 and cv2.contourArea(cs[j]) >= 4:
            holes.append(pts(cs[j]))
        j = hier[0][j][0]
    polys.append({"outline": pts(c), "holes": holes})
json.dump({"aspect": (x1 - x0) / H, "polys": polys}, open(os.path.join(ROOT, "lib", "nepamesh_logo.json"), "w"))
print(len(polys), "polygons, aspect", round((x1 - x0) / H, 3))
