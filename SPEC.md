# Open Keyboard Layout Model - Draft Specification

## Version

Draft 0.2 (2026-10-05). It supersedes the frozen 0.1 and is the only revision planned before 1.0; the structural choices and the order of work are in [ROADMAP.md](ROADMAP.md). `schemaVersion` is `MAJOR.MINOR` (`0.2`). A reader MUST refuse a MAJOR it does not know and SHOULD read a higher MINOR as valid but unsupported (it warns, it does not fail).

**Conventions.** The key words MUST, MUST NOT, SHOULD and SHOULD NOT are to be interpreted as described in BCP 14 ([RFC 2119](https://www.rfc-editor.org/rfc/rfc2119), [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174)) when, and only when, they appear in all capitals. They are used only for rules that a tool can check or that a reader or exporter can be tested against. Lowercase "must" and "should" are plain prose, and a statement marked "(strict)" is checked only by `validators/validate.py --strict`.

**Reading rule (D31).** The schema is open: no object forbids additional members. A reader MUST ignore members it does not know, MUST NOT rewrite them, and MUST keep `extensions` blocks intact. Members whose name looks like a vendor prefix (`OKLM_x`, `EXT_x`, `ABC_x`) are valid only inside `extensions`; anywhere else the schema rejects them (D34, D38). An unknown member without prefix is a warning in the validator, and an error under `--strict`.

Normative machine-readable definitions live in [`schemas/oklm-manifest.schema.json`](schemas/oklm-manifest.schema.json) and [`schemas/oklm-conversion-report.schema.json`](schemas/oklm-conversion-report.schema.json). This document explains the model; when prose and schema disagree, the schema wins for draft 0.2. Rules that JSON Schema cannot express (uniqueness, references, bounds, duplicate member names) are checked by the validator and listed under [Validation Requirements](#validation-requirements).

OKLM is a bridge and tooling layer around Unicode CLDR/LDML Keyboard, not a competing interchange format. The 0.1 schema was compared field by field with LDML Keyboard 48.2, ISO/IEC 9995-1:2026, W3C `KeyboardEvent.code` (2025) and USB HID Usage Tables 1.7 on 2026-09-03; schema 0.2 absorbed most of the findings, and the gaps that remain are listed in [CLDR-LDML.md](CLDR-LDML.md#known-gaps-against-ldml-keyboard-482). Where this document below notes an ISO/IEC 9995-1:2026 statement, it relies on the standard's public preview (foreword and contents), not on its clause text.

Design decisions referenced as D1..D44 are recorded, with their evidence, in the research journal [`research/Décisions de conception — deep research.md`](research/Décisions%20de%20conception%20—%20deep%20research.md) (in French). This document does not depend on the journal to be read: each rule is stated here.

## Design Goals

1. Represent classic keyboard layouts without losing OS-specific details.
2. Support ANSI and ISO physical geometries first.
3. Support static and dynamic legends.
4. Support dead keys and composition.
5. Support exports to OS files, web tools and dynamic-key devices.
6. Map cleanly to existing standards where possible, especially Unicode CLDR/LDML Keyboard and ISO/IEC 9995.
7. Stay readable, correctable and versionable by humans without proprietary generators.
8. Stay deterministic enough for automated validation.

## Human-Maintainable By Design

An OKLM manifest is meant to be practical to review and edit by hand. These are design rules; the validator checks none of them unless a later section says so.

- Canonical files use the `.oklm.json` extension.
- Field order SHOULD be stable: follow the property order of the manifest schema. This is not checked.
- Field names are explicit.
- Common mappings use compact notation (a plain string is a literal text output).
- Verbose notation is reserved for keys that need richer semantics (dead keys, modifiers).
- Physical key ids are stable and human-recognizable.
- Generated files do not rewrite unrelated sections unnecessarily.
- No proprietary generator is needed to understand or correct a manifest. This is a design goal, not a testable requirement.

Non-goal:

- make every file tiny. Readability and diff quality matter more than minimizing bytes.

## Non-Goals

- Define a new USB HID standard.
- Replace Windows, macOS, Linux or XKB formats.
- Replace Unicode CLDR/LDML Keyboard.
- Require cloud services.
- Require AI features.
- Require dynamic keyboards.

## Terminology

OKLM uses the ISO/IEC 9995 vocabulary of levels, groups and key numbers (D14), but not every term below comes from the standard:

- **Level**: shift state within a group. Level 1 is the unshifted state, level 2 is Level2Shift (commonly "Shift"), level 3 is Level3Shift (commonly "AltGr"), level 4 combines levels 2 and 3. The foreword of the public preview of ISO/IEC 9995-1:2026 says that labelling covers up to four levels and that level 4 is allowed, albeit not recommended. **Levels 5-8 are an OKLM extension beyond ISO**, kept in the core for layouts that condition extra levels on CapsLock (AZERTY Global, AFNOR, BÉPO): level 5 is level 1 with CapsLock, 6 is level 2 with CapsLock, 7 is level 3 with CapsLock, 8 is level 4 with CapsLock.
- **Group**: a complete alternative keymap on the same physical keys (e.g. a second script). Groups are a distinct axis from levels (D3) and are reserved in 0.2 (see Key).
- **Key number**: canonical physical key position per ISO/IEC 9995-1 (e.g. `D01`, `C00`, `B00`, `E01`).

The terms `layers` and `shift states` are not part of the model. The schema does not list a `layers` property (it is open), but the validator rejects a manifest that uses one. <!-- TODO-merge: codes -->

## Core Objects

### Manifest

Top-level object describing one layout. The project is the model; this file-level object is the manifest.

Required fields:

- `schemaVersion`
- `layoutId`
- `name`
- `version`
- `license`
- `authors`
- `locales`
- `geometry`
- `keys`

Optional fields: `description`, `levelSelectors`, `deadKeys`, `conformance`, `exports`, `metadata`, `extensions`, `extensionsUsed`, `extensionsRequired`, `featuresRequired`.

`version` is a SemVer string; a free-text label such as `2019 NF Z71-300` goes in `metadata.versionLabel`. `extensionsUsed` lists the extension namespaces the file uses, `extensionsRequired` the subset a reader must understand to use the file correctly, `featuresRequired` the core features it needs; the three are root arrays and may be empty. A reader that does not know a namespace of `extensionsRequired` MUST refuse the file. <!-- TODO-merge: codes --> `featuresRequired` has no registry of feature names in 0.2: the validator accepts any identifier, and a reader that does not know one should report the file as valid but unsupported.

`extensions` is accepted on the root object, on `levelSelectors`, on `metadata`, on a key, on a dead key, on an output written as an object, on a `conformance` claim and on an export target. It does not exist on `levels`, `groups`, `compositions` or on an output written as a plain string.

### Locales

BCP 47 language tags this layout is designed for (e.g. `fr`, `fr-FR`). The first entry is the primary locale.

### Geometry

Target physical geometries, declared as aliases (D5): a form factor family, a dash and a size.

Families the validator knows:

- `iso`: ISO keyboards (with the extra key B00 left of Z);
- `ansi`: ANSI keyboards, also written `us`;
- `jis`: Japanese keyboards;
- `abnt`: Brazilian keyboards, also written `abnt2`;
- `ks`: Korean keyboards;
- `touch`: touch keyboards;
- `custom`: a physical form that is none of the above; the manifest says nothing more about it.

Common values: `ansi-60`, `ansi-75`, `ansi-tkl`, `ansi-full`, `iso-75`, `iso-tkl`, `iso-full`, `touch`, `custom`; the `jis`, `abnt` and `ks` families follow the same `family-size` pattern. The size after the dash (`60`, `75`, `tkl`, `full`) is a free label: nothing checks it, and nothing checks that `geometry` agrees with the keys. The validator checks only the family; an unknown family is a warning, and an error under `--strict`. `geometry` is not a closed enum (D33) so that a file written for a later MINOR stays valid.

Geometry tells consumers which physical keys exist; it is informative. Exporters do not read it: the LDML exporter derives the physical form from the keys the manifest actually covers. Canonical key positions remain ISO/IEC 9995-1 key numbers regardless of geometry. A drawable geometry layer (absolute x/y/w/h coordinates, rotation, variants — D23-D30) is not part of the 0.2 core; the `OKLM_geometry` namespace is reserved for it.

### Key

Describes a graphic key of the alphanumeric section, or a modifier key that selects its levels.

Fields:

- `id`: canonical physical key identifier, an ISO/IEC 9995-1 key number (D1) — e.g. `D01` (QWERTY Q position), `B00` (ISO extra key). ISO/IEC 9995-1 is the de jure position standard used by national layout norms. The schema accepts the rows `A` to `E` with two digits (`^[A-E][0-9]{2}$`); the rows of the standard beyond `E` are frame keys, out of the core (see below).
- `hid`: mandatory USB HID Usage ID from keyboard usage page 0x07, as a hex string (D1) — the unambiguous machine anchor (e.g. the ABNT Ro key `0x87` is not the ISO B00 key `0x64`). (strict) `hid` lies in `04`-`E7`.
- `xkb`: optional XKB key name alias for Linux export (e.g. `AD01`, `LSGT`, `SPCE`).
- `code`: optional W3C UI Events `KeyboardEvent.code` cross-reference (D24) — e.g. `KeyQ`, `IntlBackslash`. (strict) `code` is one of the values of the W3C Recommendation, and no two keys carry the same `code`.
- `name`: optional human-readable label for documentation.
- `levels`: outputs by level, 1 to 8 (see Output below). A level with no output is omitted. A missing level 1-4 means the key produces nothing there. A missing level 5-8 (a CapsLock level) takes the output of the matching level without CapsLock (5 from 1, 6 from 2, 7 from 3, 8 from 4); exporters apply this when they write a level, and a reader that looks up an output applies it too. LDML Keyboard expresses the silent level differently (a keystroke with no matching layer is ignored, unless a layer `other` exists), and the LDML exporter emits LDML's implicit `gap` key at that position; see the known gaps in [CLDR-LDML.md](CLDR-LDML.md#known-gaps-against-ldml-keyboard-482). <!-- TODO-merge: codes -->
- `role`: `"key"` (the default: a graphic key described by `levels`) or `"modifier"` (a functional modifier key).
- `modifier`: the function a key with `"role": "modifier"` provides, one of `Level2Shift`, `Level3Shift`, `Level5Shift`, `CapsLock`, `NumLock` and `GroupSelect`. A modifier key SHOULD NOT carry `levels`. A key needs `levels` or a `role`. <!-- TODO-merge: codes --> `GroupSelect` names the key that would switch groups; since `groups` is reserved, no exporter gives it any effect. Like every modifier key it produces no output, and exporters skip it and declare the skip in their report.
- `groups`: **reserved**. The field is still accepted by the schema, but every exporter rejects a manifest that uses it (`compatibilityLevel` `failed`). No consumer reads it before 1.0.
- `categories`: optional semantic tags (e.g. `letter`, `digit`, `punctuation`, `french`).

Level keys are the digits `1` to `8` and group keys the digits `2` to `9`; the validator refuses any other key, in `levels` and in `groups`. <!-- TODO-merge: codes -->

Physical placement fields (`row`, `column`, `width`) are not part of the core Key object: drawable geometry is deferred to the `OKLM_geometry` namespace (D23).

Frame keys — function row, navigation, numpad, media, `Fn`, anything outside HID usage page 0x07 — are out of the LDML-aligned core and belong to the reserved `OKLM_frameKeys` namespace (D11).

### Level Selectors

Optional declaration of how levels 2-8 are selected, by functional qualifier name (D2): `Level2Shift`, `Level3Shift`, `Level5Shift`, `CapsLock`, `NumLock`. These are OKLM names. They were chosen for ISO/IEC 9995 levels 2 and 3 (and `Level5Shift`, `CapsLock` and `NumLock` have no ISO counterpart: ISO stops at four levels, and the numeric section is out of the LDML-aligned core); the exact qualifier names of ISO/IEC 9995 were not read, because the clauses are not public. Modifiers are named by function, never by the physical key that activates them. Platform bindings (AltGr vs Ctrl+Alt, macOS Option) are export concerns; on LDML export only `Level2Shift`, `Level3Shift` and `CapsLock` have a modifier component (`shift`, `altR`, `caps`), and a level that needs `Level5Shift` or `NumLock` is skipped and reported.

Defaults when omitted: level 2 = `[Level2Shift]`, level 3 = `[Level3Shift]`, level 4 = `[Level2Shift, Level3Shift]`. Levels 5-8 have no default selector: a level 5-8 that no `levelSelectors` entry resolves is accepted by the validator but skipped, with a report entry, by the exporters. Declare its selector to export it.

### Output

What a key produces at one (group, level).

Forms:

- compact: a plain string is a literal text output (one or more codepoints, covering ligatures);
- `{ "deadKey": id }`: emits the dead-key marker for a dead key defined in `deadKeys`;
- `{ "modifier": name }`: 0.1 form, removed in 0.2. A modifier key is now declared by `role` and `modifier` on the key (see Key); exporters skip it and declare the skip in the report.

Outputs are exported exactly as written: OKLM applies no Unicode normalization to them. LDML Keyboard normalizes the output of a keyboard and matches transforms on decomposed text, so an LDML consumer may recompose an output that OKLM wrote decomposed. The LDML export does not express this difference, and the report declares it as a loss. <!-- TODO-merge: codes -->

### Dead Key

Dead-key composition tables live in the top-level `deadKeys` array, separate from the key mapping (D4). Each dead key is isomorphic to an LDML Keyboard 3.0 marker plus simple transforms (D7): pressing the key outputs the marker `\m{id}`; each composition entry compiles to one transform rule (`\m{id}` + base → output). Dead-key ids MUST be unique. <!-- TODO-merge: codes -->

Fields:

- `id`: identifier; compiles to the LDML marker `\m{id}`.
- `name`: optional human-readable name.
- `display`: optional standalone character shown while the dead key is pending (e.g. `ˆ`).
- `compositions`: base input string → output string. Document order is the rule order. The base is a literal string, not a pattern. Note for LDML export: LDML's `transform@from` is a regex-like pattern, so the exporter escapes the metacharacters of the base and the `$` of the output (see [CONVERSIONS.md](CONVERSIONS.md#rules-settled-in-schema-02)).
- `fallback`: optional text emitted in place of the pending marker when no composition matches. It is an explicit transform on the bare marker, not a cancellation behavior.

Cancellation behavior (Escape, unrelated key, focus change) differs across platforms; exporters MUST document their mapping of `fallback` and cancellation (D4).

### Conformance Declaration

A manifest may claim conformance to normative references through the `conformance` array (D13). A global "ISO 9995 compliant" claim is invalid: each claim names one reference with edition (e.g. `ISO/IEC 9995-1:2026`, `AFNOR NF Z71-300:2019`) and states its scope. Partial conformance is allowed and must be scoped. ISO/IEC 9995-1:2026 (fourth edition, 2026-01-16) cancels and replaces ISO/IEC 9995-1:2009; the example manifests claim the 2026 edition for the key reference grid only, and say that the 2026 text itself was not read.

LDML alignment is not an ISO conformance claim; it is declared separately on the LDML export target (`exports[].options.conformsTo`, a whole number from 45 to 48). The range is the one the LDML Keyboard DTD of CLDR 48.2 accepts (see [CONVERSIONS.md](CONVERSIONS.md#ldml-conformsto)). <!-- TODO-merge: codes -->

### Export Target

Declared export targets (e.g. `ldml-keyboard-3`, `web-tester`, `xkb`, `windows-klc`, `macos-keylayout`, `keymap-image`). Export ids MUST be unique. Target-specific `options` are free-form in 0.2, except `conformsTo` on the LDML target (see above); per-exporter option schemas may come later.

### Metadata Envelope

The `metadata` object carries value that LDML does not cover: description, links, dynamic legends, training/pedagogy, accessibility annotations, scoped assistant metadata (D8). It is stripped on LDML export but preserved for non-OS consumers. Inner structure of these blocks is non-normative in 0.2. Four members have a fixed meaning:

- `versionLabel`: the human label of a version when `version` is SemVer;
- `attribution`: an object crediting the layout and stating its provenance;
- `layoutPattern`: the name of the layout family or pattern (`azerty`, `qwerty`, `bépo`), for documentation;
- `indicator`: the short language-bar indicator text, for example `FR`.

LDML has matching `info` attributes (`attribution`, `layout`, `indicator`), but the exporter does not write them yet: these members stay in OKLM.

Assistant metadata exists to answer deterministic typing questions ("How do I type É?", "Where is the em dash?"). It is designed not to require keylogging and not to embed predictive models; that is a design goal, not a testable requirement.

### Extensions

Namespaced extension blocks for data outside the LDML-aligned core, allowed on the objects listed under [Manifest](#manifest). Keys of `extensions` follow `^(OKLM|EXT|[A-Z][A-Z0-9]*)_[A-Za-z0-9]+$` (registry and rules: [`extensions/PREFIXES.md`](extensions/PREFIXES.md)); a name without prefix, such as `frame-keys` or `ldml`, is rejected by the schema. Namespaces that the project reserves, contents intentionally unspecified in 0.2:

- `OKLM_frameKeys` (D11): function/navigation/numpad/media/Fn keys, HID pages beyond 0x07;
- `OKLM_firmware` (D10): physical matrix / QMK-ZMK bindings — scope arbitration pending;
- `OKLM_geometry` (D23-D30): drawable absolute geometry;
- `OKLM_ldml`: LDML constructs preserved during LDML → OKLM conversion (written by `tools/import_ldml.py`).

Exporters never write `extensions` into the target format: the block and the `extensionsUsed` list are declared as skipped in the report. Extensions nested inside other objects (on a key or a dead key) are skipped too.

## Example

The [`examples/`](examples/) directory contains six manifests that validate against the manifest schema — complete descriptions of AZERTY Global, the AFNOR NF Z71-300 AZERTY, BÉPO, the legacy Windows French AZERTY and the US QWERTY baseline (see [`examples/README.md`](examples/README.md) for provenance and licenses), plus [`examples/azerty-global-minimal.oklm.json`](examples/azerty-global-minimal.oklm.json) — a minimal, hand-written subset: ISO 9995-1 key ids with mandatory `hid` and optional `xkb`/`code` aliases, `(group, level)` outputs in compact notation, two dead keys, a scoped conformance claim and two export targets.

## Validation Requirements

A valid manifest MUST:

- validate against `schemas/oklm-manifest.schema.json`;
- use unique key ids;
- use unique export ids;
- use unique dead-key ids;
- define every dead-key id referenced from key outputs;
- declare a license;
- declare at least one locale and one target geometry;
- carry a `schemaVersion` of MAJOR 0 and a SemVer `version`;
- list every `extensionsRequired` entry in `extensionsUsed`;
- use level keys `1` to `8` and group keys `2` to `9` only;
- contain no member name written twice in the same JSON object, no `NaN` or `Infinity`, and no control character in a name or in an output.

The validator refuses a manifest that breaks any of these rules, and a manifest that uses `layers`. <!-- TODO-merge: codes -->

Rules marked (strict) are enforced only under `--strict`: `hid` lies in `04`-`E7`, `code` is one of the W3C values, and no two keys carry the same `code`. Under `--strict` an unknown member (`W_UNKNOWN_MEMBER`) and a geometry family the validator does not know (`W_GEOMETRY_UNKNOWN`) become errors. `geometry` is not a closed enum (D33): the validator checks the family, with `us` read as `ansi` and `abnt2` as `abnt`.

Uniqueness and reference resolution are checked by validators beyond JSON Schema. [`validators/validate.py`](validators/validate.py) validates any manifest or conversion report from the command line; [`validators/validate_v0_2.py`](validators/validate_v0_2.py) is the schema test suite (a positive and a negative fixture per rule, plus the migration). [`tools/migrate_0_1_to_0_2.py`](tools/migrate_0_1_to_0_2.py) migrates a 0.1 manifest and only a 0.1 manifest; it stops with an error instead of overwriting a value that its changes would collide with. <!-- TODO-merge: codes --> The whole test set runs with `python tools/tests/run_all.py`.

## Export Requirements

An exporter MUST document:

- supported schema versions;
- relationship to CLDR/LDML Keyboard when relevant;
- supported geometry types;
- unsupported fields;
- output format;
- whether its output is deterministic (same input, same bytes);
- test fixtures.

## Conversion Requirements

OKLM tooling includes bidirectional conversion with LDML Keyboard:

```text
OKLM -> LDML Keyboard
LDML Keyboard -> OKLM
```

Every conversion MUST produce a machine-readable report validating against [`schemas/oklm-conversion-report.schema.json`](schemas/oklm-conversion-report.schema.json), describing:

- exported or imported fields;
- skipped fields;
- lossy mappings;
- warnings;
- errors;
- compatibility level.

See `CONVERSIONS.md` for the conversion policy.

---

*Last updated: 2026-10-10*
