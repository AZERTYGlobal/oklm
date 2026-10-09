# -*- coding: utf-8 -*-
"""OKLM exporter CLI (draft v1): OKLM -> LDML Keyboard 3 / xkb / keylayout / .klc / Stream Deck.

One-way exports only (see CONVERSIONS.md "Other export targets"). Every
export writes a target file plus a conversion report validating against
schemas/oklm-conversion-report.schema.json. If the manifest cannot be
exported at all (compatibilityLevel "failed"), only the report is written. A valid manifest that
has nothing the target can carry (compatibilityLevel "unsupported", e.g. a layout with only ASCII
letters for Stream Deck) writes its report too and is not a failure.

--out DIR is created when it does not exist. Exit code: 0 when every file was exported or is
unsupported, 1 when one failed, 2 when the output directory cannot be created.

Usage:
    python tools/export.py --target ldml|xkb|keylayout|streamdeck|klc [--out DIR] FILE [FILE ...]

Dependency: pip install jsonschema (>= 4.x, Draft 2020-12)
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "validators"))

from exporters import ldml, xkb, keylayout, streamdeck, klc  # noqa: E402
from exporters.common import ExportError, load_manifest, write_text  # noqa: E402
from validate import load_validator  # noqa: E402

EXPORTERS = {
    "ldml": (ldml, "ldml.xml"),
    "xkb": (xkb, "xkb"),
    "keylayout": (keylayout, "keylayout"),
    "streamdeck": (streamdeck, "streamDeckProfile"),
    "klc": (klc, "klc"),
}


def main():
    parser = argparse.ArgumentParser(description="Export OKLM manifests to LDML, xkb, keylayout, .klc or a Stream Deck profile.")
    parser.add_argument("files", nargs="+", metavar="FILE")
    parser.add_argument("--target", required=True, choices=sorted(EXPORTERS))
    parser.add_argument("--out", metavar="DIR", help="output directory (default: next to each input file)")
    args = parser.parse_args()

    module, extension = EXPORTERS[args.target]
    report_validator = load_validator("oklm-conversion-report.schema.json")

    if args.out:
        try:
            Path(args.out).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            print(f"ERROR cannot use the output directory {args.out}: {exc}")
            return 2

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

        try:
            text, report = module.export(manifest, source_file=path.name)
        except (ExportError, ValueError) as exc:
            print(f"ERROR {path}: {exc}")
            exit_code = 1
            continue

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

        try:
            write_text(report_path, json.dumps(report, indent=2, ensure_ascii=False))
        except OSError as exc:
            print(f"ERROR {path}: cannot write {report_path}: {exc}")
            exit_code = 1
            continue

        if text is None:
            if report["compatibilityLevel"] == "unsupported":
                print(f"UNSUPPORTED {path} -> {report_path}: nothing the target can carry (not an error)")
                for warning in report["warnings"]:
                    print(f"  - {warning}")
                continue
            print(f"FAILED  {path} -> {report_path} (compatibilityLevel: {report['compatibilityLevel']})")
            for error in report["errors"]:
                print(f"  - {error}")
            exit_code = 1
            continue

        extra = ""
        try:
            if isinstance(text, bytes):
                target_path.write_bytes(text)
            else:
                write_text(target_path, text)
            if hasattr(module, "export_compose"):
                compose_path = out_dir / f"{base}.XCompose"
                write_text(compose_path, module.export_compose(manifest, source_file=path.name))
                extra = f", {compose_path}"
        except (OSError, ExportError, ValueError) as exc:
            print(f"ERROR {path}: {exc}")
            exit_code = 1
            continue
        print(f"OK      {path} -> {target_path}, {report_path}{extra} (compatibilityLevel: {report['compatibilityLevel']})")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
