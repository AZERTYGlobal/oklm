# -*- coding: utf-8 -*-
"""OKLM validator CLI (draft 0.1).

Validate one or more OKLM files against the draft 0.1 JSON Schemas, plus the
consistency checks that JSON Schema cannot express (unique key ids, unique
export ids, dead-key reference resolution).

Usage:
    python validators/validate.py FILE [FILE ...]
    python validators/validate.py --report FILE [FILE ...]

Files are treated as OKLM manifests (.oklm.json) by default; pass --report to
validate conversion reports instead. Exit code 0 if every file is valid, 1
otherwise.

Dependency: pip install jsonschema  (>= 4.x, Draft 2020-12)
"""
import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMAS = Path(__file__).resolve().parent.parent / "schemas"


def load_validator(name):
    schema = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


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


def main():
    parser = argparse.ArgumentParser(description="Validate OKLM 0.1 files.")
    parser.add_argument("files", nargs="+", metavar="FILE")
    parser.add_argument(
        "--report",
        action="store_true",
        help="validate conversion reports instead of manifests",
    )
    args = parser.parse_args()

    if args.report:
        validator = load_validator("oklm-conversion-report.schema.json")
    else:
        validator = load_validator("oklm-manifest.schema.json")

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

        if problems:
            exit_code = 1
            print(f"INVALID {path}")
            for problem in problems:
                print(f"  - {problem}")
        else:
            print(f"VALID   {path}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
