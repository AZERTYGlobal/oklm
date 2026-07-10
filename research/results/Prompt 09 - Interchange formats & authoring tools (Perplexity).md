# Keyboard Layout Interchange Formats: Survey, Gap Analysis, and Design Recommendations

*A comparative report for engineers designing a new open, JSON-based, human-maintainable keyboard layout source format.*

***

## Executive Summary

Unicode CLDR/LDML Keyboard 3.0 ("Keyboard 3.0") is now the strongest single candidate for an open, platform-independent interchange standard, with explicit support for transforms, reordering, markers, display overrides, multi-locale, and both hardware and touch forms in one file. Its non-goals are precisely documented: IME, frame keys (Fn, cursor, IME-swap), run-time efficiency, accessibility features, and backward compatibility with prior LDML. Those non-goals, combined with LDML's XML verbosity and the absence of tooling for dynamic-legend metadata, pedagogy scaffolding, AI-assistant typing hints, and device/control-surface export, do open a genuine — though narrow — design space for a higher-level JSON layer. The risk of duplication is very high in the core mapping and transform domains; it is low in the pedagogical, dynamic-legend, and AI-metadata domains. The recommended architecture is **delegate the interchange core to LDML, wrap it in a JSON envelope that adds the higher-level metadata layer, and fan out to LDML and platform targets from that envelope**.

***

## 1. Unicode CLDR / LDML Keyboard 3.0 — The Primary Standard

### 1.1 History and Current Status

The original LDML keyboard format was introduced in 2012 and intended primarily for comparative and interchange purposes, but it "did not achieve that purpose". The data model was built around ISO hardware key positions (A01, A02…), platform-specific per-key `longPress-status`, and a `longPress`-orientation that made touch layouts awkward. The CLDR Keyboard Subcommittee was formed in mid-2020 and met for over 18 months before publishing a Technical Preview of "Keyboard 3.0" (UTS#35 Part 7) in May 2023 as Unicode Public Review Issue #476. The CLDR-TC determined that the changes were too extensive to maintain backward compatibility with CLDR v43 and prior: the new format is a **complete rewrite** with a different DTD and fundamentally different data model.[^1][^2]

The Keyboard 3.0 draft is incorporated into CLDR releases from CLDR 45 onward (tagged `keyboard3/`), with the conformance attribute `conformsTo="techpreview"` required in files targeting this draft. Keyboard submissions to the CLDR repository follow a formal intake process with a contributed/approved lifecycle.[^3][^1]

### 1.2 Structure and Key Elements

**Element: `<keyboard>`** — top-level element; carries a `locale` attribute (BCP 47), a `conformsTo` version, and child elements for all aspects of the layout.[^1]

**Element: `<keys>` / `<key>`** — a "bag of keys" model, where each key has a unique `id`, a `to` output string, optional `longPress`, `multiTap`, `flicks`, `switch`, `gap`, `width`, `stretch`, and `transform="no"` attributes. This decouples key identity from physical position and makes the same key reusable in multiple layers.[^1]

**Elements: `<flicks>` / `<flick>`** — model gesture-based input on touch surfaces; a flick in a given direction (n, ne, e, se, s, sw, w, nw) can emit one or more code points.[^1]

**Element: `ayers>` / `ayer>`** — groups keys into a physical-form-factor-specific grid via `<row keys="...">`. The `form` attribute on `ayers>` specifies either a hardware form (e.g., `us`, `iso`, `jis`, `abnt2`) or `touch`. Multiple `ayers form="touch">` elements with distinct `minDeviceWidth` values allow phone vs. tablet differentiation. Hardware layers use modifier-key combinations (`modifiers="shift"`, `modifiers="altR"`, etc.) to define which layer is active.[^1]

**Element: `<displays>` / `<display>`** — allows overriding the visual keycap label for any output character. Critical for combining marks and diacritics (e.g., displaying U+0303 combining tilde as ◌̃). Also supports per-key-id display overrides (e.g., a custom label for Shift). `<displayOptions baseCharacter="..."/>` lets scripts specify a non-U+25CC dotted circle as the combining-mark base.[^1]

**Element: `<variables>`** — defines named string (`<string>`), set (`<set>`), and UnicodeSet (`<unicodeSet>`) variables for reuse in transforms and reorder rules.[^1]

**Element: `<import>`** — references external XML fragments from the CLDR repository (e.g., standard punctuation transforms, implied key sets). Enables modular composition.[^1]

**Element: `<transforms>` / `<transformGroup>` / `<transform>`** — the most powerful element. Two subtypes:
- `type="simple"`: dead-key chains and multi-character output rules. The `from` attribute uses a regex-like syntax (supporting character classes, Unicode sets, `any()`-like matching) to match a sequence; `to` specifies output. A `before` attribute allows look-behind context.[^1]
- `type="backspace"`: custom backspace behavior for partially-composed sequences.

The transform syntax is explicitly modeled as "a subset of common regular expression syntaxes, so that existing regular expression engines may be used to implement the LDML specification". Look-ahead (`after`) was removed from the spec after proving ambiguous.[^2]

**Element: `<reorder>`** — handles scripts where input order and Unicode canonical order differ (primarily Brahmic/Indic scripts). Each `<reorder>` rule specifies a `from` character class and `order`, `tertiary`, `tertiaryBase`, and `preBase` attributes to assign reordering weights. The reorder subsystem works in concert with Unicode normalization.[^1]

**Markers (`\m{name}`)** — invisible placeholder tokens that can appear in `to` outputs and be matched in subsequent `from` patterns. Markers are used to represent intermediate dead-key states without leaking PUA code points into the text store. The `<display>` element can reference a marker for keycap display purposes.[^1]

**Element: `<settings>`** — controls `fallback` behavior (emit nothing vs. emit base-map output when a modifier combination goes unmatched), `transformFailure`, and `transformPartial` (hide/show buffer during composition).[^1]

### 1.3 What LDML Keyboard 3.0 Models Well

| Capability | LDML 3.0 Coverage |
|---|---|
| Base character mapping | Full: hardware + touch in one file |
| Shift/modifier levels | Full: arbitrary modifier combinations via `modifiers=` |
| AltGr (ISO Level 3) | Full |
| Dead keys (single) | Full: via `<transform>` rules |
| Chained dead keys | Full: multi-step transform chains with markers |
| Multi-character output | Full: `to` attribute accepts any Unicode sequence |
| Contextual rules / transforms | Strong: regex-like `from`/`to` with `before` look-behind |
| Reordering for Indic/Brahmic | Full: dedicated `<reorder>` element with ordering weights |
| Markers / variables | Full: `\m{name}` markers, `<string>`, `<set>`, `<unicodeSet>` variables |
| Normalization hint | Metadata only: `info/@normalization` (NFC/NFD/other) |
| Per-key display legends | Strong: `<display>` override; combining-mark base customization |
| Long-press (mobile) | Full: `longPress`, `longPressDefault` on `<key>` |
| Flicks (mobile gesture) | Full: `<flicks>` / `<flick>` |
| Multi-tap | Supported (though `discouraged` for accessibility) |
| Multi-locale | Full: `ocales>` child elements for additional BCP 47 tags |
| Hardware AND touch in one file | Full: `ayers form="touch">` and `ayers form="us">` coexist |
| Schema validation | Full: XML DTD + XSD schema provided |
| Import/modularization | Full: `<import base="cldr" path="..."/>` |
| Test data | Full: `<keyboardTest>` element with keystroke/emit/check |

### 1.4 Explicit Goals and Non-Goals

The primary source (PRI #476 background document and the UTS#35 Part 7 spec) states the following goals explicitly:[^2][^1]

1. Define physical and virtual keyboard layouts in a single cross-platform file.
2. Provide definitive platform-independent definitions for new layouts.
3. Cover only the **character-emitting, non-frame keys**; platform-specific keys (Fn, Numpad, IME-swap, cursor keys) are **out of scope**.
4. Deprecate and archive the earlier LDML platform-specific layouts.

Stated **non-goals**:[^2][^1]
- **Input Method Editors (IME)** — multi-candidate selection UI systems (e.g., for Han ideographs) are explicitly out of scope.
- **Localized keycap names** (e.g., the German word for "Return") — noted as belonging to LDML Part 2, not Part 7.
- **Platform-specific frame keys** (Fn, cursor, Numpad, IME-swap keys).
- **Round-tripping of existing platform formats** — not guaranteed.
- **Replacing pre-existing platform layouts** — intended for new or newly-updated layouts only.
- **Run-time efficiency** — LDML is explicitly an interchange format, not a keystroke-engine format.
- **Backward compatibility with CLDR v43 and prior**.
- **Adaptation for screen scaling resolution** — keyboards define physical size; platforms adapt.
- **Unification of pre-existing platform layouts themselves**.

The spec also notes explicitly: *"For this revision, the committee is not evaluating features or architectural designs for the purpose of improving accessibility."* Accessibility is flagged as a topic for future revisions.[^1]

**Implicit additional non-goals** (not stated but clear from scope):
- Dynamic (runtime-changeable) key legends driven by application state.
- Pedagogical/learning metadata (e.g., typing-course lesson annotations, finger placement).
- AI/language-assistant metadata (e.g., typing-effort costs, n-gram hints, autocorrect training signals).
- Device/control-surface exports (MIDI controllers, stream decks, QMK/ZMK firmware, VIA JSON).
- Human diff-friendly JSON/YAML source format (LDML is XML).

### 1.5 Tooling and Adoption

- **Keyman Developer** is the most mature LDML-capable tool. Version 17 introduced a basic LDML editor; Version 18 ships a compiler (`kmc-ldml`, also published as an npm package `@keymanapp/kmc-ldml`). The Keyman roadmap for Version 19 targets full CLDR/LDML keyboard support across mobile (Android, iOS) and web via the Keyman Core Web interface.[^4][^5][^6]
- **GNOME Caribou** used a `convert_cldr.py` script to consume old CLDR keyboard XML files for Android, ChromeOS, and macOS-sourced layouts.[^7]
- **kbdgen (Divvun)** has CLDR output "in the pipeline" but not yet released.[^8]
- **Android, ChromeOS, macOS** have historically consumed older CLDR v43-era keyboard data for built-in layouts. Migration to Keyboard 3.0 format is an ongoing process.[^9][^7]
- The CLDR keyboard repository intake process is designed explicitly for vendors: "Vendors and other implementers can utilize the repository to extend their language coverage with keyboards known to be relevant to language communities".[^3]

***

## 2. Other Source and Authoring Formats

### 2.1 kalamine (OneDeadKey)

**Input format:** YAML or TOML (`.yaml` / `.toml`) — human-readable, text-editor-friendly, with an ASCII art layout representation embedded in comments for visual editing.[^10]

**What it can express:**
- Base layer and AltGr/Option layer
- One custom dead key per layout (the "1dk" / Lafayette dead key concept)
- Standard dead keys with string maps (character-to-character)
- Chained dead keys (CDK) — explicitly supported as a design goal, with workarounds for MSKLC's CDK limitations via `wkalamine`[^11][^10]
- Key metadata: locale, name, description, geometry (ERGO ortholinear variant)

**What it does NOT express:**
- Complex contextual transforms (no full regex-like transform engine)
- Reordering rules for Indic/Brahmic scripts
- Markers / variables
- Multi-locale support
- Mobile/touch layers (no mobile output target)
- Per-key display legends beyond the keycap character itself
- Accessibility metadata, pedagogy, AI metadata

**Export targets:** Windows KLC (for MSKLC/KbdEdit), Windows AHK (user-space, unsigned), macOS `.keylayout` (XML), Linux XKB symbols, Linux XKB keymap, JSON (for the `x-keyboard` web component), SVG.[^10]

**Schema validation:** No formal schema; validation is implicit in the Python parser.

**Conversion tooling:** `kalamine build`, `wkalamine` (Windows signed installer), `xkalamine` (Linux XKB management). No LDML output.

**Assessment:** kalamine excels as a dead-key-centric, European-language Latin-script authoring tool. Its TOML/YAML source is genuinely diff-friendly. Its ceiling is single-dead-key chains for Latin scripts; it is not designed for complex-script work and has no path to LDML or mobile output.

### 2.2 kbdgen (Divvun / GiellaLT)

**Input format:** YAML project bundle (`.kbdgen` directory containing `project.yaml` and layout files). Historically Python-based; rewritten in Rust.[^8]

**What it can express (per documentation and GiellaLT usage):**
- Multi-target output from a single YAML source
- Multiple layers (base, shift, AltGr, caps, etc.)
- Long-press key variants for mobile
- Language/locale metadata
- Speller FST integration (hit-error correction model)

**What it does NOT express:**
- Complex contextual transforms or dead-key chains beyond simple dead-key support
- Reordering rules for Indic/Brahmic scripts
- Markers / variables
- Per-key display legend overrides
- Pedagogy, AI metadata, dynamic legends

**Export targets:** Linux (X11, m17n), macOS, Windows, ChromeOS, iOS/iPadOS, Android, SVG. CLDR keyboard output is "in the pipeline" but not yet released.[^8]

**Schema validation:** YAML schema (partially enforced by the Rust tooling).

**Assessment:** kbdgen has the broadest OS export footprint of any tool in this survey (including mobile). It is the primary tool for the GiellaLT minority language keyboard ecosystem. Its transform model is weaker than Keyman's, and the lack of CLDR output is a gap it explicitly acknowledges.[^8]

### 2.3 KLFC (Keyboard Layout Files Creator)

**Input format:** JSON (`.json`) — the internal canonical format; can also import from XKB, PKL, KLC.[^12]

**What it can express:**
- Multiple shift levels with arbitrary modifier combinations (Shift, AltGr, CapsLock, Extend, Win, Alt, Ctrl, NumLock — left/right variants supported)[^12]
- Custom dead keys with `stringMap` (character → string transforms)[^12]
- Physical position remapping via permutation `mods`[^12]
- Layout variants (additive patches to a base layout)[^12]
- Filter by output target (some keys only appear in certain formats)[^12]
- Chained dead keys (via the `--klc-chained-deads` flag)[^11]
- QWERTY shortcuts preservation

**What it does NOT express:**
- Contextual (regex-style) transforms
- Reordering rules
- Markers / variables
- Mobile/touch output
- Display legend overrides
- Accessibility, pedagogy, AI metadata

**Export targets:** XKB, PKL (Portable Keyboard Layout), KLC (Microsoft KLC), macOS `.keylayout`, TMK (keyboard firmware), AHK. No LDML, no mobile.[^12]

**Schema validation:** Implicit JSON schema via Haskell parser. Last release December 2021.

**Assessment:** KLFC is arguably the most capable JSON-based authoring format for desktop-only Latin-script layouts. Its modifier model is richer than kalamine's, it supports import from existing platform formats, and its JSON source is diff-friendly. However, it is unmaintained since late 2021, has no complex-script support, and no LDML or mobile output. It is the closest existing analog to the new open JSON model being proposed — and the closest to being "merely redundant."

### 2.4 Keyman / KMN (and KMX)

**Input format:** `.kmn` — a domain-specific programming language (text-based, human-writable). The Keyman touch layout is a separate `.keyman-touch-layout` file in JSON format.[^13][^14][^15]

**What it can express:**
- Full contextual rules: `any()`, `index()`, `context()`, `deadkey()`, `set()`, `if()`, `call()`, `beep()`, groups, stores[^14]
- Chained dead keys via the `deadkey()` / `dk()` mechanism — up to 65,534 unique named deadkeys per keyboard[^16]
- Visual reordering for complex scripts (context-based rule sequences handle Tamil, Indic, etc.)[^17]
- Multi-character output (over 1,000 characters at once)[^18]
- Options (persistent user-selectable settings)
- On-screen keyboard XML (`.kvks`) for desktop
- Touch layout JSON (`.keyman-touch-layout`) for mobile with longpress arrays, pop-up keys, layer switching, and font overrides[^19]
- `&displayMap` store for on-screen keyboard display data[^14]
- BCP 47 language tags, metadata (author, version, copyright)

**What it does NOT express natively (in `.kmn`):**
- Normalization-form guarantees (explicit note: "Keyman does not do any normalisation")[^20]
- Pedagogy, AI metadata, dynamic legends
- A single unified file format (touch layout is a separate JSON file)

**LDML integration:** Keyman Developer 17 introduced a basic LDML XML editor; full LDML compiler (`kmc-ldml`) ships in v18; CLDR keyboard support in mobile and web is the headline feature for v19. LDML keyboards compile to `.kmx` binary via `kmc-ldml`.[^5][^6][^4]

**Export targets:** Windows, macOS, Linux (`.kmx`), Web/JavaScript (`.js`), iOS, Android (via compiled `.js`).[^21]

**Assessment:** Keyman has the deepest complex-script capability of any tool outside LDML itself, plus the broadest real-world deployment (over 2,200 languages supported). Its `.kmn` DSL is powerful but not a portable interchange format — it is Keyman-specific. The LDML integration path is maturing actively.[^22]

### 2.5 KbdEdit (Windows, shareware)

**Input format:** Proprietary GUI; can import/export KLC files; also imports macOS `.keylayout` files (Premium edition).[^23]

**What it can express:**
- Full Windows keyboard driver capabilities: shift levels, AltGr, dead keys, chained dead keys, ligatures (multi-character output), KANA mode, Caps Lock behavior[^23]
- Remap physical key positions (Personal edition)
- Produce signed installable Windows keyboard drivers

**Export targets:** Windows keyboard driver DLL (signed installer), KLC for MSKLC compatibility. macOS `.keylayout` import/export (recent versions). No Linux, no mobile, no LDML.[^11][^23]

**Assessment:** KbdEdit is the most capable Windows-only authoring GUI. It is proprietary shareware, not a source format. No JSON or YAML representation; no diff-friendly source. Its role in the ecosystem is as an end-point installer tool, not an interchange format. Included here for completeness.

### 2.6 Microsoft KLC (MSKLC)

**Input format:** `.klc` text format (UTF-16LE with BOM) — human-readable but idiosyncratic.[^11]

**What it can express:**
- Up to 9 shift states (base, Shift, Ctrl, Ctrl+Shift, AltGr, AltGr+Shift, and combinations)
- Dead keys with single-step string maps
- Ligatures (multi-character output, up to 4 characters)

**Limitations:** No chained dead keys in MSKLC-compiled layouts (a known Windows 10/11 regression). AltGr+Space cannot be remapped. 32-bit installer only (no 64-bit support beyond KbdEdit workaround).[^11]

**Export targets:** Windows only (`.dll` keyboard driver + MSI installer).

**Assessment:** KLC is a legacy Windows-specific format. It is not a viable target for a new open cross-platform model except as a downstream export format.

### 2.7 Native OS Formats (XKB / keylayout) — Summary

**XKB (Linux):** A declarative text format organized around key symbols, modifier levels, and symbol groups. Very expressive for Latin-script modifier levels; dead-key support via `type` specifications. No contextual transform model, no mobile support. Source is diff-friendly text. Part of the X Keyboard Extension ecosystem.[^24]

**macOS `.keylayout` (XML):** Apple's XML format for keyboard definitions. Supports multiple modifier states, dead key trees, and ligatures. No mobile/touch support, no contextual transforms beyond dead key trees.[^25]

**Assessment:** Both formats are human-readable and diff-friendly but are platform-specific. They are natural output targets, not input sources, for a cross-platform model.

### 2.8 Karabiner-Elements (macOS)

Karabiner-Elements is a **key remapper**, not a keyboard layout authoring tool. Its JSON configuration (`karabiner.json`) describes `from`/`to` key code transformations with conditions (device type, modifier flags, etc.). It operates at the macOS event tap level, translating HID key codes before they reach the OS input method system. It cannot express Unicode character output in the sense that LDML or KMN can; it maps key codes to key codes (or modifier states). It has no concept of dead keys, transforms, normalization, or locale. **It is not relevant to the interchange format design space** except as context that macOS remapping tools exist and are separate from layout authoring tools.[^26][^27]

### 2.9 AutoHotkey / Espanso / Text Expansion — Adjacent Context

These tools operate post-OS at the application layer, replacing typed trigger strings with expansion strings. They are text macro tools, not keyboard layout tools. Espanso uses YAML for its configuration but does not model key codes, shift levels, or Unicode composition. They are architecturally distinct and not relevant to interchange format design, except to note that the "AI/assistant typing hints" use case overlaps partially with text expansion — a distinction any new format design should make explicit.[^28][^29]

***

## 3. Complex-Script Requirements

### 3.1 Dead-Key Chains

A dead key is a key that emits an invisible placeholder, subsequently consumed by a transform rule when the next key is pressed. Chained dead keys (CDK) stack multiple such states: pressing dead1 then dead2 then a base character produces a doubly-modified output. LDML handles this natively via multi-step `<transform>` rules using markers to track intermediate states. Keyman handles it via `deadkey()` named markers in rules. kalamine and KLFC both support single CDK but are limited by their simpler transform models. MSKLC/KLC explicitly does not support CDK on Windows 10/11.[^30][^16][^11][^1]

### 3.2 Contextual Transforms

Scripts like Indic, Southeast Asian (Khmer, Thai, Myanmar), and Arabic require rules where the output depends not just on the current keystroke but on the accumulated context in the text store. LDML's `<transform>` element with `before` look-behind handles this. Keyman's rule engine (`context()`, `any()`, `index()`, groups) is the most flexible general-purpose contextual rule engine available. XKB and `.keylayout` have no contextual transform model.[^14]

### 3.3 Reordering for Indic/Brahmic

In many Brahmic scripts, the phonological syllable structure (consonant + vowel) does not map directly to Unicode encoding order. For example, Tamil vowel signs appear before the consonant visually but must follow it in Unicode order. The LDML `<reorder>` element assigns `order`, `tertiary`, `tertiaryBase`, and `preBase` weights to character classes, allowing the keystroke engine to buffer and reorder combining sequences before emitting them. This is a significant feature not present in any other tool except Keyman (which handles this via explicit rule groups and context manipulation).[^17][^1]

### 3.4 Normalization

LDML specifies a `normalization` metadata attribute (`NFC`, `NFD`, `other`) and requires CLDR repository keyboards to be in NFC or NFD. However, Keyman explicitly does not normalize — it emits what rules specify. A new format must decide whether it enforces normalization at the source level or delegates normalization contracts to the execution layer.[^20][^1]

***

## 4. Master Feature / Coverage Matrix

The following table rates each tool's capability on each dimension:
- **✅ Full** — first-class, documented, tested support
- **⚠️ Partial** — limited, workaround, or discouraged support
- **❌ None** — not supported
- **N/A** — not applicable to this tool's scope

| Capability | LDML Keyboard 3.0 | kalamine | kbdgen | KLFC | Keyman (.kmn) | Native OS (XKB / .keylayout / KLC) |
|---|---|---|---|---|---|---|
| Base mapping (key → character) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Shift levels / modifier layers | ✅ | ✅ (base + AltGr) | ✅ | ✅ (8+ levels) | ✅ | ✅ (varies) |
| AltGr (ISO Level 3) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dead keys (single) | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ (XKB/keylayout) |
| Chained dead keys | ✅ (markers) | ✅ (wkalamine) | ❌ | ⚠️ (flag) | ✅ (named dk) | ❌ (KLC/Windows) |
| Multi-character output | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ (ligatures) |
| Contextual transforms (regex-style) | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Reordering (Indic/Brahmic) | ✅ (`<reorder>`) | ❌ | ❌ | ❌ | ✅ (rules) | ❌ |
| Markers / variables | ✅ | ❌ | ❌ | ❌ | ✅ (dk names, stores) | ❌ |
| Per-key display legends | ✅ (`<display>`) | ❌ | ❌ | ❌ | ⚠️ (.kvks / touch JSON) | ❌ |
| Locale / multi-locale | ✅ | ⚠️ (single locale) | ✅ | ⚠️ | ✅ | ❌ |
| Mobile / touch output | ✅ (touch layers) | ❌ | ✅ (iOS/Android) | ❌ | ✅ (.touch-layout JSON) | ❌ |
| Flicks / long-press (mobile) | ✅ | ❌ | ⚠️ (long-press) | ❌ | ✅ | ❌ |
| Dynamic-legend metadata | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Pedagogy / learning metadata | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| AI/assistant typing hints | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Device / control-surface exports | ❌ | ❌ | ❌ | ⚠️ (TMK firmware) | ❌ | ❌ |
| Human-readable, diff-friendly source | ❌ (XML) | ✅ (TOML/YAML) | ✅ (YAML) | ✅ (JSON) | ⚠️ (DSL, not standard) | ⚠️ (text but ad-hoc) |
| Schema validation | ✅ (DTD/XSD) | ❌ | ❌ | ❌ (implicit) | ❌ | ❌ |
| OS export targets — Windows | (data only) | ✅ | ✅ | ✅ | ✅ | ✅ (KLC) |
| OS export targets — macOS | (data only) | ✅ | ✅ | ✅ | ✅ | ✅ (.keylayout) |
| OS export targets — Linux | (data only) | ✅ | ✅ | ✅ | ✅ | ✅ (XKB) |
| OS export targets — Android/iOS | (data only) | ❌ | ✅ | ❌ | ✅ | ❌ |
| OS export targets — Web/JS | (data only) | ✅ (JSON) | ❌ | ❌ | ✅ (.js) | ❌ |
| Export to LDML | N/A | ❌ | ❌ (planned) | ❌ | ✅ (partial, v17+) | ❌ |

***

## 5. Gap Analysis

### Step 1: Independent Evidence-Based Assessment

**Areas already well-covered (high redundancy risk):**

1. **Base mapping, shift levels, AltGr, multi-character output.** Every tool in the survey covers these competently. LDML 3.0 covers them rigorously with schema validation. A new format reinventing this layer would be pure duplication.

2. **Dead-key chains and contextual transforms.** LDML 3.0 and Keyman together cover this space thoroughly. LDML's transform model is explicitly designed to be implementable using standard regex engines. Reinventing this as a JSON transform language would duplicate LDML unless it offered materially different semantics.[^2]

3. **Reordering for Indic/Brahmic.** LDML's `<reorder>` element and Keyman's rule engine are the only tools that address this, and they do so well. No gap exists for well-resourced script communities — the gap is in tooling and documentation for underserved scripts, not in format expressiveness.

4. **Normalization metadata.** LDML already carries `info/@normalization`. This is thin metadata but it exists.

5. **Mobile/touch output.** LDML 3.0 natively models touch layers. kbdgen and Keyman also produce mobile output. The gap is in a single authoring format that reaches all mobile targets; LDML does not currently produce native APK or IPA files — it provides the data, which platforms then consume. This is a **tooling gap, not a format gap**.

6. **Schema validation.** LDML provides XML DTD and XSD. Any new JSON format should provide a JSON Schema, but this is a format-implementation concern, not a structural design gap.

**Areas genuinely under-served (low redundancy risk):**

1. **Dynamic-legend metadata.** No existing format models keys whose display labels change at runtime (e.g., a key that shows the Unicode character normally but shows a mnemonic in "learning mode," or a key whose legend changes based on application context). LDML's `<display>` element is static — it maps a fixed output character to a fixed display string. This is an entirely unoccupied design space.[^1]

2. **Pedagogical / learning metadata.** No format carries finger-placement hints, typing-course lesson groupings, difficulty ratings, ergonomic annotations, or mnemonic associations. The closest analogy is Keyman's `welcome.htm` documentation, which is prose, not structured metadata.

3. **AI/language-assistant typing knowledge.** No format carries estimated typing cost, n-gram frequency weights, swipe gesture probability models, or autocorrect training signals at the per-key or per-sequence level. These are entirely new data dimensions.

4. **Device / control-surface exports.** Only KLFC exports to TMK firmware. No tool exports to QMK/ZMK JSON (for custom mechanical keyboards), VIA JSON, MIDI controller mappings, or stream deck configurations. These are adjacent but distinct use cases — and all involve the physical key-to-action mapping concept generalized beyond text input.[^12]

5. **Human-maintainable JSON source that fans out to ALL targets including LDML.** This is the structural gap: the closest JSON-source tools are KLFC (last updated 2021, no LDML output) and the web component layer of kalamine. A maintained, JSON-schema-validated, LDML-output-capable source format does not currently exist.

6. **Single-file cross-platform source with LDML as a first-class compilation target.** kbdgen explicitly lists CLDR output as "in the pipeline"; Keyman is adding it; but neither currently provides a user-maintained JSON source that cleanly round-trips to and from LDML 3.0.[^5][^8]

### Step 2: Comparison Against the Project's Hypothesis

The project hypothesizes that the under-served areas are: **(a) dynamic legends, (b) learning/pedagogy metadata, (c) AI-assistant typing knowledge, (d) device/control-surface exports, (e) a single human-maintainable source that fans out to all targets including LDML.**

**Agreement:**

- **(a) Dynamic legends** — **Agreed.** The evidence confirms this is entirely absent from all surveyed formats, including LDML. LDML's `<display>` is static and explicitly not designed for runtime-variable labels. This is a legitimate, unoccupied design space.

- **(b) Pedagogy/learning metadata** — **Agreed, with a caveat.** No format addresses this. However, the demand signal is narrow: this is primarily relevant for typing-tutor software and language education tools. A new format can add this as optional metadata without burdening implementations that do not need it — but it should be designed as a cleanly separable extension, not a core feature, to avoid scope creep.

- **(c) AI/assistant typing knowledge** — **Agreed, with a strong caveat.** This design space is real but poorly defined. "AI typing hints" can mean very different things: input prediction models (belong to the IME layer, explicitly out of scope for LDML and rightly so), per-key effort metrics (a legitimate ergonomic annotation), or training-corpus layout data (a data-pipeline concern). The format design should be precise about which of these it claims to address and resist scope inflation.

- **(d) Device/control-surface exports** — **Partially agreed.** The evidence confirms this gap, but it is arguably orthogonal to the keyboard layout format problem. A QMK/ZMK JSON or VIA keyboard definition is a firmware configuration (physical matrix → HID key code mapping), while a keyboard layout format is an HID key code → Unicode character mapping. Conflating these two layers risks confusing the format's audience. If the project's scope includes firmware-level mapping, it should be clearly separated from the language-input layer.

- **(e) Single human-maintainable JSON source fanning out to all targets including LDML** — **Agreed. This is the strongest and most defensible justification.** The evidence is clear: KLFC provides the closest analogy but is stale and has no LDML output. kbdgen is YAML-based and has no LDML output yet. The gap of a **maintained, JSON-schema-validated, LDML-output-capable authoring format** is real and well-evidenced.

**Partial disagreement / risk flags:**

- **Claim that LDML is insufficient for the core mapping layer.** This is where the risk of redundancy is highest. For base mapping, shift levels, AltGr, dead keys, and transforms for Latin-script layouts, LDML 3.0 is fully capable. A new JSON source format that re-implements these semantics in a non-LDML schema would create a parallel standard — potentially fragmenting the ecosystem rather than unifying it. The correct architecture is **delegation to LDML semantics**, not reinvention.

- **"Fans out to all targets including LDML" implies LDML is one output among many.** This framing carries the risk of treating LDML as optional. Given LDML's trajectory (Keyman 19 full CLDR support, vendor intake pipeline, GNOME usage), a design that cannot cleanly produce valid LDML 3.0 output for its core mapping data would be strategically shortsighted.

***

## 6. Recommendations for the New Open Model

### 6.1 What to Delegate to LDML (and Map To)

The new format should treat the following as **isomorphic to LDML 3.0**, meaning: the JSON source must have a 1:1 semantic mapping to LDML elements, and the build toolchain must be able to produce a valid LDML 3.0 XML file from the JSON source.

| JSON source concept | LDML 3.0 counterpart | Notes |
|---|---|---|
| Key definitions (id, output, long-press) | `<keys>` / `<key>` | Direct mapping |
| Layers / forms (hardware / touch) | `ayers form="...">` / `ayer>` | Map hardware form identifiers to LDML form names |
| Modifier levels | `modifiers=` on `ayer>` | JSON can use friendly names ("altgr", "shift+altgr") |
| Transform rules (dead keys, contextual) | `<transforms>` / `<transform>` | Do not invent a new transform language |
| Reorder rules | `<reorder>` | Complex; consider restricting to pass-through to LDML syntax |
| Markers / variables | `\m{...}`, `<variables>` | Use LDML marker syntax in JSON string fields |
| Display legend overrides (static) | `<displays>` / `<display>` | Direct mapping |
| Locale / multi-locale | `keyboard/@locale`, `ocales>` | BCP 47 identifiers |
| Import / modularization | `<import>` | JSON `$ref` or similar for modular composition |
| Normalization intent | `info/@normalization` | JSON metadata field |
| Test data | `<keyboardTest>` | JSON array of keystroke/expect pairs |

**What NOT to reinvent:** the transform language, the reorder weight model, the marker mechanism, the Unicode-set syntax. These are the most complex parts of LDML and re-implementing them in JSON would create a semantically equivalent but syntactically different standard — the definition of redundancy.

### 6.2 What the Higher-Level JSON Layer Can Legitimately Add

The following capabilities are **absent from LDML and all surveyed tools** and represent the legitimate design space for a new open model:

**1. Dynamic legend specification.** A new `displayRules` section (or a `displayMode` concept) that allows per-key display overrides that are conditional on named display modes (e.g., `"mode": "default"`, `"mode": "mnemonic"`, `"mode": "phonetic"`, `"mode": "learning"`). Each mode supplies a `display` string for a key. Implementations that do not understand modes use the default mode. This is a clean extension with no LDML equivalent.

**2. Pedagogical metadata.** An optional `pedagogy` section per key or per layout allowing:
- `fingerHint`: which finger to use (index, middle, ring, pinkie, thumb, left/right)
- `lesson`: which typing-course lesson introduces this key
- `difficulty`: a relative typing-effort score
- `mnemonic`: a short human-readable association string (useful for memory-based layouts)

**3. AI/assistant metadata (scoped).** An optional `inputModel` section at the layout level for:
- `keyEffortWeights`: per-key relative effort metrics (for optimization tools)
- `ngramFrequencySource`: a reference to a language corpus used for layout evaluation
- Explicitly **not** autocorrect or prediction data — those belong to the IME / language model layer that LDML itself excludes.

**4. Export target declarations.** A `targets` array specifying which platform formats the build toolchain should produce: `["ldml", "xkb", "klc", "keylayout", "ahk", "kbdgen", "ios", "android"]`. This is the "fan-out" capability missing from all current formats. LDML is one target; the JSON source is the single authoritative input.

**5. Human-diff-friendly JSON conventions.** JSON Schema validation (not just a parser-enforced schema), deterministic key ordering, and split-file inclusion (e.g., separate `transforms.json`, `layers.json`) for large layouts.

**6. Device / control-surface metadata (as a separate extension namespace).** If the project scope includes QMK/ZMK/VIA targets, these should be modeled as a clearly separated `"physicalMapping"` extension namespace, distinct from the Unicode text-input layer. Mixing HID-level matrix mapping with Unicode character mapping in the same schema level would be an architectural error.

### 6.3 Architecture Summary

```
[JSON source file]  ←  human-authored, diff-friendly, JSON Schema validated
        │
        ├── core/  →  LDML 3.0 XML  →  platform consumers (Android, iOS, ChromeOS, etc.)
        │              (base map, layers, transforms, reorder, markers, display, locale, tests)
        │
        ├── extended/  →  kalamine .toml  (Linux/Win/macOS Latin-script targets)
        │               →  kbdgen .kbdgen  (full cross-platform mobile targets)
        │               →  Keyman .kmn  (complex-script targets)
        │               →  XKB / KLC / keylayout  (native OS formats)
        │
        └── metadata/  →  NOT exported to any platform format
                         (dynamic legends, pedagogy, AI hints)
                         consumed only by learning tools, AI assistants, visualization tools
```

### 6.4 Explicit Redundancy Warnings

The following design choices would create **direct redundancy with LDML** and should be avoided:

- Defining a new transform rule language instead of adopting LDML's regex-subset syntax.
- Defining a new reorder weight system instead of wrapping LDML's `<reorder>` attributes.
- Defining a new marker mechanism instead of using LDML's `\m{name}` convention.
- Claiming to replace LDML as the interchange standard rather than compiling to it.
- Defining a new Unicode-set matching syntax instead of adopting UnicodeSet/UTS#18 notation.

The new format's value proposition is **source ergonomics + metadata extension**, not a new semantics for text transformation. Every byte of transform logic in the JSON source should map cleanly to LDML XML.

***

## Appendix: Limitations of This Survey

- kbdgen documentation is sparse; the "in development" CLDR output target could not be inspected in detail. The YAML project format's full schema is not publicly documented beyond examples.[^8]
- CLDR Keyboard 3.0 is still under active development (Technical Preview as of CLDR 45/46). Some element names and attributes are expected to change before finalization.[^31][^1]
- Keyman's LDML implementation (v17–18) is partial; v19 targets completion. The degree of LDML semantic completeness in compiled `.kmx` outputs was not fully verifiable from public documentation.[^5]
- KbdEdit internals are proprietary; capabilities are documented only from public marketing and changelog materials.
- The "device/control-surface" gap (QMK/ZMK/VIA) was assessed based on architectural analysis; no systematic survey of firmware-level keyboard tools (QMK, ZMK, KMK) was conducted, as these are outside the stated scope of the new format.

---

## References

1. [[PDF] Unicode Locale Data Markup Language (LDML) Part 7: Keyboards](https://www.unicode.org/review/pri476/spec/tr35-keyboards.pdf) - Allow platforms to be able to use CLDR keyboard data for the character-emitting keys (non-frame) asp...

2. [[PDF] CLDR Keyboards Subcommittee LDML (UTS#35) Part 7 - Unicode](https://www.unicode.org/L2/L2023/23180-pri476-background.pdf)

3. [Keyboard Intake Procedures in CLDR - Unicode CLDR Project](https://cldr.unicode.org/index/process/keyboard-repository-process)

4. [LDML Keyboard Editor Window](https://help.keyman.com/developer/current-version/context/ldml-editor)

5. [Keyman Roadmap – May 2025](https://blog.keyman.com/2025/05/keyman-roadmap-may-2025/) - epic/web-core The Keyman Core Web interface allows us to support CLDR keyboards on mobile and tablet...

6. [@keymanapp/kmc-ldml](https://www.npmjs.com/package/@keymanapp/kmc-ldml?activeTab=versions) - Keyman Developer LDML keyboard compiler. Latest version: 18.0.238, last published: a month ago. Star...

7. [Projects/Caribou/NewLayout – GNOME Wiki Archive](https://wiki.gnome.org/Projects/Caribou/NewLayout) - ... CLDR repository provides an extensive set of keyboard layouts used in platforms including Androi...

8. [divvun/kbdgen: The next iteration of a Rust keyboard layout generator](https://github.com/divvun/kbdgen) - A tool to build keyboard packages for a multitude of platforms using a single, simple text file defi...

9. [specs/ldml/tr35.html - platform/external/cldr - Git at Google](https://android.googlesource.com/platform/external/cldr/+/1217fc9d64a5d30a7c29beb05fecb076eb124ffb/specs/ldml/tr35.html) - keyboard element must have a value that corresponds to the file. name, such as <keyboard locale="af-...

10. [OneDeadKey/kalamine: Keyboard Layout Maker - GitHub](https://github.com/OneDeadKey/kalamine) - A text-based, cross-platform Keyboard Layout Maker. Install To install kalamine, all you need is a P...

11. [kalamine/docs/klc.md at main · OneDeadKey/kalamine](https://github.com/OneDeadKey/kalamine/blob/main/docs/klc.md) - Keyboard Layout Maker. Contribute to OneDeadKey/kalamine development by creating an account on GitHu...

12. [nick-gravgaard/qwerty-flip - GitHub](https://github.com/nick-gravgaard/qwerty-flip) - It reads the included GB and US QWERTY JSON files (derived from this), moves the keys to create QWER...

13. [Keyman Keyboard Language](https://help.keyman.com/developer/language/)

14. [Keyman Keyboard Language Reference](https://help.keyman.com/developer/language/reference/)

15. [keyman-touch-layout files](https://help.keyman.com/developer/current-version/reference/file-types/keyman-touch-layout) - A .keyman-touch-layout file is a JSON format file that describes a keyboard layout for touch devices...

16. [deadkey](https://help.keyman.com/developer/language/reference/deadkey)

17. [Techniques for Complex Script Keyboards – Visual Input Order](https://blog.keyman.com/2011/02/techniques-for-complex-script-keyboards-visual-input-order/) - A few days ago I was assisting a Tamil customer with a Unicode keyboard they had designed which used...

18. [Keyman Developer 18.0 Features](https://keyman.com/en/developer/features) - Keyman Developer 18 supports every version of Windows since Windows 7. These keyboards can also be r...

19. [Layout Specifications](https://help.keyman.com/developer/engine/web/current-version/reference/layoutspec)

20. [Unicode support](https://help.keyman.com/developer/language/guide/unicode)

21. [&targets - Keyman Support](https://help.keyman.com/developer/language/reference/targets) - Currently, the compile targets can be broken down into two categories: .kmx file: A binary keyboard ...

22. [Keyman -- get involved!](https://www.youtube.com/watch?v=UZ_lKqRlEBE) - Keyman is an open source project providing support for typing in thousands of languages around the w...

23. [The Best Keyboard Layout Editor For all current Windows versions](http://www.kbdedit.com) - Keyboard Layout Editor For Windows 10, 8, 7, Vista, XP and 2003 (32- and 64-bit)

24. [Linux: How to make your own keyboard layout - Florin Lipan](https://lipanski.com/posts/custom-keyboard-layout) - Layouts are contained within the /usr/share/X11/xkb/symbols directory. Let's start by copying the Ro...

25. [Keyboard File Types - Hugh & Becky Paterson Curriculum Vitae](https://hughandbecky.us/Hugh-CV/post/keyboard-file-types/) - This post attempts to list various kinds of keyboard layout files, and specifications. If someone wa...

26. [macOS keybinding, Karabiner-Elements](http://xahlee.info/kbd/Karabiner-Elements.html) - Karabiner-Elements (was known as KeyRemap4MacBook in 2014) lets you do advanced key remapping. Downl...

27. [Use more complex modifications - Karabiner-Elements - pqrs.org](https://karabiner-elements.pqrs.org/docs/manual/configuration/configure-complex-modifications/) - Karabiner-Elements provides more complex event modifications. These rules change keys by conditions....

28. [espanso - openshovelshack](https://openshovelshack.com/tools/espanso) - At it's core, text expansion is just replacing something you type with something else - usually this...

29. [Espanso - A Privacy-first, Cross-platform Text Expander](https://espanso.org) - Tired of typing the same sentences over and over? Discover the incredible power of a full-blown text...

30. [Step 8: Deadkeys](https://help.keyman.com/developer/8.0/docs/tutorial_keyboard_8)

31. [unicode-org/cldr release-45-alpha2 on GitHub - NewReleases.io](https://newreleases.io/project/github/unicode-org/cldr/release/release-45-alpha2) - What's Changed (since alpha1) ; CLDR-17144 Disable all CLDRModify -f except -fQ/-fP/-fV by @btangmu ...

