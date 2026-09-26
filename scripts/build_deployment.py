#!/usr/bin/env python3
"""Resolve the Server Pack dependency graph and build a deployable BepInEx tree."""

from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import re
import shutil
import sys
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
DEPENDENCY = re.compile(
    r"^(?P<owner>[A-Za-z0-9_]+)-(?P<name>[A-Za-z0-9_]+)-"
    r"(?P<version>\d+\.\d+\.\d+(?:[-+][A-Za-z0-9_.-]+)?)$"
)
USER_AGENT = "Ragnavik deployment builder/1.0"
THUNDERSTORE_CATALOG = "https://thunderstore.io/c/valheim/api/v1/package/"
METADATA_NAMES = {
    "manifest.json", "icon.png", "readme.md", "changelog.md", "license",
    "license.md", "third_party_notices.md",
}


class PackageUnavailable(RuntimeError):
    pass


def fail(message: str) -> None:
    raise RuntimeError(message)


def request(url: str, method: str = "GET") -> urllib.request.Request:
    return urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method=method)


def read_url(url: str, timeout: int = 90) -> bytes:
    with urllib.request.urlopen(request(url), timeout=timeout) as response:
        return response.read()


def split_dependency(value: str) -> tuple[str, str, str]:
    match = DEPENDENCY.fullmatch(value)
    if not match:
        fail(f"invalid dependency string: {value}")
    return match["owner"], match["name"], match["version"]


def safe_member(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        fail(f"unsafe archive member: {name}")
    return path


@dataclass(frozen=True)
class Candidate:
    source: str
    url: str


class Resolver:
    def __init__(self, cache: Path, precedence: tuple[str, ...]) -> None:
        self.cache = cache
        self.precedence = precedence
        self.thunderstore: dict[str, dict] = {}

    def load_thunderstore(self) -> None:
        if self.thunderstore:
            return
        catalog = json.loads(read_url(THUNDERSTORE_CATALOG))
        self.thunderstore = {item["full_name"]: item for item in catalog}

    def hexium_candidate(self, owner: str, name: str, version: str) -> Candidate | None:
        page_url = f"https://valheim.hexium.gg/mods/{owner}/{name}"
        try:
            page = read_url(page_url, timeout=30).decode("utf-8")
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            raise
        metadata = None
        for payload in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', page, re.DOTALL
        ):
            item = json.loads(html.unescape(payload))
            if item.get("@type") == "SoftwareApplication":
                metadata = item
                break
        if not metadata or not isinstance(metadata.get("downloadUrl"), str):
            return None
        current_url = metadata["downloadUrl"]
        candidate = current_url if metadata.get("softwareVersion") == version else (
            current_url.rsplit("/", 1)[0] + f"/{version}.zip"
        )
        try:
            with urllib.request.urlopen(request(candidate, "HEAD"), timeout=30) as response:
                if response.status == 200:
                    return Candidate("hexium", candidate)
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
        return None

    def thunderstore_candidate(self, owner: str, name: str, version: str) -> Candidate | None:
        self.load_thunderstore()
        package = self.thunderstore.get(f"{owner}-{name}")
        if not package:
            return None
        for release in package.get("versions", []):
            if release.get("version_number") == version and release.get("is_active", True):
                return Candidate("thunderstore", release["download_url"])
        return None

    def resolve(self, dependency: str) -> Candidate:
        owner, name, version = split_dependency(dependency)
        candidates = {
            "hexium": lambda: self.hexium_candidate(owner, name, version),
            "thunderstore": lambda: self.thunderstore_candidate(owner, name, version),
        }
        found: dict[str, Candidate | None] = {}
        for source in self.precedence:
            found[source] = candidates[source]()
            if found[source] is not None:
                return found[source]  # type: ignore[return-value]
        raise PackageUnavailable(
            f"{dependency} was not available at the exact version from {', '.join(self.precedence)}"
        )

    def download(self, dependency: str, candidate: Candidate) -> tuple[bytes, str]:
        target = self.cache / f"{dependency}.zip"
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_file():
            content = target.read_bytes()
        else:
            content = read_url(candidate.url)
            target.write_bytes(content)
        digest = hashlib.sha256(content).hexdigest()
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                json.loads(archive.read("manifest.json"))
        except (zipfile.BadZipFile, KeyError, json.JSONDecodeError) as error:
            fail(f"invalid package archive for {dependency}: {error}")
        return content, digest


def copy_archive(dependency: str, content: bytes, output: Path) -> dict:
    owner, name, version = split_dependency(dependency)
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        if manifest.get("name") != name or manifest.get("version_number") != version:
            fail(
                f"archive identity mismatch for {dependency}: "
                f"{manifest.get('name')} {manifest.get('version_number')}"
            )
        package_root = output / "bepinex/plugins" / f"{owner}-{name}"
        for info in archive.infolist():
            if info.is_dir():
                continue
            member = safe_member(info.filename)
            if not member.parts:
                continue
            first = member.parts[0].lower()
            if len(member.parts) == 1 and first in METADATA_NAMES:
                continue
            if first == "config" and len(member.parts) > 1:
                destination = output / "bepinex/config" / Path(*member.parts[1:])
            elif first == "patchers" and len(member.parts) > 1:
                destination = output / "bepinex/patchers" / f"{owner}-{name}" / Path(*member.parts[1:])
            else:
                destination = package_root / Path(*member.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(info))
    return manifest


def build(args: argparse.Namespace) -> None:
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("name") != "Ragnavik_Server":
        fail("deployment builds must start from Ragnavik_Server")
    if args.output.exists():
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)
    resolver = Resolver(args.cache, tuple(args.source_precedence.split(",")))
    queue = list(manifest.get("dependencies", []))
    resolved: dict[str, dict] = {}
    selected_versions: dict[str, str] = {}
    version_conflicts: list[dict[str, str]] = []
    unavailable: list[str] = []
    while queue:
        dependency = queue.pop(0)
        if dependency in resolved:
            continue
        owner, name, _ = split_dependency(dependency)
        identity = f"{owner}-{name}"
        _, _, requested_version = split_dependency(dependency)
        selected_version = selected_versions.get(identity)
        if selected_version is not None:
            if selected_version != requested_version:
                version_conflicts.append({
                    "package": identity,
                    "selected": selected_version,
                    "ignored_transitive": requested_version,
                })
            continue
        selected_versions[identity] = requested_version
        if owner == "denikson" and name == "BepInExPack_Valheim":
            resolved[dependency] = {"source": "container", "archive_sha256": None}
            continue
        try:
            candidate = resolver.resolve(dependency)
        except PackageUnavailable as error:
            unavailable.append(str(error))
            continue
        content, digest = resolver.download(dependency, candidate)
        package_manifest = copy_archive(dependency, content, args.output)
        print(f"resolved {dependency} from {candidate.source}", flush=True)
        resolved[dependency] = {
            "source": candidate.source,
            "url": candidate.url,
            "archive_sha256": digest,
            "dependencies": package_manifest.get("dependencies", []),
        }
        queue.extend(package_manifest.get("dependencies", []))

    if unavailable:
        fail("unavailable exact packages:\n- " + "\n- ".join(sorted(unavailable)))

    config_target = args.output / "bepinex/config"
    config_target.mkdir(parents=True, exist_ok=True)
    for source in sorted((ROOT / "config").rglob("*")):
        if source.is_file():
            destination = config_target / source.relative_to(ROOT / "config")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    lock = {
        "schema_version": 1,
        "server_pack": manifest["version_number"],
        "source_precedence": list(resolver.precedence),
        "packages": dict(sorted(resolved.items())),
        "version_conflicts": version_conflicts,
    }
    (args.output / "deployment-lock.json").write_text(
        json.dumps(lock, indent=2) + "\n", encoding="utf-8"
    )
    files = sorted(
        str(path.relative_to(args.output)) for path in args.output.rglob("*") if path.is_file()
    )
    inventory = {
        "schema_version": 1,
        "server_pack": manifest["version_number"],
        "files": files,
    }
    (args.output / "deployment-inventory.json").write_text(
        json.dumps(inventory, indent=2) + "\n", encoding="utf-8"
    )
    print(f"resolved {len(resolved)} packages into {len(files)} files at {args.output}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "manifest.json")
    parser.add_argument("--output", type=Path, default=ROOT / "dist/deployment")
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache/deployment-packages")
    parser.add_argument(
        "--source-precedence",
        default="hexium,thunderstore",
        help="comma-separated source order; defaults to Hexium with Thunderstore fallback",
    )
    args = parser.parse_args()
    precedence = tuple(args.source_precedence.split(","))
    if not precedence or any(item not in {"hexium", "thunderstore"} for item in precedence):
        parser.error("source precedence may contain only hexium and thunderstore")
    if len(precedence) != len(set(precedence)):
        parser.error("source precedence contains a duplicate source")
    try:
        build(args)
        return 0
    except (OSError, RuntimeError, urllib.error.URLError, json.JSONDecodeError) as error:
        print(f"deployment build failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
