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


CHECKS = {"n": 0}


def check(condition, message):
    CHECKS["n"] += 1
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

    # .XCompose companion of the xkb export: golden, determinism, integrity
    for path in EXAMPLES:
        stem = path.name[: -len(".oklm.json")]
        manifest = load_manifest(path)
        compose = xkb.export_compose(manifest, source_file=path.name)
        integrity_check(f"{stem}/XCompose", compose)
        check(compose == xkb.export_compose(manifest, source_file=path.name), f"{stem}/XCompose: not deterministic")
        golden = ROOT / "examples" / "exports" / "xkb" / f"{stem}.XCompose"
        check(golden.exists(), f"{stem}/XCompose: missing golden {golden}")
        if golden.exists():
            fresh = (compose + "\n").encode("utf-8") if not compose.endswith("\n") else compose.encode("utf-8")
            check(golden.read_bytes() == fresh, f"{stem}/XCompose: golden does not match fresh export (regression)")
        dead_ids = set() if stem != "azerty-global" else {dk["id"] for dk in manifest.get("deadKeys", [])}
        check(dead_ids <= set(xkb.DEAD_KEYSYMS), f"{stem}/xkb: dead keys without dead_* keysym: {sorted(dead_ids - set(xkb.DEAD_KEYSYMS))}")

    # .keylayout: every used dead key has a terminator and an own-state entry
    for path in EXAMPLES:
        stem = path.name[: -len(".oklm.json")]
        if stem != "azerty-global":
            continue
        text, _ = results[(stem, "keylayout")]
        used = set(re.findall(r'<action id="dk_([^"]+)"', text))
        terminators = set(re.findall(r'<when state="([^"]+)" output="[^"]*"/>', text.split("<terminators>")[-1])) if "<terminators>" in text else set()
        check(used <= terminators, f"{stem}/keylayout: dead keys without terminator: {sorted(used - terminators)}")
        for dk_id in used:
            block = re.search(rf'<action id="dk_{re.escape(dk_id)}">(.*?)</action>', text, re.S).group(1)
            if dk_id not in ("cyrillic", "extended-latin"):  # blank terminators: no own-state entry
                check(f'<when state="{dk_id}" output=' in block, f"{stem}/keylayout: dk_{dk_id} has no own-state entry")

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

    v02_checks(minimal, report_validator)

    if failures:
        print(f"FAILED ({len(failures)} problem(s) over {CHECKS['n']} checks):")
        for f in failures:
            print(f"  - {f}")
        return 1
    total = len(EXAMPLES) * len(TARGETS)
    print(f"OK: {total} exports (6 examples x 3 targets), all reports schema-valid, "
          f"deterministic, matching committed goldens; groups-scope rejection verified; "
          f"{CHECKS['n']} checks passed.")
    return 0


def v02_checks(minimal, report_validator):
    """Schema 0.2 behaviors: modifier keys, LDML escaping (E13), derived locale (E20),
    implied scan-code forms (E1), fallback transform (E15), capability lists."""
    import copy

    # E1: every scan code the HID table produces exists in CLDR's scanCodes-implied.xml
    forms = ldml.load_implied_forms()
    implied_codes = {code for rows in forms.values() for row in rows for code in row}
    check(set(forms) >= {"us", "iso", "abnt2", "jis", "ks"}, "implied forms: us/iso/abnt2/jis/ks present")
    stray = sorted(set(ldml.HID_TO_SCANCODE1.values()) - implied_codes)
    check(not stray, f"HID_TO_SCANCODE1 produces scan codes absent from CLDR implied forms: {stray}")
    check(ldml._implied_form_for(load_manifest(ROOT / "examples" / "azerty-global.oklm.json"))[0] == "iso",
          "azerty-global covers exactly the CLDR 'iso' form")
    check(ldml._implied_form_for(load_manifest(ROOT / "examples" / "qwerty-us.oklm.json"))[0] == "us",
          "qwerty-us covers exactly the CLDR 'us' form")
    check(ldml._implied_form_for(minimal) is None, "partial manifest keeps a custom form")

    # E13: escaping
    check(ldml.ldml_escape("\\") == "\\u{5C}", "E13: backslash output escaped")
    check(ldml.ldml_escape("á") == "a\\u{301}", "E13: combining mark escaped, base letter kept")
    check(ldml.ldml_escape(" ") == "\\u{A0}", "E13: no-break space escaped")
    check(ldml.ldml_escape(" ") == " ", "E13: ASCII space kept")
    check(ldml.ldml_escape("(", regex=True) == "\\u{28}" and ldml.ldml_escape("(") == "(",
          "E13: regex metacharacter escaped in `from` only")
    check(ldml.ldml_escape("$", replacement=True) == "\\u{24}", "E13: `$` escaped in `to`")
    metas = "\\^$.|?*+()[]{}"
    check(all(ldml.ldml_escape(ch, regex=True).startswith("\\u{") for ch in metas), "E13: all 14 metacharacters escaped in `from`")

    # E20: derived locale, 8-character subtags
    check(ldml.derived_locale(minimal) == ("fr-t-k0-azerty-global-minimal", False), "E20: derived locale")
    traditional = load_manifest(ROOT / "examples" / "azerty-traditionnel.oklm.json")
    check(ldml.derived_locale(traditional) == ("fr-t-k0-azerty-traditio", True), "E20: subtag cut to 8 characters")
    text, report = ldml.export(traditional, source_file="x")
    check(any(m["path"] == "layoutId" for m in report["lossyMappings"]), "E20: the cut is declared as lossy")

    # E15: fallback is a transform, not a lossy mapping
    text, report = ldml.export(minimal, source_file="x")
    check('from="\\m{circumflex}" to="^"' in text, "E15: fallback exported as a bare-marker transform")
    check(not any("fallback" in m["path"] for m in report["lossyMappings"]), "E15: fallback not reported as lossy")

    # E22: modifier keys carry no output and are skipped by every exporter
    with_modifier = copy.deepcopy(minimal)
    with_modifier["keys"].append({"id": "B99", "hid": "0xE1", "role": "modifier", "modifier": "Level2Shift"})
    for target, (module, _ext) in TARGETS.items():
        text, report = module.export(with_modifier, source_file="x")
        check(text is not None, f"E22/{target}: manifest with a modifier key exports")
        check(any(s["path"] == "keys[B99]" for s in report["skippedFields"]), f"E22/{target}: modifier key declared as skipped")
        check(not list(report_validator.iter_errors(report)), f"E22/{target}: report valid")
        reference_text, _ = module.export(minimal, source_file="x")
        check(text == reference_text, f"E22/{target}: output identical to the manifest without the modifier key")

    # capability lists and extensions are declared as skipped, never exported (E19)
    with_ext = copy.deepcopy(minimal)
    with_ext["extensions"] = {"OKLM_geometry": {"x": 1}}
    with_ext["extensionsUsed"] = ["OKLM_geometry"]
    text, report = ldml.export(with_ext, source_file="x")
    skipped = {s["path"] for s in report["skippedFields"]}
    check({"extensions", "extensionsUsed"} <= skipped, "E19: extensions and extensionsUsed declared as skipped")
    check("special" not in text and "OKLM_geometry" not in text, "E19: no `special` element, no extension content in LDML")


if __name__ == "__main__":
    sys.exit(main())
