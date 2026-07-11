# -*- coding: utf-8 -*-
"""Test suite for the OKLM v1 exporters (LDML / xkb / keylayout).

No pytest dependency: plain assertions, one process, exit code 0/1. Run
from the repository root:

    python tools/tests/run_tests.py

Covers (see .internal/plan-exporters-v1.md phase 6):
1. every example manifest exports on all 3 targets without error;
2. every generated report validates against the conversion report schema;
3. exports are byte-for-byte deterministic across two runs;
4. committed goldens in examples/exports/ match freshly generated output
   (non-regression);
5. generated files contain no U+FFFD, no control bytes, LF only, no BOM;
6. a manifest using keys[].groups (out of v1 scope) fails cleanly.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "validators"))

from exporters import ldml, xkb, keylayout  # noqa: E402
from exporters.common import load_manifest  # noqa: E402
from validate import load_validator  # noqa: E402

EXAMPLES = sorted((ROOT / "examples").glob("*.oklm.json"))
TARGETS = {
    "ldml": (ldml, "ldml.xml"),
    "xkb": (xkb, "xkb"),
    "keylayout": (keylayout, "keylayout"),
}

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def integrity_check(name, text):
    check("�" not in text, f"{name}: contains U+FFFD replacement character")
    control_chars = [f"\\x{ord(c):02x}" for c in text if 0x01 <= ord(c) <= 0x07]
    check(not control_chars, f"{name}: contains control bytes {control_chars}")
    check("\r\n" not in text, f"{name}: contains CRLF line endings")


def main():
    check(len(EXAMPLES) == 6, f"expected 6 example manifests, found {len(EXAMPLES)}")

    report_validator = load_validator("oklm-conversion-report.schema.json")
    manifest_validator = load_validator("oklm-manifest.schema.json")

    results = {}  # (example_stem, target) -> (text, report)
    for path in EXAMPLES:
        stem = path.name[: -len(".oklm.json")]
        manifest = load_manifest(path)
        for target, (module, _ext) in TARGETS.items():
            text, report = module.export(manifest, source_file=path.name)
            results[(stem, target)] = (text, report)

            check(text is not None, f"{stem}/{target}: export failed unexpectedly")
            problems = list(report_validator.iter_errors(report))
            check(not problems, f"{stem}/{target}: report invalid: {[p.message for p in problems]}")

            if text is not None:
                integrity_check(f"{stem}/{target}", text)
                text2, report2 = module.export(manifest, source_file=path.name)
                check(text == text2, f"{stem}/{target}: export is not deterministic (text differs across runs)")
                check(report == report2, f"{stem}/{target}: report is not deterministic across runs")

    for path in EXAMPLES:
        stem = path.name[: -len(".oklm.json")]
        for target, (_module, ext) in TARGETS.items():
            golden_dir = ROOT / "examples" / "exports" / target
            golden_file = golden_dir / f"{stem}.{ext}"
            golden_report = golden_dir / f"{stem}.{ext}.report.json"
            text, report = results[(stem, target)]

            check(golden_file.exists(), f"{stem}/{target}: missing golden {golden_file}")
            check(golden_report.exists(), f"{stem}/{target}: missing golden report {golden_report}")
            if golden_file.exists():
                golden_bytes = golden_file.read_bytes()
                check(golden_bytes[:3] != b"\xef\xbb\xbf", f"{stem}/{target}: golden file has a BOM")
                fresh = (text + "\n").encode("utf-8") if not text.endswith("\n") else text.encode("utf-8")
                check(golden_bytes == fresh, f"{stem}/{target}: golden {golden_file} does not match fresh export (regression)")
            if golden_report.exists():
                golden_report_obj = json.loads(golden_report.read_text(encoding="utf-8"))
                check(golden_report_obj == report, f"{stem}/{target}: golden report {golden_report} does not match fresh report (regression)")

    minimal = load_manifest(ROOT / "examples" / "azerty-global-minimal.oklm.json")
    groups_manifest = json.loads(json.dumps(minimal))
    groups_manifest["keys"][0]["groups"] = {"2": {"1": "b"}}
    for target, (module, _ext) in TARGETS.items():
        text, report = module.export(groups_manifest, source_file="synthetic-groups.oklm.json")
        check(text is None, f"groups-scope/{target}: expected export to fail (keys[].groups out of v1 scope)")
        check(report["compatibilityLevel"] == "failed", f"groups-scope/{target}: expected compatibilityLevel 'failed'")
        check(bool(report["errors"]), f"groups-scope/{target}: expected a non-empty errors list")
        problems = list(report_validator.iter_errors(report))
        check(not problems, f"groups-scope/{target}: report invalid: {[p.message for p in problems]}")

    for path in EXAMPLES:
        problems = list(manifest_validator.iter_errors(json.loads(path.read_text(encoding="utf-8"))))
        check(not problems, f"{path.name}: manifest itself no longer validates: {[p.message for p in problems]}")

    if failures:
        print(f"FAILED ({len(failures)} problem(s)):")
        for f in failures:
            print(f"  - {f}")
        return 1
    total = len(EXAMPLES) * len(TARGETS)
    print(f"OK: {total} exports (6 examples x 3 targets), all reports schema-valid, "
          f"deterministic, matching committed goldens; groups-scope rejection verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
