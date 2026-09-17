#!/usr/bin/env python3
"""Check Thunderstore dependencies and apply only explicitly reviewed patches."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = "https://thunderstore.io/c/valheim/api/v1/package/"
DEPENDENCY = re.compile(r"^(?P<package>.+)-(?P<version>\d+\.\d+\.\d+)$")


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_catalog(path: Path | None) -> list[dict]:
    if path:
        return json.loads(path.read_text(encoding="utf-8"))
    request = urllib.request.Request(
        DEFAULT_CATALOG,
        headers={"User-Agent": "Ragnavik dependency update checker"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def split_dependency(value: str) -> tuple[str, str]:
    match = DEPENDENCY.fullmatch(value)
    if not match:
        fail(f"unparseable dependency: {value}")
    return match["package"], match["version"]


def change_kind(current: str, latest: str) -> str:
    before = tuple(map(int, current.split(".")))
    after = tuple(map(int, latest.split(".")))
    if after <= before:
        return "none"
    if after[0] != before[0]:
        return "major"
    if after[1] != before[1]:
        return "minor"
    return "patch"


def updates(manifest: dict, catalog: list[dict]) -> list[dict]:
    packages = {item["full_name"]: item for item in catalog}
    result: list[dict] = []
    for dependency in manifest["dependencies"]:
        package, current = split_dependency(dependency)
        metadata = packages.get(package)
        if not metadata:
            fail(f"package missing from Thunderstore catalog: {package}")
        latest = next(
            (version for version in metadata["versions"] if version["is_active"]),
            None,
        )
        if not latest:
            fail(f"package has no active release: {package}")
        kind = change_kind(current, latest["version_number"])
        if kind == "none":
            continue
        result.append(
            {
                "package": package,
                "current": current,
                "latest": latest["version_number"],
                "kind": kind,
                "released": latest["date_created"],
                "dependencies": latest.get("dependencies", []),
                "changelog_url": (
                    "https://thunderstore.io/api/experimental/package/"
                    f"{metadata['owner']}/{metadata['name']}/{latest['version_number']}/changelog/"
                ),
            }
        )
    return result


def apply_reviewed_patches(path: Path, manifest: dict, found: list[dict], approved: set[str]) -> None:
    by_package = {item["package"]: item for item in found}
    unknown = sorted(approved - set(by_package))
    if unknown:
        fail(f"approved packages are not pending updates: {', '.join(unknown)}")
    refused = sorted(name for name in approved if by_package[name]["kind"] != "patch")
    if refused:
        fail(f"refusing non-patch updates: {', '.join(refused)}")
    replacements = {
        name: f"{name}-{by_package[name]['latest']}"
        for name in approved
    }
    manifest["dependencies"] = [
        replacements.get(split_dependency(value)[0], value)
        for value in manifest["dependencies"]
    ]
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, help="use a saved catalog instead of the live API")
    parser.add_argument(
        "--apply-patch",
        nargs="+",
        default=[],
        metavar="PACKAGE",
        help="apply only named, reviewed patch updates",
    )
    parser.add_argument("--json", action="store_true", help="print machine-readable results")
    args = parser.parse_args()
    manifest_path = ROOT / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        found = updates(manifest, load_catalog(args.catalog))
        if args.apply_patch:
            apply_reviewed_patches(manifest_path, manifest, found, set(args.apply_patch))
        if args.json:
            print(json.dumps(found, indent=2))
        elif not found:
            print("All direct Thunderstore dependencies are current.")
        else:
            for item in found:
                print(
                    f"{item['kind']:5} {item['package']}: "
                    f"{item['current']} -> {item['latest']}"
                )
                print(f"      released: {item['released']}")
                print(f"      requires: {', '.join(item['dependencies']) or 'none'}")
                print(f"      changelog: {item['changelog_url']}")
        if args.apply_patch:
            print("Applied reviewed patches: " + ", ".join(sorted(args.apply_patch)))
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"update check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
