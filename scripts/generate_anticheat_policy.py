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
    shared = load(ROOT / "manifests/shared-manifest.json")
    policy = load(ROOT / "manifests/anticheat-policy.json")

    server_package = f"LostKode-{server['name']}"
    shared_package = f"LostKode-{shared['name']}"
    client_direct = dict(split_dependency(item) for item in client["dependencies"])
    server_direct = dict(split_dependency(item) for item in server["dependencies"])
    expected_shared_version = shared["version_number"]
    if client_direct.get(shared_package) != expected_shared_version:
        raise ValueError("client must require the stored Shared manifest version")
    if server_direct.get(shared_package) != expected_shared_version:
        raise ValueError("server must require the stored Shared manifest version")
    if server_package in client_direct:
        raise ValueError(f"client must not depend on server-only package {server_package}")
    shared_deps = dict(split_dependency(item) for item in shared["dependencies"])
    client_deps = {
        **shared_deps,
        **{package: version for package, version in client_direct.items() if package != shared_package},
    }
    server_deps = {
        **shared_deps,
        **{package: version for package, version in server_direct.items() if package != shared_package},
    }

    mismatched_shared = sorted(
        package for package in set(client_deps) & set(server_deps)
        if client_deps[package] != server_deps[package]
    )
    if mismatched_shared:
        raise ValueError(f"shared dependency version mismatch: {mismatched_shared}")

    mapped_packages = set(policy["client_only"])
    actual_packages = set(client_deps) - set(server_deps)
    if mapped_packages != actual_packages:
        missing = sorted(actual_packages - mapped_packages)
        stale = sorted(mapped_packages - actual_packages)
        raise ValueError(f"client-only mapping mismatch; missing={missing}, stale={stale}")

    actual_server_only = set(server_deps) - set(client_deps)
    mapped_server_only = set(policy["server_only"])
    if mapped_server_only != actual_server_only:
        missing = sorted(actual_server_only - mapped_server_only)
        stale = sorted(mapped_server_only - actual_server_only)
        raise ValueError(f"server-only mapping mismatch; missing={missing}, stale={stale}")

    extra_guids: list[str] = []
    for dependency in client["dependencies"]:
        package, _ = split_dependency(dependency)
        if package in actual_packages:
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

    for package, component in policy["server_only"].items():
        actual = server_deps.get(package)
        if actual != component["version"]:
            raise ValueError(
                f"server-only mapping mismatch for {package}; expected={component['version']}, actual={actual}"
            )

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
