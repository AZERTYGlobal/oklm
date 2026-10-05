# OKLM / LDML Conversions

## Goal

OKLM must support conversion in both directions:

```text
OKLM -> LDML Keyboard
LDML Keyboard -> OKLM
```

The conversions do not have the same guarantees.

Both directions must produce a machine-readable report validating against [`schemas/oklm-conversion-report.schema.json`](schemas/oklm-conversion-report.schema.json).

OKLM is broader than LDML Keyboard because it can include product, pedagogy, dynamic legend, assistant and export metadata. Therefore, an OKLM to LDML conversion may lose OKLM-only information.

LDML Keyboard is a standard interchange format with its own concepts and constraints. Therefore, an LDML to OKLM conversion should preserve keyboard mapping semantics first, then represent unknown or unsupported data explicitly.

## Conversion Principles

1. Never silently discard information.
2. Always produce a conversion report.
3. Preserve keyboard mapping semantics before metadata.
4. Mark OKLM-only fields as non-LDML-exportable.
5. Preserve unsupported LDML data in an extension block when possible.
6. Make round-trip expectations explicit.
7. Keep generated files deterministic.
8. Preserve human-readable ordering and formatting where possible.

## Rules settled in schema 0.2

Decided on 2026-10-05 with schema 0.2; the exporters and the report schema follow them.

- **E8, groups.** `keys[].groups` stays reserved. Every exporter rejects a manifest that uses it and reports `compatibilityLevel: failed`.
- **E13, escaping.** A composition base is a literal string. In LDML `transform@from`, the backslash, the 14 regex metacharacters (`\ ^ $ . | ? * + ( ) [ ] { }`), the characters of categories Cc, Cf, Cs, Co, Cn, Mn, Mc, Me, Zl, Zp and every non-ASCII space are written `\u{..}`. In `transform@to` and in key outputs the same rule applies, plus `$`, which is escaped in `to`.
- **E19, extensions.** `extensions` and `extensionsUsed` are never exported; the report lists them in `skippedFields`. Extensions found by an importer are preserved in a namespace and listed in `preservedAsExtensions`.
- **E20, derived LDML locale.** The `keyboard@locale` is `<locales[0]>-t-k0-<layoutId>`. Each subtag after `k0` is cut to 8 characters; a cut is declared in `lossyMappings` (`layoutId`).
- **E21, silent level.** A level without output is a key that produces nothing. LDML gets an implicit `gap` at that position; the schema cannot express a layer `other`.
- **E1, scan codes.** When the keys cover exactly one of the CLDR implied forms (`us`, `iso`, `abnt2`, `jis`, `ks`, table `scanCodes-implied.xml` bundled in `tools/exporters/data/` with the Unicode license), the exporter uses that form and writes no custom `<form>`. Otherwise it writes a custom form.
- **E15, fallback.** `fallback` is exported as a transform on the bare marker. It is not a lossy mapping.
- **E22, modifier keys.** A key with `role: "modifier"` is skipped by the exporters and declared in `skippedFields`.
- **D33, `unsupported`.** The compatibility level `unsupported` means the source is valid but uses a construct that the converter does not handle at all and nothing usable came out. It differs from `failed`, which means the source or the conversion is broken.

## OKLM to LDML

Purpose:

- produce a standards-oriented interchange file;
- improve credibility and interoperability;
- allow future CLDR/LDML tooling to consume the layout mapping.

Expected preserved data:

- layout identity where compatible;
- locales;
- physical or virtual key mapping;
- (group, level) mappings and functional modifiers where compatible;
- dead keys (markers and simple transforms) where compatible;
- display labels where compatible;
- character outputs.

Expected lossy or non-exported data:

- dynamic legend device profiles;
- Stream Deck-style actions;
- sticker/keycap production metadata;
- learning metadata;
- "how to type" prose;
- assistant knowledge;
- companion-app commands;
- marketing or positioning metadata;
- comparison data;
- exporter-specific settings for non-LDML targets.

Required output:

```text
layout.ldml.xml
layout.ldml.report.json
```

The report must include:

- schema versions;
- exported fields;
- skipped fields;
- lossy mappings;
- warnings;
- errors;
- round-trip confidence.

## LDML to OKLM

Purpose:

- import existing LDML Keyboard files;
- make OKLM useful beyond AZERTY Global and QWERTY Global;
- help layout authors and vendors enrich existing LDML data with OKLM-specific metadata.

Expected preserved data:

- identity and locales;
- key definitions;
- groups and levels;
- transforms;
- display labels;
- character outputs;
- LDML metadata where mapped.

Expected added OKLM defaults:

- empty dynamic legend metadata;
- empty assistant metadata;
- empty training metadata;
- default export target list;
- default validation profile.

Required output:

```text
layout.oklm.json
layout.import.report.json
```

The import report must include:

- LDML version;
- OKLM schema version;
- mapped fields;
- fields preserved as extensions;
- unsupported constructs;
- warnings;
- errors;
- suggested enrichment tasks.

## Round-Trip Policy

### OKLM -> LDML -> OKLM

This is expected to preserve core keyboard mapping semantics, but not OKLM-only metadata.

Loss must be reported.

### LDML -> OKLM -> LDML

This should preserve LDML-compatible mapping semantics as closely as possible.

If OKLM enriches the file with non-LDML metadata, that metadata should not affect the regenerated LDML output unless explicitly mapped.

## Other Export Targets

Beyond the bidirectional LDML conversion above, OKLM v1 ships two additional
**one-way** exporters: `OKLM -> xkb` and `OKLM -> keylayout` (macOS). Unlike
LDML, import from xkb or Apple keylayout files back into OKLM is out of
scope for v1.

Both exporters follow the same reporting discipline as LDML: every export
produces a `*.report.json` validating against
[`schemas/oklm-conversion-report.schema.json`](schemas/oklm-conversion-report.schema.json)
(directions `oklm-to-xkb` and `oklm-to-keylayout`, schema 0.2), and nothing
is silently discarded.

Known, explicitly reported approximations:

- only ISO/IEC 9995 levels 1-4 export to xkb (standard key types support at
  most four shift levels per key); levels 5-8 (CapsLock-conditioned) are
  handled by the X server via key type and locale rules, not per-key
  declarations, and are always skipped. LDML and keylayout can export levels
  5-8 when `levelSelectors` resolves them to a combination of
  Level2Shift/Level3Shift/CapsLock;
- Level3Shift exports as xkb/LDML `altR` or macOS `anyOption`; the actual
  physical binding (AltGr vs Ctrl+Alt vs macOS Option) stays platform-specific;
- OKLM `deadKeys[].compositions` are not re-emitted as XCompose rules for
  xkb: dead keys map to `dead_*` keysyms where one exists, and the actual
  composition result is delegated to the system's own Compose
  configuration, which may differ from the OKLM table. macOS keylayout, by
  contrast, encodes the full composition table natively via its
  `<actions>`/`<terminators>` state machine;
- the exporters run from `tools/export.py` (see `tools/exporters/`) and are
  covered by golden-file tests in `examples/exports/` (`tools/tests/run_tests.py`).

See `tools/exporters/ldml.py`, `tools/exporters/xkb.py` and
`tools/exporters/keylayout.py` for the full, current list of scope notes and
approximations (kept in the module docstring, next to the code it documents).

### Stream Deck profile (`oklm-to-streamdeck`)

`python tools/export.py --target streamdeck FILE.oklm.json` writes a
`.streamDeckProfile` (zip) of Elgato "Text" buttons: one per distinct
character the layout types, except ASCII letters, digits and space, on a
Stream Deck XL grid (8 x 4, 32 buttons per page). It is a reminder and a
fallback for rarely used symbols, not a layout installer.

- Always reported as `lossy-mapping` with `roundTripConfidence: low`: key
  ids, levels, modifiers, dead-key sequences and compositions are not
  represented.
- A manifest whose outputs are all plain ASCII (the minimal example) gets
  `compatibilityLevel: unsupported` and no file (D33).
- **Not verified.** Elgato does not document the format. The structure was
  rebuilt from public sources and community tools and has not been opened
  with the Stream Deck software; the report says so in `warnings`.

### Windows `.klc` (`oklm-to-klc`)

`python tools/export.py --target klc FILE.oklm.json` writes a Microsoft
Keyboard Layout Creator source: UTF-16 LE with BOM, CRLF, shift states
`0 1 2 6 7`. The module docstring of `tools/exporters/klc.py` is the
reference for the mapping. In short:

- levels 1-4 fill states 0, 1, 6, 7; the Ctrl column gets the usual control
  codes; CapsLock levels set the `Cap` column (swap of 0/1 and of 6/7) and a
  CapsLock behaviour that needs `SGCap` is reported as lossy;
- Level5Shift, NumLock and levels without selectors are skipped and reported;
- ligatures and characters outside the BMP are not exported (reported);
- a dead key needs a standalone character: `display`, then `fallback`, then a
  table of conventional spacing accents, then a private-use placeholder
  (reported as lossy); compositions whose base or result is not one BMP
  character are skipped and counted;
- always `lossy-mapping`, `roundTripConfidence: low`.
- **Not compiled.** MSKLC was not available; the files are checked by an
  in-repo parser (`tools/tests/test_klc.py`), which proves consistency with the
  manifest and not acceptance by Windows. The report says so in `warnings`.

## Extension Blocks

OKLM may include an extension block for source-specific data:

```json
{
  "extensions": {
    "ldml": {
      "unmapped": []
    }
  }
}
```

This is useful for preserving information during imports without forcing all LDML concepts into the core OKLM schema immediately.

## Compatibility Levels

Each converter should declare a compatibility level:

- `lossless-core`: core mapping preserved.
- `lossy-metadata`: mapping preserved, metadata lost.
- `lossy-mapping`: mapping approximated, manual review required.
- `failed`: conversion not usable.

## Strategic Importance

Bidirectional LDML conversion changes OKLM's positioning.

OKLM is not a rival format. It becomes:

- an authoring model;
- a validation layer;
- a practical tooling layer;
- an enrichment layer;
- a bridge to LDML and platform-specific outputs.

---

*Last updated: 2026-07-11*
