# -*- coding: utf-8 -*-
"""OKLM exporter CLI (draft v1): OKLM -> LDML Keyboard 3 / xkb / keylayout.

One-way exports only (see CONVERSIONS.md "Other export targets"). Every
export writes a target file plus a conversion report validating against
schemas/oklm-conversion-report.schema.json. If the manifest cannot be
exported at all (compatibilityLevel "failed"), only the report is written.

Usage:
    python tools/export.py --target ldml|xkb|keylayout [--out DIR] FILE [FILE ...]

Dependency: pip install jsonschema (>= 4.x, Draft 2020-12)
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "validators"))

from exporters import ldml, xkb, keylayout  # noqa: E402
from exporters.common import ExportError, load_manifest, write_text  # noqa: E402
from validate import load_validator  # noqa: E402

EXPORTERS = {
    "ldml": (ldml, "ldml.xml"),
    "xkb": (xkb, "xkb"),
    "keylayout": (keylayout, "keylayout"),
}


def main():
    parser = argparse.ArgumentParser(description="Export OKLM manifests to LDML/xkb/keylayout.")
    parser.add_argument("files", nargs="+", metavar="FILE")
    parser.add_argument("--target", required=True, choices=sorted(EXPORTERS))
    parser.add_argument("--out", metavar="DIR", help="output directory (default: next to each input file)")
    args = parser.parse_args()

    module, extension = EXPORTERS[args.target]
    report_validator = load_validator("oklm-conversion-report.schema.json")

    exit_code = 0
    for name in args.files:
        path = Path(name)
        base = path.name
        if base.endswith(".oklm.json"):
            base = base[: -len(".oklm.json")]
        out_dir = Path(args.out) if args.out else path.parent
        target_path = out_dir / f"{base}.{extension}"
        report_path = out_dir / f"{base}.{extension}.report.json"

        try:
            manifest = load_manifest(path)
        except ExportError as exc:
            print(f"ERROR {path}: {exc}")
            exit_code = 1
            continue

        text, report = module.export(manifest, source_file=path.name)

        problems = [
            f"{'/'.join(str(p) for p in error.path) or '(root)'}: {error.message}"
            for error in report_validator.iter_errors(report)
        ]
        if problems:
            print(f"ERROR {path}: generated report does not validate against the conversion report schema")
            for problem in problems:
                print(f"  - {problem}")
            exit_code = 1
            continue

        write_text(report_path, json.dumps(report, indent=2, ensure_ascii=False))

        if text is None:
            print(f"FAILED  {path} -> {report_path} (compatibilityLevel: {report['compatibilityLevel']})")
            for error in report["errors"]:
                print(f"  - {error}")
            exit_code = 1
            continue

        write_text(target_path, text)
        print(f"OK      {path} -> {target_path}, {report_path} (compatibilityLevel: {report['compatibilityLevel']})")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
