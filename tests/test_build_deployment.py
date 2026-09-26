#!/usr/bin/env python3
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_deployment


def package(name, version, files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("manifest.json", json.dumps({"name": name, "version_number": version, "dependencies": []}))
        for path, value in files.items():
            archive.writestr(path, value)
    return stream.getvalue()


class DeploymentBuildTests(unittest.TestCase):
    def test_dependency_parser(self):
        self.assertEqual(build_deployment.split_dependency("LostKode-Ragnavik_Shared-1.0.8"), ("LostKode", "Ragnavik_Shared", "1.0.8"))

    def test_archive_routes_content(self):
        archive = package("Example", "1.2.3", {"plugins/Example.dll": b"plugin", "patchers/Patcher.dll": b"patcher", "config/example.cfg": b"config", "README.md": b"ignored"})
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            build_deployment.copy_archive("Team-Example-1.2.3", archive, output)
            self.assertEqual((output / "bepinex/plugins/Team-Example/plugins/Example.dll").read_bytes(), b"plugin")
            self.assertEqual((output / "bepinex/patchers/Team-Example/Patcher.dll").read_bytes(), b"patcher")
            self.assertEqual((output / "bepinex/config/example.cfg").read_bytes(), b"config")
            self.assertFalse((output / "bepinex/plugins/Team-Example/README.md").exists())


if __name__ == "__main__":
    unittest.main()
