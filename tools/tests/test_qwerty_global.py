# -*- coding: utf-8 -*-
"""Tests of the QWERTY Global build (tools/qwerty_global.py). Plain assertions, exit code 0/1.

    python tools/tests/test_qwerty_global.py [--sources <dossier des sources QWERTY Global>]

Checks: every committed manifest equals a fresh composition; manifests are valid in strict mode,
without `groups`; each exports to LDML, xkb and keylayout; composition is deterministic; a module
diff is minimal (no key identical to the chassis); an invalid diff or header is an error (unknown key,
unknown removal, missing header field); build writes nothing when a problem exists; check reports
orphan manifests and duplicate layoutId; import validates before writing.

Parity with the source data (composed manifests == direct conversion of the site data, key by key) is
optional: the sources are not in this repository. Point OKLM_QWERTY_SOURCES (or --sources) at the
folder holding the files listed in SOURCE_FILES; without it the parity part prints "SKIPPED (...)".
"""
import argparse
import copy
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "validators"))

import qwerty_global as qg  # noqa: E402
from exporters import keylayout, ldml, xkb  # noqa: E402
from exporters.common import load_manifest  # noqa: E402
from validate import analyze, load_validator  # noqa: E402

SOURCES_ENV = "OKLM_QWERTY_SOURCES"
# Relative paths of the source data inside the folder named by OKLM_QWERTY_SOURCES.
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


def raises(fn, *args):
    try:
        fn(*args)
    except qg.QwertyGlobalError:
        return True
    return False


def negative_diff_tests(chassis, files):
    """E-07: an unknown key or removal in a diff is an error, never silently dropped."""
    base = qg.load_json(files[0])

    def broken(mutate):
        mf = copy.deepcopy(base)
        mutate(mf)
        return mf

    key = {"id": "Z99", "hid": "0x04", "xkb": "AC01", "code": "KeyA", "levels": {"1": "a"}}
    check(raises(qg.compose, chassis, broken(lambda m: m["diff"]["setKeys"].append(key))),
          "negative: unknown key id in setKeys must raise")
    check(raises(qg.compose, chassis, broken(lambda m: m["diff"]["removeKeys"].append("Z99"))),
          "negative: unknown key in removeKeys must raise")
    check(raises(qg.compose, chassis, broken(lambda m: m["diff"]["removeDeadKeys"].append("no-such-dead-key"))),
          "negative: unknown dead key in removeDeadKeys must raise")
    check(raises(qg.compose, chassis, broken(lambda m: m["diff"]["removeFingers"].append("Z99"))),
          "negative: unknown finger in removeFingers must raise")
    check(raises(qg.compose, chassis, broken(lambda m: m["diff"]["fingers"].update({"Z99": "L1"}))),
          "negative: finger on an unknown position must raise")
    check(raises(qg.compose, chassis, broken(lambda m: m["diff"].update({"surprise": []}))),
          "negative: unknown diff field must raise")
    check(raises(qg.compose, chassis, broken(lambda m: m["diff"].pop("removeKeys"))),
          "negative: missing diff field must raise")
    check(raises(qg.compose, chassis, broken(lambda m: m["manifest"].pop("note"))),
          "negative: missing header field must raise")
    check(raises(qg.convert_source, {"rows": [{"keys": [{"position": "Z99", "scancode": "SC002"}]}]}),
          "negative: unknown source position must raise")
    check(raises(qg.convert_source, {"rows": [{"keys": [{"position": "E01", "scancode": "SC999"}]}]}),
          "negative: unknown source scancode must raise")
    check(raises(qg.convert_source, {"rows": [{"keys": [{"position": "E01", "scancode": "SC003"}]}]}),
          "negative: scancode/position mismatch must raise")


def snapshot(folder):
    return {p.name: p.read_bytes() for p in sorted(Path(folder).glob("*.json")) if p.is_file()}


def isolated_build_tests():
    """E-08, on a temporary copy of qwerty-global/ (the repository is never written)."""
    real = qg.QG
    with tempfile.TemporaryDirectory() as tmp:
        qg.QG = Path(tmp) / "qwerty-global"
        try:
            shutil.copytree(real, qg.QG)
            manifests, modules = qg.QG / "manifests", qg.QG / "modules"

            check(qg.build(check=True) == 0, "isolated copy: check should pass")

            # an orphan manifest fails check
            orphan = manifests / "qwerty-global-gone.oklm.json"
            orphan.write_bytes(b"{}\n")
            check(qg.build(check=True) == 1, "check: orphan manifest not reported")
            check(qg.build(check=False) == 0 and orphan.exists(), "build: an orphan is a warning, never deleted")
            orphan.unlink()

            # a problem in one module: build writes nothing (not even the valid modules)
            before = snapshot(manifests)
            fr = qg.load_json(modules / "fr.json")
            fr["manifest"]["layoutId"] = "Not A Kebab"
            qg.dump_json(modules / "fr.json", fr)
            stale = manifests / "qwerty-global-base.oklm.json"
            stale.write_bytes(stale.read_bytes() + b" ")  # would be rewritten if build wrote anything
            tampered = snapshot(manifests)
            check(qg.build(check=False) == 1, "build: invalid module must fail")
            check(snapshot(manifests) == tampered, "build: wrote files despite a problem")
            stale.write_bytes(before[stale.name])

            # duplicate layoutId: check fails and build writes nothing
            fr["manifest"]["layoutId"] = "qwerty-global-it"
            qg.dump_json(modules / "fr.json", fr)
            check(qg.build(check=True) == 1, "check: duplicate layoutId not reported")
            check(qg.build(check=False) == 1 and snapshot(manifests) == before, "build: duplicate layoutId wrote files")
            qg.dump_json(modules / "fr.json", qg.load_json(real / "modules" / "fr.json"))

            # a module whose `module` field differs from its file name
            it = qg.load_json(modules / "it.json")
            it["module"] = "xx"
            qg.dump_json(modules / "it.json", it)
            check(qg.build(check=True) == 1, "check: module/file name mismatch not reported")
            qg.dump_json(modules / "it.json", qg.load_json(real / "modules" / "it.json"))
            check(qg.build(check=True) == 0, "isolated copy: restored copy should pass again")

            # import validates everything before writing the chassis
            source = Path(tmp) / "source.json"
            source.write_text(json.dumps({"rows": [{"keys": [
                {"position": "E01", "scancode": "SC002", "base": "1", "shift": "!", "finger": "L4"}]}]}),
                encoding="utf-8")
            chassis_before, fr_before = (qg.QG / "chassis.json").read_bytes(), (modules / "fr.json").read_bytes()
            args = type("Args", (), {"chassis": str(source), "module": [("fr", str(source)), ("nope", str(source))]})
            check(raises(qg.import_sources, args), "import: a missing module file must raise")
            check((qg.QG / "chassis.json").read_bytes() == chassis_before, "import: chassis written before validation")
            check((modules / "fr.json").read_bytes() == fr_before, "import: module written before validation")
            headerless = qg.load_json(modules / "fr.json")
            del headerless["manifest"]["note"]
            qg.dump_json(modules / "fr.json", headerless)
            fr_before = (modules / "fr.json").read_bytes()
            args.module = [("fr", str(source))]
            check(raises(qg.import_sources, args), "import: an incomplete header must raise")
            check((qg.QG / "chassis.json").read_bytes() == chassis_before, "import: chassis written despite bad header")
            check((modules / "fr.json").read_bytes() == fr_before, "import: module written despite bad header")
            qg.dump_json(modules / "fr.json", qg.load_json(real / "modules" / "fr.json"))
            check(qg.import_sources(args) == 0, "import: valid import should succeed")
            check(qg.read_chassis()[0].keys() == {"E01"}, "import: chassis not rewritten from the source")
        finally:
            qg.QG = real


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default=os.environ.get(SOURCES_ENV),
                    help=f"folder of the QWERTY Global source data (default: ${SOURCES_ENV}; unset = parity skipped)")
    args = ap.parse_args(argv)
    sources = Path(args.sources) if args.sources else None

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

    negative_diff_tests(chassis, files)
    with contextlib.redirect_stdout(io.StringIO()):  # build/check are chatty by design
        isolated_build_tests()

    # parity with the source data, only when explicitly requested
    parity_note = None
    if sources is None:
        parity_note = f"SKIPPED (parity with the source data: {SOURCES_ENV} is not set)"
    else:
        absent = [rel for rel in SOURCE_FILES.values() if not (sources / rel).exists()]
        check(not absent, f"parity: {SOURCES_ENV}={sources} lacks {absent}")
        if absent:
            parity_note = "FAILED (source files missing)"
    if parity_note is None:
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
        print(parity_note)

    if failures:
        print(f"FAILED ({len(failures)} problem(s) over {counter['n']} checks):")
        for f in failures[:40]:
            print("  -", f)
        return 1
    print(f"OK: 3 QWERTY Global manifests, {counter['n']} checks passed, 0 failed"
          f"{'' if parity_note is None else ' (parity ' + parity_note.split(' (')[0].lower() + ')'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
