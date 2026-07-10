# OKLM and Unicode CLDR/LDML Keyboard

## Summary

OKLM must not compete with Unicode CLDR/LDML Keyboard.

Unicode CLDR/LDML Keyboard is the existing international interchange format for platform-independent keyboard mapping data. OKLM should position itself as a practical source model and tooling layer that can export to LDML, operating-system formats, dynamic-key devices, documentation, tests and assistant metadata.

Short version:

```text
OKLM = product-oriented source model and tooling layer
LDML Keyboard = standards-oriented interchange export
OS formats = installable artifacts
```

## Why LDML Matters

Unicode LDML Part 7 describes keyboards as part of the Unicode Locale Data Markup Language. Its goal is to communicate keyboard mapping data independently of vendors and platforms.

That overlaps with a central OKLM goal: describe a layout once and generate many outputs.

Therefore, OKLM should:

- study LDML Keyboard before stabilizing its schema;
- reuse LDML concepts where they fit;
- export valid LDML Keyboard XML where possible;
- import LDML Keyboard files where possible;
- report loss explicitly in both conversion directions;
- document every place where OKLM adds metadata beyond LDML.

## Why OKLM Still Exists

LDML Keyboard is primarily an interchange specification for keyboard mapping data.

OKLM has a broader product scope:

- operating-system exports;
- web tester data;
- static and dynamic keyboard legends;
- Stream Deck-style control surface profiles;
- stickers and keycaps;
- user-facing "how to type" documentation;
- learning metadata;
- accessibility labels;
- companion-app commands;
- local assistant metadata;
- comparison and validation tooling.

These are useful for AZERTY Global, QWERTY Global and other layout projects, even when the core mapping can also be represented in LDML.

## Recommended Architecture

```text
layout.oklm.json
      |
      v
OKLM tooling
      |
      +--> LDML Keyboard XML
      +--> Windows build inputs
      +--> macOS input-source files
      +--> Linux XKB / XCompose
      +--> web tester data
      +--> keyboard map images
      +--> dynamic legend packs
      +--> Stream Deck-style profiles
      +--> sticker / keycap label maps
      +--> character search indexes
      +--> local assistant knowledge files
      +--> conformance tests
```

## Boundary

OKLM should not claim:

- to replace CLDR;
- to replace LDML Keyboard;
- to be automatically installable on every OS;
- to be an official Unicode format;
- to define USB HID or hardware keyboard standards.

OKLM may claim:

- to be a practical authoring model;
- to produce LDML-compatible exports;
- to bridge OS formats, visual maps, dynamic legends and assistant metadata;
- to provide validation and reproducible generation;
- to help the industry maintain and consume one verified source of truth for each layout.

## Strategic Positioning

The public message should be:

> OKLM helps the keyboard ecosystem maintain one open source of truth for layouts, then export it to LDML, operating systems, hardware legends, dynamic-key devices, applications, documentation and assistants.

For AZERTY Global, this means:

- keep the layout stable;
- use OKLM to reduce divergence between Windows, macOS, Linux, website and documentation;
- export LDML for interoperability and credibility;
- use dynamic legends and assistant metadata as optional extensions.

For QWERTY Global, this means:

- describe a shared QWERTY chassis;
- layer local modules on top;
- demonstrate a future-proof model for global physical keyboards and local language packs.

---

*Last updated: 2026-06-03*
