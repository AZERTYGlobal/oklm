# -*- coding: utf-8 -*-
"""OKLM validator CLI (draft 0.2).

Validate one or more OKLM files against the draft 0.2 JSON Schemas, plus the
checks that JSON Schema cannot express. Every finding has a stable code (D42).

Usage:
    python validators/validate.py FILE [FILE ...]
    python validators/validate.py --strict FILE [FILE ...]
    python validators/validate.py --json FILE [FILE ...]
    python validators/validate.py --report FILE [FILE ...]

Files are treated as OKLM manifests (.oklm.json) by default; pass --report to
validate conversion reports instead. Exit code 0 if every file is valid, 1
otherwise. Warnings never change the exit code, except under --strict where
the warnings listed below become errors.

Codes (stable):
  E_SCHEMA                    JSON Schema violation (includes prefixed members outside `extensions`)
  E_DUPLICATE_KEY_ID          two keys share an id
  E_DUPLICATE_EXPORT_ID       two export declarations share an id
  E_DEADKEY_UNDEFINED         an output references a dead key that deadKeys does not define
  E_LAYERS_UNSUPPORTED        a `layers` member: OKLM outputs live in keys[].levels (D2, D14)
  E_SCHEMA_VERSION_MAJOR      schemaVersion MAJOR is not 0
  W_SCHEMA_VERSION_MINOR      schemaVersion MINOR is above 2: valid, not supported
  E_EXTENSIONS_REQUIRED       extensionsRequired is not a subset of extensionsUsed
  W_UNKNOWN_MEMBER            member the schema does not declare (error under --strict)
  W_GEOMETRY_UNKNOWN          geometry family not in the known list (error under --strict)
  E_HID_RANGE                 --strict only: hid outside 0x04-0xE7 (E10)
  E_W3C_CODE                  --strict only: code is not a W3C KeyboardEvent.code value (E10)
  E_DUPLICATE_CODE            --strict only: two keys share a code (E11)
  E_INTERNAL                  a validator stage crashed (validator bug); the other stages and files still run
  E_DUPLICATE_JSON_KEY        a member name appears twice in one JSON object (the last value would silently win)
  E_JSON_CONSTANT             NaN, Infinity, -Infinity or a number overflowing a float: not JSON
  E_SURROGATE                 a string or member name holds an unpaired surrogate (not UTF-8 encodable)
  E_READ                      file unreadable, not UTF-8 (a BOM is accepted) or not JSON; no file matches a pattern

Dependency: pip install jsonschema  (>= 4.x, Draft 2020-12)
"""
import argparse
import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from w3c_codes import W3C_CODES  # noqa: E402

SCHEMAS = Path(__file__).resolve().parent.parent / "schemas"

SUPPORTED_MAJOR = 0
SUPPORTED_MINOR = 2

HID_PHYSICAL_MIN = 0x04
HID_PHYSICAL_MAX = 0xE7

GEOMETRY_FAMILIES = {"iso", "ansi", "jis", "abnt", "ks", "touch", "custom"}
GEOMETRY_ALIASES = {"us": "ansi", "abnt2": "abnt"}

HINTS = {
    "layers": "OKLM has no `layers`; outputs live in keys[].levels (D2, D14)",
}


class Finding:
    """One validator finding: stable code, severity (error | warning), path, message."""

    def __init__(self, code, severity, path, message):
        self.code = code
        self.severity = severity
        self.path = path
        self.message = message

    def as_dict(self):
        return {"code": self.code, "severity": self.severity, "path": self.path, "message": self.message}

    def __str__(self):
        return f"{self.code} {self.path}: {self.message}"


def load_schema(name):
    schema = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def load_validator(name):
    return Draft202012Validator(load_schema(name))


def _fmt_path(parts):
    out = ""
    for part in parts:
        if isinstance(part, int):
            out += f"[{part}]"
        else:
            out += ("." if out else "") + str(part)
    return out or "(root)"


def schema_findings(manifest, validator):
    return [
        Finding("E_SCHEMA", "error", _fmt_path(error.path), error.message)
        for error in sorted(validator.iter_errors(manifest), key=lambda e: [str(p) for p in e.path])
    ]


def _dicts(value):
    """The dict items of `value` when it is a list, else nothing: a wrong type is E_SCHEMA's business."""
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _duplicates(values):
    """Sorted string values that occur more than once (one pass, O(n))."""
    counts = Counter(value for value in values if isinstance(value, str))
    return sorted(value for value, n in counts.items() if n > 1)


def _outputs(key):
    """Every output string or object of a key, levels (group 1) and groups, whatever the types around."""
    outputs = []
    levels = key.get("levels")
    if isinstance(levels, dict):
        outputs.extend(levels.values())
    groups = key.get("groups")
    if isinstance(groups, dict):
        for group in groups.values():
            if isinstance(group, dict):
                outputs.extend(group.values())
    return outputs


def _huge_int(text):
    """int(text) for digits, or a very large number for what Python refuses to convert (> 4300 digits)."""
    try:
        return int(text)
    except ValueError:
        return 10 ** 12


def consistency_findings(manifest):
    """Checks beyond JSON Schema: uniqueness, reference resolution, versions, capability lists.

    Every access is guarded by a type test: a manifest of the wrong shape is reported by the schema
    (E_SCHEMA), never by a crash here (A-01).
    """
    found = []
    if not isinstance(manifest, dict):
        return found
    keys = _dicts(manifest.get("keys"))

    for dup in _duplicates(k.get("id") for k in keys):
        found.append(Finding("E_DUPLICATE_KEY_ID", "error", "keys", f"duplicate key id {dup}"))

    exports = _dicts(manifest.get("exports"))
    for dup in _duplicates(e.get("id") for e in exports):
        found.append(Finding("E_DUPLICATE_EXPORT_ID", "error", "exports", f"duplicate export id {dup}"))

    dead_ids = {d.get("id") for d in _dicts(manifest.get("deadKeys")) if isinstance(d.get("id"), str)}
    for key in keys:
        for out in _outputs(key):
            if isinstance(out, dict) and isinstance(out.get("deadKey"), str) and out["deadKey"] not in dead_ids:
                found.append(
                    Finding(
                        "E_DEADKEY_UNDEFINED",
                        "error",
                        f"keys[{key.get('id')}]",
                        f"dead key '{out['deadKey']}' is not defined in deadKeys",
                    )
                )

    if "layers" in manifest:
        found.append(Finding("E_LAYERS_UNSUPPORTED", "error", "layers", HINTS["layers"]))

    version = manifest.get("schemaVersion")
    if isinstance(version, str) and re.fullmatch(r"[0-9]+\.[0-9]+", version):
        major, minor = (_huge_int(part) for part in version.split("."))
        if major != SUPPORTED_MAJOR:
            found.append(
                Finding("E_SCHEMA_VERSION_MAJOR", "error", "schemaVersion",
                        f"MAJOR {version.split('.')[0][:20]} is not supported "
                        f"(this validator reads MAJOR {SUPPORTED_MAJOR})")
            )
        elif minor > SUPPORTED_MINOR:
            found.append(
                Finding("W_SCHEMA_VERSION_MINOR", "warning", "schemaVersion",
                        f"{version} is valid but not supported (this validator reads up to "
                        f"{SUPPORTED_MAJOR}.{SUPPORTED_MINOR}); unknown members are ignored (D31)")
            )

    used = manifest.get("extensionsUsed")
    required = manifest.get("extensionsRequired")
    if isinstance(required, list):
        listed = {name for name in (used if isinstance(used, list) else []) if isinstance(name, str)}
        missing = sorted({name for name in required if isinstance(name, str)} - listed)
        if missing:
            found.append(
                Finding("E_EXTENSIONS_REQUIRED", "error", "extensionsRequired",
                        "not listed in extensionsUsed: " + ", ".join(missing))
            )

    geometry = manifest.get("geometry")
    for index, value in enumerate(geometry if isinstance(geometry, list) else []):
        if isinstance(value, str):
            family = value.split("-")[0]
            if family not in GEOMETRY_FAMILIES and family not in GEOMETRY_ALIASES:
                found.append(
                    Finding("W_GEOMETRY_UNKNOWN", "warning", f"geometry[{index}]",
                            f"family '{family}' is not in the known list "
                            f"({', '.join(sorted(GEOMETRY_FAMILIES | set(GEOMETRY_ALIASES)))})")
                )
    return found


def manifest_consistency_errors(manifest):
    """Back-compat helper for the exporters: error messages only."""
    return [f"{f.code} {f.path}: {f.message}" for f in consistency_findings(manifest) if f.severity == "error"]


def _resolve(schema, root):
    while isinstance(schema, dict) and "$ref" in schema:
        node = root
        for part in schema["$ref"].lstrip("#").strip("/").split("/"):
            node = node[part]
        schema = node
    return schema


def _type_matches(instance, schema):
    declared = schema.get("type")
    if declared is None:
        return True
    declared = declared if isinstance(declared, list) else [declared]
    if isinstance(instance, dict):
        return "object" in declared
    if isinstance(instance, list):
        return "array" in declared
    return not ({"object", "array"} >= set(declared))


def unknown_members(instance, schema, path=None, root=None, found=None):
    """Walk an instance alongside its schema and list members the schema does not declare.

    Free-form objects (no `properties`, no `patternProperties`) are not walked: metadata
    blocks and extension payloads carry what they want. Members that match a
    `patternProperties` entry are declared (a `false` entry is a schema error, reported
    by E_SCHEMA, not here).
    """
    root = schema if root is None else root
    path = [] if path is None else path
    found = [] if found is None else found
    schema = _resolve(schema, root)
    if not isinstance(schema, dict):
        return found

    alternatives = schema.get("oneOf", []) + schema.get("anyOf", [])
    if alternatives:
        for alt in alternatives:
            alt = _resolve(alt, root)
            if not isinstance(alt, dict) or not _type_matches(instance, alt):
                continue
            if isinstance(instance, dict) and not set(alt.get("required", [])) <= set(instance):
                continue
            unknown_members(instance, alt, path, root, found)
        # keywords next to the alternatives (key: properties, if/then) still apply
        if not schema.get("properties") and not schema.get("patternProperties"):
            return found
    for alt in schema.get("allOf", []):
        unknown_members(instance, alt, path, root, found)

    if isinstance(instance, list):
        items = schema.get("items")
        if isinstance(items, dict):
            for index, value in enumerate(instance):
                unknown_members(value, items, path + [index], root, found)
        return found

    if not isinstance(instance, dict):
        return found

    properties = schema.get("properties", {})
    patterns = schema.get("patternProperties", {})
    extra = schema.get("additionalProperties", True)
    if not properties and not patterns and not isinstance(extra, dict):
        return found  # free-form object

    for name, value in instance.items():
        here = path + [name]
        if name in properties:
            unknown_members(value, properties[name], here, root, found)
            continue
        matched = [sub for pattern, sub in patterns.items() if re.search(pattern, name)]
        if matched:
            for sub in matched:
                unknown_members(value, sub, here, root, found)
            continue
        if isinstance(extra, dict):
            unknown_members(value, extra, here, root, found)
            continue
        found.append((here, name))
    return found


def unknown_member_findings(manifest, schema, strict):
    severity = "error" if strict else "warning"
    out = []
    for here, name in unknown_members(manifest, schema):
        message = f"unknown member '{name}'"
        if name in HINTS:
            message += f" ({HINTS[name]})"
        elif name != "layers":
            message += " (a private member goes in an `extensions` object with an OKLM_, EXT_ or <VENDOR>_ prefix)"
        if name == "layers":
            continue  # reported as E_LAYERS_UNSUPPORTED
        out.append(Finding("W_UNKNOWN_MEMBER", severity, _fmt_path(here), message))
    return out


def strict_findings(manifest):
    """The --strict lint: HID usage ranges (E10), W3C code values and one code per key (E11)."""
    found = []
    codes_seen = {}
    if not isinstance(manifest, dict):
        return found
    for key in _dicts(manifest.get("keys")):
        key_id = str(key.get("id", "?"))
        hid = key.get("hid")
        if isinstance(hid, str) and re.fullmatch(r"0x[0-9A-Fa-f]{2,4}", hid):
            usage = int(hid, 16)
            if usage < HID_PHYSICAL_MIN:
                found.append(
                    Finding("E_HID_RANGE", "error", f"keys[{key_id}].hid",
                            f"{hid} is a non-physical usage (0x00-0x03: ErrorRollOver, POSTFail, ErrorUndefined)")
                )
            elif usage > HID_PHYSICAL_MAX:
                found.append(
                    Finding("E_HID_RANGE", "error", f"keys[{key_id}].hid",
                            f"{hid} is reserved in the HUT 1.7 keyboard/keypad page (0xE8-0xFFFF)")
                )
        code = key.get("code")
        if isinstance(code, str):
            if code not in W3C_CODES:
                found.append(
                    Finding("E_W3C_CODE", "error", f"keys[{key_id}].code",
                            f"'{code}' is not a KeyboardEvent.code value of the W3C Recommendation (2025-04-22)")
                )
            codes_seen.setdefault(code, []).append(key_id)
    for code, key_ids in sorted(codes_seen.items()):
        if len(key_ids) > 1:
            found.append(
                Finding("E_DUPLICATE_CODE", "error", "keys",
                        f"code '{code}' is used by keys {', '.join(key_ids)}: one code names one physical key")
            )
    return found


def guarded(stage):
    """Run one validator stage. A crash inside it becomes one E_INTERNAL finding: the other stages and
    the other files of a batch still run (A-01)."""
    try:
        return stage()
    except Exception as exc:  # noqa: BLE001 - RecursionError and MemoryError included, by design
        return [Finding("E_INTERNAL", "error", "(validator)",
                        f"internal error, this is a validator bug: {type(exc).__name__}: {str(exc)[:200]}")]


def analyze(manifest, schema=None, validator=None, strict=False):
    """All findings for one manifest. Returns a list of Finding."""
    schema = schema if schema is not None else load_schema("oklm-manifest.schema.json")
    validator = validator if validator is not None else Draft202012Validator(schema)
    stages = [lambda: schema_findings(manifest, validator),
              lambda: consistency_findings(manifest),
              lambda: unknown_member_findings(manifest, schema, strict)]
    if strict:
        stages.append(lambda: strict_findings(manifest))
    found = []
    for stage in stages:
        found += guarded(stage)
    if strict:
        for f in found:
            if f.code == "W_GEOMETRY_UNKNOWN":
                f.severity = "error"
    return found


class JsonConstantError(ValueError):
    """NaN, Infinity, -Infinity or a number that overflows a float: not JSON (RFC 8259)."""


class _Object(dict):
    """A parsed JSON object that remembers the member names it received more than once."""
    duplicates = ()


def _object_from_pairs(pairs):
    obj = _Object()
    duplicates = []
    for name, value in pairs:
        if name in obj:
            duplicates.append(name)
        obj[name] = value
    if duplicates:
        obj.duplicates = tuple(duplicates)
    return obj


def _refuse_constant(name):
    raise JsonConstantError(f"{name} is not valid JSON")


def _finite_float(text):
    value = float(text)
    if value in (float("inf"), float("-inf")):
        raise JsonConstantError(f"number {text[:30]} does not fit in a double-precision float")
    return value


def load_json_text(text):
    """Parse JSON text strictly: duplicate member names are recorded (see text_findings), NaN / Infinity
    and overflowing numbers raise JsonConstantError."""
    return json.loads(text, object_pairs_hook=_object_from_pairs, parse_constant=_refuse_constant,
                      parse_float=_finite_float)


def text_findings(instance):
    """What the JSON text can hide from a parsed document: member names given twice (the last value
    silently wins, A-11) and lone surrogates, which no UTF-8 file can carry (A-11). Iterative walk: a
    deeply nested document must not exhaust the stack."""
    found = []
    stack = [(instance, [])]
    while stack:
        node, path = stack.pop()
        if isinstance(node, dict):
            for name in getattr(node, "duplicates", ()):
                found.append(Finding("E_DUPLICATE_JSON_KEY", "error", _fmt_path(path),
                                     f"member '{name}' appears more than once in this object: "
                                     "only the last value would be kept"))
            for name, value in node.items():
                if _has_surrogate(name):
                    found.append(Finding("E_SURROGATE", "error", _fmt_path(path),
                                         "a member name contains an unpaired surrogate (not UTF-8 encodable)"))
                stack.append((value, path + [name]))
        elif isinstance(node, list):
            stack.extend((value, path + [index]) for index, value in enumerate(node))
        elif isinstance(node, str) and _has_surrogate(node):
            found.append(Finding("E_SURROGATE", "error", _fmt_path(path),
                                 "string contains an unpaired surrogate (not UTF-8 encodable)"))
    found.sort(key=lambda f: (f.path, f.code))
    return found


def _has_surrogate(text):
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        return True
    return False


def validate_file(path, schema, validator, strict=False, report=False):
    """All findings for one file. Never raises: a file that cannot be read is E_READ, a crash inside the
    validator is E_INTERNAL, so that a batch always reaches its last file."""
    path = Path(path)
    try:
        instance = load_json_text(path.read_bytes().decode("utf-8-sig"))
    except JsonConstantError as exc:
        return [Finding("E_JSON_CONSTANT", "error", "(file)", f"not JSON: {exc}")]
    except OSError as exc:
        if any(c in str(path) for c in "*?[") and not path.exists():
            return [Finding("E_READ", "error", "(file)", "no file matches this pattern")]
        return [Finding("E_READ", "error", "(file)", f"cannot read as JSON: {exc}")]
    except ValueError as exc:
        return [Finding("E_READ", "error", "(file)", f"cannot read as JSON: {exc}")]
    except RecursionError:
        return [Finding("E_READ", "error", "(file)", "cannot read as JSON: nested too deeply")]
    found = guarded(lambda: text_findings(instance))
    if report:
        return found + guarded(lambda: schema_findings(instance, validator))
    return found + analyze(instance, schema, validator, strict=strict)


def expand_arguments(names):
    """Expand wildcards ourselves: PowerShell 5.1 hands `examples/*.oklm.json` over unexpanded (A-20).
    A name that exists is kept as is; a pattern without match is kept too, validate_file reports it."""
    expanded = []
    for name in names:
        if any(c in name for c in "*?[") and not Path(name).exists():
            expanded.extend(sorted(glob.glob(name, recursive=True)) or [name])
        else:
            expanded.append(name)
    return expanded


def main():
    for stream in (sys.stdout, sys.stderr):
        try:  # redirected stdout is cp1252 on Windows: a CJK member name must not abort the report (A-12)
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description="Validate OKLM 0.2 files.")
    parser.add_argument("files", nargs="+", metavar="FILE")
    parser.add_argument("--report", action="store_true",
                        help="validate conversion reports instead of manifests")
    parser.add_argument("--strict", action="store_true",
                        help="manifests only: unknown members, unknown geometry families, non-physical or "
                        "reserved HID usages, unknown W3C code values and duplicated codes are errors")
    parser.add_argument("--json", action="store_true",
                        help="print one JSON report (stable codes) instead of text")
    args = parser.parse_args()

    schema = load_schema("oklm-conversion-report.schema.json" if args.report else "oklm-manifest.schema.json")
    validator = Draft202012Validator(schema)

    exit_code = 0
    results = []
    for name in expand_arguments(args.files):
        path = Path(name)
        findings = validate_file(path, schema, validator, strict=args.strict, report=args.report)
        errors = [f for f in findings if f.severity == "error"]
        warnings = [f for f in findings if f.severity == "warning"]
        if errors:
            exit_code = 1
        results.append({"file": str(path), "valid": not errors,
                        "findings": [f.as_dict() for f in findings]})
        if not args.json:
            if errors:
                print(f"INVALID {path}")
            else:
                print(f"VALID   {path}" + (" (strict)" if args.strict and not args.report else ""))
            for f in findings:
                print(f"  - {'WARN ' if f.severity == 'warning' else ''}{f}")
    if args.json:
        print(json.dumps({"strict": args.strict, "results": results}, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
