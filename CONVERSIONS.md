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
