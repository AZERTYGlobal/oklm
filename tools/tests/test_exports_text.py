# -*- coding: utf-8 -*-
"""Escaping and refusal of hostile text in the exports (audit 2026-10-09: B-03, B-07, B-14, B-16, B-17).

    python tools/tests/test_exports_text.py

Every XML output of the six examples is parsed; the keylayout is also checked structurally (the
Apple DTD is a system file, not available here); then hostile names, outputs and compositions are
exported: what a target can carry must come back identical, anything else must be refused with an
error in the report (never a traceback, never a silent alteration).
"""
import re
import sys

from test_exports_support import (check, examples, finish, keylayout, klc, ldml, minimal, parse_xml, report_errors,
                                  streamdeck, xkb)
from exporters.common import ExportError

EXPORTERS = {"ldml": ldml, "keylayout": keylayout, "xkb": xkb, "klc": klc, "streamdeck": streamdeck}


def check_keylayout_structure(root, stem):
    """What KeyboardLayout.dtd and the macOS loader need: map indices, references, maxout."""
    indices = {m.get("index") for m in root.iter("keyMap")}
    selected = {s.get("mapIndex") for s in root.iter("keyMapSelect")}
    check(indices == selected, f"{stem}/keylayout: keyMap indices {sorted(indices)} != keyMapSelect {sorted(selected)}")
    actions = {a.get("id"): a for a in root.iter("action")}
    states = {"none"}
    for action in actions.values():
        for when in action.iter("when"):
            if when.get("next"):
                states.add(when.get("next"))
    for element in root.iter("key"):
        if element.get("action") is not None:
            check(element.get("action") in actions, f"{stem}/keylayout: key {element.get('code')} uses unknown action {element.get('action')}")
    for when in root.iter("when"):
        check(when.get("state") in states, f"{stem}/keylayout: <when state={when.get('state')!r}> has no state to enter it")
    maxout = int(root.get("maxout"))
    longest = max((len((e.get("output") or "").encode("utf-16-le")) // 2 for e in root.iter() if e.get("output") is not None), default=0)
    check(longest <= maxout, f"{stem}/keylayout: an output of {longest} UTF-16 units exceeds maxout {maxout}")


def unescape_ldml(text):
    return re.sub(r"\\u\{([0-9A-Fa-f]+)\}", lambda m: chr(int(m.group(1), 16)), text)


def name_manifest(value):
    manifest = minimal()
    manifest["name"] = value
    return manifest


def output_manifest(value):
    manifest = minimal()
    manifest["keys"][0]["levels"]["1"] = value
    return manifest


def compose_manifest(value):
    manifest = minimal()
    manifest["deadKeys"][0]["compositions"]["a"] = value
    return manifest


def refused(module, manifest):
    """True when export returned no file, with at least one error, a schema-valid report, no exception."""
    text, report = module.export(manifest, source_file="x")
    return text is None and bool(report["errors"]) and report["compatibilityLevel"] == "failed" and not report_errors(report)


def main():
    # every XML output of the examples is well formed (B-14), keylayout is structurally coherent
    for stem, manifest in examples():
        parse_xml(ldml.export(manifest, source_file="x")[0], f"{stem}/ldml")
        text, _ = keylayout.export(manifest, source_file="x")
        root = parse_xml(text, f"{stem}/keylayout")
        if root is not None:
            check_keylayout_structure(root, stem)

    # identity text: no control character or line separator, in any exporter
    for label, value in (("newline", "A\nB"), ("tab", "A\tB"), ("carriage return", "A\rB"), ("x01", "A\x01B"),
                         ("NUL", "A\x00B"), ("line separator", "A\u2028B"), ("surrogate", "A\ud800B")):
        for target, module in EXPORTERS.items():
            check(refused(module, name_manifest(value)), f"{target}: name with {label} should be refused")
    for target, module in EXPORTERS.items():
        manifest = minimal()
        manifest["authors"] = ["Ann\nINJECTED"]
        check(refused(module, manifest), f"{target}: author with a newline should be refused")
    check(not refused(ldml, name_manifest('A "quoted" & <tagged> name')), "ldml: quotes, ampersand and brackets in `name` are escaped, not refused")
    root = parse_xml(ldml.export(name_manifest('A "q" & <t>'), source_file="x")[0], "name/ldml")
    check(root is not None and root.find("info").get("name") == 'A "q" & <t>', "ldml: `name` round trips through XML escaping")

    # lone surrogates and noncharacters in a typed output: refused everywhere
    for label, value in (("lone surrogate", "\ud800"), ("U+FFFE", "\ufffe"), ("NUL", "\x00")):
        for target, module in EXPORTERS.items():
            check(refused(module, output_manifest(value)), f"{target}: output {label} should be refused")
            check(refused(module, compose_manifest(value)) or target == "streamdeck", f"{target}: composition result {label} should be refused")

    # tab, newline and carriage return in an output
    for value in ("\t", "\n", "\r"):
        root = parse_xml(keylayout.export(output_manifest(value), source_file="x")[0], "ctrl/keylayout")
        outputs = [k.get("output") for k in root.iter("key")]
        check(value in outputs, f"keylayout: {value!r} must survive as a character reference, got {outputs[:2]}")
        text = ldml.export(output_manifest(value), source_file="x")[0]
        root = parse_xml(text, "ctrl/ldml")
        check(root is not None and unescape_ldml(root.find("keys")[0].get("output")) == value, f"ldml: {value!r} output escaped as \\u{{..}}")
        check(refused(xkb, output_manifest(value)), f"xkb: control output {value!r} should be refused")
    check(refused(keylayout, output_manifest("\x01")), "keylayout: an XML 1.0 illegal control is refused, not written")
    check(unescape_ldml(parse_xml(ldml.export(output_manifest("\x01"), source_file="x")[0], "x01/ldml").find("keys")[0].get("output")) == "\x01",
          "ldml: U+0001 is carried as \\u{1}")
    text, _ = keylayout.export(compose_manifest("x\ny"), source_file="x")
    root = parse_xml(text, "comp-newline/keylayout")
    check(root is not None and "x\ny" in [w.get("output") for w in root.iter("when")], "keylayout: newline in a composition result survives")

    # .XCompose / xkb: a newline in a result or a name cannot inject a rule
    manifest = compose_manifest('x"\n<dead_acute> <a> : "INJECTED')
    check(refused(xkb, manifest), "xkb: composition result with a newline is refused")
    try:
        xkb.export_compose(manifest, source_file="x")
        raised = False
    except ExportError:
        raised = True
    check(raised, "export_compose should raise ExportError for a result with a newline")
    text = xkb.export_compose(compose_manifest('say "hi" \\ done'), source_file="x")
    check('"say \\"hi\\" \\\\ done"' in text, "xkb: quote and backslash in a result are escaped in the .XCompose")
    text, _ = xkb.export(name_manifest('Say "hi" \\'), source_file="x")
    check('name[Group1] = "Say \\"hi\\" \\\\";' in text, "xkb: quote and backslash in `name` are escaped")

    # klc: `$` accepted a trailing newline; a name or author with CR/LF broke KBD/COPYRIGHT (B-17)
    blob, report = klc.export(output_manifest("a\n"), source_file="x")
    check(blob is not None, "klc: output 'a\\n' (two characters) is skipped, not fatal")
    check(blob is None or "\n" not in blob[2:].decode("utf-16-le").replace("\r\n", ""), "klc: a stray LF in the file")
    check(streamdeck.collect_characters(output_manifest("a\n")).count("a\n") == 1, "streamdeck: 'a\\n' is not plain ASCII")

    # klc: no IndexError when the OEM names run out (B-16)
    manifest = minimal()
    punctuation = list("!\"#$%&'()*+,-./:;<=>?@")
    manifest["keys"] = [{"id": f"E{index:02d}", "hid": hid, "levels": {"1": char, "2": char}}
                        for index, (hid, char) in enumerate(zip(list(ldml.HID_TO_SCANCODE1)[:16], punctuation))]
    manifest["deadKeys"] = []
    text, report = klc.export(manifest, source_file="x")
    check(text is None and any("no free VK" in e for e in report["errors"]), "klc: running out of VK names is an error, not an IndexError")
    return finish("text escaping and refusal")


if __name__ == "__main__":
    sys.exit(main())
