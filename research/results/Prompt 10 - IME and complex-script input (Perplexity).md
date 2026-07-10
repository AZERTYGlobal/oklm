# Complex-Script Text Input: IME Architecture, Framework Layers, and the LDML Keyboard Model Boundary

*A technical reference for engineers designing an open keyboard layout model*

***

## 1. What an IME Is and Why It Exists

### 1.1 The Fundamental Problem

A standard keyboard has roughly 100 keys. Written Chinese alone requires access to 20,000–80,000 characters; Japanese has roughly 2,000 characters in daily use; Korean has 11,172 precomposed syllables. No static key mapping can cover these repertoires. An **Input Method Editor (IME)** is the software component that bridges this gap: it intercepts sequences of keystrokes, maintains an internal composition state, queries data structures (dictionaries, syllable tables, stroke tables), presents a selection UI, and finally commits a resolved character or string to the application.

The IME paradigm is also employed, in reduced form, for scripts that do not need large dictionaries but do require *algorithmic* composition of multiple keystrokes into a single grapheme — Hangul being the clearest example — or *syntactic validation* of character sequences, as with Thai.

### 1.2 The Composition Pipeline

Every full IME follows the same three-phase pipeline, regardless of platform:

1. **Pre-edit (composition) phase.** As the user types, keystrokes are buffered in a *preedit* string displayed inline in the application, visually distinguished (typically underlined). The application receives no committed text yet. In TSF/IMM32 terms this is the composition string; in Android it is the composing span; in Web APIs it corresponds to `compositionstart` / `compositionupdate` events.[^1]

2. **Candidate-selection phase.** The IME queries its engine and presents an ordered candidate list (a pop-up window or horizontal strip). For phonetic Chinese input, multiple homophone characters are listed; for Japanese, the romaji→kana→kanji conversion produces ranked candidates using context. The user navigates with arrow keys, number keys, or touch.[^2]

3. **Commit phase.** The selected candidate is finalized: the preedit region is replaced by committed text and control returns to the application. On Android, the IME calls `InputConnection.commitText()`; on Web APIs a `compositionend` event fires; on TSF, the composition range is replaced with final text.[^3][^1]

### 1.3 Conceptual Difference from a Static Layout

A static keyboard layout is a **stateless mapping**: each keystroke is independently resolved to one or more code points by consulting a fixed key map, possibly augmented with a short-lived dead-key buffer. There is no persistent session state between keystrokes (beyond one buffered dead key), no dictionary lookup, and no user-facing selection UI. An IME is a **stateful process** that can buffer an arbitrary number of keystrokes, maintain session-level user-dictionary history, rank candidates by frequency, and implement conversion algorithms. The two concepts live at different architectural layers.

***

## 2. Per-OS IME Frameworks

### 2.1 Windows: TSF and IMM32

**IMM32** (Input Method Manager) is the legacy Windows COM-era interface, introduced in Windows 95 for East Asian editions and generalized in Windows 2000. An IMM32 IME is a DLL exposing an `ImeConvert` entry point; applications receive `WM_IME_*` messages to handle preedit display and candidate windows. It predates Win32 architecture and lacks the extensibility needed for modern input intelligence.[^4]

**Text Services Framework (TSF)** was introduced in Windows XP as IMM32's successor. TSF defines three primary components: **Applications** (TSF clients, implementing COM interfaces like `ITfTextInputProcessor`), **Text Services** (COM in-proc DLLs registered under `HKLM\SOFTWARE\Microsoft\CTF\TIP\`), and the **TSF Manager** (an OS-provided mediator that routes text between applications and text services). The TSF Manager is the only component both application and text service ever communicate with directly; they never interact with each other.[^5][^6]

TSF enables features IMM32 cannot: speech input, handwriting, reconversion after commit, autocorrect injection, and shaped-writing. Windows Store Apps (since Windows 8) accept only TSF-based IMEs, and IMM32 is deprecated for that surface. Modern Windows 11 first-party IMEs are built on WinRT/TSF, though the TSF COM interfaces remain the published SDK.[^7][^8][^9]

**How TSF relates to the keyboard layout:** The keyboard layout (`KBDINDEV.DLL` etc.) sits below TSF, handling raw scan-code-to-virtual-key translation. TSF intercepts keystrokes *after* the layout produces virtual key codes and VK-mapped characters. An IME text service overrides or augments the character stream at that point; the layout layer is immutable from the IME's perspective.

### 2.2 macOS / iOS: Input Method Kit (IMK)

Apple's **InputMethodKit** (IMK), introduced in OS X 10.5, provides a Cocoa framework for building input methods integrated with the **Text Services Manager**. An input method is a bundle whose bundle identifier must contain `.inputmethod.` in its reverse-DNS path (e.g. `com.vendor.inputmethod.MyIM`). The bundle registers as a Login Item and communicates with client applications via the framework.[^10][^11]

IMK's core classes are `IMKServer` (the process-level server communicating with the Text Services Manager), `IMKInputController` (one instance per client app focus context, handling keystrokes and preedit state), and `IMKCandidates` (the managed candidates panel). The `IMKCandidates` class presents candidates to users and notifies the `IMKInputController` when the user selects one. An IMK-based IME implements `handle(_:client:)` to decide whether to consume a keystroke (returning `true`) or pass it through, and calls `insertText(_:replacementRange:)` to commit text to the application.[^12][^13]

Apple's own documentation on IMK is sparse; most implementation knowledge is community-derived from `TextInputSources.h` (Carbon/HIToolbox).[^11]

On iOS, third-party keyboards are implemented as **App Extensions** in the `UIInputViewController` subclass framework (not IMK); they communicate through a limited `UITextDocumentProxy`. Apple's own system keyboards on iOS use a private variant of the same composing pipeline.

### 2.3 Linux: IBus, Fcitx5, m17n, and XKB

Linux input architecture is layered. At the lowest level, **XKB** (X Keyboard Extension) handles hardware scan codes → Unicode code points via a static symbol table in `/usr/share/X11/xkb/symbols/`. XKB supports dead keys, compose sequences, and up to 8 modifier levels. It is suitable for European alphabetic scripts but cannot handle CJK, syllabic Indic, or Korean composition.[^14]

For complex scripts, a framework sits above XKB:

**IBus** (Intelligent Input Bus) uses a bus-style IPC architecture. The `ibus-daemon` process mediates between IM language engine processes and the application via the IBus D-Bus protocol. Language engines are separate processes: `ibus-mozc` for Japanese, `ibus-libpinyin` for Simplified Chinese, `ibus-hangul` for Korean, `ibus-m17n` for Indic languages, etc. Applications integrate via GTK/Qt IM modules (`GTK_IM_MODULE=ibus`) or via XIM (the legacy X Input Method protocol). IBus can transparently wrap XKB so that layout changes and complex-script input coexist. Wayland support uses the `zwp_input_method_v1` protocol.[^15][^16][^17][^14]

**Fcitx5** is the other major maintained framework. It is lighter-weight, supports both X11 and Wayland natively (implementing both `zwp_input_method_v1` and `zwp_input_method_v2`), and uses an addon architecture rather than separate processes. The same underlying engines (libpinyin, Mozc/Anthy, libhangul) are wired in via adapter packages (`fcitx5-chinese-addons`, `fcitx5-anthy`, etc.).[^18][^19][^20][^21]

**m17n** (Multilingualization library) is an engine-level library for Indic and other complex scripts; it provides table-based transliteration and phonetic input for dozens of languages including InScript layouts for Indian scripts. It is surfaced through `ibus-m17n` or `fcitx5-m17n`.[^22]

**SCIM** and **uim** are legacy frameworks, no longer maintained as of 2023.[^18]

On **Wayland**, the XIM protocol cannot function because there is no X server; all IM communication must go through `text-input-unstable-v3` or equivalent Wayland protocols. Environment variables `GTK_IM_MODULE`, `QT_IM_MODULE`, and `XMODIFIERS` still route toolkit input to the framework.[^20][^17]

The layering is therefore: **XKB (scan-code → Unicode) → IBus/Fcitx5 daemon → language engine → application via IM module**. The keyboard layout is XKB; the IME is the language engine; the framework (IBus/Fcitx5) is the IPC middleware.[^23]

### 2.4 Android: InputMethodService

On Android, every IME is an **application service** subclassing `android.inputmethodservice.InputMethodService`. The framework provides three standard UI surfaces: the *input view* (the soft keyboard), the *candidates view* (the suggestion strip), and an extract-text view for fullscreen mode. The IME communicates with the focused app through an **`InputConnection`** object, calling `setComposingText()` (preedit), `setComposingRegion()`, and `commitText()` (commit).[^24][^3]

`InputMethodManagerService` (IMMS) is the system service that manages which IME is active and routes display focus. Android 10+ supports multiple displays: the IMMS can rebind the IME service when focus moves to a secondary display. The soft-keyboard IME model on Android is therefore total: there is no physical keyboard layout layer separate from the IME; the IME *is* the keyboard, drawing its own key layout and handling its own transformations.[^25]

***

## 3. Complex-Script Input Methods: Per-Script Analysis

### 3.1 Chinese

Chinese input methods divide into two paradigms:

**Phonetic methods** map the romanized or phonetic spelling of a character's pronunciation to candidates:

- **Pinyin** (mainland China): the user types the romanized pinyin syllable(s) of the desired character or word (e.g., `hao` → candidates including 好, 号, 浩…). The IME queries a large phonetic dictionary and ranks candidates by frequency and context. Modern systems (Microsoft Pinyin, Google Pinyin, Sogou) use n-gram language models for phrase-level conversion. This is dictionary-dependent and candidate-selection dependent — it cannot be expressed by a static layout or dictionary-free transforms.[^26]
- **Zhuyin/Bopomofo** (Taiwan): the user types the Zhuyin phonetic symbols (assigned to keys on a QWERTY keyboard) followed by a tone key; a single phonetic syllable is assembled and then disambiguated against a dictionary. The phonetic→character resolution requires a dictionary; the key→Zhuyin-symbol mapping is layout-level.[^27]

**Shape-based methods** map key sequences to character components (radicals/strokes):

- **Wubi**: characters are decomposed into up to 4 structural root components (字根), each mapped to a key zone (25 keys, 5 zones). Disambiguation still requires a dictionary since multiple characters can share the same root sequence, though some unique-root characters commit directly. Wubi requires a root-encoding table (essentially a static transform table per character) plus a dictionary for ambiguous cases.[^28][^26]
- **Cangjie**: characters are decomposed into 1–5 roots selected from 25 keys; a lookup table maps each character to its Cangjie code. As with Wubi, a dictionary is needed for disambiguation. Both Wubi and Cangjie are partially expressible as transform tables but require a dictionary lookup for the final character-to-code mapping.[^29]
- **Stroke** (5-stroke): characters are typed by their basic stroke categories (horizontal, vertical, left-fall, right-fall, bend), producing a stroke code resolved via a table.

**Summary for Chinese:** All Chinese input methods require at minimum a character-to-code lookup table, and all but the simplest single-character-per-code entries require a dictionary and candidate selection UI. None can be reduced to a transform-only model.

### 3.2 Japanese

Japanese input requires a multi-stage conversion pipeline:[^2]

1. **Romaji → Kana:** The user types romanized pronunciation (e.g., `a` → あ, `ka` → か, `tsu` → つ). This stage is a finite-state transform: a small table of romaji sequences maps to hiragana/katakana. This stage *is* expressible as an LDML transform set — it is dictionary-free and algorithmic.
2. **Kana → Kanji conversion:** The assembled kana string is passed to a conversion engine (Mozc, Anthy, ATOK) which segments it into words and maps each word to the most probable kanji representation using a dictionary and n-gram language model. The user then selects from a candidate list. This stage is definitionally dictionary-dependent.[^23]
3. **Direct kana input** (JIS layout): The JIS keyboard has hiragana printed on keys; `変換` (Henkan) triggers kana→kanji conversion directly. This bypasses stage 1 but still requires stage 2.[^30]

Keys specific to Japanese physical keyboards (`半角/全角`, `無変換`, `変換`, `かな`) are **frame keys** — they control mode switching and conversion triggers — and are explicitly out of scope for the LDML keyboard specification.[^31]

### 3.3 Korean: Algorithmic Hangul Composition

Korean Hangul is the clearest example of a script that requires *algorithmic* but **not dictionary-based** composition. This distinction is critical.

A Korean syllable block (e.g., 한 U+D55C) is composed of:
- A leading consonant (초성 *choseong*, U+1100–U+1112),
- A vowel (중성 *jungseong*, U+1161–U+1175),
- An optional trailing consonant (종성 *jongseong*, U+11A8–U+11C2).[^32]

The composition formula is purely arithmetic:[^33]
\[ \text{syllable} = \text{U+AC00} + (\text{initial} \times 588) + (\text{vowel} \times 28) + \text{final} \]

The reverse decomposition is equally trivial. The Hangul Syllables block (U+AC00–U+D7A3) contains 11,172 precomposed syllable blocks, all derivable from this formula.[^32]

A Hangul IME keeps a **one-syllable buffer** of at most 3 jamo (e.g., ㅎ + ㅏ + ㄴ). As each jamo keystroke arrives, the automaton checks whether the new jamo can extend the current syllable (e.g., an incoming vowel can always begin a new syllable; an incoming consonant may complete the current coda or begin the next syllable, context-dependent). When the syllable is complete, it is committed as a precomposed NFC code point via Unicode NFC normalization, which canonically composes jamo sequences.[^34][^35][^36]

**This is entirely algorithmic — no dictionary is required.** The whole of Korean jamo → syllable composition can be expressed as a finite-state automaton that applies the Unicode Hangul composition algorithm. It *can* be modeled in LDML transform rules (a series of transforms matching jamo sequences to precomposed syllables), though the LDML transform model does not have built-in support for the multi-keystroke syllable buffer state that Korean requires. The Hangul automaton is categorically different from Chinese/Japanese IMEs: it is deterministic and dictionary-free.

In Unicode normalization terms: applying NFC to a sequence of conjoining jamo (U+1100–U+11FF range) produces the precomposed syllable. NFD decomposes precomposed syllables back into their constituent jamo.[^37][^34]

### 3.4 Indic / Brahmic Scripts

Brahmic scripts (Devanagari, Bengali, Tamil, Telugu, Kannada, Malayalam, Odia, Gujarati, Gurmukhi, and their Southeast Asian relatives) share key characteristics:

- **Abugida structure:** consonants carry an inherent vowel; dependent vowel signs (matras) are written as diacritics above, below, left, or right of the consonant base. Some pre-vowels (e.g., Devanagari vowel sign I ि) are stored *after* the consonant in logical order but must be *displayed before* it visually — creating a **reordering** requirement.[^38]
- **Conjuncts:** two or more consonants can fuse into a conjunct form when joined by a virama (halant, U+094D for Devanagari). The sequence C₁ + virama + C₂ may render as a stacked or fused conjunct glyph. In Unicode, the logical storage order is C₁ ◌ C₂ virama-excluded; the shaping engine (HarfBuzz/Uniscribe) applies GSUB substitution to select the correct glyph form.[^39]
- **Unicode encoding order vs. visual order:** the Unicode Standard encodes Brahmic characters in a "logical" order that follows the phonological sequence but may differ from the visual rendering order. The reordering from logical to visual is performed by the **shaping engine** (a rendering-layer concern), not by the input layer.

**InScript layout:** The Government of India standardized InScript as the default keyboard layout for 12 Indian scripts (Devanagari, Bengali, Gujarati, etc.). InScript assigns consonants and vowel signs directly to keys, with virama on a dedicated key. Conjunct formation is achieved by typing C₁ + virama key + C₂: the user explicitly types the virama; the shaping engine handles the glyph selection. This means **Indic conjunct formation at the input layer is a static layout + dead-key transform** (key → code point, virama → dead key that modifies the next consonant) — it does not require a dictionary-driven IME.[^40]

**Phonetic/transliteration input** (e.g., typing `ka` → क, `kha` → ख) works as a transform table in m17n and similar engines; these are expressible as LDML transforms.[^22]

**Reordering in LDML:** The LDML `<reorder>` element directly addresses pre-vowel reordering. It assigns a `tertiary` order attribute to codepoints so that combining marks can be re-sorted into the correct Unicode logical order after input. For example, typing a pre-vowel key before its base consonant can be corrected by a reorder rule so that the stored sequence is base + pre-vowel (logical order) rather than pre-vowel + base (typed order). The reorder element operates on NFD codepoints.[^31]

**Unicode normalization** is central: LDML Keyboard 3.0 mandates that matching and internal processing operate in NFD; output is normalized to NFC before being committed to the application. For Indic scripts, this ensures that base + combining vowel sign sequences are canonical.[^31]

### 3.5 Arabic and Hebrew

Arabic and Hebrew present a commonly misunderstood boundary between **input** and **rendering**. It is essential to separate these levels:

**Input level:** Arabic and Hebrew keyboards map keys directly to Unicode code points (Arabic letters U+0600–U+06FF; Hebrew letters U+05D0–U+05EA). Typing is strictly one-keystroke-per-character: no composition pipeline, no preedit buffer, no candidate selection. From the input method perspective, these are **static layouts** — the keyboard layout alone suffices.[^41]

**Rendering level (shaping):** Arabic letters have up to four contextual forms (isolated, initial, medial, final) determined by their position in a word. The rendering engine (HarfBuzz, Uniscribe/DirectWrite's Arabic shaper) applies OpenType GSUB substitution lookups to select the correct glyph based on neighbouring characters. Ligatures (e.g., لا lam-alef) are handled by the GSUB `liga` feature. **This shaping is entirely a rendering/font concern and happens after text storage** — it is not the keyboard's responsibility.[^42][^43]

**RTL handling:** Arabic and Hebrew are written right-to-left. The Unicode **Bidirectional Algorithm** (UBA, UAX #9) governs the display ordering of mixed-direction text. Again, this is a rendering-layer algorithm, not an input-layer concern. The keyboard emits logical (Unicode) code points in phonological order; the BiDi algorithm reorders them for visual display.[^42]

**Hebrew keyboard:** Standard Hebrew keyboards (SI-1452) map each Hebrew letter to a key; paired delimiters have reversed *physical* positions because the rendering engine's BiDi mirroring corrects them visually — the keyboard emits the logical Unicode character.[^41]

**Diacritics (harakat/niqqud):** Arabic vocalization marks (harakat, U+064B–U+065F) and Hebrew vowel points (niqqud, U+05B0–U+05C4) are combining characters entered via AltGr or Shift+AltGr layers on the layout. They are typed as individual combining code points, stored as combining sequences, and rendered by the shaping engine. These are layout-level characters accessible via modifier layers — no IME is required.

**The key distinction:** For Arabic and Hebrew, **no IME is needed for standard typing**. The entire input stack is a static layout. The complexity of Arabic appears to users at the *rendering* layer (contextual shaping, ligatures), not at the *input* layer.

### 3.6 Southeast Asian Scripts: Thai, Khmer, Myanmar, Lao

Southeast Asian abugidas share a structural feature: some vowels and diacritics are typed *before* the consonant they modify but stored *after* it in Unicode logical order, requiring input-level reordering.

**Thai (TIS-620 / Unicode):** The Thai keyboard (QWERTY-derived layout) maps each Thai character to a key — one keystroke per character, directly producing code points. What distinguishes Thai from a simple Latin layout is *sequence validation*: the Thai Industrial Standard WTT 2.0 (TIS 1566-2541) defines three input check levels for the sequence of base consonants, above/below vowels, and tone marks:[^44][^45]
- Level 0 (passthrough): no check.
- Level 1 (basic check): rejects combinations that cannot form valid syllables.
- Level 2 (strict check): enforces the full WTT cell-column model.

**Leading vowels** (เ แ โ ใ ไ, U+0E40–U+0E44) are typed *before* the consonant but should be stored *after* it in Unicode logical order. Historically, Thai TIS-620 encoding stored them in typed order; Unicode Thai re-uses these code points in visual order. A conformant input system for Thai must either (a) detect the lead vowel + following consonant and reorder, or (b) rely on the rendering engine to compensate. This reordering can be expressed as an LDML `<reorder>` rule.[^46]

**Khmer, Myanmar, Lao:** These scripts similarly have pre-vowels stored after their base consonant in Unicode logical order. Myanmar has multiple stacking consonant mechanisms (Asat, Ya-pin, etc.) that require specific ordering rules. The Unicode Standard lacks a fully defined normalization order for most Brahmic-derived scripts, meaning that different encoding orders can be canonically equivalent — a source of search mismatch and rendering inconsistency.[^47][^48]

Input validation (rejecting invalid sequences) is analogous to Thai WTT: it can be implemented as a set of LDML transforms that accept or reject character sequences without requiring a dictionary. However, ensuring correct logical order for pre-vowels requires reorder rules.

***

## 4. The Decision Boundary: Layout vs. Transforms/Reorders vs. Full IME

### 4.1 Three-Way Decision Diagram

```
                    KEYBOARD LAYOUT LAYER
                    ┌─────────────────────────────────────────────┐
                    │ Key → base character (one-to-one mapping)   │
                    │ Shift/AltGr/Ctrl layers                      │
                    │ Dead keys (buffer one pending modifier)      │
                    │ Long-press / flick variants (touch)          │
                    │ Scan code → virtual key → Unicode mapping    │
                    └───────────────┬─────────────────────────────┘
                                    │ output: 1 or 2 code points max
                                    ▼
                    TRANSFORMS / REORDERS LAYER
                    ┌─────────────────────────────────────────────┐
                    │ Multi-keystroke dead-key sequences            │
                    │   (^+e → ê; `+a → à)                        │
                    │ Phonetic romanization → native script        │
                    │   (romaji → hiragana; Latin → Devanagari)   │
                    │ Unicode logical-order correction             │
                    │   (Thai lead vowel reorder; Indic matra)    │
                    │ Jamo → Hangul syllable composition          │
                    │   (algorithmic, finite-state, no dictionary) │
                    │ Input sequence validation (Thai WTT)         │
                    │ Normalization (NFD matching → NFC output)    │
                    │ Markers (opaque state tokens for transforms) │
                    │                                              │
                    │ CRITERION: Deterministic, dictionary-free,   │
                    │ output = f(keystroke-sequence), no candidate │
                    │ selection UI, finite state machine only.      │
                    └───────────────┬─────────────────────────────┘
                                    │ when ambiguity requires
                                    │ dictionary or candidate UI
                                    ▼
                    FULL IME LAYER (delegated / referenced)
                    ┌─────────────────────────────────────────────┐
                    │ Dictionary lookup (phoneme/radical → char)   │
                    │ N-gram / language model ranking              │
                    │ Candidate list UI                            │
                    │ Preedit / composition string management      │
                    │ Kana → Kanji conversion engine               │
                    │ Pinyin / Wubi / Cangjie disambiguation       │
                    │ User dictionary / frequency learning         │
                    │ Reconversion of committed text               │
                    │                                              │
                    │ CRITERION: Requires persistent state beyond  │
                    │ one syllable, dictionary, or probabilistic   │
                    │ candidate ranking across multiple options.   │
                    └─────────────────────────────────────────────┘
```

**Placement criteria:**

| Layer | Criterion | Examples |
|---|---|---|
| **Layout** | One key stroke → ≤2 code points, stateless | QWERTY, InScript, Arabic, Hebrew, Thai base characters |
| **Transforms/Reorders** | Finite, deterministic, dictionary-free multi-key sequences or reordering | Dead keys (^+e→ê), romaji→kana, Thai lead-vowel reorder, Hangul jamo→syllable, Indic virama conjuncts |
| **Full IME** | Dictionary lookup, candidate selection UI, n-gram ranking, or probabilistic conversion | All Chinese methods, Japanese kana→kanji, word-level prediction |

### 4.2 Script-by-Script Classification

| Script Family / Language | Typical Input Method(s) | Provided by Layout Layer | Expressible via Transforms/Reorders | Requires Full IME (dictionary/candidates/conversion) |
|---|---|---|---|---|
| **Chinese — Pinyin** | Phonetic, frequency-ranked | Key → ASCII letters (QWERTY) | Romanization → preedit syllables (partial)[^49] | **Yes** — dictionary, candidate list, n-gram ranking[^26] |
| **Chinese — Wubi** | Shape/radical | Key → root codes (QWERTY zones) | Root-sequence → code (partial table)[^28] | **Yes** — dictionary for disambiguation[^26] |
| **Chinese — Cangjie** | Shape/stroke | Key → root codes | Root lookup table[^29] | **Yes** — disambiguation dictionary |
| **Chinese — Zhuyin/Bopomofo** | Phonetic | Key → Zhuyin symbols (layout)[^27] | Symbol assembly | **Yes** — symbol → character disambiguation[^27] |
| **Chinese — Stroke** | Stroke categories | Key → stroke category | Stroke code table | **Yes** — dictionary for disambiguation |
| **Japanese — Romaji** | Romaji→kana→kanji | Key → ASCII | Romaji→hiragana transforms[^2] | **Yes** — kana→kanji conversion engine, candidate UI[^23] |
| **Japanese — Direct kana** | JIS kana layout | Key → kana directly | — | **Yes** — Henkan conversion still requires dictionary[^50] |
| **Korean — Hangul** | Jamo automaton | Key → jamo code points | **Fully expressible** — algorithmic syllable composition[^32][^33] | **No** — purely algorithmic; no dictionary needed |
| **Indic — InScript** | Direct Unicode mapping | Key → consonant/vowel sign; virama as dead key | Reorder for pre-vowels / matras; conjunct via virama transform[^40][^38] | **No** (for InScript); optional for phonetic |
| **Indic — Phonetic** | Transliteration | Key → Latin | Transliteration transforms (m17n)[^22] | Optional for disambiguation |
| **Arabic** | Direct layout | Key → Unicode code point[^41] | Diacritic combining (AltGr layer) | **No** — shaping is rendering-layer[^42][^43] |
| **Hebrew** | Direct layout | Key → Unicode code point[^41] | Niqqud combining (AltGr layer) | **No** — shaping is rendering-layer |
| **Thai** | Direct layout + WTT | Key → code point[^44] | Lead-vowel reorder; WTT sequence validation[^45][^46] | **No** (standard typing); phonetic Thai needs dictionary |
| **Khmer** | Direct layout | Key → code point | Pre-vowel reorder, stacking rules[^47] | **No** (for standard layout) |
| **Myanmar** | Direct layout | Key → code point | Pre-vowel reorder, Asat stacking[^51] | **No** (for standard layout) |
| **Lao** | Direct layout | Key → code point | Pre-vowel reorder[^51] | **No** (for standard layout) |

***

## 5. LDML Keyboard 3.0: Complex-Script Capabilities and Deliberate Limits

LDML Keyboard 3.0 (introduced in CLDR v45) is the authoritative interchange format for keyboard layout data across platforms. Its capabilities and limits for complex scripts are as follows.[^52][^31]

### 5.1 What LDML Keyboard 3.0 Can Express

**Key-to-character mapping:** The `<key>` element with its `output` attribute handles the basic layout layer. `ayers>` and `ayer>` with modifier sets handle Shift, AltGr, and modifier combinations.[^31]

**Dead keys / multi-key sequences (Transforms):** The `<transforms>` element with `<transformGroup>` and `<transform from="…" to="…">` rules handles dead-key sequences and multi-character phonetic input. Rules use NFD-normalized regex-like patterns. Example: a Devanagari phonetic layout can express `k+a → क` as a transform.[^31]

**Character reordering:** The `<reorder>` element assigns a `tertiary` sort order to codepoints, causing them to be reordered relative to their Canonical Combining Class (CCC) after input. This directly handles:
- Thai and other Southeast Asian pre-vowel correction (typed-order → logical-order)
- Indic matra pre-vowel reordering
- Any script where the user types in visual order but Unicode requires logical order[^31]

`reorder` elements operate on NFD codepoints and interact with normalization-safe segment boundaries.[^31]

**Markers:** Opaque named tokens (`\m{name}`) that can be injected into the transform output stream as bookmarks, not emitted as text, to drive subsequent transform rules — for example, to track that a virama was typed so the next consonant forms a conjunct. Markers survive through NFD normalization with defined "gluing" semantics.[^31]

**Normalization integration:** LDML mandates NFD-based matching throughout; output is normalized to NFC before delivery to the application (or a platform-specified form). This handles canonical equivalence for combining sequences.[^53][^31]

**Import of shared transform sets:** `<import base="cldr" path="…">` allows sharing romaji→kana table sets or InScript phonetic tables across keyboard files.[^31]

**Backspace transforms:** `<transforms type="backspace">` defines custom backspace behavior that correctly undoes multi-key sequences (e.g., undoing a composed Indic conjunct character-by-character rather than codepoint-by-codepoint).[^31]

### 5.2 What LDML Keyboard 3.0 Deliberately Does Not Cover

LDML's explicit non-goals and design boundaries include:

1. **Dictionary-driven disambiguation.** The format has no mechanism for candidate lists, frequency tables, n-gram models, or user dictionaries. There is no `<dictionary>` or `andidates>` element. Chinese Pinyin, Wubi, Cangjie, Japanese kana→kanji conversion, and any input method requiring a probability-ranked candidate UI are **outside scope**.[^31]

2. **Stateful composition sessions beyond one normalization-safe segment.** LDML transforms operate on the *recent input context buffer* (a short lookbehind), not on multi-sentence or session-level state. Japanese kana→kanji conversion over a whole sentence is not expressible.

3. **Frame keys.** IME swap keys, mode-switch keys (`変換`, `半角/全角`), cursor keys, Fn keys are explicitly excluded. The spec notes: *"Platform-specific frame keys such as Fn, Numpad, IME swap keys, and cursor keys are out of scope."*[^31]

4. **Run-time IME protocol.** LDML describes an interchange format; it does not specify preedit/commit lifecycle, TSF interfaces, IBus D-Bus messages, or Android `InputConnection` calls. It is a data format, not an IPC protocol.

5. **Predictive text, autocorrect, handwriting, voice.** These are explicitly adjacent-but-distinct features outside the layout model. A layout file can *reference* an IME that provides them, but cannot describe their behavior.

6. **Platform-specific keyboard frame / hardware variations.** Unification of existing platform-specific layouts (fr-AZERTY variants across Windows/macOS/Linux) is a non-goal.[^31]

7. **Rendering/shaping.** LDML does not describe how output code points are rendered. Arabic contextual forms, Devanagari conjunct glyphs, and BiDi display are concerns of the shaping engine (HarfBuzz, Uniscribe) and the font's OpenType GSUB/GPOS tables.[^54][^39]

***

## 6. Adjacent-but-Distinct Features

The following features are closely related to complex-script input but are **outside the core of a keyboard layout model**:

- **Predictive text / word completion:** Suggests the next word using a language model. Available as a candidates-strip feature on top of any IME. Requires a large language model or n-gram dictionary; not expressible in a layout file.
- **Autocorrect:** Substitutes misspelled words post-commit using an edit-distance dictionary. Operates on committed text; orthogonal to the input pipeline.
- **Transliteration input:** A mode where typing Latin characters produces native-script output according to a transliteration table (e.g., ISO 233 for Arabic, ITRANS for Devanagari). The transliteration table *is* expressible as an LDML transform set — this is one of the primary use cases for the `<transforms>` element. It does not require a dictionary as long as the mapping is one-to-one or context-deterministic.
- **Handwriting recognition:** Stroke input recognized via ML classifiers. Implemented at the IME layer (e.g., as an alternative input view in Android `InputMethodService`); not a keyboard layout concern.
- **Voice / speech recognition:** ASR pipeline producing text. Implemented as a text service in TSF (Windows) or an `InputMethodService` variant (Android); outside the layout model entirely.

***

## 7. Implications for an Open Keyboard Layout Model

### 7.1 What the Model Should Represent Directly

An open layout model aligned with LDML Keyboard 3.0 should natively represent:

1. **Base key mappings** for all modifier layers (Shift, AltGr, Ctrl+Alt, Caps-Lock combinations) — the core layer mapping from key codes to Unicode output.[^31]
2. **Dead keys** — keys that produce no immediate output but modify the next key's output, implemented as single-element transform lookbehind.
3. **Transform sets** — ordered, NFD-normalized regex-like rules mapping input context buffers to output code points. Covers: dead-key sequences, multi-character phonetic input (romaji→kana, Latin→Devanagari/other Indic scripts), simple transliteration tables.
4. **Reorder rules** — explicit tertiary-order assignments for combining marks, handling scripts where the typed order differs from Unicode logical order (Thai pre-vowels, Indic matras, other Brahmic pre-vowels).[^31]
5. **Markers** — opaque state tokens used within transform rules to track multi-step composition state (e.g., the virama state in Indic conjunct input) without requiring full FSM infrastructure outside the transform engine.
6. **Normalization metadata** — whether the keyboard operates in default NFC output, NFD matching, or disabled normalization modes.[^31]
7. **Backspace behavior** — custom undo semantics for composed sequences.
8. **Long-press / flick variants** (for touch keyboards) — secondary character lists per key.[^31]

### 7.2 What the Model Should Reference, Not Embed

For features requiring a full IME, the model should carry **declarative metadata** — a typed reference — rather than an attempt to encode the behavior:

```xml
<!-- Proposed metadata pattern (compatible with LDML's <special> extensibility) -->
<keyboard3 locale="zh-Hans-t-k0-pinyin" conformsTo="45">
  <info name="Chinese Simplified Pinyin" />
  <!-- Layout layer: key → ASCII letters -->
  <keys>...</keys>
  <!-- Transform layer: implicit (no transforms needed; Pinyin uses pure ASCII pass-through) -->
  <!-- IME reference metadata -->
  <special xmlns:ime="https://example.org/ime-metadata">
    <ime:requires
      type="phonetic-chinese"
      platforms="windows:msime-pinyin macOS:apple-pinyin linux:ibus-libpinyin android:gboard-pinyin"
      fallback="ibus-libpinyin" />
  </special>
</keyboard3>
```

The metadata should convey:

- **`type`** — a semantic category (`phonetic-chinese`, `shape-chinese`, `kana-kanji`, `phonetic-indic`, etc.) that a runtime can use to select the right IME class.
- **`platform-bindings`** — named IME identifiers per platform (TSF CLSID, macOS bundle ID, IBus engine name, Android service component name).
- **`transform-set`** — for layouts that ship a transform set (e.g., romaji→kana), an identifier or inline import that any LDML-compatible runtime can execute before handing off to the conversion engine.

### 7.3 Interoperability with LDML

The model should maintain the following LDML interoperability invariants:

1. **Layout files are valid LDML Keyboard 3.0 XML** (`conformsTo="45"` or later). IME references live in `<special>` elements, which LDML processors are required to skip if the namespace is unrecognized.[^31]
2. **Transform sets are independently importable** via `<import>` so that platform implementations can compile them into native runtime formats (e.g., `.kbd` on Windows, a compiled IBus table).
3. **Normalization contract is explicit:** the file must declare its normalization setting (`normalization="nfc"` or `"disabled"`) so importers can handle marker interaction correctly.
4. **The layout file is not an IME descriptor.** It declares *that* an IME is needed and *which* one, but does not attempt to describe candidate generation, dictionary format, or conversion algorithm. This boundary mirrors LDML's own design philosophy.
5. **Hangul is an exception:** because Hangul composition is algorithmic and dictionary-free, a complete Hangul layout can be expressed as LDML transforms (jamo → syllable) without any IME reference. An open model should recognize this class of *FSM-completable* composition and provide native transform support rather than delegating to an external IME.

### 7.4 Summary Decision Table for the Open Model

| Feature | Representation in Model |
|---|---|
| Key → base code point | Native (`<key output>`) |
| Dead keys | Native (`<transform>` with one-step lookbehind) |
| Romaji → kana, Latin → Indic transliteration | Native (`<transforms>` set) |
| Thai pre-vowel reorder | Native (`<reorder>`) |
| Indic matra / pre-vowel reorder | Native (`<reorder>`) |
| Hangul jamo → syllable composition | Native (`<transforms>` FSM — no dictionary) |
| Indic InScript conjuncts (virama-based) | Native (`<transforms>` with markers) |
| Arabic/Hebrew base input | Native layout (no transforms needed) |
| Arabic/Hebrew diacritics | Native (AltGr layer + combining code points) |
| Thai WTT sequence validation | Native (`<transforms>` with rejection rules) |
| Chinese Pinyin/Wubi/Cangjie | **Reference only** — `<special>` IME metadata |
| Japanese kana→kanji conversion | **Reference only** — `<special>` IME metadata (romaji→kana part: native transforms) |
| Predictive text / autocorrect | **Out of scope** — adjacent feature |
| Handwriting / voice | **Out of scope** — adjacent feature |

***

## Primary Sources and References

- Microsoft TSF documentation: [https://learn.microsoft.com/en-us/windows/win32/tsf/text-services-framework](https://learn.microsoft.com/en-us/windows/win32/tsf/text-services-framework)[^55][^5]
- Microsoft Simplified Chinese IME: [https://learn.microsoft.com/en-us/globalization/input/simplified-chinese-ime](https://learn.microsoft.com/en-us/globalization/input/simplified-chinese-ime)[^26]
- Microsoft Japanese IME: [https://learn.microsoft.com/en-us/globalization/input/japanese-ime](https://learn.microsoft.com/en-us/globalization/input/japanese-ime)[^50]
- Apple InputMethodKit: [https://developer.apple.com/documentation/inputmethodkit](https://developer.apple.com/documentation/inputmethodkit)[^56]
- Apple IMKCandidates: [https://developer.apple.com/documentation/inputmethodkit/imkcandidates](https://developer.apple.com/documentation/inputmethodkit/imkcandidates)[^13]
- Android InputMethodService: [https://developer.android.com/reference/android/inputmethodservice/InputMethodService](https://developer.android.com/reference/android/inputmethodservice/InputMethodService)[^24]
- Android creating an input method: [https://developer.android.com/develop/ui/views/touch-and-input/creating-input-method](https://developer.android.com/develop/ui/views/touch-and-input/creating-input-method)[^57]
- IBus (Fedora): [https://fedoraproject.org/wiki/I18N/IBus](https://fedoraproject.org/wiki/I18N/IBus)[^16]
- Fcitx5: [https://github.com/fcitx/fcitx5](https://github.com/fcitx/fcitx5)[^21]
- Unicode LDML Part 7 (Keyboards, v48.2): [https://unicode.org/reports/tr35/tr35-keyboards.html](https://unicode.org/reports/tr35/tr35-keyboards.html)[^31]
- CLDR Keyboard 3.0 release note: [https://cldr.unicode.org/downloads/cldr-45](https://cldr.unicode.org/downloads/cldr-45)[^52]
- Unicode UAX #15 (Normalization Forms): [https://unicode.org/reports/tr15/](https://unicode.org/reports/tr15/)[^58]
- Unicode normalization FAQ: [https://unicode.org/faq/normalization.html](https://unicode.org/faq/normalization.html)[^53]
- Hangul Syllables (Unicode): [https://unicodefyi.com/de/guide/hangul-block/](https://unicodefyi.com/de/guide/hangul-block/)[^32]
- InScript keyboard (Wikipedia): [https://en.wikipedia.org/wiki/InScript_keyboard](https://en.wikipedia.org/wiki/InScript_keyboard)[^40]
- Thai WTT standard: Oracle Thai Input Method: [https://docs.oracle.com/cd/E19683-01/817-0493/whatsnew-s9fcs-211/index.html](https://docs.oracle.com/cd/E19683-01/817-0493/whatsnew-s9fcs-211/index.html)[^45]
- HarfBuzz text shaping engine: [https://harfbuzz.github.io/shaping-and-shape-plans.html](https://harfbuzz.github.io/shaping-and-shape-plans.html)[^59]
- Arabic OpenType shaping (Microsoft Typography): [https://learn.microsoft.com/en-us/typography/script-development/arabic](https://learn.microsoft.com/en-us/typography/script-development/arabic)[^43]

---

## References

1. [Improving Japanese Input UX in Multilingual Applications](https://dev.to/oikon/improving-japanese-input-ux-in-multilingual-applications-properly-handling-ime-conversion-2ild) - The Problem: Event Handling During IME Conversion. Japanese input involves a conversion process from...

2. [Japanese input method (JIM) - IBM](https://www.ibm.com/docs/ssw_aix_71/globalization/japan_input_method.html) - The JIM provides Romaji-to-Kana conversion (RKC), allowing the user to type in the phonetic sounds o...

3. [How to commit composing text to an InputConnection when the user ...](https://stackoverflow.com/questions/45205410/how-to-commit-composing-text-to-an-inputconnection-when-the-user-changes-the-sel) - To handle an unfinished composing span you can use finishComposingText on the InputConnection. This ...

4. [TSF を使う (1) - Windows Input Method の歴史](https://nyaruru.hatenablog.com/entry/20070309/p1) - 前回もお伝えしたように，そもそも TSF の話を急いでする必要はなくなりました． Windows Vista で当初私が懸念していた Full IME-aware applications の UI ...

5. [Architecture (Text Services Framework) - Win32 apps](https://learn.microsoft.com/en-us/windows/win32/tsf/architecture) - Architecture

6. [Text Services Framework - Wikipedia](https://en.wikipedia.org/wiki/Text_Services_Framework)

7. [Is TSF framework still available to the public? - Microsoft Learn](https://learn.microsoft.com/en-us/answers/questions/1459476/is-tsf-framework-still-available-to-the-public) - The official TSF docs are not updated, and some pages are even broken. The samples you pointed out a...

8. [第36話：Windows 8にまつわるIMEの裏事情 - ＃モリトーク - 窓の杜](https://forest.watch.impress.co.jp/docs/serial/moritalk/577108.html) - Windows 8の“Windows ストアアプリ（以下、ストアアプリ）”では共通の操作性を提供するために、さまざまなルール・制限が設けられており、その対象のひとつがIMEである。これまでWindow...

9. [MSEdgeExplainers/TSF1/explainer.md at main · MicrosoftEdge/MSEdgeExplainers](https://github.com/MicrosoftEdge/MSEdgeExplainers/blob/main/TSF1/explainer.md) - Home for explainer documents originated by the Microsoft Edge team - MicrosoftEdge/MSEdgeExplainers

10. [What is InputMethodKit on macOS?](https://macosbin.com/bin/inputmethodkit) - The Input Method Kit allows 32-bit applications to work with 64-bit applications. The Input Method K...

11. [Input Method (IMKit) setup trouble - macos - Stack Overflow](https://stackoverflow.com/questions/8960016/input-method-imkit-setup-trouble) - I'm trying to create a new input method using Input Method Kit. The documentation is very lacking, b...

12. [IMKCandidates | Apple Developer Documentation](https://developer.apple.com/documentation/inputmethodkit/imkcandidates) - The class presents candidates to users and notifies the appropriate object when the user selects a c...

13. [IMKCandidates | Apple Developer Documentation](https://developer.apple.com/documentation/inputmethodkit/imkcandidates?changes=_8) - The IMKCandidates class presents candidates to users and notifies the appropriate IMKInputController...

14. [Typing in Linux (ibus) / Sudo Null IT News](https://sudonull.com/post/58761-Typing-in-Linux-ibus) - Programming news, technology, and just useful information

15. [About IBus - International Language Environments Guide for Oracle ...](https://docs.oracle.com/cd/E53394_01/html/E54757/glmks.html) - Intelligent Input Bus (IBus) for the Linux and UNIX operating systems is a powerful multilingual Inp...

16. [I18N/IBus - Fedora Project Wiki](https://fedoraproject.org/wiki/I18N/IBus)

17. [Input method support on Wayland · Issue #4623 · qtile/qtile](https://github.com/qtile/qtile/issues/4623) - Issue description Input method functionality (fcitx5, ibus) doesn't work fully on Wayland backend. I...

18. [Input methods : r/debian - Reddit](https://www.reddit.com/r/debian/comments/175klap/input_methods/) - First, pick an input method framework for you. Your choices include fcitx, fcitx5, ibus, and some ot...

19. [Fcitx5 - ArchWiki](https://wiki.archlinux.org/title/Fcitx5) - Fcitx5 is an input method framework with a lightweight core, offering additional language support vi...

20. [Wayland Integration | fcitx/fcitx5 | DeepWiki](https://deepwiki.com/fcitx/fcitx5/4.2-wayland-integration) - This document describes the Wayland input method frontend implementation in Fcitx5, which enables in...

21. [fcitx/fcitx5: maybe a new fcitx.](https://github.com/fcitx/fcitx5) - Next generation of fcitx, cross-platform input method framework. - fcitx/fcitx5

22. [Write in Indian Languages using IBus in openSUSE 12.1 - Neel's World](https://neelsworld.in/linux-talks/write-in-indian-languages-using-ibus-in-opensuse-12-1-2/) - There are different types of input methods available in GNU/Linux OS:most common being the SCIM (Sma...

23. [A Guide to the 3-Layer Architecture of Japanese Input on Linux: iBus ...](https://zenn.dev/ykbone/articles/60bfd2e045b347?locale=en) - Layer 3: Kana-Kanji Conversion Engine (IME). This layer converts entered Romaji into "Hiragana" or "...

24. [InputMethodService | API reference | Android Developers](https://developer.android.com/reference/android/inputmethodservice/InputMethodService.html)

25. [Input method editor support](https://source.android.com/docs/core/display/multi_display/ime-support)

26. [Simplified Chinese IME - Globalization | Microsoft Learn](https://learn.microsoft.com/en-us/globalization/input/simplified-chinese-ime) - The Microsoft Pinyin Input Method Editor and the Microsoft Wubi Input Method Editor (IME) for Window...

27. [Typing Chinese, character selection issues (windows / pinyin) - Reddit](https://www.reddit.com/r/ChineseLanguage/comments/kr75s8/typing_chinese_character_selection_issues_windows/) - I am in Windows 10, using pinyin input with traditional character output. For example: I want to typ...

28. [Type Chinese using Wubi - Simplified on Mac](https://support.apple.com/fr-fr/guide/chinese-input-method/cimwxs12971/mac) - On your Mac, enter Simplified Chinese characters using the Wubi - Simplified input source.

29. [【ENG·Language Lab】The Oldest Chinese Input Method | Cangjie Input Method | 仓颉输入法](https://www.youtube.com/watch?v=R6HPvYvzAlA) - this time appeared a chinese word, 字根, which is like the stem of a word in English but it’s not the ...

30. [Japanese Keyboard Layout: Everything You Need to Know](https://monsgeek.eu/blogs/guide/japanese-keyboard-layout) - To type Romaji, just type phonetically in the Latin alphabet. For example: Type “arigatou” → IME con...

31. [Unicode Locale Data Markup Language (LDML) Part 7: Keyboards](https://www.unicode.org/reports/tr35/tr35-70/tr35-keyboards.html)

32. [Hangul Block — Unicode-Anleitungen — UnicodeFYI](https://unicodefyi.com/de/guide/hangul-block/) - The Hangul Syllables block (U+AC00–U+D7A3) contains 11,172 precomposed Korean syllable blocks algori...

33. [[RFC] Korean Tokenization: Jamo Decomposition as Pre ... - GitHub](https://github.com/google-deepmind/gemma/issues/596) - Summary. Korean (Hangul) characters should be decomposed into their constituent jamo (consonant/vowe...

34. [Unicode implementer's guide part 3: Conjoining jamo ...](http://useless-factor.blogspot.com/2007/08/unicode-implementers-guide-part-3.html) - Ugh, Korean. In my last two posts on Unicode, I left out something very important: the Korean writin...

35. [Combine or construct korean letters](https://stackoverflow.com/questions/19814497/combine-or-construct-korean-letters) - Is there anyway that I can combine this Korean consonants and vowels into a complete character. For ...

36. [How Hangul works (in Unicode) : r/Korean - Reddit](https://www.reddit.com/r/Korean/comments/1qe3jg/how_hangul_works_in_unicode/) - Korean input method editors (IME) typically keep a buffer of one syllable that can be broken down to...

37. [List of Hangul jamo - Wikipedia](https://en.wikipedia.org/wiki/Hangul_Jamo)

38. [Unicode Fonts and Keyboards](https://www.unicode.org/media/Font-and-Keyboards-UnicodeWebinarSlides-20230515.pdf)

39. [HarfBuzz - Wikipedia](https://en.wikipedia.org/wiki/HarfBuzz)

40. [InScript keyboard - Wikipedia](https://en.wikipedia.org/wiki/InScript_keyboard)

41. [Hebrew keyboard - Wikipedia](https://en.wikipedia.org/wiki/Hebrew_keyboard)

42. [Right-to-Left (RTL) Font Guide | Arabic & Hebrew Web Fonts | 2026](https://font-converters.com/languages/right-to-left-fonts) - Master RTL font setup: CSS direction, bidirectional text handling, Arabic OpenType features, Hebrew ...

43. [Developing OpenType Fonts for Arabic Script - Typography](https://learn.microsoft.com/en-us/typography/script-development/arabic) - Developing OpenType Fonts for Arabic Script

44. [Thai Localization](https://docs.oracle.com/cd/E19683-01/806-6642/asian.supported.locales-8/index.html)

45. [New Thai Input Method](https://docs.oracle.com/cd/E19683-01/817-0493/whatsnew-s9fcs-211/index.html)

46. [Standardization and Implementations of Thai Language](https://www.nectec.or.th/it-standards/thaistd_tr.pdf)

47. [Order and disorder in Unicode - Lontar](https://lontar.eu/en/notes/order-and-disorder-in-unicode/)

48. [Duplicate Combining Characters and How to Fix Them - smokingpiper](https://www.smokingpiper.com/posts/thai-lint-4vscode) - A practical guide to detecting, understanding, and eliminating invisible Unicode bugs in Thai data

49. [Input method (IME) – Google Input Tools](https://www.google.com/inputtools/services/features/input-method.html) - As you type pinyin, e.g., “hao”, you'll see a list of candidate characters that map to your input. Y...

50. [Japanese IME - Globalization - Microsoft Learn](https://learn.microsoft.com/en-us/globalization/input/japanese-ime) - The Japanese Input Method Editor (IME) for Windows lets you enter text using hiragana or katakana ch...

51. [[PDF] L2/11-114 - Unicode](https://www.unicode.org/L2/L2011/11114-uax29-changes.pdf)

52. [CLDR 45 Release Note - Unicode CLDR Project](https://cldr.unicode.org/downloads/cldr-45)

53. [Normalization](https://unicode.org/faq/normalization.html) - Normalization

54. [Uniscribe integration: HarfBuzz Manual](https://harfbuzz.github.io/integration-uniscribe.html)

55. [Text Services Framework (Text Services Framework) - Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/tsf/text-services-framework) - A TSF text service provides multilingual support and delivers text services such as keyboard process...

56. [InputMethodKit | Apple Developer Documentation](https://developer.apple.com/documentation/inputmethodkit) - The Input Method Kit provides classes and protocols for managing communication with client applicati...

57. [Create an input method | Views - Android Developers](https://developer.android.com/develop/ui/views/touch-and-input/creating-input-method) - To add an IME to the Android system, create an Android application containing a class that extends I...

58. [UAX #15: Unicode Normalization Forms](https://unicode.org/reports/tr15/) - Specifies the Unicode Normalization Formats

59. [Shaping and shape plans: HarfBuzz Manual](https://harfbuzz.github.io/shaping-and-shape-plans.html)

