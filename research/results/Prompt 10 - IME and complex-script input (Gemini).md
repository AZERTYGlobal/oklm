Architectural Boundaries in
Complex-Script Text Input: Delineating
Layouts, Transforms, and State-Driven
Input Method Editors
Introduction to the Complex-Script Input Paradigm
The engineering of cross-platform text input systems has historically been constrained by the
paradigm of mechanical typewriters, wherein a single physical keystroke corresponds directly
and irrevocably to the emission of a single character. While this one-to-one mapping model
adequately serves basic Latin, Cyrillic, and Greek scripts, it fails categorically when applied to
the vast majority of the world's writing systems. Complex scripts—including the massive Han
ideographic inventories of East Asia, the algorithmically composed syllables of Korean Hangul,
the phonetically clustered and reordered conjuncts of Indic and Brahmic scripts, and the
syntactically validated arrays of Southeast Asian alphabets—require fundamentally different
processing pipelines.
To support these diverse writing systems, modern operating systems rely heavily on multi-stage
text transformation engines and fully fledged Input Method Editor (IME) architectures. For
systems engineers and researchers developing an open, interoperable, and cross-platform
keyboard layout model (such as those building upon the Unicode Locale Data Markup
Language), recognizing the precise technical boundaries between a static layout, a deterministic
transform/reorder layer, and a stateful IME is not merely a theoretical exercise; it is a strict
architectural necessity. An effective layout standard must encapsulate the rules it can process
deterministically while maintaining the architectural discipline to delegate fundamentally
ambiguous or dictionary-dependent operations to external text services. This report exhaustively
maps the mechanics of complex-script text input across all major platforms, details the specific
processing requirements of distinct script families, and establishes a rigid decision boundary
defining what a layout standard can inherently represent versus what must be delegated to
stateful input frameworks.
Conceptual Framework: The Evolution from Static
Layouts to Input Method Editors
To engineer a robust layout model, one must first deconstruct the functional disparities between
a low-level keyboard mapping and a high-level text service.
At its lowest conceptual level, a static keyboard layout is fundamentally a stateless translation
matrix. It intercepts physical hardware scan codes from a peripheral device and maps them to
virtual key codes. It subsequently maps those virtual key codes—often modified by stateless,
momentary modifier keys such as Shift, Control, or AltGr—into specific Unicode code points.1
Even when modern layouts support traditional "dead keys" (for example, pressing an acute

accent key which silently alters the output of the subsequent vowel keystroke), the internal state
machine is typically limited to a single depth layer. A static layout has no memory of the broader
context of the document, possesses no linguistic dictionary, performs no morphological analysis,
and emits characters instantly into the active application's focused text field.
Conversely, an Input Method Editor (IME) is a sophisticated software component that facilitates
the input of characters that cannot be easily represented on a standard physical keyboard.2 The
IME operates as a highly stateful, intermediate processing layer situated between the physical
input event and the target application's document memory.2 The IME pipeline diverges entirely
from a static layout by introducing a complex, asynchronous, multi-stage lifecycle consisting of
pre-editing, candidate selection, and final commitment.
The pipeline begins with the composition or pre-edit stage. Instead of committing characters
directly into the host application's permanent text buffer, the IME opens a temporary memory
buffer known as the composition string.3 The text within this buffer is continuously updated as
the user types and is typically rendered in the application with specific visual indicators, such as
underlines or background highlights, to inform the user that the text is in a state of flux and
remains subject to further modification.3 During this phase, the application halts normal
operations like spell-checking on the specific string, recognizing that the input is incomplete.3
Following the pre-edit stage, the pipeline enters the conversion and candidate selection phase.
Based on the phonetic, phonetic-alphabetic, or structural keystrokes accumulated in the pre-edit
buffer, the IME engine consults extensive linguistic dictionaries, heuristic algorithms, or
machine-learning language models to determine the intended character sequence.2 Because
many complex scripts suffer from a high degree of homophony (where multiple distinct words
share the exact same phonetic pronunciation), the IME must often display a "candidate window."
This user interface element presents a list of alternative characters or phrases, allowing the user
to disambiguate the input and select the correct output.2
Once the user finalizes their selection—either by pressing a specific commit key like Enter, or by
continuing to type a new discrete word—the IME pipeline terminates the composition state. It
executes a commit operation, which clears the temporary pre-edit buffer and permanently
inserts the finalized Unicode text sequence into the host application's document, advancing the
caret position accordingly.3 This pipeline demonstrates that an IME is fundamentally
out-of-scope for a simple layout mapping standard. It requires the instantiation of UI
components, dynamic memory allocation for temporary strings, asynchronous communication
with the operating system, and the hosting of massive external data structures.
Platform-Specific Input Architectures and Application
Integration
The implementation of the composition-to-commit pipeline varies significantly across different
operating systems. An open layout model must interoperate cleanly with these underlying
frameworks, requiring engineers to understand how each platform manages the boundary
between hardware events, software layouts, and text services.
Windows: From IMM32 to the Text Services Framework (TSF)

Historically, the Windows operating system managed complex text input through the Input
Method Manager (IMM32) API. IMM32 was heavily reliant on the classic Windows
message-passing architecture. Applications were required to handle specific window messages,
primarily WM_IME_COMPOSITION and WM_IME_CHAR, to render the composition state and
coordinate the display of candidate windows.7 While functional, IMM32 was tightly coupled to
physical keyboard devices and lacked the flexibility required for modern, multi-modal input.
In modern Windows environments, text input is governed by the Text Services Framework
(TSF). TSF is a robust, Component Object Model (COM)-based architecture that radically
abstracts text input, completely decoupling it from specific hardware devices to support
keyboards, handwriting recognition, and speech-to-text engines uniformly.10 TSF operates on
the principle of indirect interaction; a text service (such as an IME) never interacts directly with
an application's window or memory space.10 Instead, the architecture utilizes three primary
intermediary components.
First, the TSF Manager, exposed via the ITfThreadMgr interface, acts as the central mediator
and dispatcher within a given thread, coordinating all operations between text services and
client applications.10 Second, the architecture relies on Document Managers and Contexts. The
host application creates an ITfDocumentMgr instance for each active document, and pushes
ITfContext objects onto a stack to represent specific, focused text fields.10 Finally, applications
expose their internal text buffers via the ITextStoreACP (Application Character Position)
interface.10 This interface provides the text service with direct, synchronized access to the
underlying Unicode character stream, allowing the IME to read surrounding text for context,
apply composition underlines, and commit text.
To initiate a pre-edit state under TSF, an IME calls the ITfContextComposition::StartComposition
method, which returns an ITfComposition object. The text service retains this object to update
the composition string and applies display attributes so the application knows to render an
underline. When the user selects a candidate, the IME calls ITfComposition::EndComposition to
finalize the input, collapsing the composition string into standard text.3
macOS and iOS: The Input Method Kit (IMK)
Apple's macOS ecosystem utilizes the Input Method Kit (IMK), an Objective-C framework (now
heavily interfaced via Swift) introduced in OS X 10.5 Leopard.6 IMK manages the
communication between client applications, candidate windows, and custom input method
engines, allowing developers to build IMEs as independent, out-of-process background
applications.6
The IMK architecture is driven by the IMKServer class, which is instantiated in the main function
of the input method application and manages Inter-Process Communication (IPC) connections
to the client applications.6 For each active text field (input session) in the host application, the
IMKServer instantiates an IMKInputController object.4 The controller intercepts incoming
keystrokes via the handleEvent:client: method, granting the IME the opportunity to consume the
event before it reaches the application.17
If the keystroke triggers a complex input sequence, the controller updates the client's pre-edit

buffer using methods such as setMarkedText. If the event corresponds to candidate selection,
the controller finalizes the sequence via insertText.4 Because modern macOS enforces strict
application sandboxing protocols, the framework relies heavily on asynchronous Remote
Procedure Calls (RPC) over XPC connections, requiring developers to carefully manage thread
execution, often confining API interactions strictly to the Swift MainActor to prevent deadlocks
between the IME process and the client application.18
Linux: XKB, Display Server Protocols, and IM Daemons
The Linux text input stack is notoriously layered, characterized by a historical transition from the
X11 display server to the modern Wayland protocol.19 At the foundational hardware-abstraction
level sits XKB (X Keyboard Extension). XKB intercepts low-level hardware scan codes from the
kernel and maps them to standard layout definitions, generating keysyms (such as Multi_key
used for basic compose sequences).21
However, for complex text input requiring state and dictionaries, XKB is insufficient. Linux
delegates this to external Input Method Frameworks (IMFs) such as IBus (Intelligent Input Bus),
Fcitx5, SCIM, and uim.22 These frameworks operate as background daemons that intercept
keystrokes before they are processed by the application's GUI toolkit.
The mechanism of interception depends on the display server. Under traditional X11,
communication is historically managed via XIM (X Input Method), though modern GTK and Qt
applications bypass XIM to utilize specific IM modules triggered by environment variables such
as GTK_IM_MODULE=ibus or QT_IM_MODULE=fcitx.20 Under Wayland, the architecture shifts
significantly: applications communicate with the Wayland compositor using native text-input
protocols (e.g., text-input-v3), and the compositor acts as a privileged intermediary,
communicating with the input method daemon via protocols like input-method-v2.25
Crucially, frameworks like IBus and Fcitx5 are essentially host environments. They rely on
external engine libraries, such as m17n, to provide specific phonetic, transliteration, or layout
rules for hundreds of languages, allowing a user to type complex scripts without requiring a
bespoke IME executable for every single language.27
Android: InputMethodService and the Soft-Keyboard Paradigm
Unlike desktop environments where the IME operates as an invisible daemon intercepting
physical hardware keys, Android IMEs serve primarily as visible, on-screen soft keyboards. The
Android input architecture revolves entirely around the InputMethodService base class.30
Communication between the Android IME and the target EditText UI widget is facilitated via the
InputConnection interface.30 When a user types a complex script, the Android IME utilizes the
InputConnection.setComposingText(CharSequence, int) method to push characters into a
pre-edit buffer within the application. The operating system highlights this text using a
SPAN_COMPOSING span to indicate its active state.5
The composing region and the active text selection are managed independently, giving the IME
full control over the buffer.5 Upon user candidate selection or sequence completion, the IME
calls InputConnection.commitText(CharSequence, int). This method clears the composing span,

permanently commits the text to the document, and simultaneously advances the cursor
position, preparing the editor for the next input sequence.5
Typological Analysis of Complex-Script Processing
Mechanisms
To accurately define what an open keyboard layout model must support natively via transforms,
versus what must be delegated to the OS architectures described above, it is vital to analyze
the exact linguistic and programmatic processing required for major complex scripts.
Chinese: Dictionary Dependency and the Necessity of IMEs
Chinese input methods rely fundamentally on the conversion of structural or phonetic
components into Han ideographs. Due to the massive character inventory—consisting of tens of
thousands of codepoints—and an incredibly high degree of homophony, these systems strictly
require dictionary-backed, stateful IMEs.32
Chinese input is generally divided into phonetic and shape-based methodologies. Phonetic
methods, such as Pinyin (using Latin letters) and Zhuyin/Bopomofo (using specialized phonetic
symbols), allow the user to type the pronunciation of a character.33 Because dozens of distinct
characters share the exact same pronunciation and tone (for example, the phonetic syllable
"shi" maps to over 40 common Han characters), the input mapping is wildly non-deterministic.
The IME must maintain sophisticated frequency dictionaries and N-gram language models to
predict the intended character based on sentence context. Consequently, a pre-edit buffer and a
candidate window are absolutely mandatory for user disambiguation.32
Shape-based methods, such as Wubi, Cangjie, and Stroke input, operate differently. The user
types characters by conceptually deconstructing them into their graphical radicals or individual
brush strokes. While this severe structural filtering reduces homophony and often results in a
single definitive output character, it remains a non-algorithmic process. The mapping of a
specific radical sequence to a final Unicode Han character still requires an internal lookup table
(a static dictionary). Furthermore, short-codes often overlap, necessitating occasional fallbacks
to candidate selection. Therefore, all forms of Chinese input necessitate a full IME and cannot
be expressed purely via a stateless layout definition or a deterministic transform.
Japanese: Morphological Conversion and Kana-to-Kanji
Japanese text input is historically executed as a multi-stage process. Users typically input Latin
characters (Romaji), which the input system instantly transforms into syllabic Kana characters
(Hiragana or Katakana). Some users utilize Direct Kana input, where the physical keys map
directly to Kana symbols. The initial Romaji-to-Kana step is a highly predictable, deterministic
transformation (for instance, typing the sequence k followed by a deterministically yields か).
However, the subsequent step introduces profound complexity. Because Japanese is written
without spaces and utilizes a mix of syllabaries and logographic Kanji, the user must press the
Spacebar to initiate Kana-to-Kanji conversion. At this point, the IME engine (such as Anthy,
Mozc, or the Microsoft Japanese IME) performs morphological analysis on the continuous,
unspaced string of Hiragana in the pre-edit buffer. It segments the string into discrete

grammatical words and replaces the phonetic representations with their appropriate logographic
Kanji representations based on contextual dictionaries.
While the initial Romaji-to-Kana phase could theoretically be implemented as a layout-level
transform, the requisite Kana-to-Kanji phase requires a fully stateful, dictionary-driven IME with
a candidate window to disambiguate homophones.
Korean (Hangul): Pure Algorithmic Automata
Unlike Chinese and Japanese, modern Korean input does not inherently require a dictionary,
morphological analysis, or a candidate window. Hangul is a highly logical, featural writing
system where individual letters (Jamo) mathematically combine into two-dimensional syllable
blocks.
The composition of Hangul is entirely algorithmic. The Unicode Standard contains a dedicated
block for individual Hangul Jamo (U+1100–U+11FF), as well as a massive block for
precomposed Hangul syllables (U+AC00–U+D7A3).34 This precomposed block contains 11,172
possible combinations of initial consonants (Choseong), vowels (Jungseong), and optional final
consonants (Jongseong).34
The formula to dynamically compose a single Hangul syllable ( ) from a sequence of typed
Jamos is explicitly defined in Section 3.12 of the Unicode Standard, utilizing absolute integer
constants 35: Let , , .
Let . Let , , .
Let .
If a user types an initial consonant , a vowel , and an optional final consonant , the
Unicode codepoint of the precomposed syllable is computed strictly via integer arithmetic:
The input mechanism tracks the state of the current syllable. If the user types a sequence that
breaks the phonetic rules of a single block (for example, typing a vowel after a completed
syllable), the state automaton gracefully extracts the final consonant of the previous syllable to
act as the initial consonant of the new syllable. Because Hangul composition is purely
algorithmic, mathematically deterministic, and completely dictionary-free, it can be seamlessly
managed by a sophisticated Transform/Reorder layer natively within a keyboard layout
standard.
Indic and Brahmic Scripts: Reordering and Conjunct Formation
Scripts deriving from the Brahmi lineage—such as Devanagari, Bengali, Tamil, and
Malayalam—utilize an Abugida writing system. In these scripts, consonants carry an inherent
vowel sound. Vowels that deviate from the inherent sound are appended as dependent signs
(Matras or Swaras).37 Furthermore, consonants are frequently combined into complex, joined

ligatures (Conjuncts) by inserting a strict suppression character known as a Halant or Virama
between them.37
The standard hardware layout across India is the InScript layout, standardized by the Bureau of
Indian Standards, which logically groups vowels on the left side of the physical keyboard and
consonants on the right.39 The complexity of Indic input arises because the chronological typing
order does not always match the visual rendering order. For instance, in many Indic scripts, a
short "i" vowel is pronounced after the consonant but must be rendered visually before the
consonant.
To form a complex conjunct like the Bengali jofola (য +
្
+
ល
), the user types the logical
sequence of discrete consonants and the Virama.40 Indic script input is deterministic; it does not
require a dictionary or candidate selection. The primary challenges involve translating phonetic
keystrokes into correct Unicode scalar values, applying contextual sorting algorithms, and
ensuring strict Unicode Normalization (Forms C and D, as per UAX #15). This behavior falls
directly and exclusively into the domain of a Transform/Reorder layer.
Arabic and Hebrew: Delineating Input from Contextual Shaping
A pervasive point of confusion in text processing engineering is the distinction between inputting
Arabic or Hebrew and rendering it. Both scripts are written Right-to-Left (RTL), and Arabic
characters drastically change their visual glyph shape depending on their position within a word
(isolated, initial, medial, or final).41
However, the input layer for Arabic and Hebrew is remarkably simple. The user types the logical
characters in memory order. A standard Arabic keyboard maps one physical key to one logical
Unicode character (for example, the letter Seen, U+0633).42 The keyboard layout, and the input
model broadly, does absolutely no shaping.
The complex computational task of analyzing surrounding characters and choosing the correct
cursive medial or final glyph is the exclusive responsibility of the downstream Rendering and
Shaping Engine, such as HarfBuzz, Apple's CoreText, or Microsoft's DirectWrite.43 HarfBuzz
processes the linear stream of logical Unicode codepoints from the document's memory and
converts them into specific glyph IDs drawn from the font's internal OpenType tables.43 Similarly,
typing Arabic diacritics (Harakat) merely inserts combining marks into the logical text stream; the
renderer subsequently handles the complex vertical overlaying.44 Therefore, Arabic and Hebrew
require nothing more than a simple Static Keyboard Layout, as all complexity resides safely
out-of-scope in the text shaping engine.
Southeast Asian Scripts: Syntactic Validation and Subjoined State
Tracking
Southeast Asian scripts present a unique architectural challenge: they require strict syntactic
sequence validation and complex visual reordering, but not necessarily dictionaries.
For the Thai language, the National Electronics and Computer Technology Center (NECTEC)
defined the WTT 2.0 standard to enforce strict input sequence rules.45 A Thai syllable consists
of base consonants, leading vowels, following vowels, below-vowels, above-diacritics, and tone

marks.47 WTT 2.0 defines three levels of input strictness (Level 0: pass-through, Level 1: basic
check, Level 2: strict check) to prevent syntactically invalid strings.45 For example, the system
must actively reject keystrokes that attempt to place two tone marks on the same base
consonant.45 A compliant input system must track the internal state of the active cell and reject
invalid keystrokes dynamically.
For Khmer, the Coeng character (U+17D2) is typed to indicate that the subsequent consonant
should not be rendered normally, but rather as a subjoined, subscript form.48 Similarly, Myanmar
(Burmese) input requires significant reordering. This is especially true when transitioning from
the legacy, visually-encoded Zawgyi standard to strict Unicode, where characters must be input
and stored in a specific logical order regardless of their final visual rendering on the screen.50
Because syntactic validation and subjoined character generation are deterministic, rule-based
operations, they require a state machine capable of regex-like pattern matching and
invalidation. They fit cleanly into a robust Transform/Reorder layer.
The LDML Keyboard 3.0 Specification: Bridging
Layouts and Transforms
For engineers developing an open layout standard, the Unicode Consortium's Locale Data
Markup Language (LDML) Keyboard 3.0 specification (UTS #35, Part 7) provides the definitive
structural baseline.1 LDML 3.0 is an XML-based interchange format explicitly designed to bridge
the gap between static key mappings and state-driven deterministic transformations.54 It
introduces comprehensive transform and reorder capabilities to handle algorithmic complex
scripts without mandating a full OS-level IME.
The specification operates via a <transforms> block, housing multiple <transformGroup>
elements which contain discrete <transform> or <reorder> definitions.53 The format allows
developers to define regular-expression-like character classes using string variables (${var-id})
and mapped sets ($[1:var-id]) to represent massive groups of characters compactly (e.g.,
matching all Thai consonants).55
Crucially, LDML 3.0 introduces state markers (\m{marker-id}).55 Markers allow the layout to
retain a hidden internal state across multiple keystrokes without outputting literal text to the host
OS. This enables the multi-step finite state automata required to execute Hangul decomposition
formulas or track Thai WTT 2.0 validation stages.52 Furthermore, <reorder> elements allow the
engine to apply complex sorting algorithms to typed sequences. The LDML engine generates a
multi-tiered sort key—consisting of primary, index, tertiary, and quaternary weights—for each
character.55 This effectively resolves the requirements of Indic and Myanmar scripts to sort
combining marks or logically reorder vowels into their correct relative positions.55
However, LDML 3.0 explicitly defines its boundaries as an interchange format.53 It deliberately
stops short of implementing features requiring heavy computational processing or external
linguistic resources. Adaptation for screen scaling, resolution modifications, and
platform-specific frame keys (like Fn or IME swap keys) are entirely out of scope.55 LDML
provides absolutely no mechanism for dictionary lookups, external network requests,
morphological analysis, or UI component definitions (like candidate windows).

Adjacent but Distinct Input Modalities
When defining the technical scope of an open layout model, systems engineers must recognize
features that run parallel to text input but must be strictly excluded from the structural layout
format:
1. Predictive Text and Autocorrect: While these features heavily manipulate the active text
buffer—often replacing misspelled words or suggesting the next chronological word—they
rely on statistical language models. They operate strictly above the input layout layer,
typically triggered as a post-processing event upon hitting the spacebar or punctuation.
2. Transliteration Input: Systems that allow a user to type Latin characters (e.g.,
"namaste") and output foreign scripts (e.g., "नमस्त"े ) rely on vast phonetic dictionaries to
bridge unassociated script families. Like CJK input, this requires a stateful IME and
candidate windows, placing it out of scope for a static layout specification.20
3. Handwriting and Voice Recognition: These alternative input modalities utilize machine
learning classifiers (Optical Character Recognition and Automatic Speech Recognition).
Frameworks like TSF and IMK handle these by feeding the resultant text strings directly
into the application's document context, bypassing the keyboard layout layer entirely.57
Delineating the Three-Tier Decision Boundary
To build a modular and interoperable open keyboard layout model, architects must implement a
strict three-way decision boundary. Features must be categorically isolated into one of the
following three buckets based on precise technical constraints.
Bucket 1: The Static Keyboard Layout Layer
● Criteria: The mapping from physical key sequence to Unicode character is strictly
one-to-one or sequentially stateless. It utilizes limited, single-depth state management
(e.g., standard European dead keys). It requires zero knowledge of the previously
committed text buffer outside of the active dead-key state.
● Behaviors Placed Here: Standard Latin, Cyrillic, and Greek inputs. Arabic and Hebrew
logical character input (as contextual shaping is safely deferred to the OS rendering
engine).41 Base character mappings for all complex scripts prior to transformation.
Bucket 2: The Transform / Reorder Layer
● Criteria: The mapping from key sequence to character output is many-to-many or
context-dependent, but fundamentally deterministic and algorithmically solvable. It
requires multi-step state tracking, achievable via finite state transducers, regular
expressions, or internal memory markers. It executes character reordering, substitution, or
invalid keystroke rejection. Crucially, it does not require an external dictionary, language
model, or user-facing candidate UI.
● Behaviors Placed Here: Korean Hangul Jamo composition and arithmetic
decomposition.35 Indic/Brahmic conjunct formation and visual vowel reordering.37 Strict
Unicode Normalization execution (NFC/NFD).34 Southeast Asian (Thai/Khmer/Myanmar)
syntactic sequence validation (e.g., WTT 2.0 Level 2) and subscript generation.46

Bucket 3: The Full Input Method Editor (IME) Layer
●  Criteria: The input mapping is inherently ambiguous due to phonetic or structural
homophony, requiring morphological analysis or linguistic disambiguation. It necessitates
heavy external data structures (frequency dictionaries, n-gram models, ML predictive
engines).32 It requires deep OS-level GUI integration, specifically a pre-edit composition
buffer and an interactive candidate window.5 It executes asynchronous callbacks or
network requests.
●  Behaviors Placed Here: Chinese Pinyin, Zhuyin, Wubi, Cangjie, and Stroke input.32
Japanese Romaji-to-Kana-to-Kanji conversion engines. Any input method relying on a
semantic or phonetic translation into complex logographs.
Script Capabilities Matrix
The following matrix synthesizes the architectural requirements for supporting major script
families, detailing exactly where the execution responsibility lies for each input mechanism.
Script Family /  Typical Input  Provided by  Expressible  Requires Full
| Language  | Method(s)        | Layout Layer  | via             | IME            |
| --------- | ---------------- | ------------- | --------------- | -------------- |
|           |                  |               | Transforms/R    | (Dictionary/Ca |
|           |                  |               | eorders (e.g.,  | ndidates/Conv  |
|           |                  |               | LDML)           | ersion)        |
| Chinese   | Pinyin, Zhuyin,  | Base key      | None.           | Yes.           |
|           | Wubi, Cangjie,   | capture.      |                 | Mandatory for  |
|           | Stroke           |               |                 | homophone      |
disambiguation
,
shape-to-logog
raph mapping,
and candidate
selection.
| Japanese  | Romaji-to-Kan   | Base Romaji or  | Romaji-to-Kan   | Yes.           |
| --------- | --------------- | --------------- | --------------- | -------------- |
|           | a,              | Kana capture.   | a deterministc  | Mandatory for  |
|           | Kana-to-Kanji,  |                 | translation.    | morphological  |
|           | Direct Kana     |                 |                 | Kana-to-Kanji  |
conversion and
dictionary
lookups.
| Korean  | Hangul Jamo  | Jamo base    | Yes.         | No. (While    |
| ------- | ------------ | ------------ | ------------ | ------------- |
|         | combining    | characters.  | Algorithmic  | historically  |

|     |     |     | composition     | implemented     |
| --- | --- | --- | --------------- | --------------- |
|     |     |     | (Choseong,      | as an OS IME,   |
|     |     |     | Jungseong,      | it is           |
|     |     |     | Jongseong) via  | mathematically  |
|     |     |     | integer         | expressible     |
|     |     |     | arithmetic.     | without         |
dictionaries).
Indic/Brahmic  InScript,  Consonant/vo Yes. Virama  No. (Unless
|     | phonetic typing  | wel base  | conjunct      | using            |
| --- | ---------------- | --------- | ------------- | ---------------- |
|     |                  | mapping.  | formation,    | cross-script     |
|     |                  |           | visual vowel  | Latin            |
|     |                  |           | reordering,   | transliteration  |
|     |                  |           | character     | workflows).      |
normalization.
| Arabic/Hebre | Direct logical  | Yes. 1:1 logical  | None.        | No.  |
| ------------ | --------------- | ----------------- | ------------ | ---- |
| w            | typing          | code point        | (Contextual  |      |
|              |                 | mapping.          | cursive      |      |
shaping is
deferred
entirely to text
renderers).
| Thai  | WTT 2.0       | Consonants,  | Yes. Syntactic  | No.  |
| ----- | ------------- | ------------ | --------------- | ---- |
|       | (Ketmanee/Pat | tone marks.  | sequence        |      |
|       | tachote)      |              | validation,     |      |
invalid state
rejection,
marker
tracking.
| Khmer/Myanm | Logical typing  | Base         | Yes. Subjoined  | No.  |
| ----------- | --------------- | ------------ | --------------- | ---- |
| ar/Lao      | with            | consonants.  | character       |      |
|             | Coeng/Virama    |              | conversion      |      |
(Coeng
U+17D2),
sequence
reordering.

Implications for an Open Layout Model
For engineers designing a modern, open keyboard layout architecture, attempting to build a
monolithic engine that processes everything from basic Latin dead keys to Chinese Pinyin
conversion is an architectural anti-pattern. The model must be highly modular, adhering strictly
to the separation of concerns established above.
First, the open model must natively support, parse, and execute the transform, reorder, and
marker paradigms defined in the LDML Keyboard 3.0 specification. By doing so, the engine can
natively process Hangul automata, Indic conjunct reordering, and Southeast Asian syntactic
validation purely in-memory, without forcing the user to install a heavyweight OS-level IME for
mathematically deterministic scripts. The layout engine must contain an internal finite-state
machine capable of evaluating sorting keys and applying strict Unicode Normalization prior to
outputting text to the operating system's active context.
Second, the layout engine must remain entirely decoupled from text shaping. The model should
never attempt to map an Arabic "Heh" to its medial or isolated glyph based on keystroke
context. It must blindly emit the base Unicode scalar values and trust the OS rendering engine
(e.g., HarfBuzz or DirectWrite) to execute the cursive joining and diacritic overlay visually.
Finally, for scripts requiring a full IME (Bucket 3), the open layout schema must strictly avoid
embedding dictionary files or attempting to implement candidate window GUI logic. Instead, the
layout format should define a declarative metadata standard that explicitly hands off execution
to a registered OS-level IME daemon. For instance, an XML or JSON definition for a Simplified
Chinese layout should declare its requirements as metadata (e.g., <requires-ime
protocol="text-input-v3" engine="fcitx5-pinyin" />). By utilizing this declarative reference, the
layout file remains lightweight, cross-platform, and highly interoperable. When an operating
system parses this layout, it checks for the presence of the required IME daemon and safely
delegates the entire composition, pre-edit, and commit lifecycle to the host OS's native text
services framework.
Sources des citations
1. CLDR/LDML Keyboards - Keyman, consulté le juin 7, 2026,
https://keyman.com/ldml/
2. Input Method Editors (IME) - Windows apps | Microsoft Learn, consulté le juin 7,
2026,
https://learn.microsoft.com/en-us/windows/apps/develop/input/input-method-editor
s
3. Compositions - Win32 apps | Microsoft Learn, consulté le juin 7, 2026,
https://learn.microsoft.com/en-us/windows/win32/tsf/compositions
4. IMKInputController | Apple Developer Documentation, consulté le juin 7, 2026,
https://developer.apple.com/documentation/inputmethodkit/imkinputcontroller
5. InputConnection | API reference - Android Developers, consulté le juin 7, 2026,
https://developer.android.com/reference/android/view/inputmethod/InputConnectio

n
6. InputMethodKit | Apple Developer Documentation, consulté le juin 7, 2026,
https://developer.apple.com/documentation/inputmethodkit
7. Status, Composition, and Candidates Windows - Win32 apps | Microsoft Learn,
consulté le juin 7, 2026,
https://learn.microsoft.com/en-us/windows/win32/intl/status--composition--and-can
didates-windows
8. IInputConnection.CommitText Method (Android.Views.InputMethods) | Microsoft
Learn, consulté le juin 7, 2026,
https://learn.microsoft.com/en-us/dotnet/api/android.views.inputmethods.iinputcon
nection.committext?view=net-android-35.0
9. What is the correct, modern way to handle arbitrary text input in a custom control
on Windows? WM_CHAR? IMM? TSF? - Stack Overflow, consulté le juin 7, 2026,
https://stackoverflow.com/questions/40453186/what-is-the-correct-modern-way-to-
handle-arbitrary-text-input-in-a-custom-contr
10. Text Services Framework - Grokipedia, consulté le juin 7, 2026,
https://grokipedia.com/page/text_services_framework
11. Why Use Text Services Framework - Win32 apps - Microsoft Learn, consulté le
juin 7, 2026,
https://learn.microsoft.com/en-us/windows/win32/tsf/why-use-text-services-framew
ork
12. Architecture (Text Services Framework) - Win32 apps - Microsoft Learn, consulté
le juin 7, 2026, https://learn.microsoft.com/en-us/windows/win32/tsf/architecture
13. ITfDocumentMgr interface (msctf.h) - Win32 - Microsoft Learn, consulté le juin 7,
2026,
https://learn.microsoft.com/da-dk/windows/win32/api/msctf/nn-msctf-itfdocumentm
gr
14. win32/desktop-src/TSF/text-services-framework-interfaces.md at docs - GitHub,
consulté le juin 7, 2026,
https://github.com/MicrosoftDocs/win32/blob/docs/desktop-src/TSF/text-services-fr
amework-interfaces.md
15. Input Method Kit Overview and Guide | PDF | Class (Computer Programming) -
Scribd, consulté le juin 7, 2026,
https://www.scribd.com/document/2934627/Beijing-Presentation
16. IMKServer | Apple Developer Documentation, consulté le juin 7, 2026,
https://developer.apple.com/documentation/inputmethodkit/imkserver
17. Intercept Command+key with IMKit (or similar) - Stack Overflow, consulté le juin 7,
2026,
https://stackoverflow.com/questions/21412985/intercept-commandkey-with-imkit-o
r-similar
18. macOS Input Method Development Guidelines for 2026 | by Shiki Suen - Medium,
consulté le juin 7, 2026,
https://shikisuen.medium.com/macos-input-method-development-guidelines-for-20
26-5123461fa53b
19. The Input Stack on Linux: An End-To-End Architecture Overview - Reddit,

consulté le juin 7, 2026,
https://www.reddit.com/r/linux/comments/1p87bc2/the_input_stack_on_linux_an_e
ndtoend_architecture/
20. Understanding & setting up different input methods - Unix & Linux Stack
Exchange, consulté le juin 7, 2026,
https://unix.stackexchange.com/questions/260601/understanding-setting-up-differ
ent-input-methods
21. Xorg/Keyboard configuration - ArchWiki, consulté le juin 7, 2026,
https://wiki.archlinux.org/title/Xorg/Keyboard_configuration
22. IBus - ArchWiki, consulté le juin 7, 2026, https://wiki.archlinux.org/title/IBus
23. Smart Common Input Method - ArchWiki, consulté le juin 7, 2026,
https://wiki.archlinux.org/title/Smart_Common_Input_Method
24. InputMethods/SCIM - Ubuntu Wiki, consulté le juin 7, 2026,
https://wiki.ubuntu.com/InputMethods/SCIM
25. Fcitx5 - ArchWiki, consulté le juin 7, 2026, https://wiki.archlinux.org/title/Fcitx5
26. about Input Method wayland protocols · Issue #2331 · ibus/ibus - GitHub, consulté
le juin 7, 2026, https://github.com/ibus/ibus/issues/2331
27. Control ibus layouts right from Linux terminal - GitHub Gist, consulté le juin 7,
2026, https://gist.github.com/adnan360/11aed4d206004f32153d83c2d475eb95
28. Chapter 7. Smart Common Input Method | International Language Support Guide |
Red Hat Enterprise Linux | 5, consulté le juin 7, 2026,
https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/5/html/interna
tional_language_support_guide/red_hat_enterprise_linux_international_language_
support_guide-smart_common_input_method
29. SCIM Input Method not working - Ask Ubuntu, consulté le juin 7, 2026,
https://askubuntu.com/questions/165980/scim-input-method-not-working
30. InputConnection | API reference - Android Developers, consulté le juin 7, 2026,
https://developer.android.com/reference/kotlin/android/view/inputmethod/InputCon
nection
31. IInputConnection.SetComposingText Method (Android.Views.InputMethods),
consulté le juin 7, 2026,
https://learn.microsoft.com/en-us/dotnet/api/android.views.inputmethods.iinputcon
nection.setcomposingtext?view=net-android-35.0
32. Ubuntu Chinese Input: IBus Vs Fcitx5 Setup - SysTutorials, consulté le juin 7,
2026,
https://www.systutorials.com/how-to-add-chinese-input-method-to-unbuntu-18-04/
33. Unicode Chart, consulté le juin 7, 2026,
https://www.ssec.wisc.edu/~tomw/java/unicode.html
34. Hangul Jamo (Unicode block) - Wikipedia, consulté le juin 7, 2026,
https://en.wikipedia.org/wiki/Hangul_Jamo_(Unicode_block)
35. Hangul - tcPDF, consulté le juin 7, 2026,
https://tcpdf.org/docs/srcdoc/tc-lib-unicode/classes-Com-Tecnick-Unicode-Data-H
angul/
36. Breaking down a Hangul syllable into letters (jamo) - Stack Overflow, consulté le
juin 7, 2026,

https://stackoverflow.com/questions/41309402/breaking-down-a-hangul-syllable-in
to-letters-jamo
37. Inscript keyboard - Baraha, consulté le juin 7, 2026,
https://baraha.com/help/Keyboards/inscript-keyboard.htm
38. TDIL-DC :Keyboard standards, consulté le juin 7, 2026,
https://tdil-dc.in/index.php?option=com_vertical&parentid=12
39. Typing with Inscript Keyboard, consulté le juin 7, 2026,
https://narakas.rajbhasha.gov.in/pdf/379/3790034.pdf
40. Bangla INSCRIPT conjuncts not appearing automatically - Microsoft Q&A,
consulté le juin 7, 2026,
https://learn.microsoft.com/en-ca/answers/questions/5614516/bangla-inscript-conj
uncts-not-appearing-automatica
41. Arabic complex text layout problem · Issue #480 · harfbuzz/harfbuzz - GitHub,
consulté le juin 7, 2026, https://github.com/harfbuzz/harfbuzz/issues/480
42. Arabic and Hebrew features in InDesign - Adobe Help Center, consulté le juin 7,
2026, https://helpx.adobe.com/indesign/using/arabic-hebrew.html
43. Why do I need a shaping engine? - HarfBuzz, consulté le juin 7, 2026,
https://harfbuzz.github.io/why-do-i-need-a-shaping-engine.html
44. Arabic Decoding for Games & Game Engines – Part 5: Diacritics, consulté le juin
7, 2026,
https://mamoniem.com/arabic-decoding-for-games-game-engines-part-5-diacritics/
45. Standardization and Implementations of Thai Language - NECTEC, consulté le
juin 7, 2026, https://www.nectec.or.th/it-standards/thaistd.pdf
46. Computers and the Thai Language, consulté le juin 7, 2026,
https://www.computer.org/csdl/magazine/an/2009/01/man2009010046/13rRUytWF
b7
47. Thai Input Method Implementations, consulté le juin 7, 2026,
https://linux.thai.net/~thep/th-xim/
48. Khmer (Unicode block) - Grokipedia, consulté le juin 7, 2026,
https://grokipedia.com/page/khmer_unicode_block
49. Developing OpenType Fonts for Khmer Script - Typography - Microsoft Learn,
consulté le juin 7, 2026,
https://learn.microsoft.com/en-us/typography/script-development/khmer
50. FAQ - Myanmar Scripts and Languages - Unicode, consulté le juin 7, 2026,
http://www.unicode.org/faq/myanmar.html
51. A Guide to Using Myanmar Unicode: Introduction - thanlwinsoft.github.com,
consulté le juin 7, 2026,
https://thanlwinsoft.github.io/www.thanlwinsoft.org/ThanLwinSoft/MyanmarUnicod
e/Intro.html
52. Keyboard Intake Procedures in CLDR - Unicode CLDR Project, consulté le juin 7,
2026, https://cldr.unicode.org/index/process/keyboard-repository-process
53. Unicode Locale Data Markup Language (LDML) Part 7: Keyboards, consulté le
juin 7, 2026, https://www.unicode.org/reports/tr35/tr35-70/tr35-keyboards.html
54. Unicode Locale Data Markup Language (LDML), consulté le juin 7, 2026,
https://www.unicode.org/reports/tr35/

55. Unicode Locale Data Markup Language (LDML) Part 7: Keyboards, consulté le
juin 7, 2026, https://unicode.org/reports/tr35/tr35-keyboards.html
56. Keyman for macOS Version History, consulté le juin 7, 2026,
https://help.keyman.com/products/mac/version-history
57. Leveraging Microsoft Text Services Framework (TSF) for Red Team Operations -
Praetorian, consulté le juin 7, 2026,
https://www.praetorian.com/blog/leveraging-microsoft-text-services-framework-tsf-f
or-red-team-operations/
58. Unicode Locale Data Markup Language (LDML) Part 7: Keyboards, consulté le
juin 7, 2026, https://www.unicode.org/review/pri476/spec/tr35-keyboards.pdf