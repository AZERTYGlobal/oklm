# -*- coding: utf-8 -*-
"""OKLM validator CLI (draft 0.1).

Validate one or more OKLM files against the draft 0.1 JSON Schemas, plus the
consistency checks that JSON Schema cannot express (unique key ids, unique
export ids, dead-key reference resolution).

Usage:
    python validators/validate.py FILE [FILE ...]
    python validators/validate.py --strict FILE [FILE ...]
    python validators/validate.py --report FILE [FILE ...]

Files are treated as OKLM manifests (.oklm.json) by default; pass --report to
validate conversion reports instead. Exit code 0 if every file is valid, 1
otherwise.

--strict (decision of 2026-09-02, prerequisite of schema 0.2) adds the lint
that the schema does not carry:
  - unknown members are errors everywhere, including members that carry an
    extension prefix (OKLM_, EXT_, <VENDOR>_); without --strict an unknown
    member is accepted when it carries such a prefix, which is what the open
    0.2 schema will rely on;
  - `hid` must be a physical usage of the HUT 1.7 keyboard/keypad page:
    0x00-0x03 are non-physical (ErrorRollOver, POSTFail, ErrorUndefined) and
    0xE8-0xFFFF are reserved;
  - `code`, when present, must be one of the KeyboardEvent.code values of the
    W3C Recommendation of 2025-04-22 (validators/w3c_codes.py), and one code
    names one key only (there is only one `Backslash`).

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

# Decision 20 of 2026-09-02 (D34): extension namespaces are prefixed OKLM_,
# EXT_ or <VENDOR>_ (an upper-case vendor token).
EXTENSION_PREFIX = re.compile(r"^(OKLM_|EXT_|[A-Z][A-Z0-9]+_)")

HID_PHYSICAL_MIN = 0x04
HID_PHYSICAL_MAX = 0xE7

HINTS = {
    "layers": "OKLM has no `layers`; outputs live in keys[].levels (D2, D14)",
}


def load_schema(name):
    schema = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def load_validator(name):
    return Draft202012Validator(load_schema(name))


def manifest_consistency_errors(manifest):
    """Checks beyond JSON Schema: uniqueness and reference resolution."""
    errors = []

    key_ids = [k.get("id") for k in manifest.get("keys", [])]
    dupes = sorted({i for i in key_ids if key_ids.count(i) > 1})
    if dupes:
        errors.append("duplicate key ids: " + ", ".join(dupes))

    export_ids = [e["id"] for e in manifest.get("exports", []) if "id" in e]
    dupes = sorted({i for i in export_ids if export_ids.count(i) > 1})
    if dupes:
        errors.append("duplicate export ids: " + ", ".join(dupes))

    dead_ids = {d.get("id") for d in manifest.get("deadKeys", [])}
    for key in manifest.get("keys", []):
        outputs = list(key.get("levels", {}).values())
        for group in key.get("groups", {}).values():
            outputs.extend(group.values())
        for out in outputs:
            if isinstance(out, dict) and "deadKey" in out and out["deadKey"] not in dead_ids:
                errors.append(
                    f"key {key.get('id')}: dead key '{out['deadKey']}' is not defined in deadKeys"
                )

    return errors


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


def unknown_member_errors(instance, schema, strict, path=None, root=None, errors=None):
    """Walk an instance alongside its schema and report members the schema does not declare.

    An object that declares no `properties` and no `patternProperties` is free-form
    (metadata blocks, extension payloads) and is not walked. Elsewhere an undeclared
    member is an error, unless strict is False and the member carries an extension
    prefix (OKLM_, EXT_, <VENDOR>_).
    """
    root = schema if root is None else root
    path = [] if path is None else path
    errors = [] if errors is None else errors
    schema = _resolve(schema, root)
    if not isinstance(schema, dict):
        return errors

    alternatives = schema.get("oneOf", []) + schema.get("anyOf", [])
    if alternatives:
        for alt in alternatives:
            alt = _resolve(alt, root)
            if not _type_matches(instance, alt):
                continue
            if isinstance(instance, dict) and not set(alt.get("required", [])) <= set(instance):
                continue
            unknown_member_errors(instance, alt, strict, path, root, errors)
        return errors
    for alt in schema.get("allOf", []):
        unknown_member_errors(instance, alt, strict, path, root, errors)

    if isinstance(instance, list):
        items = schema.get("items")
        if isinstance(items, dict):
            for index, value in enumerate(instance):
                unknown_member_errors(value, items, strict, path + [str(index)], root, errors)
        return errors

    if not isinstance(instance, dict):
        return errors

    properties = schema.get("properties", {})
    patterns = schema.get("patternProperties", {})
    extra = schema.get("additionalProperties", True)
    if not properties and not patterns and not isinstance(extra, dict):
        return errors  # free-form object

    for name, value in instance.items():
        here = path + [name]
        if name in properties:
            unknown_member_errors(value, properties[name], strict, here, root, errors)
            continue
        matched = [sub for pattern, sub in patterns.items() if re.search(pattern, name)]
        if matched:
            for sub in matched:
                unknown_member_errors(value, sub, strict, here, root, errors)
            continue
        if isinstance(extra, dict):
            unknown_member_errors(value, extra, strict, here, root, errors)
            continue
        if not strict and EXTENSION_PREFIX.match(name):
            continue
        where = "/".join(path) or "(root)"
        message = f"{where}: unknown member '{name}'"
        if name in HINTS:
            message += f" ({HINTS[name]})"
        elif not strict:
            message += " (extensions carry an OKLM_, EXT_ or <VENDOR>_ prefix)"
        errors.append(message)
    return errors


def strict_lint_errors(manifest, schema, strict=True):
    """The --strict lint: unknown members, HID usage ranges, W3C code values, one code per key.

    With strict=False only the unknown-member walk runs, with extension prefixes accepted.
    """
    errors = list(unknown_member_errors(manifest, schema, strict))
    if not strict:
        return errors

    codes_seen = {}
    for key in manifest.get("keys", []):
        if not isinstance(key, dict):
            continue
        key_id = key.get("id", "?")
        hid = key.get("hid")
        if isinstance(hid, str) and re.fullmatch(r"0x[0-9A-Fa-f]{2,4}", hid):
            usage = int(hid, 16)
            if usage < HID_PHYSICAL_MIN:
                errors.append(
                    f"strict: key {key_id}: hid {hid} is a non-physical usage "
                    "(0x00-0x03: ErrorRollOver, POSTFail, ErrorUndefined)"
                )
            elif usage > HID_PHYSICAL_MAX:
                errors.append(
                    f"strict: key {key_id}: hid {hid} is reserved in the HUT 1.7 keyboard/keypad page "
                    "(0xE8-0xFFFF)"
                )
        code = key.get("code")
        if isinstance(code, str):
            if code not in W3C_CODES:
                errors.append(
                    f"strict: key {key_id}: code '{code}' is not a KeyboardEvent.code value "
                    "of the W3C Recommendation (2025-04-22)"
                )
            codes_seen.setdefault(code, []).append(key_id)
    for code, key_ids in sorted(codes_seen.items()):
        if len(key_ids) > 1:
            errors.append(
                f"strict: code '{code}' is used by keys {', '.join(key_ids)}: "
                "one code names one physical key"
            )
    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate OKLM 0.1 files.")
    parser.add_argument("files", nargs="+", metavar="FILE")
    parser.add_argument(
        "--report",
        action="store_true",
        help="validate conversion reports instead of manifests",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="manifests only: reject every unknown member (prefixed extensions included), "
        "non-physical or reserved HID usages, unknown W3C code values and duplicated codes",
    )
    args = parser.parse_args()

    if args.report:
        schema = load_schema("oklm-conversion-report.schema.json")
    else:
        schema = load_schema("oklm-manifest.schema.json")
    validator = Draft202012Validator(schema)

    exit_code = 0
    for name in args.files:
        path = Path(name)
        try:
            instance = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"ERROR {path}: cannot read as JSON: {exc}")
            exit_code = 1
            continue

        problems = [
            f"{'/'.join(str(p) for p in error.path) or '(root)'}: {error.message}"
            for error in sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
        ]
        if not args.report and not problems:
            problems = manifest_consistency_errors(instance)
            problems += strict_lint_errors(instance, schema, strict=args.strict)

        if problems:
            exit_code = 1
            print(f"INVALID {path}")
            for problem in problems:
                print(f"  - {problem}")
        else:
            print(f"VALID   {path}" + (" (strict)" if args.strict and not args.report else ""))

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
