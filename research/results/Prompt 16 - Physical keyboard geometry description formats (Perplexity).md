# Keyboard Physical Geometry Formats: A Technical Survey for an Open Layout Model

## Executive Summary

Five major formats describe the physical geometry of keyboards: the de-facto hobbyist format KLE JSON, QMK's `info.json` layout object, VIA/Vial keyboard definitions (which embed KLE JSON), the ISO/IEC 9995-1 reference grid, and XKB's `xkb_geometry` component. Each encodes physical key positions and shapes from a different vantage point — pixel-level visual rendering, firmware compilation, runtime remapping, normative standardization, and OS-level symbol dispatch — and none is fully adequate on its own as a geometry layer for an open, tool-interoperable layout model. This report surveys each format in depth, identifies where they agree and disagree, and derives a concrete recommendation for the open layout model's geometry layer.

**Geometry is kept strictly separate from mapping throughout this document.** A physical key's position, size, and rotation are geometry facts. The character or function assigned to that key is a mapping fact.

***

## 1. KLE JSON — The De-Facto Hobbyist Format

### 1.1 Overview and Coordinate Model

Keyboard Layout Editor (keyboard-layout-editor.com, "KLE") uses a serialized JSON format that has become the universal interchange currency between hobbyist keyboard design tools. The format represents a keyboard as a JSON array. The first element (optional) is a metadata object; every subsequent element is a row array containing alternating property objects and key-label strings.[^1]

The coordinate unit is **1u**, where 1u equals the edge length of a standard square keycap (typically 19.05 mm in physical space, though KLE does not encode physical dimensions directly). The origin is the top-left corner of the keyboard. `x` and `y` express the absolute position of the **top-left corner of each key** within the layout space, measured in key units. Within a row, `x` advances automatically by the key's width unless overridden.[^1]

**The format is stateful and differential.** Property objects in a row establish state that persists for all subsequent keys in that row (and some state persists across rows). For example, setting `{"w": 2}` before a key applies width 2u to that key only if the next key resets it, but the property object merges with the running state object. This statefulness is a core source of parsing bugs in third-party implementations.[^1]

The canonical parsing library, `kle-serial` (MIT-licensed, by the same author as KLE), is the reference implementation. It deserializes the raw rows into a `Keyboard` object containing a flat `keys: Key[]` array, where every key carries fully resolved, absolute properties — making each key stateless in the deserialized form.[^1]

### 1.2 Per-Key Properties

Each deserialized `Key` object carries:[^1]

- **`x`, `y`** — absolute top-left position in key units
- **`width`, `height`** — key size in key units (default 1.0 × 1.0)
- **`x2`, `y2`, `width2`, `height2`** — secondary rectangle for oddly-shaped keys (ISO Enter, Big-ass Enter, stepped keys); position is **relative** to (`x`, `y`)
- **`rotation_x`, `rotation_y`** — the center of rotation in absolute key-unit coordinates
- **`rotation_angle`** — clockwise rotation angle in degrees
- **`stepped`** — boolean indicating a stepped key
- **`nub`** — boolean indicating a homing nub/bump/dish
- **`decal`** — render labels only, no keycap border
- **`ghost`** — render semi-transparently (placeholder key)
- **`labels`** — array of up to 12 HTML strings (the legends)
- **`textColor`**, **`textSize`** — per-legend color and relative size (1–9)
- **`profile`** — keycap profile and row string, e.g. `"DCS R3"`
- **`sm`, `sb`, `st`** — switch mount, brand, type

### 1.3 Rotation Model

Rotation is applied about the explicit center `(rotation_x, rotation_y)` in the global coordinate frame, not about the key's own center. This means all keys in a rotational cluster (e.g., an ergonomic thumb arc) share the same `rotation_x`/`rotation_y` center. The angle is always specified clockwise in degrees.[^1]

**Known quirk:** In the raw JSON serialization, `rx`/`ry` (rotation center) reset `x`/`y` to the rotation center coordinates when they first appear in a row. This is one of the most frequently misimplemented aspects of the format. The `kle-serial` reference library handles it correctly; many independent parsers do not.[^1]

### 1.4 Stepped and Secondary-Rectangle Keys

The `stepped` flag combined with `(x2, y2, width2, height2)` handles the two-rectangle key model. For a stepped key, the main rectangle is the upper (visible, cap-bearing) part and the second rectangle is the larger lower part that contains the actual switch. For ISO Enter and "Big-ass Enter", two rectangles combine to form the L-shape; the union of the two overlapping rectangles defines the final shape.[^1]

**No polygon shapes** are supported natively in KLE; all shapes are derived from the union of two rectangles. Arbitrary polygons are supported only in QMK's `info.json` (see Section 2).

### 1.5 Legends and Label Placement

Up to 12 label positions map onto a 4×3 grid (rows × columns) on the keycap face:[^1]

```
[top-left]    [top-center]    [top-right]
[center-left] [center-center] [center-right]
[bottom-left] [bottom-center] [bottom-right]
[front-left]  [front-center]  [front-right]
```

Label slots 9–11 (front row) represent the keycap's front face, used in some profiles (e.g. SA) for legends on the front. The content of each label slot is **not assigned any semantic meaning** by KLE itself — it is pure display text. VIA/Vial repurpose specific label slots for matrix coordinates and layout option codes (see Section 3).

### 1.6 Known Limitations

1. **No stable key identity.** KLE has no concept of a persistent key identifier; keys are identified only by their order in the flat key array.
2. **Statefulness causes parsing complexity.** The differential row encoding is compact but error-prone.
3. **No matrix encoding.** KLE is purely about physical geometry and appearance; it has no notion of the electrical matrix.
4. **Label slots carry semantic overloading.** Tools like VIA hijack specific label slots (top-left for `row,col`; bottom-right for `option,choice`) that KLE itself treats as purely cosmetic.
5. **No machine-readable form-factor or variant concept.** There is no built-in mechanism to say "this key exists only in the ISO variant".
6. **No native polygon shapes.** ISO Enter must be approximated by two overlapping rectangles.
7. **Physical dimensions absent.** The 1u unit is abstract; no binding to millimeters is specified.

***

## 2. QMK `info.json` — Firmware Geometry and Matrix Binding

### 2.1 Overview

QMK's `info.json` is the canonical configuration file for keyboards in the QMK firmware ecosystem. It serves multiple purposes simultaneously: hardware pin configuration, feature flags, and — crucially — the physical layout representation used by QMK Configurator and the QMK API. Layout data lives under the top-level `"layouts"` key.[^2][^3]

### 2.2 Layout Format and Key Dictionary

The `"layouts"` object is keyed by layout macro names (e.g., `"LAYOUT_60_ansi"`, `"LAYOUT_iso"`). Each layout contains a `"layout"` array of **key dictionaries**. Unlike KLE, every key dictionary is **stateless** — it does not inherit from previous keys.[^3][^2]

Each key dictionary supports:[^2][^3]

| Property | Type | Meaning |
|---|---|---|
| `x` | float | **Required.** Absolute x position, top-left of key, in key units |
| `y` | float | **Required.** Absolute y position, top-left of key, in key units |
| `w` | float | Width in key units (default 1.0) |
| `h` | float | Height in key units (default 1.0) |
| `r` | float | Clockwise rotation in degrees |
| `rx` | float | Rotation center x (absolute; default = `x`) |
| `ry` | float | Rotation center y (absolute; default = `y`) |
| `ks` | array | Key shape polygon; list of `[x, y]` pairs **relative to key top-left** |
| `matrix` | `[row, col]` | Electrical matrix position — the critical addition over KLE |
| `label` | string | Human-readable name for the key position (e.g. `"Shift"`) |
| `hand` | string | `"L"`, `"R"`, or `"*"` for split keyboards |

**The `matrix` field is the fundamental addition** that KLE lacks. It binds each geometrically-described key to a specific electrical matrix intersection, resolving the physical-to-firmware mapping.[^2]

**The `ks` (key shape) polygon** is a major advance over KLE's two-rectangle model. It allows arbitrary polygon outlines, specified as `[x, y]` points relative to the key's top-left. The ISO Enter example in the docs is `[[0,0],[1.5,0],[1.5,2],[0.25,2],[0.25,1],[0,1],[0,0]]`.[^2]

### 2.3 Layout Macro Naming and Form-Factor Variants

QMK's approach to form-factor variants is to **enumerate each variant as a separate named layout macro**. A keyboard supporting both ANSI and ISO would have `"LAYOUT_60_ansi"` and `"LAYOUT_60_iso"` as separate entries in `"layouts"`, each with its own key dictionary array. Community layouts (shared standard macros like `"LAYOUT_60_ansi"`) allow different keyboards to share a common layout definition.[^4][^3]

This approach is explicit and flexible but verbose — common keys must be duplicated across variants rather than described once with a "present-in-variant-X" flag.

### 2.4 Relationship to KLE

The QMK documentation explicitly states that `info.json` key properties were designed to mirror KLE concepts, with the key difference being statefulness — QMK is stateless per key, KLE is stateful. A community-maintained converter at `qmk.fm/converter` transforms KLE raw data into a draft `info.json` layout, then the developer adds `matrix` coordinates and adjusts as needed.[^4][^2]

**The ISO Enter is handled differently:** QMK represents it as a 1.25u × 2u key (using `w` and `h`) rather than two rectangles. This is a simplification — renderers are expected to display it as the canonical ISO shape without explicit polygon data unless `ks` is provided.[^3]

### 2.5 Non-Character Keys

QMK `info.json` places all physically-present keys in the layout array regardless of their character-producing nature. Function keys (F1–F24), navigation cluster keys, media keys, and even the Fn key on a compact keyboard are all represented geometrically in the same way. The `label` field provides a human-readable hint; the `matrix` field binds to firmware. The key's actual assignment (HID code, QMK keycode, layer action) lives in the keymap — separate from `info.json`.[^2]

### 2.6 Known Limitations

1. **No stable cross-layout key identity.** Matrix coordinates serve as a key identifier within a single layout, but the same physical key may have different matrix positions in different variant layouts.
2. **Variants require full layout duplication.** There is no "delta" mechanism; ANSI and ISO Enter must be described in separate layout arrays.
3. **Label is cosmetic, not normative.** There is no binding to XKB names or USB HID usages.
4. **Rotation model inherited from KLE quirks.** The same `rx`/`ry` semantics apply, including the reset behavior.
5. **No concept of physically-present-but-unmapped keys** (e.g., Fn key on keyboards where Fn is handled purely in hardware and never sends a HID report).

***

## 3. VIA / Vial Keyboard Definitions

### 3.1 Overview

VIA and Vial are runtime remapping systems for QMK-based keyboards. A keyboard definition file (JSON) must be provided to VIA/Vial to identify the keyboard and describe its physical layout. VIA's definition format is documented at caniusevia.com.[^5]

### 3.2 Physical Layout: KLE JSON Embedded

VIA does **not** define its own coordinate system. Instead, it embeds KLE JSON directly under `layouts.keymap`:[^5]

```json
{
  "name": "Macropad",
  "vendorId": "0x5241",
  "productId": "0x1234",
  "matrix": {"rows": 1, "cols": 6},
  "layouts": {
    "keymap": [
      [{"c": "#505557", "t": "#d9d7d7", "a": 7}, "0,0", "0,1", "0,2"],
      ["0,3", "0,4", "0,5"]
    ]
  }
}
```

The `matrix` top-level property defines the PCB's switch matrix dimensions (must match `MATRIX_ROWS`/`MATRIX_COLS` in QMK firmware). The `keymap` property is literally the KLE raw-data JSON.[^6][^5]

### 3.3 Matrix Coordinate Encoding in KLE Labels

VIA repurposes KLE label slots for non-cosmetic data:[^6]

- **Top-left legend** — `"row,col"` string (e.g. `"3,5"`) specifying the electrical matrix position for this key
- **Bottom-right legend** — `"option,choice"` string (e.g. `"0,1"`) specifying layout option membership

This is a semantic overloading of KLE's cosmetic label system. The strings are parsed by VIA; they do not appear as visible keycap legends.

### 3.4 Layout Options (Variant Keys)

VIA's layout option system is the most sophisticated among the formats surveyed for handling ANSI/ISO/split-spacebar/etc. variants. A `labels` array names each option:[^6]

```json
"labels": [
  "Split Backspace",
  "ISO Enter",
  "Split Left Shift",
  "Split Right Shift",
  ["Bottom Row", "ANSI", "7U", "HHKB", "WKL"]
]
```

- A string entry → toggle (off = choice 0, on = choice 1)
- A string-array entry → dropdown select (first item is the label, rest are choices)

All variant keys live in the same KLE `keymap` array alongside the default keys. The `option,choice` bottom-right legend tags each variant key. VIA computes the bounding box from the default layout; variant choices must occupy the exact same bounding box area.[^6]

**Constraints documented by VIA:**
- Do not use stepped keys in VIA KLE[^6]
- Rotated keys are allowed but layout options for rotated keys are not supported[^6]
- Each layout option choice must cover the same area as the default for that option[^6]

### 3.5 Vial Extensions

Vial (a superset of VIA) adds support for rotary encoders in the KLE JSON via a center-label convention (`e0`, `e1`, etc.) and extends the feature set (tap-dance, combo support, etc.) while maintaining VIA-compatible definition format. The physical layout encoding is identical to VIA.[^7]

### 3.6 Non-Character Keys

In VIA/Vial, **every switch that is wired to the matrix must appear in the `keymap`** with a `row,col` top-left legend. The Fn key, if it is a matrix switch, appears as a regular key with appropriate coordinates. If the Fn key is handled purely in hardware firmware without a matrix position, it cannot be represented.[^6]

### 3.7 Known Limitations

1. **Physical geometry is entirely inherited from KLE**, including all KLE limitations (statefulness, two-rectangle shapes, no stable key IDs).
2. **Matrix coordinates embedded in cosmetic label slots** — semantic overloading that is fragile and non-obvious.
3. **Cannot represent rotated variant keys** in layout options.
4. **No polygon shape support** (inherits KLE limitation).
5. **No binding to XKB names or USB HID usages** — VIA's layer 0 keycode assignment is done through VIA's own keycode registry, not through the geometry definition.

***

## 4. ISO/IEC 9995-1 Reference Grid

### 4.1 Overview

ISO/IEC 9995-1 is the normative international standard governing keyboard layout principles. The most recent edition is ISO/IEC 9995-1:2026, published January 2026, superseding the 2009 edition. The standard defines physical sections, zones, and a key numbering system — but **does not specify a coordinate system or physical dimensions**.[^8][^9][^10][^11][^12]

### 4.2 Physical Sections and Zones

The standard divides a keyboard into four sections:[^9][^12]

- **Alphanumeric section** (zones ZA0–ZA4): the main key cluster
- **Editing and function section** (zones ZE0–ZE2 and ZF0–ZF4): cursor keys, Escape, F-keys
- **Numeric section** (zones ZN0–ZN6): the numpad

### 4.3 The Reference Grid

The reference grid is the standard's key identity system. Keys are identified by a **row letter** and **two-digit column number**:[^13][^12]

- **Row A** = the spacebar row (reference row for the alphanumeric, editing, and numeric sections)
- **Row B** = one above Row A (where Z, X, C, V, B... are on QWERTY)
- **Row C** = home row (A, S, D, F...)
- **Row D** = top letter row (Q, W, E, R, T...)
- **Row E** = number row (1, 2, 3...)
- **Row K** = function key row (reference row for F-keys)
- Rows below Row A (rare): Z, Y, X...
- **Column 01** = the column containing the digit "1" key in the alphanumeric section; columns number left-to-right from there[^12]
- Column 00 = key to the left of "1" (the `` ` ``/`~` key on ANSI keyboards)
- Columns to the left of 00 number 99, 98, 97...

The XKB symbolic key names (`<AE01>`, `<AC01>`, `<AD01>`) follow the same convention:[^14]

| ISO 9995-1 Grid ID | XKB Name | Typical ANSI key |
|---|---|---|
| E00 | `<TLDE>` | `` ` ~ `` |
| E01 | `<AE01>` | `1 !` |
| E02 | `<AE02>` | `2 @` |
| ... | ... | ... |
| D01 | `<AD01>` | `Q` |
| C01 | `<AC01>` | `A` |
| B01 | `<AB01>` | `Z` |
| A00 (spacebar spans A04–A06+) | `<SPCE>` | Space |

The two-letter prefix encodes the section (`A`=alphanumeric zone) and the row letter (`E`, `D`, `C`, `B`, `A`), followed by the two-digit column number.[^14][^13]

### 4.4 Form-Factor Variants

The 2026 edition of ISO/IEC 9995-2 codifies six named key arrangements:[^9]

| Arrangement | Common Name | Graphic keys | Key differences |
|---|---|---|---|
| **A** | ANSI | 48 | Uses D13 for the 48th key; single-row Enter; `\|` above Enter |
| **L** | (Asian alt-101) | 48 | Uses E13 (enabling a taller Enter) instead of D13 |
| **K** | Korean | 48+2 | Key arrangement L plus two mode keys flanking the spacebar |
| **E** | ISO | 49 | Adds C12 and B00 (`\|` next to Left Shift); wide Enter spanning C and D rows |
| **B** | ABNT (Brazil) | 50 | Adds B11 (`Ç`) in addition to E arrangement |
| **J** | JIS (Japan) | 49 | E00 is a function key; B11 added; three IME keys flank the spacebar |

The critical ANSI/ISO difference: ISO adds the `IntlBackslash` key at B00 (position to the left of Z) and the `Backslash` key at C12 (between `'` and Enter), while removing the separate `\|` key above Enter and shrinking Backspace slightly[^15].

### 4.5 Non-Character Keys in the Grid

ISO 9995-1 assigns all keys including function keys, Fn, and navigation keys to grid positions:[^13][^12]

- Escape: **K00** (leftmost in the function key row)
- F1–F12: **K01–K12** (function row)
- Fn: Row A or B, left of spacebar (standard says left of Alt if present)[^9]
- Numpad keys: Column 51 onward in the numeric section
- Navigation cluster (Insert, Home, PgUp, Delete, End, PgDn): editing section zones ZE1–ZE2
- Arrow keys: editing section zone ZE0, Row A level (cursor down aligned with spacebar row)[^9]

### 4.6 Known Limitations

1. **Not a machine-readable coordinate format.** No `x`, `y`, `w`, `h` — only relative row/column grid position.
2. **Does not specify key dimensions or gaps.** Absolute physical dimensions are deferred to ISO 9241-4.
3. **Grid is angled (staggered) by convention but the angle is not specified.** The standard explicitly says it expresses no preference for angled vs. square grids.[^12]
4. **Column numbers don't directly encode physical position** for staggered keyboards because the stagger offset varies per row.

***

## 5. XKB Geometry Component

### 5.1 Overview

The X Keyboard Extension (XKB) includes a `geometry` component among its five main components (keycodes, types, symbols, geometry, compatibility). XKB geometry describes the **physical appearance** of the keyboard — key shapes, positions, sections, indicator LEDs, and decorative elements — in a bespoke text format.[^16][^14]

The `xkb_geometry` file is widely acknowledged as "the most complex and most useless part of XKB" for typical use. It was designed to allow tools like `xkbprint` to render a visual keyboard diagram. It is **not used for input processing** — XKB uses keycodes and symbols components for that. As a result, geometry files are often absent or incorrect in practice.[^17][^14]

### 5.2 Coordinate System and Units

All coordinates in XKB geometry are in **millimeters** (multiples of 1 mm). The coordinate origin is the top-left of the keyboard. Coordinates increase rightward and downward. This is the only format among those surveyed that natively works in physical millimeters.[^14]

The total keyboard dimensions are declared at the top level (`width=` and `height=` in mm).[^14]

### 5.3 Shapes

A **shape** is a named polygon defined as one or more **outlines** (closed polygon paths). The interpretation depends on the outline's point count:[^14]

- **1 point** → box from (0,0) to the given point
- **2 points** → box from first to second point
- **3+ points** → arbitrary closed polygon with vertices at each coordinate

Example from a `pc101` geometry file:[^14]
```
shape "NORM" {
    { [18,18] },
    { [2,1], [16,16] }
};
```
This defines a two-outline shape (for rendering a key with an inset keycap face): outer boundary 18×18 mm, inner face starting at (2,1), size 16×16 mm.

Shapes are referenced by name (e.g., `"NORM"`, `"SPCE"`, `"LFSH"`, `"RTRN"` for ISO Enter) from key definitions.

### 5.4 Sections, Rows, and Keys

The geometry is organized hierarchically:[^14]

- **Section** (e.g., `"Function"`, `"Alpha"`, `"Editing"`, `"Numpad"`) — has `top`, `left`, `width`, `height`, `angle` in mm
- **Row** within a section — has `top` and `left` offsets *relative to the section*
- **Key** within a row — identified by its **XKB keycode name** (e.g., `<ESC>`, `<AE01>`, `<AC01>`), with optional `gap` (spacing before key in mm), `shape` name, and `color`

Key positions are implicit: the first key in a row starts at the row's left offset, and each subsequent key immediately follows the previous unless a `gap` is specified. The key's size comes from its named shape.

### 5.5 Doodads

Non-key decorative elements are **doodads**:[^18][^14]

- **solid** — a filled shape (e.g., LED panel)
- **indicator** — an LED (e.g., NumLock, CapsLock)
- **outline** — a border shape
- **text** — a text label
- **logo** — a logo graphic

Doodads are the mechanism for representing physically-present but OS-invisible elements like LED indicators.

### 5.6 XKB Keycode Names as Physical Key Identifiers

XKB keycode names — `<TLDE>`, `<AE01>`...`<AE12>`, `<AD01>`...`<AD12>`, `<AC01>`...`<AC12>`, `<AB01>`...`<AB11>`, `<SPCE>` for the alpha cluster, plus section-specific names (`<ESC>`, `<FK01>`...`<FK24>`, `<NMLK>`, `<KP0>`...`<KP9>`, etc.) — are position-based symbolic names assigned in `xkb_keycodes` files. The two-letter part (AE, AD, AC, AB) corresponds to the ISO 9995-1 grid rows D, C, B, A (offset by one letter in practice: XKB's `AE` = ISO row E, `AD` = row D, `AC` = row C, `AB` = row B).[^14]

### 5.7 Known Limitations

1. **Almost never populated in practice.** Modern Linux systems omit or barely maintain geometry files; xkeyboard-config includes them for few models.[^17]
2. **Completely separate from input processing.** Geometry is irrelevant to XKB's runtime key handling.
3. **No machine-friendly tooling.** The format is custom text with C-like syntax, not JSON or YAML.
4. **Units in mm** — excellent for physical design but mismatched with all other formats using 1u.
5. **Tool `xkbprint-kle`** (Albert-S-Briscoe, 2022) converts XKB geometry to KLE JSON, demonstrating the format's CAD-like nature but also its obscurity.[^17]

***

## 6. Cross-Format Comparison Table

| Aspect | KLE JSON | QMK `info.json` | VIA / Vial | XKB Geometry | ISO/IEC 9995-1 Grid |
|---|---|---|---|---|---|
| **Coordinate / units model** | Key units (1u = standard keycap); origin top-left; stateful differential rows | Key units; origin top-left; stateless per-key absolute | Embeds KLE JSON verbatim; inherits KLE coordinates | Millimeters; origin top-left; section→row→key hierarchy | Logical grid: row letter + 2-digit column; no coordinates |
| **Rotation / odd shapes?** | Rotation about explicit center (rx,ry); shapes via two overlapping rectangles; no native polygon | Same rotation model; polygon shapes via `ks` array | Same as KLE; rotation in options not supported | Arbitrary polygon outlines per named shape; section-level angle | N/A — no coordinate geometry |
| **Encodes matrix?** | No | Yes — `"matrix": [row, col]` per key | Yes — `"row,col"` in top-left KLE label slot | No (XKB uses keycodes component, not geometry) | No |
| **Form-factor / variant handling** | No built-in variant concept; tools extend externally | Separate named layout macros per variant (LAYOUT_60_ansi, LAYOUT_60_iso, …) | Layout options system: `option,choice` in bottom-right KLE label; labels array names options | Separate geometry variant files (e.g., `pc101`, `pc102`) | Named key arrangements (A=ANSI, E=ISO, B=ABNT, J=JIS, …); normative but not machine-readable |
| **Legend / label placement** | Up to 12 positions in a 4×3 grid (top/center/bottom × L/C/R + front row); HTML content; cosmetic only | `label` field: single human-readable string; no multi-legend | Inherits KLE labels; top-left and bottom-right slots semantically overloaded for matrix and option data | Text doodads: placed at absolute mm coordinates; not per-key labels | Not specified (refers to ISO 9995-7 for symbols) |
| **Tooling / ecosystem** | KLE website; kle-serial npm library; Blender importer; xkbprint-kle output; nearly every keyboard CAD tool accepts KLE export | QMK firmware; QMK Configurator; QMK API; keymap-drawer; wide IDE support | VIA and Vial remapping apps; the-via/keyboards GitHub repo | libxkbcommon (consumed but geometry not used); xkbprint; xkbprint-kle converter | ISO standard documents (paid); referenced by W3C UIEvents-code, XKB naming |

***

## 7. Physical Key Identity Across Schemes

Mapping the same physical key across all five systems is a central challenge. The table below shows the ANSI `Q` key as an example:

| Scheme | Identity for ANSI "Q" key |
|---|---|
| ISO/IEC 9995-1 | D01 |
| XKB keycode name | `<AD01>` |
| USB HID Usage | 0x07 0x0014 (Keyboard q and Q) |
| W3C UIEvents `code` | `"KeyQ"` |
| KLE JSON | Position in the flat key array (no stable name) |
| QMK `info.json` | `matrix: [2, 1]` (keyboard-specific); `label: "Q"` (informational) |
| VIA/Vial | Top-left KLE label: `"2,1"` (keyboard-specific) |
| XKB geometry | Section row key name `<AD01>` |

**Cross-scheme reconciliation rules:**

1. **ISO grid IDs ↔ XKB names:** The mapping is near-bijective. XKB row prefixes (`AE`=row E, `AD`=row D, `AC`=row C, `AB`=row B) correspond directly to ISO 9995-1 rows. The convention is: XKB prefix = "A" + ISO row letter.[^13][^14]

2. **XKB names ↔ W3C UIEvents `code`:** The W3C specification explicitly bases `code` values on USB HID positions and acknowledges alignment with ISO 9995-1 row letters. The mapping is not alphabetically literal (`<AD01>` → `"KeyQ"` on QWERTY), but the W3C spec's row labeling (E=top, D, C, B, A=spacebar) directly mirrors ISO 9995-1.[^15]

3. **W3C `code` ↔ USB HID usages:** Chromium's `usb_keycode_map.h` documents the explicit mapping between USB HID Usage Page 0x07 usage IDs and both XKB scancodes and `code` values. For example, HID 0x070014 = KeyQ = XKB scancode 0x0018.[^19][^20]

4. **QMK/VIA matrix ↔ everything else:** The matrix `[row, col]` pair is keyboard-specific and not globally meaningful. It must be mapped to a physical position through the `x, y` coordinates in `info.json`, which can then be cross-referenced to ISO grid IDs or `code` values via spatial proximity.

5. **KLE ↔ everything:** KLE has no stable key identity. The only reliable approach is positional matching: resolve the KLE key's absolute `(x, y)` and match it against known positions on a reference layout.

**Special cases:**

- **`IntlBackslash` (ISO B00):** Present in ISO/E/ABNT/JIS arrangements; absent in ANSI. USB HID 0x070064; W3C code `"IntlBackslash"`; XKB `<LSGT>`. KLE represents it with an explicit key entry at approximately `x=0.0, y=3.0` in a 60% layout.
- **`IntlYen` (E13 in alternate-101/JIS):** USB HID 0x070089; W3C code `"IntlYen"`; XKB `<AE13>`.
- **`IntlRo` (B11 in JIS/ABNT):** USB HID 0x070087; W3C code `"IntlRo"`; XKB `<AB11>`.
- **`Fn` key:** Hardware-handled on most compact keyboards. W3C code `"Fn"` (not Required); no USB HID usage assigned (handled in-firmware, never reported to OS); XKB `<I237>` or firmware-specific; no ISO grid position defined normatively. In QMK/VIA, if wired to the matrix, it has a matrix position like any other key.

***

## 8. Non-Character Keys Across Formats

All surveyed formats treat non-character keys (F1–F12, numpad, navigation, media, Fn) as geometrically equivalent to character keys. Their physical geometry description — position, size, rotation — uses the same mechanisms. Only the **identity** and **assignment** differs.

| Key class | KLE | QMK info.json | VIA | XKB geometry | ISO 9995-1 |
|---|---|---|---|---|---|
| **F1–F12** | Placed in layout; label = "F1" etc. | In layout array; `label: "F1"` | In KLE keymap with matrix coords | Named `<FK01>`–`<FK12>` in section `"Function"` | K01–K12 |
| **Numpad** | Placed in layout; label = digit/op | In layout array with matrix | In KLE keymap | Named `<KP0>`–`<KP9>` etc. in `"Numpad"` section | Column 51+ in numeric section |
| **Navigation** (Ins, Del, Home, End, PgUp, PgDn) | Placed in layout | In layout array | In KLE keymap | Named `<INS>`, `<DELE>`, etc. in `"Editing"` section | Editing section ZE1–ZE2 |
| **Media keys** | Placed; label cosmetic | In layout array | In KLE keymap | Usually absent (doodads only) | Not covered by standard |
| **Fn key** | Placed if designer chooses | In layout array if matrix-wired | In KLE keymap if matrix-wired | Not standardly represented | Row A, left of Alt |
| **LED indicators** | `decal: true` or cosmetic key | Not representable in layout | Not representable | `indicator` doodad (named, positioned) | Not covered |

**Key gap:** No format except XKB geometry (via doodads) can cleanly represent **physically-present-but-OS-invisible elements** like hardware LEDs or an Fn key that never sends a HID report. An open layout model must add an explicit mechanism for this.

***

## 9. Implications for an Open Layout Model

### 9.1 Recommended Geometry Representation

Based on the survey, the following geometry layer is recommended. It is designed to be **hand-maintainable** (human-readable JSON/YAML), **losslessly roundtrippable** to KLE and QMK `info.json`, and extensible for ISO/XKB identity and non-character keys.

#### 9.1.1 Units and Origin

Use **key units (1u)** for all coordinates. The origin is the top-left corner of the bounding box of the entire physical keyboard. 1u is defined as the nominal grid pitch of standard keycaps; when physical dimensions are needed, annotate at the layout metadata level (`u_mm: 19.05` for MX, `u_mm: 18` for Alps, etc.). This matches KLE and QMK exactly and avoids the mm/1u impedance mismatch with XKB.

#### 9.1.2 Per-Key Geometry Object

Each key in the `keys` array is **fully stateless** (following QMK, not KLE):

```yaml
keys:
  - id: "AD01"          # stable physical key ID (see §9.1.5)
    x: 1.5              # absolute top-left x in key units
    y: 1.0              # absolute top-left y in key units
    w: 1.0              # width (default 1.0)
    h: 1.0              # height (default 1.0)
    r: 0                # clockwise rotation in degrees (default 0)
    rx: null            # rotation center x (null = key center)
    ry: null            # rotation center y (null = key center)
    shape: null         # null = rectangle; or polygon [[x,y],...] rel. to key top-left
    variant: null       # null = always present; or "iso" / "ansi" / ...
    physical: true      # true = normal; false = ghost/placeholder
    visible: true       # true = OS-visible; false = hardware-only (Fn, LED)
    label: "Q"          # human-readable hint (informational only)
```

**Rotation center convention:** Default the rotation center to the **key's own center** (`rx = x + w/2`, `ry = y + h/2`) rather than the top-left corner. This is more intuitive than KLE/QMK's "first key in cluster" convention and avoids the reset quirk. When exporting to KLE/QMK, compute the explicit `rx`/`ry` from the key center.

#### 9.1.3 Odd Shapes

Support polygon shapes via `shape: [[x,y],...]` with coordinates **relative to the key's top-left**, matching QMK's `ks` format. This enables ISO Enter, JIS Enter, Big-ass Enter, and novelty shapes. For the KLE export path, approximate with two overlapping rectangles using `x2/y2/w2/h2`.[^2]

#### 9.1.4 Variant Keys (ANSI/ISO/JIS Differences)

Adopt a mechanism similar to VIA's layout options but bound to form-factor names rather than numeric indices. Each key has an optional `variant` field:

- `null` or absent → key is present in all variants
- `"ansi"` → present only in ANSI arrangement
- `"iso"` → present only in ISO arrangement
- `"jis"` → present only in JIS arrangement
- `"abnt"` → present only in ABNT arrangement
- An array `["ansi", "iso"]` → present in both

The model declares which variants it supports at the layout level (`variants: ["ansi", "iso"]`). A validator can then enforce completeness — that the same physical area is covered by each variant's keys. This is more explicit than QMK's approach (duplicating entire layout macros) and more semantically clear than VIA's numeric `option,choice` tags.

For export to QMK: emit one `LAYOUT_<variant>` macro per declared variant. For export to VIA: emit layout options using the `option,choice` convention with the variant name as the label.

#### 9.1.5 Stable Physical Key IDs

Assign **ISO 9995-1 grid IDs** (E00, E01...E13, D00...D13, C00...C12, B00...B12, A00 for spacebar, K00 for Escape, K01...K12 for F-keys, numpad-specific IDs, navigation-specific IDs) as the canonical stable physical key identifier. These are:[^12][^13]

- Geometry-independent (no x/y required to identify a key)
- Already used in XKB keycode names
- Mapped to W3C UIEvents `code` values and USB HID usages
- Human-readable in context

For keys outside the ISO 9995-1 scheme (media keys, encoder knobs, custom macro keys), define an `ext:` prefix namespace (e.g., `ext:encoder0`, `ext:media_play`).

**Fn keys** that are matrix-wired get regular IDs per their physical position. Fn keys that are hardware-only get an `ext:fn` ID with `visible: false`.

#### 9.1.6 Export to Existing Formats

| Target | Notes |
|---|---|
| **KLE JSON** | Serialize as stateful row arrays; compute `x2/y2/w2/h2` from polygon; place matrix in top-left label, option in bottom-right label for VIA compatibility; add metadata object |
| **QMK `info.json`** | Emit stateless key dicts; use `ks` for polygon shapes; emit separate layout objects per variant; add `matrix` from the physical→electrical binding layer (not the geometry layer) |
| **VIA/Vial** | Emit KLE JSON with `row,col` top-left legend; emit `labels` array from variant names; encode `option,choice` bottom-right legend; respect VIA KLE constraints (no stepped keys, no rotated variants) |
| **XKB geometry** | Emit sections grouped by ISO 9995-1 section; convert 1u to mm using `u_mm`; name keys by XKB `<XXNN>` codes derived from ISO 9995-1 IDs; emit polygon shapes as XKB outlines |

#### 9.1.7 ANSI/ISO/JIS/ABNT Differences — Reconciliation Strategy

The key geometric differences between the major form factors are:

1. **B00 (`IntlBackslash`, ISO/E arrangement):** `x = 0.0`, `y = 3.0`, `w = 1.0`, `h = 1.0`, `variant: ["iso", "abnt", "jis"]`
2. **ANSI Enter (D13, 2.25u × 1u) vs. ISO Enter (C13+D13, 1.25u × 2u L-shape):** The ISO Enter is best described as a polygon shape `[[0,0],[1.25,0],[1.25,2],[0,2],[0,1],[-0.25,1],[-0.25,0],[0,0]]` relative to its anchor at row C col 13. Mark with `variant: "iso"`.
3. **ANSI Backslash above Enter (D13):** `w: 1.5`, `variant: "ansi"`.
4. **JIS space cluster:** Three IME keys (NonConvert, space, Convert + KanaMode) replace the single ANSI spacebar. Each key has explicit `w` values; all tagged `variant: "jis"`.
5. **ABNT `IntlRo` (B11):** Additional key between `/` and Right Shift; `variant: ["abnt", "jis"]`.

For a layout model that only needs to support ANSI and ISO, the minimal additional keys are B00 (`IntlBackslash`) and the differently-shaped Enter. All other keys share positions.

***

## 10. Open Issues and Edge Cases

### 10.1 Keycap Profile Data

Keycap profile (SA, DSA, DCS, OEM, Cherry, etc.) affects legend placement (row-dependent slope angles, legend area size) but is purely visual. KLE encodes profile per key in the `profile` field (`"DCS R3"`). The open model should treat profile as a rendering hint, not geometry. The profile name and row classification should be an optional per-key annotation.[^1]

### 10.2 Split Keyboards

Split keyboard halves are geometrically independent keyboards. The open model should allow a `split: true` flag at the layout level and permit two disconnected coordinate spaces to coexist in one layout definition. QMK uses `hand: "L"/"R"` per key; the open model can adopt the same convention.[^3]

### 10.3 Encoders and Non-Switch Input Devices

Rotary encoders, trackballs, and touch pads are physically present but not keys. The open model should support a `type: "encoder" | "trackball" | "touchpad" | "switch"` per physical element, with the same geometry fields applicable where relevant (encoders have a position and size).

### 10.4 Matrix-Less and Direct-Pin Keyboards

Some custom keyboards wire each switch directly to a microcontroller pin, bypassing a traditional matrix. QMK supports `matrix_pins.direct` for this. The geometry layer is unaffected; the electrical binding layer must accommodate it.[^3]

### 10.5 Physical vs. Logical Key Count Mismatch

On some keyboards, two physically adjacent keys share a single matrix position (wired in parallel). This is common in split-backspace designs where the wide backspace and its two split halves may share matrix wiring. The geometry model must allow multiple physical key entries with the same matrix coordinates.

***

## 11. Conclusion

The five formats surveyed cover complementary aspects of keyboard physical geometry: KLE JSON excels at compact, visual, hobbyist-friendly description; QMK `info.json` adds firmware-binding matrix coordinates and polygon shapes; VIA/Vial extend QMK's model with runtime variant switching; ISO/IEC 9995-1 provides a normative, geometry-agnostic key naming grid; XKB geometry adds millimeter-precise physical layout but is practically unused. None is sufficient alone.

The recommended open layout model geometry layer should use 1u key units, stateless per-key objects with absolute coordinates, ISO 9995-1 grid IDs as stable key identifiers, optional polygon shapes, a variant tagging system for ANSI/ISO/JIS/ABNT differences, and explicit handling of hardware-only (OS-invisible) keys. This design maps losslessly to KLE JSON and QMK `info.json` for export, aligns with XKB keycode names for cross-platform identity, and grounds all physical key IDs in the normative ISO 9995-1 reference while remaining hand-maintainable.

---

## References

1. [ijprest/kle-serial: Serialization library for keyboard-layout-editor.com](https://github.com/ijprest/kle-serial) - This is a MIT-licensed javascript library for parsing the serialized format used on keyboard-layout-...

2. [qmk-firmware/docs/reference_info_json.md at master · samhocevar-forks/qmk-firmware](https://github.com/samhocevar/fork-qmk-firmware/blob/master/docs/reference_info_json.md) - Open-source keyboard firmware for Atmel AVR and Arm USB families - samhocevar-forks/qmk-firmware

3. [info.json Reference](https://docs.qmk.fm/reference_info_json) - Documentation for QMK Firmware

4. [Supporting Your Keyboard in QMK Configurator](https://docs.qmk.fm/reference_configurator_support) - To build the JSON file, the easiest way is to build the layout in Keyboard Layout Editor ("KLE"), fr...

5. [Specification - VIA](https://caniusevia.com/docs/specification/) - In order for VIA to configure a keyboard, it requires a definition of the keyboard - the physical la...

6. [Layouts - VIA](https://www.caniusevia.com/docs/layouts/) - Overview

7. [Build support 1 - Create JSON - Vial](https://get.vial.today/docs/porting-to-via.html) - The first step for creating a Vial port is to prepare a keyboard definition which is a JSON file des...

8. [ISO/IEC 9995-1:2009](https://www.iso.org/standard/51645.html) - Information technology — Keyboard layouts for text and office systems — Part 1: General principles g...

9. [ISO/IEC 9995 - Wikipedia](https://en.wikipedia.org/wiki/ISO/IEC_9995)

10. [Part 1: General principles governing keyboard layouts ISO ...](https://www.sis.se/produkter/informationsteknik-kontorsutrustning/terminalutrustning-och-ovrig-kringutrustning/isoiec-9995-12026/) - Information technology — Keyboard layouts for text and office systems — Part 1: General principles g...

11. [SIST ISO/IEC 9995-1:1995 - Information technology - iTeh Standards](https://standards.iteh.ai/catalog/standards/sist/e47891c1-c000-42e9-84fa-af39fbbd12b0/sist-iso-iec-9995-1-1995) - SIST ISO/IEC 9995-1:1995 - Specifies various characteristics of keyboards. Identifies the sections o...

12. [Keyboard layouts for text and office systems <P> General principles ...](https://www.unicode.org/L2/Historical/EdHart-X3L2-Arch-2004-02-12/ISO09995/Copy%20of%20ISO%209995-1%20Principles.html)

13. [Re: Keyboard layouts (ISO 9995)](https://www.unicode.org/mail-arch/unicode-ml/Archives-Old/UML018/0213.html)

14. [XKB Configuration Files - charvolant.org](https://www.charvolant.org/doug/xkb/html/node5.html) - The section beginning with solid "LedPanel" draws a solid area of colour. A solid is an example of a...

15. [UI Events KeyboardEvent code Values](https://www.w3.org/TR/uievents-code/)

16. [3. Direct XKB Configuration](https://www.x.org/releases/X11R7.0/doc/html/XKB-Config3.html)

17. [Albert-S-Briscoe/xkbprint-kle: Convert XKB geometry to a ... - GitHub](https://github.com/Albert-S-Briscoe/xkbprint-kle) - XKB has an extremely obscure format for configuring a physical layout, which is the geometry section...

18. [The X Keyboard Extension:](https://www.x.org/releases/X11R7.7-RC1/doc/libX11/XKB/xkblib.html) - Keyboard Geometry. Keyboard geometry describes the physical appearance of the keyboard, including th...

19. [Git at Google](https://chromium.googlesource.com/chromium/chromium/+/master/ui/base/keycodes/usb_keycode_map.h)

20. [USB HID keycode table + JSON, extracted from HID Usage Tables v1.21](https://gist.github.com/mildsunrise/4e231346e2078f440969cdefb6d4caa3) - USB HID keycode table + JSON, extracted from HID Usage Tables v1.21 - hid_keycodes.md

