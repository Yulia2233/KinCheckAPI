"""E01 v0.6.3 analytical contact/friction capacity check."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from kincheckapi.dynamics import ContactSpec, check_contact_capacity


def verify(_model_dir: str | Path):
    # The support/load interfaces are validated by the E01 static verifier.
    # This case checks the declared guide contact capacity for a 10 N normal
    # load and a 1 N lateral load.  It is deliberately a capacity claim, not
    # a contact-force or impact integration.
    result = check_contact_capacity(
        contact=ContactSpec(
            contact_id="platform_guide",
            normal=(0.0, 0.0, 1.0),
            friction_coefficient=0.25,
            contact_area_m2=1e-3,
            allowable_normal_force_n=25.0,
            allowable_pressure_pa=20_000.0,
        ),
        force_n=(1.0, 0.0, 10.0),
    )
    return {"operation": "verify_e01_contact_capacity", **result.to_dict()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model_dir", type=Path)
    args = parser.parse_args()
    result = verify(args.model_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
