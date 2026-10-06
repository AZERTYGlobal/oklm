# -*- coding: utf-8 -*-
"""OKLM -> xkb exporter (draft v1, one-way).

Emits a standalone `xkb_symbols` block (not a full keymap). Scope and known
approximations (see CONVERSIONS.md and the generated report):

- Only levels 1-4 are exported: standard xkb key types support at most four
  shift levels per key (base, shift, altgr, altgr+shift). CapsLock-
  conditioned levels 5-8 are handled by the X server via key type / locale
  ctype rules, not per-key declarations, and are always skipped.
- Characters are emitted as xkb keysym names: common ASCII/Latin punctuation
  and letters use their canonical X11 keysym name; everything else uses the
  Unicode keysym form `U<hex codepoint>` (lossless -- xkb resolves this to
  the Unicode codepoint directly).
- Dead keys map to `dead_*` keysyms. Where X11 has no direct `dead_*` for an
  OKLM dead key, a spare, otherwise unused `dead_*` keysym is used as a
  carrier (see DEAD_KEYSYMS); `export_compose()` writes the matching
  `.XCompose` rules, which define the real outputs. Dead keys with no
  `dead_*` entry at all fall back to their `display` character (composition
  lost) or are skipped entirely if no `display` is available.
- `export_compose()` re-emits every OKLM `compositions` table as XCompose
  rules (`<dead_x> <base> : "result"`); tools/export.py writes it next to the
  xkb file as `<name>.XCompose`.
- Keys with no `xkb` name declared are omitted (skipped, not guessed).
"""
from .common import (
    levels_used_by,
    ReportBuilder,
    reject_unsupported_v1_scope,
    skip_oklm_only_metadata,
    without_modifier_keys,
)

ASCII_KEYSYMS = {
    " ": "space", "!": "exclam", '"': "quotedbl", "#": "numbersign",
    "$": "dollar", "%": "percent", "&": "ampersand", "'": "apostrophe",
    "(": "parenleft", ")": "parenright", "*": "asterisk", "+": "plus",
    ",": "comma", "-": "minus", ".": "period", "/": "slash",
    ":": "colon", ";": "semicolon", "<": "less", "=": "equal",
    ">": "greater", "?": "question", "@": "at",
    "[": "bracketleft", "\\": "backslash", "]": "bracketright",
    "^": "asciicircum", "_": "underscore", "`": "grave",
    "{": "braceleft", "|": "bar", "}": "braceright", "~": "asciitilde",
}
for _c in "0123456789":
    ASCII_KEYSYMS[_c] = _c
for _c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
    ASCII_KEYSYMS[_c] = _c

# OKLM dead-key id -> xkb dead_* keysym (X11 keysymdef.h dead_* set).
# The first 21 entries are direct equivalents. The last 8 are carriers: X11
# has no matching dead keysym, so an unused one stands in and the .XCompose
# written by export_compose() defines the outputs (as in json_to_xkb).
# Provenance: carrier table DK_TO_XKB of azerty-global/components/website/
# scripts/json_to_xkb.py, ported 2026-10-06 (decision D28 of
# IA/operations/2026-10-04-outils-maison-vs-en-ligne), OKLM dead-key ids in
# place of the site's `dk_*` names.
DEAD_KEYSYMS = {
    "acute": "dead_acute",
    "breve": "dead_breve",
    "caron": "dead_caron",
    "cedilla": "dead_cedilla",
    "circumflex": "dead_circumflex",
    "currencies": "dead_currency",
    "diaeresis": "dead_diaeresis",
    "dot-above": "dead_abovedot",
    "dot-below": "dead_belowdot",
    "double-acute": "dead_doubleacute",
    "double-grave": "dead_doublegrave",
    "grave": "dead_grave",
    "greek": "dead_greek",
    "hook": "dead_hook",
    "horn": "dead_horn",
    "inverted-breve": "dead_invertedbreve",
    "macron": "dead_macron",
    "ogonek": "dead_ogonek",
    "ring-above": "dead_abovering",
    "stroke": "dead_stroke",
    "tilde": "dead_tilde",
    # carriers
    "horizontal-stroke": "dead_belowring",
    "comma": "dead_belowcomma",
    "cyrillic": "dead_semivoiced_sound",
    "scientific": "dead_iota",
    "punctuation": "dead_belowtilde",
    "extended-latin": "dead_voiced_sound",
    "misc-symbols": "dead_belowmacron",
    "phonetic": "dead_belowbreve",
}

# Characters -> canonical keysym names in .XCompose sequences (ported from
# json_to_xkb.py); other non-ASCII characters use the `U<hex>` form.
XCOMPOSE_KEYSYMS = {
    "À": "Agrave", "Á": "Aacute", "Â": "Acircumflex", "Ã": "Atilde", "Ä": "Adiaeresis", "Å": "Aring",
    "Æ": "AE", "Ç": "Ccedilla", "È": "Egrave", "É": "Eacute", "Ê": "Ecircumflex", "Ë": "Ediaeresis",
    "Ì": "Igrave", "Í": "Iacute", "Î": "Icircumflex", "Ï": "Idiaeresis", "Ñ": "Ntilde",
    "Ò": "Ograve", "Ó": "Oacute", "Ô": "Ocircumflex", "Õ": "Otilde", "Ö": "Odiaeresis", "Ø": "Oslash",
    "Ù": "Ugrave", "Ú": "Uacute", "Û": "Ucircumflex", "Ü": "Udiaeresis", "Ý": "Yacute",
    "à": "agrave", "á": "aacute", "â": "acircumflex", "ã": "atilde", "ä": "adiaeresis", "å": "aring",
    "æ": "ae", "ç": "ccedilla", "è": "egrave", "é": "eacute", "ê": "ecircumflex", "ë": "ediaeresis",
    "ì": "igrave", "í": "iacute", "î": "icircumflex", "ï": "idiaeresis", "ñ": "ntilde",
    "ò": "ograve", "ó": "oacute", "ô": "ocircumflex", "õ": "otilde", "ö": "odiaeresis", "ø": "oslash",
    "ù": "ugrave", "ú": "uacute", "û": "ucircumflex", "ü": "udiaeresis", "ý": "yacute", "ÿ": "ydiaeresis",
    "Œ": "OE", "œ": "oe", "ß": "ssharp", "µ": "mu",
    "¡": "exclamdown", "¿": "questiondown", "§": "section", "¶": "paragraph", "©": "copyright", "®": "registered",
    "«": "guillemotleft", "»": "guillemotright", "°": "degree", "±": "plusminus", "×": "multiply", "÷": "division",
    "£": "sterling", "€": "EuroSign",
}

LEVELS = ["1", "2", "3", "4"]


def keysym_for_char(text):
    if text in ASCII_KEYSYMS:
        return ASCII_KEYSYMS[text]
    if len(text) == 1:
        return f"U{ord(text):04X}"
    # Multi-codepoint literal output (ligature-like): no single xkb keysym
    # can hold it losslessly; fall back to the first codepoint.
    return f"U{ord(text[0]):04X}"


def compose_keysym(text):
    """Keysym name of a composition base character in an .XCompose rule, or None."""
    if len(text) != 1:
        return None
    if text in ASCII_KEYSYMS:
        return ASCII_KEYSYMS[text]
    if text in XCOMPOSE_KEYSYMS:
        return XCOMPOSE_KEYSYMS[text]
    return f"U{ord(text):04X}"


def export_compose(manifest, source_file=None):
    """Returns the .XCompose text: every composition of the dead keys that have a
    dead_* keysym (direct or carrier), like json_to_xkb."""
    lines = [
        f"# {manifest['name']}",
        "# Generated by OKLM exporters (draft v1) -- do not edit by hand.",
        f"# Source manifest: {source_file or manifest['layoutId'] + '.oklm.json'}",
        "",
        'include "%L"',
        "",
    ]
    for dk in sorted(manifest.get("deadKeys", []), key=lambda d: d["id"]):
        keysym = DEAD_KEYSYMS.get(dk["id"])
        table = dk.get("compositions", {})
        if not keysym or not table:
            continue
        lines.append(f"# Dead Key: {dk['id']}")
        for base, result in sorted(table.items(), key=lambda kv: (len(kv[0]), kv[0])):
            base_keysym = compose_keysym(base)
            if base_keysym:
                lines.append(f'<{keysym}> <{base_keysym}> : "{xkb_string_escape(result)}"')
        lines.append("")
    return "\n".join(lines)


def xkb_string_escape(text):
    return text.replace("\\", "\\\\").replace('"', '\\"')


def export(manifest, source_file=None):
    """Returns (xkb_text_or_None, report_dict)."""
    report = ReportBuilder(
        direction="oklm-to-xkb",
        source={"format": "oklm", "file": source_file, "version": manifest.get("schemaVersion")},
        target={"format": "xkb-symbols"},
    )
    report.round_trip_confidence = "medium"

    if reject_unsupported_v1_scope(report, manifest):
        return None, report.build()
    manifest = without_modifier_keys(report, manifest)

    used_levels = levels_used_by(manifest)
    skipped_levels = sorted((used_levels - set(LEVELS)), key=int)
    for level in skipped_levels:
        report.skip(
            f"keys[].levels.{level}",
            "xkb key symbol lists support at most 4 shift levels per key (FOUR_LEVEL key "
            "types); CapsLock-conditioned levels are handled by the X server via key type "
            "and locale ctype rules, not per-key declarations",
        )

    dead_keys = {dk["id"]: dk for dk in manifest.get("deadKeys", [])}
    lossy_dead_reported = set()
    unsupported_dead_reported = set()

    lines_body = []
    any_level3 = False
    for key in manifest.get("keys", []):
        xkb_name = key.get("xkb")
        if not xkb_name:
            report.skip(f"keys[{key['id']}]", "no xkb key name declared for this key")
            continue
        levels = key.get("levels", {})
        max_level = 0
        for level in LEVELS:
            if level in levels:
                max_level = int(level)
        if max_level == 0:
            continue
        if max_level >= 3:
            any_level3 = True
        symbols = []
        for i in range(1, max_level + 1):
            level = str(i)
            out = levels.get(level)
            if out is None:
                symbols.append("NoSymbol")
            elif isinstance(out, str):
                symbols.append(keysym_for_char(out))
            else:
                dk_id = out["deadKey"]
                keysym = DEAD_KEYSYMS.get(dk_id)
                if keysym:
                    symbols.append(keysym)
                else:
                    dk = dead_keys.get(dk_id, {})
                    if "display" in dk:
                        symbols.append(keysym_for_char(dk["display"]))
                        if dk_id not in lossy_dead_reported:
                            lossy_dead_reported.add(dk_id)
                            report.lossy(
                                f"deadKeys[{dk_id}]",
                                "no xkb dead_* keysym equivalent; exported as its display "
                                "character instead of a dead key, composition behavior lost",
                            )
                    else:
                        symbols.append("NoSymbol")
                        if dk_id not in unsupported_dead_reported:
                            unsupported_dead_reported.add(dk_id)
                            report.skip(
                                f"deadKeys[{dk_id}]",
                                "no xkb dead_* keysym equivalent and no display fallback available",
                            )
        lines_body.append(f"    key <{xkb_name}> {{ [ {', '.join(symbols)} ] }};")

    if dead_keys:
        report.lossy(
            "deadKeys[].compositions",
            "compositions are re-emitted as XCompose rules in the companion .XCompose file, "
            "which must be installed (~/.XCompose or merged into the system Compose "
            "configuration) for the dead keys to give the OKLM results; carrier dead_* keysyms "
            "(e.g. dead_belowring for horizontal-stroke) have no native composition meaning; "
            "dead keys without any dead_* keysym lose their compositions",
        )
    report.mapped("keys")
    report.mapped("keys[].levels")
    skip_oklm_only_metadata(report, manifest)
    for field in ("layoutId", "authors", "license", "locales", "levelSelectors"):
        if field in manifest:
            report.skip(field, "no xkb_symbols construct for this OKLM identity/provenance field in the v1 exporter")

    header = [
        "// Generated by OKLM exporters (draft v1) -- do not edit by hand.",
        f"// Source manifest: {source_file or manifest['layoutId'] + '.oklm.json'}",
    ]
    if any_level3:
        header.append(
            '// Level 3/4 present: include "level3(ralt_switch)" (or equivalent) in the '
            "consuming keymap to bind Level3Shift to a physical modifier."
        )
    lines = header + [
        "default partial alphanumeric_keys",
        f'xkb_symbols "{manifest["layoutId"]}" {{',
        f'    name[Group1] = "{xkb_string_escape(manifest["name"])}";',
        "",
    ] + lines_body + [
        "};",
    ]
    return "\n".join(lines), report.build()
