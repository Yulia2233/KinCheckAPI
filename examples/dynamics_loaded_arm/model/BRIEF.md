# E01 modeling brief — v0.6.0

The frozen requirements live one directory above; the verifier was written before these sources.

- Z up; all CAD lengths mm; shaft axis -Y through (0,0,260); initial arm +X.
- Custom fabricated sliding bushings (not rolling bearings), illustrative uniform steel 7850 kg/m³. Guard aluminum 2700 kg/m³. No manufacturer rotor inertia overlay.
- Real base, feet, bearing bores, shaft/shoulder, thrust washers, clamp ring, keyed clamping hub, hollow arm, end block, platform, payload, load ear, motor housing/rotor, motor bracket and coupling guard. Motor is illustrative geometry, not a validated electrical machine.
- Fastener axes and head sides are explicitly recorded in the assembly specification. Blind threaded engagement remains within host material; standard fastening threads use nominal screw/bore envelopes with explicit tapped depth; no screw-drive thread exists in E01. Bushings and keyed/clamped interfaces use declared ideal fixed relations; real preload/friction/stress is outside v0.6.0.
- The load is bolted down, including at 60°; it is not a freely seated payload.
- Unspecified bracket and fastener clearances use ≥0.2 mm radial clearance; nominal 0.1 mm shaft/bushing fits have their own declared geometric region. Nonfunctional external edges have C0.5 before bore cutting where this preserves functional interfaces.
- Base mount uses an explicit ideal foundation mounting plane at Z=0, four bolts and blind foundation engagement. Foundation is an external environment support, not part of mechanism effective payload.
- Geometry acceptance uses exact BREP distances/common volume with 1e-9 m query budget; render meshes are not the clearance oracle. Three static poses, all N(N−1)/2 entity pairs, including internal hardware, are checked.
- Local contact regions bind named interface faces; expected near-contact regions also verify mounting proximity. No entire pair exclusions.
- Deliver product.scadpkg, model source files, interfaces.json, physical manifest, static evidence JSON, and .kincheck archive. Empty and 3 kg variants regenerate the payload/BOM consistently.
