"""Build portable Agent Skill bundles from the checked-in skill sources."""

from __future__ import annotations

import argparse
import gzip
import json
import importlib.metadata
import re
import shutil
import tarfile
from pathlib import Path
from typing import Iterable


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_ROOT.parents[1]
LANGUAGE_DIRS = {"en": "skill", "zh": "skill_zh"}


def _source_root(source_root: Path | None) -> Path:
    if source_root is not None:
        return source_root.expanduser().resolve()
    if (REPO_ROOT / "skill").is_dir():
        return REPO_ROOT
    return Path.cwd().resolve()


def _package_source(language: str) -> Path:
    bundled = PACKAGE_ROOT / ("_skill_en" if language == "en" else "_skill_zh")
    if bundled.is_dir():
        return bundled
    raise FileNotFoundError(f"Bundled {language} Skill resources are not installed")


def _iter_markdown(root: Path) -> Iterable[Path]:
    yield from sorted(path for path in root.rglob("*.md") if path.is_file())


def _rewrite_links(text: str, *, root_file: bool) -> str:
    text = text.replace("`doc/", "`references/docs/")
    text = text.replace("(doc/", "(references/docs/")
    if root_file:
        return text
    return text.replace("../SKILL.md", "../../SKILL.md")


def _copy_skill(source: Path, destination: Path, *, skill_name: str) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    skill_text = (source / "SKILL.md").read_text(encoding="utf-8")
    skill_text = _rewrite_links(skill_text, root_file=True)
    skill_text = re.sub(r"(?m)^name: .+$", f"name: {skill_name}", skill_text, count=1)
    (destination / "SKILL.md").write_text(skill_text, encoding="utf-8")
    references = destination / "references" / "docs"
    docs = source / "doc"
    if docs.is_dir():
        for path in _iter_markdown(docs):
            relative = path.relative_to(docs)
            target = references / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                _rewrite_links(path.read_text(encoding="utf-8"), root_file=False),
                encoding="utf-8",
            )
    (references / "README.md").write_text(
        "# KinCheckAPI Skill References\n\nGenerated from the public KinCheckAPI API surface.\n",
        encoding="utf-8",
    )
    _validate_bundle(destination, skill_name=skill_name)


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("SKILL.md frontmatter is not closed")
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def _validate_bundle(bundle: Path, *, skill_name: str) -> None:
    skill_file = bundle / "SKILL.md"
    if not skill_file.is_file():
        raise FileNotFoundError(f"Generated Skill is missing {skill_file}")
    frontmatter = _frontmatter(skill_file.read_text(encoding="utf-8"))
    if frontmatter.get("name") != skill_name:
        raise ValueError("Skill frontmatter name does not match the directory name")
    if not frontmatter.get("description"):
        raise ValueError("Skill description must not be empty")
    if (bundle / "src").exists():
        raise ValueError("Portable Skill must not contain runtime source code")
    for path in bundle.rglob("*"):
        if path.name == ".DS_Store" or path.name.endswith(".pyc"):
            raise ValueError(f"Generated Skill contains forbidden file: {path}")


def _archive(bundle: Path, output_root: Path) -> Path:
    archive = output_root / f"{bundle.name}.tar.gz"
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as tar:
                for path in sorted(bundle.rglob("*")):
                    info = tar.gettarinfo(str(path), arcname=str(Path(bundle.name) / path.relative_to(bundle)))
                    info.mtime = 0
                    if path.is_file():
                        with path.open("rb") as handle:
                            tar.addfile(info, handle)
                    else:
                        tar.addfile(info)
    return archive


def _write_adapters(bundle: Path, output_root: Path, *, version: str) -> list[Path]:
    adapters_root = output_root / "adapters"
    created: list[Path] = []
    claude = adapters_root / "claude-code"
    (claude / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (claude / "skills").mkdir(parents=True, exist_ok=True)
    (claude / ".claude-plugin/plugin.json").write_text(
        json.dumps(
            {
                "$schema": "https://anthropic.com/claude-code/plugin.schema.json",
                "name": "kincheckapi",
                "version": version,
                "description": "Verification-first CAD mechanism workflows with KinCheckAPI and SimpleCADAPI.",
                "skills": "./skills",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    claude_skill = claude / "skills" / bundle.name
    shutil.copytree(bundle, claude_skill, dirs_exist_ok=True)
    (claude / "commands").mkdir(exist_ok=True)
    (claude / "commands/kincheckapi.md").write_text(
        "---\ndescription: Run verification-first KinCheckAPI workflows.\n---\n\nUse the bundled kincheckapi skill and invoke `kincheck verify` for model validation.\n",
        encoding="utf-8",
    )
    created.append(claude)
    for harness in ("codex", "gemini", "cursor-opencode"):
        target = adapters_root / harness / bundle.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(bundle, target, dirs_exist_ok=True)
        created.append(target.parent)
    return created


def build(
    *,
    language: str = "en",
    output_root: Path = Path("dist"),
    archive: bool = False,
    adapters: bool = False,
    source_root: Path | None = None,
) -> list[Path]:
    output_root = output_root.expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    languages = ("en", "zh") if language == "both" else (language,)
    root = _source_root(source_root)
    try:
        package_version = importlib.metadata.version("kincheckapi")
    except importlib.metadata.PackageNotFoundError:
        from kincheckapi import __version__

        package_version = __version__
    results: list[Path] = []
    for selected in languages:
        source = root / LANGUAGE_DIRS[selected]
        if not source.is_dir():
            source = _package_source(selected)
        name = "kincheckapi" if selected == "en" else "kincheckapi-zh"
        bundle = output_root / name
        _copy_skill(source, bundle, skill_name=name)
        results.append(bundle)
        if archive:
            results.append(_archive(bundle, output_root))
        if adapters:
            results.extend(_write_adapters(bundle, output_root, version=package_version))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the KinCheckAPI Agent Skill bundle")
    parser.add_argument("--language", choices=("en", "zh", "both"), default="en")
    parser.add_argument("--output-root", type=Path, default=Path("dist"))
    parser.add_argument("--archive", action="store_true")
    parser.add_argument("--adapters", action="store_true")
    parser.add_argument("--source-root", type=Path, default=None)
    args = parser.parse_args(argv)
    for path in build(
        language=args.language,
        output_root=args.output_root,
        archive=args.archive,
        adapters=args.adapters,
        source_root=args.source_root,
    ):
        print(path)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
