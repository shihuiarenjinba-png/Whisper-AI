"""Prepare a gated Windows full-trust MSIX layout using verified Partner Center identity.

No defaults, fake identity, auto-downloads, certificate generation or Store submission.
This script does not make or sign an MSIX; the Windows-only workflow invokes MakeAppx.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET
import zlib


class IdentityHold(ValueError):
    """Required Store identity or its verification evidence is missing."""


def verified_identity(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise IdentityHold("HOLD: Store identity is not verified; create config/verified_store_identity.json only from Partner Center.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise IdentityHold("HOLD: Store identity data cannot be read.") from exc
    if not isinstance(data, dict) or data.get("verified") is not True:
        raise IdentityHold("HOLD: verified must be true after checking Partner Center.")
    fields = ("package_name", "publisher", "publisher_display_name", "display_name",
              "version", "store_id", "evidence_reference")
    if any(not isinstance(data.get(k), str) or not data[k].strip() for k in fields):
        raise IdentityHold("HOLD: one or more Store identity values or evidence references are missing.")
    if data.get("verification_source") != "Partner Center":
        raise IdentityHold("HOLD: identity must be checked against Partner Center product identity.")
    forbidden = ("placeholder", "example", "sample", "todo", "unknown", "fake", "test-only")
    if any(any(word in data[k].lower() for word in forbidden) for k in fields):
        raise IdentityHold("HOLD: example/placeholder identity values cannot build a package.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,48}[A-Za-z0-9]", data["package_name"]):
        raise IdentityHold("HOLD: unsupported MSIX Package/Identity/Name format.")
    if not data["publisher"].startswith("CN=") or len(data["publisher"]) > 256:
        raise IdentityHold("HOLD: verify the exact Publisher DN from Partner Center.")
    if not re.fullmatch(r"[A-Za-z0-9]{8,24}", data["store_id"]):
        raise IdentityHold("HOLD: invalid Store ID.")
    parts = data["version"].split(".")
    if len(parts) != 4 or not all(x.isascii() and x.isdigit() and 0 <= int(x) <= 65535 for x in parts):
        raise IdentityHold("HOLD: version must be four integers from 0 through 65535.")
    if int(parts[0]) == 0 or int(parts[-1]) != 0:
        raise IdentityHold("HOLD: use a nonzero major version and Store-reserved revision 0.")
    return {k: data[k] for k in fields}


def _chunk(tag: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", zlib.crc32(tag + payload) & 0xffffffff)


def _create_logo(path: Path, size: int) -> None:
    """Deterministic in-house placeholder artwork, not a final Store brand asset."""
    raw = bytearray()
    for y in range(size):
        raw.append(0)
        for x in range(size):
            xx, yy = x / size, y / size
            color = (24, 36, 63)
            # Simple microphone pictogram: capsule, ring, and stand.
            if ((xx - .5) / .095) ** 2 + ((yy - .39) / .19) ** 2 < 1:
                color = (102, 225, 214)
            if .27 < yy < .69 and .5 - .18 < xx < .5 + .18:
                arc = ((xx - .5) / .18) ** 2 + ((yy - .42) / .27) ** 2
                if .84 < arc < 1.10 and yy > .42:
                    color = (240, 246, 255)
            if (.49 < xx < .51 and .64 < yy < .79) or (.37 < xx < .63 and .78 < yy < .82):
                color = (240, 246, 255)
            raw.extend(color)
    png = b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw))) + _chunk(b"IEND", b"")
    path.write_bytes(png)


def prepare(stage: Path, identity: dict[str, str]) -> Path:
    exe = stage / "LocalSpeechStudio" / "LocalSpeechStudio.exe"
    if not exe.is_file():
        raise ValueError("MSIX stage must contain LocalSpeechStudio/LocalSpeechStudio.exe (PyInstaller onedir).")
    if (stage / "AppxManifest.xml").exists():
        raise ValueError("Refusing to overwrite an existing manifest.")
    assets = stage / "Assets"
    assets.mkdir(parents=True, exist_ok=True)
    for filename, size in (("StoreLogo.png", 50), ("Square150x150Logo.png", 150), ("Square44x44Logo.png", 44)):
        _create_logo(assets / filename, size)

    f = "http://schemas.microsoft.com/appx/manifest/foundation/windows10"
    uap = "http://schemas.microsoft.com/appx/manifest/uap/windows10"
    uap10 = "http://schemas.microsoft.com/appx/manifest/uap/windows10/10"
    rescap = "http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
    ET.register_namespace("", f)
    ET.register_namespace("uap", uap)
    ET.register_namespace("uap10", uap10)
    ET.register_namespace("rescap", rescap)
    root = ET.Element("{" + f + "}Package", {"IgnorableNamespaces": "uap uap10 rescap"})
    ET.SubElement(root, "{" + f + "}Identity", {
        "Name": identity["package_name"], "Publisher": identity["publisher"],
        "Version": identity["version"], "ProcessorArchitecture": "x64"})
    props = ET.SubElement(root, "{" + f + "}Properties")
    for name, value in (
        ("DisplayName", identity["display_name"]),
        ("PublisherDisplayName", identity["publisher_display_name"]),
        ("Logo", r"Assets\StoreLogo.png")):
        ET.SubElement(props, "{" + f + "}" + name).text = value
    dependencies = ET.SubElement(root, "{" + f + "}Dependencies")
    ET.SubElement(dependencies, "{" + f + "}TargetDeviceFamily", {
        "Name": "Windows.Desktop", "MinVersion": "10.0.19041.0", "MaxVersionTested": "10.0.26100.0"})
    resources = ET.SubElement(root, "{" + f + "}Resources")
    for lang in ("ja-jp", "en-us"):
        ET.SubElement(resources, "{" + f + "}Resource", {"Language": lang})
    apps = ET.SubElement(root, "{" + f + "}Applications")
    app = ET.SubElement(apps, "{" + f + "}Application", {
        "Id": "App", "Executable": r"LocalSpeechStudio\LocalSpeechStudio.exe",
        "{" + uap10 + "}RuntimeBehavior": "packagedClassicApp",
        "{" + uap10 + "}TrustLevel": "mediumIL"})
    ET.SubElement(app, "{" + uap + "}VisualElements", {
        "DisplayName": identity["display_name"],
        "Description": "Offline audio and video transcription",
        "BackgroundColor": "#18243F",
        "Square150x150Logo": r"Assets\Square150x150Logo.png",
        "Square44x44Logo": r"Assets\Square44x44Logo.png"})
    caps = ET.SubElement(root, "{" + f + "}Capabilities")
    ET.SubElement(caps, "{" + rescap + "}Capability", {"Name": "runFullTrust"})
    ET.indent(root, space="  ")
    manifest = stage / "AppxManifest.xml"
    ET.ElementTree(root).write(manifest, encoding="utf-8", xml_declaration=True)
    ET.parse(manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--identity-file", type=Path, required=True)
    parser.add_argument("--stage-dir", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        identity = verified_identity(args.identity_file)
        if args.validate_only:
            print("Store Identity gate: VERIFIED file structure; check provenance manually before commercial submission.")
            return
        if args.stage_dir is None:
            parser.error("--stage-dir is required to generate a manifest")
        manifest = prepare(args.stage_dir, identity)
        print("Prepared QA-only MSIX manifest:", manifest)
    except (IdentityHold, OSError, ValueError) as exc:
        parser.exit(2, str(exc) + "\n")


if __name__ == "__main__":
    main()
