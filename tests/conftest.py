from __future__ import annotations

from pathlib import Path

import pytest

from kincheckapi.cadir import convert_mjcf


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def ex1_mjcf_path() -> Path:
    return PROJECT_ROOT / "tests" / "fixtures" / "legacy_assembly_tree"


@pytest.fixture(scope="session")
def ex2_mjcf_path() -> Path:
    return PROJECT_ROOT / "examples" / "compact_two_stage_planetary_reducer" / "model_before"


@pytest.fixture(scope="session")
def ex3_mjcf_path() -> Path:
    return PROJECT_ROOT / "tests" / "fixtures" / "closed_loop_four_bar"


@pytest.fixture(scope="session")
def ex4_mjcf_path() -> Path:
    return PROJECT_ROOT / "tests" / "fixtures" / "jansen_walking_leg"


@pytest.fixture(scope="session")
def ex1_assembly(ex1_mjcf_path):
    return convert_mjcf(xml_path=ex1_mjcf_path / "scene.xml", mapping_path=ex1_mjcf_path / "scene.mapping.json", asset_root=ex1_mjcf_path).assembly


@pytest.fixture(scope="session")
def ex2_assembly(ex2_mjcf_path):
    return convert_mjcf(xml_path=ex2_mjcf_path / "scene.xml", mapping_path=ex2_mjcf_path / "scene.mapping.json", asset_root=ex2_mjcf_path).assembly


@pytest.fixture(scope="session")
def ex3_assembly(ex3_mjcf_path):
    return convert_mjcf(xml_path=ex3_mjcf_path / "scene.xml", mapping_path=ex3_mjcf_path / "scene.mapping.json", asset_root=ex3_mjcf_path).assembly


@pytest.fixture(scope="session")
def ex4_assembly(ex4_mjcf_path):
    return convert_mjcf(xml_path=ex4_mjcf_path / "scene.xml", mapping_path=ex4_mjcf_path / "scene.mapping.json", asset_root=ex4_mjcf_path).assembly
