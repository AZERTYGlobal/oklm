# -*- coding: utf-8 -*-
"""Tests of tools/migrate_0_1_to_0_2.py (audit 2026-10-09, axis A: A-02, A-04, A-05, A-06, A-12, A-18, A-19
and the lost version label). Plain assertions, exit code 0/1.

    python tools/tests/test_migrate.py

Everything happens in memory or in a temporary directory; nothing is written in the repository.
"""
import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "validators"))

import migrate_0_1_to_0_2 as mg  # noqa: E402
import validate as v  # noqa: E402

SCRIPT = ROOT / "tools" / "migrate_0_1_to_0_2.py"
EXAMPLES = sorted((ROOT / "examples").glob("*.oklm.json"))
BASE = json.loads((ROOT / "examples" / "azerty-global-minimal.oklm.json").read_text(encoding="utf-8"))

failures, counter = [], {"n": 0}


def check(condition, message):
    counter["n"] += 1
    if not condition:
        failures.append(message)


def old_manifest(**changes):
    """A 0.1 manifest: the minimal example with its schemaVersion and version of that time."""
    m = copy.deepcopy(BASE)
    m["schemaVersion"] = "0.1"
    m["version"] = "2026"
    m.update(changes)
    return m


def with_key(lv=None, **extra):
    m = old_manifest()
    key = {"id": "C00", "hid": "0x39"}
    if lv is not None:
        key["levels"] = lv
    key.update(extra)
    m["keys"].append(key)
    return m


def refused(manifest):
    """The message of the MigrationError raised for `manifest`, or None when it migrates (any other exception fails the test)."""
    try:
        mg.migrate(manifest)
    except mg.MigrationError as exc:
        return str(exc)
    return None


def errors_of(manifest):
    return sorted({f.code for f in v.analyze(manifest, strict=True) if f.severity == "error"})


def cli(*args):
    env = {k: val for k, val in os.environ.items() if k not in ("PYTHONUTF8", "PYTHONIOENCODING")}
    proc = subprocess.run([sys.executable, "-B", str(SCRIPT), *map(str, args)], capture_output=True, env=env, timeout=120)
    return proc.returncode, proc.stdout.decode("utf-8", "replace"), proc.stderr.decode("utf-8", "replace")


# ---------------------------------------------------------------------------------------------
def section_schema_version():
    """A-02: only 0.1 is migrated, 0.2 is left alone, everything else is refused."""
    check(mg.migrate(old_manifest())["schemaVersion"] == "0.2", "A-02 0.1 -> 0.2")
    new = mg.migrate(old_manifest())
    check(mg.migrate(new) == new, "A-02 0.2 : inchange, idempotent")
    for example in EXAMPLES:
        manifest = json.loads(example.read_text(encoding="utf-8"))
        check(mg.migrate(manifest) == manifest, f"A-02 {example.name} (0.2) : inchange")
    for bad in ("0.3", "1.0", "2.5", "0.0", "0.2.1", "garbage", "", "0.2 ", "0.2\n", 0.2, 0.1, None, ["0.1"]):
        m = old_manifest()
        m["schemaVersion"] = bad
        message = refused(m)
        check(message and "0.1" in message, f"A-02 schemaVersion {bad!r} refuse avec un message ({message})")
    m = old_manifest()
    del m["schemaVersion"]
    check(refused(m) and "missing" in refused(m), "A-02 schemaVersion absent : refuse")
    for bad in ([], "x", None, 5):
        try:
            mg.migrate(bad)
            check(False, f"A-02 document {bad!r} : doit etre refuse")
        except mg.MigrationError:
            check(True, "")

    with tempfile.TemporaryDirectory() as tmp:
        for label, value in (("0.3", "0.3"), ("1.0", "1.0"), ("absent", None)):
            path = Path(tmp) / f"v-{label}.oklm.json"
            m = old_manifest()
            if value is None:
                del m["schemaVersion"]
            else:
                m["schemaVersion"] = value
            path.write_text(json.dumps(m), encoding="utf-8")
            before = path.read_bytes()
            rc, out, err = cli(path)
            check(rc == 1 and "error:" in err and "Traceback" not in err, f"A-02 CLI schemaVersion {label} : rc 1 et message ({rc}, {err[-120:]!r})")
            check(path.read_bytes() == before, f"A-02 CLI schemaVersion {label} : fichier intact")


def section_version_label():
    check(mg.semver_of("2026") == ("2026.0.0", None), "semver_of 2026")
    check(mg.semver_of("1.0") == ("1.0.0", None), "semver_of 1.0")
    check(mg.semver_of("1.2.3") == ("1.2.3", None), "semver_of 1.2.3")
    check(mg.semver_of("2026.1") == ("2026.1.0", "2026.1"), f"semver_of 2026.1 garde le libelle ({mg.semver_of('2026.1')})")
    check(mg.semver_of("1.5") == ("1.5.0", "1.5"), "semver_of 1.5 garde le libelle")
    check(mg.semver_of("01.02") == ("1.2.0", "01.02"), "semver_of 01.02 garde le libelle")
    check(mg.semver_of("007") == ("7.0.0", "007"), "semver_of 007 garde le libelle")
    check(mg.semver_of("NF Z71-300:2019 (AZERTY option)") == ("2019.0.0", "NF Z71-300:2019 (AZERTY option)"), "semver_of libelle avec annee")
    check(mg.semver_of("ANSI (US 104-key)") == ("1.0.0", "ANSI (US 104-key)"), "semver_of libelle sans annee")
    check(mg.semver_of("1.0.0-01") == ("1.0.0", "1.0.0-01"), "semver_of 1.0.0-01 n'est pas SemVer (identifiant a zero initial)")
    check(mg.semver_of("9" * 5000)[0] == "1.0.0", "semver_of : entier geant, pas d'exception")
    new = mg.migrate(old_manifest(version="2026.1"))
    check(new["version"] == "2026.1.0" and new["metadata"]["versionLabel"] == "2026.1", "migrate : 2026.1 -> metadata.versionLabel")
    check("versionLabel" not in mg.migrate(old_manifest(version="1.0"))["metadata"], "migrate : 1.0 sans libelle")
    m = old_manifest(version="ANSI 2019")
    m["metadata"]["versionLabel"] = "Edition courante"
    message = refused(m)
    check(message and "versionLabel" in message and "Edition courante" in message, f"A-04 versionLabel existant jamais ecrase ({message})")
    m["metadata"]["versionLabel"] = "ANSI 2019"
    check(mg.migrate(m)["metadata"]["versionLabel"] == "ANSI 2019", "A-04 versionLabel identique : accepte")
    m = old_manifest(version="ANSI 2019")
    m["metadata"] = None
    check(refused(m), "A-18 metadata null avec un libelle : refuse proprement")
    m = old_manifest(version="ANSI 2019")
    del m["metadata"]
    check(mg.migrate(m)["metadata"] == {"versionLabel": "ANSI 2019"}, "metadata absent : cree pour le libelle")
    check(refused(old_manifest(version=["x"])) and refused(old_manifest(version=True)), "version de type inattendu : refuse")
    check(mg.migrate(old_manifest(version=2026))["version"] == "2026.0.0", "version numerique 2026")


def section_collisions():
    """A-04: no silent overwrite."""
    cases = {
        "frame-keys + OKLM_frameKeys": old_manifest(extensions={"frame-keys": {"a": 1}, "OKLM_frameKeys": {"b": 2}}),
        "my-tool + my_tool": old_manifest(extensions={"my-tool": {"a": 1}, "my_tool": {"b": 2}}),
        "OKLM_x racine + extensions.OKLM_x": old_manifest(OKLM_x={"new": 1}, extensions={"OKLM_x": {"old": 1}}),
        "racine OKLM_frameKeys + extensions.frame-keys": old_manifest(OKLM_frameKeys={"new": 1}, extensions={"frame-keys": {"old": 1}}),
        "!!! + ???": old_manifest(extensions={"!!!": {}, "???": {}}),
        "metadata.OKLM_x + metadata.extensions.OKLM_x": None,
        "deux modificateurs differents": with_key({"1": {"modifier": "Level2Shift"}, "3": {"modifier": "Level3Shift"}}),
        "modificateur levels + groups differents": with_key({"1": {"modifier": "Level2Shift"}}, groups={"2": {"1": {"modifier": "CapsLock"}}}),
        "modifier existant different": with_key({"1": {"modifier": "Level2Shift"}}, modifier="CapsLock"),
        "role existant different": with_key({"1": {"modifier": "Level2Shift"}}, role="key"),
    }
    m = old_manifest()
    m["metadata"].update(OKLM_x={"new": 1}, extensions={"OKLM_x": {"old": 1}})
    cases["metadata.OKLM_x + metadata.extensions.OKLM_x"] = m
    m = old_manifest()
    m["keys"][0].update(OKLM_k={"a": 1}, extensions={"OKLM_k": {"b": 1}})
    cases["touche OKLM_k + extensions.OKLM_k"] = m
    for label, manifest in cases.items():
        message = refused(manifest)
        check(message, f"A-04 collision refusee : {label}")
    check("collides" in (refused(cases["OKLM_x racine + extensions.OKLM_x"]) or ""), "A-04 le message nomme la collision")

    # pas de faux positif : le meme modificateur deux fois, noms sans collision
    new = mg.migrate(with_key({"1": {"modifier": "Level2Shift"}, "2": {"modifier": "Level2Shift"}}))
    check(new["keys"][-1]["modifier"] == "Level2Shift" and "levels" not in new["keys"][-1], "A-04 le meme modificateur deux fois : accepte")
    new = mg.migrate(old_manifest(extensions={"frame-keys": {"a": 1}, "my-tool": {"b": 2}, "OKLM_geometry": {}}))
    check(sorted(new["extensions"]) == ["EXT_MyTool", "OKLM_frameKeys", "OKLM_geometry"], "A-04 renommages sans collision")
    # extensionsUsed existant : complete, jamais ecrase
    new = mg.migrate(old_manifest(extensions={"frame-keys": {"a": 1}}, extensionsUsed=["ACME_tool"]))
    check(new["extensionsUsed"] == ["ACME_tool", "OKLM_frameKeys"], f"A-04 extensionsUsed existant conserve ({new['extensionsUsed']})")


def section_groups_and_output():
    """A-05: groups migrated, non-object extensions refused, output validated."""
    new = mg.migrate(with_key({"1": "a"}, groups={"2": {"1": {"modifier": "Level3Shift"}}}))
    key = new["keys"][-1]
    check(key["role"] == "modifier" and key["modifier"] == "Level3Shift" and "groups" not in key and key["levels"] == {"1": "a"},
          f"A-05 sortie {{modifier}} dans un groupe migree ({key})")
    check(not errors_of(new), f"A-05 ... et le resultat est valide ({errors_of(new)})")
    new = mg.migrate(with_key({"1": "a"}, groups={"2": {"1": {"modifier": "Level3Shift"}, "2": "b"}, "3": {"1": "c"}}))
    check(new["keys"][-1]["groups"] == {"2": {"2": "b"}, "3": {"1": "c"}}, "A-05 groupes non vides conserves")
    new = mg.migrate(with_key({"1": "a"}, groups={"2": {"1": {"deadKey": "circumflex", "OKLM_x": {"a": 1}}}}))
    out = new["keys"][-1]["groups"]["2"]["1"]
    check(out == {"deadKey": "circumflex", "extensions": {"OKLM_x": {"a": 1}}} and "OKLM_x" in new["extensionsUsed"],
          f"A-05 membre prefixe dans une sortie de groupe range sous extensions ({out})")
    check(not errors_of(new), f"A-05 ... valide ({errors_of(new)})")
    for label, manifest in {
        "racine OKLM_flag true": old_manifest(OKLM_flag=True),
        "metadata.OKLM_siteView liste": None,
        "touche OKLM_k chaine": None,
    }.items():
        if manifest is None:
            manifest = old_manifest()
            if "metadata" in label:
                manifest["metadata"]["OKLM_siteView"] = [1, 2]
            else:
                manifest["keys"][0]["OKLM_k"] = "x"
        message = refused(manifest)
        check(message and "non-object" in message, f"A-05 {label} : valeur non objet refusee ({message})")
    # la sortie est validee avant d'etre rendue
    m = old_manifest()
    del m["keys"][0]["hid"]
    message = refused(m)
    check(message and "invalid" in message and "E_SCHEMA" in message, f"A-05 sortie invalide refusee ({message})")
    m = old_manifest()
    m["keys"][0]["levels"]["9"] = "x"
    check("E_LEVEL_RANGE" in (refused(m) or ""), "A-05 niveau hors bornes : refuse (E_LEVEL_RANGE)")
    # extensions de touche en minuscules : renommees comme a la racine
    m = old_manifest()
    m["keys"][0]["extensions"] = {"my-ext": {"a": 1}}
    new = mg.migrate(m)
    check(new["keys"][0]["extensions"] == {"EXT_MyExt": {"a": 1}} and "EXT_MyExt" in new["extensionsUsed"], "A-05 extensions de touche renommees")
    # A-03 cote migration : un nom suivi d'un saut de ligne n'est pas un nom prefixe
    new = mg.migrate(old_manifest(**{"OKLM_x\n": {}}))
    check("OKLM_x\n" in new and "extensions" not in new, "A-03 `OKLM_x\\n` n'est pas range sous extensions")
    # robustesse aux formes inattendues (A-18)
    for label, manifest in {
        "levels null": with_key(None, levels=None),
        "niveau non numerique": with_key({"x": "a"}),
        "touche non objet": old_manifest(keys=["x"]),
        "keys non tableau": old_manifest(keys=5),
        "groups liste": with_key({"1": "a"}, groups=["x"]),
        "groupe chaine": with_key({"1": "a"}, groups={"2": "x"}),
        "deadKeys non tableau": old_manifest(deadKeys=5),
        "extensions liste": old_manifest(extensions=[1]),
        "extensions valeur non objet": old_manifest(extensions={"frame-keys": 5}),
        "keys absent": None,
    }.items():
        if manifest is None:
            manifest = old_manifest()
            del manifest["keys"]
        try:
            mg.migrate(manifest)
            check(False, f"A-18 {label} : doit etre refuse")
        except mg.MigrationError:
            check(True, "")
        except Exception as exc:  # noqa: BLE001
            check(False, f"A-18 {label} : exception {type(exc).__name__} au lieu de MigrationError")
    # les six exemples : relus tels quels apres retour en 0.1 (version "2026") et re-migration
    for example in EXAMPLES:
        manifest = json.loads(example.read_text(encoding="utf-8"))
        again = mg.migrate(dict(manifest, schemaVersion="0.1"))
        check(again == dict(manifest, schemaVersion="0.2") or again["keys"] == manifest["keys"], f"migration de {example.name} presentee comme 0.1")
        check(not errors_of(again), f"{example.name} migre : valide en strict")


# ---------------------------------------------------------------------------------------------
def section_cli():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        # A-06 : un fichier 0.2 n'est ni reecrit ni reformate
        hand = (ROOT / "examples" / "azerty-global-minimal.oklm.json").read_text(encoding="utf-8")
        hand = hand.replace('"levels": { "1": "a", "2": "A" }', '"levels": {\n        "1": "a",\n        "2": "A"\n      }')
        path = tmp / "hand.oklm.json"
        path.write_text(hand, encoding="utf-8", newline="\n")
        before = path.stat().st_mtime_ns
        rc, out, err = cli(path)
        check(rc == 0 and path.read_text(encoding="utf-8") == hand, f"A-06 fichier 0.2 mis en forme a la main : octets inchanges ({err[-100:]!r})")
        check(path.stat().st_mtime_ns == before, "A-06 fichier 0.2 : pas meme reecrit (mtime)")
        check("unchanged" in out, f"A-06 message 'unchanged' ({out!r})")
        dest = tmp / "dest"
        rc, out, err = cli("--out", dest, path)
        check(rc == 0 and (dest / "hand.oklm.json").read_bytes() == path.read_bytes(), "A-06 --out : copie octet pour octet d'un fichier 0.2")

        # migration reelle, deux styles, idempotence du fichier
        old = old_manifest()
        compact = tmp / "compact.oklm.json"
        compact.write_bytes((mg.dumps(old) + "\n").encode("utf-8"))
        expanded = tmp / "expanded.oklm.json"
        expanded.write_text(json.dumps(old, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        rc, out, err = cli(compact, expanded)
        check(rc == 0 and out.count("migrated:") == 2, f"CLI : deux fichiers migres ({out!r}, {err[-100:]!r})")
        check(json.loads(compact.read_text(encoding="utf-8"))["schemaVersion"] == "0.2", "CLI : compact migre")
        check(expanded.read_text(encoding="utf-8") == json.dumps(mg.migrate(old), indent=2, ensure_ascii=False) + "\n", "CLI : style developpe conserve")
        after = compact.read_bytes()
        rc, out, err = cli(compact)
        check(rc == 0 and compact.read_bytes() == after and "unchanged" in out, "CLI : seconde passe sans effet")
        check(not [p for p in tmp.iterdir() if p.name.endswith(".tmp")], "CLI : aucun fichier temporaire laisse")

        # A-18 : BOM, fichier absent, erreurs par fichier
        bom = tmp / "bom.oklm.json"
        bom.write_bytes(b"\xef\xbb\xbf" + (mg.dumps(old) + "\n").encode("utf-8"))
        bad = tmp / "bad.oklm.json"
        bad.write_text(json.dumps(old_manifest(keys=5)), encoding="utf-8")
        missing = tmp / "missing.oklm.json"
        good = tmp / "good.oklm.json"
        good.write_bytes((mg.dumps(old) + "\n").encode("utf-8"))
        rc, out, err = cli(bom, missing, bad, good)
        check(rc == 1, "A-18 un lot avec des erreurs : rc 1")
        check("Traceback" not in err and err.count("error:") == 2, f"A-18 deux erreurs courtes, pas de traceback ({err[-300:]!r})")
        check(out.count("migrated:") == 2 and json.loads(good.read_text(encoding="utf-8"))["schemaVersion"] == "0.2",
              "A-18 le lot continue apres une erreur (BOM accepte, fichier suivant migre)")
        check(json.loads(bad.read_text(encoding="utf-8"))["keys"] == 5, "A-18 le fichier refuse n'est pas touche")

        # A-11 : cles dupliquees, NaN
        dup = tmp / "dup.oklm.json"
        dup.write_text(json.dumps(old).replace('"version": "2026"', '"version": "2026", "version": "1.0"'), encoding="utf-8")
        before = dup.read_bytes()
        rc, out, err = cli(dup)
        check(rc == 1 and "E_DUPLICATE_JSON_KEY" in err and dup.read_bytes() == before, f"A-11 cle dupliquee : refuse ({err[-150:]!r})")
        nan = tmp / "nan.oklm.json"
        nan.write_text(json.dumps(old).replace('"version": "2026"', '"version": "2026", "x": NaN'), encoding="utf-8")
        rc, out, err = cli(nan)
        check(rc == 1 and "Traceback" not in err, "A-19 NaN en entree : refuse")
        deep = tmp / "deep.oklm.json"
        deep.write_text(json.dumps(old).replace('"version": "2026"', '"version": "2026", "x": ' + "[" * 100000 + "]" * 100000), encoding="utf-8")
        rc, out, err = cli(deep)
        check(rc == 1 and "Traceback" not in err and "error:" in err, f"A-18 imbrication profonde : erreur courte ({err[-150:]!r})")

        # A-12 : nom de fichier hors cp1252, stdout redirige
        cjk = tmp / "日本.oklm.json"
        cjk.write_bytes((mg.dumps(old) + "\n").encode("utf-8"))
        rc, out, err = cli(cjk)
        check(rc == 0 and "Traceback" not in err and "日本" in out, f"A-12 nom CJK : rc 0 sans UnicodeEncodeError ({err[-150:]!r})")
        check(json.loads(cjk.read_text(encoding="utf-8"))["schemaVersion"] == "0.2", "A-12 nom CJK : fichier migre")

        # surrogate isole : refuse AVANT d'ecrire, le fichier reste comme il etait
        surrogate = tmp / "surrogate.oklm.json"
        surrogate.write_text(json.dumps(old).replace('"version": "2026"', '"version": "2026", "x": "\\ud800"'), encoding="utf-8")
        before = surrogate.read_bytes()
        rc, out, err = cli(surrogate)
        check(rc == 1 and surrogate.read_bytes() == before, "A-12 surrogate isole : refuse, fichier intact")

        # --out : deux entrees de meme nom, la seconde ne remplace pas la premiere
        (tmp / "a").mkdir()
        (tmp / "b").mkdir()
        first = old_manifest(layoutId="first")
        second = old_manifest(layoutId="second")
        (tmp / "a" / "x.oklm.json").write_text(json.dumps(first), encoding="utf-8")
        (tmp / "b" / "x.oklm.json").write_text(json.dumps(second), encoding="utf-8")
        rc, out, err = cli("--out", tmp / "out", tmp / "a" / "x.oklm.json", tmp / "b" / "x.oklm.json")
        check(rc == 1 and json.loads((tmp / "out" / "x.oklm.json").read_text(encoding="utf-8"))["layoutId"] == "first",
              f"--out : collision de nom refusee, premier fichier conserve ({err[-150:]!r})")

        # A-20 : joker
        rc, out, err = cli(tmp / "a" / "*.oklm.json")
        check(rc == 0 and out.count("migrated:") == 1, f"A-20 joker developpe ({out!r}, {err[-100:]!r})")

    # ecriture atomique : si le remplacement echoue, l'original est intact et aucun temporaire ne reste
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "keep.oklm.json"
        path.write_bytes(b"original")
        with mock.patch("os.replace", side_effect=OSError("disk full")):
            try:
                mg.write_manifest(path, mg.migrate(old_manifest()))
                check(False, "A-12 write_manifest : l'echec doit remonter")
            except OSError:
                check(True, "")
        check(path.read_bytes() == b"original", "A-12 ecriture atomique : l'original est intact apres un echec")
        check([p.name for p in Path(tmp).iterdir()] == ["keep.oklm.json"], "A-12 ecriture atomique : pas de temporaire")
        try:
            mg.write_manifest(path, {"x": float("nan")})
            check(False, "A-19 NaN : doit etre refuse")
        except ValueError:
            check(True, "")
        check(path.read_bytes() == b"original", "A-19 NaN : le fichier n'est pas touche")
        for fn in (lambda: mg.dumps({"x": float("inf")}), lambda: mg.manifest_bytes({"x": float("nan")}, expanded=True)):
            try:
                fn()
                check(False, "A-19 inf / nan : doit etre refuse")
            except ValueError:
                check(True, "")


def main():
    section_schema_version()
    section_version_label()
    section_collisions()
    section_groups_and_output()
    section_cli()
    if failures:
        print(f"ECHEC : {len(failures)} sur {counter['n']} verifications")
        for message in failures:
            if message:
                print("  - " + message)
        return 1
    print(f"OK: {counter['n']} verifications de la migration 0.1 -> 0.2, 0 echec.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
