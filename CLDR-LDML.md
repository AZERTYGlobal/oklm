# OKLM and Unicode CLDR/LDML Keyboard

## Summary

OKLM does not compete with Unicode CLDR/LDML Keyboard. LDML Keyboard
(UTS #35 Part 7, "keyboard3", introduced in CLDR 45 in April 2024) is the
standards-oriented interchange format for platform-independent keyboard
mapping data. OKLM is a source model and tooling layer around it: one
human-maintainable file, exported to LDML, to operating-system formats, to
documentation and to devices, always with a report of what was lost.

```text
OKLM          = source model and tooling layer, maintained by humans
LDML Keyboard = standards-oriented interchange export
OS formats    = installable artifacts
```

Where LDML represents a concept cleanly, OKLM maps to it instead of
inventing a parallel one. Where LDML is not focused (dynamic legends,
learning and accessibility metadata, assistant knowledge, device-specific
exports), OKLM adds a layer above it and strips that layer on LDML export.

## What we align with, and in which version

| Reference | Version used | Read as |
|---|---|---|
| LDML Keyboard, UTS #35 Part 7 | **48.2** (CLDR 48.2). CLDR 49 alpha was published on 2026-09-04, beta announced for 2026-09-23; this document will be re-checked against 49 when it is final. | Full text |
| ISO/IEC 9995-1 | **:2026**, fourth edition, published 2026-01-16, 16 pages. It cancels and replaces ISO/IEC 9995-1:2009. | **Public preview only** (foreword, contents, abstract). No clause text has been read; every ISO-related statement below is limited to what the preview and secondary literature say. |
| W3C UI Events `KeyboardEvent.code` | Recommendation of **2025-04-22** | Full text |
| USB HID Usage Tables | **1.7**, 2026-01-26 (incorporates Review Request 117, Keyboard Backlight) | Full text, section 10 (Keyboard/Keypad page 0x07) |

Two notes on the references themselves, found while reading them:

- HUT 1.7 writes the modifier range as "Keyboard Left Control (0x224) to
  Keyboard Right GUI (0x231)"; the table gives `E0`–`E7`. 224–231 are the
  decimal values with a stray `0x` prefix. Do not copy "0x224".
- Review Request 56 ("Keyboard Layout Usage", Apple, approved 2015,
  incorporated in HUT 1.12) adds one usage to the Consumer page (0x0C):
  `0x29D AC Next Keyboard Layout Select`, a control that cycles through a
  set of layouts. It says nothing about describing a layout. No review
  request above 117 exists at the time of writing.

## Who consumes LDML Keyboard today

Measured in September 2026, from public sources:

- **No operating system loads keyboard3 files.** Keyman is the only
  consumer, on desktop only since Keyman 17.0; support on mobile and in
  the browser is planned through its Keyman Core "web-core" work (version
  19 in the March 2026 roadmap, which states it "is predicated on reaching
  our funding goals for the project").
- **No other layout tool exports LDML.** kalamine (TOML → klc, keylayout,
  xkb, ahk, web, SVG), klfc (imports XKB/PKL/KLC) and the QMK/VIA/ZMK
  firmware ecosystem do not. The nearest neighbours are `hickford/xkb_ldml`
  (xkeyboard-config → LDML, MIT) and Keyman's own `kmc-ldml` (LDML → `.kmx`
  and `.js`).

So the "bridge to LDML" niche is empty, and demand for it is unproven. OKLM
exports LDML because it is the one vendor-neutral interchange format that
exists, not because anything installs it yet.

## Why OKLM still exists

LDML Keyboard describes mapping data. OKLM also has to carry what a layout
project needs around the mapping: OS build inputs, web tester data, static
and dynamic legends, sticker and keycap maps, "how to type" documentation,
learning metadata, accessibility labels, companion-app commands, local
assistant metadata, and the validation that keeps all of these in step.
These are useful for AZERTY Global and QWERTY Global even when the core
mapping could be written directly in LDML.

## Architecture

```text
layout.oklm.json
      |
      v
OKLM tooling  (validators/, tools/export.py)
      |
      +--> LDML Keyboard XML          exists (one-way, with loss report)
      +--> Linux xkb_symbols          exists (levels 1-4)
      +--> macOS .keylayout           exists
      +--> Windows .klc               planned (ROADMAP item 6)
      +--> web tester data            planned (ROADMAP item 2)
      +--> Stream Deck profile        planned (ROADMAP item 5)
      +--> keyboard map images, legend packs, sticker maps,
           character indexes, assistant knowledge, conformance tests
                                      not started
LDML Keyboard XML --> layout.oklm.json  planned (ROADMAP item 7, gate 3)
```

## Boundary

OKLM does not claim to replace CLDR or LDML Keyboard, to be installable on
every OS, to be an official Unicode format, or to define USB HID or
hardware standards.

OKLM may claim to be a practical authoring model, to produce LDML-compatible
exports with explicit loss reports, to bridge OS formats, visual maps,
dynamic legends and assistant metadata from one source, and to provide
validation and reproducible generation.

## Known gaps against LDML Keyboard 48.2

Gate 1 of [ROADMAP.md](ROADMAP.md) compared the 0.1 schema field by field
with the four references above (review of 2026-09-03; 26 effective gaps,
6 of them heavy). The schema was **not** changed by the review. The gaps
below are the ones a user of the LDML export should know about now; they
are inputs to schema 0.2, not decisions. IDs are those of the review.

| ID | Gap | What the v1 exporter does today |
|---|---|---|
| **E1** | **No scan codes.** OKLM anchors a key by `hid` (usage page 0x07). LDML positions keys by `form/scanCodes` (2-digit hex bytes) per physical form (`iso`, `us`, `jis`, `abnt2`, `ks`) and by the order of `row@keys`. The manifest carries no HID → scan code table. | Uses a built-in USB → PC/AT Set 1 table for the alphanumeric section and emits a custom `<form>`; any `hid` outside that table is an error. |
| **E21** | **Silent levels.** OKLM says "a level with no output is simply omitted"; LDML says keystrokes are ignored where no layer matches, unless a layer `other` exists. The two are not the same, and the schema cannot express `other`. | **Fixed 2026-09-15:** a key without output at a level is emitted as LDML's implicit `gap` key, so every `<row>` has as many entries as the form has scan codes. Before the fix the row was shorter and every following key shifted one position (measured: `azerty-global.ldml.xml`, layer `altR`, row D had 8 keys for 12 scan codes). The semantic difference stays: the schema cannot express a layer `other`. |
| **E20** | **No rule for the LDML identifier.** keyboard3 expects `locale="fr-CH-t-k0-azerty"`-style identifiers; OKLM has `locales[0]` and `layoutId` but no derivation rule, and `locales[1..]` are not checked for the forbidden `-k0-` subtag. | Emits `locale="<locales[0]>"` and drops the layout variant. |
| **E13** | **Escaping in compositions.** LDML `transform@from` is a regex-like pattern where `. ( ) ? [ \ ] { } * / ^ + \| $` must be escaped. The schema does not say whether a composition base is a literal string or a pattern. | Concatenates `\m{id}` and the base **without escaping**. A base such as `^` or `.` produces an invalid or wrong transform. |
| **E8** | **Groups.** `keys[].groups` (2–9) is an ISO/IEC 9995 concept; LDML has no groups (a different arrangement is "two different keyboards"). | Rejects any manifest that uses `groups` (v1 scope). |
| **E7** | **Levels 5–8.** ISO/IEC 9995-1:2026 allows level 4 "albeit not recommended" and its labelling clause covers "up to four levels" (foreword and contents of the public preview). No reference knows a fifth level or a `Level5Shift` qualifier; they are an OKLM extension. | Exports levels 5–8 only when `levelSelectors` resolves them to `shift`, `altR` and `caps`; `Level5Shift` and `NumLock` have no LDML component and skip the level. |
| E6, E22 | `NumLock` as a level selector and `{ "modifier": … }` as a key output: LDML treats modifier keys as frame keys that cannot generate output, and the numpad as out of scope. | Skips them and reports the skip. |
| E15 | `fallback`: LDML has no fallback or cancellation; all markers are removed from the final text. | Approximated as a transform matching the bare marker, reported as lossy. |
| E10, E11 | `hid` accepts values HUT 1.7 marks non-physical (`00`–`03`) or reserved (`E8`–`FFFF`); `code` accepts any `[A-Za-z0-9]+` rather than the W3C enumeration, and nothing enforces "only one `Backslash`". | Not validated. The `--strict` mode planned for 0.2 is where this belongs. |
| E2, E3, E4 | `version` is free text where LDML wants SEMVER; there is no equivalent of `info@attribution` (originating body), `info@layout` or `info@indicator`. | `version` copied as-is; `layoutId`, `authors`, `license` skipped. |
| E12 | Geometry aliases: OKLM says `ansi-*` and `abnt-*` where LDML says `us` and `abnt2`; `ks` (Korean) and `touch` have no alias. | Not mapped; the export uses a custom form anyway. |
| E14 | `deadKeys[].display`: LDML forbids a non-spacing mark without a base (U+25CC) in `display`; OKLM has no such rule. | Copied as-is. |

Not gaps: `output` strings, `{ "deadKey": id }` → `\m{id}`, `deadKeys[].id`
(a valid NMTOKEN) and `name` map directly. Out of the review's scope: `xkb`
aliases, the Windows and macOS targets, and LDML constructs OKLM 0.1 does
not attempt (`backspace` transforms, `reorder`, `variables`, `flicks`,
`longPress`, `multiTap`, touch layers).

## Positioning

The public message is deliberately modest until gate 4:

> OKLM keeps one open, human-maintainable source of truth for a keyboard
> layout and exports it to LDML Keyboard, operating systems, hardware
> legends, documentation and devices, reporting every loss.

For AZERTY Global: keep the layout stable, use OKLM to remove divergence
between Windows, macOS, Linux, the website and the documentation, and
export LDML for interoperability. For QWERTY Global: describe a shared
chassis and layer local modules on it.

---

*Last updated: 2026-09-15*
