# -*- coding: utf-8 -*-
"""Tests of the .klc exporter, against an in-repo parser of the format. Exit code 0/1.

    python tools/tests/test_klc.py

MSKLC was not available, so nothing here proves that Windows accepts the file: the parser below reads
what the exporter wrote the way the documented format (Microsoft `kbdus.klc` sample) is laid out, and the
checks compare it with the manifest.
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "validators"))

from exporters import klc  # noqa: E402
from exporters.common import load_manifest, resolve_level_modifiers  # noqa: E402
from exporters.ldml import HID_TO_SCANCODE1  # noqa: E402
from validate import load_validator  # noqa: E402

failures, counter = [], {"n": 0}


def check(condition, message):
    counter["n"] += 1
    if not condition:
        failures.append(message)


def parse_cell(cell):
    if cell == "-1":
        return None
    if cell.endswith("@"):
        return ("dead", chr(int(cell[:-1], 16)))
    if len(cell) == 1:
        return cell
    return chr(int(cell, 16))


def parse(blob):
    """Parse a .klc produced by the exporter."""
    assert blob[:2] == b"\xff\xfe", "missing UTF-16LE BOM"
    text = blob[2:].decode("utf-16-le")
    assert "\r\n" in text and "\n" not in text.replace("\r\n", ""), "CRLF expected"
    lines = text.split("\r\n")
    doc = {"header": {}, "states": [], "rows": [], "dead": {}, "sections": []}
    section = None
    dead = None
    for line in lines:
        if not line or line.startswith("//"):
            continue
        head = line.split("\t")[0]
        if head in ("KBD", "COPYRIGHT", "COMPANY", "LOCALENAME", "LOCALEID", "VERSION"):
            doc["header"][head] = line.split("\t")[1].strip('"') if "\t" in line else ""
            doc["sections"].append(head)
            section = None
        elif head in ("SHIFTSTATE", "LAYOUT", "DESCRIPTIONS", "LANGUAGENAMES", "ENDKBD"):
            section = head
            doc["sections"].append(head)
        elif head == "DEADKEY":
            dead = chr(int(line.split("\t")[1], 16))
            doc["dead"][dead] = {}
            section = "DEADKEY"
            doc["sections"].append(head)
        elif section == "SHIFTSTATE":
            doc["states"].append(int(head))
        elif section == "LAYOUT":
            parts = line.split("//")[0].rstrip("\t").split("\t")
            sc, vk = parts[0], parts[1]
            cap = int(parts[3])
            cells = [parse_cell(c) for c in parts[4:]]
            doc["rows"].append({"sc": sc, "vk": vk, "cap": cap, "cells": cells})
        elif section == "DEADKEY":
            parts = line.split("//")[0].rstrip("\t").split("\t")
            doc["dead"][dead][chr(int(parts[0], 16))] = chr(int(parts[1], 16))
    return doc


def main():
    validator = load_validator("oklm-conversion-report.schema.json")
    exported = 0
    for path in sorted((ROOT / "examples").glob("*.oklm.json")):
        stem = path.name[: -len(".oklm.json")]
        manifest = load_manifest(path)
        blob, report = klc.export(manifest, source_file=path.name)
        check(not list(validator.iter_errors(report)), f"{stem}: report invalid")
        check(blob is not None, f"{stem}: export failed {report['errors']}")
        if blob is None:
            continue
        exported += 1
        check(blob == klc.export(manifest, source_file=path.name)[0], f"{stem}: not deterministic")
        doc = parse(blob)
        check(doc["sections"][:6] == ["KBD", "COPYRIGHT", "COMPANY", "LOCALENAME", "LOCALEID", "VERSION"], f"{stem}: header order")
        check(doc["sections"][-1] == "ENDKBD", f"{stem}: ENDKBD missing")
        check(doc["states"] == [0, 1, 2, 6, 7], f"{stem}: shift states {doc['states']}")
        check(len(doc["header"]["KBD"].split("\t")[0]) <= 8, f"{stem}: short name too long")
        rows = doc["rows"]
        check(len(rows) == len(manifest["keys"]), f"{stem}: {len(rows)} rows for {len(manifest['keys'])} keys")
        check(len({r["vk"] for r in rows}) == len(rows), f"{stem}: duplicate VK")
        check(len({r["sc"] for r in rows}) == len(rows), f"{stem}: duplicate scan code")
        check([int(r["sc"], 16) for r in rows] == sorted(int(r["sc"], 16) for r in rows), f"{stem}: rows not sorted")
        check(all(len(r["cells"]) == 5 for r in rows), f"{stem}: wrong column count")
        resolved = resolve_level_modifiers(manifest)
        by_sc = {r["sc"]: r for r in rows}
        dead_char = {}
        for key in manifest["keys"]:
            row = by_sc[HID_TO_SCANCODE1[key["hid"]]]
            for level, state in (("1", 0), ("2", 1), ("3", 6), ("4", 7)):
                if level not in key.get("levels", {}) or resolved.get(level, []) != klc_qualifiers(level):
                    continue
                out = key["levels"][level]
                cell = row["cells"][[0, 1, 2, 6, 7].index(state)]
                if isinstance(out, dict):
                    check(isinstance(cell, tuple), f"{stem}/{key['id']}/{level}: dead key expected, got {cell!r}")
                    if isinstance(cell, tuple):
                        dead_char.setdefault(out["deadKey"], cell[1])
                        check(dead_char[out["deadKey"]] == cell[1], f"{stem}/{key['id']}: dead key char differs between keys")
                elif len(out) == 1 and ord(out) <= 0xFFFF:
                    check(cell == out, f"{stem}/{key['id']}/{level}: {cell!r} != {out!r}")
                else:
                    check(cell is None, f"{stem}/{key['id']}/{level}: unrepresentable output must be -1")
        for dk in manifest.get("deadKeys", []):
            ch = dead_char.get(dk["id"])
            if ch is None:
                continue
            block = doc["dead"].get(ch)
            check(block is not None, f"{stem}: DEADKEY {dk['id']} missing")
            if block is None:
                continue
            expected = {b: r for b, r in dk["compositions"].items() if len(b) == 1 and len(r) == 1 and ord(r) <= 0xFFFF}
            got = {b: r for b, r in block.items() if b != " " or " " in expected}
            check(got == expected, f"{stem}: DEADKEY {dk['id']} compositions differ ({len(got)} vs {len(expected)})")
            check(block.get(" ") in (ch, expected.get(" ")), f"{stem}: DEADKEY {dk['id']} space entry")
        golden = ROOT / "examples" / "exports" / "klc" / f"{stem}.klc"
        check(golden.exists() and golden.read_bytes() == blob, f"{stem}: golden missing or different")
        golden_report = ROOT / "examples" / "exports" / "klc" / f"{stem}.klc.report.json"
        check(golden_report.exists() and json.loads(golden_report.read_text(encoding="utf-8")) == report, f"{stem}: golden report")
    check(exported == 6, f"expected 6 exported examples, got {exported}")

    base = load_manifest(ROOT / "examples" / "azerty-global.oklm.json")
    grouped = copy.deepcopy(base)
    grouped["keys"][0]["groups"] = {"2": {"1": "b"}}
    blob, report = klc.export(grouped)
    check(blob is None and report["compatibilityLevel"] == "failed", "groups must be rejected")
    ligature = copy.deepcopy(base)
    ligature["keys"][0]["levels"]["3"] = "ij"
    blob, report = klc.export(ligature)
    check(blob is not None and any("ligature" in m["detail"] for m in report["lossyMappings"]), "ligature must be reported as lossy")
    nodisplay = copy.deepcopy(base)
    nodisplay["deadKeys"][0]["display"] = None
    nodisplay["deadKeys"][0].pop("display")
    blob, report = klc.export(nodisplay)
    check(blob is not None, "dead key without standalone character still exports")
    odd = copy.deepcopy(base)
    odd["keys"][1]["hid"] = "0x99"
    blob, report = klc.export(odd)
    check(blob is None and report["compatibilityLevel"] == "failed", "unknown HID must fail")

    if failures:
        print(f"FAILED ({len(failures)} problem(s) over {counter['n']} checks):")
        for f in failures[:30]:
            print("  -", f)
        return 1
    print(f"OK: {exported} .klc files, {counter['n']} checks passed, 0 failed.")
    return 0


def klc_qualifiers(level):
    return {"1": [], "2": ["Level2Shift"], "3": ["Level3Shift"], "4": ["Level2Shift", "Level3Shift"]}[level]


if __name__ == "__main__":
    sys.exit(main())
