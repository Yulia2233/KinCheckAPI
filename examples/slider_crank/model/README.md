# Slider-crank model contract

`source/slider_crank.cadir.py` is the runnable SimpleCADAPI/CADIR source. It
builds one grounded assembly from four explicit single-solid parts:

- `ground`: 280 x 120 x 20 mm base, bored Ø22 mm crank pedestal, and two
  160 mm guide rails with a 1 mm lateral shoe clearance;
- `crank`: Ø18 mm shaft, Ø60 mm flywheel, and Ø14 mm eccentric pin at a 20 mm
  crank radius;
- `connecting_rod`: 100 mm capsule web with Ø16 mm reamed bores in Ø28 mm eyes;
- `slider`: carriage, lower support, Ø14 mm pin shaft and guide shoes. The
  slider pin is separated from the carriage by the support geometry, so the
  connecting rod has a real one millimetre pin clearance and cannot float.

The assembly has three revolute joints and one X-axis prismatic joint. The
source uses explicit connector datums, a grounded root, and placements chosen
so the crank pin, rod bores, slider pin shaft, and guide origin coincide at the
nominal start state. The CADIR export produces `scene.xml`,
`scene.mapping.json`, and `meshes/`; the legacy b1 placement normalization is
kept only for reproducibility with the local exporter.

Build the package and run the independent acceptance program with:

```bash
uv run --extra addon python examples/slider_crank/model/source/slider_crank.cadir.py
uv run python examples/slider_crank/verification/verify.py examples/slider_crank/model
uv run python examples/slider_crank/verification/export_motion_package.py
```

The verifier consumes only the exported model directory. It checks all 201
motion samples for residuals, driver tracking, limits, trajectory bounds,
interference, signed minimum clearance (threshold 0.5 mm), and single-network
assembly integrity with the slider guide containment interval. A successful
run must report `passed: true`; warnings from the physics backend remain
visible in the structured motion result.
