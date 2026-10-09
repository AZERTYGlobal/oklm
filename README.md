# Open Keyboard Layout Model

> A public draft of an open model and manifest format to describe a
> keyboard layout once, in a file a human can read and correct, and export
> it to Unicode LDML Keyboard, operating systems, hardware legends,
> documentation and devices, with an explicit report of what each export
> loses.

## Status

**Draft 0.2, public, in the open.** Not a published or adopted standard.

What exists today:

- a manifest JSON Schema (0.2, open: extensions carry a vendor prefix) and a conversion-report schema (0.2), with a 0.1 to 0.2 migration tool;
- six example manifests: AZERTY Global, the AFNOR NF Z71-300 AZERTY, BÉPO,
  the legacy Windows French AZERTY, US QWERTY, and a minimal teaching
  subset;
- QWERTY Global: a shared chassis plus one diff per language module, composed into one manifest per module (`qwerty-global/`, `tools/qwerty_global.py`);
- a reference validator and a schema test suite;
- an LDML Keyboard 3 importer (`tools/import_ldml.py`, round trip measured) and five one-way exporters with loss reports: LDML Keyboard 3 (keyboard3),
  Linux `xkb_symbols` (with a `.XCompose` companion), macOS `.keylayout`, Windows `.klc`, Stream Deck profile; reference exports
  checked for determinism;
- [oklm.org](https://oklm.org), a demo rendered from the real manifests.

What does not exist yet: an importer for xkb, keylayout or `.klc`, and any
use of OKLM by a project we did not write.

Progress is measured by four gates, not by dates. Gates 1 (gap review
against the reference standards) and 2 (reproducible checks) are passed;
gate 3 (LDML round trip) was measured and passed on 2026-10-05 and merged into
`main` on 2026-10-06; gate 4 (independent use) is open. Details and
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

## Install

Python 3 (tested with 3.13) and `jsonschema` 4 or later (tested with 4.26.0, Draft 2020-12). Nothing else: the tools use the standard library.

```text
pip install -r requirements.txt
```

Run every command from the repository root. The tools take file names, not
patterns. A Unix shell expands `examples/*.oklm.json` before the tool sees
it; Windows PowerShell and `cmd` do not. In PowerShell, replace the pattern with
`(Get-ChildItem examples/*.oklm.json).FullName`, for example:

```text
python validators/validate.py (Get-ChildItem examples/*.oklm.json).FullName
```

The examples below use the Unix form.

## Exporters

`tools/export.py` converts an `.oklm.json` manifest to one of five one-way
targets, each producing a target file plus a conversion report:

```text
python tools/export.py --target TARGET [--out DIR] FILE.oklm.json [FILE ...]
```

`TARGET` is one of `ldml`, `xkb`, `keylayout`, `klc` or `streamdeck`.

- `ldml`: CLDR/UTS #35 Part 7 `keyboard3` XML;
- `xkb`: a standalone `xkb_symbols` block for Linux (levels 1–4), plus a companion `<name>.XCompose` file that carries the dead-key compositions (it must be installed for the dead keys to work);
- `keylayout`: an Apple `.keylayout` file for macOS;
- `klc`: a Microsoft Keyboard Layout Creator source for Windows (never compiled, see CONVERSIONS.md);
- `streamdeck`: an Elgato `.streamDeckProfile` of Text buttons (untested with the Stream Deck software, see CONVERSIONS.md).

Every export writes `<name>.<ext>` and `<name>.<ext>.report.json`, the
latter validating against
[`schemas/oklm-conversion-report.schema.json`](schemas/oklm-conversion-report.schema.json).
Reports declare what was mapped, skipped or approximated; nothing is
silently discarded. The command exits with status 1 when it writes no target
file (a `FAILED` line, which also covers the compatibility level
`unsupported`, for example the plain-ASCII minimal example with
`--target streamdeck`) or when an input cannot be read. [CONVERSIONS.md](CONVERSIONS.md) states the policy and
the known approximations; [CLDR-LDML.md § Known gaps](CLDR-LDML.md#known-gaps-against-ldml-keyboard-482)
lists what the LDML export gets wrong or cannot express today.
`examples/exports/` holds the committed reference exports;
`tools/tests/` checks them for regressions, determinism and schema validity.

## LDML importer

```text
python tools/import_ldml.py [--out DIR] [--license SPDX] [--author NAME] [--layout-id ID] FILE.xml [FILE.xml ...]
```

Reads a CLDR `keyboard3` file and writes `<name>.oklm.json` and
`<name>.import.report.json` (direction `ldml-to-oklm`: mapped fields, what is
preserved as an extension, what is unsupported, enrichment tasks, round-trip
confidence). What the core cannot express goes verbatim into
`extensions.OKLM_ldml`. The CLDR key imports (`keys-Latn-implied`,
`keys-Zyyy-punctuation`, `keys-Zyyy-currency`, release 47, Unicode license) are
bundled in `tools/importers/data/`, so nothing is fetched. Three third-party
CLDR keyboards (`tools/tests/fixtures/ldml/`) and their imports
(`examples/imports/ldml/`) are the reference cases; rules and measured round
trip are in [CONVERSIONS.md](CONVERSIONS.md).

## QWERTY Global

`qwerty-global/` holds a shared US ANSI chassis (`chassis.json`) and one diff
per language module (`modules/`: base, French, Italian). The manifests in
`qwerty-global/manifests/` are generated from them, one per module:

```text
python tools/qwerty_global.py build
python tools/qwerty_global.py check
```

`build` recomposes the manifests from the chassis and the diffs; `check` fails
when a committed manifest differs from a recomposition. `import` (re)computes
the chassis and the diffs from the QWERTY Global project's own source files,
which are not in this repository.

## Checks

```text
python tools/tests/run_all.py
```

runs every check below in one process and exits with status 1 if one of them fails. Separately:

```text
python validators/validate.py examples/*.oklm.json
python validators/validate.py --strict examples/*.oklm.json
python validators/validate_v0_2.py
python tools/tests/run_tests.py
python tools/tests/test_qwerty_global.py
python tools/tests/test_streamdeck.py
python tools/tests/test_klc.py
python tools/tests/test_ldml_import.py
```

`validate.py` validates manifests; with `--report` it validates conversion
reports instead (`python validators/validate.py --report FILE.report.json`).
`--strict` lints what the schema does not: unknown members and extension
prefixes, HID usage ranges, W3C `code` values, one physical code per key; it
turns the warnings `W_UNKNOWN_MEMBER` and `W_GEOMETRY_UNKNOWN` into errors.
`--json` prints the findings with stable codes. Beyond the schema, the
validator refuses duplicated JSON member names, `NaN` and `Infinity`, control
characters in names and outputs, level and group keys out of bounds and
duplicated dead keys (see [SPEC.md](SPEC.md#validation-requirements)).
<!-- TODO-merge: codes -->

`run_tests.py` covers the LDML, xkb (with its `.XCompose` companion) and
keylayout exports of the six examples (18 exports, with their reports). The `.klc` and Stream Deck exports are covered
by `test_klc.py` and `test_streamdeck.py`, and the importer by
`test_ldml_import.py`. `test_qwerty_global.py` skips, and says it skips, the
parity checks against the QWERTY Global source files when it cannot find them.

```text
python tools/migrate_0_1_to_0_2.py [--out DIR] FILE.oklm.json [FILE ...]
```

migrates a 0.1 manifest to 0.2, and only a 0.1 manifest. **Without `--out` it
rewrites the file in place**; with `--out DIR` it writes a copy and keeps the
source. It stops with an error instead of overwriting a value that its changes
would collide with. <!-- TODO-merge: codes -->

## What this is not

Not a new keyboard layout, not a hardware keyboard, not an OS driver, not a
replacement for OS-native layout formats or for LDML Keyboard, not a
commercial product. It is the description layer that generates or
documents those outputs.

## Repository shape

```text
oklm/
├── README.md
├── SPEC.md               manifest specification, draft 0.2
├── CLDR-LDML.md          relationship with LDML Keyboard, reference versions, known gaps
├── CONVERSIONS.md        conversion policy and reports
├── INDUSTRY-ADOPTION.md  who could use this, and in which order we will find out
├── ROADMAP.md            four gates and the ordered work list
├── GOVERNANCE.md         stewardship, decision record, version policy
├── CONTRIBUTING.md       how to propose a change
├── SECURITY.md           how to report a vulnerability
├── CHANGELOG.md          what changed, release by release
├── LICENSE               EUPL 1.2 (code, schemas)
├── LICENSE-CC-BY-4.0     CC BY 4.0 (documentation)
├── requirements.txt      Python dependencies
├── docs/                 oklm.org site (GitHub Pages)
├── examples/             six example manifests
│   ├── exports/          committed reference exports (ldml, xkb with .XCompose, keylayout, klc, streamdeck)
│   └── imports/          three CLDR keyboards imported by tools/import_ldml.py
├── extensions/           PREFIXES.md, the extension prefix registry
├── qwerty-global/        chassis + module diffs, composed into one manifest per module
├── research/             deep-research journal and decisions D1–D44 (French)
├── schemas/              manifest and conversion-report 0.2 JSON Schemas, and a 0.1 design note (historical)
├── tools/                export.py, import_ldml.py, qwerty_global.py, migrate_0_1_to_0_2.py,
│                         exporters/, importers/, tests/
└── validators/           validate.py, validate_v0_2.py (schema test suite), w3c_codes.py
```

## Naming

Public name: OKLM. Full name: Open Keyboard Layout Model. Canonical file
format: OKLM Manifest, usually `.oklm.json`. JSON was chosen for its
tooling and schema validation; an OKLM file must nevertheless stay
hand-maintainable: stable field order, explicit names, shallow structures,
no generator-only encoding.

Domains: `oklm.org` (canonical) and `openkeyboardlayoutmodel.org` (meant to
redirect to it; on 2026-10-09 the redirect worked over plain HTTP only, HTTPS was not configured).

## Licensing

Copyright 2026 the OKLM project and its contributors, stewarded by the AMCF
(see [GOVERNANCE.md](GOVERNANCE.md)).

Dual license by content type. Code, schemas and tooling are licensed under the
EUPL, Version 1.2 ([LICENSE](LICENSE)); the specification and the
documentation are licensed under CC BY 4.0 ([LICENSE-CC-BY-4.0](LICENSE-CC-BY-4.0)).
By path:

| Path | License |
|---|---|
| `*.md` (specification, documentation), except `research/results/` | [CC BY 4.0](LICENSE-CC-BY-4.0) |
| `schemas/*.json`, `validators/`, `tools/` (code and tests), reference exporters and importer | [EUPL 1.2](LICENSE) |
| `docs/index.html` (markup, style and script of oklm.org) | [EUPL 1.2](LICENSE); the text it displays and `docs/llms.txt` are CC BY 4.0 |
| `examples/*.oklm.json`, `qwerty-global/` and `docs/manifests/` (layout data) | the license each manifest declares in its `license` field, which can be `NOASSERTION`; see [examples/README.md](examples/README.md) |
| `examples/exports/` (generated files) | generated from the example manifests: they carry the license status of the manifest they come from |
| `examples/imports/` (imported files) | derived from third-party CLDR keyboards: Unicode License |
| `tools/exporters/data/`, `tools/importers/data/`, `tools/tests/fixtures/ldml/` (data copied from Unicode CLDR) | Unicode License (Unicode, Inc.), text in the `LICENSE-UNICODE` file next to the data; not covered by the EUPL |
| `research/results/` (raw reports of third-party AI research engines, archived as inputs) | not covered by the CC BY 4.0 grant above; the project makes no license claim over them, and the terms of the services that produced them apply |

The oklm.org page loads the Inter and JetBrains Mono fonts from Google Fonts;
they are not distributed in this repository.

Layout data described *with* OKLM keeps its own license, declared in the
manifest's `license` field.

---

*Last updated: 2026-10-10*
