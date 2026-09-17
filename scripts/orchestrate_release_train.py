#!/usr/bin/env python3
"""Dispatch and wait for every package in a validated release train."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import subprocess
import time
from pathlib import Path

from validate_release_train import validate

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = "publish-thunderstore.yml"
PACKAGES = {
    "ui": ("ragnavik-ui", "package/manifest.json"),
    "progress": ("ragnavik-progress", "package/manifest.json"),
    "sleep_timer": ("ragnavik-sleep-timer", "package/manifest.json"),
    "catos_reporter": ("ragnavik-catos-reporter", "package/manifest.json"),
    "server": ("ragnavik-server-pack", "manifest.json"),
    "client": ("ragnavik-client-pack", "manifest.json"),
}


def run(command: list[str], *, capture: bool = False, timeout: int | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        timeout=timeout,
    )
    return result.stdout if capture else ""


def remote_manifest(repo: str, path: str) -> dict:
    encoded = run(
        [
            "gh", "api", "--method", "GET", f"repos/LostKode/{repo}/contents/{path}",
            "-f", "ref=main", "--jq", ".content",
        ],
        capture=True,
    ).strip()
    return json.loads(base64.b64decode(encoded).decode("utf-8"))


def check_remote_versions(train: dict) -> None:
    for package, version in train["packages"].items():
        if version is None:
            continue
        repo, manifest_path = PACKAGES[package]
        actual = remote_manifest(repo, manifest_path).get("version_number")
        if actual != version:
            raise SystemExit(
                f"LostKode/{repo} main contains {actual}, expected {version} for {package}"
            )
        print(f"source verified: LostKode/{repo} {actual}")


def dispatch(package: str, version: str, train: dict, publish: bool) -> tuple[str, str, dt.datetime]:
    repo, _ = PACKAGES[package]
    started = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=5)
    run([
        "gh", "workflow", "run", WORKFLOW,
        "--repo", f"LostKode/{repo}",
        "--ref", "main",
        "-f", f"release_id={train['release_id']}",
        "-f", f"expected_version={version}",
        "-f", f"blog_url={train['blog_url']}",
        "-f", f"publish={str(publish).lower()}",
    ])
    print(f"dispatched {package} {version} in LostKode/{repo}")
    return repo, version, started


def find_run(repo: str, version: str, release_id: str, started: dt.datetime) -> int:
    title = f"Thunderstore {release_id} {version}"
    for _ in range(120):
        data = json.loads(run([
            "gh", "run", "list",
            "--repo", f"LostKode/{repo}",
            "--workflow", WORKFLOW,
            "--event", "workflow_dispatch",
            "--branch", "main",
            "--limit", "20",
            "--json", "databaseId,displayTitle,createdAt",
        ], capture=True))
        for item in data:
            created = dt.datetime.fromisoformat(item["createdAt"].replace("Z", "+00:00"))
            if item["displayTitle"] == title and created >= started:
                return int(item["databaseId"])
        time.sleep(5)
    raise SystemExit(f"timed out finding workflow run for LostKode/{repo} {version}")


def wait_for_phase(dispatched: list[tuple[str, str, dt.datetime]], release_id: str) -> None:
    runs: list[tuple[str, int]] = []
    for repo, version, started in dispatched:
        runs.append((repo, find_run(repo, version, release_id, started)))
    for repo, run_id in runs:
        run([
            "gh", "run", "watch", str(run_id),
            "--repo", f"LostKode/{repo}",
            "--exit-status",
        ], timeout=7200)
        print(f"completed: LostKode/{repo} run {run_id}")


def execute_phase(names: tuple[str, ...], train: dict, publish: bool) -> None:
    pending = [
        dispatch(name, train["packages"][name], train, publish)
        for name in names
        if train["packages"][name] is not None
    ]
    if pending:
        wait_for_phase(pending, train["release_id"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("train", type=Path)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if not os.environ.get("GH_TOKEN"):
        raise SystemExit("GH_TOKEN is required for cross-repository coordination")
    train = validate(args.train, check_blog=True)
    check_remote_versions(train)
    execute_phase(("ui", "progress", "sleep_timer", "catos_reporter"), train, args.publish)
    execute_phase(("server",), train, args.publish)
    execute_phase(("client",), train, args.publish)
    status = "READY_FOR_DEPLOYMENT" if train["deployment_required"] else "COMPLETE_NO_SERVER_DEPLOYMENT"
    print(f"{status}: {train['release_id']}")


if __name__ == "__main__":
    main()
