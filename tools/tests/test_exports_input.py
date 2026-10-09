# -*- coding: utf-8 -*-
"""Manifests the exporters must refuse (audit 2026-10-09: B-08/C-05 conformsTo, B-09 duplicate HID).

    python tools/tests/test_exports_input.py

The validator is another component: these tests call the exporters directly, as a library user would,
so a manifest the validator lets through still gets a clear error and no ambiguous file.
"""
import sys

from test_exports_support import check, finish, keylayout, klc, ldml, minimal, parse_xml, report_errors, xkb, streamdeck

EXPORTERS = {"ldml": ldml, "keylayout": keylayout, "xkb": xkb, "klc": klc, "streamdeck": streamdeck}


def with_conforms_to(value):
    manifest = minimal()
    manifest["exports"] = [{"target": "ldml-keyboard-3", "options": {"conformsTo": value}}]
    return manifest


def main():
    # B-08 / C-05: only the DTD values 45-48, as integers
    for value in (45, 46, 47, 48):
        text, report = ldml.export(with_conforms_to(value), source_file="x")
        root = parse_xml(text, f"conformsTo {value}") if text else None
        check(root is not None and root.get("conformsTo") == str(value), f"conformsTo {value} should export")
        check(text is not None and f"/cldr/{value}/keyboard3" in text, f"conformsTo {value}: xmlns follows")
    for value in (44, 49, 99, 0, -1, "46", "forty", 46.0, True, None, [45], '45" evil="1'):
        text, report = ldml.export(with_conforms_to(value), source_file="x")
        check(text is None and report["compatibilityLevel"] == "failed" and any("conformsTo" in e for e in report["errors"]),
              f"conformsTo {value!r} should be refused with an error naming conformsTo")
        check(not report_errors(report), f"conformsTo {value!r}: report invalid")
    text, report = ldml.export(minimal(), source_file="x")
    check(text is not None and 'conformsTo="45"' in text, "default conformsTo stays 45")

    # B-09: two keys on one HID are refused by the exporters that place keys by HID
    manifest = minimal()
    manifest["keys"][1]["hid"] = manifest["keys"][0]["hid"]
    for target in ("ldml", "keylayout", "klc"):
        text, report = EXPORTERS[target].export(manifest, source_file="x")
        check(text is None and report["compatibilityLevel"] == "failed", f"{target}: duplicate HID should be refused")
        check(any("share HID" in e for e in report["errors"]), f"{target}: the error names the duplicate HID: {report['errors']}")
        check(not report_errors(report), f"{target}: report invalid")
    lowered = minimal()
    lowered["keys"][0]["hid"], lowered["keys"][1]["hid"] = "0x1E", "0x1e"
    text, report = ldml.export(lowered, source_file="x")
    check(text is None and any("share HID" in e for e in report["errors"]), "the same HID written in lower case is still a duplicate")
    # a modifier key does not count: it is dropped before placement
    with_modifier = minimal()
    with_modifier["keys"].append({"id": "B99", "hid": with_modifier["keys"][0]["hid"], "role": "modifier", "modifier": "Level2Shift"})
    check(ldml.export(with_modifier, source_file="x")[0] is not None, "a role:modifier key sharing a HID is dropped, not a duplicate")
    return finish("refused manifests")


if __name__ == "__main__":
    sys.exit(main())
