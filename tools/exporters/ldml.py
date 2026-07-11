# -*- coding: utf-8 -*-
"""OKLM -> LDML Keyboard 3 exporter (draft v1, one-way).

Targets the CLDR/UTS #35 Part 7 "keyboard3" format. Scope and known
approximations (see CONVERSIONS.md and the generated report):

- Levels 1-4 map to the LDML modifier components "none", "shift", "altR"
  and "altR shift". Level3Shift is exported as "altR" (AltGr); the actual
  physical binding (AltGr vs Ctrl+Alt vs macOS Option) is platform-specific
  (SPEC.md "Level Selectors") and this is recorded as a lossy mapping.
- Levels 5-8 export only when levelSelectors resolves them to a combination
  of Level2Shift/Level3Shift/CapsLock (the only functional qualifiers with a
  direct LDML modifier component: shift, altR, caps). Level5Shift and
  NumLock have no LDML equivalent and cause that level to be skipped.
- Physical key placement uses a custom, self-contained <form> (scanCodes),
  which UTS #35 permits for keyboards not intended for the CLDR repository
  (our manifests only cover the alphanumeric section, not a full physical
  keyboard). Placement is derived from each key's mandatory `hid` (USB HID
  usage page 0x07) via the standard USB-to-PS/2-Set-1 scan code table.
- Dead keys compile to LDML markers (`\\m{id}`) and simple <transform>
  rules, one per composition entry, in manifest document order. `fallback`
  is approximated as a transform matching the bare marker; this is recorded
  as a lossy mapping because bare-marker fallback/cancellation semantics are
  not fully pinned down across implementations.
- OKLM-only metadata (description, conformance, exports, metadata,
  extensions) is never exported; always recorded as skipped.
"""
from .common import (
    ReportBuilder,
    resolve_level_modifiers,
    levels_used_by,
    reject_unsupported_v1_scope,
    skip_oklm_only_metadata,
    xml_escape,
)

# USB HID keyboard-usage-page (0x07) -> PC/AT Set 1 scan code, for the
# alphanumeric-section keys covered by OKLM v1 (Microsoft "Keyboard Scan
# Code Specification" / USB-IF HID-to-PS2 translation table).
HID_TO_SCANCODE1 = {
    "0x1E": "02", "0x1F": "03", "0x20": "04", "0x21": "05", "0x22": "06",
    "0x23": "07", "0x24": "08", "0x25": "09", "0x26": "0A", "0x27": "0B",
    "0x2D": "0C", "0x2E": "0D",
    "0x14": "10", "0x1A": "11", "0x08": "12", "0x15": "13", "0x17": "14",
    "0x1C": "15", "0x18": "16", "0x0C": "17", "0x12": "18", "0x13": "19",
    "0x2F": "1A", "0x30": "1B", "0x35": "29",
    "0x04": "1E", "0x16": "1F", "0x07": "20", "0x09": "21", "0x0A": "22",
    "0x0B": "23", "0x0D": "24", "0x0E": "25", "0x0F": "26", "0x33": "27",
    "0x34": "28", "0x31": "2B",
    "0x1D": "2C", "0x1B": "2D", "0x06": "2E", "0x19": "2F", "0x05": "30",
    "0x11": "31", "0x10": "32", "0x36": "33", "0x37": "34", "0x38": "35",
    "0x2C": "39",
    "0x64": "56",
}

ROW_ORDER = "EDCBA"

# Functional qualifier (SPEC.md "Level Selectors") -> LDML modifier component
# (UTS #35 Part 7 valid components: none, alt, altL, altR, caps, ctrl,
# ctrlL, ctrlR, shift, other).
QUALIFIER_TO_LDML = {
    "Level2Shift": "shift",
    "Level3Shift": "altR",
    "CapsLock": "caps",
}
MODIFIER_ORDER = ["caps", "altR", "shift"]


def _rows(manifest):
    by_row = {}
    for key in manifest.get("keys", []):
        letter = key["id"][0]
        by_row.setdefault(letter, []).append(key)
    rows = []
    for letter in ROW_ORDER:
        if letter in by_row:
            rows.append(sorted(by_row[letter], key=lambda k: int(k["id"][1:])))
    return rows


def _layer_modifiers(level, resolved, report, warned_altR):
    if level == "1":
        return "none"
    qualifiers = resolved.get(level)
    if qualifiers is None:
        report.skip(f"keys[].levels.{level}", "no levelSelectors entry (explicit or default) for this level")
        return None
    tokens = set()
    for qualifier in qualifiers:
        token = QUALIFIER_TO_LDML.get(qualifier)
        if token is None:
            report.skip(
                f"keys[].levels.{level}",
                f"functional qualifier '{qualifier}' has no LDML modifier component equivalent",
            )
            return None
        tokens.add(token)
        if token == "altR" and "Level3Shift" not in warned_altR:
            warned_altR.add("Level3Shift")
            report.lossy(
                "levelSelectors.Level3Shift",
                "exported as LDML modifier component 'altR' (AltGr); actual physical binding "
                "(AltGr vs Ctrl+Alt vs macOS Option) is platform-specific per SPEC.md",
            )
    return " ".join(t for t in MODIFIER_ORDER if t in tokens)


def export(manifest, source_file=None):
    """Returns (xml_text_or_None, report_dict)."""
    report = ReportBuilder(
        direction="oklm-to-ldml",
        source={"format": "oklm", "file": source_file, "version": manifest.get("schemaVersion")},
        target={"format": "ldml-keyboard-3"},
    )
    report.round_trip_confidence = "medium"

    if reject_unsupported_v1_scope(report, manifest):
        return None, report.build()

    conforms_to = 45
    for export_target in manifest.get("exports", []):
        if export_target.get("target") == "ldml-keyboard-3":
            conforms_to = export_target.get("options", {}).get("conformsTo", 45)
            break

    locales = manifest["locales"]
    primary_locale = locales[0]
    report.mapped("locales")
    if len(locales) > 1:
        report.lossy("locales", f"only the primary locale '{primary_locale}' is exported; LDML keyboard3 declares one locale")

    for field in ("layoutId", "authors", "license"):
        report.skip(field, "no LDML info attribute for this OKLM identity/provenance field in the v1 exporter")

    rows = _rows(manifest)
    unmapped_hid = []
    for row in rows:
        for key in row:
            if key["hid"] not in HID_TO_SCANCODE1:
                unmapped_hid.append((key["id"], key["hid"]))
    if unmapped_hid:
        for key_id, hid in unmapped_hid:
            report.error(f"key {key_id}: HID {hid} has no known PC/AT Set 1 scan code mapping in the v1 exporter")
        return None, report.build()

    resolved = resolve_level_modifiers(manifest)
    used_levels = sorted(levels_used_by(manifest), key=int)
    warned_altR = set()

    layers = []  # list of (modifiers_string, level)
    for level in used_levels:
        modifiers = _layer_modifiers(level, resolved, report, warned_altR)
        if modifiers is not None:
            layers.append((modifiers, level))
    if not layers:
        report.error("no exportable level (level 1 is always expected)")
        return None, report.build()
    report.mapped("keys")
    report.mapped("keys[].levels")
    if "levelSelectors" in manifest:
        report.mapped("levelSelectors")

    dead_keys = manifest.get("deadKeys", [])
    dead_key_ids = {dk["id"] for dk in dead_keys}

    key_elements = []  # (id, output)
    layer_rows = {level: [] for _, level in layers}
    for row in rows:
        for level in layer_rows:
            layer_rows[level].append([])
        for key in row:
            for _, level in layers:
                out = key.get("levels", {}).get(level)
                if out is None:
                    continue
                elem_id = f"k_{key['id']}_{level}"
                if isinstance(out, str):
                    output = out
                else:
                    output = f"\\m{{{out['deadKey']}}}"
                key_elements.append((elem_id, output))
                layer_rows[level][-1].append(elem_id)

    form_id = f"{manifest['layoutId']}-form"
    scancode_rows = []
    for row in rows:
        codes = " ".join(HID_TO_SCANCODE1[key["hid"]] for key in row)
        scancode_rows.append(codes)

    displays = []
    transforms = []
    for dk in dead_keys:
        marker = f"\\m{{{dk['id']}}}"
        if "display" in dk:
            displays.append((marker, dk["display"]))
        for base, result in dk.get("compositions", {}).items():
            transforms.append((f"{marker}{base}", result))
        if "fallback" in dk:
            transforms.append((marker, dk["fallback"]))
            report.lossy(
                f"deadKeys[{dk['id']}].fallback",
                "approximated as a transform matching the bare marker; bare-marker fallback/"
                "cancellation semantics are not fully pinned down across implementations",
            )
    if dead_keys:
        report.mapped("deadKeys")

    skip_oklm_only_metadata(report, manifest)

    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(
        f'<keyboard3 xmlns="https://schemas.unicode.org/cldr/{conforms_to}/keyboard3" '
        f'locale="{xml_escape(primary_locale)}" conformsTo="{conforms_to}">'
    )
    lines.append(f'  <version number="{xml_escape(str(manifest["version"]))}"/>')
    lines.append(f'  <info name="{xml_escape(manifest["name"])}"/>')
    lines.append("  <keys>")
    for elem_id, output in key_elements:
        lines.append(f'    <key id="{elem_id}" output="{xml_escape(output)}"/>')
    lines.append("  </keys>")
    if displays:
        lines.append("  <displays>")
        for marker, display in displays:
            lines.append(f'    <display output="{xml_escape(marker)}" display="{xml_escape(display)}"/>')
        lines.append("  </displays>")
    lines.append("  <forms>")
    lines.append(f'    <form id="{form_id}">')
    for codes in scancode_rows:
        lines.append(f'      <scanCodes codes="{codes}"/>')
    lines.append("    </form>")
    lines.append("  </forms>")
    lines.append(f'  <layers formId="{form_id}">')
    for modifiers, level in layers:
        lines.append(f'    <layer modifiers="{modifiers}">')
        for row_ids in layer_rows[level]:
            lines.append(f'      <row keys="{" ".join(row_ids)}"/>')
        lines.append("    </layer>")
    lines.append("  </layers>")
    if transforms:
        lines.append('  <transforms type="simple">')
        lines.append("    <transformGroup>")
        for from_seq, to in transforms:
            lines.append(f'      <transform from="{xml_escape(from_seq)}" to="{xml_escape(to)}"/>')
        lines.append("    </transformGroup>")
        lines.append("  </transforms>")
    lines.append("</keyboard3>")

    return "\n".join(lines), report.build()
