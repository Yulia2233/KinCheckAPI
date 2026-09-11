#!/usr/bin/env python3
"""Stage a clean local addon repository without copying virtual environments."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil


def stage_addon(*, source: Path, destination: Path) -> Path:
    source = source.resolve()
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    for name in ("sca-addon.toml", "pyproject.toml", "LICENSE", "README.md", "README_zh.md", "MANIFEST.in"):
        shutil.copy2(source / name, destination / name)
    for name in ("src", "skill", "skill_zh"):
        shutil.copytree(
            source / name,
            destination / name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info", ".DS_Store"),
        )
    scripts = destination / "scripts"
    scripts.mkdir()
    shutil.copy2(source / "scripts/package_addon.py", scripts / "package_addon.py")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(stage_addon(source=Path(__file__).resolve().parents[1], destination=args.destination))
