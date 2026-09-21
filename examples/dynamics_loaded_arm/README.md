# E01 loaded arm — v0.6.0

This is the complete CADIR-backed static example for v0.6.0. The design brief and verifier were frozen before the model source. CAD uses millimetres and Z-up; public physics uses SI. The rated variant has 76 physical occurrences, including repeated washers, screws, keys, bushings, motor parts, guard and a calibrated 2 kg payload. Empty and 3 kg overload variants regenerate their BOM and manifest.

Run from the KinCheckAPI 2.1.3b3 addon environment:

```bash
python model/build_cadir.py                         # rated 2 kg
python model/build_cadir.py --variant empty
python model/build_cadir.py --variant overload
python verification/verify.py model
python verification/verify_dynamic.py model
python verification/verify_contact.py model
python verification/archive_results.py model /path/to/verification.json output
python verification/negative_controls.py
```

`verify.py` consumes explicit `product.scadpkg`, `scene.xml`, `scene.mapping.json` and `interfaces.json`. It integrates closed BREP mass properties, expands every occurrence frame, aggregates fixed groups, compiles explicit MuJoCo inertials, checks all 2,850 physical pairs at each 0°/30°/60° pose, and compares static moments against an independent sum. The viewer package displays numeric load frames and support totals; arrows are evidence presentation only.

The rated geometry/static cases pass. The 100 N eccentric load is intentionally over the illustrative 20/35 N·m ratings at 0° and therefore remains a failed limit check inside otherwise valid physics evidence. Individual bearing reaction sharing is not claimed. `model/faults/` is reserved for source-owned negative variants that must fail at the CAD/solver gate rather than be made to pass by exclusions.

The dynamic verifier adds a 30° prescribed-state inverse-dynamics case with a
2 rad/s² acceleration and a 35 N·m effort limit, then runs a 0.2 s finite
motor profile. The contact verifier checks a supplied platform-guide load with
Coulomb friction and pressure limits. These are scalar-tree and analytical
capacity claims; they do not claim closed-loop reaction sharing, contact-force
response, impact, stress, vibration, or fatigue.
