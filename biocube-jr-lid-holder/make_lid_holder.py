"""Parametric lid prop for the Coralife BioCube JR (14 gal) hinged hood.

Side view, world frame (mm): X points toward the FRONT of the tank, Z is up.
The rim's top surface is Z=0 and its outside front face is X=0, so the rim
occupies X<0, Z<0. The hood hinge is at the back, about HINGE_TO_FRONT behind.

  * Foot: an L hook. The pad sits on the rim, the lip hangs over the outside
    front face. The lid load pushes the foot forward, the lip takes it.
  * Strut: leans back toward the hinge at the angle the lid edge swings to.
  * Head: a fork that straddles the hood's front edge (skirt). The slot is
    lined up with the skirt at the open angle so the edge drops straight in
    and is locked front to back. No friction needed.

The profile is extruded THICK mm and printed lying flat.

Run:  python3 make_lid_holder.py   (writes the STLs next to this script)
"""

from pathlib import Path

import numpy as np
import trimesh
from shapely.affinity import rotate, translate
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

IN = 25.4

# Tank (Coralife lists the 14/16 footprint around 15 x 16.75 in). The hinge
# to front edge distance is the one unknown that matters; the design is
# checked across HINGE_RANGE below.
HINGE_TO_FRONT = 15.5 * IN
HINGE_RANGE = (14.0 * IN, 17.0 * IN)

TOTAL_LEN = 8 * IN          # overall part length, lip bottom to fork tip
THICK = 16.0                # extrude depth = foot/head width across the tank
STRUT_W = 20.0

PAD_LEN = 22.0              # how far the pad reaches back over the rim top
PAD_T = 8.0
LIP_T = 7.0                 # lip thickness in front of the rim face
LIP_DROP = 10.0             # how far the lip hangs down the rim face
CORNER_RELIEF_R = 1.5       # lets the L seat on a sharp or burred rim corner

SKIRT_T = 3 / 8 * IN        # lid edge thickness (your 3/8 in measurement)
SLOT_W = 14.0               # SKIRT_T + room for angle error and a thicker edge
SLOT_DEPTH = 18.0           # outer tine length from the seat
INNER_TINE_DEPTH = 9.0      # short inner tine so it clears ribs inside the hood
TINE_T = 7.0
HEAD_BACK = 9.0             # material below the seat


def lid_pose(contact_len, hinge_to_front):
    """Lid open angle and prop lean for a prop of contact_len between the rim
    corner and the lid edge seat. Edge point E = (-d + d cos t, d sin t)."""
    d = hinge_to_front
    t = np.linspace(1e-4, 1.4, 200001)
    ex, ez = -d + d * np.cos(t), d * np.sin(t)
    i = np.argmin(abs(np.hypot(ex, ez) - contact_len))
    theta = t[i]
    lean = np.arctan2(-ex[i], ez[i])
    return theta, lean


def build(contact_len):
    theta, lean = lid_pose(contact_len, HINGE_TO_FRONT)
    axis = np.array([-np.sin(lean), np.cos(lean)])        # base -> seat
    u = np.array([-np.sin(theta), np.cos(theta)])          # skirt, edge -> into lid
    n = np.array([np.cos(theta), np.sin(theta)])           # outward from the hood
    seat = axis * contact_len

    pad = box(-PAD_LEN, 0, 0, PAD_T)
    lip = box(0, -LIP_DROP, LIP_T, PAD_T)

    strut_len = contact_len + 1
    strut = box(-STRUT_W / 2, 0, STRUT_W / 2, strut_len)
    strut = rotate(strut, np.degrees(lean), origin=(0, 0))
    strut = strut.difference(box(-500, -500, 500, 0))      # nothing below rim top...
    strut = unary_union([strut, lip, pad])

    def along(p0, du, dn):
        return tuple(p0 + u * du + n * dn)

    half = SLOT_W / 2 + TINE_T
    head = Polygon([along(seat, -HEAD_BACK, -half), along(seat, SLOT_DEPTH, -half),
                    along(seat, SLOT_DEPTH, half), along(seat, -HEAD_BACK, half)])
    head = head.buffer(1.5, join_style="round")
    # round bottomed slot (seat at its lowest point) with a flared mouth
    r = SLOT_W / 2
    c0 = seat + u * r
    slot = unary_union([
        Point(*c0).buffer(r, resolution=48),
        Polygon([along(c0, 0, -r), along(c0, 60, -r), along(c0, 60, r), along(c0, 0, r)]),
        Polygon([along(seat, SLOT_DEPTH - 2.5, -r), along(seat, SLOT_DEPTH + 3, -r - 3),
                 along(seat, SLOT_DEPTH + 3, r + 3), along(seat, SLOT_DEPTH - 2.5, r)]),
    ])
    inner_trim = Polygon([along(seat, INNER_TINE_DEPTH, -60), along(seat, 60, -60),
                          along(seat, 60, -r + 0.01), along(seat, INNER_TINE_DEPTH, -r + 0.01)])
    head = head.difference(slot).difference(inner_trim)

    part = unary_union([strut, head]).difference(slot)
    part = part.difference(box(-500, -500, 0, 0))          # ...and never inside the rim
    part = part.difference(Point(0, 0).buffer(CORNER_RELIEF_R, resolution=24))
    # soften outside corners
    part = part.buffer(-1.0, join_style="round").buffer(1.0, join_style="round")
    if part.geom_type != "Polygon":
        part = max(part.geoms, key=lambda g: g.area)
    return part, dict(theta=theta, lean=lean, seat=seat, axis=axis, u=u)


def overall_length(part, axis):
    pts = np.array(part.exterior.coords)
    proj = pts @ axis
    return proj.max() - proj.min()


def solve_contact_len():
    lo, hi = 120.0, 200.0
    for _ in range(40):
        mid = (lo + hi) / 2
        part, info = build(mid)
        if overall_length(part, info["axis"]) > TOTAL_LEN:
            hi = mid
        else:
            lo = mid
    return lo


def lay_flat(part, axis):
    """Rotate so the strut runs along X on the bed, origin at 0,0."""
    flat = rotate(part, -np.degrees(np.arctan2(axis[1], axis[0])), origin=(0, 0))
    minx, miny, _, _ = flat.bounds
    return translate(flat, -minx, -miny)


def extrude(poly):
    # drop near duplicate points left by the booleans, they break the triangulation
    mesh = trimesh.creation.extrude_polygon(poly.simplify(0.01), THICK)
    mesh.merge_vertices()
    return mesh


if __name__ == "__main__":
    out = Path(__file__).parent
    contact_len = solve_contact_len()
    part, info = build(contact_len)
    foot_test = part.intersection(box(-60, -60, 40, 34))
    head_test = part.intersection(Point(*info["seat"]).buffer(34))
    parts = {
        "biocube_jr_lid_holder.stl": part,
        "fit_test_foot.stl": foot_test,
        "fit_test_fork.stl": head_test,
    }
    for name, poly in parts.items():
        mesh = extrude(lay_flat(poly, info["axis"]))
        assert mesh.is_watertight, name
        mesh.export(out / name)
        ext = mesh.bounds[1] - mesh.bounds[0]
        print(f"{name}: {ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm, "
              f"{mesh.volume / 1000:.1f} cm3, watertight={mesh.is_watertight}")
    print(f"contact length {contact_len:.1f} mm, overall {overall_length(part, info['axis']) / IN:.2f} in")
    print(f"design: lid opens {np.degrees(info['theta']):.1f} deg, prop leans {np.degrees(info['lean']):.1f} deg")
