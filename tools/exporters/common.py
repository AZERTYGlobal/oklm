# -*- coding: utf-8 -*-
# SPDX-License-Identifier: EUPL-1.2
"""Shared helpers for OKLM exporters (draft v1: LDML, xkb, keylayout).

All exporters are one-way (OKLM -> target). Every export call must produce a
conversion report validating against schemas/oklm-conversion-report.schema.json
(schemaVersion 0.2) -- see CONVERSIONS.md. Nothing here talks to the network
or the filesystem beyond plain read/write of the files it is given.
"""
import json
import sys
import unicodedata
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMAS = ROOT / "schemas"
VALIDATORS = ROOT / "validators"

if str(VALIDATORS) not in sys.path:
    sys.path.insert(0, str(VALIDATORS))

from validate import analyze, load_schema, load_validator  # noqa: E402

GENERATOR_NAME = "oklm-exporters"
GENERATOR_VERSION = "0.2"

# Default functional qualifiers per ISO/IEC 9995 level, used when a manifest
# omits levelSelectors (SPEC.md "Level Selectors"). Levels 5-8 have no
# default: they must be declared explicitly to be exported.
DEFAULT_LEVEL_SELECTORS = {
    "2": ["Level2Shift"],
    "3": ["Level3Shift"],
    "4": ["Level2Shift", "Level3Shift"],
}


class ExportError(Exception):
    """Raised when a manifest cannot be exported at all (compatibilityLevel failed)."""


def load_manifest(path):
    """Load and validate an .oklm.json manifest. Raises ExportError on failure."""
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ExportError(f"cannot read {path} as JSON: {exc}") from exc

    problems = [
        f"{finding.code} {finding.path}: {finding.message}"
        for finding in analyze(manifest, load_schema("oklm-manifest.schema.json"))
        if finding.severity == "error"
    ]
    if problems:
        raise ExportError(f"{path} is not a valid OKLM manifest: " + "; ".join(problems))
    return manifest


def resolve_level_modifiers(manifest):
    """Map each declared level ("2".."8") to its list of functional qualifiers.

    Level "1" is intentionally absent: it is always the unmodified base level.
    Levels without a default and without an explicit levelSelectors entry are
    left unresolved (absent from the returned dict) -- callers must treat
    that as "unknown modifier combination" and skip/report the level.
    """
    declared = dict(manifest.get("levelSelectors", {}))
    resolved = dict(DEFAULT_LEVEL_SELECTORS)
    resolved.update(declared)
    return resolved


def caps_base_levels(resolved):
    """Map each CapsLock level to the level without CapsLock that has the same other qualifiers.

    With the default selectors this is 5 -> 1, 6 -> 2, 7 -> 3, 8 -> 4. A CapsLock level whose
    non-CapsLock counterpart is not declared (explicitly or by default) is absent from the result.
    """
    by_qualifiers = {frozenset(): "1"}
    for level in sorted(resolved, key=int):
        if "CapsLock" not in resolved[level]:
            by_qualifiers.setdefault(frozenset(resolved[level]), level)
    return {
        level: by_qualifiers[frozenset(q for q in qualifiers if q != "CapsLock")]
        for level, qualifiers in resolved.items()
        if "CapsLock" in qualifiers and frozenset(q for q in qualifiers if q != "CapsLock") in by_qualifiers
    }


def effective_output(levels, level, caps_base):
    """Output of a key at `level`; a CapsLock level the key does not define falls back on the
    matching level without CapsLock (decision of the 2026-10 audit, batch 1, B-02).

    `levels` is the key's levels object, `caps_base` the result of caps_base_levels().
    Returns (output or None, True when the fallback was used).
    """
    out = levels.get(level)
    if out is None and level in caps_base:
        base = levels.get(caps_base[level])
        if base is not None:
            return base, True
    return out, False


CAPS_FALLBACK_WARNING = (
    "CapsLock levels a key does not define take the output of the matching level without CapsLock "
    "(5 -> 1, 6 -> 2, 7 -> 3, 8 -> 4 with the default selectors): {count} key output(s) filled this way"
)


# Standalone (spacing) character of a dead key, by OKLM dead-key id: what the key types when the
# sequence does not compose (macOS terminator, Windows DEADKEY name). Used by keylayout and klc, in
# that order of preference: the dead key's `fallback`, its `display`, then this table. Provenance: the
# `<terminators>` of the shipped AZERTY Global.keylayout (azerty-global release audit 2026-09-05), keyed
# by OKLM dead-key id; ported 2026-10-06 (decision D29 of IA/operations/2026-10-04-outils-maison-vs-en-
# ligne). The entries for cyrillic and extended-latin are U+0020, as in that file.
DEAD_KEY_STANDALONE = {
    "acute": "´", "double-acute": "˝", "grave": "`", "double-grave": "̏",
    "cyrillic": " ", "greek": "µ", "phonetic": "ʁ", "stroke": "/",
    "horizontal-stroke": "-", "breve": "˘", "inverted-breve": "̑",
    "caron": "ˇ", "circumflex": "^", "horn": "̛", "hook": "̉",
    "cedilla": "¸", "extended-latin": " ", "macron": "¯", "ogonek": "˛",
    "dot-above": "˙", "dot-below": "̣", "punctuation": "§",
    "ring-above": "˚", "misc-symbols": "→", "currencies": "¤",
    "scientific": "±", "tilde": "~", "diaeresis": "¨", "comma": "̦",
}


def standalone_char(dead_key):
    """(character, origin) of a dead key's standalone character, one policy for every exporter:
    `fallback`, else `display`, else DEAD_KEY_STANDALONE, else the result the manifest gives for the
    dead key followed by a space (the conventional "dead key + Space"). origin is "fallback",
    "display", "default", "space", or None (character None) when the dead key has none of them."""
    if "fallback" in dead_key:
        return dead_key["fallback"], "fallback"
    if "display" in dead_key:
        return dead_key["display"], "display"
    if dead_key["id"] in DEAD_KEY_STANDALONE:
        return DEAD_KEY_STANDALONE[dead_key["id"]], "default"
    space = dead_key.get("compositions", {}).get(" ")
    if isinstance(space, str) and space:
        return space, "space"
    return None, None


def levels_used_by(manifest):
    """Every level number (as string) referenced by any key's levels object."""
    used = set()
    for key in manifest.get("keys", []):
        used.update(key.get("levels", {}).keys())
    return used


def without_modifier_keys(report, manifest):
    """Return the manifest minus its role:modifier keys (E22), which carry no output.

    Every exporter works on the returned copy. The skipped keys are declared in the report:
    a modifier key is a functional declaration, the target formats place their own modifier
    keys through levelSelectors.
    """
    modifiers = [key for key in manifest.get("keys", []) if key.get("role") == "modifier"]
    if not modifiers:
        return manifest
    for key in modifiers:
        report.skip(
            f"keys[{key['id']}]",
            f"modifier key (role: modifier, {key['modifier']}): carries no output; the target "
            "binds its own modifier keys",
        )
    prepared = dict(manifest)
    prepared["keys"] = [key for key in manifest["keys"] if key.get("role") != "modifier"]
    return prepared


def xml_escape(text):
    """Escape a string for use as XML text or a double-quoted attribute value.

    Tab, line feed and carriage return become character references (a raw one in an attribute is
    normalized to a space by every XML parser). A character XML 1.0 cannot carry (most C0
    controls, lone surrogates, U+FFFE, U+FFFF) raises ValueError: exporters refuse such text
    beforehand with reject_unsafe_text, so reaching it here is a bug, never a silent alteration.
    """
    for ch in text:
        if _xml_illegal(ch):
            raise ValueError(f"U+{ord(ch):04X} cannot be written in an XML 1.0 document")
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("\t", "&#x9;")
        .replace("\n", "&#xA;")
        .replace("\r", "&#xD;")
    )


def _xml_illegal(ch):
    code = ord(ch)
    return (code < 0x20 and ch not in "\t\n\r") or 0xD800 <= code <= 0xDFFF or code in (0xFFFE, 0xFFFF)


def _char_problem(ch, policy):
    """Why a character cannot be exported under `policy`, or None.

    policy "line": identity text (name, authors...), written in comments, titles and attributes: no
    control character and no line or paragraph separator. "refuse": any control character is
    refused (xkb keysyms and Compose strings). "xml": what XML 1.0 cannot carry, \\t \\n \\r being
    written as character references. "any": only what no target can hold (NUL, lone surrogates,
    U+FFFE, U+FFFF).
    """
    code = ord(ch)
    category = unicodedata.category(ch)
    if code == 0:
        return "NUL character"
    if category == "Cs":
        return "lone surrogate"
    if code in (0xFFFE, 0xFFFF):
        return "noncharacter"
    if policy == "line" and category in ("Cc", "Zl", "Zp"):
        return "control or line separator character"
    if policy == "refuse" and category == "Cc":
        return "control character"
    if policy == "xml" and _xml_illegal(ch):
        return "control character XML 1.0 cannot carry"
    return None


def iter_manifest_texts(manifest):
    """(path, text, kind) of every string an exporter writes: kind "line" for identity text, kind
    "output" for what keys and dead keys type."""
    for field in ("name", "version", "license"):
        if isinstance(manifest.get(field), str):
            yield field, manifest[field], "line"
    for index, author in enumerate(manifest.get("authors", [])):
        if isinstance(author, str):
            yield f"authors[{index}]", author, "line"
    for key in manifest.get("keys", []):
        for level, out in key.get("levels", {}).items():
            if isinstance(out, str):
                yield f"keys[{key['id']}].levels.{level}", out, "output"
    for dead_key in manifest.get("deadKeys", []):
        base = f"deadKeys[{dead_key['id']}]"
        for field in ("display", "fallback"):
            if isinstance(dead_key.get(field), str):
                yield f"{base}.{field}", dead_key[field], "output"
        for sequence, result in dead_key.get("compositions", {}).items():
            yield f"{base}.compositions[{sequence!r}]", sequence, "output"
            if isinstance(result, str):
                yield f"{base}.compositions[{sequence!r}] (result)", result, "output"


def reject_unsafe_text(report, manifest, outputs="any"):
    """Refuse text the target cannot carry (audit B-03, B-07, B-16, B-17). Returns True and records one
    error per offending string when there is any; nothing is altered silently.

    `outputs` is the policy for typed outputs ("any", "xml", "refuse", see _char_problem); identity
    text is always held to the "line" policy.
    """
    found = []
    for path, text, kind in iter_manifest_texts(manifest):
        policy = "line" if kind == "line" else outputs
        for ch in text:
            reason = _char_problem(ch, policy)
            if reason:
                found.append(f"{path}: U+{ord(ch):04X} ({reason}) is not exportable")
                break
    for message in found[:20]:
        report.error(message)
    if len(found) > 20:
        report.error(f"... and {len(found) - 20} more unexportable text(s)")
    return bool(found)


def reject_duplicate_hid(report, manifest):
    """Refuse two keys on the same HID usage (audit B-09): the target would get two entries for one
    physical key. Returns True and records an error per duplicate when there is any."""
    seen = {}
    duplicated = False
    for key in manifest.get("keys", []):
        hid = key["hid"].lower()
        if hid in seen:
            report.error(f"keys {seen[hid]} and {key['id']} share HID {key['hid']}: one physical key cannot carry two keys")
            duplicated = True
        else:
            seen[hid] = key["id"]
    return duplicated


def write_text(path, text):
    """Write UTF-8 without BOM, LF line endings only."""
    if not text.endswith("\n"):
        text += "\n"
    path.write_bytes(text.encode("utf-8"))


class ReportBuilder:
    """Accumulates one conversion report (schemas/oklm-conversion-report.schema.json)."""

    def __init__(self, direction, source, target):
        self.direction = direction
        self.source = source
        self.target = target
        self.mapped_fields = []
        self.skipped_fields = []  # list of (path, reason)
        self.lossy_mappings = []  # list of (path, detail)
        self.warnings = []
        self.errors = []
        self.round_trip_confidence = None
        self.unsupported = False

    def mapped(self, path):
        if path not in self.mapped_fields:
            self.mapped_fields.append(path)

    def skip(self, path, reason):
        self.skipped_fields.append({"path": path, "reason": reason})

    def lossy(self, path, detail):
        self.lossy_mappings.append({"path": path, "detail": detail})

    def warn(self, message):
        self.warnings.append(message)

    def mark_unsupported(self, message):
        """The source is valid but nothing usable can be produced (D33)."""
        self.unsupported = True
        self.warnings.append(message)

    def error(self, message):
        self.errors.append(message)

    def compatibility_level(self):
        if self.errors:
            return "failed"
        if self.unsupported:
            return "unsupported"
        if self.lossy_mappings:
            return "lossy-mapping"
        if self.skipped_fields:
            return "lossy-metadata"
        return "lossless-core"

    def build(self):
        report = {
            "schemaVersion": "0.2",
            "direction": self.direction,
            "source": self.source,
            "target": self.target,
            "compatibilityLevel": self.compatibility_level(),
            "mappedFields": list(self.mapped_fields),
            "skippedFields": list(self.skipped_fields),
            "lossyMappings": list(self.lossy_mappings),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "generator": {"name": GENERATOR_NAME, "version": GENERATOR_VERSION},
        }
        if self.round_trip_confidence:
            report["roundTripConfidence"] = self.round_trip_confidence
        return report

    def validate_against_schema(self):
        """Self-check: the report this builder produces must validate. Returns
        a list of problems (empty if valid)."""
        validator = load_validator("oklm-conversion-report.schema.json")
        instance = self.build()
        return [
            f"{'/'.join(str(p) for p in error.path) or '(root)'}: {error.message}"
            for error in validator.iter_errors(instance)
        ]


def reject_unsupported_v1_scope(report, manifest):
    """v1 exporters cover keys[].levels only, not keys[].groups (no example
    manifest uses groups; see .internal/plan-exporters-v1.md scope note).
    Returns True and records an error if the manifest is out of scope."""
    keys_with_groups = [key["id"] for key in manifest.get("keys", []) if key.get("groups")]
    if keys_with_groups:
        report.error(
            "keys[].groups is not supported by the v1 exporters (out of scope: no example manifest "
            "uses it): " + ", ".join(keys_with_groups)
        )
        return True
    return False


KEY_FIELDS = ("id", "hid", "xkb", "code", "name", "role", "modifier", "levels", "groups", "categories", "extensions")
DEAD_KEY_FIELDS = ("id", "name", "display", "compositions", "fallback", "extensions")


def declare_unmapped_fields(report, manifest, target, key_fields, dead_key_fields=None):
    """Declare as skipped every key and dead-key field the exporter does not write (audit B-10): a
    field present in at least one key (or dead key) and absent from the mapped set. `key_fields`
    and `dead_key_fields` are the field names the exporter reads; dead_key_fields=None means the
    dead keys are declared elsewhere as a whole. Nothing is dropped without a line in the report."""
    for fields, mapped, items, label in (
        (KEY_FIELDS, key_fields, manifest.get("keys", []), "keys[]"),
        (DEAD_KEY_FIELDS, dead_key_fields, manifest.get("deadKeys", []), "deadKeys[]"),
    ):
        if mapped is None:
            continue
        for field in fields:
            if field not in mapped and any(field in item for item in items):
                report.skip(f"{label}.{field}", f"not represented in {target}")


def skip_oklm_only_metadata(report, manifest):
    """Declare the OKLM-only top-level fields that no v1 exporter maps."""
    for field, reason in (
        ("description", "free-text description, not part of any target's mapping model"),
        ("conformance", "OKLM conformance claims are not expressed by target formats"),
        ("exports", "OKLM export declarations are input to this tooling, not output data"),
        ("metadata", "OKLM metadata envelope (pedagogy, AI, accessibility, links) has no target equivalent"),
        ("extensions", "OKLM extension namespaces are OKLM-specific by definition"),
        ("extensionsUsed", "OKLM capability list, not part of any target's mapping model"),
        ("extensionsRequired", "OKLM capability list, not part of any target's mapping model"),
        ("featuresRequired", "OKLM capability list, not part of any target's mapping model"),
    ):
        if field in manifest:
            report.skip(field, reason)
