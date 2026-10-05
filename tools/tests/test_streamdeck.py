# -*- coding: utf-8 -*-
"""Tests of the Stream Deck exporter. Plain assertions, exit code 0/1.

    python tools/tests/test_streamdeck.py

Covers: structure of the zip (package.json, profile manifest, one manifest per page), one Text button per
distinct non-ASCII-alphanumeric character with the right settings, grid bounds, determinism, committed
goldens, report validity, the `unsupported` level (D33) and the rejection of `groups`. The profile is NOT
opened with the Stream Deck software: these tests check our own structure, not Elgato's acceptance.
"""
import copy
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "validators"))

from exporters import streamdeck  # noqa: E402
from exporters.common import load_manifest  # noqa: E402
from validate import load_validator  # noqa: E402

failures, counter = [], {"n": 0}


def check(condition, message):
    counter["n"] += 1
    if not condition:
        failures.append(message)


def read_profile(blob):
    archive = zipfile.ZipFile(io.BytesIO(blob))
    check(archive.testzip() is None, "zip integrity")
    files = {i.filename: json.loads(archive.read(i)) for i in archive.infolist()}
    return archive, files


def main():
    validator = load_validator("oklm-conversion-report.schema.json")
    examples = sorted((ROOT / "examples").glob("*.oklm.json"))
    exported = 0
    for path in examples:
        stem = path.name[: -len(".oklm.json")]
        manifest = load_manifest(path)
        blob, report = streamdeck.export(manifest, source_file=path.name)
        check(not list(validator.iter_errors(report)), f"{stem}: report invalid")
        expected = streamdeck.collect_characters(manifest)
        if stem == "azerty-global-minimal":
            check(blob is None and report["compatibilityLevel"] == "unsupported", f"{stem}: expected unsupported")
            continue
        exported += 1
        check(blob is not None, f"{stem}: export failed {report['errors']}")
        if blob is None:
            continue
        check(report["compatibilityLevel"] == "lossy-mapping" and report["roundTripConfidence"] == "low", f"{stem}: level")
        check(any("not been opened" in w for w in report["warnings"]), f"{stem}: unverified status not stated")
        check(blob == streamdeck.export(manifest, source_file=path.name)[0], f"{stem}: not deterministic")
        archive, files = read_profile(blob)
        package = files["package.json"]
        check(package["DeviceModel"] == streamdeck.DEVICE_MODEL and package["FormatVersion"] == 1, f"{stem}: package.json")
        profile_manifest = [v for k, v in files.items() if k.endswith(".sdProfile/manifest.json")]
        check(len(profile_manifest) == 1, f"{stem}: one profile manifest")
        pages = profile_manifest[0]["Pages"]["Pages"]
        check(len(pages) == -(-len(expected) // streamdeck.PER_PAGE), f"{stem}: page count")
        typed = []
        for name, page in files.items():
            if "/Profiles/" not in name:
                continue
            for pos, action in page["Controllers"][0]["Actions"].items():
                col, row = map(int, pos.split(","))
                check(0 <= col < streamdeck.COLUMNS and 0 <= row < streamdeck.ROWS, f"{stem}: {pos} outside the grid")
                check(action["UUID"] == streamdeck.TEXT_ACTION and action["Settings"]["isTypingMode"] is True, f"{stem}: action settings")
                typed.append(action["Settings"]["pastedText"])
        check(sorted(typed) == sorted(expected), f"{stem}: buttons differ from the expected characters")
        check(len(set(typed)) == len(typed), f"{stem}: duplicate button")
        golden = ROOT / "examples" / "exports" / "streamdeck" / f"{stem}.streamDeckProfile"
        check(golden.exists() and golden.read_bytes() == blob, f"{stem}: golden missing or different")
        golden_report = ROOT / "examples" / "exports" / "streamdeck" / f"{stem}.streamDeckProfile.report.json"
        check(golden_report.exists() and json.loads(golden_report.read_text(encoding="utf-8")) == report, f"{stem}: golden report")
    check(exported == 5, f"expected 5 exported examples, got {exported}")

    base = load_manifest(ROOT / "examples" / "azerty-global.oklm.json")
    check(len(streamdeck.collect_characters(base)) > streamdeck.PER_PAGE, "azerty-global should need several pages")
    grouped = copy.deepcopy(base)
    grouped["keys"][0]["groups"] = {"2": {"1": "b"}}
    blob, report = streamdeck.export(grouped, source_file="g.oklm.json")
    check(blob is None and report["compatibilityLevel"] == "failed", "groups must be rejected")

    if failures:
        print(f"FAILED ({len(failures)} problem(s) over {counter['n']} checks):")
        for f in failures[:30]:
            print("  -", f)
        return 1
    print(f"OK: {exported} Stream Deck profiles, {counter['n']} checks passed, 0 failed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
