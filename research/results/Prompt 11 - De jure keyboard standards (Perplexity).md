# Formal Keyboard Standards: A Catalog for Open Layout Model Design

**Prepared for:** Engineers designing an open keyboard layout model  
**Purpose:** Map the de jure standards landscape — international and national — so the model can adopt established vocabulary, enable conformance claims, and avoid re-inventing standardized concepts.  
**Note on access:** Most ISO, DIN, JIS, and AFNOR documents are paywalled. Normative content is cited from official abstracts, publicly available sample PDFs, and authoritative secondary sources (Wikipedia's ISO/IEC 9995 article, which is closely maintained by contributors to the standards themselves, JTC1/SC35 documents, and per-standard bibliographic records). Where the source is a secondary account of a normative requirement, this is noted.

***

## 1. ISO/IEC 9995 — The International Framework

### 1.1 Overview and Governance

ISO/IEC 9995, titled *Information technology — Keyboard layouts for text and office systems*, is the foundational international standard series governing keyboard layout principles. It is prepared by the joint technical committee **ISO/IEC JTC 1/SC 35** (User interfaces) and was first published in 1994, with a significant major revision published across 2025–2026. Crucially, ISO/IEC 9995 does **not** define specific national layouts; it provides a framework — a vocabulary of sections, zones, levels, and groups — that national bodies use to define their own layouts. The series is normatively hierarchical: ISO/IEC 9995-1 is the umbrella document and all other parts explicitly operate "within the general scope described in ISO/IEC 9995-1."[^1][^2][^3][^4]

The 2025–2026 revision is the most comprehensive update since the series' inception. Parts 1, 2, 3, 4, 9, 10, and 11 were all republished in that cycle.[^2]

### 1.2 Multipart Structure (Current Editions as of Early 2026)

| Part | Title | Current Edition | Primary Scope |
|------|-------|-----------------|---------------|
| **9995-1** | General principles governing keyboard layouts | 2026 | Definitions, physical sections/zones, key reference grid and numbering, keytop labeling conventions |
| **9995-2** | Alphanumeric section | 2026 | Key count, zone arrangement, function keys, level/group selectors, allocation guidelines for Latin scripts |
| **9995-3** | Latin International keyboard layout | 2026 (completely rewritten from 2010) | A complete specific layout for Latin script; predecessor edition (2010) defined the "common secondary group" |
| **9995-4** | Numeric section | 2025 | Layout of the numeric keypad: 1-2-3 vs. 7-8-9 arrangement, arithmetic symbols |
| **9995-5** | Editing and function section | 2009 | Escape key placement at K00; cursor key cross/inverted-T arrangement |
| **9995-6** | *(Function section — withdrawn 2009)* | — | Content absorbed into 9995-5 |
| **9995-7** | Symbols used to represent functions | 2009 + Amd.1:2012 (revision CD in progress as of 2026) | Graphical symbols for function keys (Esc, Alt, Tab, Return, etc.) — the keycap legend standard |
| **9995-8** | Allocation of letters to the keys of a numeric keypad | 2009 | Assigns A–Z to numeric keypad keys per ITU-T E.161 |
| **9995-9** | Groups and mechanisms for multilingual and multiscript input | 2026 | IPA Special Selector, Superselect key, multiscript group switching |
| **9995-10** | Conventional symbols for graphic characters not uniquely recognizable by glyph | 2025 | Disambiguation symbols on keytops (e.g., em-dash vs. en-dash), representation of diacritics on dead keys |
| **9995-11** | Functionality and labelling of dead keys | 2026 | Dead-key behavior (press-release-then-base), peculiar characters, superscript/subscript via dead keys, labeling rectangles |
| **9995-12** | Keyboard group selection | 2020 | Dynamic group switching mechanism for multi-script environments |

[^4][^2]

Parts 9995-5, 9995-8, and 9995-12 were unaffected by the 2025–2026 revision.[^2]

### 1.3 ISO/IEC 9995-1 in Depth

#### 1.3.1 Physical Sections and Zones

ISO/IEC 9995-1 divides the keyboard **physically** into three **sections**, each subdivided into **zones**:[^4]

- **Alphanumeric section**
  - *Alphanumeric zone (ZA0)*: the primary character-entry keys (the "main block")
  - *Function zones (left and right)*: modifier and control keys flanking the main block
- **Numeric section** (optional — may be placed right or left of the alphanumeric section)
  - *Numeric zone*: digit and arithmetic keys
  - *Function zone*: the numeric section's control keys
- **Editing and function section**: everything else — including:
  - *Cursor key zone*: arrow keys
  - *Editing function zone*: Insert, Delete, Home, End, Page Up/Down, and similar

The standard does not require all sections to be present; compact keyboards (e.g., 60% or tenkeyless) remain conformant by simply omitting sections.[^4]

#### 1.3.2 The Key Reference Grid and Key Numbering System

ISO/IEC 9995-1 specifies a **coordinate-based key reference grid** that uniquely identifies every key position on any keyboard, regardless of physical size. This is a normative element of 9995-1 and is the preferred vocabulary for designating physical key positions in conformant documents.[^5][^4]

**Row identifiers (letters)** run from the bottom up in the alphanumeric section:
- **Row A**: space bar row (bottommost)
- **Row B**: lower letter row (Z/X/C/… in QWERTY)
- **Row C**: home row (A/S/D/… in QWERTY)
- **Row D**: upper letter row (Q/W/E/… in QWERTY)
- **Row E**: digit row (1/2/3/…)
- Rows above E are labelled **K, L, M…** (function/escape row)
- Rows below A are labelled **Z, Y, X…** downwards

**Column identifiers (two-digit numbers)** run left to right within the alphanumeric section, starting at 00 for the leftmost key in that row. Columns for editing or function keys placed beyond a right-side numeric section start at 60; those placed left of the alphanumeric section count down from 80.

A key is therefore designated by the combination of its row letter and column number. Examples:
- **E01**: the "1" digit key on most QWERTY layouts
- **D01**: the "Q" key on QWERTY
- **C00**: the Caps Lock key position
- **B99**: the left Shift key position
- **K00**: the Escape key position (per 9995-5)[^4]

This grid is entirely physical — it says nothing about which character is mapped to a position, which is the role of the layout standard.

#### 1.3.3 Logical Division: Levels and Groups

ISO/IEC 9995-1 introduces the two-axis **logical model** for character access (normatively detailed in 9995-2):[^6]

**Levels** are the lower-level axis, selected by *level-select* (qualifier) keys:
- **Level 1** (default/unshifted): primary characters, e.g., lowercase letters
- **Level 2** (shifted): secondary characters, e.g., uppercase letters
- **Level 3** (AltGr): tertiary characters accessible via a Level 3 Select key (AltGr)
- **Level 4** (Shift+AltGr): quaternary characters; the 2026 edition permits up to four levels but recommends Level 4 only for obscure characters, as simultaneous three-key actuation is ergonomically problematic[^2]

**Groups** are the higher-level axis, selected by a *group-select* mechanism:
- **Group 1** (primary): the default group for a given layout
- **Group 2** (secondary): an alternate character set accessed via a group-select key or Shift+AltGr combination; may be labeled "extra characters" when it supplements rather than replaces the primary group
- Additional groups are possible (e.g., for third/fourth scripts)[^4]

Within each group, up to four levels may be defined. The hierarchy is: Group → Level. The "default" state is Group 1, Level 1.[^6]

#### 1.3.4 Keytop Labeling Conventions

ISO/IEC 9995-1:2026 specifies three formally named keytop labeling schemes:[^2]

1. **Columnar placement**: Level axis = row position (Level 2 above Level 1; Level 3 below Level 1); Group axis = column position (Group 1 at left edge, Group 2 at right edge)
2. **Group-1-priorized placement**: for single-group layouts, Level 3 may occupy the lower-right corner; for two-group layouts, Group 2 occupies the upper-right quadrant
3. **Level-4-including placement**: for layouts where Level 3/4 characters are mostly case-paired letters (e.g., US-International)

### 1.4 ISO/IEC 9995-2 in Depth

9995-2 is the normative specification for the **alphanumeric section**. Key normative requirements include:[^3][^7]

- Minimum 47 graphic keys in the alphanumeric zone, including the space bar
- Rows E, D, C, B must meet minimum key counts at specified column positions (e.g., ≥12 keys in row E at E00–E15)
- Position D00: Tab key; C00: Caps Lock (or Level 2 Lock, or Generalized Lock); B99: left Shift; one Return key right of character keys in row C
- Layouts for Latin script must include all 26 basic letters A–Z, digits 0–9, and specified ISO 646 characters including `#` and `@` (added in 2026 edition)[^2]

9995-2 also defines the **"harmonized 48–50 graphic key keyboard arrangement"** — a narrower specification identifying six named physical key arrangements (informative annex in the 2026 edition):[^2]
- **Key arrangement A**: 48 graphic keys, uses D13 for 48th key → standard "ANSI" physical form
- **Key arrangement E**: 49 graphic keys, uses C12 and B00 → standard "ISO" physical form (conformant with NF Z71-300 and DIN 2137-01)
- **Key arrangement J**: 49 graphic keys, with E00 as function key and extra IME keys → Japanese physical form
- **Key arrangement B**: 50 graphic keys → Brazilian ABNT2 physical form[^2]

### 1.5 ISO/IEC 9995-3: From Common Secondary Group to Latin International

The 2026 edition completely changed the purpose of 9995-3. The predecessor (2010) defined a **common secondary group** — a fixed overlay accessible via group-select, providing European and indigenous-language Latin characters on top of any existing national layout. The 2026 edition replaces this entirely with the **"Latin International" keyboard layout** — a complete standalone layout (not an overlay) that uses AltGr, an Extra Selector key, an IPA Special Selector, and a Superselect key to provide broad multilingual Latin coverage.[^8][^9][^10][^4][^2]

### 1.6 ISO/IEC 9995-7: Symbols for Control Functions (Keycap Legends)

ISO/IEC 9995-7:2009 (Amendment 1: 2012) specifies a set of **graphical symbols** for representing control functions on keycaps. Each symbol is intended to be language-independent — a universal icon rather than a text label. Examples include the symbols for Escape, Tab, Caps Lock, Shift, Return, Backspace, Delete, Insert, and group/level select functions. As of 2026, a full revision of 9995-7 is under development as a Committee Draft.[^11][^12][^13][^4]

The symbols are intended for use on physical keycap engravings or prints. Some have been encoded as Unicode code points; others have been proposed but deferred.[^4]

### 1.7 ISO/IEC 9995-10: Disambiguation Symbols

9995-10:2025 specifies symbols to uniquely identify characters on keytops that are visually ambiguous in practice (e.g., em-dash vs. en-dash, and various diacritic representations on dead keys). This is the secondary graphic standard complementing 9995-7.[^2]

### 1.8 ISO/IEC 9995-11: Dead Keys

9995-11:2026 defines the **functionality** (press-then-release dead key, then base character) and **labeling** (narrow rectangles indicating diacritic position) of dead keys. It covers: precomposed characters per Unicode, dead-key-then-space for spacing variants, superscript/subscript via circumflex/caron on digits, and the "peculiar characters" mechanism for combinations yielding mathematical or technical symbols.[^14][^15][^2]

### 1.9 Conformance Framework

ISO/IEC 9995-1 contains a normative **conformance clause** (Clause 2):[^6]

- A keyboard **conforms to ISO/IEC 9995-1** if it meets clauses 5–9 of that part. Not all sections/zones need be implemented depending on the keyboard's intended purpose (e.g., a tenkeyless board omits the numeric section).
- A keyboard **claiming conformance with the ISO/IEC 9995 series** must, at minimum, conform to 9995-1 *and* all other parts relevant to that keyboard model.
- Any conformance claim **must list** the specific parts claimed (e.g., "conforms to ISO/IEC 9995-1:2026 and ISO/IEC 9995-2:2026").
- Conformance with 9995-7 (symbols) or 9995-8 (numeric keypad letters) does **not** require conformance with any other part.[^6]

***

## 2. National and Regional De Jure Standards

### 2.1 France — AFNOR NF Z71-300 (2019)

| Attribute | Detail |
|-----------|--------|
| **Designator** | NF Z71-300 |
| **Issuing body** | AFNOR (Association française de normalisation) |
| **Edition/year** | April 2019 |
| **Full title** | *Interfaces utilisateurs — Dispositions de clavier bureautique français* |
| **Status** | Voluntary (norme volontaire) |
| **Physical key form** | Key arrangement E (ISO physical — 49 graphic keys) |

NF Z71-300 was developed at the request of the French Ministry of Culture's DGLFLF and published after a public consultation in 2019. It normatively defines **two** complete keyboard layouts for French:[^16][^17][^18][^19]
1. An improved **AZERTY** layout: preserves the main alphabetic block but repositions symbols, adds accented capitals (É, Ç, Æ, Œ, etc.), guillemets, typographic dashes, and dead keys for European languages and Greek
2. The **BÉPO** layout: an ergonomic alternative designed for touch-typing, with a completely rearranged character set

The standard explicitly references ISO/IEC 9995 as its normative framework. NF Z71-300 is voluntary — manufacturers are not legally required to adopt it — but Windows 11 (version 24H2) implements the NF Z71-300 AZERTY layout natively. The improved AZERTY was designed using computational optimization algorithms and is designed to cover all French orthographic requirements as well as all EU Latin languages.[^20][^21]

### 2.2 Germany — DIN 2137

| Attribute | Detail |
|-----------|--------|
| **Designator** | DIN 2137-1 (Part 1: layout) / DIN 2137-2 (Part 2, 2018) |
| **Issuing body** | DIN (Deutsches Institut für Normung) |
| **Current edition** | DIN 2137-01:2023-08 (Part 1, August 2023); DIN 2137-2:2018-12 (Part 2) |
| **Physical key form** | E1 variant uses Key arrangement E (ISO physical); E2 variant uses Key arrangement A (ANSI physical) |

DIN 2137 is the German keyboard standard, first published in 1976 and substantially revised in 2018 and again in 2023. The current edition defines **three** layouts:[^22][^23][^24]

- **T1**: The legacy standard QWERTZ layout used on virtually all German keyboards for decades. Retained in the 2023 edition for backward compatibility; now described as a "partially labeled E1" keyboard
- **E1** ("Erweiterte Tastaturbelegung 1"): An extended layout that enables entry of all letters and diacritical marks used in world primary official languages (Latin script), European minority languages, EU punctuation, and transliterations of Arabic (per DIN 31635), Chinese (Pinyin), Hebrew (DIN 31636), Russian (DIN 1460), and Sanskrit (IAST). Uses Key arrangement E (ISO physical). Supported natively in Windows 11 24H2 as "Deutsch erweitert (E1)"[^25][^24]
- **E2**: A variant of E1 adapted for ANSI-physical keyboards (Key arrangement A), lacking the extra key at B00[^22][^25]

The 2012 edition's T2 ("Europatastatur") and T3 layouts have been deprecated and are no longer part of the current standard. DIN 2137 explicitly references ISO/IEC 9995 as its normative basis.[^26][^27][^24]

### 2.3 Japan — JIS X 6002 (and JIS X 6004)

| Attribute | Detail |
|-----------|--------|
| **Designator** | JIS X 6002:1980 (current: reaffirmed 2024) |
| **Issuing body** | JSA (Japanese Standards Association, operating under JISC — Japanese Industrial Standards Committee) |
| **Edition/year** | JIS X 6002: originally April 1980 (reaffirmed October 2024); JIS X 6004: 1986, **withdrawn** March 1999 |
| **Physical key form** | "JIS physical" — Key arrangement J (ISO 9995-2:2026 nomenclature): extra function keys flanking short space bar |

**JIS X 6002:1980** (*Keyboard layout for information processing using the JIS 7-bit coded character set*) specifies the relative key arrangement for two-handed information-processing keyboards using the JIS X 0201 (ASCII + Katakana) 7-bit coded character set. The standard covers character key placement; it **explicitly excludes** physical dimensions (key spacing, tilt, keytop dimensions). The standard specifies 48 graphic character keys arranged over four rows, covering 26 uppercase and 26 lowercase Latin letters, 55 Katakana characters, decimal digits, and special characters. The JIS physical form is characterized by a narrow space bar with Muhenkan, Henkan, and Katakana/Hiragana/Romaji keys flanking it, a vertical/L-shaped Return key, and a narrow Backspace.[^28][^29][^30]

JIS X 6002 has a related international document, ISO 2530:1975. The OADG 109/109A keyboard used on most Japanese PCs conforms to JIS X 6002 for its character key arrangement.[^31][^32]

**JIS X 6004:1986** defined an improved kana layout (the "New JIS keyboard") designed to improve kana direct input by reducing it from four rows to three. It was withdrawn in 1999 due to lack of adoption.[^33][^31]

### 2.4 USA — ANSI INCITS 154

| Attribute | Detail |
|-----------|--------|
| **Designator** | ANSI INCITS 154 (also written INCITS 154) |
| **Issuing body** | ANSI / INCITS (InterNational Committee for Information Technology Standards, formerly ANSI X3) |
| **Edition lineage** | ASA X4.7 (1966) → ANSI X4.14 (1971) → ANSI X4.23 (1982) → **ANSI X3.154 (1988)** → renumbered **ANSI INCITS 154 (2002 reaffirmation, no layout change)** |
| **Full title** | *Office Machines and Supplies — Alphanumeric Machines — Keyboard Arrangement* |
| **Physical key form** | Key arrangement A ("ANSI physical"): 48 graphic keys, wide left Shift, D13 as 48th key, horizontal Enter |

The lineage of the US standard begins with ASA X4.7 (1966), which standardized the Electric Typewriter Keyboard arrangement as IBM proposed it. ANSI X4.14 (1971) extended this for computers with the "Typewriter Pairing" arrangement based on the IBM Selectric, mapping 94 ASCII characters to 47 keys. The 1988 consolidation as ANSI X3.154 unified typewriter and computer keyboards, leaving certain key specifics (for vendor differences) normatively blank. In 2002, upon the reorganization of ANSI's IT standards body into INCITS, the standard was renumbered **ANSI INCITS 154** without any layout change.[^34][^35][^36]

The standard's scope is the **physical key arrangement** of the alphanumeric section, including key spacing (0.75-inch / 19 mm centers), key travel minimum (3.8 mm), and the arrangement of the alphanumeric keys. The US QWERTY character assignment is established by usage and tradition, not solely by this standard. ANSI INCITS 154 is considered conformant with ISO/IEC 9995-2 for Key arrangement A.[^36][^2]

### 2.5 Brazil — ABNT NBR 10346 (ABNT2)

| Attribute | Detail |
|-----------|--------|
| **Designator** | ABNT NBR 10346 variant 2 (alphanumeric); NBR 10347 (numeric) |
| **Issuing body** | ABNT (Associação Brasileira de Normas Técnicas) |
| **Physical key form** | Key arrangement B (ISO 9995-2:2026): 50 graphic keys, smaller right Shift, smaller numpad Plus |

The Brazilian ABNT2 standard specifies the physical layout used for Brazilian Portuguese keyboards. It adds a dedicated Ç key and uses the same ISO-style large Enter key as Key arrangement E, but also inserts a key on the right side of the bottom row (giving 50 graphic keys). ABNT2 is the dominant keyboard form in Brazil and is supported natively by all major OSes.[^37][^38]

### 2.6 Russia — GOST (Cyrillic ЙЦУКЕН)

| Attribute | Detail |
|-----------|--------|
| **Designator** | GOST 6431-90 (formerly GOST 6431-52, since 1953) |
| **Issuing body** | GOST (Gosstandart, now Rosstandart — Federal Agency on Technical Regulating and Metrology) |
| **Current status** | GOST 6431-90 is the keyboard standard used in Unix-like systems; the layout itself (ЙЦУКЕН) has been stable since the 1950s Soviet-era standardization |

The Russian ЙЦУКЕН layout was formalized in the USSR beginning with GOST 6431-52 (effective 1 July 1953), which standardized Cyrillic letter, number, and symbol positions for typewriters. The modern computer form is referenced as GOST 6431-90 in Unix/Linux XKB definitions. The layout is the overwhelming de facto and de jure standard for Cyrillic input in Russia and CIS countries. It uses an ISO physical form (Key arrangement E) with QWERTY for the Latin layer; the Cyrillic characters occupy the same physical positions across all platforms. A separate GOST series (GOST 16876, replaced by GOST 7.79-2000) covers transliteration, not keyboard layout.[^39]

### 2.7 Nordic Countries

There is no single "Nordic keyboard standard." Each country maintains its own national standard or adopts its layout through established national usage and OS vendor support:

- **Sweden/Finland**: QWERTY with Å, Ä, Ö — Swedish standard is defined by SIS (Swedish Standards Institute) and often referenced via EU harmonization
- **Denmark/Norway**: QWERTY with Æ, Ø, Å — similar but with Æ/Ø instead of Ä/Ö
- **Iceland**: QWERTY with Þ, Ð, Æ, Ö

All Nordic layouts use the ISO physical form (Key arrangement E). The layouts are largely handled through OS vendor keyboard definitions (Windows KBDDV, Linux XKB) rather than dedicated published national standards comparable to DIN 2137 or NF Z71-300.[^40][^41]

***

## 3. Standards Table

| Standard | Issuing Body | Scope | Key Concepts Defined | Current Edition/Year | Relationship to OS Layouts | Relationship to LDML |
|----------|-------------|-------|---------------------|---------------------|---------------------------|----------------------|
| **ISO/IEC 9995-1** | ISO/IEC JTC1/SC35 | General principles: physical sections, key grid, keytop labeling, conformance | Sections, zones, levels, groups, key reference grid, key numbering (E01, D01, etc.), keytop label positions | 2026 | Foundation for all OS keyboard models; XKB geometry uses 9995-1 grid implicitly | LDML explicitly cites ISO 9995-1:2009 for "base character = Group 1, Level 1"[^42] |
| **ISO/IEC 9995-2** | ISO/IEC JTC1/SC35 | Alphanumeric section: key counts, zone layout, function key positions, Latin character requirements | Alphanumeric zone, function zone, harmonized key arrangements (A/E/J/B), Level/Group selector placement | 2026 | Named key arrangements (A/E/J/B) map to ANSI/ISO/JIS/ABNT physical forms | LDML `<form>` element references physical arrangements; no normative mapping |
| **ISO/IEC 9995-3** | ISO/IEC JTC1/SC35 | Latin International keyboard layout (2026); predecessor: common secondary group | Latin International layout; (predecessor: secondary group, group selector, peculiar characters, dead key combinations) | 2026 (complete rewrite of 2010) | Implemented in some OS keyboard drivers; predecessor's CSA (Quebec) layout widely deployed | LDML does not reference 9995-3 directly; Latin International is a new layout |
| **ISO/IEC 9995-7** | ISO/IEC JTC1/SC35 | Graphical symbols for function key legends | Standardized glyphs for Esc, Tab, Shift, CapsLock, Return, Backspace, Del, AltGr, group-select, etc. | 2009 + Amd1:2012 (revision in progress) | Symbol set used in DIN 2137 and some OS keycap docs; not enforced by OS drivers | Out of LDML scope (LDML governs character output, not keycap graphics) |
| **ISO/IEC 9995-11** | ISO/IEC JTC1/SC35 | Dead key functionality and labeling | Dead key algorithm, precomposed character support, peculiar characters, diacritic rectangle labeling | 2026 | Windows KBD driver model constrains dead keys to precomposed Unicode (as noted in 9995-11:2026)[^2] | LDML `<transforms>` element handles dead key behavior independently |
| **ISO/IEC 9995-12** | ISO/IEC JTC1/SC35 | Keyboard group selection (dynamic, multi-script) | Superselect-based group switching | 2020 | No known OS implementations as of February 2026[^2] | Outside LDML scope |
| **AFNOR NF Z71-300** | AFNOR (France) | French keyboard layouts: improved AZERTY and BÉPO | Two specific layouts conforming to ISO/IEC 9995 framework | 2019 | Windows 11 24H2 includes NF Z71-300 AZERTY; macOS/Linux support via third-party drivers | LDML would represent it as `fr-t-k0-azerty-nfz71300` or similar locale tag |
| **DIN 2137-01** | DIN (Germany) | German keyboard layouts: T1, E1, E2 | T1 (legacy QWERTZ), E1 (extended ISO-physical), E2 (extended ANSI-physical); references DIN 31635, DIN 31636, DIN 1460 for transliterations | 2023-08 (Part 1); 2018-12 (Part 2) | Windows 11 24H2 includes E1 and E2; T1 = all legacy German keyboards | LDML represents layouts independently of DIN designation |
| **JIS X 6002** | JISC/JSA (Japan) | Keyboard arrangement for JIS 7-bit coded character set (Latin + Katakana) | Physical key arrangement for 48 graphic keys; Latin and Katakana character placement | 1980 (reaffirmed 2024) | All major Japanese OS keyboard drivers derive from JIS X 6002 | LDML `ja` keyboard file reflects JIS X 6002 character assignments |
| **ANSI INCITS 154** | ANSI/INCITS (USA) | Alphanumeric keyboard physical arrangement + US QWERTY character assignment | Key arrangement A physical form; 0.75-inch key centers; 3.8mm key travel minimum | 1988 (renumbered INCITS 154 in 2002, no layout change) | Directly defines US QWERTY physical form; all US Windows/Mac/Linux layouts derive from it | LDML `en-US` keyboard represents INCITS 154 character assignments |
| **ABNT NBR 10346** | ABNT (Brazil) | Brazilian Portuguese keyboard: ABNT2 physical form + character assignment | Key arrangement B; 50 graphic keys; dedicated Ç key | NBR 10346 var. 2 (current) | Implemented as KBDBR in Windows; standard pt-BR layout on all OSes | LDML `pt-BR` keyboard represents this layout |
| **GOST 6431-90** | Rosstandart (Russia) | Cyrillic ЙЦУКЕН keyboard layout for computers | Russian Cyrillic key arrangement; stable ЙЦУКЕН layout | 1990 (current) | XKB `ru` layout directly implements GOST 6431-90[^39]; Windows Russian layout | LDML `ru` keyboard reflects GOST 6431-90 character assignments |

***

## 4. Physical Form Factors: ANSI vs. ISO vs. JIS vs. ABNT

The colloquial terms "ANSI keyboard," "ISO keyboard," "JIS keyboard," and "ABNT keyboard" refer to distinct physical key arrangements standardized or referenced by those bodies. ISO/IEC 9995-2:2026 formalizes these as named key arrangements in its informative annex:[^29][^36][^2]

| Colloquial Name | ISO 9995-2:2026 Name | Key Count | Distinctive Features | Conformant National Standard(s) |
|----------------|---------------------|-----------|---------------------|----------------------------------|
| **ANSI** | Key arrangement A | 48 graphic keys | Wide horizontal Enter; wide left Shift (B99 extends to B00); backslash key at D13 | ANSI INCITS 154-1988 |
| **ISO** | Key arrangement E | 49 graphic keys | Tall L-shaped Enter; extra key at B00 (between left Shift and Z); narrower left Shift at B99 | NF Z71-300, DIN 2137-01 (E1 variant), most European national standards |
| **JIS** | Key arrangement J | 49 graphic keys (+ function keys) | E00 used as function key; E13/C12/B11 as graphic keys; narrow space bar with Muhenkan/Henkan/Kana keys | JIS X 6002 |
| **ABNT2** | Key arrangement B | 50 graphic keys | ISO form + extra key right of right Shift; smaller numpad Plus | ABNT NBR 10346 var. 2 |

[^37][^2]

Each arrangement is defined by which positions (per the ISO/IEC 9995-1 reference grid) carry graphic keys vs. function keys, and by the minimum sizes of specific keys (Shift, Enter, Space bar). Physical dimensions (pitch, travel, profile) are governed by ergonomics standards (ISO 9241-4) rather than 9995 itself.

***

## 5. Keycap Legend and Symbol Standards

### 5.1 ISO/IEC 9995-7: Standardized Function Symbols

ISO/IEC 9995-7:2009 (with Amendment 1:2012) defines a normative catalog of graphical symbols for function keys. Each symbol represents a control function in a language-independent graphical form. The standard covers symbols for:[^12][^11]

- **Navigation / editing**: Backspace, Delete, Insert, Home, End, Page Up/Down, cursor arrows
- **Mode/state**: Caps Lock, Shift Lock, Num Lock, Scroll Lock
- **Entry**: Tab, Return/Enter
- **Modifier**: Alternate (Alt), Control (Ctrl), Level 3 Select (AltGr symbol)
- **Group selection**: the group-select arrow symbol (⇨) and Extra Selector variants
- **Special**: Escape, Print Screen, Pause/Break, Function key Fn

Many of these symbols have been proposed for Unicode encoding; some are already encoded (e.g., ⇧ U+21E7 UPWARDS WHITE ARROW for Shift); others remain pending. DIN 2137 uses ISO/IEC 9995-7 symbols extensively in its layout documentation.[^4]

### 5.2 ISO/IEC 9995-10: Disambiguation on Keytops

9995-10:2025 supplements 9995-7 by providing symbols that distinguish visually similar characters (e.g., hyphen-minus from en-dash or em-dash) and standardizes the way diacritical marks are represented on dead keys. This is normatively relevant for high-typography keyboard designs and for conformant dead-key labeling.[^2]

### 5.3 ISO/IEC 9995-11: Dead Key Label Rectangles

9995-11:2026 specifies that dead keys for diacritical marks are labeled with **narrow horizontal rectangles** positioned to indicate both the shape and relative position of the diacritical mark with respect to the base letter. For example, a key with a comma-below diacritic shows a small rectangle with a comma beneath it. This is normative for any layout claiming conformance with 9995-11.[^2]

### 5.4 Legend Positioning Rules (ISO/IEC 9995-1)

The three keytop labeling schemes defined in 9995-1:2026 (columnar, group-1-priorized, level-4-including) are normative for layouts claiming conformance. Briefly:[^2]
- For a single-group layout with up to three levels: Group 1 Level 1 lower-left, Level 2 upper-left, Level 3 lower-right (group-1-priorized)
- For two-group layouts: Group 1 characters on left side of key, Group 2 characters on right side; within each group, Level 2 above Level 1
- Level 4 characters are not required to appear on keytops[^2]

***

## 6. Relationship to De Facto OS Layouts and Unicode LDML

### 6.1 Windows Keyboard Driver Model

Windows implements keyboard layouts as DLL files (`.dll`) identified by hexadecimal registry keys under `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Keyboard Layouts`. Each DLL maps **scan codes** → **virtual key codes** → **characters** using a table of shift states. The shift states correspond roughly to ISO/IEC 9995 levels (unshifted = Level 1; Shift = Level 2; AltGr = Level 3; Shift+AltGr = Level 4), but the mapping is platform-specific and the terminology is entirely internal. Windows does not formally reference ISO/IEC 9995 concepts in its driver API. The NF Z71-300 AZERTY and DIN 2137 E1/E2 implementations in Windows 11 24H2 represent the most direct recent OS adoption of formal keyboard standards.[^43][^24][^44][^20]

### 6.2 XKB (X Keyboard Extension) — Linux/X11

XKB is the keyboard configuration framework for X11 and Wayland-based Linux desktops. Its data model uses: `XkbModel` (physical keyboard model, e.g., `pc105` = ISO physical), `XkbLayout` (layout name), `XkbVariant`, and `XkbOptions`. XKB symbols files assign characters to keys using a multilayer model that parallels ISO/IEC 9995 levels (level 1–4) and supports multiple groups via group-switching mechanisms. The geometry files for XKB (used for visual display) reference key positions using naming conventions derived from but not identical to the ISO/IEC 9995-1 reference grid. XKB is a de facto standard, not a de jure one, and has no formal normative reference to ISO/IEC 9995 in its specification.[^45][^43]

### 6.3 Unicode LDML (UTS #35 Part 7) — "Keyboard 3.0"

The Unicode Common Locale Data Repository (CLDR) maintains the **LDML keyboard format**, specified in Unicode Technical Standard #35 Part 7. A major rewrite called "Keyboard 3.0" was introduced in CLDR v45 (2024), making it backward-incompatible with prior versions.[^42]

**Scope of LDML:** An XML interchange format for keyboard layout data — defining which Unicode characters are produced by which key positions under which modifier combinations, for both hardware and touch keyboards. Key design goals include:[^46][^47][^42]
1. Physical and virtual (touch) keyboards defined in a single file
2. Platform-independent definitions for new layouts
3. Use by any implementation to interpret keystrokes and produce Unicode text output

**Key LDML concepts** and their relationship to ISO/IEC 9995:
- LDML explicitly states: "Base character: The character emitted by a particular key when no modifiers are active. In ISO 9995-1:2009 terms, this is Group 1, Level 1." — LDML thus borrows ISO 9995-1 vocabulary for documentation[^42]
- LDML `ayer>` elements with modifier sets correspond to ISO/IEC 9995 levels (e.g., Shift → Level 2, AltGr → Level 3)
- LDML `<form>` elements reference named physical arrangements (though LDML's names do not directly mirror the ISO 9995-2 Key arrangement A/E/J/B nomenclature)
- LDML `<transforms>` elements implement dead-key behavior, analogous to ISO/IEC 9995-11 functionality but with a different algorithmic specification
- LDML includes Unicode normalization processing (NFD matching, NFC output) that ISO/IEC 9995 does not address

**Non-goals of LDML** that ISO/IEC 9995 *does* cover:[^42]
- Physical key dimensions and ergonomics
- Keycap symbol/legend design
- Unification of pre-existing platform layouts (LDML does not rename or resolve conflicts between Windows/macOS/XKB variants of the same layout)
- Platform-specific frame keys (Fn, IME keys, cursor keys) are explicitly out of scope

**Where they overlap and conflict:**
- ISO/IEC 9995 is a normative engineering standard governing physical keyboards, labeling, and character access hierarchy. LDML is a data interchange format for software character mapping. They occupy different layers of the stack.
- ISO/IEC 9995 defines up to 4 levels; LDML's `ayer>` concept maps directly but uses different terminology and can represent arbitrary modifier combinations
- A layout can simultaneously conform to ISO/IEC 9995-2 (physical/structural) and be expressed in LDML (software/data) without conflict — the two complement rather than conflict

***

## 7. ISO/IEC 9995 Vocabulary Glossary

The following definitions are taken from normative content of ISO/IEC 9995-1:2006/2026 (the 2006 PDF sample is publicly available; the 2026 standard is paywalled but its content is well-documented via secondary sources). Definitions marked **(N)** are normative; **(I)** are informative.

| Term | Precise Definition |
|------|--------------------|
| **Section** (N) | A block of keys, mostly with some functional relationship, forming one of three main physical divisions of the keyboard: the alphanumeric section, the numeric section, or the editing and function section[^6] |
| **Zone** (N) | A part of a keyboard section as further defined within ISO/IEC 9995. E.g., the alphanumeric zone (ZA0) and the function zones are sub-divisions of the alphanumeric section[^6] |
| **Level** (N) | A logical state of a keyboard providing access to a particular collection of graphic characters. Within a group, up to four levels are defined: Level 1 (unshifted/default), Level 2 (shifted), Level 3 (AltGr), Level 4 (Shift+AltGr). Levels are selected by level-select (qualifier) keys[^6] |
| **Level select** (N) | A function that, when activated, changes the keyboard state to produce characters from a different level; implemented as Shift (Level 2), AltGr or Level 3 Select key (Level 3), Shift+AltGr (Level 4)[^6] |
| **Group** (N) | A logical state of a keyboard providing access to a collection of graphic characters that logically belong together (e.g., characters for a different script). Groups are hierarchically superior to levels: each group may contain up to four levels. Group 1 is the primary/default group[^6] |
| **Group select** (N) | A function that, when activated, changes the keyboard state to produce characters from a different group; implemented as a dedicated group-select key or as the Shift+Level-3-Select combination[^6] |
| **Primary group layout** (N) | The allocation of graphic characters of Group 1 to the keys of a particular keyboard, defined by a national standard or established by common usage in a particular country or group of countries[^6] |
| **Secondary group layout** (N) | The allocation of graphic characters of Group 2 to the keys of a particular keyboard[^6] |
| **Key reference grid** (N) | The coordinate system specified in ISO/IEC 9995-1 by which every key position is uniquely identified by a letter (row) and two-digit number (column). E.g., E01 is the "1" key position; D01 is the "Q" key position on QWERTY[^5][^4] |
| **Key number / key designation** (N) | The specific identifier for a key position within the reference grid, composed of a row letter and a column number (e.g., C13 for the Return key position, B99 for the left Shift position)[^5][^4] |
| **Graphic key** (N) | A key whose primary purpose is input of a graphic character; includes the space bar in the 2026 edition[^2][^6] |
| **Function key** (N) | A key whose primary purpose is input of a control function[^6] |
| **Qualifier key** (N) | A key whose operation has no immediate visible effect but which, while actuated, modifies the effect of other keys (e.g., Shift, AltGr, Ctrl)[^6] |
| **Dead key** (N) | A key that does not produce a character immediately on actuation but instead modifies the next graphic key input to produce a combined character (e.g., pressing the acute-accent dead key then "e" produces "é")[^6] |
| **Group selector / secondary group selector** (I) | Colloquial term for the key or key combination (standardly shown as ⇨ per ISO/IEC 9995-7) used to access Group 2; may be a dedicated key or achieved by Shift+Level-3-Select. In the 2026 edition, when Group 2 is a supplement, this mechanism is termed the "Extra selector"[^4][^2] |
| **Harmonized keyboard arrangement** (I) | A narrower normative sub-specification within ISO/IEC 9995-2 identifying named physical key arrangements (A, E, J, B, K, L) that comply with both the standard and specific widely-used hardware forms[^2] |
| **Alphanumeric zone (ZA0)** (N) | The zone within the alphanumeric section containing the graphic keys (the "main block"); normatively requires a minimum number of keys in rows A through E at specified column positions[^3][^4] |

***

## 8. Implications for an Open Layout Model

### 8.1 ISO/IEC 9995 Concepts to Adopt or Map

An open keyboard layout model should adopt ISO/IEC 9995 vocabulary directly rather than inventing parallel terms. Specific recommendations:

**Level and Group model (adopt verbatim):**
Use `level` and `group` exactly as defined in ISO/IEC 9995-1. Represent each character cell as `(group, level)`. This allows a layout file to declare, e.g., "key E01, Group 1 Level 1 = '1'; Group 1 Level 2 = '!'; Group 1 Level 3 = '¹'; Group 2 Level 1 = 'superscript one'" without ambiguity. The level numbering (1–4) and group numbering (1–n) should match the standard's numbering, because every engineer and standards body working with keyboards understands this vocabulary.[^6]

**Key reference grid (adopt verbatim):**
Use the ISO/IEC 9995-1 key designation system (row letter + two-digit column: E01, D01, C00, B99, etc.) as the canonical identifier for key **positions**. This is a stable, hardware-independent, internationally recognized coordinate system. Note:[^5][^4]
- Physical key positions referenced this way make the layout model independent of any specific hardware brand
- The grid is defined normatively in 9995-1 and used by all conformant national standards (NF Z71-300, DIN 2137, etc.)

**Functional sections and zones (adopt as taxonomy):**
Adopt the section/zone taxonomy (alphanumeric section, alphanumeric zone, function zone, numeric section, editing and function section) as the top-level structural vocabulary of the model. This allows the model to describe compact layouts (no numeric section, no editing section) cleanly, matching the explicit permissiveness in ISO/IEC 9995-1's conformance clause.[^6]

**Key arrangement names (reference, do not reinvent):**
Reference the ISO/IEC 9995-2:2026 key arrangement identifiers (A, E, J, B, K, L) when describing physical keyboard forms. Do not use the colloquial terms "ANSI layout" and "ISO layout" as normative identifiers in the model — they are ambiguous and informal. Instead, say "Key arrangement A (ANSI INCITS 154-compatible)" and "Key arrangement E (ISO physical, conformant with NF Z71-300 and DIN 2137-01 E1)."[^2]

**Dead keys and keytop symbols (reference, implement):**
The dead key algorithm and labeling conventions from ISO/IEC 9995-11 should be the normative reference for the model's dead key behavior spec. Keycap legend positioning should reference ISO/IEC 9995-1's three named placement schemes and ISO/IEC 9995-7 symbols for function keys.[^2]

### 8.2 How a Layout Can Declare Conformance

Based on the conformance framework in ISO/IEC 9995-1 (Clause 2.3), a layout defined using the open model should make conformance claims of the following form:[^6]

**Structural conformance** (to the ISO/IEC 9995 framework):
> "This layout conforms to ISO/IEC 9995-1:2026 and ISO/IEC 9995-2:2026 for Key arrangement E."

This claim attests that: (a) the key reference grid, section/zone taxonomy, and keytop labeling conventions follow 9995-1:2026; and (b) the alphanumeric section's key count, zone arrangement, and function key positions follow 9995-2:2026 for the ISO physical form.

**National standard conformance** (to a specific layout):
> "This layout conforms to AFNOR NF Z71-300:2019, AZERTY variant."  
> "This layout conforms to DIN 2137-01:2023-08, layout E1."

These claims attest that the character assignments, dead key behavior, and special character access follow the cited national standard.

**Combined claim** (structural + national):
> "This layout conforms to ISO/IEC 9995-1:2026, ISO/IEC 9995-2:2026 (Key arrangement E), ISO/IEC 9995-11:2026 (dead keys), and AFNOR NF Z71-300:2019 (AZERTY variant)."

**Partial conformance** (allowable per 9995-1):
A compact 60% layout can claim conformance to ISO/IEC 9995-1:2026 and ISO/IEC 9995-2:2026 while noting "numeric section absent; editing and function section absent."

**LDML alignment** (not a conformance claim, but an interoperability declaration):
> "This layout is expressed in Unicode CLDR LDML Keyboard 3.0 format (UTS #35 Part 7, CLDR v45)."

This is separate from ISO/IEC 9995 conformance, because LDML is a data format, not a layout standard.

### 8.3 Terminology to Reuse Rather Than Reinvent

| Reinvention to Avoid | Established ISO/IEC 9995 Term | Notes |
|---------------------|-------------------------------|-------|
| "shift state" | **level** | ISO 9995 uses "level"; LDML uses "layer" or "modifier set" |
| "mode" / "layer" (for character switching) | **group** | Reserve "layer" for LDML-specific touch keyboard concepts |
| "AltGr layer" | **Level 3** (in a Level 3 select context) or **Group 2** (if a group selector key is used) | These are distinct concepts — using only "AltGr layer" conflates them |
| "dead accent" | **dead key** | ISO 9995-11 term is "dead key" |
| "key code" or "scan position" | **key designation** (e.g., E01) | The ISO grid designation is hardware-independent |
| "physical layout" (for ANSI/ISO/JIS physical form) | **key arrangement** (A/E/J/B per ISO 9995-2:2026) | The ISO 9995-2 names are normative and unambiguous |
| "secondary function" | **Level 2 allocation** or **Level 3 allocation** | Be explicit about which level |
| Custom "compose" key concept | **dead key** + **peculiar character mechanism** (ISO 9995-11) | If behavior matches, reference 9995-11 |
| "modifier key" | **level-select key**, **group-select key**, or **qualifier key** | ISO 9995-1 distinguishes these by function |

[^4][^6][^2]

***

## 9. Summary of Standards Provenance and Normative vs. Informative Status

- **ISO/IEC 9995-1**: fully normative except Annex A (examples of national standards) which is informative[^6]
- **ISO/IEC 9995-2**: Clauses governing key counts, zone arrangement, function key positions, and level/group selection are normative; the "Allocation guidelines" annex for Latin letter arrangement is explicitly **informative** — meaning DVORAK and other non-QWERTY arrangements do not violate 9995-2[^4]
- **ISO/IEC 9995-7**: the symbol catalog is normative; the correspondence between symbols and their Unicode encoding points is informative
- **NF Z71-300**: voluntary standard; the two layout definitions (AZERTY and BÉPO) are normative within the standard, but adoption by manufacturers is voluntary[^18]
- **DIN 2137-01:2023-08**: voluntary German standard; T1, E1, E2 are all normatively defined; T2 and T3 are deprecated and no longer normative
- **ANSI INCITS 154**: voluntary US standard; the physical arrangement and character assignment for the US QWERTY layout are normative within the standard; industry adoption is contractual/commercial
- **JIS X 6002**: Japanese Industrial Standard; character key arrangement is normative; physical dimensions excluded from scope[^30]
- **LDML UTS #35 Part 7**: a Unicode Technical Standard; normative for CLDR conformance but an independent specification — conformance to the Unicode Standard does not imply conformance to any UTS[^42]

---

## References

1. [ISO/IEC 9995-1:2009 - Information technology — Keyboard layouts for text and office systems — Part 1: General principles governing keyboard layouts](https://standards.iteh.ai/catalog/standards/iso/bde51464-be60-456b-8f37-f4a251c2551b/iso-iec-9995-1-2009) - ISO/IEC 9995 defines a framework for the layout of all alphanumeric and numeric keyboards across the...

2. [ISO/IEC 9995 - Wikipedia](https://en.wikipedia.org/wiki/ISO/IEC_9995)

3. [ISO/IEC 9995-2:2009](https://www.iso.org/standard/51644.html) - Information technology — Keyboard layouts for text and office systems — Part 2: Alphanumeric section

4. [ISO/IEC 9995 - Wikiwand](https://www.wikiwand.com/en/articles/ISO_keyboard) - ISO/IEC 9995 Information technology — Keyboard layouts for text and office systems is an ISO/IEC sta...

5. [ISO/IEC 9995-1:2009](https://www.iso.org/standard/51645.html) - Information technology — Keyboard layouts for text and office systems — Part 1: General principles g...

6. [Jis X6004 Layout](http://xahlee.info/kbd/Japan_keyboard_layouts.html)

7. [ISO/IEC 9995-2:2026 - Alphanumeric section](https://standards.iteh.ai/catalog/standards/iso/f404b877-8814-40f9-b965-3114fdbd08a5/iso-iec-9995-2-2026) - ISO/IEC 9995-2 sets global standards for alphanumeric keyboard layouts, ensuring unified design, opt...

8. [BS ISO/IEC 9995-3:2026 | 28 Feb 2026 - BSI Knowledge](https://knowledge.bsigroup.com/products/information-technology-keyboard-layouts-for-text-and-office-systems-latin-international-keyboard-layout)

9. [ISO/IEC 9995-3:2026 - Genorma](https://genorma.com/en/standards/iso-iec-9995-3-2026) - Information technology — Keyboard layouts for text and office systems — Part 3: Latin International ...

10. [ISO/IEC 9995-3:2010](https://www.iso.org/standard/52869.html) - Information technology — Keyboard layouts for text and office systems — Part 3: Complementary layout...

11. [SIST ISO/IEC 9995-7:2010 - Information technology - iTeh Standards](https://standards.iteh.ai/catalog/standards/sist/4ac29f4c-a6bd-403d-b8dc-7d20a2c5bc69/sist-iso-iec-9995-7-2010) - SIST ISO/IEC 9995-7:2010 - ISO/IEC 9995 defines a framework for the layout of all alphanumeric and n...

12. [ISO/IEC 9995-7:1994 - Information technology — Keyboard layouts for text and office systems — Part 7: Symbols used to represent functions](https://standards.iteh.ai/catalog/standards/iso/1eb2ce65-d765-42e9-85ef-faec39f2f28c/iso-iec-9995-7-1994) - ISO/IEC 9995-7:1994 - Defines symbols for functions found on any type of numeric, alphanumeric or co...

13. [ISO/IEC CD 9995-7](https://www.iso.org/standard/90275.html) - Information technology — Keyboard layouts for text and office systems — Part 7: Symbols used to repr...

14. [ISO/IEC 9995-11:2026](https://webstore.iec.ch/en/publication/111518) - This document defines the functionality of dead keys and repertoires of characters entered by dead k...

15. [ISO/IEC 9995-11:2026 - EVS standard evs.ee | en](https://www.evs.ee/en/iso-iec-9995-11-2026) - This document defines the functionality of dead keys and repertoires of characters entered by dead k...

16. [A standard for the French keyboard by the end of the year](https://labo.societenumerique.gouv.fr/en/articles/a-standard-for-the-french-keyboard-dictation-at-the-end-of-the-year/)

17. [Disposition de clavier Azerty afnor (NF Z71-300)](https://doc.ubuntu-fr.org/utilisateurs/bcag2/tuto_azerty-afnor)

18. [Clavier français : tout sur la nouvelle norme facilitant l'écriture du ...](https://sti.eduscol.education.fr/actualites/clavier-francais-tout-sur-la-nouvelle-norme-facilitant-lecriture-du-francais)

19. [Journal La norme française de dispositions de clavier a été publiée](https://linuxfr.org/users/elessar/journaux/la-norme-francaise-de-dispositions-de-clavier-a-ete-publiee) - La norme française de dispositions de clavier a été publiée

20. [France's new AZERTY keyboard layout - Globalization](https://learn.microsoft.com/en-us/globalization/keyboards/azerty_english) - The new AZERTY keyboard layout makes it easeier to enter accented characters and ligatures used in F...

21. [french-nf-azerty-mac/kbdrefs/nf_z71_300.md at master · cyril-L/french-nf-azerty-mac](https://github.com/cyril-L/french-nf-azerty-mac/blob/master/kbdrefs/nf_z71_300.md) - macOS keyboard layout for the standardized AZERTY (NF Z 71‐300 A) - cyril-L/french-nf-azerty-mac

22. [German extended keyboard layout - Wikipedia](https://en.wikipedia.org/wiki/German_extended_keyboard_layout)

23. [DIN 2137 – Wikipedia](https://de.wikipedia.org/wiki/DIN_2137)

24. [We need new keyboards - Page 2](https://typedrawers.com/discussion/5080/we-need-new-keyboards/p2) - @"John Butler", you may be pleased to learn that as of Windows 11, version 24H2, two new German keyb...

25. [E1 (Tastaturbelegung) - Wikiwand](https://www.wikiwand.com/de/articles/E1_(Tastaturbelegung)) - Die Tastaturbelegung E1 („Erweiterte Tastaturbelegung 1“) ermöglicht die Eingabe aller Buchstaben un...

26. [DIN 2137 — Wikipédia](https://fr.wikipedia.org/wiki/DIN_2137)

27. [Stellungnahme zum Norm-Entwurf DIN 2137-1:2018-04 - Bitkom e.V.](https://www.bitkom.org/Bitkom/Publikationen/Stellungnahme-zum-Norm-Entwurf-DIN-2137-12018-04.html) - Bitkom unterstützt die Zielsetzung der neuen DIN 2137-1 zur erweiterten Zeicheneingabe, warnt jedoch...

28. [日本規格協会 JSA GROUP Webdesk](https://webdesk.jsa.or.jp/books/W11M0090/index/?bunsyo_id=JIS+X+6002%3A1980)

29. [JIS Master Race - General - Colemak forum](https://forum.colemak.com/topic/2187-jis-master-race/)

30. [JISX6002:1980 情報処理系けん盤配列](https://kikakurui.com/x6/X6002-1980-01.html) - この規格は，JIS X 0201（情報交換用符号）の英字・片仮名用7単位符号を用いる両手操作形情報処理系けん盤配列について規定する。

31. [JISキーボード - Wikipedia](https://ja.wikipedia.org/wiki/JIS_X_6002?oldformat=true)

32. [JIS X 6002](https://www.boutique.afnor.org/en-gb/standard/jis-x-6002/keyboard-layout-for-information-processing-using-the-jis-7-bit-coded-charac/as011790/297302) - Keyboard layout for information processing using the JIS 7 bit coded character set / Note: Approved ...

33. [新JISキーボード](https://www.wdic.org/w/TECH/%E6%96%B0JIS%E3%82%AD%E3%83%BC%E3%83%9C%E3%83%BC%E3%83%89) - 通信用語の基礎知識オンライン検索システム

34. [QWERTY配列の変遷100年間(4) | タイプライターに魅せられた ...](https://dictionary.sanseido-publ.co.jp/column/qwerty04) - （QWERTY配列の変遷100年間(3)からつづく） 1933年6月、IBMはエレクトロマチック・タイプライターズ社を買収し、「IBM Electromatic」の販売を開始しました。「IBM Ele...

35. [Difference Between ANSI and ISO Keyboard Layouts](https://www.virtualcuriosities.com/articles/3220/difference-between-ansi-and-iso-keyboard-layouts) - The ANSI keyboard is set in INCITS 154-1988 [S2009] – Office Machines and Supplies – Alphanumeric Ma...

36. [Keyboard Types and Standards Explained | PDF | Computers - Scribd](https://www.scribd.com/document/537216118/keyboard1) - ANSI keyboards have keys spaced 0.75 inches apart and a minimum key travel of 3.8 mm. ANSI (ANSI-INC...

37. [ABNT2 layout | Keyboard Dictionary](https://sharktastica.co.uk/topics/dictionary?id=rIT7huNT) - ASK Keyboard Dictionary entry for "ABNT2 layout"

38. [Portuguese keyboard layout - Alchetron, the free social encyclopedia](https://alchetron.com/Portuguese-keyboard-layout) - There are two QWERTYbased keyboard layouts used for the Portuguese language. Additionally, there are...

39. [JCUKEN - Wikipedia](https://en.wikipedia.org/wiki/JCUKEN) - JCUKEN (ЙЦУКЕН, also known as YCUKEN, YTsUKEN and JTSUKEN) is the main Cyrillic keyboard layout [1] ...

40. [What Is the Nordic Keyboard Layout? Everything You Need to Know](https://monsgeek.eu/de/blogs/guide/what-is-the-nordic-keyboard-layout-everything-you-need-to-know) - The Nordic keyboard layout is optimized for Nordic language special characters and is suitable for S...

41. [The layout of Finland](https://typingdonewell.com/blog/what-is-a-nordic-layout-the-list-of-all-nordic-layouts-with-explanation/) - What is the Nordic keyboard layout? Nordic QWERTY is a modification to the standard QWERTY. It is us...

42. [UTS #35: Unicode LDML: Keyboards](https://unicode.org/cldr/charts/smoke/staging-dev/ldml/v37/tr35-keyboards.html)

43. [Xorg/Keyboard configuration - ArchWiki](https://wiki.archlinux.org/title/Xorg/Keyboard_configuration) - The Xorg server uses the X keyboard extension (XKB) to define keyboard layouts. Optionally, xmodmap ...

44. [Keyboard identifiers and input method editors for Windows](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/windows-language-pack-default-values?view=windows-11) - Use keyboard identifiers and Input Method Editors (IMEs) to identify the keyboard type.

45. [Custom keyboard layout - raphael.li](https://www.raphael.li/blog/2016/06/custom-xkb-layout/) - In most Linux desktop environments, the magic of keyboard layouts happens in xkb - the X Keyboard Ex...

46. [CLDR/LDML Keyboards - Keyman](https://keyman.com/ldml/) - LDML is the Locale Data Markup Language. It it an XML-based format specified as the Unicode Consorti...

47. [CLDR Keyboard Working Group - Unicode CLDR Project](https://cldr.unicode.org/index/keyboard-workgroup) - LDML: The universal interchange format for keyboards. The CLDR Keyboard Working Group is currently r...

