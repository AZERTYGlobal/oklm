Standardized Keyboard Layouts and
Terminology: A Reference for Open
Systems Design
Introduction to Keyboard Standardization and
Typographic Telemetry
The design, architecture, and implementation of modern keyboard layouts operate at the
complex intersection of historical mechanical paradigms, evolving linguistic orthographies, and
strict computational logic. For systems engineers and researchers architecting an open
keyboard layout model, navigating this fragmented landscape requires a precise understanding
of established, de jure standardization frameworks. Rather than reinventing taxonomies to
describe spatial hardware coordinates, modifier states, or character matrices, an open model
must natively integrate the formal vocabulary and geometric abstractions defined by
international and national standards bodies.
This report provides an exhaustive, highly detailed catalog of the formal regulatory frameworks
governing keyboard arrangements. It thoroughly analyzes the multi-part ISO/IEC 9995
architecture, national variants from regulatory organizations such as ANSI/INCITS, DIN, AFNOR,
and JIS, and the modern software bridging technologies managed by the Unicode Consortium,
specifically the Locale Data Markup Language (LDML) Keyboard 3.0 specification. It is
important to note that because the normative texts of standards published by the International
Electrotechnical Commission (IEC) and the International Organization for Standardization (ISO)
are heavily paywalled and restricted by copyright 1, the following architectural analysis
synthesizes their normative mandates and informative annexes utilizing official abstracts,
working group drafts, and reputable secondary institutional summaries.3
By adopting the precise terminology and structural concepts outlined in these standardized
documents, engineers can ensure that an open layout model avoids redundant definitions,
remains universally compatible with existing hardware parsing mechanisms across disparate
operating systems, and possesses the necessary structural architecture to declare formal,
legally recognized conformance to global standards.
The ISO/IEC 9995 Standard Series: Architecture and
Core Concepts
The foundational international standard governing keyboard topologies is ISO/IEC 9995,
formally titled "Information technology — Keyboard layouts for text and office systems."
Initiated by the ISO in 1985 under the proposition of Dr. Yves Neuville, this standard series
abstracts the physical hardware of a human-interface device into a mathematically consistent
geometric grid.5 By completely decoupling the logical software output of a key from its
physical electrical switch, ISO/IEC 9995 creates a universal coordinate system that functions

irrespective of regional languages. The standard has undergone continual evolution, with a
major comprehensive revision culminating between late 2025 and early 2026.5
Multipart Structure and Scope of Governance
The ISO/IEC 9995 standard is not a single document but a modular architecture divided into
distinct, interlocking parts, each governing a specific functional domain of the keyboard.5
ISO/IEC 9995-1:2026 (General principles governing keyboard layouts): This document
serves as the prerequisite standard for the entire series. It defines the physical divisions of the
hardware into sections and zones, establishes the alphanumeric reference grid, and codifies
the core vocabulary utilized throughout the subsequent parts.5 It also governs the depictions
on keytops, specifying three normative ways of key labeling and symbol positioning: columnar
placement, group-1-priorized placement, and level-4-including placement.5 Any hardware or
software claiming conformance to the broader ISO/IEC 9995 framework must inherently
conform to Part 1.3
ISO/IEC 9995-2:2026 (Alphanumeric section): This part strictly governs the primary typing
area, specifically the alphanumeric zone and its adjacent function zones.5 It defines what
constitutes a "graphic key" (a key used to input characters) versus a "function key" (a key used
for control functions).3 Crucially, Part 2 specifies the "harmonized 48–50 graphic key keyboard
arrangement," establishing exact geometric boundaries and requirements for layout density.5 It
also defines the critical mechanisms for level selection, dictating how shifting algorithms
operate across the character matrix.5
ISO/IEC 9995-3:2026 (Latin International keyboard layout): This part addresses the
complexities of multilingual input. Earlier editions (notably the 2002 and 2010 versions) defined
a "common secondary group" or "complementary layout," which was essentially a standardized
secondary mapping overlay based on the Unicode MES-1 subset.5 This overlay could be added
to existing national layouts to allow users to type characters from neighboring European
languages.5 The sweeping 2026 revision fundamentally redesigned this approach, replacing the
supplementary overlay concept with a standalone, comprehensive "Latin International" layout.5
ISO/IEC 9995-4:2025 and ISO/IEC 9995-8:2009 (Numeric sections): Part 4 specifies the
layout of numeric keypads, accommodating both the traditional calculator-style "7-8-9" top
row and the telephone-style "1-2-3" top row.5 Part 8 explicitly governs the allocation of
alphabetic letters to the keys of a numeric keypad, a standard that originated to facilitate
mobile phone text entry and specialized numeric-alphabetic mapping.5
ISO/IEC 9995-5:2009 (Editing and function section): This part specifies the placement of
navigation and editing keys. It formally mandates that the Escape key must be located at
position K00 (or to the left of it) on the reference grid. It also strictly dictates that the four
primary cursor arrows (up, down, left, right) must be arranged in either a "cross layout" or an
"inverted T layout," with the "cursor down" key placed on the same geometric row as the space
bar.5 Note that ISO/IEC 9995-6 (Function section) was formally withdrawn in October 2009,
with its relevant clauses absorbed into Part 5.5
ISO/IEC 9995-7:2009 and ISO/IEC 9995-10:2025 (Symbols and visual representations):

Part 7 (augmented by Amendment 1 in 2012) establishes a universal, language-agnostic
iconography for control functions.5 By utilizing standardized symbols for actions like "Escape,"
"Control," or "Compose," hardware manufacturers can bypass localization requirements.9 Many
of these symbols have been formally encoded into the Unicode standard.5 Part 10 provides
visual disambiguation conventions for "peculiar characters"—characters that appear visually
identical in standard typography but carry different computational meanings. It establishes
methods to uniquely identify symbols such as em-dashes versus en-dashes on physical
keytops and in software documentation.5
ISO/IEC 9995-9, 9995-11, and 9995-12 (Advanced input mechanisms): Part 9 (2026) governs
groups and mechanisms for multilingual and multiscript input, standardizing how a user
switches between entirely different writing systems on a single hardware device.5 Part 11 (2026)
is dedicated to the functionality and labeling of dead keys. It standardizes how non-spacing
diacritical markers should behave and how they must be visually represented on keytops, such
as the use of the special dead key for the horizontal crossbar used in languages like Maltese
and Serbo-Croatian.2 Finally, Part 12 (2020) governs keyboard group selection logic, formalizing
the algorithms for switching between language groups.5
Functional Sections, Zones, and the Key Reference Grid
To create a mathematically universal language for hardware geometry, ISO/IEC 9995-1 divides
the physical keyboard into functional sections, which are subsequently subdivided into zones.5
The primary division is the Alphanumeric Section, which contains the Alphanumeric Zone (ZA0)
housing the graphic keys, flanked by the Left Function Zone (ZA1) and Right Function Zone
(ZA2) housing boundary control modifiers.5 Separate from this core section are the Numeric
Section (composed of the numeric zone ZN0 and function zone ZN1) and the Editing and
Function Section (composed of the cursor key zone ZEF0 and editing function zone ZEF1).10
The most vital conceptual tool defined by the standard, and one that an open layout model
must adopt natively, is the Key Reference Grid.5 Rather than referring to a key by its printed
legend (which changes depending on the regional layout mapping) or its hardware USB
scancode (which is bound to proprietary firmware and physical port logic), the ISO grid assigns
an absolute, language-agnostic alphanumeric coordinate to every physical switch on the
keyboard.3
Under this grid system, horizontal rows are designated by letters. The space bar is located on
Row A. Progressing upwards through the alphanumeric section, the bottom alphabetic row
(the 'Z' row in a QWERTY layout) is Row B, the home row is Row C, the upper alphabetic row is
Row D, and the numeric row is Row E.7 If keys are located below the space bar, they are
designated with Z-series letters descending (Z, Y, X). Rows positioned above the alphanumeric
section (such as the traditional F1-F12 function key rows) are designated with K-series letters
ascending.3
Columns are numbered systematically from left to right, starting at 00. Therefore, the key in the
bottom-left corner of the main alphabetic block is precisely designated as B00, while the '1' key
on the numeric row is designated as E01.7 Column numbering for editing or function keys

begins at 60 and ascends if placed to the right of the numeric section, or starts at 80 and
descends if placed to the left of the alphanumeric section.5 This geometric coordinate system
is entirely agnostic to the physical staggering of the keys; whether the keyboard utilizes a
traditional staggered typewriter arrangement or an ortholinear (grid-aligned) matrix, the ISO
reference grid remains mathematically valid and structurally applicable.5
Levels, Groups, and State Selection Mechanisms
To address the spatial limitations of standard hardware, ISO/IEC 9995 implements a complex
hierarchical state-machine architecture defined by "Levels" and "Groups".5 When designing an
open layout model, systems engineers must strictly adhere to this formal nomenclature rather
than relying on colloquial or arbitrary terms like "layers," "fn-states," or "shift states."
A "Level" represents a specific logical state within a given layout mapping.5 ISO/IEC 9995-2
explicitly defines up to four levels per graphic key. Level 1 represents the unshifted base state,
typically generating lowercase letters or primary digits.5 Level 2 represents the shifted state,
accessed via the Level 2 Select key (commonly known as the Shift key), which generates
uppercase letters or secondary punctuation.5 Level 3 is accessed via the Level 3 Select key, a
modifier commonly designated on hardware as AltGr (Alternative Graphic). Level 4 is a highly
specialized state accessed via a simultaneous combination of Level 2 and Level 3 Select
modifiers (AltGr + Shift). Because accessing Level 4 often requires a difficult, multi-finger
"guitar chord grip," the standard's normative guidelines advise reserving Level 4 strictly for
obscure or rarely used typographical symbols.5
When four levels are geometrically or linguistically insufficient to accommodate a user's
typographic requirements—or when a user needs to alternate between entirely disparate
writing systems (such as transitioning from Latin to Cyrillic or Arabic)—the standard introduces
the architectural concept of "Groups".5 A Group is a higher-order container that holds its own
distinct set of up to four Levels. Group selection can be configured in hardware or software as
a temporary latch (holding a modifier key to access Group 2 momentarily) or as a persistent
lock (pressing a modifier key to toggle into Group 2 indefinitely).5 The specific mechanics of
these state changes are governed collaboratively by ISO/IEC 9995-2, 9995-9, and 9995-12.5
Rules for Declarations and Formal Conformance
For a keyboard layout software model, hardware peripheral, or driver to formally declare
conformance to ISO/IEC 9995, it must explicitly and precisely state which specific parts of the
standard it complies with.3 A blanket marketing claim of "ISO 9995 Compliant" is considered
invalid under the standard's own rules.3 The declaration must read, for example, "Conforms to
the general principles of ISO/IEC 9995-1:2026 and the alphanumeric section requirements of
ISO/IEC 9995-2:2026."
Compliance with ISO/IEC 9995-2 specifically requires fulfilling strict hardware and mapping
mandates.7 A manufacturer or software architect must choose between two paths of
compliance. They may meet the requirements of Clause 7.1 (General keyboard arrangement),
which requires the alphanumeric zone to have a space bar and at least 47 graphic keys.7

Alternatively, they may meet the requirements of Clause 7.2 (Harmonized 48 graphic key
keyboard arrangement), which mandates exactly 48 graphic keys and one space bar placed
precisely according to a predefined row-by-row specification.7 Both compliance paths strictly
require meeting Clause 8.3 (Minimum function key requirements), which mandates the
presence of specific control functions, including Tabulation, Return, Level 2 Select, and Level 3
Select.7
Furthermore, while Annex A of ISO/IEC 9995-2 provides an informative guideline for the
placement of Latin letters (establishing the historical foundation for familiar layouts like
QWERTY, AZERTY, and QWERTZ), this annex is explicitly informative rather than normative.5
Therefore, alternative ergonomic character layouts like the Dvorak keyboard or the Turkish
F-keyboard can legally claim full ISO/IEC 9995-2 conformance, provided they meet the
geometric and functional prerequisites of Clauses 7 and 8.5
Glossary of Normative ISO/IEC 9995 Vocabulary
To prevent terminology fragmentation and ensure alignment with official standards, engineers
developing an open layout model must strictly adopt the following normative definitions
provided by the ISO/IEC 9995 texts.3
ISO/IEC 9995 Term  Precise Normative  Functional Implication for
|     | Definition  | Open Layout Models  |
| --- | ----------- | ------------------- |
Section  A primary physical division  Dictates the macro-level
|       | of the keyboard unit (e.g.,  | bounding boxes and          |
| ----- | ---------------------------- | --------------------------- |
|       | Alphanumeric, Numeric,       | physical clustering of      |
|       | Editing).                    | hardware topologies.        |
| Zone  | A localized subdivision      | Determines the operational  |
|       | within a Section (e.g.,      | domain of a key,            |
|       | Alphanumeric Zone ZA0,       | differentiating character   |
|       | Function Zone ZA1).          | input zones from system     |
control borders.
Level  A logical state of character  Replaces colloquial terms
|     | output selected during         | like "layer." A standard    |
| --- | ------------------------------ | --------------------------- |
|     | input, typically via Shift or  | graphic key maxes out at    |
|     | AltGr modifiers.               | four distinct Levels under  |
normal ISO definitions.
| Group  | A discrete hierarchical   | Used to switch entirely       |
| ------ | ------------------------- | ----------------------------- |
|        | repertoire of characters  | between scripts (e.g., Latin  |
|        | encompassing up to four   | to Cyrillic) or to access     |
deep secondary

|     | Levels.  | mathematical/symbolic  |
| --- | -------- | ---------------------- |
layouts.
Secondary Group  A modifier key or sequence  Enables multi-script
Selector  (often AltGr or a dedicated  functionality on a single
|     | key) that shifts the active  | hardware peripheral         |
| --- | ---------------------------- | --------------------------- |
|     | matrix to a secondary        | without requiring OS-level  |
|     | character Group.             | language switching          |
interfaces.
Key Reference Grid  A mathematically pure  Allows engineers to
|     | coordinate system        | reference a physical switch   |
| --- | ------------------------ | ----------------------------- |
|     | designating keys by Row  | (e.g., "B00") independently   |
|     | (A-Z, K) and Column      | of the localized glyph        |
|     | (00-99).                 | printed on its keycap or its  |
OS scancode.
| Graphic Key   | A key whose primary           | Distinguishes character     |
| ------------- | ----------------------------- | --------------------------- |
|               | purpose is to input a         | data inputs from            |
|               | character, symbol, or         | system-level interrupt      |
|               | graphical element.            | requests.                   |
| Function Key  | A key whose primary           | Handled via specific        |
|               | purpose is the input of a     | scancode interrupts rather  |
|               | control function rather than  | than UTF-8 string outputs.  |
a printable character.
Active Position  The character position  In general software
|     | which is to image the  | environments, the active    |
| --- | ---------------------- | --------------------------- |
|     | graphic symbol         | position is indicated in a  |
|     | representing the next  | display by a cursor.        |
graphic character.
Associated System  The overarching system to  The OS and drivers that
|     | which the keyboard is     | intercept the scancodes        |
| --- | ------------------------- | ------------------------------ |
|     | attached, comprising      | and translate them based       |
|     | processors and software.  | on the active layout profile.  |
National and Regional De Jure Standards

While ISO/IEC 9995 provides the universal geometric and structural framework, individual
national standardization bodies dictate the precise character mappings and cultural semantics
utilized within their specific jurisdictions. These de jure standards are tightly bound to national
orthographic reforms, localized ergonomic philosophies, and the historical lineage of
mechanical typewriters.
United States: ANSI-INCITS 154
In the United States, keyboard arrangements are governed by the American National Standards
Institute (ANSI) and the InterNational Committee for Information Technology Standards
(INCITS). The governing normative document is strictly designated as INCITS 154-1988
(formerly known under the designation ANSI X3.154-1988 (R1999)), formally titled "Office
Machines and Supplies – Alphanumeric Machines – Keyboard Arrangement".16
Unlike many European standards that have undergone significant computational modernization
to support extended character sets, INCITS 154 remains heavily tethered to its 19th-century
mechanical origins. The layout traces its direct lineage to the Sholes & Glidden typewriter.16 The
popular historical theory behind the QWERTY mapping standardized by ANSI asserts that its
creators designed the layout to spread out commonly paired letters, thereby preventing the
mechanical typebars from jamming when struck in rapid succession.16 This mechanical debt is
permanently codified in the modern standard.
The ANSI standard dictates a 104-key physical footprint (or a 109-key variant in specific
extended configurations). It is geometrically characterized by a horizontally elongated Return
key spanning a single row, and the placement of the backslash/pipe key directly above the
Return key.19 Because standard English typography lacks complex diacritical marks or accented
vowels, INCITS 154 effectively utilizes only two Levels (Base and Shift), operating completely
without the necessity of a Level 3 Select (AltGr) key.19 This simplicity makes it the baseline for
many computing systems, but limits its utility for multilingual users.
Germany and Austria: DIN 2137
The Deutsches Institut für Normung (DIN) regulates German-language keyboard layouts under
the DIN 2137 standard, which is widely used across Germany, Austria, and parts of Central
Europe.14 This standard experienced a monumental revision in 2023, designated as DIN
2137-01:2023-08, making it one of the most mechanically sophisticated implementations of the
ISO/IEC 9995 framework currently in existence.21
Historically, the standard defined a basic QWERTZ layout known as "T1" (Tastaturbelegung 1),
characterized by transposing the Y and Z keys relative to the English QWERTY layout to
optimize for the higher frequency of 'Z' in the German vocabulary, and providing dedicated
keys for umlauted vowels (Ä, Ö, Ü) and the sharp s (ß).14 In 2012, DIN attempted to modernize
by introducing the "T2" and "T3" layout extensions to support Vietnamese, Arabic, European
minority languages, and complex scientific inputs.21 However, the T2 and T3 layouts failed to
achieve market penetration because they required a dedicated Group Selection key, which
necessitated non-standard hardware modifications that manufacturers refused to adopt.23
Learning from this hardware failure, the 2023 revision deprecated the T2 and T3 layouts entirely,

replacing them with two highly capable, hardware-agnostic layouts: "E1" (Erweitert 1) and "E2"
(Erweitert 2).21 The E1 layout maps onto the standard 105-key ISO physical format. It utilizes
exhaustive Level 3 (AltGr) and Level 4 (AltGr + Shift) assignments to provide access to every
single character required by the primary official languages of the world and European minority
languages utilizing Latin scripts.21 It also formally introduces an "Extra Selector" key mechanism
(functioning effectively as an ISO/IEC 9995 Level 5 shift or compose sequence) to generate
horizontal ellipses, directional arrows, transcription characters, and even invoke an emoji
selection function.21 The E2 layout provides an identical logical software mapping but is
structurally adapted to function on 104-key ANSI hardware, ensuring that users lacking the
extra ISO B00 key (the key next to the left Shift) can still access the complete typographical
repertoire using alternative modifier sequences.21
France: AFNOR NF Z71-300
French keyboard standards experienced a computational renaissance with the publication of
the Association Française de Normalisation (AFNOR) voluntary standard NF Z71-300 in April
2019.26 The French Ministry of Culture—specifically the General Delegation for the French
Language and the Languages of France—initiated this project upon observing that the legacy
AZERTY layout was structurally incapable of producing proper French typography. The old
layout critically lacked uppercase accented letters (É, Ç), essential typographic ligatures (æ, œ),
and standard French guillemets (« »).26
NF Z71-300 formally codifies two distinct layouts to resolve these deficiencies.29 The first is an
optimized, modernized AZERTY layout. Unlike historical layouts based on typewriter mechanics,
this new AZERTY was developed using complex computer algorithms analyzing massive French
text corpora, including newspapers, programming code, and Twitter data, combined with
ergonomic keystroke telemetry.29 While unaccented letters and numbers remain in their legacy
positions to preserve user muscle memory, the standard extensively utilizes AltGr mechanisms
to group logical symbols together. For instance, all bracket types have opening and closing
forms on adjacent keys, and mathematical symbols are clustered together.28
The second layout standardized under NF Z71-300 is BÉPO. BÉPO is an ergonomic layout
heavily inspired by Dvorak principles, which places high-frequency vowels and consonants on
the home row to drastically minimize finger travel and repetitive strain.27 An open layout model
targeting the French demographic must specify whether it implements the legacy OS-based
AZERTY configuration, the normative NF Z71-300 algorithmic AZERTY, or the BÉPO mapping.30
Japan: JIS X 6002 and JIS X 6004
The Japanese Industrial Standards (JIS) committee navigates the profound unique challenge of
inputting three distinct scripts—hiragana, katakana, and kanji—through a Latin-based hardware
interface. The foundational standard is JIS X 6002:1980 ("Keyboard layout for information
processing using the JIS 7 bit coded character set").20 JIS X 6002 dictates a 109-key physical
layout featuring a massive, visually distinct inverted-L Return key and a severely truncated
Space bar. The abbreviated Space bar makes physical room for critical Group-shifting and

conversion keys: Muhenkan (Non-conversion), Henkan (Conversion), and the
Hiragana/Katakana toggle.33
Input under JIS X 6002 typically functions through Romaji, requiring a multi-stage input logic.34
A user types Latin letters (e.g., "ka"), which the physical keyboard sends as scancodes. The
operating system's Input Method Editor (IME) intercepts this Romaji stream and automatically
converts it to hiragana (e.g., "か"). Pressing the space bar or the Henkan key opens a candidate
window, allowing the IME to parse grammar rules and propose kanji variants (e.g., "加／河／花
／科").33
However, the standard also defines a direct Kana input layer, where each physical key
corresponds directly to a hiragana character printed on the keycap.35 In 1986, JIS published JIS
X 6004, which attempted to optimize this direct Kana arrangement based on ergonomic
n-gram frequency analysis, functioning essentially as a "Japanese Dvorak".32 While X 6004 was
analytically superior, it failed to supplant the massive market inertia of X 6002 and was formally
abolished as a standard in 1999, though its variations remain actively utilized by niche
enthusiast communities.36 Today, the physical hardware format is widely standardized around
the OADG 109 layout, which builds upon the JIS framework.37
Russia: GOST 6431-90
The Russian Federation relies on the JCUKEN layout for Cyrillic input, tracing its lineage directly
back to early 20th-century Soviet-era typewriters.39 The de jure specification governing this
arrangement is GOST 6431-90.39
A critical historical divergence occurred with the advent of personal computing. Unix-like
operating systems and OpenSolaris adopted the strict GOST 6431-90 layout, which simulates a
typewriter. In this strict GOST layout, numbers are relegated to the shifted state of the top row,
prioritizing rapid access to punctuation marks without requiring a shift modifier.39 Conversely,
when Microsoft entered the Russian market, they engineered an altered JCUKEN-QWERTY
variant for MS-DOS and Windows. This Windows variant placed the numbers in their standard
unshifted positions, forcing punctuation into shifted states.39 Therefore, an open layout model
must distinguish between "Russian (Typewriter/GOST)" and "Russian (Windows)" mappings to
avoid completely disrupting a user's punctuation muscle memory.40 Additionally, GOST
16876-71 dictates the scientific transliteration system for converting Cyrillic characters to Latin,
which is critical for phonetic keyboard layers.42
Brazil: ABNT NBR 10346
In Brazil, keyboard layouts are governed by the Associação Brasileira de Normas Técnicas
(ABNT), specifically under the NBR 10346 (alphanumeric portion) and NBR 10347 (numeric
portion) standards.44 The Brazilian layout requires a unique physical alteration to the standard
ISO hardware geometry. To accommodate the frequent use of the letter 'Ç' (cedilha), the ABNT
standard inserts a 48th graphic key on Row C, located directly between the semicolon key and
the Right Shift key.44 An open model must explicitly account for this physical Key Arrangement
anomaly (often designated as C12 in the ISO grid) when generating scancode mappings for

Brazilian Portuguese input, as it splits the standard ISO Right Shift key into two separate
discrete keys.7
Nordic Configurations
Rather than relying on heavily isolated national standards, the Nordic countries (Sweden,
Denmark, Norway, Finland) utilize a closely harmonized regional implementation that overlays
strictly onto the standard ISO geometry.47 While localized national variations exist (e.g., the
Icelandic standard ÍST 125, or the Swedish standard SS 662241), they share a unified
architecture that places their unique linguistic vowels (Æ, Ø, Å in Danish/Norwegian; Ä, Ö, Å in
Swedish/Finnish) in the upper right quadrant of the alphanumeric zone.47 This positioning
displaces standard punctuation characters, forcing them into AltGr (Level 3) layers. The
cross-compatibility of these Nordic layouts relies entirely on the uniform implementation of the
ISO Left Shift truncation to accommodate the < > key at grid position B00.13
Physical Form Factors and Geometric Mapping
The historical divergence between the aforementioned national standards has resulted in four
primary physical form factors that dictate modern hardware manufacturing. An open layout
model cannot simply output characters into a void; it must map those characters to specific
geometric coordinate frames to function correctly across different devices.
1. ANSI (American Form Factor): Derived from INCITS 154, this layout features 104 keys. It
is defined geometrically by a wide, single-row Enter key (spanning Row C entirely), and a
wide Left Shift key. Crucially, the ISO grid position B00 does not physically exist on this
layout.19
2. ISO (European/Global Form Factor): Based on the geometric arrangements suggested
in ISO/IEC 9995-2, this layout features 105 keys. The Enter key spans Rows C and D
vertically, forming a distinct inverted-L shape. The Left Shift key is truncated to
accommodate the extra key at position B00, which typically hosts angle brackets,
backslashes, or broken bars depending on the localized mapping.13
3. JIS (Japanese Form Factor): Based on JIS X 6002, this layout features 109 keys. It
retains the vertical Enter key of the ISO layout but physically truncates the Backspace key
to add a dedicated yen/pipe key at position E13. It also severely truncates the space bar
to add physical conversion keys at positions A03, A05, and A07.7
4. ABNT (Brazilian Form Factor): A specialized variant of the ISO layout that splits the
Right Shift key to add a dedicated physical key (position C12) for the cedilla character on
the home row.7
When documenting and architecting an open layout model, engineers must reference these
physical topologies using the ISO/IEC 9995-1 grid coordinates. Stating that a character
mapping targets "Key B00" provides unambiguous, universal telemetry. It guarantees that the
software driver expects an electrical input from the switch located immediately to the right of
the Left Shift key, regardless of whether the physical keycap displays a < (Nordic), \ (UK), or |
(German).13

Keycap Legends, Marking Norms, and Symbolic
Standards
To ensure visual consistency and facilitate language-agnostic hardware manufacturing, an
open layout model must align its graphical outputs and interface documentation with the
symbol sets defined in ISO/IEC 9995-7 and ISO/IEC 9995-10.
ISO/IEC 9995-7: Control Functions and Unicode Integration
ISO/IEC 9995-7 standardizes the iconography utilized for control modifiers. By referencing
these standards, an open model avoids the need to localize system labels across dozens of
languages, preventing cluttered UI or hardware.9 Many of these symbols have been formally
adopted into the Unicode standard, specifically within the Miscellaneous Technical and
Miscellaneous Symbols and Arrows blocks, allowing open software models to render them
natively in text.5
Critical control mappings include:
● Alternative Key (Alt): Symbolized by ISO-7000-2105, encoded as U+2387 (⎇
ALTERNATIVE KEY SYMBOL).52
● Control Key (Ctrl): Symbolized by the helm symbol, encoded as U+2388 (⎈ CONTROL
KEY SYMBOL).53
● Compose / Multi Key: Symbol 15 in ISO/IEC 9995-7, encoded as U+2384 (⎄
COMPOSITION SYMBOL).54
● Group Selection: Symbolized by specific enclosing arrows or rounded squares, mapped
to Unicode characters such as U+20F1 (COMBINING ENCLOSING SQUARE WITH
ROUNDED CORNERS).55
Dead Keys and Peculiar Characters
ISO/IEC 9995-11 strictly governs the behavior and labeling of "dead keys"—specialized modifier
keys that do not instantly produce a glyph but rather alter the subsequent keystroke to
produce a precomposed Unicode character featuring a diacritic.2 To comply with the standard,
keycap manufacturers and virtual keyboard designers must engrave or display dead keys
utilizing spacing variants of the diacritic, often accompanied by a dashed rectangular box
indicating the base letter's location relative to the mark.5
Furthermore, ISO/IEC 9995-10 provides disambiguation symbols for "peculiar characters." If an
open model maps a typographic quote or a specific dash, it should reference the Part 10 visual
guidelines to ensure users can differentiate a minus sign from an en-dash or em-dash on the
physical hardware or within the software's layout preview documentation.5
Interoperability: OS Implementations and Unicode
LDML
The translation mechanism from a physical keystroke to a digital character relies entirely on the
host parsing software. An open layout model must reconcile the theoretical geometric

perfection of ISO standards with the highly idiosyncratic legacy implementations found in
modern Operating Systems (OS) and markup languages.
Operating System Deviations (XKB vs Windows vs macOS)
While Windows and macOS handle keyboard mapping through proprietary, closed-source
binary drivers (often utilizing rigid state-machines that limit complex dead-key chaining),
Unix-like systems (Linux, OpenSolaris) utilize the X Keyboard Extension (XKB).11 XKB introduces
a historical conceptual conflict with the formal ISO/IEC 9995 nomenclature.
In the pure ISO/IEC 9995 specification, shifting to an AltGr state accesses "Level 3" of the
currently active character group.5 XKB, however, historically confused the structural concepts
of Levels and Groups.59 In XKB architecture, a key can be defined programmatically as
ONE_LEVEL, TWO_LEVEL, or FOUR_LEVEL.58 While XKB supports multiple Levels, legacy
implementations frequently abused the "Group" functionality to achieve Level 3 outputs (e.g.,
configuring Mode_switch to access Group 2 instead of properly utilizing Level 3).58 An open
model must explicitly map ISO Level 3 (AltGr) logic directly to XKB Level 3 syntax to maintain
modern standard compliance and ensure ongoing compatibility with Wayland compositors,
completely bypassing deprecated tools like xmodmap.57 On macOS, the model must account
for the Option key, which functions similarly to AltGr but possesses its own unique ecosystem
of modifier behaviors and symbols.52
Unicode LDML Keyboard 3.0 Specification
The ultimate bridge between formal hardware topologies and open software implementations
is the Common Locale Data Repository (CLDR) Locale Data Markup Language (LDML).61
Managed by the Unicode Consortium, LDML Part 7 (UTS #35) defines a universal,
cross-platform XML format for keyboard configurations, allowing a layout to be defined once
and deployed anywhere.61
In CLDR Version 44/45, the Unicode Consortium undertook a massive architectural rewrite of
the standard, officially designated as "Keyboard 3.0" (utilizing the <keyboard3> root element).64
This specification is highly relevant to open layout models for several critical reasons:
1. Unified Ecosystems: The <keyboard3> schema fundamentally unifies physical hardware
definitions with virtual, touch-based mobile keyboards, allowing a single XML file to
dictate behavior across all device types seamlessly.63
2. Schema Enforcement and BCP47: Keyboards submitted to the CLDR must pass rigid
XML schema validations (.xsd). All locale IDs within the keyboard definition must be
minimized according to BCP47 tags, ensuring strict linguistic tracking.64
3. Transforms over Dead Keys: Keyboard 3.0 deliberately shifts away from relying on
hardcoded OS dead-key logic. Instead, it utilizes regex-like <transforms> and
<transformGroup> elements.64 This architectural change allows the layout model itself to
govern complex ligature creation and diacritical combining logic, transferring control
from the host OS kernel directly to the layout architect.
4. Backspace Telemetry: The standard introduces explicit backspace transforms. This

allows layout authors to dictate whether striking the Backspace key deletes a
precomposed character entirely or incrementally strips the combining diacritics one by
one, ensuring intuitive behavior for complex scripts.64
Catalog of De Jure Standards and Scopes
The following table catalogs the authoritative standards that an open model must reference
when establishing locale-specific configurations, bridging the gap between national mandates
and software implementation:
| Standard     | Scope /  | Key Concepts  | Current  | Relation to OS  |
| ------------ | -------- | ------------- | -------- | --------------- |
| Designation  | Nation   | Defined       | Edition  | / LDML          |
ISO/IEC 9995  Global (Base  Reference grid,  2026 (Major  Serves as the
(Parts 1-12)  Framework)  levels, groups,  revision of  structural
|     |     | dead keys,  | Parts 1, 2, 3, 9,  | baseline; maps  |
| --- | --- | ----------- | ------------------ | --------------- |
|     |     | symbols,    | 11)                | directly to     |
|     |     | functional  |                    | LDML <layers>.  |
zones.
| ANSI INCITS  | United States  | 104-key           | 1988     | Serves as the    |
| ------------ | -------------- | ----------------- | -------- | ---------------- |
| 154          |                | physical          |          | default          |
|              |                | geometry,         |          | physical         |
|              |                | wide Return       |          | hardware map     |
|              |                | key, absence      |          | in               |
|              |                | of grid position  |          | Windows/mac      |
|              |                | B00.              |          | OS/XKB.          |
| DIN 2137-01  | Germany /      | T1 legacy         | 2023-08  | Relies heavily   |
|              | Austria        | layout; E1 (ISO   |          | on AltGr (Level  |
|              |                | hardware) and     |          | 3) and Extra     |
|              |                | E2 (ANSI          |          | Selector (Level  |
|              |                | hardware)         |          | 5) concepts.     |
extended
mappings.
| AFNOR NF  | France  | Algorithmic      | 2019  | Standardizes     |
| --------- | ------- | ---------------- | ----- | ---------------- |
| Z71-300   |         | modernized       |       | previously       |
|           |         | AZERTY,          |       | fractured        |
|           |         | ergonomic        |       | OS-level         |
|           |         | BÉPO, French     |       | AZERTY           |
|           |         | ligatures/guille |       | variants into a  |
|           |         | mets.            |       | cohesive         |

model.
| JIS X 6002 / X  | Japan  | 109-key         | 1980 / 1986  | Requires deep  |
| --------------- | ------ | --------------- | ------------ | -------------- |
| 6004            |        | hardware,       |              | integration    |
|                 |        | Henkan/Muhen    |              | with OS-level  |
|                 |        | kan conversion  |              | Input Method   |
|                 |        | keys, direct    |              | Editors (IME)  |
|                 |        | Kana mapping.   |              | for Romaji     |
conversion.
| GOST     | Russia  | JCUKEN       | 1990  | Significant      |
| -------- | ------- | ------------ | ----- | ---------------- |
| 6431-90  |         | layout,      |       | conflicts exist  |
|          |         | typewriter   |       | between strict   |
|          |         | punctuation  |       | GOST (Unix)      |
|          |         | origins.     |       | and Windows      |
variants.
| ABNT NBR  | Brazil  | ISO variant   | 1991  | Requires       |
| --------- | ------- | ------------- | ----- | -------------- |
| 10346     |         | requiring an  |       | custom         |
|           |         | extra Row C   |       | software       |
|           |         | key for the   |       | mapping for    |
|           |         | Cedilha (Ç).  |       | the anomalous  |
physical key
C12.
Implications for an Open Layout Model
The synthesis of these historical, geometric, and computational standards reveals highly
actionable directives for engineers designing an open layout model. To guarantee
interoperability, longevity, and professional adoption, the model must embrace ISO/IEC 9995
taxonomy and utilize Unicode LDML schema as its primary transport layer.
1. Adoption of Standardized Terminology:
The open model must entirely abandon proprietary, OS-specific, or hobbyist terminology (e.g.,
"layers," "fn-toggles," "shift-states"). All internal documentation and code architecture should
strictly utilize the term Levels to denote shift-states (like Shift and AltGr) and Groups to denote
macro-state changes between entirely different scripts. Furthermore, physical key addressing
within the source code must map directly to the ISO Key Reference Grid (e.g., defining an
action for Key_C12 or Key_B00 rather than Key_Backslash). This ensures that the hardware
interface remains mathematically pure and totally agnostic to the linguistic overlay applied by
the user.

2. Declaration of Conformance:
The open model can formally declare conformance by stating precise subset alignments rather
than making legally invalid blanket claims. For instance, the core geometry engine
documentation should state, "Conforms to the General Principles and Key Reference Grid of
ISO/IEC 9995-1:2026." Individual layout configuration files can then declare regional
compliance, such as, "This French mapping profile conforms to AFNOR NF Z71-300 (AZERTY
variant)." Conformance claims regarding ISO/IEC 9995-2 must specify whether the layout
complies with Clause 7.1 (General arrangement) or Clause 7.2 (Harmonized 48 graphic key
arrangement), and confirm adherence to the Clause 8.3 function key requirements.
3. Utilizing LDML <keyboard3> Architecture:
The model should adopt the CLDR LDML <keyboard3> XML schema as its native configuration
language. By architecting around this standard, the model inherits the capability to compile and
generate layouts for Windows, macOS, Linux (XKB), iOS, and Android from a single source of
truth. Furthermore, relying on LDML's <transforms> element allows the layout to resolve
complex dead-key combinatorics internally. This prevents the host Operating System's
text-rendering engine from improperly handling national typographic requirements, ensuring
perfect execution of complex standards like DIN 2137-01:2023-08 or AFNOR NF Z71-300.
4. Iconography and Keycap Metadata Integration:
When generating graphical representations of the layout (such as virtual on-screen touch
keyboards or SVG reference files for hardware keycap manufacturing), the model must link
control functions to the official Unicode mappings of ISO/IEC 9995-7 (e.g., U+2387 for Alt,
U+2388 for Control). This guarantees that the layout remains visually compliant with
international usability standards, avoiding hardcoded linguistic text strings that break
localization efforts and clutter the visual interface.
Sources des citations
1. ISO/IEC 9995-1:2026, consulté le juin 7, 2026,
https://webstore.iec.ch/en/publication/111520
2. ISO/IEC 9995-11:2026, consulté le juin 7, 2026,
https://webstore.iec.ch/en/publication/111518
3. INTERNATIONAL STANDARD - Open Standards, consulté le juin 7, 2026,
https://www.open-std.org/jtc1/sc35/wg1/docs/madison/SC35N791%20ISO-CEI%2
09995-1%20FCD(en).doc
4. DOD Information Technology Standard Guidance (ITSG) Version 3.1 - DTIC,
consulté le juin 7, 2026, https://apps.dtic.mil/sti/tr/pdf/ADA286922.pdf
5. ISO/IEC 9995 - Wikipedia, consulté le juin 7, 2026,
https://en.wikipedia.org/wiki/ISO/IEC_9995
6. Information technology — Keyboard layouts for text and ... - Unicode, consulté le
juin 7, 2026,
https://www.unicode.org/L2/Historical/EdHart-X3L2-Arch-2004-02-12/ISO09995/
Copy%20of%20ISO%209995-1%20Principles.html
7. ISO/IEC 9995-2 - iTeh Standards, consulté le juin 7, 2026,
https://cdn.standards.iteh.ai/samples/51644/fe874182c6274a6a8148fa4f17732968/I

SO-IEC-9995-2-2009.pdf
8. ISO/IEC 995-5 - iTeh Standards, consulté le juin 7, 2026,
https://cdn.standards.iteh.ai/samples/17913/710ea6f21a3249f4ba4dbff508a21670/
ISO-IEC-9995-5-1994.pdf
9. EG 202 132 - V1.1.1 - Human Factors (HF); User Interfaces - ETSI, consulté le juin 7,
2026,
https://www.etsi.org/deliver/etsi_eg/202100_202199/202132/01.01.01_60/eg_2021
32v010101p.pdf
10. ISO/IEC 9995-1 - iTeh Standards, consulté le juin 7, 2026,
https://cdn.standards.iteh.ai/samples/51645/8a32c7971efc4a52ac12e9416f828758/
ISO-IEC-9995-1-2009.pdf
11. Keyboard layout - Wikipedia, consulté le juin 7, 2026,
https://en.wikipedia.org/wiki/Keyboard_layout
12. ISO/IEC 9995-2 - iTeh Standards, consulté le juin 7, 2026,
https://cdn.standards.iteh.ai/samples/36042/03e673414f4241ce839e9b1bad5bdb
cd/ISO-IEC-9995-2-2002.pdf
13. QWERTY | Ultimate Pop Culture Wiki - Fandom, consulté le juin 7, 2026,
https://ultimatepopculture.fandom.com/wiki/QWERTY
14. German keyboard layout - Wikipedia, consulté le juin 7, 2026,
https://en.wikipedia.org/wiki/German_keyboard_layout
15. ISO/IEC 9995-1 - iTeh Standards, consulté le juin 7, 2026,
https://cdn.standards.iteh.ai/samples/42981/72afb66c5e7d4ad7ae7fbdebf9a4d04
c/ISO-IEC-9995-1-2006.pdf
16. Standardization of Keyboard Layouts - The ANSI Blog, consulté le juin 7, 2026,
https://blog.ansi.org/ansi/standardization-of-keyboard-layouts/
17. INCITS 154-1988[S2009] - Office Machines and Supplies û Alphanumeric
Machines û Keyboard Arrangement (formerly ANSI X3.154-1988 (R1999)) - ANSI
Webstore, consulté le juin 7, 2026,
https://webstore.ansi.org/standards/incits/incits1541988s2009
18. ANSI INCITS 154-1988 (R1999) - Office Machines and Supplies - ANSI Webstore,
consulté le juin 7, 2026,
https://webstore.ansi.org/standards/incits/ansiincits1541988r1999
19. German keyboard layout - Grokipedia, consulté le juin 7, 2026,
https://grokipedia.com/page/German_keyboard_layout
20. Difference Between ANSI and ISO Keyboard Layouts - Virtual Curiosities, consulté
le juin 7, 2026,
https://www.virtualcuriosities.com/articles/3220/difference-between-ansi-and-iso
-keyboard-layouts
21. German extended keyboard layout - Wikipedia, consulté le juin 7, 2026,
https://en.wikipedia.org/wiki/German_extended_keyboard_layout
22. DIN 2137:2011 - Deskthority, consulté le juin 7, 2026,
https://deskthority.net/viewtopic.php?t=1864
23. We need new keyboards - Page 2 - TypeDrawers, consulté le juin 7, 2026,
https://typedrawers.com/discussion/5080/we-need-new-keyboards/p2
24. DIN 2137-1:2023 - Keyboards for data and text input - Part 1 - ANSI Webstore,

consulté le juin 7, 2026, https://webstore.ansi.org/standards/din/din21372023
25. How many of us use nonstandard keyboard layouts? - #7 by Moonbase59 - Linux
lounge, consulté le juin 7, 2026,
https://forum.endeavouros.com/t/how-many-of-us-use-nonstandard-keyboard-l
ayouts/71468/7
26. French keyboard: a voluntary standard to make it easier to type all characters -
Afnor, consulté le juin 7, 2026,
https://www.afnor.org/en/news/electrotechnologies/french-keyboard-voluntary-s
tandard/
27. BÉPO - Wikipedia, consulté le juin 7, 2026,
https://en.wikipedia.org/wiki/B%C3%89PO
28. France's new AZERTY keyboard layout - Globalization - Microsoft Learn, consulté
le juin 7, 2026,
https://learn.microsoft.com/en-us/globalization/keyboards/azerty_english
29. The new AZERTY, consulté le juin 7, 2026, https://norme-azerty.fr/en/
30. New AZERTY French Keyboard Layout (2019), consulté le juin 7, 2026,
http://xahlee.info/kbd/french_new_keyboard_layout.html
31. Buy JIS X 6002:1980 | Intertek Inform, consulté le juin 7, 2026,
https://www.intertekinform.com/en-us/standards/jis-x-6002-1980-632821_saig_js
a_jsa_1451402/
32. Survey of Language Computing in Asia, consulté le juin 7, 2026,
http://www.cle.org.pk/research/rep/Survey.pdf
33. What Is the Japanese Keyboard Layout? JIS vs English QWERTY, consulté le juin 7,
2026,
https://electronics.alibaba.com/question/japanese-keyboard-layout-explained-jis-
vs-us-qwerty
34. What Is a Japanese Keyboard? Layout, Setup & Typing Explained, consulté le juin
7, 2026,
https://electronics.alibaba.com/question/japanese-keyboard-guide-layout,-setup
-real-world-use
35. Thumb-shift keyboard - Grokipedia, consulté le juin 7, 2026,
https://grokipedia.com/page/thumb_shift_keyboard
36. Japanese Key Layouts | Esrille NISSE, consulté le juin 7, 2026,
https://www.esrille.com/keyboard/layouts.ja-jp.html
37. Japan Layout Alliance - JLA｜Organize bottom row of Japanese array -
Greenkeys, consulté le juin 7, 2026,
https://green-keys.info/en/japan-layout-alliance/
38. Category:Japanese keyboard layouts - Wikimedia Commons, consulté le juin 7,
2026, https://commons.wikimedia.org/wiki/Category:Japanese_keyboard_layouts
39. JCUKEN - Wikipedia, consulté le juin 7, 2026, https://en.wikipedia.org/wiki/JCUKEN
40. What does a Russian keyboard look like? How can one type in Cyrillic letters with
it? - Quora, consulté le juin 7, 2026,
https://www.quora.com/What-does-a-Russian-keyboard-look-like-How-can-one
-type-in-Cyrillic-letters-with-it
41. What keyboard layout do you use/recommend? : r/russian - Reddit, consulté le

juin 7, 2026,
https://www.reddit.com/r/russian/comments/6j5js3/what_keyboard_layout_do_yo
u_userecommend/
42. GOST 16876-71 - Wikipedia, consulté le juin 7, 2026,
https://en.wikipedia.org/wiki/GOST_16876-71
43. Translit RU: Russian Transliteration and Virtual Keyboard, consulté le juin 7, 2026,
https://translit.cc/
44. List of QWERTY keyboard language variants - Wikipedia, consulté le juin 7, 2026,
https://en.wikipedia.org/wiki/List_of_QWERTY_keyboard_language_variants
45. ABNT NBR 10346 - 1991-08-30 - DIN Media, consulté le juin 7, 2026,
https://www.dinmedia.de/en/standard/abnt-nbr-10346/180540023
46. A Visual Comparison of Different National Layouts on a Computer Keyboard. -
Miguel Farah, consulté le juin 7, 2026,
https://www.farah.cl/Keyboardery/A-Visual-Comparison-of-Different-National-La
youts/
47. What Is the Nordic Keyboard Layout? Everything You Need to Know -
Monsgeek.eu, consulté le juin 7, 2026,
https://monsgeek.eu/blogs/guide/what-is-the-nordic-keyboard-layout-everythin
g-you-need-to-know
48. Understanding Different Physical Layouts For Keyboards: ANSI Vs ISO Vs JIS -
MechKeys, consulté le juin 7, 2026,
https://mechkeys.com/blogs/guide/understanding-different-physical-layouts-for-
keyboards-ansi-vs-iso-vs-jis
49. Keyboard layout - Wikipedia, the free encyclopedia, consulté le juin 7, 2026,
http://taggedwiki.zubiaga.org/new_content/b996676d2852e3818a60c2655ac10e7
3
50. Miscellaneous Technical - Wikipedia, consulté le juin 7, 2026,
https://en.wikipedia.org/wiki/Miscellaneous_Technical
51. Miscellaneous Symbols and Arrows - Wikipedia, consulté le juin 7, 2026,
https://en.wikipedia.org/wiki/Miscellaneous_Symbols_and_Arrows
52. Alt key - Wikipedia, consulté le juin 7, 2026, https://en.wikipedia.org/wiki/Alt_key
53. Control key - Wikipedia, consulté le juin 7, 2026,
https://en.wikipedia.org/wiki/Control_key
54. Compose key - Wikipedia, consulté le juin 7, 2026,
https://en.wikipedia.org/wiki/Compose_key
55. Proposal to incorporate the symbols of ISO/IEC 9995-7:2009 and its Amendment
1 and of ISO - Unicode, consulté le juin 7, 2026,
https://www.unicode.org/L2/L2017/17072-symbols-9995.pdf
56. 1. Introduction 1.1 Introduction of the symbols from ISO/IEC 9995-7:2009 and its
Amendment 1 (2012) 1.2 Introduction of the symb - Unicode, consulté le juin 7,
2026, https://unicode.org/wg2/docs/n4984-Unicode-Proposal-9995-V7.pdf
57. xkeyboard-config-2.47-160099.1.1 RPM for noarch - Rpmfind.net, consulté le juin
7, 2026,
https://rpmfind.net/linux/RPM/opensuse/16.1/noarch/xkeyboard-config-2.47-1600
99.1.1.noarch.html

58. How do FOUR_LEVEL_SEMIALPHABETIC xkb keys work? - Unix & Linux Stack
Exchange, consulté le juin 7, 2026,
https://unix.stackexchange.com/questions/398283/how-do-four-level-semialphab
etic-xkb-keys-work
59. XKB groups vs levels - Unix & Linux Stack Exchange, consulté le juin 7, 2026,
https://unix.stackexchange.com/questions/557014/xkb-groups-vs-levels
60. The XKB keymap text format, V1 and V2 - xkbcommon, consulté le juin 7, 2026,
https://xkbcommon.org/doc/current/keymap-text-format-v1-v2.html
61. CLDR/LDML Keyboards - Keyman, consulté le juin 7, 2026,
https://keyman.com/ldml/
62. hickford/xkb_ldml: LDML keyboard mappings for XKB layouts - GitHub, consulté
le juin 7, 2026, https://github.com/hickford/xkb_ldml
63. CLDR Keyboard Working Group - Unicode CLDR Project, consulté le juin 7, 2026,
https://cldr.unicode.org/index/keyboard-workgroup
64. Unicode Locale Data Markup Language (LDML) Part 7: Keyboards, consulté le juin
7, 2026, https://unicode.org/reports/tr35/tr35-keyboards.html
65. CLDR 45 Release Note - Unicode CLDR Project, consulté le juin 7, 2026,
https://cldr.unicode.org/downloads/cldr-45
66. CLDR 44 Release Note - Unicode CLDR Project, consulté le juin 7, 2026,
https://cldr.unicode.org/downloads/cldr-44
67. Keyboard Intake Procedures in CLDR - Unicode CLDR Project, consulté le juin 7,
2026, https://cldr.unicode.org/index/process/keyboard-repository-process
68. Unicode Locale Data Markup Language (LDML) Part 7: Keyboards, consulté le juin
7, 2026, https://www.unicode.org/reports/tr35/tr35-70/tr35-keyboards.html