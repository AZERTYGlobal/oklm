# -*- coding: utf-8 -*-
"""Validation OKLM v0.2 : meta-validation des schemas, exemples, une fixture positive et
une negative par regle du validateur (codes stables), migration 0.1 -> 0.2, rapports.

Usage : python validators/validate_v0_2.py  (depuis la racine du dossier OKLM)
Dependance : pip install jsonschema  (>= 4.x, Draft 2020-12)
"""
import copy
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "validators"))
sys.path.insert(0, str(BASE / "tools"))
import validate as v  # noqa: E402
import migrate_0_1_to_0_2 as migrate  # noqa: E402

manifest_schema = json.loads((BASE / "schemas" / "oklm-manifest.schema.json").read_text(encoding="utf-8"))
report_schema = json.loads((BASE / "schemas" / "oklm-conversion-report.schema.json").read_text(encoding="utf-8"))
example = json.loads((BASE / "examples" / "azerty-global-minimal.oklm.json").read_text(encoding="utf-8"))

failures = []
total = 0


def check(label, ok, detail=""):
    global total
    total += 1
    print(("OK   " if ok else "FAIL ") + label + (" -- " + detail if detail else ""))
    if not ok:
        failures.append(label)


def codes(manifest, strict=False, severity=None):
    found = v.analyze(manifest, manifest_schema, strict=strict)
    return sorted({f.code for f in found if severity is None or f.severity == severity})


def errors(manifest, strict=False):
    return codes(manifest, strict, "error")


def warnings(manifest, strict=False):
    return codes(manifest, strict, "warning")


# 1. Meta-validation
for label, schema in [("manifest schema est un JSON Schema 2020-12 valide", manifest_schema),
                      ("report schema est un JSON Schema 2020-12 valide", report_schema)]:
    try:
        Draft202012Validator.check_schema(schema)
        check(label, True)
    except Exception as e:  # noqa: BLE001
        check(label, False, str(e))
check("$id du schema manifeste en 0.2", "/0.2/" in manifest_schema["$id"])
check("aucune cloture additionalProperties:false dans le schema manifeste",
      "\"additionalProperties\": false" not in json.dumps(manifest_schema))

rv = Draft202012Validator(report_schema)

# 2. Les 6 exemples : valides, y compris en strict, sans avertissement
for path in sorted((BASE / "examples").glob("*.oklm.json")):
    manifest = json.loads(path.read_text(encoding="utf-8"))
    check("exemple valide en strict, sans avertissement : " + path.name,
          not codes(manifest, strict=True), str(codes(manifest, strict=True)))

# 3. Une regle, une fixture negative et une positive
def mutate(fn):
    m = copy.deepcopy(example)
    fn(m)
    return m


# E_SCHEMA : touche sans hid, id mal forme, locales absentes, deadKey mal forme, version non SemVer
check("E_SCHEMA : touche sans hid", "E_SCHEMA" in errors(mutate(lambda m: m["keys"][0].pop("hid"))))
check("E_SCHEMA : id de touche non ISO 9995-1", "E_SCHEMA" in errors(mutate(lambda m: m["keys"][0].update(id="Q"))))
check("E_SCHEMA : manifeste sans locales", "E_SCHEMA" in errors(mutate(lambda m: m.pop("locales"))))
check("E_SCHEMA : id de deadKey mal forme",
      "E_SCHEMA" in errors(mutate(lambda m: m["keys"][2]["levels"].update({"1": {"deadKey": "Circumflex!"}}))))
check("E_SCHEMA : version non SemVer (E2)", "E_SCHEMA" in errors(mutate(lambda m: m.update(version="2026"))))
check("version SemVer 1.2.3-rc.1+build.5 acceptee", not errors(mutate(lambda m: m.update(version="1.2.3-rc.1+build.5"))))
check("E_SCHEMA : touche sans levels ni role", "E_SCHEMA" in errors(mutate(lambda m: m["keys"][0].pop("levels"))))
check("E_SCHEMA : role modifier sans modifier",
      "E_SCHEMA" in errors(mutate(lambda m: m["keys"][0].update(role="modifier"))))
check("touche role modifier + modifier sans levels acceptee",
      not errors(mutate(lambda m: (m["keys"][0].pop("levels"), m["keys"][0].update(role="modifier", modifier="Level2Shift")))))
check("E_SCHEMA : ancienne sortie {modifier} retiree du schema (E22)",
      "E_SCHEMA" in errors(mutate(lambda m: m["keys"][0]["levels"].update({"3": {"modifier": "Level3Shift"}}))))
check("E_SCHEMA : membre prefixe hors extensions", "E_SCHEMA" in errors(mutate(lambda m: m.update(OKLM_x={}))))
check("E_SCHEMA : membre prefixe dans metadata", "E_SCHEMA" in errors(mutate(lambda m: m["metadata"].update(OKLM_siteView={}))))
check("E_SCHEMA : cle d'extensions sans prefixe",
      "E_SCHEMA" in errors(mutate(lambda m: m.update(extensions={"frame-keys": {}}))))
check("extensions prefixees acceptees sur racine, touche, sortie, deadKey, metadata, conformance, export",
      not errors(mutate(lambda m: (
          m.update(extensions={"OKLM_frameKeys": {}, "ACME_tool": {"x": 1}}),
          m["keys"][0].update(extensions={"EXT_shape": {"w": 2}}),
          m["keys"][2]["levels"]["1"].update(extensions={"EXT_hint": {}}),
          m["deadKeys"][0].update(extensions={"OKLM_note": {}}),
          m["metadata"].update(extensions={"OKLM_siteView": {"a": 1}}),
          m["conformance"][0].update(extensions={"OKLM_c": {}}),
          m["exports"][0].update(extensions={"OKLM_e": {}}),
          m.update(extensionsUsed=["ACME_tool", "OKLM_frameKeys"]),
      ))))

# E_DUPLICATE_KEY_ID, E_DUPLICATE_EXPORT_ID, E_DEADKEY_UNDEFINED
check("E_DUPLICATE_KEY_ID", "E_DUPLICATE_KEY_ID" in errors(mutate(lambda m: m["keys"].append(copy.deepcopy(m["keys"][0])))))
check("ids de touches uniques : fixture positive", "E_DUPLICATE_KEY_ID" not in errors(example))
check("E_DUPLICATE_EXPORT_ID",
      "E_DUPLICATE_EXPORT_ID" in errors(mutate(lambda m: m["exports"].append({"target": "xkb", "id": m["exports"][0].get("id", "a")}) if m["exports"][0].get("id") else m["exports"].extend([{"target": "xkb", "id": "dup"}, {"target": "xkb", "id": "dup"}]))))
check("E_DEADKEY_UNDEFINED",
      "E_DEADKEY_UNDEFINED" in errors(mutate(lambda m: m["keys"][2]["levels"].update({"1": {"deadKey": "nope"}}))))
check("references deadKey : fixture positive", "E_DEADKEY_UNDEFINED" not in errors(example))

# E_LAYERS_UNSUPPORTED
found = v.analyze(mutate(lambda m: m.update(layers=["base"])), manifest_schema)
check("E_LAYERS_UNSUPPORTED avec indication keys[].levels",
      any(f.code == "E_LAYERS_UNSUPPORTED" and "keys[].levels" in f.message for f in found))
check("layers : pas de W_UNKNOWN_MEMBER en double",
      not any(f.code == "W_UNKNOWN_MEMBER" and f.path == "layers" for f in found))

# E_SCHEMA_VERSION_MAJOR / W_SCHEMA_VERSION_MINOR
check("E_SCHEMA_VERSION_MAJOR : 1.0 refuse", "E_SCHEMA_VERSION_MAJOR" in errors(mutate(lambda m: m.update(schemaVersion="1.0"))))
check("W_SCHEMA_VERSION_MINOR : 0.3 valide, non supporte",
      errors(mutate(lambda m: m.update(schemaVersion="0.3"))) == [] and
      warnings(mutate(lambda m: m.update(schemaVersion="0.3"))) == ["W_SCHEMA_VERSION_MINOR"])
check("schemaVersion 0.2 sans avertissement", not codes(example))
check("E_SCHEMA : schemaVersion mal forme", "E_SCHEMA" in errors(mutate(lambda m: m.update(schemaVersion="v2"))))

# E_EXTENSIONS_REQUIRED
check("E_EXTENSIONS_REQUIRED : requis non utilise",
      "E_EXTENSIONS_REQUIRED" in errors(mutate(lambda m: m.update(extensionsUsed=["OKLM_a"], extensionsRequired=["OKLM_b"]))))
check("extensionsRequired inclus dans extensionsUsed : accepte",
      not errors(mutate(lambda m: m.update(extensionsUsed=["OKLM_a", "OKLM_b"], extensionsRequired=["OKLM_b"]))))
check("tableaux de capacites vides autorises",
      not errors(mutate(lambda m: m.update(extensionsUsed=[], extensionsRequired=[], featuresRequired=[]))))

# W_UNKNOWN_MEMBER (avertissement), erreur en strict
bad = mutate(lambda m: m.update(foo=1))
check("W_UNKNOWN_MEMBER : avertissement hors strict, manifeste valide",
      warnings(bad) == ["W_UNKNOWN_MEMBER"] and errors(bad) == [])
check("W_UNKNOWN_MEMBER : erreur en strict", "W_UNKNOWN_MEMBER" in errors(bad, strict=True))
bad = mutate(lambda m: m["keys"][0]["levels"].update({"1": {"deadKey": "circumflex", "extra": 1}}))
check("W_UNKNOWN_MEMBER : membre inconnu dans une sortie oneOf", "W_UNKNOWN_MEMBER" in warnings(bad))
bad = mutate(lambda m: m["metadata"].update(training={"anything": {"goes": [1, 2]}}))
check("blocs metadata non normatifs laisses libres, meme en strict", not codes(bad, strict=True))
bad = mutate(lambda m: m["keys"][0].update(typo="x"))
check("W_UNKNOWN_MEMBER : faute de frappe sur une touche, chemin donne",
      any(f.path == "keys[0].typo" for f in v.analyze(bad, manifest_schema)))

# W_GEOMETRY_UNKNOWN
check("W_GEOMETRY_UNKNOWN : famille inconnue, avertissement",
      warnings(mutate(lambda m: m.update(geometry=["zzz-full"]))) == ["W_GEOMETRY_UNKNOWN"])
check("W_GEOMETRY_UNKNOWN : erreur en strict", "W_GEOMETRY_UNKNOWN" in errors(mutate(lambda m: m.update(geometry=["zzz-full"])), strict=True))
check("geometry : ks-*, touch, custom et alias us / abnt2 connus",
      not codes(mutate(lambda m: m.update(geometry=["ks-full", "touch", "custom", "us-full", "abnt2"])), strict=True))

# E_HID_RANGE / E_W3C_CODE / E_DUPLICATE_CODE : strict seulement
check("E_HID_RANGE : 0x01 non physique", "E_HID_RANGE" in errors(mutate(lambda m: m["keys"][0].update(hid="0x01")), strict=True))
check("E_HID_RANGE : 0xE8 reserve", "E_HID_RANGE" in errors(mutate(lambda m: m["keys"][0].update(hid="0xE8")), strict=True))
check("E_HID_RANGE : hors strict, silencieux", "E_HID_RANGE" not in codes(mutate(lambda m: m["keys"][0].update(hid="0x01"))))
check("E_HID_RANGE : bornes 0x04 et 0xE7 acceptees",
      "E_HID_RANGE" not in errors({"keys": [{"id": "A01", "hid": "0x04"}, {"id": "A02", "hid": "0xE7"}]}, strict=True))
check("E_W3C_CODE : KeyQQ", "E_W3C_CODE" in errors(mutate(lambda m: m["keys"][0].update(code="KeyQQ")), strict=True))
check("E_DUPLICATE_CODE : deux Backslash",
      "E_DUPLICATE_CODE" in errors(mutate(lambda m: (m["keys"][0].update(code="Backslash"), m["keys"][1].update(code="Backslash"))), strict=True))

# 4. Rapports de conversion : valides + negatifs
report_export = {
    "schemaVersion": "0.2", "direction": "oklm-to-ldml",
    "source": {"format": "oklm", "file": "azerty-global.oklm.json", "version": "0.2"},
    "target": {"format": "ldml-keyboard-3", "file": "azerty-global.ldml.xml", "version": "48.2", "conformsTo": 45},
    "compatibilityLevel": "lossy-metadata", "mappedFields": ["keys", "deadKeys", "locales"],
    "skippedFields": [{"path": "exports", "reason": "OKLM tooling declaration, out of LDML scope"}],
    "lossyMappings": [], "roundTripConfidence": "high", "warnings": [], "errors": [],
    "generator": {"name": "oklm-tools", "version": "0.0.1"},
}
check("rapport oklm-to-ldml valide", not list(rv.iter_errors(report_export)))
report_import = {
    "schemaVersion": "0.2", "direction": "ldml-to-oklm",
    "source": {"format": "ldml-keyboard-3", "version": "48.2", "conformsTo": 45},
    "target": {"format": "oklm", "version": "0.2"}, "compatibilityLevel": "lossless-core",
    "mappedFields": ["keys", "transforms"], "skippedFields": [], "lossyMappings": [],
    "preservedAsExtensions": [{"construct": "flicks", "extensionNamespace": "OKLM_ldml"}],
    "unsupportedConstructs": [], "suggestedEnrichmentTasks": [], "warnings": [], "errors": [],
}
check("rapport ldml-to-oklm valide", not list(rv.iter_errors(report_import)))
bad = copy.deepcopy(report_export); del bad["roundTripConfidence"]
check("rejet attendu : export sans roundTripConfidence", bool(list(rv.iter_errors(bad))))
bad = copy.deepcopy(report_import); del bad["preservedAsExtensions"]
check("rejet attendu : import sans preservedAsExtensions", bool(list(rv.iter_errors(bad))))
bad = copy.deepcopy(report_export); bad["compatibilityLevel"] = "perfect"
check("rejet attendu : compatibilityLevel hors enum", bool(list(rv.iter_errors(bad))))
ok_unsupported = copy.deepcopy(report_export); ok_unsupported["compatibilityLevel"] = "unsupported"
check("compatibilityLevel unsupported accepte (D33)", not list(rv.iter_errors(ok_unsupported)))
for direction, fmt in (("oklm-to-klc", "windows-klc"), ("oklm-to-streamdeck", "streamdeck-profile")):
    r = copy.deepcopy(report_export); r["direction"] = direction; r["target"] = {"format": fmt}
    check(f"rapport {direction} valide", not list(rv.iter_errors(r)))

# 5. Migration 0.1 -> 0.2
check("semver_of : 2026 -> 2026.0.0", migrate.semver_of("2026") == ("2026.0.0", None))
check("semver_of : 1.0 -> 1.0.0", migrate.semver_of("1.0") == ("1.0.0", None))
check("semver_of : 1.2.3 inchange", migrate.semver_of("1.2.3") == ("1.2.3", None))
check("semver_of : libelle avec annee", migrate.semver_of("NF Z71-300:2019 (AZERTY option)") == ("2019.0.0", "NF Z71-300:2019 (AZERTY option)"))
check("semver_of : libelle sans annee", migrate.semver_of("ANSI (US 104-key)") == ("1.0.0", "ANSI (US 104-key)"))
old = copy.deepcopy(example)
old["schemaVersion"] = "0.1"; old["version"] = "2026"
old["keys"][0]["levels"]["3"] = {"modifier": "Level3Shift"}
old["keys"][1] = {"id": "C00", "hid": "0x39", "levels": {"1": {"modifier": "CapsLock"}}}
old["metadata"]["OKLM_siteView"] = {"a": 1}
old["extensions"] = {"frame-keys": {"x": 1}, "my-tool": {}}
new = migrate.migrate(old)
check("migration : schemaVersion et version", new["schemaVersion"] == "0.2" and new["version"] == "2026.0.0")
check("migration : modificateur de niveau -> role/modifier sur la touche, niveau retire",
      new["keys"][1]["role"] == "modifier" and new["keys"][1]["modifier"] == "CapsLock" and "levels" not in new["keys"][1])
check("migration : sortie {modifier} dans une touche a plusieurs niveaux",
      new["keys"][0]["role"] == "modifier" and "3" not in new["keys"][0]["levels"] and "1" in new["keys"][0]["levels"])
check("migration : OKLM_siteView range sous metadata.extensions",
      new["metadata"]["extensions"] == {"OKLM_siteView": {"a": 1}} and "OKLM_siteView" not in new["metadata"])
check("migration : namespaces renommes", sorted(new["extensions"]) == ["EXT_MyTool", "OKLM_frameKeys"])
check("migration : extensionsUsed rempli", new["extensionsUsed"] == ["EXT_MyTool", "OKLM_frameKeys", "OKLM_siteView"])
check("migration : resultat valide en strict", not errors(new, strict=True), str(errors(new, strict=True)))
check("migration : idempotente", migrate.migrate(new) == new)
check("migration : l'entree n'est pas modifiee", old["schemaVersion"] == "0.1")
check("migration : sortie deterministe", migrate.dumps(migrate.migrate(old)) == migrate.dumps(migrate.migrate(old)))
check("migration : la sortie compacte est relue a l'identique",
      json.loads(migrate.dumps(new)) == new)

print()
if failures:
    print(f"ECHEC : {len(failures)} test(s) en echec sur {total} : {failures}")
    sys.exit(1)
print(f"SUCCES : {total} verifications de validation passent.")
