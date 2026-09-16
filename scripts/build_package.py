#!/usr/bin/env python3
"""Build a byte-for-byte reproducible Thunderstore package."""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDED = ("manifest.json", "README.md", "CHANGELOG.md", "icon.png", "config", "plugins")
FIXED_TIME = (2020, 1, 1, 0, 0, 0)


def package_files() -> list[Path]:
    files: list[Path] = []
    for name in INCLUDED:
        path = ROOT / name
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(item for item in path.rglob("*") if item.is_file())
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix())


def build(output: Path) -> str:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in package_files():
            name = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return hashlib.sha256(output.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", type=Path, default=ROOT / "dist/Ragnavik_Server.zip")
    args = parser.parse_args()
    digest = build(args.output)
    print(f"{digest}  {args.output}")


if __name__ == "__main__":
    main()
