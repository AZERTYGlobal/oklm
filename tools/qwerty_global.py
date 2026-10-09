# -*- coding: utf-8 -*-
# SPDX-License-Identifier: EUPL-1.2
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
import re
import sys
from collections import OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "validators"))

from oklm_keyboard_tables import (  # noqa: E402
    LEVEL_MAP, LEVEL_SELECTORS, POSITION_TABLE, SCANCODE_TO_HID, convert_output, dead_key_id)
from migrate_0_1_to_0_2 import semver_of  # noqa: E402

QG = ROOT / "qwerty-global"
ORDER = list(POSITION_TABLE)
CONVENTION_FALLBACK = {"caps_alt_gr": "alt_gr", "caps_shift_alt_gr": "shift_alt_gr"}
ISO_GRID_NOTE = "Key reference grid used for canonical key identifiers."
MANIFEST_FIELDS = ("layoutId", "name", "version", "license", "authors", "locales", "geometry", "summary", "note")
DIFF_FIELDS = ("removeKeys", "setKeys", "removeDeadKeys", "setDeadKeys", "fingers", "removeFingers")
MODULE_ID = re.compile(r"[a-z0-9][a-z0-9-]*")


class QwertyGlobalError(ValueError):
    """Donnee invalide (source, diff, en-tete de module) : rien n'est ecrit."""


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
            if pos not in POSITION_TABLE:
                raise QwertyGlobalError(f"source: position inconnue {pos!r}")
            if pos in keys:
                raise QwertyGlobalError(f"source: position {pos} en double")
            hid, xkb, code = POSITION_TABLE[pos]
            if k["scancode"] not in SCANCODE_TO_HID:
                raise QwertyGlobalError(f"source: scancode inconnu {k['scancode']!r} ({pos})")
            if SCANCODE_TO_HID[k["scancode"]] != hid:
                raise QwertyGlobalError(
                    f"Incoherence {pos}: scancode {k['scancode']} et position ne donnent pas le meme HID")
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


def check_diff(chassis, diff, label="diff"):
    """Leve QwertyGlobalError si le diff ne s'applique pas proprement au chassis."""
    c_keys, c_dead, c_fingers = chassis
    if not isinstance(diff, dict):
        raise QwertyGlobalError(f"{label}: le diff n'est pas un objet")
    missing = [f for f in DIFF_FIELDS if f not in diff]
    if missing:
        raise QwertyGlobalError(f"{label}: champs de diff absents {missing}")
    unknown = sorted(set(diff) - set(DIFF_FIELDS))
    if unknown:
        raise QwertyGlobalError(f"{label}: champs de diff inconnus {unknown}")
    for field, known, what in (("removeKeys", c_keys, "touches"), ("removeDeadKeys", c_dead, "touches mortes"),
                               ("removeFingers", c_fingers, "doigts")):
        absent = [x for x in diff[field] if x not in known]
        if absent:
            raise QwertyGlobalError(f"{label}: {field} retire des {what} absentes du chassis {absent}")
    for k in diff["setKeys"]:
        if k.get("id") not in POSITION_TABLE:
            raise QwertyGlobalError(f"{label}: setKeys contient une position inconnue {k.get('id')!r}")
    unknown_fingers = [p for p in diff["fingers"] if p not in POSITION_TABLE]
    if unknown_fingers:
        raise QwertyGlobalError(f"{label}: fingers contient des positions inconnues {unknown_fingers}")
    if any(not d.get("id") for d in diff["setDeadKeys"]):
        raise QwertyGlobalError(f"{label}: setDeadKeys contient une touche morte sans id")


def apply_diff(chassis, diff, label="diff"):
    check_diff(chassis, diff, label)
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
    unknown = [p for p in keys if p not in POSITION_TABLE]
    if unknown or len(keys) != len(c["keys"]):
        raise QwertyGlobalError(f"chassis.json: positions inconnues {unknown} ou en double")
    dead = OrderedDict((d["id"], d) for d in c["deadKeys"])
    return keys, dead, c["fingers"]


def compose(chassis, module_file):
    """Manifeste OKLM 0.2 d'un module : chassis + diff + en-tete."""
    label = f"module {module_file.get('module', '?')}"
    head = module_file.get("manifest")
    if not isinstance(head, dict):
        raise QwertyGlobalError(f"{label}: en-tete 'manifest' absent")
    absent = [f for f in MANIFEST_FIELDS if f not in head]
    if absent:
        raise QwertyGlobalError(f"{label}: champs d'en-tete absents {absent}")
    if "diff" not in module_file or "module" not in module_file:
        raise QwertyGlobalError(f"{label}: champ 'module' ou 'diff' absent")
    keys, dead, fingers = apply_diff(chassis, module_file["diff"], label)
    ordered = [keys[p] for p in ORDER if p in keys]
    assert len(ordered) == len(keys)  # check_diff garantit qu'aucune cle ne disparait
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


LAYOUT_ID = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")  # meme motif que le schema : sert aussi de nom de fichier


def compose_all(chassis):
    """Compose tous les modules en memoire. Retourne (items, problems) ; ne touche pas au disque.

    items : liste de (chemin de sortie, manifeste, texte) ; problems : liste de messages.
    """
    from validate import analyze
    items, problems, seen = [], [], {}
    for path in module_files():
        try:
            mf = load_json(path)
            if mf.get("module") != path.stem:
                raise QwertyGlobalError(f"{path.name}: le champ 'module' ({mf.get('module')!r}) differe du nom du fichier")
            manifest = compose(chassis, mf)
            layout_id = manifest["layoutId"]
            if not isinstance(layout_id, str) or not LAYOUT_ID.fullmatch(layout_id):
                raise QwertyGlobalError(f"{path.name}: layoutId invalide {layout_id!r}")
        except (QwertyGlobalError, OSError, ValueError, KeyError, TypeError) as exc:
            problems.append(f"{path.name}: {type(exc).__name__}: {exc}")
            continue
        out = QG / "manifests" / f"{layout_id}.oklm.json"
        if layout_id in seen:
            problems.append(f"{path.name}: layoutId {layout_id!r} deja produit par le module {seen[layout_id]}")
            continue
        seen[layout_id] = path.name
        found = [str(f) for f in analyze(manifest, strict=True)]
        if found:
            problems.append(f"{out.name}: {found}")
        items.append((out, manifest, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"))
    return items, problems


def orphan_manifests(items):
    expected = {out.name for out, _, _ in items}
    return sorted(p.name for p in (QG / "manifests").glob("*.oklm.json") if p.name not in expected)


def build(check=False):
    """build : compose puis ecrit, seulement si tout est valide. check : compare sans ecrire."""
    chassis = read_chassis()
    items, problems = compose_all(chassis)
    orphans = orphan_manifests(items) if not problems else []  # liste peu fiable si un module n'a pas compose
    if check:
        for out, _, text in items:
            if not out.exists() or out.read_bytes() != text.encode("utf-8"):
                problems.append(f"{out.name}: differs from a fresh composition")
        problems += [f"{name}: orphan manifest, produced by no module" for name in orphans]
    else:
        for name in orphans:
            print(f"WARNING {name}: orphan manifest, produced by no module (not deleted)")
    for p in problems:
        print("PROBLEM", p)
    if problems:
        if not check:
            print("Nothing written: fix the problems above first.")
        return 1
    if check:
        print(f"OK  {len(items)} manifests identical to a fresh composition")
    else:
        for out, manifest, text in items:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            Path(out).write_bytes(text.encode("utf-8"))
            print(f"OK  {out.name}: {len(manifest['keys'])} keys, {len(manifest.get('deadKeys', []))} dead keys")
    return 0


def import_sources(args):
    """Valide tout (sources, identifiants, en-tetes, diffs recomposables) avant d'ecrire quoi que ce soit."""
    chassis_src = convert_source(load_json(args.chassis))
    ids = [module_id for module_id, _ in args.module]
    for module_id in ids:
        if not MODULE_ID.fullmatch(module_id):
            raise QwertyGlobalError(f"identifiant de module invalide {module_id!r}")
    if len(set(ids)) != len(ids):
        raise QwertyGlobalError(f"identifiants de module en double : {ids}")
    planned = []
    for module_id, source in args.module:
        path = QG / "modules" / f"{module_id}.json"
        if not path.exists():
            raise QwertyGlobalError(f"{path} is missing: write its 'manifest' header first, then re-run import")
        existing = load_json(path)
        module_src = convert_source(load_json(source))
        diff = diff_against(chassis_src, module_src)
        if apply_diff(chassis_src, diff, module_id) != module_src:
            raise QwertyGlobalError(f"{module_id}: le diff ne reconstitue pas la source")
        existing["diff"] = diff
        compose(chassis_src, existing)  # en-tete complet et manifeste composable
        planned.append((module_id, path, existing, diff))
    dump_json(QG / "chassis.json", OrderedDict([
        ("description", "Common QWERTY Global chassis, converted from the protected 'QWERTY World Base' data. "
                        "Regenerate with tools/qwerty_global.py import."),
        ("keys", list(chassis_src[0].values())),
        ("deadKeys", list(chassis_src[1].values())),
        ("fingers", chassis_src[2]),
    ]))
    for module_id, path, existing, diff in planned:
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
    try:
        if args.cmd == "import":
            return import_sources(args)
        return build(check=(args.cmd == "check"))
    except (QwertyGlobalError, OSError, ValueError, KeyError) as exc:
        print(f"ERROR {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
