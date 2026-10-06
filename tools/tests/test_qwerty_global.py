# -*- coding: utf-8 -*-
"""Tests of the QWERTY Global build (tools/qwerty_global.py). Plain assertions, exit code 0/1.

    python tools/tests/test_qwerty_global.py [--sources "D:/.../projects/qwerty-global"]

Checks: every committed manifest equals a fresh composition; manifests are valid in strict mode,
without `groups`; each exports to LDML, xkb and keylayout; composition is deterministic; a module
diff is minimal (no key identical to the chassis); and, when the QWERTY Global source data is
reachable, the composed manifests equal a direct conversion of that data, key by key.
"""
import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "validators"))

import qwerty_global as qg  # noqa: E402
from exporters import keylayout, ldml, xkb  # noqa: E402
from exporters.common import load_manifest  # noqa: E402
from validate import analyze, load_validator  # noqa: E402

DEFAULT_SOURCES = Path("D:/My files/Keyboard Layouts/projects/qwerty-global")
SOURCE_FILES = {
    "base": "components/layout-data/QWERTY World Base.json",
    "fr": "components/french-website/data/QWERTY Francais.json",
    "it": "sources/legacy/QWERTY Global/Italian/Italian.json",
}
failures, counter = [], {"n": 0}


def check(condition, message):
    counter["n"] += 1
    if not condition:
        failures.append(message)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default=str(DEFAULT_SOURCES))
    args = ap.parse_args(argv)
    sources = Path(args.sources)

    chassis = qg.read_chassis()
    files = qg.module_files()
    check(len(files) == 3, f"expected 3 modules, found {len(files)}")
    report_validator = load_validator("oklm-conversion-report.schema.json")

    check(qg.build(check=True) == 0, "committed manifests differ from a fresh composition")

    composed = {}
    for path in files:
        mf = qg.load_json(path)
        mid = mf["module"]
        manifest = qg.compose(chassis, mf)
        composed[mid] = manifest
        check(json.dumps(qg.compose(chassis, mf)) == json.dumps(manifest), f"{mid}: composition is not deterministic")
        found = analyze(manifest, strict=True)
        check(not found, f"{mid}: strict findings {[str(f) for f in found]}")
        check(all("groups" not in k for k in manifest["keys"]), f"{mid}: uses reserved `groups`")
        check(len({k["id"] for k in manifest["keys"]}) == len(manifest["keys"]), f"{mid}: duplicate key id")
        stale = [k["id"] for k in mf["diff"]["setKeys"] if chassis[0].get(k["id"]) == k]
        check(not stale, f"{mid}: diff keeps keys identical to the chassis: {stale}")
        path_manifest = qg.QG / "manifests" / f"{manifest['layoutId']}.oklm.json"
        loaded = load_manifest(path_manifest)
        for target, module in (("ldml", ldml), ("xkb", xkb), ("keylayout", keylayout)):
            text, report = module.export(loaded, source_file=path_manifest.name)
            check(text is not None, f"{mid}/{target}: export failed: {report.get('errors')}")
            check(not list(report_validator.iter_errors(report)), f"{mid}/{target}: report invalid")

    # a removed chassis key and an added module key survive composition
    check("C12" not in {k["id"] for k in composed["fr"]["keys"]}, "fr: chassis key C12 should be removed")
    check("B00" in {k["id"] for k in composed["fr"]["keys"]}, "fr: module key B00 should be present")
    check(composed["base"]["keys"] == [chassis[0][p] for p in qg.ORDER if p in chassis[0]], "base: empty diff must keep the chassis keys")

    # a broken diff is caught: an unknown dead key reference fails the validator
    broken = copy.deepcopy(qg.load_json(files[0]))
    broken["diff"]["setKeys"].append({"id": "E01", "hid": "0x1E", "xkb": "AE01", "code": "Digit1",
                                      "levels": {"1": {"deadKey": "does-not-exist"}}})
    found = analyze(qg.compose(chassis, broken), strict=True)
    check(any(f.code == "E_DEADKEY_UNDEFINED" for f in found), "negative: undefined dead key not detected")

    # parity with the source data, when reachable
    reachable = all((sources / rel).exists() for rel in SOURCE_FILES.values())
    if reachable:
        for mid, rel in SOURCE_FILES.items():
            keys, dead, fingers = qg.convert_source(qg.load_json(sources / rel))
            manifest = composed[mid]
            got = {k["id"]: k for k in manifest["keys"]}
            check(set(got) == set(keys), f"parity {mid}: key set differs {sorted(set(got) ^ set(keys))}")
            for pos, k in keys.items():
                check(got.get(pos) == k, f"parity {mid}/{pos}: key differs from the source data")
            got_dead = {d["id"]: d for d in manifest.get("deadKeys", [])}
            check(got_dead == dict(dead), f"parity {mid}: dead keys differ from the source data")
            check(manifest["metadata"]["training"]["fingers"] == dict(fingers), f"parity {mid}: fingers differ")
    else:
        print("NOTE: QWERTY Global source data not reachable, parity checks skipped")

    if failures:
        print(f"FAILED ({len(failures)} problem(s) over {counter['n']} checks):")
        for f in failures[:40]:
            print("  -", f)
        return 1
    print(f"OK: 3 QWERTY Global manifests, {counter['n']} checks passed, 0 failed"
          f"{'' if reachable else ' (parity skipped)'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
