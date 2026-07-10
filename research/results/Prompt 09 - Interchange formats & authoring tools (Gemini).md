System Interchange and Authoring
Formats for Keyboard Layouts: A
Comparative Analysis
The architecture of digital text input has historically suffered from profound fragmentation. For
decades, the process of mapping physical hardware events to digital text was governed by
proprietary, operating system-specific paradigms. Microsoft Windows relied on the brittle
Keyboard Layout Creator (KLC) format, macOS utilized XML-based keylayout definitions
coupled with proprietary finite state machines, and Linux systems depended on the historically
dense C-style configuration files of the X Keyboard Extension (XKB). As the computational
ecosystem expanded to encompass mobile touch surfaces, embedded hardware, and
cross-platform applications, this fragmentation became a critical bottleneck. The
contemporary landscape requires a precise delineation between two fundamentally different
engineering requirements: interchange formats, which serve as highly explicit,
machine-readable specifications that any operating system or text engine can consume
natively, and authoring formats, which act as ergonomic, human-readable source formats
utilized by linguists and software engineers to design these layouts.
This comprehensive report conducts an exhaustive survey of the platform-independent
interchange formats and existing layout-authoring source tools. It evaluates their expressive
capabilities, explores the rigorous mechanisms required to support complex-script text input,
and executes a candid, evidence-based gap analysis. The ultimate objective is to determine
whether the creation of a new open, JSON-based, human-maintainable source format is
technically justified, juxtaposed against the severe risk of generating redundant engineering
overhead that merely duplicates existing international standards.
1. The Unicode CLDR and LDML Keyboard 3.0 Standard
The Unicode Common Locale Data Repository (CLDR) Locale Data Markup Language (LDML)
represents the prevailing global standard for the exchange of structured locale data.1
Historically, the keyboard specification within LDML (Part 7 of UTS #35) was a descriptive
format.1 Designed in 2012, its primary utility was comparative—allowing linguists to catalog how
different keyboards functioned, but proving wholly insufficient for the actual implementation of
complex keyboard layouts across diverse software platforms.3 Recognizing this critical
limitation, the CLDR Keyboard Working Group initiated a systemic redesign. This effort
culminated in the "Keyboard 3.0" specification, which saw its first major integration in CLDR
release 45.3
1.1 The Architectural Shift: Descriptive to Prescriptive
The transition from the legacy LDML keyboard format to LDML Keyboard 3.0 marks a paradigm
shift from a descriptive catalog to a highly prescriptive, platform-independent interchange
format.5 The core philosophy of Keyboard 3.0 is that layout authors should be able to write a

single XML mapping file for their target language, which disparate software implementations
can consume to instantiate that layout natively.5
This shift is indicated at the very root of the document. Modern files utilize the <keyboard3>
root element rather than the legacy <keyboard> element, ensuring backward compatibility is
maintained for parsers that expect the older schema.5 Furthermore, the metadata
enforcement is strict; a Keyboard 3.0 file must define a conformsTo attribute.5 While earlier
iterations used numerical versioning (e.g., conformsTo="45"), active development phases utilize
the techpreview designation.6 The files are decoupled from the main CLDR source tree to
emphasize their utility as standalone artifacts intended for external consumption.6
1.2 Structural Hierarchy and Logical Abstraction
The LDML 3.0 schema achieves platform independence by establishing a rigorous hierarchy of
abstractions that decouple physical hardware constraints from logical text generation.
The foundation of this abstraction begins with the <scanCodes>, <keys>, and <key> elements.
Instead of relying on proprietary OS keycodes, LDML maps standardized physical key positions
(e.g., the hardware key adjacent to the left shift key on an ISO board) to logical identifiers.6
Because physical hardware varies geometrically, LDML 3.0 introduces <forms> and <form>
elements. These elements handle permutations like ISO, ANSI, and JIS physical keyboard
geometries. The standard achieves a baseline configuration by utilizing implied default imports,
such as the scanCodes-implied.xml document, which implementations must treat as virtually
present.5
Upon this base layer, the format superimposes modifier states utilizing <layers> and <layer>
elements. These define shift states, AltGr states, and custom layer modifiers, mapping logical
keystrokes to specific Unicode outputs depending on the currently active modifier
combination.6
To address the reality of modern computing, LDML 3.0 extends its architecture to encompass
touch-based interfaces natively. This is achieved through the <flicks>, <flick>, and
<flickSegment> elements. A flick defines a swipe gesture emanating from a base virtual key,
allowing a mobile keyboard implementation to map directional touch movements (e.g., swiping
upward on a key) to alternate character outputs.5 Visual representation on these keys is strictly
governed by the <displays>, <display>, and <displayOptions> elements. These directives
instruct the rendering engine on how to visually present a keycap.6 For instance, it provides
mechanisms to render a combining mark over a dotted circle base (U+25CC) so that
unattached diacritics do not render improperly, or it maps a non-printing control key to a
standardized symbolic representation.5
1.3 State Machines and Complex Script Modeling
The true technical achievement of LDML Keyboard 3.0 lies in its ability to abstract the complex
state machines required for international text input without requiring the host OS to execute
arbitrary code. This logic is isolated within the <transforms> element, which encapsulates
<transformGroup> and <transform> sub-elements.5

LDML 3.0 handles complex contextual logic by inspecting the text buffer. The <transform>
element utilizes from and before attributes to define match parameters.5 The from attribute
identifies the string generated by the current keystroke, while the before attribute allows the
keyboard driver to inspect the string immediately preceding the cursor in the host application's
text buffer.5 If both conditions are met, the keystroke is transformed.
This system elegantly models the reordering requirements of Indic and Brahmic scripts. In many
of these scripts, a user may type a consonant followed by a vowel, but typographic rules
require the vowel to be rendered before the consonant. Instead of forcing the keyboard driver
to implement a custom shaping engine, LDML provides an order integer attribute within the
<transform> element.5 By assigning numerical order values (ranging from -128 to +127), the
standard deterministically handles positional normalization directly at the input level.5
Furthermore, the standard natively supports UnicodeSet notation. Through the use of
<variables>, including set and uset variables, layout authors can define broad classes of
characters utilizing standard \u{...} escaping.5 This allows a single transform rule to apply to an
entire class of characters (e.g., all lowercase vowels) without requiring exhaustive duplication.5
Finally, the standard explicitly addresses state unwinding via the type="backspace" transform.
When a user deletes a character that was formed by a complex multi-stage transformation or
chained dead keys, the backspace transform dictates exactly how the text buffer should revert
to its previous state.5
1.4 Scope Limitations and Explicit Non-Goals
Because LDML Keyboard 3.0 is fundamentally an interchange format optimized for text
generation across diverse software platforms, it maintains strict boundaries regarding its
scope. It possesses several explicit non-goals that are crucial to understand when evaluating
the need for higher-level authoring tools.
Firstly, LDML refuses to model low-level hardware or control surfaces. It maps to standard
scancodes or virtual touch grids, but it contains zero knowledge of firmware matrices, physical
wiring logic, macro pads, or raw Human Interface Device (HID) descriptor generation. It is
entirely detached from the domains governed by hardware firmware like QMK, TMK, or ZMK.5
Secondly, LDML is incapable of expressing dynamic legends or context-aware adaptive
interfaces. While the <displays> element maps an output to a visual keycap, this mapping is
static within any given modifier layer.5 LDML cannot encode logic such as "alter this keycap's
visual icon if the host operating system launches a video editing application," nor can it display
dynamically generated predictive symbols pushed by an Artificial Intelligence interface.
Thirdly, the standard contains zero metadata pertaining to pedagogy or typing instruction. It
cannot express which human finger is optimally assigned to a specific key, nor does it provide
structural data that a typing tutor software could parse to generate progressive learning
curricula. Similarly, it lacks AI and assistant metadata; LDML maps a keypress to a Unicode
string, but it does not encode the semantic intent of the key (e.g., differentiating between a
generic slash used for punctuation versus a slash explicitly intended as a mathematical division
operator).

1.5 The State of Tooling and Native Adoption
The LDML 3.0 format is rapidly asserting itself as the definitive backend target for keyboard
implementation. The SIL Keyman project, arguably the most prominent historical force in
cross-platform layout authoring, has systematically embraced the new standard. Keyman
versions 17.0 and 18.0 ship with comprehensive open-source implementations of the LDML
format, allowing their desktop engines and developer toolchains to natively compile, validate,
and execute LDML keyboards across Windows, macOS, and Linux.10
Beyond Keyman, integration is accelerating across open-source desktop environments.
Projects such as the GNOME Caribou virtual keyboard utilize ingestion scripts (convert_cldr.py)
to parse CLDR XML data directly, transpiling it into the specific XML formats required by the
Caribou layout engine.13 This momentum indicates that LDML 3.0 will soon be the universal
denominator for operating system text input, solidifying its status as an interchange artifact
rather than a human-facing authoring tool.
2. Survey of Existing Authoring Formats and Tools
The verbosity of XML, while ideal for machine parsing and validation via Document Type
Definitions (DTDs), is inherently hostile to human authors. Consequently, layout engineers,
linguists, and hobbyists invariably turn to higher-level domain-specific languages (DSLs) or
modern data serialization formats (YAML, TOML, JSON) to architect their layouts. A rich
ecosystem of authoring tools has evolved to abstract the complexities of generating native OS
layout files.
2.1 kalamine
Kalamine stands as a highly effective, cross-platform keyboard layout generator that utilizes
YAML or TOML syntax to define key mappings.14 Its defining characteristic is its prioritization of
human readability; layouts are frequently designed using ASCII-art representations of the
physical keyboard geometry directly embedded within the configuration files.14
The expressive capabilities of kalamine cover the core requirements of standard desktop
computing. It adeptly handles base character mappings, shift levels, AltGr (Option) layers,
ortholinear geometries, and standard dead keys, utilizing a custom abstraction known as the
1dk (One Dead Key) model to simplify cross-platform dead key deployment.15 From a single
TOML or YAML source file, kalamine compiles distributable drivers for XKB (Linux), MSKLC
(Windows), .keylayout (macOS), AutoHotkey (AHK), as well as JSON files for web components
and SVG files for visual documentation.15
The tooling ecosystem surrounding kalamine is robust, relying on standard Python package
management (pipx).15 It provides a dedicated command-line interface, xkalamine, which
streamlines the notoriously difficult process of installing XKB layouts on Linux, interacting
directly with Wayland and Xorg configurations in both user-space and root system
directories.15 Perhaps most impressively, kalamine circumvents severe architectural limitations
within Microsoft's Keyboard Layout Creator (MSKLC). MSKLC famously fails to compile layouts
containing chained dead keys or AltGr+Space combinations. Kalamine solves this via

wkalamine, a Windows-specific CLI that generates raw C code and tricks the MSKLC
compilation pipeline by injecting this C layout file as a read-only dependency prior to
execution, thereby bypassing Microsoft's graphical limitations entirely.15
2.2 kbdgen (Divvun)
Developed by the Divvun group at the Arctic University of Norway, kbdgen is an
enterprise-grade compiler designed specifically to support the linguistic infrastructure of
minority and indigenous languages, with a historical focus on Sámi languages.20 Written
primarily in Rust, with legacy components in Python, it serves as a massive pipeline rather than
a simple layout transpiler.20
The syntax of kbdgen relies on pure YAML configuration files. Layouts are not defined in a
single file but are spread across a highly structured directory tree managed by a central
project.yaml file, which dictates metadata, target architectures, and specific key matrices.21
While it can express standard desktop modifiers, its expressive capability is uniquely optimized
for mobile touch layouts.22 It is one of the only open-source authoring formats that natively
prioritizes the integration of keyboard definitions with advanced computational linguistics,
natively supporting finite state transducer spellers (ZHFST/BHFST) and constraint-grammar
syntax checkers directly within the keyboard compilation pipeline.20
The export targets for kbdgen are exhaustive. It compiles to Windows (via KLC source
generation), macOS, X11, Chrome OS, and crucially, Android and iOS.23 For mobile platforms,
kbdgen acts as a complete Continuous Integration and Continuous Deployment (CI/CD)
engine. It consumes the YAML definitions alongside localization data and icon assets, combines
them with a pre-built Swift or Java hosting application, compiles the entire project, signs the
binaries, and prepares them for direct upload to the Apple App Store or Google Play Store.22
2.3 KLFC (Keyboard Layout Files Creator)
KLFC occupies a specific niche aimed at advanced layout enthusiasts, ergonomic typists (such
as the Colemak community), and developers operating at the intersection of software OS
layouts and hardware firmware.26 It is written in Haskell and distributed via the Haskell Cabal
toolchain, with extensive support for reproducible builds via the Nix package manager.27
The input syntax for KLFC is pure JSON, governed by a rigorous internal schema documented
in the project's layout.md file.27 Its expressive capability is high, natively supporting advanced
modifier mappings, custom dead keys, and complex substitutions required by ergonomic
communities.9
The export targets distinguish KLFC from its peers. From a single JSON source, it generates
XKB directories, Windows KLC files, macOS keylayouts, AutoHotkey (AHK) scripts, and Portable
Keyboard Layout (PKL) configurations.9 PKL is significant as it allows users to carry a keyboard
layout on a USB drive and execute it on a restricted Windows machine without requiring
administrator installation privileges. Furthermore, KLFC bridges the software-hardware divide
by exporting directly to TMK firmware directories.9 This allows an author to define a layout once
and deploy it either as a software OS driver or burn it directly onto the microcontroller of a

custom mechanical keyboard. The tool does suffer from occasional limitations tied to its
reliance on legacy targets, such as issues parsing XKB hyphenated filenames, but remains a
vital tool for structural JSON authoring.29
2.4 SIL Keyman (.kmn and.kmx)
SIL Keyman is unequivocally the most mature, feature-rich, and linguistically capable authoring
system in existence for complex scripts.11 Originally developed to support languages that native
operating systems ignored, Keyman operates on a proprietary Domain Specific Language (DSL)
encoded in .kmn source files.30
The expressive capability of the Keyman DSL achieves near Turing-complete text
transformation. It abandons simple one-to-one key mapping in favor of a rule-based finite
state transducer model. The core mechanics rely on store, any, and index statements.30 A
layout author can define a store containing a massive array of characters (e.g., all lowercase
vowels). They can then write a rule stating that if an any condition matches a character from
that store, the output should be generated by pulling the corresponding character from a
different store using an index coordinate.31
Keyman natively supports infinite chained dead keys through the deadkey() or dk() statements,
which emit invisible placeholders into the text buffer that subsequent keystrokes can match
and consume.33 Contextual transforms are handled flawlessly via the context() offset, which
allows a rule to evaluate previously typed characters and dynamically alter the current output.31
To address visual touch layouts, Keyman utilizes .kvks (visual keyboard) and displayMap JSON
files. These map logical outputs to Private Use Area (PUA) Unicode values, ensuring that
unattached diacritics render consistently across all mobile environments without relying on the
host OS's unpredictable font shaping engines.7
Keyman source files are compiled into proprietary .kmx binary formats. These binaries are not
native OS drivers; rather, they are ingested by the Keyman Engine, which runs as an intercept
layer across Windows, macOS, Linux, iOS, Android, and Web applications.11 Recognizing the
momentum of standard formats, Keyman Developer 17.0 and 18.0 now natively cross-compile
to and from the LDML Keyboard 3.0 standard, explicitly linking the most powerful authoring
DSL with the most standard interchange format.10
2.5 Native OS Formats (MSKLC, XKB, keylayout)
Native OS formats exist primarily as compilation targets rather than human-centric source
formats. Attempting to author directly in these formats is highly discouraged in modern
development due to severe structural limitations and maintenance overhead.
Microsoft Keyboard Layout Creator (MSKLC) produces .klc files. While the graphical tool is
accessible, the underlying .klc format is notoriously brittle. It fails catastrophically when
attempting to compile layouts containing chained dead keys, and it lacks the ability to map
characters outside the Basic Multilingual Plane (BMP) efficiently.15 Third-party shareware tools
like KbdEdit exist to bypass the graphical limitations of MSKLC, but they still ultimately interface
with the rigid Windows driver model.

macOS relies on .keylayout files, which utilize an explicitly defined XML state machine. While
capable of handling standard dead key states via nested action elements, the format becomes
astronomically verbose and nearly unmaintainable when attempting to model the complex
contextual reordering required by Indic scripts.18
Linux relies on the X Keyboard Extension (XKB). XKB is a marvel of legacy engineering, utilizing a
highly complex, inheritance-based C-style syntax dispersed across multiple system directories
(typically /usr/share/X11/xkb/symbols, rules, and compat).15 Because a single layout requires
modifying multiple files requiring root access, user-space installation is highly error-prone
without wrapper tools like xkalamine to manage the symlinks and registry entries.15
2.6 Event Interceptors vs. Layout Engines: Karabiner-Elements
Karabiner-Elements is frequently discussed alongside keyboard layout tools, but it represents
an entirely different class of software: it is a kernel-level event interceptor and remapper.38
Configured via a complex JSON schema, Karabiner operates directly on the HID event
stream.38 It intercepts physical hardware keycodes before they reach the macOS layout engine,
translates them based on logic conditions, and passes new keycodes to the OS.38 It evaluates
deep state conditions, such as the frontmost active application or concurrent modifier presses,
allowing users to execute macros, launch shell commands, or fundamentally alter modifier
topology (e.g., mapping Caps Lock to act as a Hyper key).38
However, Karabiner is strictly not a layout format. If a user sets their native macOS layout to
QWERTY, Karabiner merely maps physical key presses to virtual QWERTY keystrokes.39 It
cannot define new Unicode character outputs that the base OS layout does not already
possess. If a user wishes to output a rare phonetics symbol, Karabiner cannot generate it
unless a native .keylayout driver is installed that maps a keycode to that symbol.
2.7 Adjacent Context: AutoHotkey and Espanso
Tools like AutoHotkey (AHK) and Espanso operate even further up the software stack. They are
text expansion and macro execution environments. While they can simulate keyboard layouts
by intercepting keystrokes and pasting Unicode strings, they are fundamentally unsuited for
base layout definition. They suffer from latency, they frequently break in secure password fields
or terminal emulators that bypass the standard OS text clipboard, and they do not integrate
with the OS's native language and input method UI. They exist as productivity wrappers, not as
foundational system infrastructure.
3. Typographic Constraints and Complex-Script
Requirements
Any layout format that aspires to global utility must seamlessly handle the typographic
complexities of the world's writing systems. A format that only maps one key to one Latin
character is trivial; the true test of a format lies in its handling of the following mechanisms.
Dead-Key Chains: Western European languages generally require only simple dead keys (e.g.,
striking ^ followed by a to produce â). However, scripts like Polytonic Greek or languages like

Vietnamese frequently require extensive chaining. A user might strike a circumflex dead key,
followed by a tonal dead key, followed by a base vowel character. Legacy OS formats,
particularly MSKLC, fail completely at this depth.15 LDML handles this flawlessly via
<transforms>, maintaining internal buffer states and outputting the final composed Unicode
character only when the chain resolves.5 Keyman handles this through persistent context arrays
and consecutive dk() definitions that queue invisible tokens in the text buffer until a matching
rule fires.33
Contextual Transforms and Shaping: In scripts like Arabic or Syriac, characters change their
visual shape depending on their position within a word (isolated, initial, medial, final). While
OpenType shaping engines within the application usually handle this rendering automatically,
the keyboard must sometimes intervene to force specific behaviors. For example, a user may
need to output a Zero Width Non-Joiner (ZWNJ) to break a ligature. The keyboard layout must
be aware of the preceding context to determine if a ZWNJ is valid. LDML utilizes the before
attribute in the <transform> element to peer into the preceding string buffer.5 Keyman uses the
context() offset to evaluate previously typed characters, dynamically injecting control codes
based on adjacent letters.31
Reordering and Normalization: Indic and Brahmic scripts demand aggressive reordering. A
user typing Hindi will logically type a consonant, followed by a matra (a dependent vowel sign).
However, depending on the specific matra, typographic rules may dictate that the vowel must
be rendered visually before the consonant, or wrapped around it. To abstract this normalization
process away from the application layer, the keyboard driver must reorder the input string
before committing it to the OS. LDML handles this directly through the order attribute inside a
<reorder> element, intercepting the keystrokes, buffering them, and committing them in the
typographically correct sequence.5 Keyman utilizes advanced regex-style contextual rules to
consume the typed characters and output them in the inverted sequence. Formats like
kalamine or KLFC, which map directly to standard XKB or KLC layouts, entirely lack the ability to
express this logic natively, relying instead on the host OS's text engine to resolve the sequence
post-input.
4. Master Feature and Coverage Matrix
The following matrix compares the expressive capabilities and architectural scopes of the
surveyed formats, highlighting the profound divergence between interchange standards,
human authoring tools, and native OS targets.
Capabilit LDML kalamine kbdgen KLFC Keyman Native
y / Keyboar (YAML/T (YAML) (JSON) (.kmn) OS
Feature d 3.0 OML) Targets
(KLC,
XKB,
keylayou
t)

| Base  | Yes  | Yes  | Yes  | Yes  | Yes  | Yes  |
| ----- | ---- | ---- | ---- | ---- | ---- | ---- |
Mapping
& Shift
Levels
| AltGr /  | Yes  | Yes  | Yes  | Yes  | Yes  | Yes  |
| -------- | ---- | ---- | ---- | ---- | ---- | ---- |
Option
Levels
| Dead  | Yes  | Yes  | Yes  | Yes  | Yes  | Yes  |
| ----- | ---- | ---- | ---- | ---- | ---- | ---- |
Keys
| Chained  | Yes        | Limited    | Yes  | Yes  | Yes (dk())  | Varies       |
| -------- | ---------- | ---------- | ---- | ---- | ----------- | ------------ |
| Dead     | (<transfor | (via C     |      |      |             | (KLC fails,  |
| Keys     | ms>)       | injection  |      |      |             | XKB/Mac      |
|          |            | hack)      |      |      |             | pass)        |
| Multi-ch | Yes        | Yes        | Yes  | Yes  | Yes         | Varies       |
| aracter  |            |            |      |      |             | (XKB         |
| Output   |            |            |      |      |             | limited,     |
Mac
pass)
| Contextu | Yes        | No  | No  | No  | Yes (any,  | No        |
| -------- | ---------- | --- | --- | --- | ---------- | --------- |
| al       | (<transfor |     |     |     | context)   | (Delegate |
| Transfor | ms>)       |     |     |     |            | d to OS   |
| ms       |            |     |     |     |            | text      |
engines)
| Reorderi | Yes      | No  | No  | No  | Yes  | No  |
| -------- | -------- | --- | --- | --- | ---- | --- |
| ng       | (order,  |     |     |     |      |     |
| (Comple  | before)  |     |     |     |      |     |
x
Scripts)
| Markers  | Yes (uset,  | No  | No  | No  | Yes      | No  |
| -------- | ----------- | --- | --- | --- | -------- | --- |
| &        | zwnj)       |     |     |     | (store)  |     |
Variables

| Per-key   | Yes        | No          | No   | No   | Yes       | No   |
| --------- | ---------- | ----------- | ---- | ---- | --------- | ---- |
| Display   | (<displays | (Relies on  |      |      | (displayM |      |
| Legends   | >)         | OS UI)      |      |      | ap)       |      |
| Locale /  | Yes        | Yes         | Yes  | Yes  | Yes       | Yes  |
BCP-47
Target
| Mobile /  | Yes         | No  | Yes       | No  | Yes (via  | No  |
| --------- | ----------- | --- | --------- | --- | --------- | --- |
| Touch     | (<flicks>)  |     | (iOS/Andr |     | Keyman    |     |
| Output    |             |     | oid UI)   |     | Engine)   |     |
| Dynamic   | No          | No  | No        | No  | No        | No  |
Legend
Metadat
a
| Accessib | Limited  | No  | No  | No  | No  | No  |
| -------- | -------- | --- | --- | --- | --- | --- |
ility
Metadat
a
| OS       | N/A        | Windows,  | Windows,  | Windows,  | Keyman    | Native   |
| -------- | ---------- | --------- | --------- | --------- | --------- | -------- |
| Export   | (Consum    | macOS,    | macOS,    | macOS,    | Engine    | (Target  |
| Targets  | ed by OS)  | Linux     | Linux,    | Linux,    | (All      | Only)    |
|          |            |           | iOS,      | TMK, PKL  | platforms |          |
|          |            |           | Android   |           | )         |          |
| Hardwar  | No         | No        | No        | Yes (TMK  | No        | No       |
| e /      |            |           |           | Firmware  |           |          |
| Firmwar  |            |           |           | )         |           |          |
e Export
| Human-    | Moderate  | Excellent  | Excellent  | Good     | Moderate  | Poor       |
| --------- | --------- | ---------- | ---------- | -------- | --------- | ---------- |
| Readabl   | (Verbose  | (YAML +    | (YAML      | (JSON    | (Propriet | (C-struct  |
| e Source  | XML)      | ASCII      | trees)     | arrays)  | ary DSL)  | s / XML    |
|           |           | grid)      |            |          |           | binaries)  |
| Schema    | Yes (DTD  | Yes        | Yes        | Yes      | Yes (Via  | Partial    |
| Validatio | Specifica |            |            |          | Compiler  |            |

n tion) )
5. Comprehensive Gap Analysis
The objective of this analysis is to rigorously evaluate where new engineering efforts should be
deployed, avoiding the catastrophic reinvention of mature standards. This analysis proceeds in
two discrete steps.
Step 1: Independent Evidence-Based Findings
Evaluating the matrix and the qualitative data reveals a deeply saturated market regarding text
generation. The fundamental abstraction of mapping a physical keystroke to a Unicode
sequence is a solved problem. Furthermore, the implementation of complex text
transformations—contextual lookbacks, chained dead keys, buffer unwinding, and Indic string
reordering—represents an exceptionally difficult computer science domain. This domain has
been exhaustively conquered by Keyman's DSL and has now been codified into an international
interchange standard via LDML Keyboard 3.0.
If a team attempts to create a new JSON format that defines its own proprietary syntax for
"reordering an Indic matra depending on the preceding consonant," it will immediately trigger a
massive redundancy trap. It will merely duplicate the exact semantic logic of LDML's
<transformGroup> and <reorder> elements, swapping XML tags for JSON brackets, while
failing to achieve the universal parsing support that the Unicode Consortium provides.
Furthermore, building compilers that translate simple JSON mappings into native OS binaries
(like XKB or KLC) duplicates the precise, grueling engineering work already completed,
maintained, and open-sourced by tools like KLFC, kalamine, and kbdgen.
However, moving beyond text generation reveals genuine, critical gaps in the ecosystem. The
existing landscape focuses strictly on the text generation state machine and target platform
deployment. The following domains are functionally absent from all major formats, including
LDML, Keyman, and KLFC:
1. Semantic and Pedagogical Context: There exists no standard format to declare the
purpose of a layout to a human learning it. Metrics such as finger assignment mappings,
ergonomic heatmaps, and learning progressions are not expressible in LDML or XKB. A
typing tutor cannot parse an LDML file to understand that the 'F' key is anchored to the
left index finger.
2. Dynamic Interface Definitions: While LDML supports static touch flicks and display
legends, it cannot describe an interface that adapts based on external application states.
As computing moves toward adaptive control surfaces (e.g., OLED StreamDecks,
dynamic touch-bars, split ergonomic displays), the layout format must be capable of
expressing logic such as "change the keycap visual from a spreadsheet macro to a video
editing scrub wheel when the active application changes."
3. Hardware Genericity: The chasm between software text layout (LDML) and hardware
matrix definitions (QMK/TMK/ZMK) remains vast. While KLFC attempts to bridge this by

generating TMK headers 9, its data model remains rigid. An authoring format should be
capable of defining the logical layout once, and fanning it out to both the OS driver and
the firmware configuration of the physical microcontroller.
4. A Unified Source of Truth: Layout authors are currently forced into a compromise. They
must choose between human-friendly YAML that lacks complex script support
(kalamine), or complex script support encapsulated in a verbose DSL/XML
(Keyman/LDML) that completely lacks hardware firmware export capabilities.
Step 2: Evaluation of the Project's Hypothesis
The core hypothesis under evaluation posits that an open, JSON-based format could serve as a
human-maintainable source to address under-served areas—specifically dynamic legends,
learning/pedagogy metadata, AI-assistant typing knowledge, and device/control-surface
exports—while interoperating with LDML by using a fan-out compilation approach.
Conclusion: The evidence heavily supports this hypothesis, but only under the strict
condition of architectural delegation.
The hypothesis correctly identifies that current standards (including LDML 3.0) treat keyboards
purely as "dumb" translation layers standing between a hardware scancode and a Unicode
character. By elevating the layout definition to include rich metadata—AI semantic intent,
pedagogical data, hardware topology—a new JSON format provides immense, unrealized
value. JSON is universally parsed, easily validated by JSON Schema, natively compatible with
web-based visual layout editors, and easily version-controlled.
However, the explicit caveat—and the highest risk of systemic failure—lies in how the new
format handles text transformations. The new JSON format must not attempt to write or define
its own text-shaping engine. It must act strictly as a metadata envelope. The hypothesis that a
single human-maintainable source should fan out to all targets is valid, provided that whenever
complex text logic is required, the JSON format compiles down to LDML, delegating the text
state machine entirely to the Unicode standard.
6. Strategic Recommendations
To justify its existence, avoid redundancy, and provide unique utility to layout engineers, the
proposed JSON-based format must adhere to a strict architectural division of labor. It must
operate as an Authoring Envelope, separating text generation from semantic metadata.
1. What Must Be Delegated to LDML 3.0:
● The Text State Machine: Any logic involving contextual string replacement, dead key
buffering, backspace un-rolling, and Indic matra reordering must be mapped directly to
LDML <transforms> arrays.5 The JSON should merely provide an array structure that
passes this logic directly to the LDML compiler.
● Unicode Escaping and Character Classes: The JSON format should rely on LDML's
integration with UTS #35 UnicodeSets (\u{...}, uset) for broad character matching, rather
than inventing its own regex syntax.5
● Standard Touch Flicks: Basic swipe-to-type metrics on virtual mobile keyboards should
map directly to LDML <flicks> objects.5
2. What the JSON Format Must Add as a Higher-Level Layer:

● Hardware and Matrix Abstractions: The JSON schema must include definitions for
physical hardware mapping. This allows the compiler to generate not just OS layouts, but
QMK, ZMK, and TMK firmware header files, creating a unified source of truth for custom
mechanical keyboard builders.9
● Dynamic and Adaptive Legends: Define schema objects for dynamic states (e.g.,
"onStateChange": {"display": "glyph"}). While this data will be stripped out when compiling
to LDML (which cannot parse it), it can be preserved when compiling to modern web
frameworks, touch-bar APIs, or hardware tools like split OLED keyboards.
● Pedagogical Metadata: Introduce standardized JSON arrays for "fingerAssignment",
"homeRowAnchor", and "curriculumLevel" assigned to specific keys or layers. This enables
typing tutors and educational software to consume the exact same JSON file used to
build the OS driver, ensuring perfect synchronization between the learning software and
the active system layout.
● Semantic and AI Bindings: Introduce a "semanticIntent" tag for keys. A key could be
tagged as "intent": "math_operator" or "intent": "ai_prompt_trigger". When compiled for a
native OS, this metadata is discarded. However, when consumed by a smart IDE or a
system-level AI assistant, it provides deep contextual awareness regarding the user's
hardware input stream.
● Authoring Ergonomics: The JSON syntax should support matrix-style visual
representations (similar to kalamine's ASCII-art YAML arrays) to ensure maximum human
maintainability, allowing developers to visually map the physical keyboard directly within
the code editor.14
In summary, the new JSON format should not attempt to usurp LDML as an interchange format,
nor should it attempt to rewrite Keyman's complex script parser. Instead, it must position itself
as the ultimate semantic authoring layer. By wrapping text-transformation syntax (which
compiles cleanly down to standard LDML) alongside rich pedagogical, hardware, and dynamic
metadata, it will fill a massive void in the current ecosystem, dramatically advancing the state of
keyboard layout engineering without duplicating the exhaustive work already completed by the
global linguistic community.
Sources des citations
1. cldr/docs/ldml/tr35-general.md at main · unicode-org/cldr · GitHub, consulté le
juin 7, 2026,
https://github.com/unicode-org/cldr/blob/main/docs/ldml/tr35-general.md
2. Unicode Locale Data Markup Language (LDML), consulté le juin 7, 2026,
https://www.unicode.org/reports/tr35/
3. CLDR Keyboard Working Group - Unicode CLDR Project, consulté le juin 7, 2026,
https://cldr.unicode.org/index/keyboard-workgroup
4. CLDR 45 Release Note - Unicode CLDR Project, consulté le juin 7, 2026,
https://cldr.unicode.org/downloads/cldr-45
5. Unicode Locale Data Markup Language (LDML) Part 7: Keyboards, consulté le juin
7, 2026, https://unicode.org/reports/tr35/tr35-keyboards.html

6. Unicode Locale Data Markup Language (LDML) Part 7: Keyboards, consulté le juin
7, 2026, https://www.unicode.org/reports/tr35/tr35-70/tr35-keyboards.html
7. &displayMap store - Keyman Support, consulté le juin 7, 2026,
https://help.keyman.com/developer/language/reference/displaymap
8. Unicode Locale Data Markup Language (LDML) Part 7: Keyboards, consulté le juin
7, 2026, https://www.unicode.org/review/pri476/spec/tr35-keyboards.pdf
9. nick-gravgaard/qwerty-flip - GitHub, consulté le juin 7, 2026,
https://github.com/nick-gravgaard/qwerty-flip
10. CLDR/LDML Keyboards - Keyman, consulté le juin 7, 2026,
https://keyman.com/ldml/
11. Keyman Developer | Build custom keyboard layouts for desktop, web, phone and
tablets, consulté le juin 7, 2026, https://keyman.com/developer/
12. LDML Keyboard Editor Window - Keyman Support, consulté le juin 7, 2026,
https://help.keyman.com/developer/current-version/context/ldml-editor
13. Projects/Caribou/NewLayout – GNOME Wiki Archive, consulté le juin 7, 2026,
https://wiki.gnome.org/Projects/Caribou/NewLayout
14. kalamine - PyPI, consulté le juin 7, 2026, https://pypi.org/project/kalamine/0.9.2/
15. OneDeadKey/kalamine: Keyboard Layout Maker - GitHub, consulté le juin 7, 2026,
https://github.com/OneDeadKey/kalamine
16. GitHub - Nuclear-Squid/ergol: A Colemak-style keyboard layout for
French-speaking typists and programmers., consulté le juin 7, 2026,
https://github.com/Nuclear-Squid/ergol
17. OneDeadKey - GitHub, consulté le juin 7, 2026, https://github.com/OneDeadKey
18. GitHub - OneDeadKey/1dk: A sane way to use Qwerty-US keyboards with
non-English languages., consulté le juin 7, 2026,
https://github.com/OneDeadKey/1dk
19. kalamine - PyPI, consulté le juin 7, 2026, https://pypi.org/project/kalamine/0.13/
20. Divvun - GitHub, consulté le juin 7, 2026, https://github.com/divvun
21. Getting Started With Keyboard Development - GiellaLT documentation, consulté
le juin 7, 2026,
https://giellalt.uit.no/keyboards/GettingStartedWithKeyboardDevelopment.html
22. GiellaLT: an infrastructure for rule-based language technology tool development
- UP Journals, consulté le juin 7, 2026,
https://upjournals.up.ac.za/index.php/dhasa/article/download/4451/3863
23. consulté le juin 7, 2026,
https://raw.githubusercontent.com/RichardLitt/endangered-languages/master/RE
ADME.md
24. Unmasking the Myth of Effortless Big Data - Making an Open Source Multi-lingual
Infrastructure and Building Language Resources f - ACL Anthology, consulté le
juin 7, 2026, https://aclanthology.org/2022.lrec-1.125.pdf
25. divvun/giellakbd-ios: Open source reimplementation of iOS keyboard with
localisation support - GitHub, consulté le juin 7, 2026,
https://github.com/divvun/giellakbd-ios
26. keylayout · GitHub Topics, consulté le juin 7, 2026,
https://github.com/topics/keylayout

27. 39aldo39/klfc: Keyboard Layout Files Creator - GitHub, consulté le juin 7, 2026,
https://github.com/39aldo39/klfc
28. Keyboard Layout Files Creator - User contributions - Colemak forum, consulté le
juin 7, 2026, https://forum.colemak.com/topic/2168-keyboard-layout-files-creator/
29. Issues · 39aldo39/klfc - GitHub, consulté le juin 7, 2026,
https://github.com/39aldo39/klfc/issues
30. Tavultesoft Keyboard Manager - Keyman Support, consulté le juin 7, 2026,
https://help.keyman.com/developer/4.0/keyman40.html
31. Tavultesoft Keyboard Manager Developer Documentation - Keyman Support,
consulté le juin 7, 2026,
https://help.keyman.com/products/windows/5.0/km50dev.pdf
32. Tavultesoft Keyboard Manager User's Guide and Reference - Keyman Support,
consulté le juin 7, 2026,
https://help.keyman.com/products/windows/3.0/keyman32.pdf
33. deadkey - Keyman Support, consulté le juin 7, 2026,
https://help.keyman.com/developer/language/reference/deadkey
34. deadkey statement - Keyman Support, consulté le juin 7, 2026,
https://help.keyman.com/developer/8.0/docs/reference_deadkey
35. Range expansions - Keyman Support, consulté le juin 7, 2026,
https://help.keyman.com/developer/language/guide/expansions
36. &visualkeyboard - Keyman Support, consulté le juin 7, 2026,
https://help.keyman.com/developer/language/reference/visualkeyboard
37. FEATURE REQUEST to keyboard-layout-editor.com: klc file support :
r/KeyboardLayouts, consulté le juin 7, 2026,
https://www.reddit.com/r/KeyboardLayouts/comments/14rlcuj/feature_request_to
_keyboardlayouteditorcom_klc/
38. Use more complex modifications - Karabiner-Elements - pqrs.org, consulté le juin
7, 2026,
https://karabiner-elements.pqrs.org/docs/manual/configuration/configure-comple
x-modifications/
39. Karabiner-Elements uses qwerty layout instead of colemak - Reddit, consulté le
juin 7, 2026,
https://www.reddit.com/r/Colemak/comments/105gn6f/karabinerelements_uses_
qwerty_layout_instead_of/