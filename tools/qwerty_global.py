# -*- coding: utf-8 -*-
"""QWERTY Global : manifestes OKLM generes depuis un chassis commun et un diff par module.

Decision de cadrage C4 (2026-09-21) : un manifeste par module, compose au build ;
`keys[].groups` reste inutilise. Les entrees versionnees sont :

    qwerty-global/chassis.json          touches, touches mortes et doigts du chassis commun
    qwerty-global/modules/<id>.json     en-tete du manifeste + diff contre le chassis

et la sortie est `qwerty-global/manifests/<layoutId>.oklm.json`.

Sous-commandes :
    import  <id> <source.json> ...   (re)calcule chassis et diffs depuis les JSON du site
                                     (format interne QWERTY Global, lecture seule)
    build                            compose les manifestes depuis chassis + diffs
    check                            echoue si un manifeste versionne differe d'une recomposition

    python tools/qwerty_global.py import --chassis "QWERTY World Base.json" \
        --module fr "QWERTY Francais.json" --module it "Italian.json"
    python tools/qwerty_global.py build
"""
import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "validators"))

from convert_site_to_oklm import (  # noqa: E402
    LEVEL_MAP, LEVEL_SELECTORS, POSITION_TABLE, SCANCODE_TO_HID, convert_output, dead_key_id)
from migrate_0_1_to_0_2 import semver_of  # noqa: E402

QG = ROOT / "qwerty-global"
ORDER = list(POSITION_TABLE)
CONVENTION_FALLBACK = {"caps_alt_gr": "alt_gr", "caps_shift_alt_gr": "shift_alt_gr"}
ISO_GRID_NOTE =("Key reference grid used for canonical key identifiers.")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=OrderedDict)


def dump_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes((json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def convert_source(src):
    """Format interne du site -> (keys par id, touches mortes par id, doigts par id)."""
    keys, fingers = OrderedDict(), OrderedDict()
    conventions = src.get("conventions", {})
    for row in src["rows"]:
        for k in row["keys"]:
            pos = k["position"]
            hid, xkb, code = POSITION_TABLE[pos]
            if SCANCODE_TO_HID[k["scancode"]] != hid:
                raise SystemExit(f"Incoherence {pos}: scancode {k['scancode']} et position ne donnent pas le meme HID")
            levels = OrderedDict()
            for field, level in LEVEL_MAP:
                value = k.get(field)
                if not value and field in CONVENTION_FALLBACK and field in conventions:
                    # The source documents "if absent, use the alt_gr value": E21 would otherwise drop it.
                    value = k.get(CONVENTION_FALLBACK[field])
                if value:
                    levels[level] = convert_output(value)
            keys[pos] = OrderedDict([("id", pos), ("hid", hid), ("xkb", xkb), ("code", code), ("levels", levels)])
            if k.get("finger"):
                fingers[pos] = k["finger"]
    dead = OrderedDict()
    for raw_id, entry in src.get("dead_keys", {}).items():
        item = OrderedDict([("id", dead_key_id(raw_id))])
        if entry.get("description"):
            item["name"] = entry["description"]
        item["compositions"] = OrderedDict(entry["table"])
        dead[item["id"]] = item
    return keys, dead, fingers


def diff_against(chassis, module):
    """Diff d'un module (keys, dead, fingers) contre le chassis (memes structures)."""
    c_keys, c_dead, c_fingers = chassis
    m_keys, m_dead, m_fingers = module
    d = OrderedDict()
    d["removeKeys"] = [p for p in c_keys if p not in m_keys]
    d["setKeys"] = [m_keys[p] for p in ORDER if p in m_keys and m_keys[p] != c_keys.get(p)]
    d["removeDeadKeys"] = [i for i in c_dead if i not in m_dead]
    d["setDeadKeys"] = [m_dead[i] for i in m_dead if m_dead[i] != c_dead.get(i)]
    d["fingers"] = OrderedDict((p, f) for p, f in m_fingers.items() if c_fingers.get(p) != f)
    d["removeFingers"] = [p for p in c_fingers if p not in m_fingers]
    return d


def apply_diff(chassis, diff):
    c_keys, c_dead, c_fingers = chassis
    keys = OrderedDict((p, v) for p, v in c_keys.items() if p not in diff["removeKeys"])
    for k in diff["setKeys"]:
        keys[k["id"]] = k
    dead = OrderedDict((i, v) for i, v in c_dead.items() if i not in diff["removeDeadKeys"])
    for item in diff["setDeadKeys"]:
        dead[item["id"]] = item
    fingers = OrderedDict((p, f) for p, f in c_fingers.items() if p not in diff["removeFingers"])
    fingers.update(diff["fingers"])
    return keys, dead, fingers


def read_chassis():
    c = load_json(QG / "chassis.json")
    keys = OrderedDict((k["id"], k) for k in c["keys"])
    dead = OrderedDict((d["id"], d) for d in c["deadKeys"])
    return keys, dead, c["fingers"]


def compose(chassis, module_file):
    """Manifeste OKLM 0.2 d'un module : chassis + diff + en-tete."""
    head = module_file["manifest"]
    keys, dead, fingers = apply_diff(chassis, module_file["diff"])
    ordered = [keys[p] for p in ORDER if p in keys]
    used = {lv for k in ordered for lv in k["levels"]}
    selectors = OrderedDict((lv, LEVEL_SELECTORS[lv]) for lv in sorted(used) if lv != "1")
    version, label = semver_of(head["version"])
    metadata = OrderedDict([("description", head["note"])])
    if label:
        metadata["versionLabel"] = label
    if head.get("links"):
        metadata["links"] = head["links"]
    metadata["training"] = OrderedDict(fingers=OrderedDict((p, fingers[p]) for p in ORDER if p in fingers))
    description = (f"OKLM description of {head['summary']} ({len(ordered)} graphic keys, {len(used)} levels, "
                   f"{len(dead)} dead keys), composed at build time from the QWERTY Global chassis and the "
                   f"'{module_file['module']}' module diff. Frame keys (function row, navigation, numpad) are "
                   "out of the draft 0.2 core.")
    manifest = OrderedDict([
        ("schemaVersion", "0.2"),
        ("layoutId", head["layoutId"]),
        ("name", head["name"]),
        ("version", version),
        ("license", head["license"]),
        ("authors", head["authors"]),
        ("description", description),
        ("locales", head["locales"]),
        ("geometry", head["geometry"]),
        ("levelSelectors", selectors),
        ("keys", ordered),
    ])
    if dead:
        manifest["deadKeys"] = list(dead.values())
    manifest["conformance"] = [OrderedDict([("reference", "ISO/IEC 9995-1:2026"), ("scope", ISO_GRID_NOTE),
        ("notes", "Key reference grid unchanged since the 2009 edition; the 2026 text was not read.")])]
    manifest["exports"] = [
        OrderedDict([("target", "ldml-keyboard-3"), ("id", "ldml"), ("options", {"conformsTo": 45})]),
        OrderedDict([("target", "web-tester"), ("id", "web")]),
    ]
    manifest["metadata"] = metadata
    return manifest


def module_files():
    return sorted((QG / "modules").glob("*.json"))


def build(check=False):
    chassis = read_chassis()
    problems, written = [], 0
    from validate import analyze
    for path in module_files():
        mf = load_json(path)
        manifest = compose(chassis, mf)
        errors = [str(f) for f in analyze(manifest, strict=True) if f.severity == "error"]
        warnings = [str(f) for f in analyze(manifest, strict=True) if f.severity != "error"]
        out = QG / "manifests" / f"{manifest['layoutId']}.oklm.json"
        text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        if errors or warnings:
            problems.append(f"{out.name}: {errors + warnings}")
        if check:
            if not out.exists() or out.read_bytes() != text.encode("utf-8"):
                problems.append(f"{out.name}: differs from a fresh composition")
        else:
            dump_json(out, manifest)
            written += 1
            print(f"OK  {out.name}: {len(manifest['keys'])} keys, {len(manifest.get('deadKeys', []))} dead keys")
    for p in problems:
        print("PROBLEM", p)
    return 1 if problems else 0


def import_sources(args):
    chassis_src = convert_source(load_json(args.chassis))
    dump_json(QG / "chassis.json", OrderedDict([
        ("description", "Common QWERTY Global chassis, converted from the protected 'QWERTY World Base' data. "
                        "Regenerate with tools/qwerty_global.py import."),
        ("keys", list(chassis_src[0].values())),
        ("deadKeys", list(chassis_src[1].values())),
        ("fingers", chassis_src[2]),
    ]))
    for module_id, source in args.module:
        diff = diff_against(chassis_src, convert_source(load_json(source)))
        path = QG / "modules" / f"{module_id}.json"
        existing = load_json(path) if path.exists() else None
        if existing is None:
            raise SystemExit(f"{path} is missing: write its 'manifest' header first, then re-run import")
        existing["diff"] = diff
        dump_json(path, existing)
        print(f"OK  {module_id}: {len(diff['setKeys'])} keys set, {len(diff['removeKeys'])} removed, "
              f"{len(diff['setDeadKeys'])} dead keys set")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    imp = sub.add_parser("import")
    imp.add_argument("--chassis", required=True)
    imp.add_argument("--module", nargs=2, action="append", metavar=("ID", "SOURCE"), default=[])
    sub.add_parser("build")
    sub.add_parser("check")
    args = p.parse_args(argv)
    if args.cmd == "import":
        return import_sources(args)
    return build(check=(args.cmd == "check"))


if __name__ == "__main__":
    sys.exit(main())
