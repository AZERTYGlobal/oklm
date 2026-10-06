# -*- coding: utf-8 -*-
"""OKLM -> Elgato Stream Deck profile exporter (`.streamDeckProfile`, one-way, draft).

What it produces: a profile of "Text" actions, one button per distinct character that a layout
types and that is not an ASCII letter or digit (those are on every keyboard). Buttons are laid out
on a Stream Deck XL grid (8 columns x 4 rows, 32 buttons per page), one page per 32 characters,
in key order then level order. Pressing a button types the character, whatever layout is active,
which is what makes the profile useful as a reminder and as a fallback for rarely used symbols.

What it does not carry (declared in the report): key positions, levels and modifiers, dead-key
sequences and compositions, fallbacks, geometry, every other OKLM field.

VERIFICATION STATUS: the file format is not documented by Elgato for third-party generation. The
layout below (zip with package.json and Profiles/<UUID>.sdProfile/{manifest.json, Profiles/<page>/
manifest.json}, manifest "Version" 3.0, Text action settings isTypingMode / pastedText, buttons
addressed "column,row") was rebuilt from public sources and community tools, and has NOT been
opened with the Stream Deck software. The report says so in `warnings`.

Output is deterministic: UUIDs are derived from the layout id, zip entries are sorted and carry a
fixed timestamp.
"""
import io
import json
import re
import uuid
import zipfile

from .common import ReportBuilder, reject_unsupported_v1_scope, skip_oklm_only_metadata, without_modifier_keys

DEVICE_MODEL = "20GBA9911"  # Stream Deck XL, 8 x 4
COLUMNS, ROWS = 8, 4
PER_PAGE = COLUMNS * ROWS
APP_VERSION = "7.1.0"
TEXT_ACTION = "com.elgato.streamdeck.system.text"
NAMESPACE = uuid.UUID("5d0e6f3a-0c1b-4f7e-9a2d-6f1c1f0b4e11")
ASCII_PLAIN = re.compile(r"^[A-Za-z0-9 ]$")
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def _uuid(*parts):
    return str(uuid.uuid5(NAMESPACE, "/".join(parts))).upper()


def collect_characters(manifest):
    """Distinct string outputs, first-seen order (keys in manifest order, levels ascending), minus plain ASCII."""
    seen, ordered = set(), []
    for key in manifest.get("keys", []):
        levels = key.get("levels", {})
        for level in sorted(levels, key=int):
            out = levels[level]
            if isinstance(out, str) and out and not ASCII_PLAIN.match(out) and out not in seen:
                seen.add(out)
                ordered.append(out)
    return ordered


def _json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _action(layout_id, char):
    return {
        "ActionID": _uuid(layout_id, "action", char),
        "LinkedTitle": False,
        "Name": "Text",
        "Plugin": {"Name": "Text", "UUID": TEXT_ACTION, "Version": "1.0"},
        "Settings": {"isSendingEnter": False, "isTypingMode": True, "pastedText": char},
        "State": 0,
        "States": [{"Title": char, "ShowTitle": True, "TitleAlignment": "middle", "FontSize": 16}],
        "UUID": TEXT_ACTION,
    }


def build_profile(manifest, characters):
    """Returns the zip file as bytes."""
    layout_id = manifest["layoutId"]
    profile_id = _uuid(layout_id, "profile")
    pages = [characters[i:i + PER_PAGE] for i in range(0, len(characters), PER_PAGE)]
    page_ids = [_uuid(layout_id, "page", str(n)) for n in range(len(pages))]
    entries = {
        "package.json": _json({"AppVersion": APP_VERSION, "DeviceModel": DEVICE_MODEL, "FormatVersion": 1}),
        f"Profiles/{profile_id}.sdProfile/manifest.json": _json({
            "Name": manifest["name"],
            "Version": "3.0",
            "Device": {"Model": DEVICE_MODEL},
            "Pages": {"Current": page_ids[0], "Default": page_ids[0], "Pages": page_ids},
        }),
    }
    for n, (page_id, chars) in enumerate(zip(page_ids, pages), start=1):
        actions = {f"{i % COLUMNS},{i // COLUMNS}": _action(layout_id, ch) for i, ch in enumerate(chars)}
        entries[f"Profiles/{profile_id}.sdProfile/Profiles/{page_id}/manifest.json"] = _json({
            "Controllers": [{"Actions": actions, "Type": "Keypad"}],
            "Name": f"{manifest['name']} {n}/{len(pages)}",
        })
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, entries[name])
    return buffer.getvalue()


def export(manifest, source_file=None):
    """Returns (zip_bytes_or_None, report_dict)."""
    report = ReportBuilder(
        direction="oklm-to-streamdeck",
        source={"format": "oklm", "file": source_file, "version": manifest.get("schemaVersion")},
        target={"format": "streamdeck-profile"},
    )
    report.round_trip_confidence = "low"
    if reject_unsupported_v1_scope(report, manifest):
        return None, report.build()
    manifest = without_modifier_keys(report, manifest)

    characters = collect_characters(manifest)
    if not characters:
        report.mark_unsupported("no exportable character: every output is a plain ASCII letter, digit or space")
        return None, report.build()

    report.mapped("keys[].levels")
    report.lossy("keys", f"one Text button per distinct character ({len(characters)}), not per key: key ids, "
                         "levels and modifiers are not represented, only the character typed")
    if manifest.get("deadKeys"):
        report.skip("deadKeys", "dead-key sequences and compositions have no Stream Deck equivalent; "
                                "only characters typed directly by a key are exported")
    if any(isinstance(o, dict) for k in manifest.get("keys", []) for o in k.get("levels", {}).values()):
        report.skip("keys[].levels", "dead-key outputs are not exported (no character is typed by them)")
    for field in ("levelSelectors", "geometry", "locales", "layoutId", "authors", "license", "version"):
        if field in manifest:
            report.skip(field, "not represented in a Stream Deck profile (only the profile name is taken from `name`)")
    pages = -(-len(characters) // PER_PAGE)
    report.warn(f"{len(characters)} buttons on {pages} page(s) of {COLUMNS}x{ROWS} (Stream Deck XL); "
                "other models need the profile to be adapted in the Stream Deck software")
    report.warn("the .streamDeckProfile layout was rebuilt from public sources and has not been opened "
                "with the Stream Deck software: treat the output as untested")
    skip_oklm_only_metadata(report, manifest)

    return build_profile(manifest, characters), report.build()
