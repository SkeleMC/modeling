"""Parametric lid prop for the AquaLife / Coralife BioCube JR hood.

Layout (all mm, part lies flat for printing, X = length, Z = thickness):

  peg | shoulder foot | taper | strut ............ | flare | cradle (U notch)
  x=0                                                              x=203.2 (8 in)

The 3/8 in peg drops into the slot in the tank rim, the wide shoulder sits on
the rim around the slot, and the U notch at the top catches the lid edge/rib
so the lid cannot slide off the prop.

Run:  python3 make_lid_holder.py   (writes the STLs next to this script)
"""

from pathlib import Path

import trimesh
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

IN = 25.4

# User measurements
TOTAL_LEN = 8 * IN          # overall length, peg tip to cradle tips
END_SIZE = 3 / 8 * IN       # 9.525, slot / lid feature size

# Fit clearances (tuned for FDM, adjust if your printer runs tight or loose)
PEG_CLEARANCE = 0.3         # peg comes out 0.3 under 3/8 in
NOTCH_CLEARANCE = 0.5       # notch comes out 0.5 over 3/8 in

THICK = END_SIZE - PEG_CLEARANCE   # whole part is peg-thick so the peg is square
PEG_W = END_SIZE - PEG_CLEARANCE
PEG_LEN = 10.0
PEG_TIP_CHAMFER = 1.2

SHOULDER_W = 28.0
SHOULDER_LEN = 6.0
STRUT_W = 20.0
TAPER_LEN = 20.0
FLARE_LEN = 15.0
HEAD_W = 26.0
HEAD_LEN = 16.0
NOTCH_W = END_SIZE + NOTCH_CLEARANCE
NOTCH_DEPTH = 11.0
NOTCH_ENTRY_CHAMFER = 1.5
CORNER_R = 1.5


def outline(total_len=TOTAL_LEN):
    """2D profile in the XY plane, X along the length, centered on Y=0."""
    x_sh0 = PEG_LEN
    x_sh1 = x_sh0 + SHOULDER_LEN
    x_strut0 = x_sh1 + TAPER_LEN
    x_head0 = total_len - HEAD_LEN
    x_strut1 = x_head0 - FLARE_LEN

    body = Polygon([
        (x_sh0, -SHOULDER_W / 2), (x_sh1, -SHOULDER_W / 2),
        (x_strut0, -STRUT_W / 2), (x_strut1, -STRUT_W / 2),
        (x_head0, -HEAD_W / 2), (total_len, -HEAD_W / 2),
        (total_len, HEAD_W / 2), (x_head0, HEAD_W / 2),
        (x_strut1, STRUT_W / 2), (x_strut0, STRUT_W / 2),
        (x_sh1, SHOULDER_W / 2), (x_sh0, SHOULDER_W / 2),
    ])
    # round the outside corners so nothing snags or cracks at a sharp point
    body = body.buffer(-CORNER_R, join_style="round").buffer(CORNER_R, join_style="round")

    # U notch with a round bottom (no sharp inside corner to start a crack)
    r = NOTCH_W / 2
    x_notch_bottom = total_len - NOTCH_DEPTH + r
    notch = unary_union([
        box(x_notch_bottom, -r, total_len + 1, r),
        Point(x_notch_bottom, 0).buffer(r, resolution=32),
        Polygon([
            (total_len - NOTCH_ENTRY_CHAMFER, -r), (total_len + 0.01, -r - NOTCH_ENTRY_CHAMFER),
            (total_len + 0.01, r + NOTCH_ENTRY_CHAMFER), (total_len - NOTCH_ENTRY_CHAMFER, r),
        ]),
    ])
    body = body.difference(notch)

    c = PEG_TIP_CHAMFER
    peg = Polygon([
        (0, -PEG_W / 2 + c), (c, -PEG_W / 2), (PEG_LEN + 1, -PEG_W / 2),
        (PEG_LEN + 1, PEG_W / 2), (c, PEG_W / 2), (0, PEG_W / 2 - c),
    ])
    return unary_union([body, peg])


def extrude(poly):
    mesh = trimesh.creation.extrude_polygon(poly, THICK)
    mesh.merge_vertices()
    return mesh


def fit_test():
    """Just the peg, shoulder and a stub, about 5 minutes to print."""
    full = outline()
    return full.intersection(box(-1, -50, PEG_LEN + SHOULDER_LEN + 8, 50))


def notch_test():
    """Just the cradle head, to check it grabs the lid edge before the full print."""
    full = outline()
    return full.intersection(box(TOTAL_LEN - HEAD_LEN - 6, -50, TOTAL_LEN + 1, 50))


if __name__ == "__main__":
    out = Path(__file__).parent
    parts = {
        "biocube_jr_lid_holder.stl": outline(),
        "fit_test_peg.stl": fit_test(),
        "fit_test_notch.stl": notch_test(),
    }
    for name, poly in parts.items():
        mesh = extrude(poly)
        assert mesh.is_watertight, name
        mesh.export(out / name)
        ext = mesh.bounds[1] - mesh.bounds[0]
        print(f"{name}: {ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm, "
              f"{mesh.volume / 1000:.1f} cm3, watertight={mesh.is_watertight}")
