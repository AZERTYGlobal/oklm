# Roadmap

OKLM moves by **gates, not dates**. A gate is a verifiable state of the
project; it is either passed, with the evidence named, or open. Work items
have an order and dependencies, never a target month. This replaced the
dated phase plan of June 2026 on 2026-09-15 (see "Retired plan" below).

## Role, first

OKLM is a **bridge and tooling layer**, not a rival to Unicode CLDR/LDML
Keyboard (see [CLDR-LDML.md](CLDR-LDML.md)). Its first users are the two
layouts it was built for: [AZERTY Global](https://azerty.global) and
QWERTY Global. External use is welcome but is not solicited before gate 4:
a format that has not yet served its own authors has nothing to sell.

## The four gates

| Gate | What must be true | State |
|---|---|---|
| **1 — Gap review** | The 0.1 manifest schema has been compared field by field with LDML Keyboard (UTS #35 Part 7, version 48.2), ISO/IEC 9995-1:2026, W3C UI Events `KeyboardEvent.code` (Recommendation, 2025-04-22) and USB HID Usage Tables 1.7, and the gaps are written down. The schema itself stays untouched by the review. | **Passed 2026-09-03.** Findings summarised in [CLDR-LDML.md § Known gaps](CLDR-LDML.md#known-gaps-against-ldml-keyboard-482). ISO/IEC 9995-1:2026 was read from its public preview only (foreword, contents, abstract); the ISO-related findings carry that caveat. |
| **2 — Reproducible checks** | The validator, the schema test suite and the exporter golden tests run green on a clean machine, and the 18 committed reference exports are byte-identical when regenerated. | **Passed 2026-09-02.** `validators/validate_v0_1.py` 15/15, `tools/tests/run_tests.py` 18 deterministic exports matching their goldens, 6 example manifests valid. |
| **3 — Round trip** | An LDML Keyboard → OKLM importer exists, with its own conversion report, and the OKLM → LDML → OKLM round trip is measured on the six example manifests and on at least one third-party CLDR keyboard. | Open. Only the OKLM → LDML direction exists today. |
| **4 — Independent use** | Two implementations or usages of OKLM that this project did not write. | Open. Observed, not planned: nothing on this roadmap produces it directly. |

## Work items, in order

Each item lists what it depends on. None has a date.

1. **Public documents at the bridge role** — this file, `README.md`,
   `SPEC.md`, `GOVERNANCE.md`, `CLDR-LDML.md`, `INDUSTRY-ADOPTION.md` and
   the oklm.org site say the same thing about role, gates and known gaps.
   *Done 2026-09-15.*
2. **AZERTY Global website reads its layout from OKLM** — the manifest
   `azerty-global.oklm.json` becomes the canonical description; the data
   files the website's keyboard component reads are generated from it at
   build time, and the generated files are proven byte-identical to the
   current ones before the switch. Depends on gates 1 and 2.
3. **QWERTY Global manifest** — a shared US ANSI chassis plus local modules
   (French, Italian first). Design question to settle first: modules as
   `groups` inside one manifest (reserved in 0.1, not yet exported by any
   v1 exporter) or as separate manifests sharing the chassis. Depends on
   item 2, whose build chain it reuses.
4. **Schema 0.2** — one revision, not several. Already decided: the
   normative schema opens (`additionalProperties` no longer `false`
   everywhere) and the `--strict` validator mode (in the validator since
   2026-09-15) takes over the rejection of unknown members; extension namespaces take the prefixes `OKLM_`, `EXT_`
   and `<VENDOR>_` with a public prefix registry; three capability arrays at
   the root (`featuresRequired`, `extensionsRequired`, and their optional
   counterpart) replace any `minVersion`; `metadata` stays the only
   free-form envelope. The revision also absorbs the gate 1 findings and
   what items 2 and 3 taught about real use. Depends on gate 1 and items
   2 and 3.
5. **Stream Deck profile export** — characters and shortcuts of a layout as
   an Elgato `.streamDeckProfile`, with a conversion report. First
   potential consumer outside an operating system. Depends on item 4.
6. **Windows `.klc` export** — completes the OS trio (LDML, xkb, keylayout
   already exist); the output must compile in MSKLC. Depends on item 4.
7. **LDML Keyboard importer** — `ldml-to-oklm` with its report; round trip
   measured. This is gate 3. Depends on item 4.

What is deliberately **not** on this list: a kalamine bridge, a firmware
(QMK/ZMK) exporter, dynamic-legend device profiles other than Stream Deck,
and a "candidate standard" release. They may come back once gate 4 is
passed and a second author has a say.

## Research still feeding the schema

Sixteen deep-research prompts were written in June 2026 to survey the
ecosystem (formats, OS pipelines, dynamic keys, standards). Six are
triangulated across three engines and consigned as decisions D1–D44 in
[`research/`](research/); ten remain, to be run in blocks before schema 0.2.
The journal is in French.

## Retired plan

The roadmap published from June to September 2026 had five dated phases
(product framing in June 2026, draft schema after the AZERTY Global
release, dynamic legends in the second half of 2026, OS and AI-key
integration in late 2026, QWERTY Global modules in 2027, candidate standard
2027+). Phases 0 and 1 happened; the dates of the rest were wishes. They
are replaced by the gates above and are kept in the git history only.

---

*Last updated: 2026-09-15*
