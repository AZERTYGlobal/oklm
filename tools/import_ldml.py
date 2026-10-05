# -*- coding: utf-8 -*-
"""OKLM importer CLI (draft): LDML Keyboard 3 -> OKLM.

Writes `<name>.oklm.json` and `<name>.import.report.json` (CONVERSIONS.md "LDML to OKLM"). The manifest is
checked against the manifest schema (strict validator) and the report against the report schema before
anything is written; a failure prints the problems and writes only the report.

Usage:
    python tools/import_ldml.py [--out DIR] [--license SPDX] [--author NAME ...] [--layout-id ID] FILE.xml [FILE.xml ...]

Dependency: pip install jsonschema (>= 4.x, Draft 2020-12)
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "validators"))

from importers import ldml  # noqa: E402
from exporters.common import write_text  # noqa: E402
from validate import analyze, load_schema, load_validator  # noqa: E402


def check_outputs(manifest, report):
    problems = []
    for finding in analyze(manifest, load_schema("oklm-manifest.schema.json"), strict=True):
        if finding.severity == "error":
            problems.append(f"manifest {finding.code} {finding.path}: {finding.message}")
    validator = load_validator("oklm-conversion-report.schema.json")
    for error in validator.iter_errors(report):
        problems.append(f"report {'/'.join(str(p) for p in error.path) or '(root)'}: {error.message}")
    return problems


def main():
    parser = argparse.ArgumentParser(description="Import LDML Keyboard 3 files into OKLM manifests.")
    parser.add_argument("files", nargs="+", metavar="FILE")
    parser.add_argument("--out", metavar="DIR", help="output directory (default: next to each input file)")
    parser.add_argument("--license", help="SPDX license of the layout data (default NOASSERTION)")
    parser.add_argument("--author", action="append", help="layout author (repeatable; default: info@author)")
    parser.add_argument("--layout-id", help="layoutId (default: the -t-k0- tail of the locale, else a slug of the name)")
    args = parser.parse_args()

    exit_code = 0
    for name in args.files:
        path = Path(name)
        out_dir = Path(args.out) if args.out else path.parent
        base = path.name.split(".")[0] if path.name.endswith(".ldml.xml") else path.stem
        manifest_path = out_dir / f"{base}.oklm.json"
        report_path = out_dir / f"{base}.import.report.json"
        try:
            data = path.read_bytes()
        except OSError as exc:
            print(f"ERROR {path}: {exc}")
            exit_code = 1
            continue
        manifest, report = ldml.import_ldml(data, source_file=path.name, license=args.license,
                                            authors=args.author, layout_id=args.layout_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        if manifest is not None:
            report["target"]["file"] = manifest_path.name
            problems = check_outputs(manifest, report)
            if problems:
                print(f"ERROR {path}: the import does not validate")
                for problem in problems:
                    print(f"  - {problem}")
                exit_code = 1
                manifest = None
        if manifest is None:
            write_text(report_path, json.dumps(report, indent=2, ensure_ascii=False))
            print(f"FAILED  {path} -> {report_path} (compatibilityLevel: {report['compatibilityLevel']})")
            for error in report["errors"]:
                print(f"  - {error}")
            exit_code = 1
            continue
        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
        write_text(report_path, json.dumps(report, indent=2, ensure_ascii=False))
        print(f"OK      {path} -> {manifest_path} ({report['compatibilityLevel']}, round trip {report['roundTripConfidence']}, "
              f"{len(manifest['keys'])} keys, {len(manifest.get('deadKeys', []))} dead keys, "
              f"{len(report['preservedAsExtensions'])} preserved, {len(report['unsupportedConstructs'])} unsupported)")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
