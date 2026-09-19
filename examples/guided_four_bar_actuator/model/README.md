# Model directory

`scene.xml`, `scene.mapping.json`, and `meshes/` are the CADIR export consumed by the independent verifier. The canonical editable source and `.scadpkg` are under `source/` and `out/` respectively.

Rebuild from source if the package or exported scene changes:

```bash
/Users/liuyu/Documents/cadir/repo/.venv/bin/python source/guided_four_bar_actuator.cadir.py
/Users/liuyu/Documents/cadir/repo/.venv/bin/python source/export_mjcf.py
```

`collision_meshes/` contains individual definition STLs from the same build, in
millimetres. These preserve base/guard/pin checks inside MJCF rigid groups;
the verifier applies a 0.001 scale and the exported geom-to-group transform.
`out/geometry_validation.json` records BREP validity, single-solid/closed-shell
counts, volume and bounds for every definition.
