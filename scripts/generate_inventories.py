#!/usr/bin/env python3
"""Generate normalized before and proposed package inventories."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "14402f192cb744a87e92ec7e0154b811c7de9106"
OUTPUT = ROOT / "manifests/package-inventories.json"
APPROVED_REMOVALS = {
    "ADARC-BackpacksValheim1Compat",
    "BentoG-MissingPieces",
    "Chazman-RunicCharacterVault",
    "Crystal-ProperPortals",
    "Digitalroot-Eternal_Fire",
    "MainStreetGaming-BetterDiving",
    "MaxFoxGaming-Better_Beehives",
    "RandyKnapp-Jam",
    "TastyChickenLegs-AutomaticFuel",
    "TastyChickenLegs-BetterCarts",
    "TeamNibake-SleepSkip1point0fork",
    "Vapok-ShieldMeBruh",
    "Vapok-XPortalNetworks",
    "VentureValheim-Need_For_Speed",
    "VentureValheim-Venture_Floating_Items",
    "blacks7ar-Agility",
    "blacks7ar-Endurance",
    "blacks7ar-Husky",
    "blacks7ar-MagicRevamp",
    "ishid4-BetterArchery",
    "shudnal-ProtectiveWards",
}
APPROVED_REMOVED_FILES = {
    "config/XPortalNetworks/xportal_networks.json",
    "config/chazman.RunicCharacterVault.cfg",
    "config/vapok.mods.shieldmebruh.cfg",
    "config/vapok.mods.xportalnetworks.cfg",
    "plugins/RagnavikEpicMMOReloadGuard/RagnavikEpicMMOReloadGuard.dll",
}


def split_dependency(value: str) -> str:
    return value.rsplit("-", 1)[0]


def base_file(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)


def base_files(directory: str) -> list[str]:
    output = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", BASE, directory], cwd=ROOT, text=True
    )
    return sorted(line for line in output.splitlines() if line)


def current_files(directory: str) -> list[str]:
    root = ROOT / directory
    return sorted(path.relative_to(ROOT).as_posix() for path in root.rglob("*") if path.is_file())


def inventory() -> dict:
    before_manifest = json.loads(base_file("manifest.json"))
    server = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    client = json.loads((ROOT / "manifests/client-manifest.json").read_text(encoding="utf-8"))
    before_names = {split_dependency(item) for item in before_manifest["dependencies"]}
    proposed_names = {split_dependency(item) for item in server["dependencies"]}
    removed = sorted(before_names - proposed_names)
    unapproved = sorted(set(removed) - APPROVED_REMOVALS)
    if unapproved:
        raise ValueError(f"unapproved dependency removals: {unapproved}")
    before_files = set(base_files("config") + base_files("plugins") + base_files("patchers"))
    proposed_files = set(current_files("config") + current_files("plugins") + current_files("patchers"))
    removed_files = sorted(before_files - proposed_files)
    unapproved_files = sorted(set(removed_files) - APPROVED_REMOVED_FILES)
    if unapproved_files:
        raise ValueError(f"unapproved package file removals: {unapproved_files}")
    return {
        "baseline_commit": BASE,
        "before": {
            "server_dependencies": sorted(before_manifest["dependencies"]),
            "config_files": base_files("config"),
            "plugin_files": base_files("plugins"),
            "patcher_files": base_files("patchers"),
            "assets": ["icon.png"],
        },
        "proposed": {
            "server_dependencies": sorted(server["dependencies"]),
            "client_direct_dependencies": sorted(client["dependencies"]),
            "client_effective_dependencies": sorted(set(server["dependencies"] + client["dependencies"])),
            "config_files": current_files("config"),
            "plugin_files": current_files("plugins"),
            "patcher_files": current_files("patchers"),
            "assets": ["LICENSE", "THIRD_PARTY_NOTICES.md", "icon.png"],
        },
        "diff": {
            "approved_removed_dependencies": removed,
            "approved_removed_files": removed_files,
            "added_dependencies": sorted(proposed_names - before_names),
            "added_files": sorted(proposed_files - before_files),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        content = json.dumps(inventory(), indent=2, sort_keys=True) + "\n"
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else None
        if args.check and current != content:
            print(f"stale generated file: {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
            return 1
        if not args.check and current != content:
            OUTPUT.write_text(content, encoding="utf-8", newline="\n")
            print(f"updated {OUTPUT.relative_to(ROOT)}")
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        print(f"inventory generation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
