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
- Dead keys map to `dead_*` keysyms only where a direct xkb equivalent
  exists. OKLM `compositions` tables are not re-emitted as XCompose rules:
  actual composition results depend on the system's Compose configuration,
  which is recorded as a lossy mapping. Dead keys with no `dead_*`
  equivalent fall back to their `display` character (composition lost) or
  are skipped entirely if no `display` is available.
- Keys with no `xkb` name declared are omitted (skipped, not guessed).
"""
from .common import levels_used_by, ReportBuilder, reject_unsupported_v1_scope, skip_oklm_only_metadata

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

# OKLM dead-key id -> xkb dead_* keysym, only where a direct equivalent
# exists (X11 keysymdef.h dead_* set).
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
            "composition tables are not re-emitted as XCompose rules; results for dead_* "
            "keysyms are delegated to the system's own Compose configuration and may differ "
            "from the OKLM compositions",
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
