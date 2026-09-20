# E01 verification

`verify.py` is independent of the CAD model generators. It requires the exact package members and reports machine-readable `passed`, `status`, `what_happened`, `cause`, `how_to_fix`, object IDs, units, evidence, and source hashes. `checks.py` performs conversion, static cases, BREP pair ledger, independent moment comparison and rating checks. `archive_results.py` writes `.kincheck`, `physics.json`, viewer evidence, manifest and round-trip JSON. `negative_controls.py` exercises missing density, invalid units, payload double count, missing support, free axis, redundant reaction request, rating failure, density tampering, frame corruption, coverage deletion and a guard intrusion.

A returned `passed` value means the requested claim was established; a failed limit or an indeterminate reaction remains visible and is not rewritten as success. Later versions are not included in this claim.
