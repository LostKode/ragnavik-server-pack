#!/usr/bin/env python3
"""Validate a coordinated Ragnavik release train against effective policy."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_KEYS = ("ui", "progress", "sleep_timer", "server", "client")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
RELEASE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
VERSIONED_DEPENDENCY = re.compile(r"^(?P<package>.+)-(?P<version>\d+\.\d+\.\d+)$")


def fail(message: str) -> None:
    print(f"release train validation failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        fail(f"cannot read {path}: {error}")


def dependency_versions(manifest: dict) -> dict[str, str]:
    result: dict[str, str] = {}
    for dependency in manifest.get("dependencies", []):
        match = VERSIONED_DEPENDENCY.fullmatch(dependency)
        if not match:
            fail(f"unparseable dependency: {dependency}")
        result[match["package"]] = match["version"]
    return result


def require_equal(label: str, declared: str | None, effective: str) -> None:
    if declared is not None and declared != effective:
        fail(f"{label} declares {declared}, but effective source contains {effective}")


def validate_blog(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {
        "ragnavik.com", "www.ragnavik.com", "ragnavik.vercel.app"
    }:
        fail("blog_url must be an HTTPS Ragnavik website URL")
    request = urllib.request.Request(url, headers={"User-Agent": "Ragnavik release validation"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status >= 400:
                fail(f"blog_url returned HTTP {response.status}")
    except Exception as error:
        fail(f"blog_url is not publicly reachable: {error}")


def validate(train_path: Path, check_blog: bool) -> dict:
    train = load(train_path)
    expected_top = {"schema_version", "release_id", "blog_url", "packages", "deployment_required"}
    if set(train) != expected_top:
        fail(f"top-level keys must be exactly {sorted(expected_top)}")
    if train["schema_version"] != 1:
        fail("schema_version must be 1")
    if not isinstance(train["release_id"], str) or not RELEASE_ID.fullmatch(train["release_id"]):
        fail("release_id contains unsupported characters")
    if not isinstance(train["deployment_required"], bool):
        fail("deployment_required must be true or false")
    packages = train["packages"]
    if not isinstance(packages, dict) or set(packages) != set(PACKAGE_KEYS):
        fail(f"packages must contain exactly: {', '.join(PACKAGE_KEYS)}")
    if not any(packages.values()):
        fail("at least one package must participate")
    for name, version in packages.items():
        if version is not None and (not isinstance(version, str) or not SEMVER.fullmatch(version)):
            fail(f"packages.{name} must be semantic x.y.z or null")
    if (packages["server"] or packages["progress"]) and not train["deployment_required"]:
        fail("Server or Progress releases must require deployment")
    if (packages["ui"] or packages["sleep_timer"] or packages["server"]) and not packages["client"]:
        fail("UI, Sleep Timer, and Server releases must include the dependent Client package")
    if check_blog:
        validate_blog(train["blog_url"])

    server = load(ROOT / "manifest.json")
    client = load(ROOT / "manifests/client-manifest.json")
    policy = load(ROOT / "manifests/anticheat-policy.json")
    client_dependencies = dependency_versions(client)
    require_equal("packages.server", packages["server"], server["version_number"])
    require_equal("packages.client", packages["client"], client["version_number"])
    require_equal("packages.ui", packages["ui"], client_dependencies["LostKode-Ragnavik_UI"])
    require_equal(
        "packages.progress",
        packages["progress"],
        policy["server_only"]["RagnavikProgress"]["version"],
    )
    require_equal(
        "packages.sleep_timer",
        packages["sleep_timer"],
        policy["client_embedded"]["RagnavikSleepTimer"]["version"],
    )
    if client_dependencies.get("LostKode-Ragnavik_Server") != server["version_number"]:
        fail("effective client manifest does not pin the effective Server version")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/generate_anticheat_policy.py"), "--check"],
        cwd=ROOT,
        check=True,
    )
    return train


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("train", type=Path)
    parser.add_argument("--skip-blog-check", action="store_true")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    train = validate(args.train, not args.skip_blog_check)
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as output:
            output.write(f"release_id={train['release_id']}\n")
            output.write(f"blog_url={train['blog_url']}\n")
            output.write(f"packages={json.dumps(train['packages'], separators=(',', ':'))}\n")
            output.write(f"deployment_required={str(train['deployment_required']).lower()}\n")
    print(json.dumps(train, indent=2))


if __name__ == "__main__":
    main()
