# -*- coding: utf-8 -*-
"""Round-trip measurement for the LDML bridge (gate 3).

`core_view` reduces a manifest to what both formats carry: the keys (id, HID), their outputs addressed by
the *set of functional qualifiers* that selects the level (so level 5 and level 7 that mean the same
modifiers compare equal), the dead keys (display, composition list in order, fallback), the name, the
version and the primary locale. `compare` counts what is equal.

    oklm_round_trip(manifest)  OKLM -> LDML -> OKLM  (what the exporter and the importer keep)
    ldml_round_trip(xml_text)  LDML -> OKLM -> LDML -> OKLM  (fixed point of the pair)
"""
from exporters import ldml as ldml_exporter
from exporters.common import resolve_level_modifiers
from importers import ldml as ldml_importer

# fields an LDML file cannot carry back; listed when the original has them and the result differs
LOSSY_BY_DESIGN = ("authors", "license", "geometry", "description", "conformance", "exports", "metadata",
                   "extensions", "extensionsUsed", "extensionsRequired", "featuresRequired")


def _qualifiers(manifest):
    resolved = resolve_level_modifiers(manifest)
    return {level: frozenset(sel) for level, sel in resolved.items()}


def core_view(manifest):
    """Normalised core, restricted to what the LDML exporter can write."""
    qualifiers = _qualifiers(manifest)
    exportable = set(ldml_exporter.QUALIFIER_TO_LDML)
    view_keys = {}
    for key in manifest["keys"]:
        if key.get("role") == "modifier":
            continue
        by_selector = {}
        for level, out in key.get("levels", {}).items():
            if level == "1":
                selector = frozenset()
            else:
                selector = qualifiers.get(level)
                if selector is None or not selector <= exportable:
                    continue
            by_selector[selector] = ("deadKey", out["deadKey"]) if isinstance(out, dict) else out
        if by_selector:
            view_keys[key["id"]] = (key["hid"], by_selector)
    dead = {}
    for entry in manifest.get("deadKeys", []):
        dead[entry["id"]] = {
            "display": entry.get("display"),
            "compositions": list(entry["compositions"].items()),
            "fallback": entry.get("fallback"),
        }
    return {
        "name": manifest["name"],
        "version": manifest["version"],
        "locale": manifest["locales"][0],
        "keys": view_keys,
        "deadKeys": dead,
    }


def compare(expected, got):
    """Counts of equal items between two core views."""
    result = {
        "keys": [0, len(expected["keys"])],
        "outputs": [0, 0],
        "deadKeys": [0, len(expected["deadKeys"])],
        "compositions": [0, 0],
        "scalars": [0, 3],
        "differences": [],
    }
    for scalar in ("name", "version", "locale"):
        if expected[scalar] == got[scalar]:
            result["scalars"][0] += 1
        else:
            result["differences"].append(f"{scalar}: {expected[scalar]!r} != {got[scalar]!r}")
    for key_id, (hid, outputs) in expected["keys"].items():
        result["outputs"][1] += len(outputs)
        other = got["keys"].get(key_id)
        if other is None:
            result["differences"].append(f"key {key_id} missing")
            continue
        if other[0] != hid:
            result["differences"].append(f"key {key_id}: hid {hid} != {other[0]}")
            continue
        result["keys"][0] += 1
        for selector, out in outputs.items():
            if other[1].get(selector) == out:
                result["outputs"][0] += 1
            else:
                result["differences"].append(f"key {key_id} {sorted(selector)}: {out!r} != {other[1].get(selector)!r}")
    result["differences"].extend(f"key {k} unexpected" for k in got["keys"] if k not in expected["keys"])
    for dead_id, entry in expected["deadKeys"].items():
        result["compositions"][1] += len(entry["compositions"])
        other = got["deadKeys"].get(dead_id)
        if other is None:
            result["differences"].append(f"dead key {dead_id} missing")
            continue
        if other["display"] == entry["display"] and other["fallback"] == entry["fallback"] and other["compositions"] == entry["compositions"]:
            result["deadKeys"][0] += 1
        else:
            result["differences"].append(f"dead key {dead_id} differs")
        shared = set(other["compositions"]) & set(entry["compositions"])
        result["compositions"][0] += len(shared)
    result["differences"].extend(f"dead key {d} unexpected" for d in got["deadKeys"] if d not in expected["deadKeys"])
    return result


def is_equal(result):
    return not result["differences"] and all(a == b for a, b in (result["keys"], result["outputs"], result["deadKeys"], result["compositions"], result["scalars"]))


def oklm_round_trip(manifest, source_file="x.oklm.json"):
    """OKLM -> LDML -> OKLM. Returns (comparison, lost_fields, export_report, import_report)."""
    xml, export_report = ldml_exporter.export(manifest, source_file=source_file)
    if xml is None:
        return None, [], export_report, None
    back, import_report = ldml_importer.import_ldml(xml, source_file="round-trip.ldml.xml")
    if back is None:
        return None, [], export_report, import_report
    comparison = compare(core_view(manifest), core_view(back))
    lost = [f for f in LOSSY_BY_DESIGN if f in manifest and manifest[f] != back.get(f)]
    if manifest["locales"] != back["locales"]:
        lost.append("locales")
    return comparison, lost, export_report, import_report


def ldml_round_trip(xml_text, source_file="x.xml", **options):
    """LDML -> OKLM (A) -> LDML -> OKLM (B). Returns (A, B, comparison of A and B, exported LDML text, re-exported text)."""
    first, first_report = ldml_importer.import_ldml(xml_text, source_file=source_file, **options)
    if first is None:
        return None, None, None, None, None
    xml, _ = ldml_exporter.export(first, source_file=source_file)
    if xml is None:
        return first, None, None, None, None
    second, _ = ldml_importer.import_ldml(xml, source_file="round-trip.ldml.xml", **options)
    if second is None:
        return first, None, None, xml, None
    again, _ = ldml_exporter.export(second, source_file=source_file)
    return first, second, compare(core_view(first), core_view(second)), xml, again
