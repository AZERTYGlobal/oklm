# -*- coding: utf-8 -*-
"""CapsLock levels (5-8) a key does not define: audit 2026-10-09, B-02. Exit code 0/1.

    python tools/tests/test_exports_caps.py

Decision: an absent CapsLock level reads as the matching level without CapsLock (5 -> 1, 6 -> 2,
7 -> 3, 8 -> 4). keylayout and LDML copy the output into the CapsLock layer, .klc reads it as
"CapsLock has no effect" (Cap column 0), xkb exports levels 1-4 only.
"""
import sys

from test_exports_support import check, examples, finish, keylayout, klc, ldml, minimal, parse_xml
from exporters.common import caps_base_levels, effective_output, resolve_level_modifiers

CAPS_SELECTORS = {"5": ["CapsLock"], "6": ["CapsLock", "Level2Shift"], "7": ["CapsLock", "Level3Shift"],
                  "8": ["CapsLock", "Level2Shift", "Level3Shift"]}


def keymaps(root):
    """keyMap index -> {key code: output or action}; keyMap index -> modifier keys string."""
    maps = {km.get("index"): {k.get("code"): k.get("output") or k.get("action") for k in km.iter("key")}
            for km in root.iter("keyMap")}
    modifiers = {s.get("mapIndex"): s.find("modifier").get("keys") for s in root.iter("keyMapSelect")}
    return maps, modifiers


def klc_cap_column(manifest, key):
    """The Cap column of the key's row in the .klc."""
    blob, _ = klc.export(manifest, source_file="x")
    scan = ldml.HID_TO_SCANCODE1[key["hid"]]
    for line in blob[2:].decode("utf-16-le").split("\r\n"):
        cells = line.split("\t")
        if len(cells) > 5 and cells[0] == scan:
            return cells[3]
    return None


def main():
    resolved = resolve_level_modifiers({"levelSelectors": CAPS_SELECTORS})
    check(caps_base_levels(resolved) == {"5": "1", "6": "2", "7": "3", "8": "4"}, "caps_base_levels: 5->1, 6->2, 7->3, 8->4")
    check(caps_base_levels({"5": ["Level5Shift"]}) == {}, "a level without CapsLock has no caps base")
    levels = {"1": "a", "2": "A", "6": "!"}
    base = {"5": "1", "6": "2"}
    check(effective_output(levels, "5", base) == ("a", True), "level 5 absent: level 1")
    check(effective_output(levels, "6", base) == ("!", False), "level 6 defined: kept")
    check(effective_output(levels, "7", base) == (None, False), "level 7 without declared base: still absent")

    for stem, manifest in examples():
        resolved = resolve_level_modifiers(manifest)
        if not any("CapsLock" in q for q in resolved.values()):
            continue
        # keylayout: every code of a keyMap has the same code in the matching CapsLock keyMap
        text, report = keylayout.export(manifest, source_file="x")
        maps, modifiers = keymaps(parse_xml(text, f"{stem}/keylayout"))
        by_modifiers = {frozenset(value.split()): index for index, value in modifiers.items()}
        caps_maps = [(index, frozenset(value.split()) - {"caps"}) for index, value in modifiers.items() if "caps" in value.split()]
        check(caps_maps, f"{stem}/keylayout: no CapsLock keyMap")
        for index, rest in caps_maps:
            missing = set(maps[by_modifiers[rest]]) - set(maps[index])
            check(not missing, f"{stem}/keylayout: CapsLock keyMap {index} lacks codes {sorted(missing)} present without CapsLock")
        check(any("CapsLock levels a key does not define" in w for w in report["warnings"]),
              f"{stem}/keylayout: the CapsLock fallback is not declared in the report")
        # LDML: no gap in a CapsLock layer where the matching layer has a key
        text, _ = ldml.export(manifest, source_file="x")
        layers = {l.get("modifiers"): [r.get("keys").split() for r in l.iter("row")] for l in parse_xml(text, f"{stem}/ldml").iter("layer")}
        for value, rows in layers.items():
            if "caps" not in value.split():
                continue
            rest = " ".join(t for t in value.split() if t != "caps") or "none"
            for caps_row, base_row in zip(rows, layers[rest]):
                for caps_cell, base_cell in zip(caps_row, base_row):
                    check(not (caps_cell == "gap" and base_cell != "gap"), f"{stem}/ldml: layer '{value}' has a gap where '{rest}' has {base_cell}")

    # synthetic manifest: a letter with no level 5, another with an explicit level 5, the same under .klc
    manifest = minimal()
    manifest["levelSelectors"] = CAPS_SELECTORS
    letters = [k for k in manifest["keys"] if isinstance(k["levels"].get("1"), str) and k["levels"]["1"].isalpha()]
    plain, explicit = letters[0], letters[1]
    plain["levels"].pop("5", None)
    plain["levels"]["6"] = "Ä"
    explicit["levels"]["5"] = "Q"
    outputs = {k.get("id"): k.get("output") for k in parse_xml(ldml.export(manifest, source_file="x")[0], "synthetic/ldml").iter("key")}
    check(outputs[f"k_{plain['id']}_5"] == outputs[f"k_{plain['id']}_1"], "ldml: absent level 5 copies level 1")
    check(outputs[f"k_{plain['id']}_6"] == "Ä", "ldml: explicit level 6 is kept")
    check(outputs[f"k_{explicit['id']}_5"] == "Q", "ldml: explicit level 5 is kept")
    check(klc_cap_column(manifest, plain) == "0", ".klc: absent CapsLock level reads as no effect (Cap column 0)")
    return finish("CapsLock fallback (B-02)")


if __name__ == "__main__":
    sys.exit(main())
