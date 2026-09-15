# Open Keyboard Layout Model

> A public draft of an open model and manifest format to describe a
> keyboard layout once, in a file a human can read and correct, and export
> it to Unicode LDML Keyboard, operating systems, hardware legends,
> documentation and devices, with an explicit report of what each export
> loses.

## Status

**Draft 0.1, public, in the open.** Not a published or adopted standard.

What exists today:

- a manifest JSON Schema (0.1) and a conversion-report schema (0.2);
- six example manifests: AZERTY Global, the AFNOR NF Z71-300 AZERTY, BÉPO,
  the legacy Windows French AZERTY, US QWERTY, and a minimal teaching
  subset;
- a reference validator and a schema test suite;
- three one-way exporters with loss reports: LDML Keyboard 3 (keyboard3),
  Linux `xkb_symbols`, macOS `.keylayout`; 18 committed reference exports
  checked for determinism;
- [oklm.org](https://oklm.org), a demo rendered from the real manifests.

What does not exist yet: any importer, the Windows `.klc` export, any
device profile export, and any use of OKLM by a project we did not write.

Progress is measured by four gates, not by dates. Gates 1 (gap review
against the reference standards) and 2 (reproducible checks) are passed;
gates 3 (LDML round trip) and 4 (independent use) are open. Details and
the ordered work list: [ROADMAP.md](ROADMAP.md).

## Role: a bridge, used first by its authors

OKLM is a **bridge and tooling layer**. It does not compete with Unicode
CLDR/LDML Keyboard, the vendor-neutral interchange format for keyboard
mapping data; it exports to it. Where LDML represents a concept cleanly,
OKLM maps to it rather than inventing a parallel one. Where LDML is not
focused (dynamic legends, learning and accessibility metadata, assistant
knowledge, device exports), OKLM adds a layer above and strips it on LDML
export. The boundary, the reference versions and the known gaps are in
[CLDR-LDML.md](CLDR-LDML.md).

Its first users are the two layouts it was built for, [AZERTY
Global](https://azerty.global) and QWERTY Global. The next work item makes
the AZERTY Global website read its layout data from the OKLM manifest. A
format that has not yet served its own authors has nothing to offer other
authors; external adoption is welcome, and is observed at gate 4 rather than
solicited before it.

## Why

Keyboard layouts are still distributed as OS-specific files, images,
installers, firmware assumptions or informal documentation. A layout
project that ships on Windows, macOS, Linux and a website maintains the
same mapping four or five times and discovers divergences by hand.

One description, exported everywhere, is the ordinary answer, and kalamine
and kbdgen already export one description to several operating systems.
OKLM's bet is on the pieces they leave out: a source file written for
humans first, ISO/IEC 9995 positions plus USB HID usages as the machine
anchor, an LDML Keyboard export, and a conversion report that says exactly
what each export did not preserve.

## Core idea

A keyboard layout should be both a documented typing system for humans and
structured data for software.

> An OKLM file must be readable, correctable and versionable by a human
> without a proprietary generator.

The manifest describes physical keys anchored on ISO/IEC 9995-1 positions
and USB HID usages; outputs per ISO level (levels 5–8 as an OKLM
extension); dead keys and their compositions; scoped conformance claims;
declared export targets; and a free-form `metadata` envelope for what LDML
does not cover. The specification is [SPEC.md](SPEC.md); the schema wins
when prose and schema disagree.

## Exporters

`tools/export.py` converts an `.oklm.json` manifest to one of three one-way
targets, each producing a target file plus a conversion report:

```text
python tools/export.py --target ldml|xkb|keylayout FILE.oklm.json [FILE ...]
```

- `ldml`: CLDR/UTS #35 Part 7 `keyboard3` XML;
- `xkb`: a standalone `xkb_symbols` block for Linux (levels 1–4);
- `keylayout`: an Apple `.keylayout` file for macOS.

Every export writes `<name>.<ext>` and `<name>.<ext>.report.json`, the
latter validating against
[`schemas/oklm-conversion-report.schema.json`](schemas/oklm-conversion-report.schema.json).
Reports declare what was mapped, skipped or approximated; nothing is
silently discarded. [CONVERSIONS.md](CONVERSIONS.md) states the policy and
the known approximations; [CLDR-LDML.md § Known gaps](CLDR-LDML.md#known-gaps-against-ldml-keyboard-482)
lists what the LDML export gets wrong or cannot express today.
`examples/exports/` holds the committed reference exports;
`tools/tests/run_tests.py` checks them for regressions, determinism and
schema validity.

## Checks

```text
python validators/validate.py examples/*.oklm.json
python validators/validate_v0_1.py
python tools/tests/run_tests.py
```

All three ran green on a clean machine on 2026-09-02 (gate 2). They need
Python 3 and `jsonschema`.

## What this is not

Not a new keyboard layout, not a hardware keyboard, not an OS driver, not a
replacement for OS-native layout formats or for LDML Keyboard, not a
commercial product. It is the description layer that generates or
documents those outputs.

## Repository shape

```text
oklm/
├── README.md
├── SPEC.md               manifest specification, draft 0.1
├── CLDR-LDML.md          relationship with LDML Keyboard, reference versions, known gaps
├── CONVERSIONS.md        conversion policy and reports
├── INDUSTRY-ADOPTION.md  who could use this, and in which order we will find out
├── ROADMAP.md            four gates and the ordered work list
├── GOVERNANCE.md         stewardship, decision record, version policy
├── docs/                 oklm.org site (GitHub Pages)
├── examples/             six example manifests
│   └── exports/          committed reference exports (ldml/xkb/keylayout)
├── research/             deep-research journal and decisions D1–D44 (French)
├── schemas/              manifest 0.1 and conversion-report 0.2 JSON Schemas
├── tools/                export.py, exporters/, tests/
└── validators/           reference validation scripts
```

## Naming

Public name: OKLM. Full name: Open Keyboard Layout Model. Canonical file
format: OKLM Manifest, usually `.oklm.json`. JSON was chosen for its
tooling and schema validation; an OKLM file must nevertheless stay
hand-maintainable: stable field order, explicit names, shallow structures,
no generator-only encoding.

Domains: `oklm.org` (canonical) and `openkeyboardlayoutmodel.org`
(redirects to it).

## Licensing

Dual license by content type:

- specification and documentation (`*.md`): [CC BY 4.0](LICENSE-CC-BY-4.0);
- schemas, validators, tooling and reference exporters: [EUPL 1.2](LICENSE).

Layout data described *with* OKLM keeps its own license, declared in the
manifest's `license` field.

---

*Last updated: 2026-09-15*
