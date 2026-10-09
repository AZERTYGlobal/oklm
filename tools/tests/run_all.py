# -*- coding: utf-8 -*-
# SPDX-License-Identifier: EUPL-1.2
"""Lanceur unique des controles du depot OKLM. Code de sortie 0 si tout passe, 1 sinon.

    python tools/tests/run_all.py            # depuis n'importe ou ; resume + sortie des suites en echec
    python tools/tests/run_all.py -v         # sortie complete de chaque suite
    python tools/tests/run_all.py --list     # liste ce qui serait lance, sans rien lancer

Lance, chacune dans son processus (cwd = racine du depot) :
  1. tools/tests/run_tests.py                       (exporteurs LDML / xkb / keylayout)
  2. tools/tests/test_*.py                          (decouverts automatiquement : un nouveau test_*.py est lance)
  3. validators/validate_v0_2.py                    (schemas, regles du validateur, migration)
  4. validators/validate.py --strict <manifestes>   (tous les *.oklm.json du depot, hors fixtures)

Dependances : voir requirements.txt (jsonschema). Une suite qui imprime "SKIPPED (...)" reste verte ;
ce lanceur ne rend ce message qu'en clair, il ne le masque pas.
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TESTS = ROOT / "tools" / "tests"
PRUNE = {".git", "__pycache__", "fixtures", "node_modules", ".venv", "venv"}
TIMEOUT = 900


def manifests():
    """Tous les *.oklm.json du depot (liste construite en Python, pas de glob shell), tries."""
    found = []
    for folder, dirs, names in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in PRUNE)
        found += [Path(folder) / n for n in names if n.endswith(".oklm.json")]
    return sorted(found)


def plan():
    """Liste de (nom, argv relatif a la racine)."""
    jobs = []
    if (TESTS / "run_tests.py").exists():
        jobs.append(("tools/tests/run_tests.py", ["tools/tests/run_tests.py"]))
    for path in sorted(TESTS.glob("test_*.py")):
        rel = path.relative_to(ROOT).as_posix()
        jobs.append((rel, [rel]))
    jobs.append(("validators/validate_v0_2.py", ["validators/validate_v0_2.py"]))
    files = [p.relative_to(ROOT).as_posix() for p in manifests()]
    jobs.append((f"validators/validate.py --strict ({len(files)} manifestes)",
                 ["validators/validate.py", "--strict"] + files))
    return jobs


def run(argv):
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    start = time.time()
    try:
        done = subprocess.run([sys.executable, "-B"] + argv, cwd=ROOT, env=env, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT)
        code, out = done.returncode, done.stdout + done.stderr
    except subprocess.TimeoutExpired as exc:
        code, out = 124, f"TIMEOUT apres {TIMEOUT}s\n{exc.stdout or ''}"
    return code, out, time.time() - start


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-v", "--verbose", action="store_true", help="afficher la sortie de chaque suite")
    ap.add_argument("--list", action="store_true", help="lister sans lancer")
    args = ap.parse_args(argv)

    jobs = plan()
    if args.list:
        for name, _ in jobs:
            print(name)
        return 0
    if not any(name.startswith("tools/tests/") for name, _ in jobs):
        print("ERREUR : aucune suite de tests trouvee dans tools/tests/")
        return 1

    results = []
    for name, argv_job in jobs:
        code, out, seconds = run(argv_job)
        results.append((name, code, seconds, out))
        print(f"{'OK  ' if code == 0 else 'FAIL'} {name} ({seconds:.1f}s)", flush=True)
        if args.verbose or code != 0:
            lines = out.rstrip().splitlines()
            for line in lines if args.verbose else lines[-60:]:
                print("     | " + line)

    skipped = [(n, line.strip()) for n, _, _, out in results for line in out.splitlines() if "SKIPPED" in line]
    failed = [n for n, code, _, _ in results if code != 0]
    print()
    print(f"Resume : {len(results) - len(failed)}/{len(results)} suites OK, {len(failed)} en echec.")
    for n, line in skipped:
        print(f"  note ({n}) : {line}")
    for n in failed:
        print(f"  ECHEC : {n}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
