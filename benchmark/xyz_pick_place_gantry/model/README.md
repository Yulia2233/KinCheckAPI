# XYZ gantry model source

Run from the KinCheckAPI environment:

```bash
.venv/bin/python benchmark/xyz_pick_place_gantry/model/source/build_xyz_pick_place_gantry.py
```

The script captures the canonical package at
`benchmark/xyz_pick_place_gantry/output/xyz_pick_place_gantry.scadpkg`.
Geometry is authored in millimetres and uses the four explicit `kg/mm^3`
materials from `prompt.md`; the adapter records conversion to SI density when
exporting MJCF.
