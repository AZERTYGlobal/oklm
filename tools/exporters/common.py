# -*- coding: utf-8 -*-
"""Shared helpers for OKLM exporters (draft v1: LDML, xkb, keylayout).

All exporters are one-way (OKLM -> target). Every export call must produce a
conversion report validating against schemas/oklm-conversion-report.schema.json
(schemaVersion 0.2) -- see CONVERSIONS.md. Nothing here talks to the network
or the filesystem beyond plain read/write of the files it is given.
"""
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMAS = ROOT / "schemas"
VALIDATORS = ROOT / "validators"

if str(VALIDATORS) not in sys.path:
    sys.path.insert(0, str(VALIDATORS))

from validate import load_validator, manifest_consistency_errors  # noqa: E402

GENERATOR_NAME = "oklm-exporters"
GENERATOR_VERSION = "0.1"

# Default functional qualifiers per ISO/IEC 9995 level, used when a manifest
# omits levelSelectors (SPEC.md "Level Selectors"). Levels 5-8 have no
# default: they must be declared explicitly to be exported.
DEFAULT_LEVEL_SELECTORS = {
    "2": ["Level2Shift"],
    "3": ["Level3Shift"],
    "4": ["Level2Shift", "Level3Shift"],
}


class ExportError(Exception):
    """Raised when a manifest cannot be exported at all (compatibilityLevel failed)."""


def load_manifest(path):
    """Load and validate an .oklm.json manifest. Raises ExportError on failure."""
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ExportError(f"cannot read {path} as JSON: {exc}") from exc

    validator = load_validator("oklm-manifest.schema.json")
    problems = [
        f"{'/'.join(str(p) for p in error.path) or '(root)'}: {error.message}"
        for error in sorted(validator.iter_errors(manifest), key=lambda e: list(e.path))
    ]
    if not problems:
        problems = manifest_consistency_errors(manifest)
    if problems:
        raise ExportError(f"{path} is not a valid OKLM manifest: " + "; ".join(problems))
    return manifest


def resolve_level_modifiers(manifest):
    """Map each declared level ("2".."8") to its list of functional qualifiers.

    Level "1" is intentionally absent: it is always the unmodified base level.
    Levels without a default and without an explicit levelSelectors entry are
    left unresolved (absent from the returned dict) -- callers must treat
    that as "unknown modifier combination" and skip/report the level.
    """
    declared = dict(manifest.get("levelSelectors", {}))
    resolved = dict(DEFAULT_LEVEL_SELECTORS)
    resolved.update(declared)
    return resolved


def levels_used_by(manifest):
    """Every level number (as string) referenced by any key's levels object."""
    used = set()
    for key in manifest.get("keys", []):
        used.update(key.get("levels", {}).keys())
    return used


def xml_escape(text):
    """Escape a string for use as XML text or a double-quoted attribute value."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_text(path, text):
    """Write UTF-8 without BOM, LF line endings only."""
    if not text.endswith("\n"):
        text += "\n"
    path.write_bytes(text.encode("utf-8"))


class ReportBuilder:
    """Accumulates one conversion report (schemas/oklm-conversion-report.schema.json)."""

    def __init__(self, direction, source, target):
        self.direction = direction
        self.source = source
        self.target = target
        self.mapped_fields = []
        self.skipped_fields = []  # list of (path, reason)
        self.lossy_mappings = []  # list of (path, detail)
        self.warnings = []
        self.errors = []
        self.round_trip_confidence = None

    def mapped(self, path):
        if path not in self.mapped_fields:
            self.mapped_fields.append(path)

    def skip(self, path, reason):
        self.skipped_fields.append({"path": path, "reason": reason})

    def lossy(self, path, detail):
        self.lossy_mappings.append({"path": path, "detail": detail})

    def warn(self, message):
        self.warnings.append(message)

    def error(self, message):
        self.errors.append(message)

    def compatibility_level(self):
        if self.errors:
            return "failed"
        if self.lossy_mappings:
            return "lossy-mapping"
        if self.skipped_fields:
            return "lossy-metadata"
        return "lossless-core"

    def build(self):
        report = {
            "schemaVersion": "0.2",
            "direction": self.direction,
            "source": self.source,
            "target": self.target,
            "compatibilityLevel": self.compatibility_level(),
            "mappedFields": list(self.mapped_fields),
            "skippedFields": list(self.skipped_fields),
            "lossyMappings": list(self.lossy_mappings),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "generator": {"name": GENERATOR_NAME, "version": GENERATOR_VERSION},
        }
        if self.round_trip_confidence:
            report["roundTripConfidence"] = self.round_trip_confidence
        return report

    def validate_against_schema(self):
        """Self-check: the report this builder produces must validate. Returns
        a list of problems (empty if valid)."""
        validator = load_validator("oklm-conversion-report.schema.json")
        instance = self.build()
        return [
            f"{'/'.join(str(p) for p in error.path) or '(root)'}: {error.message}"
            for error in validator.iter_errors(instance)
        ]


def reject_unsupported_v1_scope(report, manifest):
    """v1 exporters cover keys[].levels only, not keys[].groups (no example
    manifest uses groups; see .internal/plan-exporters-v1.md scope note).
    Returns True and records an error if the manifest is out of scope."""
    keys_with_groups = [key["id"] for key in manifest.get("keys", []) if key.get("groups")]
    if keys_with_groups:
        report.error(
            "keys[].groups is not supported by the v1 exporters (out of scope: no example manifest "
            "uses it): " + ", ".join(keys_with_groups)
        )
        return True
    return False


def skip_oklm_only_metadata(report, manifest):
    """Declare the OKLM-only top-level fields that no v1 exporter maps."""
    for field, reason in (
        ("description", "free-text description, not part of any target's mapping model"),
        ("conformance", "OKLM conformance claims are not expressed by target formats"),
        ("exports", "OKLM export declarations are input to this tooling, not output data"),
        ("metadata", "OKLM metadata envelope (pedagogy, AI, accessibility, links) has no target equivalent"),
        ("extensions", "OKLM extension namespaces are OKLM-specific by definition"),
    ):
        if field in manifest:
            report.skip(field, reason)
