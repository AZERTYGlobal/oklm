# -*- coding: utf-8 -*-
"""Dead keys across the exporters (audit 2026-10-09: B-06, B-18, B-19; B-05 is added with its fix).

    python tools/tests/test_exports_deadkeys.py

The standalone character of a dead key (what is typed when the sequence does not compose) follows one
policy in keylayout and klc: `fallback`, else `display`, else a built-in table by dead-key id
(common.DEAD_KEY_STANDALONE).
"""
import re
import sys

from test_exports_support import check, examples, finish, keylayout, klc, minimal, parse_xml, xkb
from test_klc import parse as parse_klc
from exporters.common import standalone_char


def main():
    # policy order
    check(standalone_char({"id": "acute", "fallback": "A", "display": "B"}) == ("A", "fallback"), "fallback comes first")
    check(standalone_char({"id": "acute", "display": "B"}) == ("B", "display"), "display comes second")
    check(standalone_char({"id": "acute"}) == ("´", "default"), "the table comes third")
    check(standalone_char({"id": "unknown-kind"}) == (None, None), "an unknown id has no standalone character")

    for stem, manifest in examples():
        blob, report = klc.export(manifest, source_file="x")
        doc = parse_klc(blob)
        private = [m for m in report["lossyMappings"] if "private-use" in m["detail"]]
        # B-06: a private-use name (typed after a dead key that does not compose) only when the dead key
        # has no standalone character at all, or shares it with another dead key already named by it
        expected, taken = [], set()
        for dk in manifest.get("deadKeys", []):
            char, _ = standalone_char(dk)
            if char is None or char in taken:
                expected.append(dk["id"])
            else:
                taken.add(char)
        check(sorted(m["path"] for m in private) == sorted(f"deadKeys[{i}]" for i in expected),
              f"{stem}: private-use names for {[m['path'] for m in private]}, expected {expected}")
        for char in doc["dead"]:
            check(not (0xE000 <= ord(char) <= 0xF8FF) or private, f"{stem}: private-use DEADKEY without a lossy mapping")

    # B-19: the same character in the DEADKEY name (klc) and in the terminator (keylayout)
    manifest = minimal()
    circumflex = next(d for d in manifest["deadKeys"] if d["id"] == "circumflex")
    check("fallback" in circumflex and "display" in circumflex and circumflex["fallback"] != circumflex["display"],
          "fixture assumption: the minimal manifest's circumflex has a fallback different from its display")
    names = set(parse_klc(klc.export(manifest, source_file="x")[0])["dead"])
    root = parse_xml(keylayout.export(manifest, source_file="x")[0], "minimal/keylayout")
    terminators = {w.get("state"): w.get("output") for w in root.find("terminators")}
    check(circumflex["fallback"] in names and circumflex["display"] not in names, f"klc names the DEADKEY by the fallback, got {sorted(names)}")
    check(terminators["circumflex"] == circumflex["fallback"], "keylayout terminator is the fallback")

    # B-05: a dead key id in no table gets a spare dead_* carrier (declared lossy), its rules reach the .XCompose
    manifest = minimal()
    for index, dead_id in enumerate(("zz-one", "zz-two")):
        manifest["deadKeys"].append({"id": dead_id, "compositions": {"a": f"à{index}"}})
        manifest["keys"][index]["levels"]["3"] = {"deadKey": dead_id}
    text, report = xkb.export(manifest, source_file="x")
    dead_map = xkb.dead_keysym_map(manifest)
    check(dead_map["zz-one"] != dead_map["zz-two"] and dead_map["zz-one"] in xkb.SPARE_CARRIERS, f"spare carriers: {dead_map}")
    check(dead_map["zz-one"] not in xkb.DEAD_KEYSYMS.values(), "a spare carrier is not one of the table's keysyms")
    check(dead_map["zz-one"] in text and dead_map["zz-two"] in text, "xkb: both unknown dead keys appear in the symbols")
    check(any(m["path"] == "deadKeys[zz-one]" and dead_map["zz-one"] in m["detail"] for m in report["lossyMappings"]), "the spare carrier is declared lossy")
    check(not any(s["path"].startswith("deadKeys[zz") for s in report["skippedFields"]), "an unknown dead key is not skipped while carriers remain")
    compose = xkb.export_compose(manifest, source_file="x")
    check(f'<{dead_map["zz-one"]}> <a> : "à0"' in compose, "the .XCompose has the unknown dead key's rule")

    # B-18: the KBD short name is unique and valid (8 characters at most, letters and digits)
    ids = [stem for stem, _ in examples()] + ["azerty-global-v2", "azerty-global-minimal-2", "a", "x-y-z", "", "BÉPO"]
    shorts = {layout_id: klc.short_name(layout_id) for layout_id in ids}
    check(len(set(shorts.values())) == len(ids), f"short names collide: {shorts}")
    check(all(re.fullmatch(r"[a-z0-9]{1,8}", v) for v in shorts.values()), f"invalid short name in {shorts}")
    check(shorts["azerty-global"] != shorts["azerty-global-minimal"], "azerty-global and azerty-global-minimal share a KBD name")
    return finish("dead keys")


if __name__ == "__main__":
    sys.exit(main())
