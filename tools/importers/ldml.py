# -*- coding: utf-8 -*-
"""LDML Keyboard 3 -> OKLM importer (draft, schema 0.2).

Reads a CLDR/UTS #35 Part 7 `keyboard3` file and produces an OKLM manifest plus a conversion report
(direction `ldml-to-oklm`). Keyboard mapping semantics come first (CONVERSIONS.md principle 3); whatever
the core cannot express is kept verbatim in the `OKLM_ldml` extension and declared in the report, or
declared as unsupported when even that was not possible. Nothing is dropped silently.

What is mapped
- keyboard locale -> `locales` (the language part) and `layoutId` (E20 reversed: the `-t-k0-<id>` tail, or
  a slug of `info@name`, each subtag cut to 8 characters);
- `version@number` -> `version`; `info@name` -> `name`; `info@author` -> `authors`;
- hardware layers: a layer's `modifiers` -> an ISO level (none 1, shift 2, altR 3, altR+shift 4, and the
  same with caps 5-8, declared in `levelSelectors`); `ctrl alt` is read as AltGr (lossy, reported). Each
  row is paired with the scan codes of the layers' form: a CLDR implied form (us, iso, abnt2, jis, ks) or a
  `<forms>` form with `scanCodes`. A scan code gives the ISO key id and the HID usage (the table of the
  exporters, plus the ABNT2 Ro and JIS Yen keys);
- `<key>` definitions, including the implicit CLDR import `keys-Latn-implied` (letters, digits, space, gap)
  and the explicit `keys-Zyyy-punctuation` / `keys-Zyyy-currency` imports, bundled in
  `tools/importers/data/` (CLDR release 47, Unicode license) because the importer works offline;
- outputs: literal text, `\\u{..}` escapes and `${string}` variables; a single marker `\\m{id}` is a
  dead-key output;
- simple transforms whose `from` is a marker followed by literal characters or one `$[set]` (captured or
  not) become dead-key compositions; sets are expanded (`$1` and `$[1:set]` in `to`); a bare marker
  with a literal `to` is the dead key `fallback` (E15). The first rule wins when two give the same base;
- `<display output="\\m{id}">` -> dead key `display`.

What is preserved in `extensions.OKLM_ldml.unmapped` (verbatim XML) rather than mapped: transforms with
regular-expression constructs, chained markers or no `to`; transform types other than `simple`; touch
layers and forms; keys with attributes the core has no field for (long press, flick, switch...);
displays that are not about a marker; unresolved imports; `settings`, `flicks`, `names`... and any
element this importer does not know. XML comments are not kept.

What is reported as unsupported (neither mapped nor preserved): a key id used in a layer that nothing
defines (output lost, the id is listed), an output that mixes a marker and text, a scan code without an
ISO key id, a marker that has no transform (its key outputs become silent, E21).

Scope limits: no `uset` variables, no `type="final"` or `backspace` transforms, no reorder, no gesture
keys (flicks / long press): they are preserved, not interpreted.
"""
import re
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

from exporters.common import GENERATOR_VERSION
from exporters.ldml import HID_TO_SCANCODE1, load_implied_forms

NAMESPACE = "OKLM_ldml"
DATA = Path(__file__).resolve().parent / "data"
BUNDLED_IMPORTS = {"keys-Zyyy-punctuation.xml", "keys-Zyyy-currency.xml", "keys-Latn-implied.xml"}
SCHEMA_VERSION = "0.2"

HARDWARE_FORM_GEOMETRY = {"us": "ansi-full", "iso": "iso-full", "abnt2": "abnt-full", "jis": "jis-full", "ks": "ks-full"}

LEVEL_OF = {
    frozenset(): "1",
    frozenset({"shift"}): "2",
    frozenset({"altR"}): "3",
    frozenset({"altR", "shift"}): "4",
    frozenset({"caps"}): "5",
    frozenset({"caps", "shift"}): "6",
    frozenset({"caps", "altR"}): "7",
    frozenset({"caps", "altR", "shift"}): "8",
}
SELECTORS_OF = {
    "5": ["CapsLock"],
    "6": ["CapsLock", "Level2Shift"],
    "7": ["CapsLock", "Level3Shift"],
    "8": ["CapsLock", "Level2Shift", "Level3Shift"],
}

REGEX_META = set("\\^$.|?*+()[]{}")
SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$")
LOCALE_OK = re.compile(r"^[a-zA-Z]{2,8}(-[a-zA-Z0-9]{1,8})*$")
LAYOUT_ID_OK = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DEADKEY_ID_OK = re.compile(r"^[a-z][a-z0-9-]*$")

TOKEN = re.compile(r"\\m\{([^}]+)\}|\\u\{([0-9A-Fa-f]+(?: [0-9A-Fa-f]+)*)\}|\\(.)|(.)", re.S)
VARIABLE = re.compile(r"\$\{([^}]+)\}")


class Unsupported(Exception):
    """A construct this importer does not map (the caller preserves or reports it)."""


# ---------------------------------------------------------------------------
# scan codes
# ---------------------------------------------------------------------------

def _scan_tables():
    rows = {
        "E": "29 02 03 04 05 06 07 08 09 0A 0B 0C 0D",
        "D": "10 11 12 13 14 15 16 17 18 19 1A 1B",
        "C": "1E 1F 20 21 22 23 24 25 26 27 28 2B",
        "B": "56 2C 2D 2E 2F 30 31 32 33 34 35",
    }
    ids = {}
    for row, codes in rows.items():
        first = 0 if row in "EB" else 1
        for index, code in enumerate(codes.split()):
            ids[code] = f"{row}{first + index:02d}"
    ids.update({"39": "A03", "73": "B11", "7D": "E13"})
    hids = {code: hid for hid, code in HID_TO_SCANCODE1.items()}
    hids.update({"73": "0x87", "7D": "0x89"})
    return ids, hids


SCAN_TO_ID, SCAN_TO_HID = _scan_tables()
ROW_ORDER = "EDCBA"


def key_sort(key_id):
    return ROW_ORDER.index(key_id[0]), int(key_id[1:])


# ---------------------------------------------------------------------------
# text helpers
# ---------------------------------------------------------------------------

def tokenize(text):
    """LDML string -> [("m", id) | ("t", text)]. Raises Unsupported for an escape this importer does not know."""
    tokens = []
    for match in TOKEN.finditer(text):
        marker, code_points, other, plain = match.groups()
        if marker is not None:
            tokens.append(("m", marker))
            continue
        if code_points is not None:
            try:
                piece = "".join(chr(int(cp, 16)) for cp in code_points.split())
            except (ValueError, OverflowError) as exc:
                raise Unsupported(f"invalid code point in \\u{{{code_points}}}") from exc
        elif other is not None:
            raise Unsupported(f"escape \\{other} is not part of the LDML output syntax")
        else:
            piece = plain
        if tokens and tokens[-1][0] == "t":
            tokens[-1] = ("t", tokens[-1][1] + piece)
        else:
            tokens.append(("t", piece))
    return tokens


def substitute(text, strings):
    """Replace ${name} by the value of the `string` variable. Raises Unsupported for an unknown name."""
    def repl(match):
        name = match.group(1)
        if name not in strings:
            raise Unsupported(f"variable ${{{name}}} is not defined by a string element")
        return strings[name]
    return VARIABLE.sub(repl, text)


def literal(text, strings):
    """A string without markers: escapes and ${} resolved."""
    tokens = tokenize(substitute(text, strings))
    if any(kind == "m" for kind, _ in tokens):
        raise Unsupported("a marker where plain text was expected")
    return "".join(value for _, value in tokens)


def slug(text):
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")


def _strip_namespaces(root):
    for element in root.iter():
        if isinstance(element.tag, str) and "}" in element.tag:
            element.tag = element.tag.split("}", 1)[1]


def xml_of(element):
    saved = element.tail
    element.tail = None
    text = ET.tostring(element, encoding="unicode")
    element.tail = saved
    return re.sub(r"\s+\n", "\n", text.strip())


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

class ImportReport:
    def __init__(self, source_file):
        self.source_file = source_file
        self.source_version = None
        self.conforms_to = None
        self.target_file = None
        self.mapped = []
        self.skipped = []
        self.lossy = []
        self.preserved = {}  # construct -> count
        self.unsupported = []
        self.enrichment = []
        self.warnings = []
        self.errors = []
        self.keys_mapped = 0

    def map(self, path):
        if path not in self.mapped:
            self.mapped.append(path)

    def preserve(self, construct):
        self.preserved[construct] = self.preserved.get(construct, 0) + 1

    def build(self):
        if self.errors:
            level = "failed"
        elif not self.keys_mapped:
            level = "unsupported"
        elif self.lossy or self.unsupported:
            level = "lossy-mapping"
        elif self.preserved or self.skipped:
            level = "lossy-metadata"
        else:
            level = "lossless-core"
        if level in ("failed", "unsupported") or self.unsupported:
            confidence = "low"
        elif self.lossy or self.preserved:
            confidence = "medium"
        else:
            confidence = "high"
        source = {"format": "ldml-keyboard-3"}
        if self.source_file:
            source["file"] = self.source_file
        if self.source_version:
            source["version"] = self.source_version
        if self.conforms_to:
            source["conformsTo"] = self.conforms_to
        target = {"format": "oklm", "version": SCHEMA_VERSION}
        if self.target_file:
            target["file"] = self.target_file
        return {
            "schemaVersion": SCHEMA_VERSION,
            "direction": "ldml-to-oklm",
            "source": source,
            "target": target,
            "compatibilityLevel": level,
            "mappedFields": list(self.mapped),
            "skippedFields": list(self.skipped),
            "lossyMappings": list(self.lossy),
            "preservedAsExtensions": [
                {"construct": f"{name} ({count})" if count > 1 else name, "extensionNamespace": NAMESPACE}
                for name, count in self.preserved.items()
            ],
            "unsupportedConstructs": list(self.unsupported),
            "suggestedEnrichmentTasks": list(self.enrichment),
            "roundTripConfidence": confidence,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "generator": {"name": "oklm-importers", "version": GENERATOR_VERSION},
        }


# ---------------------------------------------------------------------------
# variables, sets, transforms
# ---------------------------------------------------------------------------

def expand_set(name, sets, strings, stack=()):
    if name not in sets:
        raise Unsupported(f"set ${{[{name}]}} is not defined")
    if name in stack:
        raise Unsupported(f"set {name} refers to itself")
    items = []
    for token in sets[name].split():
        ref = re.fullmatch(r"\$\[([^\]]+)\]", token)
        if ref:
            items.extend(expand_set(ref.group(1), sets, strings, stack + (name,)))
        else:
            items.append(literal(token, strings))
    return items


def parse_from(text, strings):
    """-> (marker, prefix, set name or None, suffix). Raises Unsupported."""
    text = substitute(text, strings)
    position = 0
    marker = None
    prefix, suffix, set_name = [], [], None
    target = prefix
    while position < len(text):
        rest = text[position:]
        if rest.startswith("\\m{"):
            end = rest.index("}") if "}" in rest else -1
            if end < 0:
                raise Unsupported("unterminated marker")
            if marker is not None:
                raise Unsupported("a second marker in `from` (chained dead keys)")
            if position != 0:
                raise Unsupported("`from` does not start with a marker")
            marker = rest[3:end]
            position += end + 1
            continue
        if marker is None:
            raise Unsupported("`from` does not start with a marker")
        capture = re.match(r"\(\$\[([^\]]+)\]\)", rest)
        bare = re.match(r"\$\[([^\]]+)\]", rest)
        if capture or bare:
            if set_name is not None:
                raise Unsupported("more than one set in `from`")
            set_name = (capture or bare).group(1)
            target = suffix
            position += len((capture or bare).group(0))
            continue
        match = TOKEN.match(text, position)
        marker_id, code_points, other, plain = match.groups()
        if marker_id is not None:
            raise Unsupported("a second marker in `from` (chained dead keys)")
        if code_points is not None:
            try:
                target.append("".join(chr(int(cp, 16)) for cp in code_points.split()))
            except (ValueError, OverflowError) as exc:
                raise Unsupported("invalid code point in `from`") from exc
        elif other is not None:
            if other in REGEX_META:
                target.append(other)
            else:
                raise Unsupported(f"regular-expression escape \\{other}")
        else:
            if plain in REGEX_META:
                raise Unsupported(f"regular-expression construct '{plain}'")
            target.append(plain)
        position = match.end()
    if marker is None:
        raise Unsupported("`from` does not start with a marker")
    return marker, "".join(prefix), set_name, "".join(suffix)


def parse_to(text, strings):
    """-> list of parts: ("t", text) | ("capture",) | ("mapped", set name)."""
    text = substitute(text, strings)
    parts = []
    position = 0

    def add_text(piece):
        if parts and parts[-1][0] == "t":
            parts[-1] = ("t", parts[-1][1] + piece)
        else:
            parts.append(("t", piece))

    while position < len(text):
        rest = text[position:]
        mapped = re.match(r"\$\[1:([^\]]+)\]", rest)
        if mapped:
            parts.append(("mapped", mapped.group(1)))
            position += len(mapped.group(0))
            continue
        if rest.startswith("$1"):
            parts.append(("capture",))
            position += 2
            continue
        if rest.startswith("$"):
            raise Unsupported("a `$` reference other than $1 and $[1:set] in `to`")
        match = TOKEN.match(text, position)
        marker_id, code_points, other, plain = match.groups()
        if marker_id is not None:
            raise Unsupported("a marker in `to`")
        if code_points is not None:
            try:
                add_text("".join(chr(int(cp, 16)) for cp in code_points.split()))
            except (ValueError, OverflowError) as exc:
                raise Unsupported("invalid code point in `to`") from exc
        elif other is not None:
            raise Unsupported(f"escape \\{other} in `to`")
        else:
            add_text(plain)
        position = match.end()
    return parts


def expand_rule(from_text, to_text, sets, strings):
    """One simple transform -> (marker, [(base, result), ...]) or (marker, None, fallback).

    Raises Unsupported when the rule cannot be expressed as compositions.
    """
    if to_text is None:
        raise Unsupported("a transform without `to` deletes its match")
    marker, prefix, set_name, suffix = parse_from(from_text, strings)
    parts = parse_to(to_text, strings)
    uses_set = any(p[0] in ("capture", "mapped") for p in parts)
    if set_name is None:
        if uses_set:
            raise Unsupported("`to` refers to a capture that `from` does not have")
        result = "".join(p[1] for p in parts)
        if not result:
            raise Unsupported("empty result")
        if not prefix and not suffix:
            return marker, None, result
        return marker, [(prefix + suffix, result)], None
    members = expand_set(set_name, sets, strings)
    lookups = {}
    for part in parts:
        if part[0] == "mapped":
            targets = expand_set(part[1], sets, strings)
            if len(targets) != len(members):
                raise Unsupported(f"sets {set_name} and {part[1]} have different sizes ({len(members)} / {len(targets)})")
            lookups[part[1]] = targets
    pairs = []
    for index, member in enumerate(members):
        out = []
        for part in parts:
            if part[0] == "t":
                out.append(part[1])
            elif part[0] == "capture":
                out.append(member)
            else:
                out.append(lookups[part[1]][index])
        result = "".join(out)
        if result:
            pairs.append((prefix + member + suffix, result))
    return marker, pairs, None


# ---------------------------------------------------------------------------
# the importer
# ---------------------------------------------------------------------------

def _combo_level(components):
    components = set(components)
    note = None
    if {"ctrl", "alt"} <= components:
        components -= {"ctrl", "alt"}
        components.add("altR")
        note = "ctrl alt"
    return LEVEL_OF.get(frozenset(components)), note


def parse_modifiers(attr):
    """-> ([levels], [notes], [unmapped alternatives])."""
    levels, notes, rejected = [], [], []
    for alternative in attr.split(","):
        words = alternative.split()
        components = [] if words in ([], ["none"]) else words
        level, note = _combo_level(components)
        if level is None:
            rejected.append(alternative.strip())
        else:
            levels.append(level)
            if note:
                notes.append(note)
    return levels, notes, rejected


def import_ldml(source, source_file=None, license=None, authors=None, layout_id=None):
    """Returns (manifest_dict_or_None, report_dict). `source` is the XML text or bytes."""
    report = ImportReport(source_file)
    unmapped = []  # preserved verbatim: {"construct", "reason", "xml"}

    def keep(construct, reason, element):
        report.preserve(construct)
        unmapped.append({"construct": construct, "reason": reason, "xml": xml_of(element)})

    try:
        root = ET.fromstring(source)
    except ET.ParseError as exc:
        report.errors.append(f"not well-formed XML: {exc}")
        return None, report.build()
    namespace_uri = root.tag.split("}")[0][1:] if root.tag.startswith("{") else ""
    _strip_namespaces(root)
    if root.tag != "keyboard3":
        report.errors.append(f"root element is <{root.tag}>, expected <keyboard3> (LDML Keyboard 3.0)")
        return None, report.build()
    found = re.search(r"/cldr/(\d+)/keyboard3", namespace_uri)
    if found:
        report.source_version = found.group(1)
    conforms = root.get("conformsTo")
    if conforms and conforms.isdigit() and int(conforms) >= 45:
        report.conforms_to = int(conforms)
    elif conforms:
        report.warnings.append(f"conformsTo='{conforms}' is below 45: not carried to the report")
    report.map("keyboard3@conformsTo")

    children = {}
    for child in root:
        children.setdefault(child.tag, []).append(child)

    # -- identity -----------------------------------------------------------------------------
    locale_attr = root.get("locale") or ""
    info = (children.get("info") or [None])[0]
    name = (info.get("name") if info is not None else None) or ""
    base_locale = re.split(r"-[tu]-", locale_attr)[0] if locale_attr else ""
    tail = re.search(r"-t-k0-(.+)$", locale_attr)
    locales = []
    if base_locale and LOCALE_OK.match(base_locale):
        locales.append(base_locale)
    elif base_locale:
        report.warnings.append(f"locale '{base_locale}' is not a valid BCP 47 language tag: ignored")
    for locales_element in children.get("locales", []):
        for item in locales_element.iter("locale"):
            tag = item.get("id")
            if tag and LOCALE_OK.match(tag) and tag not in locales:
                locales.append(tag)
            elif tag and tag not in locales:
                report.warnings.append(f"locale '{tag}' is not a valid BCP 47 language tag: ignored")
    if not locales:
        locales = ["und"]
        report.lossy.append({"path": "locales", "detail": "no usable locale in the file: 'und' (undetermined) used"})
    report.map("keyboard3@locale")
    if children.get("locales"):
        report.map("locales")

    if layout_id:
        resolved_id = layout_id
    elif tail and LAYOUT_ID_OK.match(tail.group(1).lower()):
        resolved_id = tail.group(1).lower()
    else:
        words = [w[:8] for w in slug(name).split("-") if w] if name else []
        resolved_id = "-".join(words) or "imported-layout"
        report.lossy.append({
            "path": "layoutId",
            "detail": f"the locale '{locale_attr}' carries no -t-k0-<id> tail: layoutId derived from info@name "
                      f"as '{resolved_id}' (each subtag cut to 8 characters, E20)"})
    if not LAYOUT_ID_OK.match(resolved_id):
        report.errors.append(f"layoutId '{resolved_id}' is not lowercase kebab-case")
        return None, report.build()

    version_element = (children.get("version") or [None])[0]
    version_number = version_element.get("number") if version_element is not None else None
    metadata = {}
    if version_number and SEMVER.match(version_number):
        version = version_number
        report.map("version@number")
    else:
        version = "1.0.0"
        if version_number:
            metadata["versionLabel"] = version_number
            report.lossy.append({"path": "version@number", "detail": f"'{version_number}' is not SemVer: version 1.0.0, label kept in metadata.versionLabel"})
        else:
            report.warnings.append("the file has no version element: version 1.0.0 (OKLM default)")

    if not name:
        name = layout_id or resolved_id
        report.warnings.append(f"info@name is missing: the layoutId '{name}' is used as the name")
    report.map("info@name")
    info_extra = {}
    author = info.get("author") if info is not None else None
    if info is not None:
        for attribute, value in info.attrib.items():
            if attribute not in ("name", "author"):
                info_extra[attribute] = value
    if authors:
        author_list = list(authors)
    elif author:
        author_list = [author]
        report.map("info@author")
    else:
        author_list = ["Unknown"]
        report.warnings.append("info@author is missing: authors is ['Unknown'] (OKLM requires one author)")
        report.enrichment.append("name the layout authors (the file does not say)")

    # -- variables ----------------------------------------------------------------------------
    strings, sets, usets = {}, {}, []
    for variables in children.get("variables", []):
        for variable in variables:
            if variable.tag == "string" and variable.get("id") is not None:
                strings[variable.get("id")] = variable.get("value", "")
            elif variable.tag == "set" and variable.get("id") is not None:
                sets[variable.get("id")] = variable.get("value", "")
            else:
                usets.append(variable)
    if strings or sets:
        report.map("variables.string")
        report.map("variables.set")

    # -- key definitions ----------------------------------------------------------------------
    key_outputs = {}
    gap_ids = {"gap"}
    unresolved_imports = []
    width_noted = []

    def read_keys(container, origin):
        for element in container:
            if element.tag == "import":
                base_name = (element.get("path") or "").rsplit("/", 1)[-1]
                if element.get("base") == "cldr" and base_name in BUNDLED_IMPORTS:
                    bundled = ET.parse(DATA / base_name).getroot()
                    read_keys(bundled, base_name)
                    report.map("keys.import@cldr")
                else:
                    unresolved_imports.append(element)
                    keep("keys import (unresolved)", f"import {element.get('base')}:{element.get('path')} is not bundled; the keys it defines are unknown", element)
                continue
            if element.tag != "key":
                keep(f"keys/{element.tag}", "element not interpreted", element)
                continue
            key_id = element.get("id")
            if key_id is None:
                keep("key without id", "no id", element)
                continue
            if element.get("gap") == "true":
                gap_ids.add(key_id)
                continue
            extra = set(element.attrib) - {"id", "output", "width", "stretch"}
            if origin == "file" and ({"width", "stretch"} & set(element.attrib)) and not width_noted:
                width_noted.append(True)
                report.skipped.append({"path": "keys.key@width, keys.key@stretch", "reason": "relative key sizes only matter to touch layouts and drawn hardware rows"})
            if extra:
                keep("key attributes", "attributes with no OKLM core field: " + ", ".join(sorted(extra)), element)
            if element.get("output") is not None:
                key_outputs[key_id] = element.get("output")
            elif not extra:
                keep("key without output", "no output attribute", element)

    read_keys(ET.parse(DATA / "keys-Latn-implied.xml").getroot(), "implied")
    for keys in children.get("keys", []):
        read_keys(keys, "file")
    report.map("keys.key")

    # -- forms ----------------------------------------------------------------------------------
    custom_forms = {}
    for forms in children.get("forms", []):
        for form in forms:
            rows = [[code.upper() for code in row.get("codes", "").split()] for row in form.iter("scanCodes")]
            if form.tag == "form" and rows:
                custom_forms[form.get("id")] = rows
            else:
                keep("form (not hardware)", "no scanCodes rows", form)
    implied = load_implied_forms()

    # -- layers ---------------------------------------------------------------------------------
    positions = {}  # scan code -> {level: tokens}
    used_levels = {}  # level -> modifiers attribute
    form_id_used = None
    form_rows_used = []
    hardware_done = False
    for layers in children.get("layers", []):
        form_id = layers.get("formId")
        rows_of_form = custom_forms.get(form_id) or implied.get(form_id)
        if rows_of_form is None or hardware_done:
            keep("layers (not the hardware layers)", f"formId={form_id}: touch layout or second hardware layout", layers)
            continue
        hardware_done = True
        form_id_used = form_id
        form_rows_used = rows_of_form
        for layer in layers.findall("layer"):
            modifiers = layer.get("modifiers")
            if modifiers is None:
                keep("layer (no modifiers)", "touch layer", layer)
                continue
            levels, notes, rejected = parse_modifiers(modifiers)
            if not levels:
                keep("layer (modifiers not mapped)", f"modifiers='{modifiers}' has no ISO level equivalent", layer)
                continue
            if rejected:
                keep("layer alternatives", f"modifiers='{modifiers}': alternative(s) '{', '.join(rejected)}' not mapped", layer)
            if notes:
                report.lossy.append({"path": f"layers.layer[{modifiers}]", "detail": "'ctrl alt' is read as the AltGr level (Level3Shift)"})
            fresh = [level for level in levels if level not in used_levels]
            if not fresh:
                keep("layer (duplicate level)", f"modifiers='{modifiers}' maps to level(s) {', '.join(levels)} already filled by an earlier layer", layer)
                continue
            for level in fresh:
                used_levels[level] = modifiers
            layer_rows = layer.findall("row")
            if len(layer_rows) > len(rows_of_form):
                keep("layer (more rows than the form)", f"{len(layer_rows)} rows for a form of {len(rows_of_form)}", layer)
                for level in fresh:
                    used_levels.pop(level)
                continue
            for row_index, row in enumerate(layer_rows):
                ids = (row.get("keys") or "").split()
                codes = rows_of_form[row_index]
                if len(ids) > len(codes):
                    report.warnings.append(f"layer '{modifiers}', row {row_index + 1}: {len(ids)} keys for {len(codes)} scan codes: the extra keys are ignored")
                for code, key_id in zip(codes, ids):
                    if key_id in gap_ids:
                        continue
                    if key_id not in key_outputs:
                        report.unsupported.append({
                            "construct": f"key id '{key_id}'",
                            "detail": f"used in layer '{modifiers}' at scan code {code} but defined by nothing the importer can read: output lost"})
                        continue
                    try:
                        tokens = tokenize(substitute(key_outputs[key_id], strings))
                    except Unsupported as exc:
                        report.unsupported.append({"construct": f"key id '{key_id}'", "detail": f"output not readable ({exc})"})
                        continue
                    for level in fresh:
                        positions.setdefault(code, {})[level] = (key_id, tokens)
    if not hardware_done:
        report.errors.append("no hardware <layers> element: nothing to map (touch-only keyboard)")
        return None, report.build()
    # scan code 2B is the key right of the bracket: D13 on the US/KS forms (it ends the Q row there),
    # C12 on the ISO-family forms (it ends the A row). Same HID 0x31 either way.
    id_for = dict(SCAN_TO_ID)
    if any("2B" in row for row in form_rows_used[1:2]):
        id_for["2B"] = "D13"
    report.map("layers.layer")
    report.map("layers.row")
    report.map("layers@formId" if form_id_used in implied and form_id_used not in custom_forms else "forms.form")

    # -- transforms -----------------------------------------------------------------------------
    compositions = {}  # marker -> {base: result}
    fallbacks = {}
    shadowed = 0
    for transforms in children.get("transforms", []):
        if transforms.get("type") != "simple":
            keep(f"transforms type={transforms.get('type')}", "only simple transforms are interpreted", transforms)
            continue
        for group in transforms:
            if group.tag != "transformGroup":
                keep(f"transforms/{group.tag}", "element not interpreted", group)
                continue
            for rule in group:
                if rule.tag != "transform":
                    keep(f"transformGroup/{rule.tag}", "reorder or other group content is not interpreted", rule)
                    continue
                extra = set(rule.attrib) - {"from", "to"}
                if extra:
                    keep("transform", "attributes not interpreted: " + ", ".join(sorted(extra)), rule)
                    continue
                try:
                    marker, pairs, fallback = expand_rule(rule.get("from", ""), rule.get("to"), sets, strings)
                except Unsupported as exc:
                    keep("transform", str(exc), rule)
                    continue
                table = compositions.setdefault(marker, {})
                if fallback is not None:
                    if marker in fallbacks:
                        shadowed += 1
                    else:
                        fallbacks[marker] = fallback
                for base, result in pairs or []:
                    if base in table:
                        shadowed += 1
                    else:
                        table[base] = result
    if children.get("transforms"):
        report.map("transforms.transform")
    if shadowed:
        report.warnings.append(f"{shadowed} composition(s) were shadowed by an earlier rule for the same marker and base and dropped (first rule wins)")

    # -- dead-key ids -----------------------------------------------------------------------------
    id_of = {}
    marker_used_in_keys = []
    for code in sorted(positions, key=lambda c: key_sort(id_for[c]) if c in id_for else (9, 0)):
        for level in sorted(positions[code], key=int):
            for kind, value in positions[code][level][1]:
                if kind == "m" and value not in marker_used_in_keys:
                    marker_used_in_keys.append(value)
    marker_order = list(marker_used_in_keys)
    for marker in list(compositions) + list(fallbacks):
        if marker not in marker_order:
            marker_order.append(marker)

    def deadkey_id(marker):
        if marker in id_of:
            return id_of[marker]
        candidate = re.sub(r"[^a-z0-9-]+", "-", marker.lower().replace("_", "-")).strip("-")
        if not DEADKEY_ID_OK.match(candidate):
            candidate = "m-" + candidate if candidate else "marker"
        taken = set(id_of.values())
        unique = candidate
        counter = 2
        while unique in taken:
            unique = f"{candidate}-{counter}"
            counter += 1
        id_of[marker] = unique
        if unique != marker:
            report.lossy.append({"path": f"deadKeys[{unique}]", "detail": f"marker '{marker}' renamed '{unique}' (dead-key ids are lowercase kebab-case); original kept in extensions.{NAMESPACE}"})
        return unique

    # a marker defines a dead key only if it has a composition or a fallback
    live_markers = [m for m in marker_order if compositions.get(m) or m in fallbacks]
    for marker in live_markers:
        deadkey_id(marker)

    # -- displays ---------------------------------------------------------------------------------
    displays = {}
    for display_group in children.get("displays", []):
        for display in display_group:
            if display.tag != "display" or display.get("output") is None or display.get("display") is None or display.get("keyId"):
                keep("display (not about a marker)", "display of a key id or a character", display)
                continue
            try:
                out_tokens = tokenize(display.get("output"))
                shown = literal(display.get("display"), strings)
            except Unsupported as exc:
                keep("display", f"not readable ({exc})", display)
                continue
            if len(out_tokens) == 1 and out_tokens[0][0] == "m" and shown:
                displays.setdefault(out_tokens[0][1], shown)
            else:
                keep("display (not about a marker)", "display of a character sequence", display)
    if displays:
        report.map("displays.display")

    # -- keys -------------------------------------------------------------------------------------
    keys = []
    silent_dead = {}
    dropped_positions = []
    for code in sorted(positions, key=lambda c: key_sort(id_for[c]) if c in id_for else (9, 0)):
        if code not in id_for:
            ids = sorted({entry[0] for entry in positions[code].values()})
            report.unsupported.append({"construct": f"scan code {code}", "detail": f"no ISO key id / HID for this scan code: keys {', '.join(ids)} not mapped"})
            continue
        levels = {}
        for level in sorted(positions[code], key=int):
            key_id, tokens = positions[code][level]
            if len(tokens) == 1 and tokens[0][0] == "t":
                levels[level] = tokens[0][1]
            elif len(tokens) == 1:
                marker = tokens[0][1]
                if marker in id_of and marker in live_markers:
                    levels[level] = {"deadKey": id_of[marker]}
                else:
                    silent_dead.setdefault(marker, []).append(f"{id_for[code]}/{level}")
            elif not tokens:
                continue
            else:
                report.unsupported.append({"construct": f"key id '{key_id}'", "detail": f"output mixes a marker and text ({key_outputs[key_id]}): level {level} of {id_for[code]} lost"})
        if levels:
            keys.append({"id": id_for[code], "hid": SCAN_TO_HID[code], "levels": levels})
        else:
            dropped_positions.append(id_for[code])
    for marker, where in silent_dead.items():
        report.unsupported.append({
            "construct": f"marker '{marker}'",
            "detail": f"no transform uses it: the key outputs {', '.join(where)} produce nothing visible and become silent levels (E21)"})
    if dropped_positions:
        report.warnings.append(f"{len(dropped_positions)} key position(s) have no output at any level and were not created: {', '.join(dropped_positions)}")
    report.keys_mapped = len(keys)
    if not keys:
        report.errors.append("no key with an output could be mapped")
        return None, report.build()
    report.map("keys")

    dead_keys = []
    for marker in live_markers:
        entry = {"id": id_of[marker]}
        if marker in displays:
            entry["display"] = displays.pop(marker)
        compositions_of = compositions.get(marker, {})
        if not compositions_of:
            compositions_of = {}
        entry["compositions"] = compositions_of
        if marker in fallbacks:
            entry["fallback"] = fallbacks[marker]
        if id_of[marker] != marker:
            entry["extensions"] = {NAMESPACE: {"markerId": marker}}
        dead_keys.append(entry)
    for marker, shown in displays.items():
        unmapped.append({"construct": "display (marker without dead key)", "reason": "the marker has no transform", "xml": f'<display output="\\m{{{marker}}}" display="{shown}"/>'})
        report.preserve("display (marker without dead key)")
    # compositions can be empty only when a fallback gives the dead key a meaning; the schema wants
    # at least one composition, so a dead key with only a fallback keeps the fallback as its composition of space.
    for entry in dead_keys:
        if not entry["compositions"]:
            entry["compositions"] = {" ": entry["fallback"]}
            report.lossy.append({"path": f"deadKeys[{entry['id']}]", "detail": "the marker has only a bare-marker rule; the schema requires one composition, so space -> fallback was added (same output as the fallback rule)"})
    if dead_keys:
        report.map("deadKeys")

    # -- levels and selectors --------------------------------------------------------------------
    present_levels = {level for key in keys for level in key["levels"]}
    level_selectors = {level: SELECTORS_OF[level] for level in sorted(present_levels) if level in SELECTORS_OF}
    if level_selectors:
        report.map("levelSelectors")

    # -- what else the file has --------------------------------------------------------------------
    known = {"version", "info", "locales", "keys", "forms", "layers", "transforms", "displays", "variables"}
    for tag, elements in children.items():
        if tag not in known:
            for element in elements:
                keep(f"{tag}", "element not interpreted by the importer", element)
    for element in usets:
        keep("variables/uset", "UnicodeSet variables are not interpreted", element)
    if unmapped and (strings or sets):
        for variables in children.get("variables", []):
            unmapped.append({"construct": "variables", "reason": "needed to read the preserved constructs", "xml": xml_of(variables)})
            report.preserve("variables")
    raw = source if isinstance(source, str) else bytes(source).decode("utf-8", "replace")
    if "<!--" in raw:
        report.skipped.append({"path": "(XML comments)", "reason": "comments are not part of the parsed model and are not kept"})

    # -- assemble the manifest ---------------------------------------------------------------------
    geometry = HARDWARE_FORM_GEOMETRY.get(form_id_used)
    if geometry is None:
        geometry = "custom"
        report.warnings.append(f"form '{form_id_used}' is a custom scan-code form: geometry is 'custom'")
    else:
        report.warnings.append(f"form '{form_id_used}' gives the family only: geometry declared as '{geometry}' (LDML does not say the physical size)")
    if license:
        license_value = license
    else:
        license_value = "NOASSERTION"
        report.warnings.append("an LDML keyboard file carries no license field: license is NOASSERTION (pass --license to set it)")
        report.enrichment.append("set the license (the file does not carry one; CLDR data is Unicode-3.0)")

    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "layoutId": resolved_id,
        "name": name,
        "version": version,
        "license": license_value,
        "authors": author_list,
        "description": f"Imported from an LDML Keyboard 3 file ({source_file or 'unnamed'}"
                       + (f", conformsTo {report.conforms_to}" if report.conforms_to else "") + "). Draft 0.2 core.",
        "locales": locales,
        "geometry": [geometry],
    }
    if level_selectors:
        manifest["levelSelectors"] = level_selectors
    manifest["keys"] = sorted(keys, key=lambda k: key_sort(k["id"]))
    if dead_keys:
        manifest["deadKeys"] = dead_keys
    exports_options = {"conformsTo": report.conforms_to or 45}
    manifest["exports"] = [{"target": "ldml-keyboard-3", "id": "ldml", "options": exports_options}]
    if metadata:
        manifest["metadata"] = metadata
    extension = {"source": {"namespace": namespace_uri, "locale": locale_attr}}
    if info_extra:
        extension["info"] = info_extra
        report.preserve("info attributes")
    if unmapped:
        extension["unmapped"] = unmapped
    manifest["extensionsUsed"] = [NAMESPACE]
    manifest["extensions"] = {NAMESPACE: extension}
    report.enrichment.extend([
        "add metadata.training (fingers, difficulty) and metadata.dynamicLegends if the layout should be taught or shown",
        "name the dead keys (deadKeys[].name) and describe the layout (description)",
        "declare the physical sizes in geometry (the import only knows the family)",
    ])
    if unmapped:
        report.enrichment.append(f"review the {len(unmapped)} construct(s) kept in extensions.{NAMESPACE}.unmapped and decide which belong in the core")
    return manifest, report.build()
