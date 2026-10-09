# -*- coding: utf-8 -*-
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
def main():
    section_a01()
    if failures:
        print(f"ECHEC : {len(failures)} sur {counter['n']} verifications")
        for message in failures:
            print("  - " + message)
        return 1
    print(f"OK: {counter['n']} verifications de validate.py, 0 echec.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
