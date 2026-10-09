# -*- coding: utf-8 -*-
"""Shared helpers of the test_exports_*.py scripts (not a test itself).

Plain assertions, no pytest: each test script collects its failures with `check`, then calls `finish`.
"""
import copy
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "validators"))

from exporters import klc, keylayout, ldml, streamdeck, xkb  # noqa: E402,F401
from exporters.common import load_manifest  # noqa: E402,F401
from validate import load_validator  # noqa: E402,F401

EXAMPLES = sorted((ROOT / "examples").glob("*.oklm.json"))
FIXTURES = ROOT / "tools" / "tests" / "fixtures"
failures, counter = [], {"n": 0}
_report_validator = None


def check(condition, message):
    counter["n"] += 1
    if not condition:
        failures.append(message)


def stem_of(path):
    return path.name[: -len(".oklm.json")]


def examples():
    """(stem, manifest) of the six example manifests."""
    return [(stem_of(path), load_manifest(path)) for path in EXAMPLES]


def minimal():
    return copy.deepcopy(load_manifest(ROOT / "examples" / "azerty-global-minimal.oklm.json"))


def report_errors(report):
    global _report_validator
    if _report_validator is None:
        _report_validator = load_validator("oklm-conversion-report.schema.json")
    return [error.message for error in _report_validator.iter_errors(report)]


def parse_xml(text, label):
    """Parse an XML export; record a failure (and return None) when it is not well formed."""
    try:
        root = ET.fromstring(text.encode("utf-8") if isinstance(text, str) else text)
    except ET.ParseError as exc:
        check(False, f"{label}: XML not well formed: {exc}")
        return None
    for element in root.iter():  # drop the namespace: tests look elements up by local name
        if isinstance(element.tag, str) and element.tag.startswith("{"):
            element.tag = element.tag.split("}", 1)[1]
    return root


def finish(title):
    if failures:
        print(f"FAILED {title} ({len(failures)} problem(s) over {counter['n']} checks):")
        for message in failures[:40]:
            print("  -", message)
        return 1
    print(f"OK: {title}, {counter['n']} checks passed, 0 failed.")
    return 0
