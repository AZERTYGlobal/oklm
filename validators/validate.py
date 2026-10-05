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

Dependency: pip install jsonschema  (>= 4.x, Draft 2020-12)
"""
import argparse
import json
import re
import sys
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


def consistency_findings(manifest):
    """Checks beyond JSON Schema: uniqueness, reference resolution, versions, capability lists."""
    found = []
    keys = [k for k in manifest.get("keys", []) if isinstance(k, dict)]

    key_ids = [k.get("id") for k in keys]
    for dup in sorted({i for i in key_ids if key_ids.count(i) > 1}, key=str):
        found.append(Finding("E_DUPLICATE_KEY_ID", "error", "keys", f"duplicate key id {dup}"))

    exports = [e for e in manifest.get("exports", []) if isinstance(e, dict)]
    export_ids = [e["id"] for e in exports if "id" in e]
    for dup in sorted({i for i in export_ids if export_ids.count(i) > 1}):
        found.append(Finding("E_DUPLICATE_EXPORT_ID", "error", "exports", f"duplicate export id {dup}"))

    dead_ids = {d.get("id") for d in manifest.get("deadKeys", []) if isinstance(d, dict)}
    for key in keys:
        outputs = list((key.get("levels") or {}).values())
        for group in (key.get("groups") or {}).values():
            outputs.extend(group.values())
        for out in outputs:
            if isinstance(out, dict) and "deadKey" in out and out["deadKey"] not in dead_ids:
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
        major, minor = (int(part) for part in version.split("."))
        if major != SUPPORTED_MAJOR:
            found.append(
                Finding("E_SCHEMA_VERSION_MAJOR", "error", "schemaVersion",
                        f"MAJOR {major} is not supported (this validator reads MAJOR {SUPPORTED_MAJOR})")
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
        missing = sorted(set(required) - set(used if isinstance(used, list) else []))
        if missing:
            found.append(
                Finding("E_EXTENSIONS_REQUIRED", "error", "extensionsRequired",
                        "not listed in extensionsUsed: " + ", ".join(missing))
            )

    for index, value in enumerate(manifest.get("geometry", [])):
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
    for key in manifest.get("keys", []):
        if not isinstance(key, dict):
            continue
        key_id = key.get("id", "?")
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


def analyze(manifest, schema=None, validator=None, strict=False):
    """All findings for one manifest. Returns a list of Finding."""
    schema = schema if schema is not None else load_schema("oklm-manifest.schema.json")
    validator = validator if validator is not None else Draft202012Validator(schema)
    found = schema_findings(manifest, validator)
    found += consistency_findings(manifest)
    found += unknown_member_findings(manifest, schema, strict)
    if strict:
        found += strict_findings(manifest)
        for f in found:
            if f.code == "W_GEOMETRY_UNKNOWN":
                f.severity = "error"
    return found


def main():
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
    for name in args.files:
        path = Path(name)
        try:
            instance = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            findings = [Finding("E_READ", "error", "(file)", f"cannot read as JSON: {exc}")]
        else:
            if args.report:
                findings = schema_findings(instance, validator)
            else:
                findings = analyze(instance, schema, validator, strict=args.strict)
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
