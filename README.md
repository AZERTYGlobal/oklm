# Open Keyboard Layout Model

> Public draft for an open model and manifest format to make keyboard layouts interoperable across operating systems, hardware keyboards, dynamic key displays, applications, enterprise deployments and AI-assisted input workflows.

## Status

Draft product concept.

This folder is the starting point for a future public standard and reference implementation. It is not yet a published specification.

## Why

Keyboard layouts are still mostly distributed as operating-system-specific files, static images, installer packages, firmware assumptions or informal documentation.

That is no longer enough.

Modern input needs a shared model across:

- classic ANSI and ISO keyboards;
- OS-level keyboard layouts;
- web-based keyboard testers;
- dynamic key displays;
- Stream Deck-like control surfaces;
- keycap and sticker production;
- laptop and keyboard OEMs;
- browsers, IDEs, remote desktop tools and games;
- enterprise IT deployment;
- AI assistants and local agents;
- accessibility profiles;
- learning and migration tools.

Open Keyboard Layout Model defines a common representation so one layout can be described once, then exported to many targets.

## Core Idea

A keyboard layout should be both:

- usable by humans as a documented typing system;
- usable by software as structured data.

Core promise:

> An OKLM file must be readable, correctable and versionable by a human without a proprietary generator.

The manifest describes:

- physical keys and geometry;
- ISO/IEC 9995 groups, levels and functional modifiers;
- dead keys and composition rules;
- visible legends;
- dynamic labels;
- character metadata;
- training hints;
- export targets;
- compatibility notes.

## Relationship With Existing Standards

Open Keyboard Layout Model should not ignore Unicode CLDR/LDML Keyboard.

The goal is to complement and bridge existing formats:

- CLDR/LDML Keyboard for platform-independent keyboard description;
- XKB/XCompose for Linux and Wayland ecosystems;
- Windows keyboard layouts and companion apps;
- macOS input sources;
- web testers and documentation;
- dynamic-key devices and control surfaces.

If CLDR/LDML can represent a feature cleanly, the manifest should map to it instead of inventing an incompatible concept. Where CLDR/LDML is not focused, especially dynamic legends, learning metadata, accessibility labels, AI assistant knowledge and device-specific exports, this project can add a higher-level layer.

See [OKLM and Unicode CLDR/LDML Keyboard](CLDR-LDML.md) for the intended boundary.

OKLM tooling should support both [OKLM / LDML conversions](CONVERSIONS.md):

- OKLM -> LDML Keyboard, with an explicit loss report for OKLM-only features;
- LDML Keyboard -> OKLM, preserving mapping semantics and extension data where possible.

## Reference Layouts

The first intended reference layouts are:

- AZERTY Global;
- QWERTY Global;
- QWERTY Global local modules.

These projects are reference implementations, not hard dependencies. The model should remain usable by operating-system vendors, hardware manufacturers, software vendors, enterprise tools and independent layout projects.

## Industry Goal

OKLM is not only a convenience format for layout authors. Layout authors are the first users because they can validate the model quickly.

The long-term goal is industry adoption:

- OS vendors can consume verified layout metadata.
- Keyboard and laptop manufacturers can generate legends, keycap sets, dynamic displays and regional variants.
- Application vendors can show correct shortcuts and physical-key hints for the user's actual layout.
- Remote desktop and virtualization tools can preserve keyboard intent across platforms.
- Enterprise IT can deploy and audit keyboard layouts consistently.
- AI and assistant platforms can answer deterministic "how do I type this?" questions without guessing.

See [Industry Adoption Strategy](INDUSTRY-ADOPTION.md).

## What This Is Not

Open Keyboard Layout Model is not:

- a new keyboard layout;
- a hardware keyboard;
- an operating-system driver;
- a replacement for OS-native layout formats;
- a commercial product by itself.

It is the common description layer that can generate or document those outputs.

## Target Exports

Initial export targets:

- static keyboard maps;
- web tester data;
- character search indexes;
- dynamic legend packs;
- Stream Deck-style profiles;
- OS-specific build inputs;
- keycap and sticker label maps.

Future export targets:

- Copilot key and AI-key companion apps;
- Flux/Nemeio-style dynamic keyboard profiles;
- accessibility-optimized legends;
- local assistant knowledge files.

## Exporters

`tools/export.py` converts an `.oklm.json` manifest to one of three one-way
export targets, each producing a target file plus a conversion report:

```text
python tools/export.py --target ldml|xkb|keylayout FILE.oklm.json [FILE ...]
```

- `ldml`: CLDR/UTS #35 Part 7 `keyboard3` XML;
- `xkb`: a standalone `xkb_symbols` block for Linux;
- `keylayout`: an Apple `.keylayout` file for macOS.

Every export writes `<name>.<ext>` and `<name>.<ext>.report.json`, the
latter validating against
[`schemas/oklm-conversion-report.schema.json`](schemas/oklm-conversion-report.schema.json).
Reports declare exactly what was mapped, skipped, or approximated — see
[CONVERSIONS.md](CONVERSIONS.md) "Other Export Targets" for the current,
honest list of scope limits (e.g. xkb only exports ISO/IEC 9995 levels
1-4). `examples/exports/` holds committed reference exports for all six
example manifests; `tools/tests/run_tests.py` checks them for regressions,
determinism, and schema validity.

## Repository Shape

Current public repository structure:

```text
Open Keyboard Layout Model/
├── README.md
├── SPEC.md
├── CLDR-LDML.md
├── CONVERSIONS.md
├── INDUSTRY-ADOPTION.md
├── ROADMAP.md
├── GOVERNANCE.md
├── examples/     # six example manifests (5 complete layouts + minimal subset)
│   └── exports/  # committed reference exports (ldml/xkb/keylayout) for each example
├── schemas/      # manifest + conversion-report JSON Schemas (manifest 0.1, report 0.2)
├── tools/        # export.py CLI + exporters/ (ldml, xkb, keylayout) + tests/
└── validators/   # reference validation script

Planned next: LDML/xkb/keylayout importers.
```

## Naming

Public name: OKLM.

Full name: Open Keyboard Layout Model.

Canonical file format: OKLM Manifest, usually `.oklm.json`.

The canonical format is JSON because it has strong tooling and schema validation, but OKLM JSON must remain hand-maintainable: stable field order, explicit names, shallow structures where possible and no generator-only encoding.

Domains:

- `oklm.org`: canonical public domain.
- `openkeyboardlayoutmodel.org`: long-form domain, intended to redirect to `oklm.org`.

## Licensing

Dual license by content type:

- specification and documentation (`*.md`): [CC BY 4.0](LICENSE-CC-BY-4.0);
- schemas, validators, tooling and reference exporters: [EUPL 1.2](LICENSE).

Layout data described *with* OKLM keeps its own license, declared in the manifest's `license` field.

---

*Last updated: 2026-07-11*
