# -*- coding: utf-8 -*-
"""LDML exporter: validity against the CLDR DTD and the audit 2026-10-09 corrections. Exit code 0/1.

    python tools/tests/test_exports_ldml.py

The DTD is a copy of the official ldmlKeyboard3.dtd (CLDR release-48-2, Unicode License, see
fixtures/ldml/LICENSE-UNICODE). It is applied with lxml; without lxml the DTD checks are skipped (said
on the first line of the output) and everything else still runs.
"""
import copy
import sys

from test_exports_support import FIXTURES, check, examples, finish, ldml, minimal, parse_xml

try:
    from lxml import etree
except ImportError:  # the DTD checks need lxml
    etree = None

DTD_FILE = FIXTURES / "ldml" / "ldmlKeyboard3.dtd"


def dtd_problems(text):
    """Validation errors of an LDML document against the official DTD."""
    dtd = etree.DTD(str(DTD_FILE))
    document = etree.fromstring(text.encode("utf-8"))
    return [] if dtd.validate(document) else [str(e) for e in dtd.error_log.filter_from_errors()]


def main():
    if etree is None:
        print("SKIPPED (DTD): lxml is not installed, the LDML DTD validation did not run (pip install lxml)")
    else:
        check(DTD_FILE.exists(), f"missing DTD fixture {DTD_FILE}")
        # the DTD itself must accept the third-party CLDR keyboards (sanity of the validator setup)
        for name in ("fr", "mt47", "ptabnt"):
            text = (FIXTURES / "ldml" / f"{name}.xml").read_text(encoding="utf-8")
            problems = dtd_problems(text)
            check(not problems, f"fixture {name}.xml should be DTD-valid: {problems[:1]}")

    for stem, manifest in examples():
        text, _ = ldml.export(manifest, source_file="x")
        check(parse_xml(text, f"{stem}/ldml") is not None, f"{stem}/ldml: XML parse")
        if etree is not None:
            problems = dtd_problems(text)
            check(not problems, f"{stem}/ldml: not valid against the CLDR DTD: {problems[:1]}")

    # <displays> comes before <keys> (DTD: displays?, keys?), checked without lxml too
    root = parse_xml(ldml.export(minimal(), source_file="x")[0], "minimal/ldml")
    order = [child.tag for child in root]
    check(order.index("displays") < order.index("keys"), f"<displays> must precede <keys>, got {order}")
    return finish("LDML DTD and corrections")


if __name__ == "__main__":
    sys.exit(main())
