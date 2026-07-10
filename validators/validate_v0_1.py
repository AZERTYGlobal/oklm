# -*- coding: utf-8 -*-
"""Validation OKLM v0.1 : méta-validation des schémas, exemple, tests négatifs, rapports.

Usage : python validators/validate_v0_1.py  (depuis la racine du dossier OKLM)
Dépendance : pip install jsonschema  (>= 4.x, Draft 2020-12)
"""
import copy
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

BASE = Path(__file__).resolve().parent.parent

manifest_schema = json.loads((BASE / "schemas" / "oklm-manifest.schema.json").read_text(encoding="utf-8"))
report_schema = json.loads((BASE / "schemas" / "oklm-conversion-report.schema.json").read_text(encoding="utf-8"))
example = json.loads((BASE / "examples" / "azerty-global-minimal.oklm.json").read_text(encoding="utf-8"))

failures = []

def check(label, ok, detail=""):
    print(("OK   " if ok else "FAIL ") + label + (" -- " + detail if detail else ""))
    if not ok:
        failures.append(label)

# 1. Méta-validation : les deux fichiers sont des JSON Schema 2020-12 valides
for label, schema in [("manifest schema est un JSON Schema 2020-12 valide", manifest_schema),
                      ("report schema est un JSON Schema 2020-12 valide", report_schema)]:
    try:
        Draft202012Validator.check_schema(schema)
        check(label, True)
    except Exception as e:
        check(label, False, str(e))

mv = Draft202012Validator(manifest_schema)
rv = Draft202012Validator(report_schema)

# 2. L'exemple valide contre le schéma manifeste
errors = sorted(mv.iter_errors(example), key=lambda e: list(e.path))
check("exemple azerty-global-minimal valide contre le schéma manifeste", not errors,
      "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:5]))

# 3. Cohérences hors JSON Schema (unicité des ids, résolution des références deadKey)
key_ids = [k["id"] for k in example["keys"]]
check("ids de touches uniques", len(key_ids) == len(set(key_ids)))
dead_ids = {d["id"] for d in example.get("deadKeys", [])}
refs = set()
for k in example["keys"]:
    for out in list(k.get("levels", {}).values()) + [o for g in k.get("groups", {}).values() for o in g.values()]:
        if isinstance(out, dict) and "deadKey" in out:
            refs.add(out["deadKey"])
check("toutes les références deadKey sont définies", refs <= dead_ids, str(refs - dead_ids) if refs - dead_ids else "")

# 4. Tests négatifs manifeste : chacun DOIT échouer
def must_fail(label, instance):
    check("rejet attendu : " + label, bool(list(mv.iter_errors(instance))))

bad = copy.deepcopy(example); del bad["keys"][0]["hid"]
must_fail("touche sans hid (D1)", bad)
bad = copy.deepcopy(example); bad["keys"][0]["id"] = "Q"
must_fail("id de touche non ISO 9995-1", bad)
bad = copy.deepcopy(example); bad["layers"] = ["base", "shift"]
must_fail("champ 'layers' (terminologie pré-D2/D14)", bad)
bad = copy.deepcopy(example); bad["keys"][2]["levels"]["1"] = {"deadKey": "Circumflex!"}
must_fail("id de deadKey mal formé", bad)
bad = copy.deepcopy(example); del bad["locales"]
must_fail("manifeste sans locales", bad)

# 5. Instances de rapport de conversion : valides + négatives
report_export = {
    "schemaVersion": "0.1",
    "direction": "oklm-to-ldml",
    "source": {"format": "oklm", "file": "azerty-global.oklm.json", "version": "0.1"},
    "target": {"format": "ldml-keyboard-3", "file": "azerty-global.ldml.xml", "version": "48.2", "conformsTo": 45},
    "compatibilityLevel": "lossy-metadata",
    "mappedFields": ["keys", "deadKeys", "locales"],
    "skippedFields": [
        {"path": "metadata.links", "reason": "OKLM-only metadata, not representable in LDML Keyboard 3.0"},
        {"path": "exports", "reason": "OKLM tooling declaration, out of LDML scope"}
    ],
    "lossyMappings": [
        {"path": "deadKeys.circumflex.fallback", "detail": "Mapped to a final transform rule; platform cancellation semantics differ."}
    ],
    "roundTripConfidence": "high",
    "warnings": [],
    "errors": [],
    "generator": {"name": "oklm-tools", "version": "0.0.1"}
}
errs = list(rv.iter_errors(report_export))
check("rapport oklm-to-ldml valide", not errs, "; ".join(e.message for e in errs[:5]))

report_import = {
    "schemaVersion": "0.1",
    "direction": "ldml-to-oklm",
    "source": {"format": "ldml-keyboard-3", "version": "48.2", "conformsTo": 45},
    "target": {"format": "oklm", "version": "0.1"},
    "compatibilityLevel": "lossless-core",
    "mappedFields": ["keys", "transforms"],
    "skippedFields": [],
    "lossyMappings": [],
    "preservedAsExtensions": [{"construct": "flicks", "extensionNamespace": "ldml"}],
    "unsupportedConstructs": [],
    "suggestedEnrichmentTasks": ["Add training metadata", "Add dynamic legends"],
    "warnings": [],
    "errors": []
}
errs = list(rv.iter_errors(report_import))
check("rapport ldml-to-oklm valide", not errs, "; ".join(e.message for e in errs[:5]))

bad = copy.deepcopy(report_export); del bad["roundTripConfidence"]
check("rejet attendu : export sans roundTripConfidence", bool(list(rv.iter_errors(bad))))
bad = copy.deepcopy(report_import); del bad["preservedAsExtensions"]
check("rejet attendu : import sans preservedAsExtensions", bool(list(rv.iter_errors(bad))))
bad = copy.deepcopy(report_export); bad["compatibilityLevel"] = "perfect"
check("rejet attendu : compatibilityLevel hors enum", bool(list(rv.iter_errors(bad))))

print()
if failures:
    print(f"ECHEC : {len(failures)} test(s) en échec : {failures}")
    sys.exit(1)
print("SUCCES : tous les tests de validation passent.")
