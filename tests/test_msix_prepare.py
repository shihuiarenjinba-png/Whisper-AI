from pathlib import Path
import json
import struct
import tempfile
import unittest
import xml.etree.ElementTree as ET

from scripts.msix_prepare import IdentityHold, prepare, verified_identity


def fixture():
    # Synthetic test fixture; NEVER a real Store identity.
    return {
        "verified": True, "package_name": "Training.FictionalSpeech",
        "publisher": "CN=00000000-0000-0000-0000-000000000001",
        "publisher_display_name": "Fictional QA Publisher",
        "display_name": "Fictional Speech QA", "version": "1.0.0.0",
        "store_id": "9PT000000001",
        "verification_source": "Partner Center", "evidence_reference": "Fixture-only unit test verification",
    }


class MsixGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "identity.json"

    def check(self, data):
        self.path.write_text(json.dumps(data), encoding="utf-8")
        return verified_identity(self.path)

    def test_no_identity_is_hold(self):
        with self.assertRaises(IdentityHold):
            verified_identity(self.path)

    def test_unverified_and_missing_evidence_are_hold(self):
        value = fixture()
        value["verified"] = False
        with self.assertRaises(IdentityHold):
            self.check(value)
        value["verified"] = True
        value["evidence_reference"] = ""
        with self.assertRaises(IdentityHold):
            self.check(value)

    def test_rejects_placeholder_and_bad_versions(self):
        for changed in ({"package_name": "PLACEHOLDER.Name"}, {"version": "1.0.1.2"},
                        {"version": "0.0.0.0"}, {"publisher": "Unknown"}):
            with self.subTest(changed=changed), self.assertRaises(IdentityHold):
                self.check({**fixture(), **changed})

    def test_manifest_and_logos_are_generated_only_for_verified_data(self):
        identity = self.check(fixture())
        stage = self.root / "stage"
        (stage / "LocalSpeechStudio").mkdir(parents=True)
        (stage / "LocalSpeechStudio" / "LocalSpeechStudio.exe").write_bytes(b"synthetic EXE")
        manifest = prepare(stage, identity)
        root = ET.parse(manifest).getroot()
        f = "{http://schemas.microsoft.com/appx/manifest/foundation/windows10}"
        res = "{http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities}"
        self.assertEqual(root.find(f + "Identity").attrib["Name"], identity["package_name"])
        self.assertEqual(root.find(f + "Capabilities").find(res + "Capability").attrib["Name"], "runFullTrust")
        self.assertEqual(root.find(f + "Applications").find(f + "Application").attrib["Executable"],
                         r"LocalSpeechStudio\LocalSpeechStudio.exe")
        for fn, size in (("StoreLogo.png", 50), ("Square150x150Logo.png", 150), ("Square44x44Logo.png", 44)):
            png = (stage / "Assets" / fn).read_bytes()
            self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II", png[16:24]), (size, size))
        with self.assertRaises(ValueError):
            prepare(stage, identity)


if __name__ == "__main__":
    unittest.main()
