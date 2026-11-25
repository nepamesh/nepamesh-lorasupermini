#!/usr/bin/env python3
"""Generate the NEPAMesh LoraSupermini KiCad 9 project (libs, schematic, PCB).

Run:  python3 tools/build.py        (from the project root)
Everything under lib/ and the *.kicad_* files is regenerated; edit this script, not the outputs.
"""
import os, re, uuid, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "nepamesh_lorasupermini"
SYM_DIR = "/usr/share/kicad/symbols"
FP_DIR = "/usr/share/kicad/footprints"
NS = uuid.UUID("6f1c2a52-0000-4000-8000-00000000c0de")


def U(tag):
    return str(uuid.uuid5(NS, tag))


def fmt(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ----------------------------------------------------------------------------
# s-expression helpers
# ----------------------------------------------------------------------------
def block_end(t, i):
    """index just past the paren block starting at t[i]=='('"""
    d = 0
    q = False
    j = i
    while j < len(t):
        c = t[j]
        if q:
            if c == "\\":
                j += 1
            elif c == '"':
                q = False
        else:
            if c == '"':
                q = True
            elif c == "(":
                d += 1
            elif c == ")":
                d -= 1
                if d == 0:
                    return j + 1
        j += 1
    raise ValueError("unbalanced")


def extract_symbol(libfile, name):
    t = open(os.path.join(SYM_DIR, libfile)).read()
    m = re.search(r'\n\t\(symbol "%s"\n' % re.escape(name), t)
    assert m, name
    s = m.start() + 1
    return t[s:block_end(t, s)]


def sym_pins(block):
    pins = {}
    for m in re.finditer(
            r'\(pin (\w+) (\w+)\s*\(at ([-\d.]+) ([-\d.]+) (\d+)\)\s*\(length ([-\d.]+)\)(.*?)\(number "([^"]+)"',
            block, re.S):
        pins[m.group(8)] = (float(m.group(3)), float(m.group(4)), int(m.group(5)))
    return pins


# ----------------------------------------------------------------------------
# Custom footprints
# ----------------------------------------------------------------------------
# Supermini (Nice!Nano clone): 2 x 13 through-holes, 2.54 pitch, rows 15.24 apart. USB end at top (-y).
SUPERMINI_LEFT = ["B-", "P0.06", "P0.08", "GND", "GND", "P0.17", "P0.20", "P0.22", "P0.24", "P1.00", "P0.11",
                  "P1.04", "P1.06"]                                         # pads 1..13 top->bottom
SUPERMINI_RIGHT = ["B+", "RAW", "GND", "RST", "VCC", "P0.31", "P0.29", "P0.02", "P1.15", "P1.13", "P1.11",
                   "P0.10", "P0.09"]                                        # top->bottom; pad numbers 26..14
SM_PITCH = 2.54
SM_ROW = 15.24


def sm_pad_xy(n):
    if n <= 13:
        return (-SM_ROW / 2, -6 * SM_PITCH + (n - 1) * SM_PITCH)
    return (SM_ROW / 2, -6 * SM_PITCH + (26 - n) * SM_PITCH)


# Wio-SX1262, datasheet top view, y down.  pad centres 0.3 mm inside the 11.6 x 11.0 body edge.
WIO_W, WIO_H = 11.6, 11.0


def wio_pad_xy(n):
    if n <= 8:
        return (-5.8 + 1.33 + 1.27 * (n - 1), WIO_H / 2)
    x12 = -5.8 + 2.60
    return (x12 + 1.27 * (12 - n), -WIO_H / 2)


def rect_lines(x0, y0, x1, y1, layer, w):
    out = []
    for (a, b, c, d) in [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]:
        out.append(f'(fp_line (start {fmt(a)} {fmt(b)}) (end {fmt(c)} {fmt(d)}) '
                   f'(stroke (width {w}) (type solid)) (layer "{layer}"))')
    return out


def fp_common(name, descr, tags, attr, ref_at, val_at):
    return [
        f'(footprint "{name}"',
        '(version 20241229) (generator "nepamesh_build") (generator_version "1.0")',
        '(layer "F.Cu")',
        f'(descr "{descr}")',
        f'(tags "{tags}")',
        f'(property "Reference" "REF**" (at {ref_at[0]} {ref_at[1]} 0) (layer "F.SilkS") '
        '(effects (font (size 1 1) (thickness 0.15))))',
        f'(property "Value" "{name}" (at {val_at[0]} {val_at[1]} 0) (layer "F.Fab") '
        '(effects (font (size 1 1) (thickness 0.15))))',
        f'(attr {attr})',
    ]


def supermini_fp():
    L = fp_common("Supermini_nRF52840_THT",
                  "nRF52840 supermini / Nice!Nano clone, 2x13 through-hole, 2.54mm pitch, 15.24mm row spacing",
                  "nrf52840 supermini nicenano", "through_hole", (0, -11.5), (0, 19))
    L += rect_lines(-9, -16.5, 9, 16.5, "F.SilkS", 0.15)
    L += rect_lines(-9.0, -16.6, 9.0, 16.6, "F.CrtYd", 0.05)
    L.append('(fp_text user "USB" (at 0 -14.2 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))')
    for n in range(1, 27):
        x, y = sm_pad_xy(n)
        shape = "rect" if n == 1 else "circle"
        L.append(f'(pad "{n}" thru_hole {shape} (at {fmt(x)} {fmt(y)}) (size 1.7 1.7) (drill 1.0) '
                 '(layers "*.Cu" "*.Mask"))')
    L.append(")")
    return "\n".join(L)


def wio_fp():
    L = fp_common("Wio-SX1262_Seeed",
                  "Seeed Wio-SX1262 (114993390) 12-pin SMD module 11.6x11mm. Datasheet top view, pin 1 bottom-left.",
                  "lora sx1262 seeed wio", "smd", (-7.6, 0), (0, 7.5))
    for sx in (-5.8, 5.8):
        L.append(f'(fp_line (start {sx} -5.5) (end {sx} 5.5) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))')
    L += rect_lines(-5.8, -5.5, 5.8, 5.5, "F.Fab", 0.1)
    L += rect_lines(-6.3, -6.85, 6.3, 6.85, "F.CrtYd", 0.05)
    L += rect_lines(1.4, -5.4, 5.7, -1.4, "F.Fab", 0.1)
    L.append('(fp_text user "IPEX" (at 3.55 -3.4 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    L.append('(fp_circle (center -6.5 5.5) (end -6.3 5.5) (stroke (width 0.12) (type solid)) (fill none) (layer "F.SilkS"))')
    for n in range(1, 13):
        x, y = wio_pad_xy(n)
        L.append(f'(pad "{n}" smd rect (at {fmt(x)} {fmt(y)}) (size 0.6 2.2) (layers "F.Cu" "F.Mask" "F.Paste"))')
    L.append(")")
    return "\n".join(L)


# ----------------------------------------------------------------------------
# Custom symbols
# ----------------------------------------------------------------------------
def eff(sz=1.27, hide=False):
    return f'(effects (font (size {sz} {sz})){" (hide yes)" if hide else ""})'


def sym_prop(k, v, x, y, hide=False):
    return f'(property "{k}" "{v}" (at {x} {y} 0) {eff(hide=hide)})'


def make_sym(name, desc, fp, body, left, right, ytop):
    """left/right: list of (number, label) top->bottom. body=(halfwidth, halfheight)"""
    hw, hh = body
    out = [f'(symbol "{name}" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)',
           sym_prop("Reference", "U", 0, hh + 2.54),
           sym_prop("Value", name, 0, -hh - 2.54),
           sym_prop("Footprint", fp, 0, 0, True),
           sym_prop("Datasheet", "~", 0, 0, True),
           sym_prop("Description", desc, 0, 0, True),
           f'(symbol "{name}_0_1" (rectangle (start {fmt(-hw)} {fmt(hh)}) (end {fmt(hw)} {fmt(-hh)}) '
           '(stroke (width 0.254) (type default)) (fill (type background))))',
           f'(symbol "{name}_1_1"']
    for i, (num, lab) in enumerate(left):
        y = ytop - 2.54 * i
        out.append(f'(pin passive line (at {fmt(-hw - 2.54)} {fmt(y)} 0) (length 2.54) '
                   f'(name "{lab}" {eff()}) (number "{num}" {eff()}))')
    for i, (num, lab) in enumerate(right):
        y = ytop - 2.54 * i
        out.append(f'(pin passive line (at {fmt(hw + 2.54)} {fmt(y)} 180) (length 2.54) '
                   f'(name "{lab}" {eff()}) (number "{num}" {eff()}))')
    out.append("))")
    return "\n".join(out)


SM_LEFT_PINS = [(str(i + 1), n) for i, n in enumerate(SUPERMINI_LEFT)]
SM_RIGHT_PINS = [(str(26 - i), n) for i, n in enumerate(SUPERMINI_RIGHT)]
SYM_SM = make_sym("Supermini_nRF52840", "nRF52840 supermini (Nice!Nano clone), 2x13 header",
                  "nepamesh:Supermini_nRF52840_THT", (12.7, 17.78), SM_LEFT_PINS, SM_RIGHT_PINS, 15.24)
WIO_LEFT = [("1", "RF_SW"), ("2", "MISO"), ("3", "MOSI"), ("4", "SCK"), ("5", "NRST"), ("6", "NSS"), ("7", "GND"),
            ("8", "VCC")]
WIO_RIGHT = [("12", "DIO1"), ("11", "BUSY"), ("10", "GND"), ("9", "ANT")]
SYM_WIO = make_sym("Wio-SX1262", "Seeed Wio-SX1262 LoRa module 114993390",
                   "nepamesh:Wio-SX1262_Seeed", (10.16, 10.16), WIO_LEFT, WIO_RIGHT, 8.89)

# ----------------------------------------------------------------------------
# Net / part data (single source of truth for schematic and PCB)
# ----------------------------------------------------------------------------
NETS = ["GND", "+3V3", "BAT_IN", "BAT_F", "BPLUS", "BNEG", "SCK", "MOSI", "MISO", "RF_SW", "NRST", "NSS", "BUSY",
        "DIO1"]
NETID = {n: i + 1 for i, n in enumerate(NETS)}

U1_NETS = {1: "BNEG", 4: "GND", 5: "GND", 12: "NRST", 13: "NSS", 16: "RF_SW", 17: "MISO", 18: "MOSI", 19: "SCK",
           20: "DIO1", 21: "BUSY", 22: "+3V3", 24: "GND", 26: "BPLUS"}
U2_NETS = {1: "RF_SW", 2: "MISO", 3: "MOSI", 4: "SCK", 5: "NRST", 6: "NSS", 7: "GND", 8: "+3V3", 10: "GND",
           11: "BUSY", 12: "DIO1"}
PARTS = {  # ref: (lib symbol, value, footprint, {pin: net})
    "J1": ("Connector_Generic:Conn_01x02", "Battery JST-PH (1=+)", "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical",
           {"1": "BAT_IN", "2": "GND"}),
    "F1": ("Device:Polyfuse", "PTC 1206 ~0.75A hold", "Fuse:Fuse_1206_3216Metric", {"1": "BAT_IN", "2": "BAT_F"}),
    "Q1": ("Transistor_FET:Q_PMOS_GSD", "AO3401A", "Package_TO_SOT_SMD:SOT-23", {"1": "GND", "2": "BPLUS", "3": "BAT_F"}),
    "JP1": ("Jumper:SolderJumper_2_Bridged", "B- to GND (bridged)",
            "Jumper:SolderJumper-2_P1.3mm_Bridged_Pad1.0x1.5mm", {"1": "GND", "2": "BNEG"}),
    "C1": ("Device:C", "22uF 6.3V X5R", "Capacitor_SMD:C_0805_2012Metric", {"1": "+3V3", "2": "GND"}),
    "C2": ("Device:C", "100nF", "Capacitor_SMD:C_0603_1608Metric", {"1": "+3V3", "2": "GND"}),
}

# ----------------------------------------------------------------------------
# Schematic
# ----------------------------------------------------------------------------
ROOT_UUID = U("root-sheet")


def build_sch():
    libsyms = {}
    pins = {}
    for ls, lf, nm in [("Device:C", "Device.kicad_sym", "C"), ("Device:Polyfuse", "Device.kicad_sym", "Polyfuse"),
                       ("Transistor_FET:Q_PMOS_GSD", "Transistor_FET.kicad_sym", "Q_PMOS_GSD"),
                       ("Connector_Generic:Conn_01x02", "Connector_Generic.kicad_sym", "Conn_01x02"),
                       ("Jumper:SolderJumper_2_Bridged", "Jumper.kicad_sym", "SolderJumper_2_Bridged"),
                       ("Mechanical:MountingHole", "Mechanical.kicad_sym", "MountingHole")]:
        b = extract_symbol(lf, nm)
        pins[ls] = sym_pins(b)
        libsyms[ls] = b.replace(f'(symbol "{nm}"', f'(symbol "{ls}"', 1)
    pins["nepamesh:Supermini_nRF52840"] = {n: (-12.7 - 2.54, 15.24 - 2.54 * i, 0) for i, (n, _) in enumerate(SM_LEFT_PINS)}
    pins["nepamesh:Supermini_nRF52840"].update(
        {n: (12.7 + 2.54, 15.24 - 2.54 * i, 180) for i, (n, _) in enumerate(SM_RIGHT_PINS)})
    pins["nepamesh:Wio-SX1262"] = {n: (-10.16 - 2.54, 8.89 - 2.54 * i, 0) for i, (n, _) in enumerate(WIO_LEFT)}
    pins["nepamesh:Wio-SX1262"].update({n: (10.16 + 2.54, 8.89 - 2.54 * i, 180) for i, (n, _) in enumerate(WIO_RIGHT)})
    libsyms["nepamesh:Supermini_nRF52840"] = SYM_SM.replace('(symbol "Supermini_nRF52840"',
                                                              '(symbol "nepamesh:Supermini_nRF52840"', 1)
    libsyms["nepamesh:Wio-SX1262"] = SYM_WIO.replace('(symbol "Wio-SX1262"', '(symbol "nepamesh:Wio-SX1262"', 1)

    body = []
    labels = []
    ncs = []

    def place(ref, lib, val, fp, x, y, nets, nc_pins=(), dy=5.08):
        pp = pins[lib]
        body.append(
            f'(symbol (lib_id "{lib}") (at {fmt(x)} {fmt(y)} 0) (unit 1) (exclude_from_sim no) (in_bom yes) '
            f'(on_board yes) (dnp no) (uuid "{U("sym-" + ref)}")\n'
            f'  (property "Reference" "{ref}" (at {fmt(x + 5)} {fmt(y - dy)} 0) (effects (font (size 1.27 1.27)) (justify left)))\n'
            f'  (property "Value" "{val}" (at {fmt(x + 5)} {fmt(y + dy)} 0) (effects (font (size 1.27 1.27)) (justify left)))\n'
            f'  (property "Footprint" "{fp}" (at {fmt(x)} {fmt(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            f'  (property "Datasheet" "~" (at {fmt(x)} {fmt(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            + "".join(f'  (pin "{p}" (uuid "{U("pin-" + ref + p)}"))\n' for p in pp)
            + f'  (instances (project "{NAME}" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1)))))')
        for p, net in nets.items():
            px, py, pa = pp[str(p)]
            sx, sy = x + px, y - py
            # label direction: away from the symbol body
            ang = {0: 180, 180: 0, 90: 270, 270: 90}[pa]
            just = "right" if ang in (180, 270) else "left"
            labels.append(f'(label "{net}" (at {fmt(sx)} {fmt(sy)} {ang}) (effects (font (size 1.27 1.27)) '
                          f'(justify {just} bottom)) (uuid "{U("lbl-" + ref + str(p))}"))')
        for p in nc_pins:
            px, py, pa = pp[str(p)]
            ncs.append(f'(no_connect (at {fmt(x + px)} {fmt(y - py)}) (uuid "{U("nc-" + ref + str(p))}"))')

    u1_used = {str(k): v for k, v in U1_NETS.items()}
    u1_nc = [n for n in pins["nepamesh:Supermini_nRF52840"] if n not in u1_used]
    place("U1", "nepamesh:Supermini_nRF52840", "nRF52840 supermini", "nepamesh:Supermini_nRF52840_THT",
          110.49, 105.41, u1_used, u1_nc, dy=21.0)
    u2_used = {str(k): v for k, v in U2_NETS.items()}
    place("U2", "nepamesh:Wio-SX1262", "Wio-SX1262 (114993390)", "nepamesh:Wio-SX1262_Seeed", 213.36, 105.41,
          u2_used, ["9"], dy=15.0)
    pos = {"J1": (30.48, 50.8), "F1": (66.04, 45.72), "Q1": (101.6, 50.8), "JP1": (30.48, 81.28),
           "C1": (228.6, 152.4), "C2": (248.92, 152.4)}
    for ref, (lib, val, fp, nets) in PARTS.items():
        place(ref, lib, val, fp, *pos[ref], nets)

    for i, hx in enumerate([260.0, 270.0, 280.0, 290.0]):
        place(f"H{i + 1}", "Mechanical:MountingHole", "M2", "MountingHole:MountingHole_2.2mm_M2", hx, 30.0, {})

    notes = [
        ("NEPAMesh LoraSupermini v0.1  -  nRF52840 supermini + Seeed Wio-SX1262 carrier, 18650 off-board", 25.4, 20.32, 2.0),
        ("J1: JST-PH battery, pin 1 = +. Check your lead's polarity - many 18650 holders are wired backwards.", 25.4, 30.48, 1.27),
        ("Q1 blocks reversed battery. JP1 ties B- to GND; cut it if a meter shows B- is not GND on your clone.", 25.4, 33.02, 1.27),
        ("RF_SW (RXEN): drive HIGH for RX, LOW otherwise; TX is switched by SX1262 DIO2 inside the module. DIO3 = TCXO supply.", 120, 185, 1.27),
        ("Wio pin 9 (ANT) is only populated on the -N SMT-pin variant; unused with the IPEX 114993390.", 120, 190, 1.27),
    ]
    txt = "\n".join(
        f'(text "{t}" (exclude_from_sim no) (at {x} {y} 0) (effects (font (size {s} {s})) (justify left bottom)) '
        f'(uuid "{U("txt" + str(i))}"))' for i, (t, x, y, s) in enumerate(notes))
    out = [f'(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0") '
           f'(uuid "{ROOT_UUID}") (paper "A4")',
           "(lib_symbols", *libsyms.values(), ")",
           *body, *labels, *ncs, txt,
           '(sheet_instances (path "/" (page "1")))', ")"]
    return "\n".join(out)


# ----------------------------------------------------------------------------
# PCB
# ----------------------------------------------------------------------------
OX, OY = 100.0, 100.0          # supermini centre on the sheet
XMIN, XMAX, YMIN, YMAX = -16.0, 16.0, -19.0, 36.5


def A(x, y):
    return OX + x, OY + y


def strip_uuids(t):
    return re.sub(r'\s*\(uuid "[^"]*"\)', "", t)


def add_pad_nets_and_rot(t, nets, rot):
    out = []
    i = 0
    for m in re.finditer(r'\(pad "([^"]+)"', t):
        pass
    res = t
    pos = 0
    while True:
        m = re.compile(r'\(pad "([^"]+)"').search(res, pos)
        if not m:
            break
        s = m.start()
        e = block_end(res, s)
        blk = res[s:e]
        num = m.group(1)
        if rot:
            blk = re.sub(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)',
                         lambda mm: f'(at {mm.group(1)} {mm.group(2)} {fmt((float(mm.group(3) or 0) + rot) % 360)})',
                         blk, count=1)
        if num in nets:
            net = nets[num]
            blk = blk[:-1] + f' (net {NETID[net]} "/{net}"))'
        res = res[:s] + blk + res[e:]
        pos = s + len(blk)
    return res


def embed_fp(libref, ref, value, x, y, rot, nets, custom=None, ref_at=None, hide_ref=False):
    lib, name = libref.split(":")
    if custom:
        t = custom
    else:
        t = open(os.path.join(FP_DIR, lib + ".pretty", name + ".kicad_mod")).read()
    t = strip_uuids(t)
    t = re.sub(r'^\(footprint "[^"]*"', f'(footprint "{libref}"', t, count=1)
    ax, ay = A(x, y)
    at = f'(at {fmt(ax)} {fmt(ay)}{(" " + fmt(rot)) if rot else ""})'
    t = t.replace('(layer "F.Cu")', f'(layer "F.Cu") (uuid "{U("fp-" + ref)}") {at}', 1)
    t = re.sub(r'(\(property "Reference" )"[^"]*"', r'\1"%s"' % ref, t, count=1)
    t = re.sub(r'(\(property "Value" )"[^"]*"', r'\1"%s"' % value, t, count=1)
    if ref_at or hide_ref:
        def fix(m):
            at = f'(at {fmt(ref_at[0])} {fmt(ref_at[1])} {fmt(rot)})' if ref_at else m.group(2)
            return m.group(1) + at + (' (hide yes)' if hide_ref else '')
        t = re.sub(r'(\(property "Reference" "[^"]*"\s*)(\(at [^)]*\))', fix, t, count=1)
    t = add_pad_nets_and_rot(t, {str(k): v for k, v in nets.items()}, rot)
    return t


def seg(x1, y1, x2, y2, net, layer, w=0.25):
    a, b = A(x1, y1), A(x2, y2)
    return (f'(segment (start {fmt(a[0])} {fmt(a[1])}) (end {fmt(b[0])} {fmt(b[1])}) (width {w}) '
            f'(layer "{layer}") (net {NETID[net]}) (uuid "{U("seg%s%s%s%s%s" % (x1, y1, x2, y2, layer))}"))')


def via(x, y, net, size=0.8, drill=0.4):
    a = A(x, y)
    return (f'(via (at {fmt(a[0])} {fmt(a[1])}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") '
            f'(net {NETID[net]}) (uuid "{U("via%s%s" % (x, y))}"))')


def path(pts, net, layer, w=0.25):
    return [seg(*pts[i], *pts[i + 1], net, layer, w) for i in range(len(pts) - 1)]


def build_pcb():
    fps = []
    fps.append(embed_fp("nepamesh:Supermini_nRF52840_THT", "U1", "nRF52840 supermini", 0, 0, 0, U1_NETS,
                        custom=supermini_fp()))
    UX, UY = 0.0, 26.0
    fps.append(embed_fp("nepamesh:Wio-SX1262_Seeed", "U2", "Wio-SX1262 (114993390)", UX, UY, 180, U2_NETS, custom=wio_fp()))
    fps.append(embed_fp(PARTS["J1"][2], "J1", PARTS["J1"][1], 13.0, -6.5, 270, {1: "BAT_IN", 2: "GND"}, hide_ref=True))
    fps.append(embed_fp(PARTS["F1"][2], "F1", PARTS["F1"][1], 13.0, -11.6, 90, {1: "BAT_IN", 2: "BAT_F"}))
    fps.append(embed_fp(PARTS["Q1"][2], "Q1", PARTS["Q1"][1], 12.0625, -16.19, 0, {1: "GND", 2: "BPLUS", 3: "BAT_F"}, ref_at=(-2.7, -1.0)))
    fps.append(embed_fp(PARTS["JP1"][2], "JP1", PARTS["JP1"][1], -11.8, -15.24, 0, {1: "GND", 2: "BNEG"}))
    fps.append(embed_fp(PARTS["C1"][2], "C1", PARTS["C1"][1], -8.6, 20.8, 180, {1: "+3V3", 2: "GND"}))
    fps.append(embed_fp(PARTS["C2"][2], "C2", PARTS["C2"][1], -8.6, 24.6, 180, {1: "+3V3", 2: "GND"}))
    for i, (hx, hy) in enumerate([(-13.0, -8), (13.5, 6), (-13.0, 33), (13.5, 33)]):
        fps.append(embed_fp("MountingHole:MountingHole_2.2mm_M2", f"H{i + 1}", "M2", hx, hy, 0, {}))

    T = []     # tracks / vias
    # --- top layer SPI legs (nested L-shapes), pin -> pad
    # right column pins (x=7.62): SCK(002,y=2.54)->pad4 x=.66 ; MOSI(115,5.08)->pad3 1.93 ; MISO(113,7.62)->pad2 3.2 ; RF_SW(111,10.16)->pad1 4.47
    PADY = 20.5
    for net, py, px in [("SCK", 2.54, 0.66), ("MOSI", 5.08, 1.93), ("MISO", 7.62, 3.2), ("RF_SW", 10.16, 4.47)]:
        T += path([(7.62, py), (px, py), (px, PADY)], net, "F.Cu")
    # left column: NRST (P1.04, y=12.7)->pad5 x=-.61 ; NSS (P1.06, y=15.24)->pad6 x=-1.88
    T += path([(-7.62, 12.7), (-0.61, 12.7), (-0.61, PADY)], "NRST", "F.Cu")
    T += path([(-7.62, 15.24), (-1.88, 15.24), (-1.88, PADY)], "NSS", "F.Cu")
    # --- bottom layer: 3V3 rail (hole VCC y=-5.08 -> x=5.0 -> down -> y=17.4 -> pad8 via)
    T += path([(7.62, -5.08), (4.8, -5.08), (4.8, 17.4), (-4.42, 17.4)], "+3V3", "B.Cu", 0.5)
    T.append(via(-4.42, 17.4, "+3V3"))
    T += path([(-4.42, 17.4), (-4.42, PADY)], "+3V3", "F.Cu", 0.5)
    # decoupling caps tie into the VCC pad
    T += path([(-7.65, 20.8), (-4.42, 20.8)], "+3V3", "F.Cu", 0.5)
    T += path([(-7.825, 24.6), (-7.65, 24.6), (-7.65, 20.8)], "+3V3", "F.Cu", 0.4)
    # --- bottom layer: BUSY / DIO1 around the module's right side (inside the header ring)
    FY_BUSY, FY_DIO = 33.0, 34.4
    T += path([(7.62, -2.54), (5.6, -2.54), (5.6, FY_BUSY), (1.93, FY_BUSY)], "BUSY", "B.Cu")
    T.append(via(1.93, FY_BUSY, "BUSY"))
    T += path([(1.93, FY_BUSY), (1.93, 31.5)], "BUSY", "F.Cu")
    T += path([(7.62, 0), (6.15, 0), (6.15, FY_DIO), (3.2, FY_DIO)], "DIO1", "B.Cu")
    T.append(via(3.2, FY_DIO, "DIO1"))
    T += path([(3.2, FY_DIO), (3.2, 31.5)], "DIO1", "F.Cu")
    # --- module GND pads (7 near edge, 10 far edge) via GND vias
    T += path([(-3.15, PADY), (-3.15, 18.6)], "GND", "F.Cu")
    T.append(via(-3.15, 18.6, "GND"))
    T += path([(0.66, 31.5), (0.66, 33.2)], "GND", "F.Cu")
    T.append(via(0.66, 33.2, "GND"))
    # --- power block (top layer)
    T += path([(13.0, -6.5), (13.0, -10.2)], "BAT_IN", "F.Cu", 0.5)
    T += path([(13.0, -13.0), (13.0, -16.19)], "BAT_F", "F.Cu", 0.5)
    T += path([(11.125, -15.24), (7.62, -15.24)], "BPLUS", "F.Cu", 0.5)
    T += path([(-11.15, -15.24), (-7.62, -15.24)], "BNEG", "F.Cu", 0.4)
    # --- GND stitching vias
    for vx, vy in [(-14, 0), (-14, 14), (-14, 27), (14.5, 0), (14.5, 14), (14.5, 26), (-3.5, -9), (3.5, -9),
                   (-3.5, 3), (-6.0, 30), (14.5, 20)]:
        T.append(via(vx, vy, "GND"))

    # outline
    o = []
    pts = [(XMIN, YMIN), (XMAX, YMIN), (XMAX, YMAX), (XMIN, YMAX)]
    for i in range(4):
        a, b = A(*pts[i]), A(*pts[(i + 1) % 4])
        o.append(f'(gr_line (start {fmt(a[0])} {fmt(a[1])}) (end {fmt(b[0])} {fmt(b[1])}) '
                 f'(stroke (width 0.1) (type solid)) (layer "Edge.Cuts") (uuid "{U("edge%d" % i)}"))')
    zpts = " ".join(f'(xy {fmt(A(*p)[0])} {fmt(A(*p)[1])})' for p in pts)
    zone = (f'(zone (net {NETID["GND"]}) (net_name "/GND") (layers "F.Cu" "B.Cu") (uuid "{U("zone")}") '
            f'(hatch edge 0.5) (connect_pads (clearance 0.25)) (min_thickness 0.25) (filled_areas_thickness no) '
            f'(fill yes (thermal_gap 0.3) (thermal_bridge_width 0.4)) (polygon (pts {zpts})))')
    silk = []
    for i, (t, x, y, sz) in enumerate([("J1: 1=+", 12.8, -0.8, 0.8),
                                       ("NEPAMesh LoraSupermini v0.1", 0, 28.5 + 6.5, 0.9)]):
        a = A(x, y)
        silk.append(f'(gr_text "{t}" (at {fmt(a[0])} {fmt(a[1])} 0) (layer "F.SilkS") (uuid "{U("gt%d" % i)}") '
                    f'(effects (font (size {sz} {sz}) (thickness 0.15))))')

    layers = """(layers
 (0 "F.Cu" signal) (2 "B.Cu" signal)
 (9 "F.Adhes" user "F.Adhesive") (11 "B.Adhes" user "B.Adhesive")
 (13 "F.Paste" user) (15 "B.Paste" user)
 (5 "F.SilkS" user "F.Silkscreen") (7 "B.SilkS" user "B.Silkscreen")
 (1 "F.Mask" user) (3 "B.Mask" user)
 (17 "Dwgs.User" user "User.Drawings") (19 "Cmts.User" user "User.Comments")
 (21 "Eco1.User" user "User.Eco1") (23 "Eco2.User" user "User.Eco2")
 (25 "Edge.Cuts" user) (27 "Margin" user)
 (31 "F.CrtYd" user "F.Courtyard") (29 "B.CrtYd" user "B.Courtyard")
 (35 "F.Fab" user "F.Fabrication") (33 "B.Fab" user "B.Fabrication"))"""
    head = ('(kicad_pcb (version 20241229) (generator "pcbnew") (generator_version "9.0")\n'
            '(general (thickness 1.6) (legacy_teardrops no))\n(paper "A4")\n' + layers +
            '\n(setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no)'
            ' (pcbplotparams (layerselection 0x00000000_00000000_55555555_5755f5ff) (plot_on_all_layers_selection 0x00000000_00000000_00000000_00000000)'
            ' (disableapertmacros no) (usegerberextensions no) (usegerberattributes yes) (usegerberadvancedattributes yes)'
            ' (creategerberjobfile yes) (dashed_line_dash_ratio 12) (dashed_line_gap_ratio 3) (svgprecision 4) (plotframeref no)'
            ' (mode 1) (useauxorigin no) (hpglpennumber 1) (hpglpenspeed 20) (hpglpendiameter 15) (pdf_front_fp_property_popups yes)'
            ' (pdf_back_fp_property_popups yes) (pdf_metadata yes) (pdf_single_document no) (dxfpolygonmode yes) (dxfimperialunits yes)'
            ' (dxfusepcbnewfont yes) (psnegative no) (psa4output no) (plot_black_and_white yes) (sketchpadsonfab no)'
            ' (plotpadnumbers no) (hidednponfab no) (sketchdnponfab yes) (crossoutdnponfab yes) (subtractmaskfromsilk no)'
            ' (outputformat 1) (mirror no) (drillshape 1) (scaleselection 1) (outputdirectory "gerbers/")))\n'
            '(net 0 "")\n' + "\n".join(f'(net {NETID[n]} "/{n}")' for n in NETS) + "\n")
    return head + "\n".join(fps + T + o + silk + [zone]) + "\n)\n"


def build_pro():
    return json.dumps({
        "meta": {"filename": f"{NAME}.kicad_pro", "version": 3},
        "board": {"design_settings": {
            "defaults": {"copper_line_width": 0.2, "silk_line_width": 0.12},
            "rules": {"min_clearance": 0.15, "min_copper_edge_clearance": 0.3, "min_track_width": 0.2,
                      "min_via_diameter": 0.6, "min_through_hole_diameter": 0.3, "min_via_annular_width": 0.15},
            "track_widths": [0.0, 0.25, 0.4, 0.5], "via_dimensions": [{"diameter": 0.0, "drill": 0.0},
                                                                       {"diameter": 0.8, "drill": 0.4}]}},
        "net_settings": {"classes": [{"name": "Default", "clearance": 0.2, "track_width": 0.25,
                                      "via_diameter": 0.8, "via_drill": 0.4}], "meta": {"version": 3}},
        "sheets": [[ROOT_UUID, "Root"]],
        "text_variables": {}}, indent=2)


def main():
    os.makedirs(os.path.join(ROOT, "lib", "nepamesh.pretty"), exist_ok=True)
    w = lambda p, s: open(os.path.join(ROOT, p), "w").write(s)
    w("lib/nepamesh.pretty/Supermini_nRF52840_THT.kicad_mod", supermini_fp() + "\n")
    w("lib/nepamesh.pretty/Wio-SX1262_Seeed.kicad_mod", wio_fp() + "\n")
    w("lib/nepamesh.kicad_sym",
      '(kicad_symbol_lib (version 20241209) (generator "nepamesh_build") (generator_version "1.0")\n'
      + SYM_SM + "\n" + SYM_WIO + "\n)\n")
    w("sym-lib-table", '(sym_lib_table (version 7)\n  (lib (name "nepamesh")(type "KiCad")'
                       '(uri "${KIPRJMOD}/lib/nepamesh.kicad_sym")(options "")(descr "project symbols"))\n)\n')
    w("fp-lib-table", '(fp_lib_table (version 7)\n  (lib (name "nepamesh")(type "KiCad")'
                      '(uri "${KIPRJMOD}/lib/nepamesh.pretty")(options "")(descr "project footprints"))\n)\n')
    w(f"{NAME}.kicad_pro", build_pro())
    w(f"{NAME}.kicad_sch", build_sch() + "\n")
    w(f"{NAME}.kicad_pcb", build_pcb())
    print("generated")


if __name__ == "__main__":
    main()
