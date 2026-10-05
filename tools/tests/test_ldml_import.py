# -*- coding: utf-8 -*-
"""Tests of the LDML -> OKLM importer and of the round trip (gate 3). Plain assertions, exit code 0/1.

    python tools/tests/test_ldml_import.py            # check
    python tools/tests/test_ldml_import.py --update   # rewrite the goldens in examples/imports/ldml/

Covers: (1) third-party CLDR keyboards (fixtures/ldml, Unicode license): manifest and report validity,
goldens, an independent reading of the XML compared with the imported keys; (2) OKLM -> LDML -> OKLM on
the six examples; (3) LDML -> OKLM -> LDML fixed point on the third-party keyboards; (4) unit cases of
the rule parser, the layer/modifier mapping and every "preserved" / "unsupported" path of the report.
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "validators"))

from exporters.common import load_manifest  # noqa: E402
from importers import ldml, roundtrip  # noqa: E402
from import_ldml import check_outputs  # noqa: E402

FIXTURES = ROOT / "tools" / "tests" / "fixtures" / "ldml"
GOLDENS = ROOT / "examples" / "imports" / "ldml"
DATA = ROOT / "tools" / "importers" / "data"
IMPLIED = ROOT / "tools" / "exporters" / "data" / "scanCodes-implied.xml"
THIRD_PARTY = ["fr", "ptabnt", "mt47"]

failures, counter = [], {"n": 0}


def check(condition, message):
    counter["n"] += 1
    if not condition:
        failures.append(message)


def render(manifest, report):
    return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", json.dumps(report, indent=2, ensure_ascii=False) + "\n"


def import_fixture(name):
    manifest, report = ldml.import_ldml((FIXTURES / f"{name}.xml").read_bytes(), source_file=f"{name}.xml")
    if manifest is not None:
        report["target"]["file"] = f"{name}.oklm.json"
    return manifest, report


# --- an independent reading of the XML (no code shared with the importer) ------------------------------

def unescape(text):
    return re.sub(r"\\u\{([0-9A-Fa-f ]+)\}", lambda m: "".join(chr(int(c, 16)) for c in m.group(1).split()), text)


def independent_reading(path):
    """{(scan code, modifiers attribute): output text or ('m', id)} straight from the XML."""
    keys = {}
    for source in (DATA / "keys-Latn-implied.xml", DATA / "keys-Zyyy-punctuation.xml", DATA / "keys-Zyyy-currency.xml", path):
        for element in ET.parse(source).getroot().iter("key"):
            if element.get("output") is not None:
                keys[element.get("id")] = element.get("output")
    root = ET.parse(path).getroot()
    namespace = root.tag.split("}")[0] + "}"
    forms = {f.get("id"): [r.get("codes").upper().split() for r in f.iter("scanCodes")]
             for f in ET.parse(IMPLIED).getroot().iter("form")}
    layers = root.find(namespace + "layers")
    rows_of_form = forms[layers.get("formId")]
    reading = {}
    for layer in layers.findall(namespace + "layer"):
        for index, row in enumerate(layer.findall(namespace + "row")):
            for code, key_id in zip(rows_of_form[index], row.get("keys").split()):
                if key_id in keys:
                    out = keys[key_id]
                    marker = re.fullmatch(r"\\m\{([^}]+)\}", out)
                    reading[(code, layer.get("modifiers"))] = ("m", marker.group(1)) if marker else unescape(out)
    return reading


MODIFIERS_TO_LEVEL = {"none": "1", "shift": "2", "altR": "3", "altR shift": "4", "ctrl alt": "3", "ctrl alt shift": "4"}


def check_against_reading(name, manifest):
    reading = independent_reading(FIXTURES / f"{name}.xml")
    by_hid = {key["hid"]: key for key in manifest["keys"]}
    by_code = {code: by_hid[hid] for code, hid in ldml.SCAN_TO_HID.items() if hid in by_hid}
    expected = got = 0
    for (code, modifiers), out in reading.items():
        level = MODIFIERS_TO_LEVEL[modifiers]
        key = by_code.get(code)
        value = key["levels"].get(level) if key else None
        if isinstance(out, tuple):
            # a marker: a dead key output if some transform uses it, otherwise the level is silent
            expected += 1
            if value is None or isinstance(value, dict):
                got += 1
            continue
        expected += 1
        if value == out:
            got += 1
        else:
            failures.append(f"{name}: {code}/{modifiers}: independent reading {out!r}, imported {value!r}")
    check(expected == got, f"{name}: {got}/{expected} outputs agree with the independent reading")
    return expected


# --- unit helpers --------------------------------------------------------------------------------------

def keyboard(layers="", keys="", extra="", locale="xx-t-k0-test", form="us"):
    return (f'<keyboard3 xmlns="https://schemas.unicode.org/cldr/45/keyboard3" locale="{locale}" conformsTo="45">'
            '<version number="1.2.3"/><info name="Test layout" author="Tester"/>'
            f'<keys>{keys}</keys>{extra}<layers formId="{form}">{layers}</layers></keyboard3>')


def layer(modifiers, keys_row1):
    return f'<layer modifiers="{modifiers}"><row keys="{keys_row1}"/></layer>'


def run(text, **options):
    manifest, report = ldml.import_ldml(text, source_file="t.xml", **options)
    return manifest, report


def expect_rule(from_text, to_text, sets=None, strings=None):
    try:
        return ldml.expand_rule(from_text, to_text, sets or {}, strings or {})
    except ldml.Unsupported as exc:
        return str(exc)


def unit_cases():
    # tokens and escapes
    check(ldml.tokenize("a\\u{41 42}\\m{x}b") == [("t", "aAB"), ("m", "x"), ("t", "b")], "tokenize mixes text, code points and markers")
    try:
        ldml.tokenize("\\n")
        check(False, "unknown escape must be refused")
    except ldml.Unsupported:
        check(True, "")
    check(ldml.slug("Français normalisé (AZERTY)") == "francais-normalise-azerty", "slug")

    # rules
    check(expect_rule("\\m{acute}e", "é") == ("acute", [("e", "é")], None), "literal composition")
    check(expect_rule("\\m{acute}", "´") == ("acute", None, "´"), "bare marker is the fallback (E15)")
    check(expect_rule("\\m{acute}\\u{5C}", "x") == ("acute", [("\\", "x")], None), "escaped backslash as a base")
    check(expect_rule("\\m{acute}\\u{28}", "x") == ("acute", [("(", "x")], None), "escaped parenthesis as a base is a literal")
    sets = {"v": "a e", "w": "á é", "short": "á"}
    check(expect_rule("\\m{acute}($[v])", "$[1:w]", sets) == ("acute", [("a", "á"), ("e", "é")], None), "mapped set")
    check(expect_rule("\\m{c}($[v])", "$1\\u{0301}", sets) == ("c", [("a", "a\u0301"), ("e", "e\u0301")], None), "capture + combining mark")
    check(expect_rule("\\m{c}$[v]x", "y", sets) == ("c", [("ax", "y"), ("ex", "y")], None), "bare set with a suffix")
    for case, args in {
        "regex dot": ("\\m{m}.", "x"), "regex group": ("\\m{m}(a|b)", "x"), "chained markers": ("\\m{m}\\m{n}", "x"),
        "no marker": ("ab", "x"), "no to": ("\\m{m}a", None), "star": ("\\m{m}a*", "x"), "unknown escape": ("\\m{m}\\d", "x"),
        "second dollar": ("\\m{m}a", "$2"), "set sizes": ("\\m{m}($[v])", "$[1:short]"), "unknown set": ("\\m{m}($[zzz])", "$1"),
    }.items():
        outcome = expect_rule(*args, sets=sets) if case != "x" else None
        check(isinstance(outcome, str), f"rule refused: {case} (got {outcome!r})")
    check(isinstance(expect_rule("\\m{m}a", "$1"), str), "capture in `to` without capture in `from`")
    check(expect_rule("\\m{m}${s}", "x", strings={"s": "q"}) == ("m", [("q", "x")], None), "string variable in from")

    # layers and modifiers
    levels, notes, rejected = ldml.parse_modifiers("caps altR shift")
    check(levels == ["8"] and not notes and not rejected, "caps altR shift is level 8")
    levels, notes, rejected = ldml.parse_modifiers("ctrl alt, altR")
    check(levels == ["3", "3"] and notes == ["ctrl alt"], "ctrl alt is read as AltGr")
    levels, notes, rejected = ldml.parse_modifiers("ctrl")
    check(not levels and rejected == ["ctrl"], "ctrl alone has no ISO level")

    # a plain keyboard
    text = keyboard(layer("none", "a b") + layer("shift", "A B") + layer("caps", "A B") + layer("caps shift", "a b") + layer("caps altR", "c d") + layer("caps altR shift", "C D"))
    manifest, report = run(text)
    check(manifest is not None and not check_outputs(manifest, report), "minimal keyboard imports and validates")
    if manifest:
        check(manifest["layoutId"] == "test" and manifest["locales"] == ["xx"] and manifest["version"] == "1.2.3" and manifest["authors"] == ["Tester"], "identity")
        row = {k["id"]: k["levels"] for k in manifest["keys"]}
        check(row.get("E00") == {"1": "a", "2": "A", "5": "A", "6": "a", "7": "c", "8": "C"}, f"levels of the first key {row.get('E00')}")
        check(manifest["levelSelectors"]["7"] == ["CapsLock", "Level3Shift"] and manifest["levelSelectors"]["8"] == ["CapsLock", "Level2Shift", "Level3Shift"], "selectors of 7 and 8")
        check(report["compatibilityLevel"] == "lossless-core" and report["roundTripConfidence"] == "high", f"clean import is lossless-core/high, got {report['compatibilityLevel']}")
        check(report["direction"] == "ldml-to-oklm" and report["source"]["conformsTo"] == 45 and report["source"]["version"] == "45", "report source")

    # errors
    manifest, report = run("<keyboard/>")
    check(manifest is None and report["compatibilityLevel"] == "failed", "wrong root element fails")
    manifest, report = run("<keyboard3")
    check(manifest is None and report["compatibilityLevel"] == "failed", "malformed XML fails")
    manifest, report = run(keyboard(layers='<layer modifiers="none"><row keys="a"/></layer>', form="touch"))
    check(manifest is None and "touch-only" in " ".join(report["errors"]), "touch-only keyboard fails")

    # report: unsupported and preserved paths
    manifest, report = run(keyboard(layer("none", "zzz a"), extra="<settings fallback=\"omit\"/><flicks/>"))
    check(manifest is not None, "unknown key id still imports the rest")
    check(any(u["construct"] == "key id 'zzz'" for u in report["unsupportedConstructs"]), "undefined key id is unsupported")
    check({p["construct"] for p in report["preservedAsExtensions"]} >= {"settings", "flicks"}, "unknown elements are preserved")
    check(manifest and {u["construct"] for u in manifest["extensions"]["OKLM_ldml"]["unmapped"]} >= {"settings", "flicks"}, "verbatim copy in the extension")
    check(report["roundTripConfidence"] == "low" and report["compatibilityLevel"] == "lossy-mapping", "unsupported construct gives low / lossy-mapping")

    manifest, report = run(keyboard(layer("none", "a b"), keys='<key id="a" output="x\\m{d}y"/><key id="b" output="b"/>'))
    check(any("mixes a marker and text" in u["detail"] for u in report["unsupportedConstructs"]), "marker + text output is unsupported")
    check(manifest and manifest["keys"][0]["id"] == "E01", "the other key still maps (position 2)")

    manifest, report = run(keyboard(layer("none", "a b") + layer("ctrl", "A B") + layer("altL", "a b") + layer("none", "c d"),
                                    keys='<key id="a" output="a"/>'))
    names = {p["construct"] for p in report["preservedAsExtensions"]}
    check("layer (modifiers not mapped)" in " ".join(names) and "layer (duplicate level)" in " ".join(names), f"unmapped and duplicate layers preserved: {names}")

    manifest, report = run(keyboard(layer("none", "a b"), keys='<key id="a" output="a" longPressKeyIds="b"/><key id="b" output="b"/>'
                                    '<import base="cldr" path="45/keys-Unknown.xml"/>'))
    names = " ".join(p["construct"] for p in report["preservedAsExtensions"])
    check("key attributes" in names and "keys import (unresolved)" in names, f"gesture attributes and unresolved imports preserved: {names}")

    # dead keys: marker with transforms, marker without, renamed marker, fallback only
    text = keyboard(layer("none", "a b c d"),
                    keys='<key id="a" output="\\m{Acute_X}"/><key id="b" output="\\m{lonely}"/><key id="c" output="\\m{fb}"/><key id="d" output="d"/>',
                    extra='<transforms type="simple"><transformGroup><transform from="\\m{Acute_X}d" to="é"/><transform from="\\m{fb}" to="!"/></transformGroup></transforms>')
    manifest, report = run(text)
    if manifest:
        dead = {d["id"]: d for d in manifest["deadKeys"]}
        check(set(dead) == {"acute-x", "fb"}, f"dead key ids {set(dead)}")
        check(dead["acute-x"]["extensions"]["OKLM_ldml"]["markerId"] == "Acute_X", "renamed marker keeps its original id")
        check(dead["fb"]["fallback"] == "!" and dead["fb"]["compositions"] == {" ": "!"}, "fallback-only dead key")
        row = {k["id"]: k["levels"] for k in manifest["keys"]}
        check("E01" not in row and row["E00"]["1"] == {"deadKey": "acute-x"}, "silent marker makes its key disappear, the others stay")
        check(not check_outputs(manifest, report), f"dead-key manifest validates: {check_outputs(manifest, report)[:2]}")
    check(any(u["construct"] == "marker 'lonely'" for u in report["unsupportedConstructs"]), "marker without transform is unsupported")
    check(any("renamed" in m["detail"] for m in report["lossyMappings"]), "renaming is a lossy mapping")

    # shadowing: first rule wins
    text = keyboard(layer("none", "a"), keys='<key id="a" output="\\m{m}"/>',
                    extra='<variables><set id="s" value="x y"/></variables><transforms type="simple"><transformGroup>'
                          '<transform from="\\m{m}x" to="1"/><transform from="\\m{m}($[s])" to="2"/></transformGroup></transforms>')
    manifest, report = run(text)
    check(manifest and manifest["deadKeys"][0]["compositions"] == {"x": "1", "y": "2"}, "first rule wins on a shared base")
    check(any("shadowed" in w for w in report["warnings"]), "shadowing is reported")

    # layoutId and locale
    manifest, report = run(keyboard(layer("none", "a"), locale="pt-t-k0-abnt2"))
    check(manifest and manifest["layoutId"] == "abnt2" and manifest["locales"] == ["pt"], "layoutId from the -t-k0- tail")
    manifest, report = run(keyboard(layer("none", "a"), locale="fr"))
    check(manifest and manifest["layoutId"] == "test-layout" and any(m["path"] == "layoutId" for m in report["lossyMappings"]), "layoutId derived from the name is lossy")
    check(manifest and manifest["extensions"]["OKLM_ldml"]["source"]["locale"] == "fr", "original locale kept")
    manifest, report = run(keyboard(layer("none", "a")), layout_id="forced", license="MIT", authors=["Me"])
    check(manifest and manifest["layoutId"] == "forced" and manifest["license"] == "MIT" and manifest["authors"] == ["Me"], "options override defaults")

    # scan codes: US D13 vs ISO C12, custom form, ABNT2 Ro
    keys_def = "".join(f'<key id="k{i}" output="{chr(0x61 + i % 26)}"/>' for i in range(26))
    row_one, row_two = " ".join(f"k{i}" for i in range(13)), " ".join(f"k{i}" for i in range(13, 26))
    text = keyboard(f'<layer modifiers="none"><row keys="{row_one}"/><row keys="{row_two}"/></layer>', keys=keys_def)
    manifest, _ = run(text)
    ids = [k["id"] for k in manifest["keys"]] if manifest else []
    check("D13" in ids and "C12" not in ids, f"US form: backslash key is D13 ({ids[-3:]})")
    manifest, _ = run(keyboard(layer("none", "a"), form="abnt2"))
    check(manifest and manifest["geometry"] == ["abnt-full"], "abnt2 form gives abnt geometry")
    custom = '<forms><form id="mine"><scanCodes codes="1E 1F"/><scanCodes codes="73"/></form></forms>'
    manifest, report = run(f'<keyboard3 xmlns="https://schemas.unicode.org/cldr/45/keyboard3" locale="xx-t-k0-t" conformsTo="45"><info name="N"/><keys><key id="a" output="a"/><key id="b" output="b"/><key id="c" output="c"/></keys>{custom}'
                           '<layers formId="mine"><layer modifiers="none"><row keys="a b"/><row keys="c"/></layer></layers></keyboard3>')
    if manifest:
        check([(k["id"], k["hid"]) for k in manifest["keys"]] == [("C01", "0x04"), ("C02", "0x16"), ("B11", "0x87")] and manifest["geometry"] == ["custom"], f"custom form: {[(k['id'], k['hid']) for k in manifest['keys']]}")
    else:
        check(False, f"custom form must import: {report['errors']}")

    # LDML-only HID: abnt2 Ro exports back
    if manifest:
        from exporters import ldml as exporter
        xml, export_report = exporter.export(manifest)
        check(xml is not None and "73" in xml, "the importer's B11 key exports back to scan code 73")


def main():
    update = "--update" in sys.argv
    GOLDENS.mkdir(parents=True, exist_ok=True)
    third_party_outputs = 0
    for name in THIRD_PARTY:
        manifest, report = import_fixture(name)
        check(manifest is not None, f"{name}: import failed {report['errors']}")
        if manifest is None:
            continue
        problems = check_outputs(manifest, report)
        check(not problems, f"{name}: does not validate: {problems[:2]}")
        manifest_text, report_text = render(manifest, report)
        check(report["direction"] == "ldml-to-oklm" and "preservedAsExtensions" in report and "unsupportedConstructs" in report, f"{name}: report fields")
        check(report["suggestedEnrichmentTasks"], f"{name}: enrichment tasks")
        check((manifest_text, report_text) == render(*import_fixture(name)), f"{name}: not deterministic")
        golden_manifest, golden_report = GOLDENS / f"{name}.oklm.json", GOLDENS / f"{name}.import.report.json"
        if update:
            golden_manifest.write_bytes(manifest_text.encode("utf-8"))
            golden_report.write_bytes(report_text.encode("utf-8"))
        check(golden_manifest.exists() and golden_manifest.read_bytes() == manifest_text.encode("utf-8"), f"{name}: golden manifest missing or different (run with --update)")
        check(golden_report.exists() and golden_report.read_bytes() == report_text.encode("utf-8"), f"{name}: golden report missing or different (run with --update)")
        third_party_outputs += check_against_reading(name, manifest)
        # LDML -> OKLM -> LDML fixed point
        first, second, comparison, xml, again = roundtrip.ldml_round_trip((FIXTURES / f"{name}.xml").read_bytes(), f"{name}.xml")
        check(comparison is not None and roundtrip.is_equal(comparison), f"{name}: LDML round trip differs: {comparison and comparison['differences'][:3]}")
        check(xml == again, f"{name}: exported LDML is not a fixed point")
        print(f"  {name}: {len(manifest['keys'])} keys, {len(manifest.get('deadKeys', []))} dead keys, "
              f"{sum(len(d['compositions']) for d in manifest.get('deadKeys', []))} compositions, level {report['compatibilityLevel']}, "
              f"{len(report['preservedAsExtensions'])} preserved, {len(report['unsupportedConstructs'])} unsupported; "
              f"LDML round trip {comparison['keys'][0]}/{comparison['keys'][1]} keys, {comparison['outputs'][0]}/{comparison['outputs'][1]} outputs, "
              f"{comparison['compositions'][0]}/{comparison['compositions'][1]} compositions")

    # OKLM -> LDML -> OKLM on the six examples
    totals = {"keys": [0, 0], "outputs": [0, 0], "deadKeys": [0, 0], "compositions": [0, 0]}
    examples = sorted((ROOT / "examples").glob("*.oklm.json"))
    check(len(examples) == 6, f"expected 6 examples, got {len(examples)}")
    for path in examples:
        manifest = load_manifest(path)
        comparison, lost, export_report, import_report = roundtrip.oklm_round_trip(manifest, path.name)
        check(comparison is not None, f"{path.name}: round trip could not run {export_report['errors']}")
        if comparison is None:
            continue
        check(roundtrip.is_equal(comparison), f"{path.name}: OKLM round trip differs: {comparison['differences'][:3]}")
        for field in totals:
            totals[field][0] += comparison[field][0]
            totals[field][1] += comparison[field][1]
        check(import_report["roundTripConfidence"] == "high" and import_report["compatibilityLevel"] == "lossless-core",
              f"{path.name}: the re-import of exporter output must be lossless-core/high, got {import_report['compatibilityLevel']}")
        print(f"  {path.name}: keys {comparison['keys'][0]}/{comparison['keys'][1]}, outputs {comparison['outputs'][0]}/{comparison['outputs'][1]}, "
              f"dead keys {comparison['deadKeys'][0]}/{comparison['deadKeys'][1]}, compositions {comparison['compositions'][0]}/{comparison['compositions'][1]}; "
              f"not carried by LDML: {', '.join(lost)}")
    print("  six examples, OKLM -> LDML -> OKLM: " + ", ".join(f"{k} {a}/{b}" for k, (a, b) in totals.items()))

    unit_cases()

    if failures:
        print(f"FAILED ({len(failures)} problem(s) over {counter['n']} checks):")
        for f in failures[:40]:
            print("  -", f)
        return 1
    print(f"OK: {len(THIRD_PARTY)} third-party keyboards ({third_party_outputs} outputs read independently), 6 round trips, "
          f"{counter['n']} checks passed, 0 failed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
