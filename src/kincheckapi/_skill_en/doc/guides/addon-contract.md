# SimpleCADAPI addon contract

Use this page before consuming a `.scadpkg` or installing the addon. The addon
uses the SDK inside its own Python environment. It never installs analysis
dependencies into the environment that models geometry.

## Install and preflight

From a KinCheckAPI source checkout on macOS arm64:

```bash
uv venv --python 3.12 "$HOME/.local/share/kincheckapi/venv"
uv pip install --python "$HOME/.local/share/kincheckapi/venv/bin/python" -e '.[addon]' -e ../CADIR
export PATH="$HOME/.local/share/kincheckapi/venv/bin:$PATH"
kincheck doctor --addon --format json
```

This development release uses the sibling CADIR checkout, including its MJCF
canonical-frame decoding fix in 2.1.3b3. Do not substitute an unpatched 2.1.3b1.
After both releases are published, installing `kincheckapi[addon]` from the package
index can replace the two editable source arguments. `tool.uv.sources` records
the sibling checkout for development; package metadata retains a version range.
The `addon` extra contains `simplecadapi>=2.1.3b3,<2.1.4`; it agrees with the
descriptor's compatibility range. Existing MJCF-only installations can continue
without this extra. Python 3.12 is used for the addon integration checks; the
existing library's Python requirement is unchanged.

The descriptor declares only `macos-arm64`. Do not claim other addon platforms
until their native dependencies and package integration have been tested. This
restriction concerns addon installation, not the existing Python API.

Run the exact probe `kincheck doctor --addon --format json` before first use.
Exit 0 means usable. On nonzero exit, read `checks`, name the missing runtime and
stop. Do not silently change interpreter or skip a check. The probe is local,
headless and intended to finish in about two seconds. It checks the four native
analysis dependencies, compatible SDK version, package reader and MJCF exporter.

## Register the skill

The `sca` commands below manage copied skills, not Python environments. Keep the
addon environment on PATH so the descriptor's probe finds the correct `kincheck`.
For a clean repository use `sca addon add ./repo`. For a development checkout
containing virtual environments, first stage only distributable files:

```bash
python scripts/package_addon.py dist/sca-kincheckapi-0.5.7
sca addon init
sca addon add ./dist/sca-kincheckapi-0.5.7
sca addon list
```

The installed skill name is `sca-kincheckapi`. Runtime probe failure at installation
is a loud warning; installation still proceeds. First use remains blocked until
the probe succeeds. A foreign skill directory must not be overwritten.

`sca addon update kincheckapi` refreshes the registered source; `sca addon remove
kincheckapi` removes the registered addon and copied skill. Existing portable
`kincheckapi`/`kincheckapi-zh` archives remain available through `kincheck-skill-pack`.
If both variants are installed, invoke `sca-kincheckapi` for package consumption.

## Consume a package, preserve existing verification APIs

```python
from kincheckapi.addon import prepare_package
from verification.verify import verify

prepared = prepare_package(
    package_path="product.scadpkg",
    work_dir="analysis-work",
    required_interfaces={
        "node/product/bracket": ("interface.mount_face",),
    },
)
result = verify(prepared.model_dir)
result.raise_if_failed()
```

The occurrence and tag in this example are placeholders for the frozen acceptance
claim. Do not infer them from display names. Requirements are optional when a
claim uses only explicit joint/connector IDs. An empty mapping means no required
geometry tags; it does not select every interface.

The equivalent package CLI keeps `verify(model_dir)` unchanged:

```bash
kincheck verify-package product.scadpkg --work-dir analysis-work --script verification/verify.py --require-interface node/product/bracket=interface.mount_face --format json
```

`kincheck prepare-package product.scadpkg --work-dir analysis-work --format json`
prepares inputs only; its success does not establish mechanism acceptance. The
API and both package commands enforce the runtime probe before reading a package.
Existing `kincheck verify model/ --script verification/verify.py --format json`
continues to accept the original directory contract.

Every preparation owns a fresh directory under `work_dir`, containing `scene.xml`,
`scene.mapping.json`, `meshes/`, and `package-provenance.json`. Keep this directory
while using results or exporting their mesh assets. Temporary STL analysis caches
are created here by the unchanged MJCF adapter, away from the source package.
The source package is read once and never extracted, edited or overwritten.

## Package and interface rules

The main `simplecadapi` skill's `references/scadpkg-format.md` is the format
reference. A copy is in [scadpkg-format.md](scadpkg-format.md); authoritative
schemas are shipped at `simplecadapi/contracts/` in the SDK wheel.

Only package.json is parsed before checking schema major 3. Then the SDK validates
the full archive, definition schemas, manifest hash, member SHA256 values and
occurrence graph closure. Logical topology references are resolved by their
SHA256 through `manifest.blobs[].storage.path`, never by guessed filenames.

Part definitions must use millimeters. Interface requirements use exact part
occurrence node IDs from the occurrence graph. The index preserves definition
ID, revision, content hash, parent node and local transform for every occurrence;
instances of one definition are not conflated. All entities under an interface
name are retained in their recorded order. Missing occurrences, missing or empty
required names, corrupt members and unsupported schemas are named failures. Never
substitute approximate geometry for a required `interface.*` entry.

The input must be assembly-rooted and satisfy the upstream MJCF exporter's
supported mechanism contract. Unsupported exports fail explicitly; this addon
does not approximate an unsupported joint or closure. Exporter limitations and
source package hashes are retained in the provenance file.

## Units, coordinates and modeling handoff

Package lengths and geometry are in mm. Persisted occurrence and connector frames
encode these values as canonical integer ticks; SDK decoding must precede unit
conversion. The provenance `transform` retains this encoded representation,
identified by `transform_encoding`; do not interpret its raw integers as mm.
Use the SDK's decoded placements or exported MJCF frames for calculations.
SDK MJCF export converts positions to m,
angles to rad, and declares mesh scale `0.001`; the existing adapter applies that
scale once. Do not apply an additional mm-to-m conversion to MJCF positions or
normalized STL assets. Public KinCheckAPI quantities remain SI.

Occurrence transforms are parent-relative. Geometry tags belong to the part's
definition-local frame; use occurrence transforms and exported connector frames
for assembly/world interpretation. MJCF quaternions use `wxyz`; Pose uses `xyzw`.
`convert_mjcf()` performs this reordering. Public joint direction is
`component_b - component_a`; traversal direction is handled by the existing
kinematic conventions, not inferred from names.

Freeze the acceptance program first when designing a new mechanism. Delegate
modeling to the main SimpleCADAPI skill in its separate environment, then
`capture(result, "product.scadpkg")`. This addon consumes that completed package.
If verification requires geometry changes, return the evidence to the main skill,
change the modeling source and re-capture. Never edit package members, regenerate
geometry inside the verifier, or weaken the original acceptance claim to pass.

## Release checks

Run the core regression suite without the addon extra, then run addon integration
tests in its independent environment. Exercise package tampering, unsupported
schema, missing interfaces and runtime failures, as well as a real MJCF conversion
and unchanged solver path. Run local `sca addon add`, `list`, `update` and `remove`
with temporary home/skills locations; confirm the copied skill name and no drift.
Measure the probe as a fresh process on each declared platform. Keep a release
version consistent across package, descriptor and skills. Tag only the tested
release; users can pin `owner/repo@<tag>`. Widen the SDK range or platform list
only after the corresponding integration checks pass.
