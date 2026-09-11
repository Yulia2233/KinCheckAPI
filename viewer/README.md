# KinCheck Viewer

This is a standalone viewer for KinCheckAPI `.kincheck` motion packages. It is
deliberately outside `src/kincheckapi`: KinCheckAPI produces and validates package
data, while this application unpacks the data and plays it in a browser.

From the repository root:

```bash
python viewer/kincheck_viewer.py package_output/ex1.kincheck --serve
```

The command creates `viewer/runtime/ex1/`, checks every indexed file hash,
extracts the STL meshes, and starts the viewer at `http://127.0.0.1:8767/`.
Use the play button, timeline, speed selector, component visibility, and
orbit controls in the browser. Stop the server with `Ctrl-C`.

For ex2, use the same command with the other package:

```bash
python viewer/kincheck_viewer.py package_output/ex2.kincheck --serve
```

The package already contains the recorded component poses and joint
trajectories for every sampled time. The optional `--input-joint`,
`--output-joint`, and `--expected-ratio` arguments only annotate the
transmission metrics panel; they do not affect playback or run a new
simulation.

Without `--serve`, the command only unpacks the package and prints the local
`index.html` path.
