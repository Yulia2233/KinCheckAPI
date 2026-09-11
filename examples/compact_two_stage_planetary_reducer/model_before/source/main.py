"""Build, capture, and validate the compact planetary reducer package."""

from __future__ import annotations

import sys
from pathlib import Path

import simplecadapi as scad
from simplecadapi.translator.package_units import (
    read_product_package_translation_units,
)

if __package__:
    import importlib

    _module_names = (
        "dimensions",
        "common",
        "materials",
        "bearings",
        "carriers",
        "flanges",
        "gears",
        "housing",
        "shafts",
        "assembly",
    )
    _missing_module = object()
    _previous_modules = {
        name: sys.modules.get(name, _missing_module) for name in _module_names
    }
    try:
        for _module_name in _module_names:
            sys.modules[_module_name] = importlib.import_module(
                f"{__package__}.{_module_name}"
            )
        from .assembly import build_two_stage_planetary_reducer_product
        from .dimensions import (
            STAGE_1,
            STAGE_2,
            TOTAL_REDUCTION,
        )
    finally:
        for _module_name, _previous in _previous_modules.items():
            if _previous is _missing_module:
                sys.modules.pop(_module_name, None)
            else:
                sys.modules[_module_name] = _previous
else:
    from assembly import build_two_stage_planetary_reducer_product
    from dimensions import STAGE_1, STAGE_2, TOTAL_REDUCTION


# Herringbone gear profile graphs are intentionally deep.
sys.setrecursionlimit(30000)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "output"
PACKAGE_PATH = OUT_DIR / "compact_two_stage_planetary_reducer.scadpkg"


def _validate_runtime_assembly(*, assembly: scad.Assembly) -> None:
    """Check the design invariants retained from the former artifact example."""

    assert STAGE_1.ring_teeth == STAGE_1.sun_teeth + 2 * STAGE_1.planet_teeth
    assert STAGE_2.ring_teeth == STAGE_2.sun_teeth + 2 * STAGE_2.planet_teeth
    assert STAGE_1.fixed_ring_ratio == 5.0
    assert STAGE_2.fixed_ring_ratio == 4.0
    assert TOTAL_REDUCTION == 20.0
    assert len(assembly.component_ids()) == 25
    assert len(set(assembly.component_ids())) == 25
    assert len(assembly.constraint_ids()) == 45
    assert len(set(assembly.constraint_ids())) == 45
    assert len(assembly.grounded_component_ids) == 3
    assert len(assembly.connector_ids()) == 3

    constraint_report = scad.inspect_assembly_constraints_rconstraintreport(
        assembly=assembly
    )
    assert constraint_report.solved
    assert not constraint_report.unsolved_component_ids
    assert all(residual.within_tolerance for residual in constraint_report.residuals)

    collision_report = scad.verifier.check_collision_rcollisionreport(
        assembly=assembly,
        config=scad.verifier.CollisionCheckConfig(
            max_allowed_penetration=0.02,
            max_contacts_per_pair=16,
        ),
    )
    if collision_report.completed:
        assert collision_report.passed
        assert collision_report.failed_pair_count == 0
        collision_status = f"passed pairs={collision_report.checked_pair_count}"
    else:
        assert {warning.code for warning in collision_report.warnings} == {
            "backend_unavailable"
        }
        collision_status = "skipped backend=python-fcl"

    print(
        f"runtime_validation=passed components={len(assembly.component_ids())} "
        f"constraints={len(assembly.constraint_ids())} "
        f"collision={collision_status}"
    )


def _validate_package(*, path: Path) -> None:
    """Read the captured package back and prove that it is self-contained."""

    package = scad.read_product_package(path)
    scad.validate_product_package(package)
    translated_package, translation_units = read_product_package_translation_units(
        path
    )
    definition = scad.load_product_package(path)
    rebuilt = scad.materialize_definition(definition)

    assert package.manifest["schema_version"] == "2.0"
    assert package.manifest["artifact_kind"] == "product_package"
    assert package.root_kind == "assembly"
    assert package.root_id == "compact_two_stage_planetary_reducer"
    assert translated_package.root_id == package.root_id
    assert len(translation_units) == 17
    assert translation_units[-1].definition_id == package.root_id
    assert package.scene_path == "scene/scene.zip"
    assert package.scene_path in package.objects
    assert len(package.manifest["objects"]) == 17
    packaged_ids = {
        record["definition_id"] for record in package.manifest["objects"]
    }
    assert packaged_ids == {
        "compact_two_stage_planetary_reducer",
        "micro_radial_ball_bearing",
        "micro_radial_ball_bearing_ball",
        "micro_radial_ball_bearing_inner_ring",
        "micro_radial_ball_bearing_outer_ring",
        "reducer_housing",
        "input_flange",
        "output_flange",
        "input_shaft",
        "stage1_ring_gear",
        "stage1_sun_gear",
        "stage1_planet_gear",
        "stage1_carrier",
        "stage2_ring_gear",
        "stage2_sun_gear",
        "stage2_planet_gear",
        "stage2_carrier",
    }
    assert isinstance(definition, scad.AssemblyDefinition)
    assert isinstance(rebuilt, scad.Assembly)
    assert rebuilt.assembly_id == package.root_id
    assert rebuilt.component_ids() == tuple(
        instance.instance_id for instance in definition.instances
    )
    assert len(rebuilt.component_ids()) == 25
    assert len(rebuilt.constraint_ids()) == 45

    print(
        f"package_validation=passed schema={package.manifest['schema_version']} "
        f"definitions={len(package.manifest['objects'])} "
        f"bytes={path.stat().st_size}"
    )


def main() -> None:
    """Generate the canonical product package under ``output/``."""

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    product_result = build_two_stage_planetary_reducer_product()
    _validate_runtime_assembly(assembly=product_result.assembly)

    captured = scad.capture(product_result, PACKAGE_PATH)
    assert captured.value is product_result.assembly
    assert captured.package_bytes == PACKAGE_PATH.read_bytes()
    _validate_package(path=PACKAGE_PATH)

    print(f"product_package={PACKAGE_PATH}")


if __name__ == "__main__":
    main()
