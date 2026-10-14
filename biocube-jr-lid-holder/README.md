# BioCube JR lid holder

Prop that holds the Coralife BioCube JR (14 gal) hood open. 8 in overall.

* **Top fork** straddles the hood's front edge (up to about 1/2 in thick) and locks it
  front to back, so the lid can't slide off. The inner tine is short so it clears
  ribs inside the hood.
* **Bottom hook** sits on the rim at the front and its lip hangs over the outside
  face. The lid's weight pushes the foot forward, which is exactly what the lip stops.
* Built at the 12.5 deg lean the lid edge swings to, so the load runs straight down
  the strut. Lid opens about 25 deg, front edge about 6.5 in above the rim.

![preview](preview.png)

## Files

| File | What it is |
| --- | --- |
| `biocube_jr_lid_holder.stl` | The holder |
| `fit_test_foot.stl` | Foot only, check it hooks your rim |
| `fit_test_fork.stl` | Fork only, check it drops over the hood's front edge |
| `make_lid_holder.py` | Generator. Change `SLOT_W`, `LIP_DROP`, `HINGE_TO_FRONT` etc and rerun |

## Print settings (PLA)

* Orientation: flat, exactly as the STL loads. No supports.
* Layer height: 0.2 mm
* Walls: 5
* Top/bottom: 5 layers
* Infill: 40% gyroid
* Brim: not needed

## Math

Hood weight isn't published; a replacement 14/16 canopy is listed at 4.5 lb, used as the worst case.

| Hinge to front | Lid opens | Lean | Fork misalignment | Prop load |
| --- | --- | --- | --- | --- |
| 14 in | 27.7 deg | 13.8 deg | +1.4 deg | 2.05 lb |
| 15.5 in (design) | 24.9 deg | 12.5 deg | 0 | 2.09 lb |
| 17 in | 22.7 deg | 11.4 deg | -1.1 deg | 2.12 lb |

* Buckling (PLA, conservative E = 2 GPa): about 1050 lb. Whole 4.5 lb hood on it: 233x margin.
* Strut stress 0.06 MPa, worst case tine bending 2.8 MPa, PLA is about 50 MPa. No creep concern.
* A 3/8 in edge fits the 14 mm fork across the full 14 to 17 in range (needs 9.7 mm max).
* Foot tilt across that range lifts the pad under 0.6 mm, the lip still hangs 10 mm.

Regenerate with `pip install trimesh shapely mapbox_earcut numpy && python3 make_lid_holder.py`.
