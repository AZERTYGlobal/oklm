# -*- coding: utf-8 -*-
"""OKLM -> Apple .keylayout exporter (draft v1, one-way).

Targets the macOS `KeyboardLayout.dtd` format (`<keyboard>` root). Scope and
known approximations (see CONVERSIONS.md and the generated report):

- Physical placement uses each key's mandatory `hid` (USB HID usage page
  0x07) mapped to the standard macOS virtual keycode for the alphanumeric
  section (Apple `Events.h` kVK_ANSI_* / kVK_ISO_Section constants).
- The `<layouts>` hardware-detection range is not modeled per OKLM geometry
  in v1: every export uses the generic `first="0" last="17" mapSet="ANSI"`
  range from Apple's own reference example. This only affects which real
  keyboard model auto-selects the layout on first plug-in, not the mapping
  itself, and is recorded as a lossy mapping.
- Levels 1-4 map to modifier combinations "", "anyShift", "anyOption",
  "anyShift anyOption". Level3Shift is exported as "anyOption"; the actual
  physical binding is platform-specific (SPEC.md), recorded as lossy.
  Levels 5-8 export only when levelSelectors resolves to a combination of
  Level2Shift/Level3Shift/CapsLock (the only qualifiers with a direct
  modifier equivalent: anyShift, anyOption, caps).
- Dead keys compile to the macOS `<actions>`/`<terminators>` state machine:
  the dead key's own key triggers a state via `next=`; every base character
  that participates in any composition gets a shared `<action>` with one
  `<when state="...">` per dead key it composes with. Dead-key presses emit
  no visible glyph while pending (`display` is not used for the trigger
  itself), matching the standard macOS convention.
- OKLM-only metadata (description, conformance, exports, metadata,
  extensions) is never exported; always recorded as skipped.
"""
import zlib

from .common import (
    ReportBuilder,
    resolve_level_modifiers,
    levels_used_by,
    reject_unsupported_v1_scope,
    skip_oklm_only_metadata,
    xml_escape,
)

# USB HID keyboard-usage-page (0x07) -> macOS virtual keycode, for the
# alphanumeric-section keys covered by OKLM v1 (Apple HIToolbox Events.h
# kVK_ANSI_* / kVK_ISO_Section constants).
HID_TO_MACVK = {
    "0x04": "0", "0x16": "1", "0x07": "2", "0x09": "3", "0x0B": "4",
    "0x0A": "5", "0x1D": "6", "0x1B": "7", "0x06": "8", "0x19": "9",
    "0x64": "10", "0x05": "11", "0x14": "12", "0x1A": "13", "0x08": "14",
    "0x15": "15", "0x1C": "16", "0x17": "17", "0x1E": "18", "0x1F": "19",
    "0x20": "20", "0x21": "21", "0x23": "22", "0x22": "23", "0x2E": "24",
    "0x26": "25", "0x24": "26", "0x2D": "27", "0x25": "28", "0x27": "29",
    "0x30": "30", "0x12": "31", "0x18": "32", "0x2F": "33", "0x0C": "34",
    "0x13": "35", "0x0F": "37", "0x0D": "38", "0x34": "39", "0x0E": "40",
    "0x33": "41", "0x31": "42", "0x36": "43", "0x38": "44", "0x11": "45",
    "0x10": "46", "0x37": "47", "0x2C": "49", "0x35": "50",
}

QUALIFIER_TO_MAC = {
    "Level2Shift": "anyShift",
    "Level3Shift": "anyOption",
    "CapsLock": "caps",
}
MODIFIER_ORDER = ["caps", "anyOption", "anyShift"]


def _char_action_id(text):
    return "char_" + "_".join(f"{ord(c):04x}" for c in text)


def _layer_modifiers(level, resolved, report, warned_option):
    if level == "1":
        return ""
    qualifiers = resolved.get(level)
    if qualifiers is None:
        report.skip(f"keys[].levels.{level}", "no levelSelectors entry (explicit or default) for this level")
        return None
    tokens = set()
    for qualifier in qualifiers:
        token = QUALIFIER_TO_MAC.get(qualifier)
        if token is None:
            report.skip(
                f"keys[].levels.{level}",
                f"functional qualifier '{qualifier}' has no macOS modifier equivalent",
            )
            return None
        tokens.add(token)
        if token == "anyOption" and "Level3Shift" not in warned_option:
            warned_option.add("Level3Shift")
            report.lossy(
                "levelSelectors.Level3Shift",
                "exported as macOS modifier 'anyOption'; actual physical binding "
                "(AltGr vs Ctrl+Alt vs macOS Option) is platform-specific per SPEC.md",
            )
    return " ".join(t for t in MODIFIER_ORDER if t in tokens)


def export(manifest, source_file=None):
    """Returns (keylayout_xml_or_None, report_dict)."""
    report = ReportBuilder(
        direction="oklm-to-keylayout",
        source={"format": "oklm", "file": source_file, "version": manifest.get("schemaVersion")},
        target={"format": "apple-keylayout"},
    )
    report.round_trip_confidence = "medium"

    if reject_unsupported_v1_scope(report, manifest):
        return None, report.build()

    unmapped_hid = [
        (key["id"], key["hid"]) for key in manifest.get("keys", []) if key["hid"] not in HID_TO_MACVK
    ]
    if unmapped_hid:
        for key_id, hid in unmapped_hid:
            report.error(f"key {key_id}: HID {hid} has no known macOS virtual keycode mapping in the v1 exporter")
        return None, report.build()

    resolved = resolve_level_modifiers(manifest)
    used_levels = sorted(levels_used_by(manifest), key=int)
    warned_option = set()

    exportable = []  # (level, modifiers)
    for level in used_levels:
        modifiers = _layer_modifiers(level, resolved, report, warned_option)
        if modifiers is not None:
            exportable.append((level, modifiers))
    if not exportable:
        report.error("no exportable level (level 1 is always expected)")
        return None, report.build()
    report.mapped("keys")
    report.mapped("keys[].levels")
    if "levelSelectors" in manifest:
        report.mapped("levelSelectors")

    dead_keys = manifest.get("deadKeys", [])
    dead_by_id = {dk["id"]: dk for dk in dead_keys}

    # Reverse index: base char -> [(deadKeyId, result), ...], in deadKeys/
    # compositions document order.
    base_to_compositions = {}
    for dk in dead_keys:
        for base, result in dk.get("compositions", {}).items():
            base_to_compositions.setdefault(base, []).append((dk["id"], result))

    dead_ids_used = set()
    key_lines = []  # per (level) -> list of key XML lines
    per_level_lines = {level: [] for level, _ in exportable}
    max_output_len = 1

    for key in manifest.get("keys", []):
        vk = HID_TO_MACVK[key["hid"]]
        for level, _ in exportable:
            out = key.get("levels", {}).get(level)
            if out is None:
                continue
            if isinstance(out, str):
                max_output_len = max(max_output_len, len(out.encode("utf-16-le")) // 2)
                if out in base_to_compositions:
                    per_level_lines[level].append(f'      <key code="{vk}" action="{_char_action_id(out)}"/>')
                else:
                    per_level_lines[level].append(f'      <key code="{vk}" output="{xml_escape(out)}"/>')
            else:
                dk_id = out["deadKey"]
                dead_ids_used.add(dk_id)
                per_level_lines[level].append(f'      <key code="{vk}" action="dk_{dk_id}"/>')

    if dead_keys:
        report.mapped("deadKeys")

    action_blocks = []
    for base in sorted(base_to_compositions, key=lambda c: [ord(ch) for ch in c]):
        action_id = _char_action_id(base)
        whens = [f'    <when state="none" output="{xml_escape(base)}"/>']
        for dk_id, result in base_to_compositions[base]:
            max_output_len = max(max_output_len, len(result.encode("utf-16-le")) // 2)
            whens.append(f'    <when state="{dk_id}" output="{xml_escape(result)}"/>')
        action_blocks.append(f'  <action id="{action_id}">\n' + "\n".join(whens) + "\n  </action>")

    for dk_id in sorted(dead_ids_used):
        action_blocks.append(f'  <action id="dk_{dk_id}">\n    <when state="none" next="{dk_id}"/>\n  </action>')

    terminator_lines = []
    for dk in dead_keys:
        if dk["id"] not in dead_ids_used:
            continue
        if "fallback" in dk:
            terminator_lines.append(f'    <when state="{dk["id"]}" output="{xml_escape(dk["fallback"])}"/>')
        elif "display" in dk:
            terminator_lines.append(f'    <when state="{dk["id"]}" output="{xml_escape(dk["display"])}"/>')
            report.lossy(
                f"deadKeys[{dk['id']}]",
                "no 'fallback' declared; the dead key's 'display' character is used as the "
                "macOS terminator output instead",
            )
        else:
            report.warn(
                f"deadKeys[{dk['id']}]: no 'fallback' or 'display' declared; no terminator "
                "emitted, behavior when input matches no composition is undefined on macOS"
            )

    modifier_select = []
    keymap_blocks = []
    for index, (level, modifiers) in enumerate(exportable):
        modifier_select.append(f'    <keyMapSelect mapIndex="{index}">\n      <modifier keys="{modifiers}"/>\n    </keyMapSelect>')
        keymap_blocks.append(f'    <keyMap index="{index}">\n' + "\n".join(per_level_lines[level]) + "\n    </keyMap>")

    for field in ("layoutId", "authors", "license"):
        report.skip(field, "no macOS keylayout attribute for this OKLM identity/provenance field in the v1 exporter")
    report.lossy(
        "geometry",
        "the <layouts> hardware-detection range is not modeled per OKLM geometry in v1; "
        "the generic first=0 last=17 mapSet=ANSI range from Apple's reference example is used",
    )
    locales = manifest["locales"]
    if len(locales) > 1:
        report.skip("locales", "macOS keylayout files are not locale-tagged; only the layout name is used")
    skip_oklm_only_metadata(report, manifest)

    keyboard_id = -(20000 + (zlib.crc32(manifest["layoutId"].encode("utf-8")) % 10000))

    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<!DOCTYPE keyboard SYSTEM "file://localhost/System/Library/DTDs/KeyboardLayout.dtd">')
    lines.append(
        f'<keyboard group="0" id="{keyboard_id}" name="{xml_escape(manifest["name"])}" maxout="{max_output_len}">'
    )
    lines.append("  <layouts>")
    lines.append('    <layout first="0" last="17" modifiers="modifiers" mapSet="ANSI"/>')
    lines.append("  </layouts>")
    lines.append('  <modifierMap id="modifiers" defaultIndex="0">')
    lines.extend(modifier_select)
    lines.append("  </modifierMap>")
    lines.append('  <keyMapSet id="ANSI">')
    lines.extend(keymap_blocks)
    lines.append("  </keyMapSet>")
    if action_blocks:
        lines.append("  <actions>")
        lines.extend(action_blocks)
        lines.append("  </actions>")
    if terminator_lines:
        lines.append("  <terminators>")
        lines.extend(terminator_lines)
        lines.append("  </terminators>")
    lines.append("</keyboard>")

    return "\n".join(lines), report.build()
