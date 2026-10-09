# -*- coding: utf-8 -*-
"""LDML exporter: validity against the CLDR DTD and the audit 2026-10-09 corrections. Exit code 0/1.

    python tools/tests/test_exports_ldml.py

The DTD is a copy of the official ldmlKeyboard3.dtd (CLDR release-48-2, Unicode License, see
fixtures/ldml/LICENSE-UNICODE). It is applied with lxml; without lxml the DTD checks are skipped (said
on the first line of the output) and everything else still runs.
"""
import re
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

    # C-02: the derived locale is a valid RFC 6497 t-extension (field = tkey 1*("-" 3*8alphanum))
    tfield = re.compile(r"^[a-z][0-9](-[a-z0-9]{3,8})+$")
    for stem, manifest in examples():
        locale = ldml.derived_locale(manifest)[0]
        check(tfield.match(locale.split("-t-", 1)[1]) is not None, f"{stem}: derived locale '{locale}' is not RFC 6497")
    for layout_id, expected in (("qwerty-us", "qwertyus"), ("us", "usx"), ("a-b-cdef", "abcdef"), ("ab-cdefghijkl", "abcdefgh"),
                                ("azerty-global-minimal", "azerty-global-minimal"), ("abcdefghijk-xy", "abcdefgh")):
        subtags, changes = ldml.locale_subtags(layout_id)
        check("-".join(subtags) == expected, f"locale_subtags({layout_id!r}) gave {subtags}, expected {expected}")
        check(all(3 <= len(t) <= 8 for t in subtags), f"locale_subtags({layout_id!r}): subtag length out of 3-8")
        check(bool(changes) == (expected != layout_id), f"locale_subtags({layout_id!r}): changes {changes}")

    # C-04: the slash is escaped in a transform `from`; C-03: fallback = marker + (.) after the compositions
    manifest = minimal()
    circumflex = next(d for d in manifest["deadKeys"] if d["id"] == "circumflex")
    circumflex["compositions"]["/"] = "\u2044"
    text, _ = ldml.export(manifest, source_file="x")
    froms = [t.get("from") for t in parse_xml(text, "slash/ldml").iter("transform")]
    check("\\m{circumflex}\\u{2F}" in froms and "\\m{circumflex}/" not in froms, f"C-04: slash base escaped in from, got {froms[:12]}")
    mine = [f for f in froms if f.startswith("\\m{circumflex}")]
    check(mine and mine[-1] == "\\m{circumflex}(.)" and mine.count("\\m{circumflex}(.)") == 1, "C-03: the fallback rule comes last for its marker")
    check("\\m{circumflex}" not in froms, "C-03: no rule on the bare marker")
    check(any(t.get("to") == "^$1" for t in parse_xml(text, "fallback/ldml").iter("transform")), "C-03: fallback keeps the typed character ($1)")
    if etree is not None:
        problems = dtd_problems(text)
        check(not problems, f"slash/fallback manifest: LDML not valid against the DTD: {problems[:1]}")
    # the importer reads that rule back as the dead key fallback
    from importers import ldml as importer
    imported, _ = importer.import_ldml(text.encode("utf-8"), source_file="x.ldml.xml")
    dead = {d["id"]: d for d in imported["deadKeys"]}
    check(dead["circumflex"].get("fallback") == "^" and dead["diaeresis"].get("fallback") == "\u00a8", "C-03: re-import gives the fallback back")

    # <displays> comes before <keys> (DTD: displays?, keys?), checked without lxml too
    root = parse_xml(ldml.export(minimal(), source_file="x")[0], "minimal/ldml")
    order = [child.tag for child in root]
    check(order.index("displays") < order.index("keys"), f"<displays> must precede <keys>, got {order}")
    return finish("LDML DTD and corrections")


if __name__ == "__main__":
    sys.exit(main())
