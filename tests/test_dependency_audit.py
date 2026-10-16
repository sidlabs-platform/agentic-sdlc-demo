import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "dependency_audit", Path(__file__).resolve().parents[1] / "scripts/audit-template-deps.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class AuditTests(unittest.TestCase):
    def test_pinned_manifest_includes_all_tooling_packages(self):
        directory = Path(__file__).resolve().parents[1] / "scripts"
        names = {name for name, _version in AUDIT.pinned_packages(directory / "requirements-checks.txt", directory)}
        self.assertEqual(names, {"PyYAML", "ruff", "defusedxml"})

    def test_requirements_include_cannot_escape_or_be_unpinned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "requirements.txt"
            for content in ("-r ../outside.txt", "package>=1.0", "https://external.invalid/package.whl"):
                manifest.write_text(content, encoding="utf-8")
                with self.subTest(content=content), self.assertRaises(ValueError):
                    AUDIT.pinned_packages(manifest, root)

    def test_medium_advisories_block_and_withdrawn_do_not(self):
        class API:
            def pages(self, path):
                return iter(self.advisories)

        api = API()
        api.advisories = [{"ghsa_id": "GHSA-example", "severity": "medium", "withdrawn_at": None}]
        with self.assertRaisesRegex(ValueError, "advisory policy failed"):
            AUDIT.audit(api, [("example", "1.0")])
        api.advisories[0]["withdrawn_at"] = "2026-01-01"
        AUDIT.audit(api, [("example", "1.0")])


if __name__ == "__main__":
    unittest.main()
