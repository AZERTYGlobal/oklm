# -*- coding: utf-8 -*-
"""OKLM -> Microsoft Keyboard Layout Creator source (`.klc`, one-way, draft).

Output: UTF-16 little endian with BOM, CRLF line endings, tab separated, as MSKLC writes it.
Section order: KBD, COPYRIGHT, COMPANY, LOCALENAME, LOCALEID, VERSION, SHIFTSTATE, LAYOUT, DEADKEY blocks,
KEYNAME (omitted), DESCRIPTIONS, LANGUAGENAMES, ENDKBD.

Mapping:
- shift states are always `0 1 2 6 7` (none, Shift, Ctrl, Ctrl+Alt = AltGr, Shift+Ctrl+Alt). A level whose
  qualifiers are {} / {Level2Shift} / {Level3Shift} / {Level2Shift, Level3Shift} fills states 0 / 1 / 6 / 7.
  The Ctrl column carries the usual control codes (letters, `[ \\ ] 6 -`, space) derived from the key's VK.
- CapsLock levels (a level whose qualifiers include CapsLock) are not columns: they set the `Cap` column.
  Cap = 1 when CapsLock swaps states 0 and 1, +4 when it swaps states 6 and 7. A caps level that matches
  neither "no effect" nor "swap" (MSKLC would need an SGCap line) is reported as lossy and ignored. Levels
  omitted by the manifest are read as "no CapsLock data" (no effect), not as E21 "no output".
- Levels needing Level5Shift or NumLock, or without a levelSelectors entry, are skipped and reported.
- Every output is written as 4 hexadecimal digits, except ASCII letters and digits, which are written as is;
  a dead key output is `<hex>@`. Only BMP single code point outputs fit: a ligature (several code points)
  or a character outside the BMP is skipped and reported (the LIGATURE section is not generated).
- A dead key becomes a DEADKEY block named by its standalone character: `display`, else `fallback`.
  Compositions whose base or result is not a single BMP character are skipped and reported. The space
  base is added (space gives the standalone character) when the manifest does not define it.
- VK names: an ASCII letter or digit at level 1 gives its own VK; other keys get the OEM name of their
  position, or the first free OEM name when it is taken. Windows only needs them to be unique.
- LOCALEID comes from a small table of locales; an unknown locale falls back to 0409 with a lossy report.

VERIFICATION STATUS: MSKLC was not available, so the output was never compiled. Tests use an in-repo
parser of the format as documented by Microsoft samples (`kbdus.klc`); treat the file as untested.
"""
import re

from .common import ReportBuilder, reject_unsupported_v1_scope, resolve_level_modifiers, skip_oklm_only_metadata, \
    without_modifier_keys
from .ldml import HID_TO_SCANCODE1

STATES = [0, 1, 2, 6, 7]
LOCALES = {  # BCP 47 -> (LCID hex, language name)
    "en": ("0409", "English (United States)"), "en-US": ("0409", "English (United States)"),
    "fr": ("040c", "French (France)"), "fr-FR": ("040c", "French (France)"),
    "it": ("0410", "Italian (Italy)"), "it-IT": ("0410", "Italian (Italy)"),
    "de": ("0407", "German (Germany)"), "de-DE": ("0407", "German (Germany)"),
    "es": ("0c0a", "Spanish (Spain)"), "es-ES": ("0c0a", "Spanish (Spain)"),
    "pt-BR": ("0416", "Portuguese (Brazil)"), "en-GB": ("0809", "English (United Kingdom)"),
}
CODE_TO_VK = {
    "Backquote": "OEM_3", "Minus": "OEM_MINUS", "Equal": "OEM_PLUS", "BracketLeft": "OEM_4",
    "BracketRight": "OEM_6", "Backslash": "OEM_5", "Semicolon": "OEM_1", "Quote": "OEM_7",
    "Comma": "OEM_COMMA", "Period": "OEM_PERIOD", "Slash": "OEM_2", "IntlBackslash": "OEM_102",
    "Space": "SPACE",
}
SPARE_VK = ["OEM_1", "OEM_2", "OEM_3", "OEM_4", "OEM_5", "OEM_6", "OEM_7", "OEM_8", "OEM_102",
            "OEM_COMMA", "OEM_PERIOD", "OEM_PLUS", "OEM_MINUS"]
CTRL_OEM = {"OEM_4": "001b", "OEM_5": "001c", "OEM_6": "001d", "OEM_MINUS": "001f", "SPACE": "0020"}
STANDALONE = {  # dead key id -> conventional standalone (spacing) character
    "acute": "´", "grave": "`", "circumflex": "^", "diaeresis": "¨",
    "tilde": "~", "caron": "ˇ", "breve": "˘", "cedilla": "¸",
    "macron": "¯", "ogonek": "˛", "ring-above": "˚", "dot-above": "˙",
    "double-acute": "˝",
}
PRIVATE_USE_START = 0xE000
ALNUM = re.compile(r"^[A-Za-z0-9]$")


def _hex(ch):
    return f"{ord(ch):04x}"


def _fits(output):
    return isinstance(output, str) and len(output) == 1 and ord(output) <= 0xFFFF


def _cell(output):
    if output is None:
        return "-1"
    return output if ALNUM.match(output) else _hex(output)


def _name(ch):
    import unicodedata
    return unicodedata.name(ch, f"U+{ord(ch):04X}")


def assign_vks(keys):
    """key id -> VK name, unique."""
    vks, used = {}, set()
    for key in keys:  # pass 1: own VK for ASCII letters and digits at level 1
        base = key.get("levels", {}).get("1")
        if isinstance(base, str) and ALNUM.match(base) and base.upper() not in used:
            vks[key["id"]] = base.upper()
            used.add(base.upper())
    for key in keys:  # pass 2: OEM name of the position
        if key["id"] in vks:
            continue
        vk = CODE_TO_VK.get(key.get("code", ""))
        if vk is None and key.get("code", "").startswith("Digit"):
            vk = key["code"][-1]
        if vk and vk not in used:
            vks[key["id"]] = vk
            used.add(vk)
    spare = [v for v in SPARE_VK if v not in used]
    for key in keys:  # pass 3: whatever is left
        if key["id"] not in vks:
            vks[key["id"]] = spare.pop(0)
            used.add(vks[key["id"]])
    return vks


def classify_levels(manifest, report):
    """level number -> (state, caps) with state in STATES minus 2, or None (skipped)."""
    resolved = resolve_level_modifiers(manifest)
    table = {"1": (0, False)}
    column = {frozenset(): 0, frozenset({"Level2Shift"}): 1, frozenset({"Level3Shift"}): 6,
              frozenset({"Level2Shift", "Level3Shift"}): 7}
    used = {lv for k in manifest["keys"] for lv in k.get("levels", {})}
    for level in sorted(used, key=int):
        if level == "1":
            continue
        qualifiers = resolved.get(level)
        if qualifiers is None:
            report.skip(f"keys[].levels.{level}", "no levelSelectors entry (explicit or default) for this level")
            continue
        caps = "CapsLock" in qualifiers
        rest = frozenset(q for q in qualifiers if q != "CapsLock")
        if rest not in column:
            report.skip(f"keys[].levels.{level}", f"qualifiers {sorted(qualifiers)} have no Windows shift state in .klc")
            continue
        table[level] = (column[rest], caps)
    return table


def short_name(layout_id):
    name = re.sub(r"[^a-z0-9]", "", layout_id.lower())[:8]
    return name or "oklm"


def export(manifest, source_file=None):
    """Returns (utf16_bytes_or_None, report_dict)."""
    report = ReportBuilder(
        direction="oklm-to-klc",
        source={"format": "oklm", "file": source_file, "version": manifest.get("schemaVersion")},
        target={"format": "windows-klc"},
    )
    report.round_trip_confidence = "low"
    if reject_unsupported_v1_scope(report, manifest):
        return None, report.build()
    manifest = without_modifier_keys(report, manifest)

    unmapped = [(k["id"], k["hid"]) for k in manifest["keys"] if k["hid"] not in HID_TO_SCANCODE1]
    if unmapped:
        for key_id, hid in unmapped:
            report.error(f"key {key_id}: HID {hid} has no known PC/AT Set 1 scan code")
        return None, report.build()

    keys = sorted(manifest["keys"], key=lambda k: int(HID_TO_SCANCODE1[k["hid"]], 16))
    vks = assign_vks(keys)
    levels = classify_levels(manifest, report)

    # dead keys: standalone character, blocks
    dead_char, dead_blocks = {}, {}
    private = PRIVATE_USE_START
    for dk in manifest.get("deadKeys", []):
        standalone = dk.get("display") or dk.get("fallback") or STANDALONE.get(dk["id"])
        if standalone is None or standalone in dead_blocks:
            while chr(private) in dead_blocks:
                private += 1
            standalone = chr(private)
            report.lossy(f"deadKeys[{dk['id']}]", f"no usable standalone character: private-use U+{private:04X} names the DEADKEY "
                                                 "and would be typed if the sequence does not compose")
        if not _fits(standalone):
            report.error(f"dead key {dk['id']}: standalone character {standalone!r} is not a single BMP character")
            continue
        dead_char[dk["id"]] = standalone
        dead_blocks[standalone] = dk
    if report.errors:
        return None, report.build()

    def output_of(key, level):
        out = key.get("levels", {}).get(level)
        if out is None:
            return None
        if isinstance(out, dict):
            ch = dead_char.get(out["deadKey"])
            return ("dead", ch) if ch else None
        if not _fits(out):
            report.lossy(f"keys[{key['id']}].levels.{level}",
                         f"output {out!r} is a ligature or lies outside the BMP: not representable without a LIGATURE section")
            return None
        return out

    rows = []
    used_dead = set()
    for key in keys:
        plain, caps = {}, {}
        for level, (state, is_caps) in levels.items():
            out = output_of(key, level)
            if out is None:
                continue
            (caps if is_caps else plain)[state] = out
        cap_value = 0
        for lo, hi, bit in ((0, 1, 1), (6, 7, 4)):
            if not any(s in caps for s in (lo, hi)):
                continue
            swapped = caps.get(lo, plain.get(lo)) == plain.get(hi) and caps.get(hi, plain.get(hi)) == plain.get(lo)
            same = caps.get(lo, plain.get(lo)) == plain.get(lo) and caps.get(hi, plain.get(hi)) == plain.get(hi)
            if swapped and not same:
                cap_value |= bit
            elif not same:
                report.lossy(f"keys[{key['id']}].levels",
                             f"CapsLock behaviour on states {lo}/{hi} is neither 'no effect' nor 'swap': needs SGCap, ignored")
        vk = vks[key["id"]]
        ctrl = "-1"
        if vk.isalpha() and len(vk) == 1:
            ctrl = f"{ord(vk) - 64:04x}"
        elif vk == "6":
            ctrl = "001e"
        elif vk in CTRL_OEM:
            ctrl = CTRL_OEM[vk]
        cells = []
        for state in STATES:
            if state == 2:
                cells.append(ctrl)
                continue
            out = plain.get(state)
            if isinstance(out, tuple):
                used_dead.add(out[1])
                cells.append(_hex(out[1]) + "@")
            else:
                cells.append(_cell(out))
        shown = ", ".join("<none>" if plain.get(s) is None else _name(plain[s][1] if isinstance(plain[s], tuple) else plain[s])
                           for s in STATES if s != 2)
        rows.append(f"{HID_TO_SCANCODE1[key['hid']]}\t{vk}\t\t{cap_value}\t" + "\t".join(cells) + f"\t// {shown}")

    report.mapped("keys")
    report.mapped("keys[].levels")
    if "levelSelectors" in manifest:
        report.mapped("levelSelectors")
    report.lossy("keys[].levels", "Ctrl column filled with the standard control codes; CapsLock reduced to the Cap column")

    lines = []
    name = manifest["name"].replace('"', "'")
    author = (manifest.get("authors") or ["unknown"])[0].replace('"', "'")
    known = [l for l in manifest.get("locales", []) if l in LOCALES]
    locale = next((l for l in known if "-" in l), known[0] if known else None)
    if locale is None:
        locale = "en-US"
        report.lossy("locales", f"no known LCID for {manifest.get('locales')}: 0409 (en-US) written")
    lcid, language = LOCALES[locale]
    lines += [
        f'KBD\t{short_name(manifest["layoutId"])}\t"{name}"', "",
        f'COPYRIGHT\t"(c) {author}, license {manifest["license"]}"', "",
        f'COMPANY\t"{author}"', "",
        f'LOCALENAME\t"{locale}"', "",
        f'LOCALEID\t"0000{lcid}"', "",
        "VERSION\t1.0", "",
        "SHIFTSTATE", "",
    ]
    labels = {0: "", 1: "Shft", 2: "Ctrl", 6: "Ctrl Alt", 7: "Shft Ctrl Alt"}
    for i, state in enumerate(STATES):
        lines.append(f"{state}\t//Column {i + 4} : {labels[state]}".rstrip())
    lines += ["", "LAYOUT\t\t;an extra '@' at the end is a dead key", "",
              "//SC\tVK_\t\tCap\t" + "\t".join(str(s) for s in STATES), ""]
    lines += rows
    lines.append("")

    for ch in sorted(used_dead, key=ord):
        dk = dead_blocks[ch]
        lines.append(f"DEADKEY\t{_hex(ch)}")
        lines.append("")
        entries, skipped = {}, 0
        for base, result in dk.get("compositions", {}).items():
            if _fits(base) and _fits(result):
                entries[base] = result
            else:
                skipped += 1
        entries.setdefault(" ", ch)
        for base, result in sorted(entries.items(), key=lambda kv: ord(kv[0])):
            lines.append(f"{_hex(base)}\t{_hex(result)}\t// {_name(base)}, {_name(result)}")
        lines.append("")
        if skipped:
            report.lossy(f"deadKeys[{dk['id']}].compositions",
                         f"{skipped} composition(s) skipped: base or result is not a single BMP character")
    unused = [dk["id"] for dk in manifest.get("deadKeys", []) if dead_char.get(dk["id"]) not in used_dead]
    if manifest.get("deadKeys"):
        report.mapped("deadKeys")
    for dk_id in unused:
        report.skip(f"deadKeys[{dk_id}]", "dead key not produced by any exportable key output")
    lines += ["DESCRIPTIONS", "", f"{lcid}\t{name}", "", "LANGUAGENAMES", "", f"{lcid}\t{language}", "", "ENDKBD", ""]

    for field in ("geometry", "layoutId", "version"):
        if field in manifest:
            report.skip(field, "not represented in .klc (the short name comes from layoutId)")
    skip_oklm_only_metadata(report, manifest)
    report.warn("MSKLC was not available: the .klc was never compiled; it is checked by an in-repo parser only")

    text = "\r\n".join(lines)
    return b"\xff\xfe" + text.encode("utf-16-le"), report.build()
