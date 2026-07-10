# Open Keyboard Layout Model - Draft Specification

## Version

Draft 0.1.

Normative machine-readable definitions live in [`schemas/oklm-manifest.schema.json`](schemas/oklm-manifest.schema.json) and [`schemas/oklm-conversion-report.schema.json`](schemas/oklm-conversion-report.schema.json). This document explains the model; when prose and schema disagree, the schema wins for draft 0.1.

Design decisions referenced as D1..D30 are recorded in [`research/Décisions de conception — deep research.md`](research/Décisions%20de%20conception%20—%20deep%20research.md).

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

An OKLM manifest must be practical to review and edit by hand.

Requirements:

- canonical files use `.oklm.json`;
- field order should be stable (follow the property order of the manifest schema);
- field names should be explicit;
- common mappings should use compact notation (a plain string is a literal text output);
- verbose notation should be reserved for keys that need richer semantics (dead keys, modifiers);
- physical key ids should be stable and human-recognizable;
- generated files should not rewrite unrelated sections unnecessarily;
- proprietary generators must never be required to understand or correct a manifest.

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

OKLM uses ISO/IEC 9995 terminology verbatim (D14):

- **Level**: shift state within a group. Level 1 is the unshifted state, level 2 is Level2Shift (commonly "Shift"), level 3 is Level3Shift (commonly "AltGr"), level 4 combines levels 2 and 3. Levels 5-8 are optional.
- **Group**: a complete alternative keymap on the same physical keys (e.g. a second script). Groups are a distinct axis from levels (D3).
- **Key number**: canonical physical key position per ISO/IEC 9995-1 (e.g. `D01`, `C00`, `B00`, `E01`).

The terms `layers` and `shift states` are not part of the model; a manifest using a `layers` property is rejected by the schema.

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

Optional fields: `description`, `levelSelectors`, `deadKeys`, `conformance`, `exports`, `metadata`, `extensions`.

### Locales

BCP 47 language tags this layout is designed for (e.g. `fr`, `fr-FR`). The first entry is the primary locale.

### Geometry

Target physical geometries, declared as aliases (D5): form factor family plus size.

Common values:

- `ansi-60`
- `ansi-75`
- `ansi-tkl`
- `ansi-full`
- `iso-75`
- `iso-tkl`
- `iso-full`
- `custom`

Geometry tells consumers which physical keys exist. Canonical key positions remain ISO/IEC 9995-1 key numbers regardless of geometry. A drawable geometry layer (absolute x/y/w/h coordinates, rotation, variants — D23-D30) is intentionally not part of core 0.1; the `extensions.geometry` namespace is reserved for it.

### Key

Describes a graphic key of the alphanumeric section.

Fields:

- `id`: canonical physical key identifier, an ISO/IEC 9995-1 key number (D1) — e.g. `D01` (QWERTY Q position), `B00` (ISO extra key). ISO/IEC 9995-1 is the de jure position standard used by national layout norms.
- `hid`: mandatory USB HID Usage ID from keyboard usage page 0x07, as a hex string (D1) — the unambiguous machine anchor (e.g. the ABNT Ro key `0x87` is not the ISO B00 key `0x64`).
- `xkb`: optional XKB key name alias for Linux export (e.g. `AD01`, `LSGT`, `SPCE`).
- `code`: optional W3C UI Events `KeyboardEvent.code` cross-reference (D24) — e.g. `KeyQ`, `IntlBackslash`.
- `name`: optional human-readable label for documentation.
- `levels`: outputs by ISO level for group 1 (see Output below). A level with no output is omitted.
- `groups`: optional additional ISO groups, starting at `"2"` (group 1 is `levels`).
- `categories`: optional semantic tags (e.g. `letter`, `digit`, `punctuation`, `french`).

Physical placement fields (`row`, `column`, `width`) are not part of the core Key object: drawable geometry is deferred to the `extensions.geometry` namespace (D23).

Frame keys — function row, navigation, numpad, media, `Fn`, anything outside HID usage page 0x07 — are out of the LDML-aligned core and belong to the reserved `extensions.frame-keys` namespace (D11).

### Level Selectors

Optional declaration of how levels 2-8 are selected, using ISO/IEC 9995 functional qualifier names (D2): `Level2Shift`, `Level3Shift`, `Level5Shift`, `CapsLock`, `NumLock`. Modifiers are named by function, never by the physical key that activates them. Platform bindings (AltGr vs Ctrl+Alt, macOS Option) are export concerns.

Defaults when omitted: level 2 = `[Level2Shift]`, level 3 = `[Level3Shift]`, level 4 = `[Level2Shift, Level3Shift]`.

### Output

What a key produces at one (group, level).

Forms:

- compact: a plain string is a literal text output (one or more codepoints, covering ligatures);
- `{ "deadKey": id }`: emits the dead-key marker for a dead key defined in `deadKeys`;
- `{ "modifier": name }`: declares a functional modifier key (named by function, D2).

### Dead Key

Dead-key composition tables live in the top-level `deadKeys` array, separate from the key mapping (D4). Each dead key is isomorphic to an LDML Keyboard 3.0 marker plus simple transforms (D7): pressing the key outputs the marker `\m{id}`; each composition entry compiles to one transform rule (`\m{id}` + base → output).

Fields:

- `id`: identifier; compiles to the LDML marker `\m{id}`.
- `name`: optional human-readable name.
- `display`: optional standalone character shown while the dead key is pending (e.g. `ˆ`).
- `compositions`: base input string → output string. Document order is the rule order.
- `fallback`: optional text emitted in place of the pending marker when no composition matches.

Cancellation behavior (Escape, unrelated key, focus change) differs across platforms; exporters must document their mapping of `fallback` and cancellation (D4).

### Conformance Declaration

A manifest may claim conformance to normative references through the `conformance` array (D13). A global "ISO 9995 compliant" claim is invalid: each claim names one reference with edition (e.g. `ISO/IEC 9995-1:2026`, `AFNOR NF Z71-300:2019`) and states its scope. Partial conformance is allowed and must be scoped.

LDML alignment is not an ISO conformance claim; it is declared separately on the LDML export target (`exports[].options.conformsTo`, a whole number ≥ 45 per UTS #35 Part 7).

### Export Target

Declared export targets (e.g. `ldml-keyboard-3`, `web-tester`, `xkb`, `windows-klc`, `macos-keylayout`, `keymap-image`). Export ids must be unique. Target-specific `options` are free-form in 0.1; per-exporter option schemas will come with the exporter research prompts.

### Metadata Envelope

The `metadata` object carries value that LDML does not cover (D8): description, links, dynamic legends, training/pedagogy, accessibility annotations, scoped assistant metadata. It is stripped on LDML export but preserved for non-OS consumers. Inner structure of these blocks is non-normative in 0.1.

Assistant metadata exists to answer deterministic typing questions ("How do I type É?", "Where is the em dash?"). It must not require keylogging and must not embed predictive models.

### Extensions

Namespaced extension blocks for data outside the LDML-aligned core. Reserved namespaces, contents intentionally unspecified in 0.1:

- `frame-keys` (D11): function/navigation/numpad/media/Fn keys, HID pages beyond 0x07;
- `firmware` (D10): physical matrix / QMK-ZMK bindings — scope arbitration pending;
- `geometry` (D23-D30): drawable absolute geometry;
- `ldml`: LDML constructs preserved during LDML → OKLM conversion.

## Example

See [`examples/azerty-global-minimal.oklm.json`](examples/azerty-global-minimal.oklm.json) — a minimal, hand-written AZERTY Global subset that validates against the manifest schema: ISO 9995-1 key ids with mandatory `hid` and optional `xkb`/`code` aliases, `(group, level)` outputs in compact notation, two dead keys, a scoped conformance claim and two export targets.

## Validation Requirements

A valid manifest must:

- validate against `schemas/oklm-manifest.schema.json`;
- use unique key ids;
- use unique export ids;
- define every dead-key id referenced from key outputs;
- declare a license;
- declare at least one locale and one target geometry.

Uniqueness and reference resolution are checked by validators beyond JSON Schema. [`validators/validate.py`](validators/validate.py) validates any manifest or conversion report from the command line; [`validators/validate_v0_1.py`](validators/validate_v0_1.py) is the schema test suite.

## Export Requirements

An exporter must document:

- supported schema versions;
- relationship to CLDR/LDML Keyboard when relevant;
- supported geometry types;
- unsupported fields;
- output format;
- deterministic behavior;
- test fixtures.

## Conversion Requirements

OKLM tooling should include bidirectional conversion with LDML Keyboard:

```text
OKLM -> LDML Keyboard
LDML Keyboard -> OKLM
```

Every conversion must produce a machine-readable report validating against [`schemas/oklm-conversion-report.schema.json`](schemas/oklm-conversion-report.schema.json), describing:

- exported or imported fields;
- skipped fields;
- lossy mappings;
- warnings;
- errors;
- compatibility level.

See `CONVERSIONS.md` for the conversion policy.

---

*Last updated: 2026-07-10*
