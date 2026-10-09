# -*- coding: utf-8 -*-
# SPDX-License-Identifier: EUPL-1.2
"""Adversarial tests of validators/validate.py (audit 2026-10-09, axis A). Plain assertions, exit code 0/1.

    python tools/tests/test_validate.py

Each section reproduces cases of the audit harness (A-01 ... A-20, B-03, C-14 ... C-16): the manifest or
the file is built in memory or in a temporary directory, nothing is written in the repository.
"""
import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "validators"))

import validate as v  # noqa: E402

VALIDATE = ROOT / "validators" / "validate.py"
SCHEMA = v.load_schema("oklm-manifest.schema.json")
VALIDATOR = v.Draft202012Validator(SCHEMA)
BASE_PATH = ROOT / "examples" / "azerty-global-minimal.oklm.json"
BASE_TEXT = BASE_PATH.read_text(encoding="utf-8")
BASE = json.loads(BASE_TEXT)

failures, counter = [], {"n": 0}


def check(condition, message):
    counter["n"] += 1
    if not condition:
        failures.append(message)


class Root:
    """Replaces the whole document (a mutator returning None means: keep the mutated copy)."""

    def __init__(self, value):
        self.value = value


def mutated(fn):
    manifest = copy.deepcopy(BASE)
    result = fn(manifest)
    return result.value if isinstance(result, Root) else manifest


def findings(manifest, strict=False):
    return v.analyze(manifest, SCHEMA, VALIDATOR, strict=strict)


def codes(manifest, strict=False, severity=None):
    return sorted({f.code for f in findings(manifest, strict) if severity is None or f.severity == severity})


def errors(manifest, strict=False):
    return codes(manifest, strict, "error")


def cli(*args, files=None, env_drop=("PYTHONUTF8", "PYTHONIOENCODING")):
    """Run validate.py as a subprocess; stdout is a pipe (cp1252 on Windows unless the environment says otherwise)."""
    env = {k: val for k, val in os.environ.items() if k not in env_drop}
    proc = subprocess.run([sys.executable, "-B", str(VALIDATE), *args], capture_output=True, env=env, timeout=120)
    return proc.returncode, proc.stdout.decode("utf-8", "replace"), proc.stderr.decode("utf-8", "replace")


# ---------------------------------------------------------------------------------------------
# A-01 : types inattendus, jamais de plantage ; un plantage interne devient E_INTERNAL
# ---------------------------------------------------------------------------------------------
def section_a01():
    cases = {
        "racine liste": lambda m: Root([]),
        "racine chaine": lambda m: Root("x"),
        "racine null": lambda m: Root(None),
        "racine entier": lambda m: Root(5),
        "keys entier": lambda m: m.update(keys=5),
        "keys null": lambda m: m.update(keys=None),
        "keys objet": lambda m: m.update(keys={}),
        "keys [chaine]": lambda m: m.update(keys=["x"]),
        "geometry null": lambda m: m.update(geometry=None),
        "geometry 5": lambda m: m.update(geometry=5),
        "deadKeys 5": lambda m: m.update(deadKeys=5),
        "deadKeys null": lambda m: m.update(deadKeys=None),
        "deadKeys [chaine]": lambda m: m.update(deadKeys=["x"]),
        "levels liste": lambda m: m["keys"][0].update(levels=["a"]),
        "levels chaine": lambda m: m["keys"][0].update(levels="a"),
        "groups {'2': 'x'}": lambda m: m["keys"][0].update(groups={"2": "x"}),
        "groups liste": lambda m: m["keys"][0].update(groups=["x"]),
        "deadKey de sortie []": lambda m: m["keys"][2]["levels"].update({"1": {"deadKey": []}}),
        "deadKeys[0].id []": lambda m: m["deadKeys"][0].update(id=[]),
        "exports[].id []": lambda m: m.update(exports=[{"target": "xkb", "id": []}, {"target": "xkb", "id": []}]),
        "exports [5]": lambda m: m.update(exports=[5]),
        "extensionsRequired [[]]": lambda m: m.update(extensionsUsed=[], extensionsRequired=[[]]),
        "ids entiers, meme code (strict)": lambda m: (m["keys"][0].update(id=5, code="KeyQ"),
                                                       m["keys"][1].update(id=5, code="KeyQ")),
        "schemaVersion geante": lambda m: m.update(schemaVersion="9" * 5000 + ".0"),
    }
    for label, fn in cases.items():
        manifest = mutated(fn)
        for strict in (False, True):
            try:
                errs = errors(manifest, strict)
            except BaseException as exc:  # noqa: BLE001
                check(False, f"A-01 {label} (strict={strict}) : plantage {type(exc).__name__}: {exc}")
                continue
            check(errs, f"A-01 {label} (strict={strict}) : doit etre rejete")
            check("E_INTERNAL" not in errs, f"A-01 {label} (strict={strict}) : E_INTERNAL ne doit pas etre necessaire")

    # un plantage interne est rapporte par fichier, le lot continue, --json sort toujours
    saved = v.consistency_findings
    try:
        def boom(manifest):
            raise RuntimeError("boom")
        v.consistency_findings = boom
        internal = findings(copy.deepcopy(BASE))
    finally:
        v.consistency_findings = saved
    check([f.code for f in internal if f.severity == "error"] == ["E_INTERNAL"], "A-01 E_INTERNAL : un controle qui plante")
    check(any("boom" in f.message for f in internal), "A-01 E_INTERNAL : le message nomme l'exception")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        good = tmp / "good.oklm.json"
        good.write_text(BASE_TEXT, encoding="utf-8")
        crash = tmp / "crash.oklm.json"
        crash.write_text("[]", encoding="utf-8")
        rc, out, err = cli("--json", str(good), str(crash), str(good))
        check(rc == 1, f"A-01 lot avec un fichier invalide : rc 1 (obtenu {rc})")
        try:
            report = json.loads(out)
        except ValueError:
            report = None
            check(False, f"A-01 --json : sortie JSON absente ({err[-200:]!r})")
        if report:
            flags = [r["valid"] for r in report["results"]]
            check(flags == [True, False, True], f"A-01 le lot continue apres le fichier invalide : {flags}")
        rc, out, err = cli(str(good), str(crash), str(good))
        check(out.count("VALID") >= 3 and "Traceback" not in err, "A-01 lot texte : trois verdicts, pas de traceback")


# ---------------------------------------------------------------------------------------------
# A-11, A-18, A-12, A-20 : lecture du fichier, affichage, jokers
# ---------------------------------------------------------------------------------------------
def file_codes(raw, *flags, name="case.oklm.json"):
    """Write `raw` (bytes) in a temporary file and run the CLI with --json: (rc, set of codes, stdout, stderr)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / name
        path.write_bytes(raw)
        rc, out, err = cli("--json", *flags, str(path))
    try:
        report = json.loads(out)
        found = {f["code"] for f in report["results"][0]["findings"]}
    except (ValueError, KeyError, IndexError):
        found = {"<pas de JSON>"}
    return rc, found, out, err


def section_files():
    levels_old = '"levels": { "1": "a", "2": "A" }'
    check(levels_old in BASE_TEXT, "fixture : le texte de reference contient les niveaux attendus")

    def text_with(replacement, old=levels_old):
        return BASE_TEXT.replace(old, replacement).encode("utf-8")

    rc, found, out, err = file_codes(BASE_TEXT.encode("utf-8"), "--strict")
    check(rc == 0 and not found, f"base : valide en strict ({found})")

    # A-11 : cles dupliquees, constantes non JSON, surrogates isoles
    rc, found, out, err = file_codes(text_with('"levels": { "1": "a", "1": "ZZZ", "2": "A" }'), "--strict")
    check(rc == 1 and "E_DUPLICATE_JSON_KEY" in found, f"A-11 cle JSON dupliquee refusee ({found})")
    check("levels" in out and "'1'" in out, "A-11 le message nomme la cle et son objet")
    rc, found, out, err = file_codes(BASE_TEXT.replace('"links": {', '"training": {"x": NaN}, "links": {').encode("utf-8"))
    check(rc == 1 and "E_JSON_CONSTANT" in found, f"A-11 NaN refuse ({found})")
    rc, found, out, err = file_codes(BASE_TEXT.replace('"links": {', '"training": {"x": -Infinity}, "links": {').encode("utf-8"))
    check(rc == 1 and "E_JSON_CONSTANT" in found, f"A-11 -Infinity refuse ({found})")
    rc, found, out, err = file_codes(BASE_TEXT.replace('"links": {', '"training": {"x": 1e999}, "links": {').encode("utf-8"))
    check(rc == 1 and "E_JSON_CONSTANT" in found, f"A-11 nombre hors flottant refuse ({found})")
    rc, found, out, err = file_codes(text_with('"levels": { "1": "\\ud800", "2": "A" }'), "--strict")
    check(rc == 1 and "E_SURROGATE" in found, f"A-11 surrogate isole dans une valeur ({found})")
    manifest = json.loads(BASE_TEXT)
    manifest["foo\ud800"] = 1
    rc, found, out, err = file_codes(json.dumps(manifest).encode("ascii"), "--strict")
    check(rc == 1 and "E_SURROGATE" in found and "Traceback" not in err, f"A-11 surrogate isole dans un nom de membre ({found})")
    rc, found, out, err = file_codes(text_with('"levels": { "1": "\\ud83d\\ude00", "2": "A" }'))
    check(rc == 0, f"A-11 une paire de surrogates valide (U+1F600) reste acceptee ({found})")

    # A-18 : BOM, profondeur
    rc, found, out, err = file_codes(b"\xef\xbb\xbf" + BASE_TEXT.encode("utf-8"), "--strict")
    check(rc == 0 and not found, f"A-18 BOM UTF-8 accepte ({found})")
    deep = "[" * 100000 + "]" * 100000
    rc, found, out, err = file_codes(BASE_TEXT.replace('"links": {', f'"training": {{"x": {deep}}}, "links": {{').encode("utf-8"))
    check(rc == 1 and "E_READ" in found and "Traceback" not in err, f"A-18 imbrication profonde : E_READ propre ({found})")
    rc, found, out, err = file_codes(BASE_TEXT.encode("utf-16"))
    check(rc == 1 and "E_READ" in found, f"A-18 UTF-16 : E_READ ({found})")

    # A-12 : sortie redirigee en cp1252, nom de membre hors cp1252
    manifest = json.loads(BASE_TEXT)
    manifest["日本語"] = 1
    raw = json.dumps(manifest, ensure_ascii=False).encode("utf-8")
    rc, found, out, err = file_codes(raw, "--strict")
    check(rc == 1 and "W_UNKNOWN_MEMBER" in found and "Traceback" not in err, f"A-12 --json : CJK sans plantage (rc {rc}, {err[-120:]!r})")
    check("日本語" in out, "A-12 --json : le nom CJK est ecrit en UTF-8")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "cjk.oklm.json"
        path.write_bytes(raw)
        rc, out, err = cli("--strict", str(path))
    check(rc == 1 and "Traceback" not in err and "INVALID" in out and "日本語" in out, f"A-12 texte : CJK sans plantage ({err[-120:]!r})")

    # A-20 : les jokers sont developpes par le validateur (PowerShell ne le fait pas)
    with tempfile.TemporaryDirectory() as tmp:
        for name in ("one", "two"):
            (Path(tmp) / f"{name}.oklm.json").write_text(BASE_TEXT, encoding="utf-8")
        rc, out, err = cli("--strict", str(Path(tmp) / "*.oklm.json"))
        check(rc == 0 and out.count("VALID") == 2 and "INVALID" not in out, f"A-20 joker developpe ({out!r})")
        rc, out, err = cli(str(Path(tmp) / "*.nothing.json"))
        check(rc == 1 and "E_READ" in out and "no file matches" in out, f"A-20 joker sans correspondance : E_READ clair ({out!r})")


# ---------------------------------------------------------------------------------------------
# A-03 : un motif en `$` ne doit pas accepter un saut de ligne final
# ---------------------------------------------------------------------------------------------
def section_a03():
    cases = {
        "schemaVersion 1.0\\n (MAJOR 1)": lambda m: m.update(schemaVersion="1.0\n"),
        "schemaVersion 0.2\\n": lambda m: m.update(schemaVersion="0.2\n"),
        "layoutId": lambda m: m.update(layoutId="abc\n"),
        "version": lambda m: m.update(version="1.0.0\n"),
        "locale": lambda m: m.update(locales=["fr\n"]),
        "geometry": lambda m: m.update(geometry=["iso-full\n"]),
        "id de touche": lambda m: m["keys"][0].update(id="D01\n"),
        "hid": lambda m: m["keys"][0].update(hid="0x14\n"),
        "xkb": lambda m: m["keys"][0].update(xkb="AD01\n"),
        "code": lambda m: m["keys"][0].update(code="KeyQ\n"),
        "id de deadKey": lambda m: m["deadKeys"][0].update(id="circumflex\n"),
        "reference deadKey": lambda m: m["keys"][2]["levels"].update({"1": {"deadKey": "circumflex\n"}}),
        "cible d'export": lambda m: m["exports"][0].update(target="xkb\n"),
        "extensionsUsed": lambda m: m.update(extensionsUsed=["OKLM_a\n"]),
        "featuresRequired": lambda m: m.update(featuresRequired=["feat\n"]),
    }
    for label, fn in cases.items():
        manifest = mutated(fn)
        for strict in (False, True):
            check("E_SCHEMA" in errors(manifest, strict), f"A-03 {label} + saut de ligne final refuse (strict={strict})")
    check("E_SCHEMA_VERSION_MAJOR" in errors(mutated(lambda m: m.update(schemaVersion="1.0"))), "A-03 temoin : 1.0 donne E_SCHEMA_VERSION_MAJOR")
    # aucun motif du schema ne se termine par un `$` nu
    for name in ("oklm-manifest.schema.json", "oklm-conversion-report.schema.json"):
        text = (ROOT / "schemas" / name).read_text(encoding="utf-8")
        check('$"' not in text.replace('(?!\\\\n)$"', ""), f"A-03 {name} : aucun motif ne finit par un `$` nu")


# ---------------------------------------------------------------------------------------------
# A-07 : bornes des niveaux et des groupes ; A-08 : `layers` a tous les etages
# ---------------------------------------------------------------------------------------------
def section_a07_a08():
    for bad in ["0", "9", "10", "-1", "01", "1.0", "a", "", "1\n", "+1", "１"]:
        manifest = mutated(lambda m, bad=bad: m["keys"][0]["levels"].update({bad: "x"}))
        for strict in (False, True):
            check("E_LEVEL_RANGE" in errors(manifest, strict), f"A-07 niveau {bad!r} hors 1-8 (strict={strict})")
    for good in "12345678":
        check(not errors(mutated(lambda m, good=good: m["keys"][0]["levels"].update({good: "x"})), True),
              f"A-07 niveau {good} accepte")
    for bad in ["1", "10", "0", "a", "2\n"]:
        manifest = mutated(lambda m, bad=bad: m["keys"][0].update(groups={bad: {"1": "x"}}))
        check("E_LEVEL_RANGE" in errors(manifest), f"A-07 groupe {bad!r} hors 2-9")
    check("E_LEVEL_RANGE" in errors(mutated(lambda m: m["keys"][0].update(groups={"2": {"9": "x"}}))), "A-07 niveau 9 dans un groupe")
    check(not errors(mutated(lambda m: m["keys"][0].update(groups={"2": {"1": "x"}, "9": {"8": "y"}}))), "A-07 groupes 2 et 9, niveaux 1 et 8 acceptes")
    for bad in ["1", "9", "0", "x"]:
        manifest = mutated(lambda m, bad=bad: m["levelSelectors"].update({bad: ["Level2Shift"]}))
        check("E_LEVEL_RANGE" in errors(manifest), f"A-07 levelSelectors {bad!r} hors 2-8")
    check(not errors(mutated(lambda m: m["levelSelectors"].update({"5": ["Level5Shift"], "8": ["CapsLock"]})), True), "A-07 levelSelectors 5 et 8 acceptes")
    # un seul constat par membre : pas de W_UNKNOWN_MEMBER en double
    found = findings(mutated(lambda m: m["keys"][0]["levels"].update({"9": "x"})))
    check([f.code for f in found if f.path == "keys[0].levels.9"] == ["E_LEVEL_RANGE"], "A-07 un seul constat pour le niveau 9")

    # A-08 : layers n'est avale nulle part
    nested = {
        "racine": (lambda m: m.update(layers=["base"]), "layers"),
        "touche": (lambda m: m["keys"][0].update(layers={"base": "a"}), "keys[0].layers"),
        "deadKey": (lambda m: m["deadKeys"][0].update(layers=1), "deadKeys[0].layers"),
        "levels": (lambda m: m["keys"][0]["levels"].update(layers="a"), "keys[0].levels.layers"),
        "sortie": (lambda m: m["keys"][2]["levels"].update({"1": {"deadKey": "circumflex", "layers": 1}}), "keys[2].levels.1.layers"),
        "export": (lambda m: m["exports"][0].update(layers=1), "exports[0].layers"),
        "metadata": (lambda m: m["metadata"].update(layers=1), "metadata.layers"),
    }
    for label, (fn, path) in nested.items():
        manifest = mutated(fn)
        for strict in (False, True):
            hits = [f for f in findings(manifest, strict) if f.code == "E_LAYERS_UNSUPPORTED"]
            check(len(hits) == 1 and hits[0].path == path and hits[0].severity == "error" and "keys[].levels" in hits[0].message,
                  f"A-08 layers dans {label} : E_LAYERS_UNSUPPORTED a {path} (strict={strict}) -> {[h.path for h in hits]}")
        check(not any(f.code == "W_UNKNOWN_MEMBER" and f.path == path for f in findings(manifest)), f"A-08 {label} : pas de W_UNKNOWN_MEMBER en double")
    check("E_LAYERS_UNSUPPORTED" not in codes(mutated(lambda m: m["metadata"].update(training={"layers": 1})), True),
          "A-08 `layers` dans un bloc metadata libre reste libre")


# ---------------------------------------------------------------------------------------------
# A-09 : unicite des deadKeys, des hid et des xkb ; C-14, C-15 : avertissements de capacite
# ---------------------------------------------------------------------------------------------
def section_a09():
    manifest = mutated(lambda m: m["deadKeys"].append(copy.deepcopy(m["deadKeys"][0])))
    for strict in (False, True):
        check("E_DUPLICATE_DEADKEY_ID" in errors(manifest, strict), f"A-09 deadKey de meme id (strict={strict})")
    check("E_DUPLICATE_DEADKEY_ID" not in codes(BASE, True), "A-09 temoin : ids de deadKeys uniques")

    manifest = mutated(lambda m: m["keys"][1].update(hid=m["keys"][0]["hid"]))
    check("E_DUPLICATE_HID" not in codes(manifest) and codes(manifest, severity="warning").count("W_DUPLICATE_HID") == 1,
          f"A-09 hid en double : avertissement hors strict ({codes(manifest)})")
    check("W_DUPLICATE_HID" in errors(manifest, True), "A-09 hid en double : erreur en strict")
    other_case = mutated(lambda m: m["keys"][1].update(hid=m["keys"][0]["hid"].replace("0x", "0x00").lower()))
    check("W_DUPLICATE_HID" in codes(other_case), "A-09 hid en double sous une autre graphie (0x0014 / 0x14)")
    manifest = mutated(lambda m: (m["keys"][0].update(xkb="AD01"), m["keys"][1].update(xkb="AD01")))
    check("W_DUPLICATE_XKB" in codes(manifest, severity="warning"), "A-09 xkb en double : avertissement hors strict")
    check("W_DUPLICATE_XKB" in errors(manifest, True), "A-09 xkb en double : erreur en strict")
    check(not codes(BASE, True), "A-09 temoin : le manifeste de reference n'a aucun constat en strict")

    # C-15 : featuresRequired n'a pas de registre, un lecteur ne peut pas les honorer
    manifest = mutated(lambda m: m.update(featuresRequired=["some-feature"]))
    check(codes(manifest, severity="warning") == ["W_FEATURE_UNREGISTERED"] and not errors(manifest, True),
          f"C-15 featuresRequired : avertissement, meme en strict ({codes(manifest, True)})")
    check(not codes(mutated(lambda m: m.update(featuresRequired=[]))), "C-15 featuresRequired vide : rien")

    # C-14 : niveaux 5-8 sans levelSelectors
    manifest = mutated(lambda m: (m["levelSelectors"].pop("5", None), m["keys"][0]["levels"].update({"5": "x"})))
    check(codes(manifest, severity="warning") == ["W_LEVEL_NO_SELECTOR"] and not errors(manifest, True),
          f"C-14 niveau 5 sans selecteur : avertissement ({codes(manifest, True)})")
    manifest = mutated(lambda m: (m["levelSelectors"].update({"5": ["Level5Shift"]}), m["keys"][0]["levels"].update({"5": "x"})))
    check(not codes(manifest, True), "C-14 niveau 5 avec selecteur : rien")
    manifest = mutated(lambda m: (m["levelSelectors"].pop("6", None), m["keys"][0].update(groups={"2": {"6": "x"}})))
    check("W_LEVEL_NO_SELECTOR" in codes(manifest), "C-14 niveau 6 d'un groupe sans selecteur")
    check("W_LEVEL_NO_SELECTOR" not in codes(mutated(lambda m: m["keys"][0]["levels"].update({"4": "x"}))), "C-14 niveau 4 : defaut, pas d'avertissement")


# ---------------------------------------------------------------------------------------------
# A-10, A-15, C-16, A-17 : le schema lui-meme
# ---------------------------------------------------------------------------------------------
def section_schemas():
    # A-10 : options.conformsTo de la cible ldml
    def ldml_conforms(value):
        return mutated(lambda m: m.update(exports=[{"target": "ldml-keyboard-3", "options": {"conformsTo": value}}]))

    for bad in (10, 44, 49, "45", 45.5, True, None, [45]):
        check("E_SCHEMA" in errors(ldml_conforms(bad)), f"A-10 conformsTo {bad!r} refuse pour ldml-keyboard-3")
    for good in (45, 46, 47, 48):
        check(not errors(ldml_conforms(good), True), f"A-10 conformsTo {good} accepte")
    check(not errors(mutated(lambda m: m.update(exports=[{"target": "xkb", "options": {"conformsTo": 10}}]))),
          "A-10 la regle ne vise que la cible ldml-keyboard-3")
    check(not errors(mutated(lambda m: m.update(exports=[{"target": "ldml-keyboard-3"}]))), "A-10 options absentes : accepte")

    # A-15 : SemVer officiel, doublons, modifier => role
    for bad in ("1.0.0-01", "1.0.0-01.2", "1.0.0-1.01", "1.0.0-", "1.0.0+", "1.0.0-alpha..1", "01.0.0", "1.0", "v1.0.0", "1.0.0-α"):
        check("E_SCHEMA" in errors(mutated(lambda m, bad=bad: m.update(version=bad))), f"A-15 version {bad!r} refusee")
    for good in ("0.0.0", "1.0.0-0", "1.0.0-0a", "1.0.0-alpha.1", "1.0.0-x.7.z.92", "1.0.0+001", "1.2.3-rc.1+build.5", "10.20.30"):
        check(not errors(mutated(lambda m, good=good: m.update(version=good))), f"A-15 version {good!r} acceptee")
    dups = {
        "locales": lambda m: m.update(locales=["fr", "fr"]),
        "authors": lambda m: m.update(authors=["A", "A"]),
        "geometry": lambda m: m.update(geometry=["iso-full", "iso-full"]),
        "levelSelectors": lambda m: m["levelSelectors"].update({"2": ["Level2Shift", "Level2Shift"]}),
    }
    for label, fn in dups.items():
        check("E_SCHEMA" in errors(mutated(fn)), f"A-15 doublons refuses dans {label}")
    check("E_SCHEMA" in errors(mutated(lambda m: m["keys"][0].update(modifier="Level2Shift"))), "A-15 `modifier` sans role: modifier refuse")
    check("E_SCHEMA" in errors(mutated(lambda m: m["keys"][0].update(role="key", modifier="Level2Shift"))), "A-15 `modifier` avec role: key refuse")
    check(not errors(mutated(lambda m: (m["keys"][0].pop("levels"), m["keys"][0].update(role="modifier", modifier="Level2Shift")))),
          "A-15 role modifier + modifier accepte")

    # C-16 : role key = touche graphique, il lui faut des levels
    check("E_SCHEMA" in errors(mutated(lambda m: (m["keys"][0].pop("levels"), m["keys"][0].update(role="key")))), "C-16 role key sans levels refuse")
    check(not errors(mutated(lambda m: m["keys"][0].update(role="key"))), "C-16 role key avec levels accepte")

    # A-17 : coherence du rapport de conversion
    report_schema = v.load_schema("oklm-conversion-report.schema.json")
    rv = v.Draft202012Validator(report_schema)
    report = {
        "schemaVersion": "0.2", "direction": "oklm-to-ldml",
        "source": {"format": "oklm", "version": "0.2"}, "target": {"format": "ldml-keyboard-3", "conformsTo": 45},
        "compatibilityLevel": "lossless-core", "mappedFields": ["keys"], "skippedFields": [],
        "lossyMappings": [], "roundTripConfidence": "high", "warnings": [], "errors": [],
    }

    def report_ok(**changes):
        return not list(rv.iter_errors({**report, **changes}))

    check(report_ok(), "A-17 temoin : rapport lossless-core propre")
    check(not report_ok(lossyMappings=[{"path": "keys", "detail": "x"}]), "A-17 lossless-core + lossyMappings refuse")
    check(not report_ok(errors=["boom"]), "A-17 lossless-core + errors refuse")
    check(report_ok(warnings=["w"]), "A-17 lossless-core + warnings accepte")
    check(report_ok(compatibilityLevel="lossy-mapping", lossyMappings=[{"path": "keys", "detail": "x"}]), "A-17 lossy-mapping + lossyMappings accepte")
    check(not report_ok(compatibilityLevel="failed"), "A-17 failed sans erreur refuse")
    check(report_ok(compatibilityLevel="failed", errors=["boom"]), "A-17 failed avec erreur accepte")
    check(report_ok(compatibilityLevel="unsupported"), "A-17 unsupported : inchange (D33)")


# ---------------------------------------------------------------------------------------------
# B-03 : pas de saut de ligne ni de caractere de controle dans les textes et les sorties
# ---------------------------------------------------------------------------------------------
def section_b03():
    fields = {
        "name": (lambda m, s: m.update(name="AZERTY" + s), "name"),
        "description": (lambda m, s: m.update(description="d" + s), "description"),
        "license": (lambda m, s: m.update(license="EUPL" + s), "license"),
        "authors": (lambda m, s: m.update(authors=["A" + s]), "authors[0]"),
        "metadata.description": (lambda m, s: m["metadata"].update(description="d" + s), "metadata.description"),
        "metadata.versionLabel": (lambda m, s: m["metadata"].update(versionLabel="v" + s), "metadata.versionLabel"),
        "metadata.layoutPattern": (lambda m, s: m["metadata"].update(layoutPattern="p" + s), "metadata.layoutPattern"),
        "metadata.indicator": (lambda m, s: m["metadata"].update(indicator="F" + s), "metadata.indicator"),
        "metadata.links": (lambda m, s: m["metadata"]["links"].update(home="https://example.org/" + s), "metadata.links.home"),
        "key.name": (lambda m, s: m["keys"][0].update(name="Q" + s), "keys[0].name"),
        "key.categories": (lambda m, s: m["keys"][0].update(categories=["letter" + s]), "keys[0].categories[0]"),
        "sortie de niveau": (lambda m, s: m["keys"][0]["levels"].update({"1": "a" + s}), "keys[0].levels.1"),
        "sortie de groupe": (lambda m, s: m["keys"][0].update(groups={"2": {"1": "a" + s}}), "keys[0].groups.2.1"),
        "deadKey.name": (lambda m, s: m["deadKeys"][0].update(name="Circonflexe" + s), "deadKeys[0].name"),
        "deadKey.display": (lambda m, s: m["deadKeys"][0].update(display="^" + s), "deadKeys[0].display"),
        "deadKey.fallback": (lambda m, s: m["deadKeys"][0].update(fallback="^" + s), "deadKeys[0].fallback"),
        "composition (valeur)": (lambda m, s: m["deadKeys"][0]["compositions"].update({"a": "â" + s}), "deadKeys[0].compositions.a"),
        "composition (base)": (lambda m, s: m["deadKeys"][0]["compositions"].update({"z" + s: "ẑ"}), None),
        "conformance.reference": (lambda m, s: m["conformance"][0].update(reference="ISO" + s), "conformance[0].reference"),
        "conformance.scope": (lambda m, s: m["conformance"][0].update(scope="grid" + s), "conformance[0].scope"),
        "conformance.notes": (lambda m, s: m["conformance"][0].update(notes="n" + s), "conformance[0].notes"),
    }
    controls = {"LF": "\n", "CR": "\r", "NUL": "\x00", "TAB": "\t", "ESC": "\x1b", "DEL": "\x7f", "C1 NEL": "\x85", "LS": " "}
    for label, (fn, path) in fields.items():
        for cname, char in controls.items():
            manifest = mutated(lambda m, fn=fn, char=char: fn(m, char))
            hits = [f for f in findings(manifest) if f.code == "E_CONTROL_CHAR"]
            check(len(hits) == 1 and hits[0].severity == "error", f"B-03 {label} + {cname} : un E_CONTROL_CHAR ({len(hits)})")
            if hits and path:
                check(hits[0].path == path, f"B-03 {label} : chemin {hits[0].path!r} attendu {path!r}")
            if hits:
                check(char not in hits[0].path and char not in hits[0].message, f"B-03 {label} + {cname} : le constat n'embarque pas le caractere brut")
    # texte legitime : ZWJ, ZWNJ, espace insecable, combinants, emoji, texte multilingue
    legit = "é ‍‌ \U0001F600 日本語 ÿ"
    manifest = mutated(lambda m: (m["keys"][0]["levels"].update({"1": legit}), m.update(name="Nom " + legit),
                                  m["deadKeys"][0]["compositions"].update({"q" + "́": legit})))
    check("E_CONTROL_CHAR" not in codes(manifest, True), "B-03 ZWJ, espace insecable, combinants et emoji restent acceptes")
    check("E_CONTROL_CHAR" not in codes(mutated(lambda m: m["metadata"].update(training={"note": "a\nb"})), True),
          "B-03 les blocs metadata libres (training...) ne sont pas controles")
    check("E_CONTROL_CHAR" not in codes(BASE, True), "B-03 temoin : le manifeste de reference est propre")


# ---------------------------------------------------------------------------------------------
def main():
    section_a01()
    section_files()
    section_a03()
    section_a07_a08()
    section_a09()
    section_schemas()
    section_b03()
    if failures:
        print(f"ECHEC : {len(failures)} sur {counter['n']} verifications")
        for message in failures:
            print("  - " + message)
        return 1
    print(f"OK: {counter['n']} verifications de validate.py, 0 echec.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
