#!/usr/bin/env python3
"""Generate CatosAntiCheat allowlists from the effective package manifests."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(r"^(?P<package>.+)-(?P<version>\d+\.\d+\.\d+(?:[-+].+)?)$")


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def split_dependency(value: str) -> tuple[str, str]:
    match = VERSION_RE.match(value)
    if not match:
        raise ValueError(f"dependency has no semantic version: {value}")
    return match.group("package"), match.group("version")


def render(title: str, guids: list[str]) -> str:
    return "\n".join([f"# GENERATED: {title}. Run scripts/generate_anticheat_policy.py.", *guids, ""])


def outputs() -> dict[Path, str]:
    server = load(ROOT / "manifest.json")
    client = load(ROOT / "manifests/client-manifest.json")
    policy = load(ROOT / "manifests/anticheat-policy.json")

    server_package = f"LostKode-{server['name']}"
    client_deps = dict(split_dependency(item) for item in client["dependencies"])
    expected_server_version = client_deps.pop(server_package, None)
    if expected_server_version != server["version_number"]:
        raise ValueError(
            f"client must pin {server_package}-{server['version_number']}; got {expected_server_version!r}"
        )

    mapped_packages = set(policy["client_only"])
    actual_packages = set(client_deps)
    if mapped_packages != actual_packages:
        missing = sorted(actual_packages - mapped_packages)
        stale = sorted(mapped_packages - actual_packages)
        raise ValueError(f"client-only mapping mismatch; missing={missing}, stale={stale}")

    extra_guids: list[str] = []
    for dependency in client["dependencies"]:
        package, _ = split_dependency(dependency)
        if package != server_package:
            extra_guids.extend(policy["client_only"][package])
    for component in policy["client_embedded"].values():
        extra_guids.extend(component["guids"])

    server_guids = [
        guid
        for component in policy["server_only"].values()
        for guid in component["guids"]
    ]
    if len(extra_guids) != len(set(extra_guids)) or len(server_guids) != len(set(server_guids)):
        raise ValueError("duplicate plugin GUID in anti-cheat policy")

    return {
        ROOT / "config/CatosAntiCheat_ExtraWhitelist.txt": render(
            "client-only plugins from the complete effective client manifest", extra_guids
        ),
        ROOT / "config/CatosAntiCheat_ServerOnly.txt": render(
            "server-only plugins from the complete effective server manifest", server_guids
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail instead of rewriting stale files")
    args = parser.parse_args()
    stale: list[str] = []
    try:
        rendered = outputs()
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"policy generation failed: {error}", file=sys.stderr)
        return 1
    for path, content in rendered.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == content:
            continue
        if args.check:
            stale.append(str(path.relative_to(ROOT)))
        else:
            path.write_text(content, encoding="utf-8", newline="\n")
            print(f"updated {path.relative_to(ROOT)}")
    if stale:
        print("stale generated files: " + ", ".join(stale), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
