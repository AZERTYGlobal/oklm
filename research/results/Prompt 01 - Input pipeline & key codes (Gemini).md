Architectural Mapping of Keyboard
Input Pipelines: From Physical Switch to
Operating System Character
Composition
The translation of a kinetic, physical key press into a textual character or a functional action
across modern computing systems represents one of the most complex, legacy-burdened
hardware-to-software pipelines in computer science. Modern operating systems—specifically
Windows, macOS, and Linux—employ radically different architectural models to process,
abstract, and map keyboard input. For engineers designing an open, OS-independent model to
describe keyboard layouts, understanding the granular mechanics of this pipeline is mandatory.
This report provides an exhaustive, end-to-end analysis of the keyboard input pipeline. It
dissects the hardware matrix scanning, the Universal Serial Bus (USB) Human Interface Device
(HID) protocols, the persistence of legacy PS/2 scancodes, OS-specific kernel drivers, virtual
key abstractions, and user-space composition engines. Furthermore, it details the geometric
idiosyncrasies of international standards (ANSI, ISO, JIS, ABNT) and the resulting implications
for constructing a stable, portable layout specification.
1. Glossary of Core Code Terminology
To establish a precise nomenclature for the architecture of keyboard input processing, the
following identifiers map the journey of a keystroke across the hardware and software layers.
Terminology Precise Definition
Scancode A low-level hardware identifier emitted by a
keyboard microcontroller (originally
adhering to PS/2 Sets 1, 2, or 3) representing
the physical position of a pressed or
released key, prior to any logical character
mapping.1
Usage ID A standardized, position-based 16-bit value
defined by the USB Implementers Forum
within a specific Usage Page (e.g., Page
0x07 for Keyboard/Keypad) identifying the
physical location of a key on a standard
reference layout.2

Keycode An OS-specific numeric identifier
representing a physical key after the
lower-level hardware protocols have been
parsed by the kernel input driver (e.g., Linux
evdev keycodes or macOS virtual
keycodes).4
Virtual Key (VK) A high-level, hardware-independent
numeric identifier used by an operating
system's user-space APIs (e.g., VK_* in
Windows) to represent the logical semantic
value of a physical key before shift-state
modifiers and dead-key composition are
applied.6
Keysym An abstraction utilized primarily by the X
Window System (X11/Wayland) consisting
of an integer value that defines the exact
logical character or action bound to a
specific keycode under current modifier
states.8
2. The End-to-End Input Pipeline Architecture
The transformation of a physical kinetic action into a rendered textual character involves a
strictly chronological traversal of hardware switch matrices, microcontroller firmware, USB
protocols, kernel-level device drivers, OS translation layers, and user-space layout models. The
relationship between physical position, the logical key representation, and the ultimately
produced character shifts across these boundaries. The physical position is immutable and
defined by hardware coordinates; the logical key is a software abstraction representing the
base semantic identity of the key; and the produced character is the final state-dependent
output.
2.1 Stage-by-Stage Pipeline Diagram
The following sequence illustrates the complete input pipeline, detailing what occurs at each
stage and identifying the component responsible for layout logic.
Pipeline Stage Component Action and Layout Ownership
Processing Logic
1. Physical Mechanical Switch A user depresses a None
Actuation mechanical switch,

membrane dome,
or capacitive
spring, closing an
electrical circuit.
2. Matrix Scan Keyboard The firmware Hardware routing
Microcontroller sequentially applies
voltage to row lines
and reads column
lines to detect
closed circuits
representing the
switch actuation.10
3. Debouncing & Keyboard Firmware The firmware filters Firmware
Anti-Ghosting out electrical noise
(contact bounce)
over a time window
and utilizes
anti-ghosting diode
matrices to validate
discrete N-key
rollover (NKRO)
states.12
4. Protocol USB HID Interface The microcontroller USB-IF Standard
Encoding maps the physical
switch location to a
USB HID Usage ID
(Page 0x07),
packaging the state
into an interrupt
transfer report.3
5. Kernel Driver OS HID Class Driver The OS USB host OS Kernel
Reception controller receives
the transfer. The
HID class driver
parses the report
descriptor and
hands the data to a
keyboard-specific

mapper.3
6. OS Input The kernel driver OS Kernel
Scancode/Keycod Subsystem maps the USB
e Translation Usage ID into a
low-level,
OS-specific
hardware
abstraction (e.g.,
PS/2 Set 1
scancodes on
Windows, evdev
constants on
Linux).1
7. Virtual Key OS Windowing The OS input OS User Space
Mapping System subsystem
translates the
low-level code into
a
hardware-independ
ent virtual keycode
(e.g., VK_Q,
kVK_ANSI_Q, or X11
keycode).17
8. Modifier State OS Layout Engine The layout engine OS Layout Model
Evaluation evaluates the
concurrent state of
modifier keys (Shift,
Alt, Control, Caps
Lock) using internal
bitmasks or
shift-level arrays.6
9. Dead Key OS Composition The OS checks if OS Layout Model
Composition Layer the current key
forms part of a
sequence (e.g., a
dead key) by
maintaining a state
machine variable.20

10. Character Application/Text The keyboard Application / OS
Resolution Buffer layout table outputs
the final Unicode
codepoint or
functional Keysym
to the active
application.6
2.2 Hardware Layer Mechanics: Matrix Scanning, Ghosting, and
Debouncing
Keyboards do not dedicate a discrete microcontroller General-Purpose Input/Output (GPIO)
pin to every single key, as a standard 104-key chassis would exhaust the available pins on
standard embedded microcontrollers. Instead, switches are wired into a grid known as a
keyboard matrix.11 The microcontroller performs a rapid polling loop: it drives one row line high
while keeping others at a high-impedance state, and then reads all column pins to detect
voltage.10 This scanning process occurs continuously, often at intervals of 20 microseconds per
row, allowing a full matrix scan every 200 microseconds.10
When multiple keys are pressed simultaneously, "ghosting" can occur. If three keys defining
three corners of a rectangle in the electrical matrix are depressed, the current flows backwards
through the intersecting traces, making the microcontroller falsely register the fourth corner as
pressed.13 To achieve true N-Key Rollover (NKRO), modern mechanical keyboards place a
switching diode in series with every key switch, ensuring current only flows in one direction and
entirely eliminating both ghosting and masking.12
Simultaneously, the firmware must "debounce" the signal. Physical metal contacts exhibit
elasticity, rapidly making and breaking the circuit at a microscopic level upon actuation. The
firmware implements a causal reconstruction algorithm, usually requiring the pin state to
remain stable (using a Schmitt trigger abstraction) for several consecutive polling cycles
(typically 5 to 20 milliseconds) before signaling a definitive state change to the USB controller.10
3. Key Code Systems and Their OS-Specific Roles
The mapping of keyboard identifiers is deeply fragmented. Operating systems rely on historical
artifacts—such as IBM PC AT scancodes and original Macintosh architectures—to process
modern USB inputs.
3.1 USB HID Usage IDs (Keyboard/Keypad Usage Page 0x07)
The transition to Universal Serial Bus (USB) keyboards established the Human Interface Device
(HID) protocol, standardizing input communication. The USB Implementers Forum (USB-IF)
maintains the HID Usage Tables, where Usage Page 0x07 is dedicated specifically to Keyboard
and Keypad devices.2
A critical architectural principle of the USB HID specification is that Usage IDs are strictly
position-based, not character-based.23 The Usage ID represents a specific physical coordinate

on a standard reference chassis. For example, Usage ID 0x14 is formally designated as
"Keyboard q and Q".2 If a user connects a keyboard configured physically for the French
AZERTY layout, pressing the key in the top-left alpha position (physically printed as "A") still
transmits Usage ID 0x14. The USB protocol is completely agnostic to the localized ink printed on
the keycaps; it relies entirely on the host operating system's software layout database to
translate 0x14 into the letter 'a' or 'q'.23
In the standard Boot Protocol mode—used for compatibility during UEFI/BIOS system startup
before full OS drivers load—the keyboard transmits an 8-byte input report. This structure
consists of a modifier byte (representing the state of the 8 standard modifier keys), a reserved
byte, and a 6-byte array allowing up to 6 simultaneous non-modifier key presses to be
reported.3 Modern keyboards operating outside of boot mode implement NKRO by utilizing
larger report descriptors with multiple arrays or bitmap representations of the entire Usage
Page.3
3.2 PS/2 Scan Code Sets (Set 1, Set 2, and Set 3)
Prior to USB, the IBM AT and PS/2 protocols defined keyboard communication. IBM developed
three distinct sets of hardware "scancodes": Set 1 (original PC/XT), Set 2 (AT keyboards), and
Set 3 (specialized terminals).1
Despite the obsolescence of the PS/2 connector, PS/2 scancodes deeply influence modern
operating systems. Under all Microsoft operating systems, legacy PS/2 keyboards actually
transmit Scan Code Set 2 values down the wire from the keyboard to the motherboard's i8042
controller chip. This chip transparently translates the Set 2 values into Scan Code Set 1 values
before passing them to the CPU.1 Set 1 scancodes operate using a discrete make/break
paradigm. For example, pressing the 'A' key emits a "make" code of 0x1E, and releasing it emits
a "break" code of 0x9E (which is the make code with the most significant bit set). Extended
keys—such as the arrow keys or the right Alt key—are preceded by a 0xE0 prefix to distinguish
them from standard keys.27
Even when a keyboard is connected via USB, Windows maintains an internal abstraction layer
(kbdhid.sys) that forces USB HID Usage IDs to be mapped back into legacy PS/2 Set 1
scancodes before passing them up the driver stack to kbdclass.sys.3 Scan Code Set 3 is
effectively ignored by modern consumer operating systems.1
3.3 Windows Virtual Key Codes (VK_*) and Translation
In Windows, the kernel driver (kbdclass.sys) passes the synthesized Set 1 scancodes up to the
Win32k.sys subsystem, which translates them into Virtual Key (VK) codes (e.g., VK_A,
VK_SPACE, VK_RETURN).6 Virtual Keys are hardware-independent numeric identifiers exposed
to user-space applications via messages like WM_KEYDOWN.29
The mapping of a scancode to a VK_ code, and subsequently to a Unicode character, is defined
by the active Windows Keyboard Layout DLL (KBD*.DLL). This translation relies on a complex
C-structure defined in the Windows Driver Kit as KBDTABLES.30 The BaseLayer configuration
translates the scancode into the corresponding VK_ code.

However, international key geometries expose deep idiosyncrasies in Windows VK mapping.
For instance, the extra physical key located to the left of "Z" on European ISO keyboards is
mapped to VK_OEM_102 (0xE2).17 On Brazilian ABNT2 keyboards, an extra key situated near the
right Shift key generates a highly specific VK_ABNT_C1 (0xC1).33 The translation from physical
scancode to Virtual Key is therefore not purely hardware-based; it is heavily influenced by the
localized expectations of the loaded DLL.
3.4 macOS Virtual Keycodes (Carbon / HIToolbox)
Apple's macOS bypasses the legacy of PS/2 scancodes entirely. At the kernel level, the
IOHIDSystem and AppleUSBHIDDriver parse USB HID reports.23 The operating system utilizes a
proprietary virtual keycode system originating from the classic Mac OS (documented in Inside
Mac Volume V) and formalized in the Carbon framework's Events.h and HIToolbox.4 These are
denoted by the kVK_ANSI_* constants.17
Like USB HID usages, kVK constants are strictly positional.18 The constant kVK_ANSI_S (0x01)
refers exclusively to the physical key in the second row, second column of the alphabetic block,
regardless of whether the software layout is Dvorak, AZERTY, or QWERTY.18 Applications must
utilize functions like UCKeyTranslate to pass the positional kVK code, combined with current
modifier states, through the active .keylayout XML file to produce a localized string.20
3.5 Linux: Evdev Keycodes, X11 Keycodes, and Keysyms
The Linux input pipeline fragments the translation process between the kernel space and the
user space display server (X11 or Wayland), relying heavily on the libxkbcommon library.
1. Evdev Keycodes: The Linux kernel's input subsystem (evdev) directly translates USB HID
usages into internal macro values defined in <linux/input-event-codes.h> (e.g., KEY_Q is
16, KEY_SPACE is 57).5 These codes represent the absolute physical hardware.
2. X11 Keycodes: For historical reasons relating to the early X Window System protocol, the
minimum valid keycode permitted was 8.19 Consequently, X11 keycodes are calculated as
the evdev keycode plus exactly 8.5 Thus, KEY_Q (16) becomes X11 keycode 24.
3. Keysyms: The user-space library libxkbcommon takes the X11 keycode and evaluates
the active keyboard layout configuration. It maps the integer keycode to a "Keysym" (e.g.,
XK_q or XK_Shift_L).8 Keysyms represent the exact, resolved semantic glyph or action,
fully abstracting away the physical hardware.
4. Physical Geometries and Key Naming Conventions
Keyboard layouts are not merely software constructs; they are rigidly constrained by the
physical geometry of the chassis.37 An OS-independent layout model must perfectly account
for the variations between standard physical formats, namely ANSI, ISO, JIS, and ABNT.
4.1 ANSI, ISO, JIS, and ABNT Chassis Variations
The physical arrangement of keys dictates which keycodes can physically be generated by the
user.

Standard Description and Defining Characteristics
ANSI The American National Standards Institute
layout, featuring 104 keys. It is defined by a
wide, single-row Enter key and a wide Left
Shift key.37
ISO The International Organization for
Standardization layout, featuring 105 keys.
It modifies ANSI by utilizing a tall, reverse-L
shaped Enter key, shortening the Left Shift,
and inserting a 105th physical key between
Left Shift and the 'Z' position.38
JIS The Japanese Industrial Standard 106-key
layout. It shortens the Backspace and Right
Shift keys, while drastically shrinking the
Spacebar to accommodate dedicated
Japanese Input Method Editor (IME) keys:
Muhenkan (Non-conversion), Henkan
(Conversion), Hiragana/Katakana, and
additional keys for Yen and Ro.40
ABNT / ABNT2 The Associação Brasileira de Normas
Técnicas layout used in Brazil. It adds a
specific physical key beside the Right Shift
(often used for / and ?) and a numeric
keypad separator.33
4.2 XKB Key Naming Standards
To address the variance in physical key placements across these geometries without relying on
OS-specific integer codes, the X11 Keyboard Extension (XKB) developed a standardized,
alphanumeric grid naming convention for physical switch positions.43
● Rows are designated by letters from bottom to top: Row A (Spacebar row), Row B (ZXCV
row), Row C (ASDF row), Row D (QWERTY row), and Row E (Numbers 1-0).44
● Columns are numbered sequentially from left to right.47
Under this nomenclature:
● AE01 designates the '1' key.48
● AD01 designates the 'Q' key.48
● AC01 designates the 'A' key.48

● AB01 designates the 'Z' key on ANSI, representing the leftmost letter of the bottom row.48
● TLDE designates the top-left key under Escape (typically Tilde/Grave).48
● BKSL designates the Backslash key.48
For the extra physical keys introduced by international geometries, XKB uses specific
mnemonic monikers rather than grid coordinates:
● LSGT (Less/Greater): The 105th key added in the ISO layout, located immediately to the
right of the shortened Left Shift.49
● AB11: The extra key located near the Right Shift on Japanese or ABNT layouts.49
5. Modifiers, Shift Levels, and State Modeling
Modifier keys dictate how the base physical input maps to alternate character outputs.
However, operating systems model modifier states with radically different underlying
mathematical logic, presenting a major architectural hurdle for portable layout models.
5.1 Shift Levels and Extended Modifiers
While standard modifiers include Shift, Control, Alt, and the Super/Command key, international
typography necessitates additional "levels" of character output beyond basic capitalization.21
● Level 1: The base character (e.g., 'a', '2').
● Level 2: The shifted character (e.g., 'A', '@').
● Level 3: Accessed via the AltGr (Right Alt) key. This is ubiquitous on ISO layouts for
inputting symbols like the Euro sign '€' or '@' on European configurations.51
● Level 5: Accessed via specialized modifiers (e.g., Mode_switch or ISO Level 5 shift) to
support heavily extended typographical or multilingual needs on a single layout.50
5.2 OS-Specific Modifier Implementations
The internal representation of these levels is completely divergent across operating systems.
Windows Bitmap Logic and the AltGr Hack: Windows manages modifiers using a 16-bit
bitmap. The active KBDTABLES DLL maps incoming Virtual Keys to internal bit flags: KBDSHIFT,
KBDCTRL, KBDALT, KBDKANA, KBDROYA, and KBDLOYA.6 These bits are ORed together. The
layout table then translates this ORed bitmap into a hidden integer called the "modification
column".6 The layout uses this modification column to select the correct character from the
active mapping array.6
Crucially, Windows implements the AltGr key (Level 3) via a hardcoded macro injection. When
the Right Alt key is pressed and the layout possesses the KLLF_ALTGR flag, the Windows kernel
artificially injects a fake Left Control down-event.6 Consequently, applications receiving
messages do not see a pure "AltGr" signal; they see Ctrl + Alt. If the user releases the Right Alt
key, Windows injects a fake Left Control up-event. Furthermore, Windows performs complex
virtual key massaging for Numpad keys if VK_SHIFT and NumLock are simultaneously active,
injecting fake Shift releases to invert the Numpad behavior.6
Linux (libxkbcommon) Procedural Types: Linux/XKB completely abandons bitmasks in favor
of a highly modular "types" system.21 libxkbcommon defines arbitrary xkb_types (e.g.,

ALPHABETIC, FOUR_LEVEL_ALPHABETIC). Each individual physical key is assigned a specific
type. The type definition explicitly declares how arbitrary combinations of modifiers (e.g., Shift
+ Level3_Shift) map to an integer array index (Level 1, 2, 3, 4, etc.).19 This makes XKB infinitely
extensible but structurally difficult to parse cleanly into a flat model.
macOS EventModifiers: macOS utilizes 32-bit EventModifiers masks (e.g., shiftKey, optionKey,
cmdKey, activeFlag).4 This state is passed directly as the modifierKeyState integer into the
UCKeyTranslate function.20 macOS neatly isolates the Option key (used for Level 3 output)
without injecting fake Control events, relying on the proprietary .keylayout XML structural
mappings to define the output permutations.36
5.3 Caps Lock and Locale-Specific Behavior
Caps Lock is not a simple inverse of the Shift key. Its behavior is deeply locale-specific and
layout-dependent. In standard US English layouts, Caps Lock affects only alphabetic keys.
However, in French AZERTY or German QWERTZ layouts, enabling Caps Lock often affects the
number row, effectively inverting the Shift requirement for digits versus symbols.53
Furthermore, some legacy Swiss or German configurations utilize a "Shift Lock" paradigm,
where pressing Caps Lock mimics holding the physical Shift key for all keys (including
punctuation), and only pressing the physical Shift key disengages the lock.53
6. Dead Keys and OS-Level Composition
Dead keys are keystrokes that do not immediately produce a character. Instead, they latch the
input subsystem into a temporary state, waiting for a subsequent keystroke to compose a
diacritic character (e.g., typing ~ then n to produce ñ).
6.1 State Machines and Layer Processing
The location and persistence of the dead key state machine varies fundamentally by operating
system.
macOS User-Space Pointers: macOS manages dead key state explicitly via framework
pointers. The UCKeyTranslate function accepts a deadKeyState parameter (a pointer to a
UInt32 variable).20 When a dead key is struck, UCKeyTranslate returns a string length of 0 and
mutates the deadKeyState integer.20 On the subsequent keystroke, the application feeds the
mutated state back into UCKeyTranslate. The API then resolves the composed character (or
ejects both the base character and the diacritic sequentially if the composition is invalid) and
resets the state to 0.55
Windows Thread-Local Destructive State: Windows maintains dead key state as a
thread-local property deeply embedded within the Win32 subsystem.57 The ToUnicodeEx
function applies the current thread's modifier and dead key state to the incoming virtual key.58
However, this architecture possesses a fatal flaw: calling ToUnicodeEx is destructive and
actually mutates the kernel's state. If a monitoring application, input interceptor, or terminal
emulator "peeks" at the keystroke by calling ToUnicodeEx, it will inadvertently consume the
dead key state, permanently preventing the target application from completing the
composition.59 To circumvent this, developers must execute complex workarounds to restore

the state, though historical implementations remain notoriously fragile.60
Linux Composition Separation: In modern Wayland and XKB implementations, libxkbcommon
explicitly separates basic layout translation from character composition. A dedicated
sub-module, xkbcommon-compose, is responsible for managing dead keys and Compose key
sequences (e.g., holding a dedicated Compose key, then typing , and c for ç).61 The client
application maintains an xkb_compose_state object in user-space, feeding keysyms into it
sequentially and querying the API to determine if the composition sequence is finished,
ongoing, or cancelled.61
7. Cross-Reference Table: The Anatomy of
Representative Keys
To illustrate the highly disjointed nature of physical key identifiers across systems, the following
table maps 10 representative physical locations across the USB, Windows, macOS, and Linux
evdev/XKB stacks.
| Physical  | USB HID   | Windows  | Windows  | macOS    | Linux  | Typical  |
| --------- | --------- | -------- | -------- | -------- | ------ | -------- |
| Descripti | Usage ID  | Scancod  | Virtual  | Virtual  | evdev  | X11      |
on (XKB  (Page  e (Set 1)  Key (VK)  Keycode  Keycode  Keysym
| Name)  | 0x07)  |     |     | (kVK)  |     | (Level 1,  |
| ------ | ------ | --- | --- | ------ | --- | ---------- |
US/Stand
ard)
| QWERTY    | 0x14  | 0x10  | VK_Q       | kVK_ANSI   | KEY_Q    | XK_q      |
| --------- | ----- | ----- | ---------- | ---------- | -------- | --------- |
| "Q"       |       |       | (0x51)     | _Q         | (16)     |           |
| (AD01)    |       |       |            | (0x0C)     |          |           |
| Key left  | 0x35  | 0x29  | VK_OEM_    | kVK_ANSI   | KEY_GRA  | XK_grave  |
| of "1"    |       |       | 3 (0xC0)   | _Grave     | VE (41)  |           |
| (TLDE)    |       |       |            | (0x32)*    |          |           |
| Spaceba   | 0x2C  | 0x39  | VK_SPAC    | kVK_Spa    | KEY_SPA  | XK_space  |
| r (SPCE)  |       |       | E (0x20)   | ce (0x31)  | CE (57)  |           |
| Enter     | 0x28  | 0x1C  | VK_RETU    | kVK_Retu   | KEY_ENT  | XK_Retur  |
| (Main)    |       |       | RN         | rn (0x24)  | ER (28)  | n         |
| (RTRN)    |       |       | (0x0D)     |            |          |           |
| Caps      | 0x39  | 0x3A  | VK_CAPIT   | kVK_Cap    | KEY_CAP  | XK_Caps   |
| Lock      |       |       | AL (0x14)  | sLock      | SLOCK    | _Lock     |
| (CAPS)    |       |       |            | (0x39)     | (58)     |           |

| ISO extra   | 0x64  | 0x56  | VK_OEM_   | kVK_ISO_ | KEY_102  | XK_less /  |
| ----------- | ----- | ----- | --------- | -------- | -------- | ---------- |
| key         |       |       | 102       | Section  | ND (86)  | XK_great   |
| (LSGT)      |       |       | (0xE2)    | (0x0A)*  |          | er         |
| JIS "Yen /  | 0x89  | 0x7D  | VK_OEM_   | kVK_JIS_ | KEY_YEN  | XK_yen     |
| |" (AE13)   |       |       | 5         | Yen      | (124)    |            |
|             |       |       | (0xDC)**  | (0x5D)   |          |            |
| JIS         | 0x8B  | 0x7B  | VK_NON    | kVK_JIS_ | KEY_MUH  | XK_Muhe    |
| "Muhenk     |       |       | CONVER    | Eisu     | ENKAN    | nkan       |
| an"         |       |       | T (0x1D)  | (0x66)   | (94)     |            |
(MUHE)
| JIS       | 0x8A  | 0x79  | VK_CON  | kVK_JIS_ | KEY_HEN   | XK_Henk   |
| --------- | ----- | ----- | ------- | -------- | --------- | --------- |
| "Henkan"  |       |       | VERT    | Kana     | KAN (92)  | an        |
| (HENK)    |       |       | (0x1C)  | (0x68)   |           |           |
| ABNT2     | 0x87  | 0x73  | VK_ABNT | Undefine | KEY_RO    | XK_slash  |
| Extra     |       |       | _C1     | d /      | (89)***   | /         |
| (AB11)    |       |       | (0xC1)  | Mapped   |           | XK_quest  |
|           |       |       |         | to ISO   |           | ion       |
7.1 Cross-Platform Implementation Traps
The data mapped above exposes several severe implementation traps that break input
translation if not explicitly handled:
* The macOS ISO Swap Trap: macOS notoriously intercepts the firmware reports of European
ISO keyboards at the kernel level and forcibly swaps the keycodes for kVK_ANSI_Grave and
kVK_ISO_Section.62 Specifically, if KBGetLayoutType detects kKeyboardISO, the OS reverses
the inputs.63 This firmware-hack necessitates deep un-swapping logic in cross-platform
applications to ensure the physical key beside the Left Shift registers correctly.
The JIS Yen Trap: Japanese JIS keyboards emit different scancodes depending on
hardware/driver interpretation. Windows generally forces the Yen key through standard OEM
VK codes (like VK_OEM_5) depending on the KBDTABLES definitions, blurring the line between
international extensions and generic OEM fallback keys.31
*** The ABNT Identity Crisis Trap: The Brazilian ABNT2 slash key physically maps to KEY_RO in
Linux evdev (0x87 HID, International 1). However, in Windows mapping, it requires explicit
translation paths to VK_ABNT_C1.33 Applications (like game streaming clients) that blindly
normalize this key to the ISO standard VK_OEM_102 completely break the /? input for Brazilian
users.33

8. Implications for an OS-Independent Layout Model
For systems researchers and engineers tasked with designing a unified, JSON- or XML-based
open format capable of defining keyboard layouts flawlessly across Windows, macOS, and
Linux, the analysis of these pipelines dictates several strict architectural requirements. A failure
to address the divergent OS assumptions will result in a model that inevitably fails on
international chassis geometries.
8.1 The Primary Physical Identifier Scheme
An OS-independent layout model must explicitly abandon OS-specific Virtual Keys or Keysyms
as its primary mapping anchor. Because VK_OEM_102 means entirely different things on
different layouts, and X11 keysyms depend entirely on the active XKB mapping algorithm,
neither is stable.
The model must anchor exclusively to USB HID Usage IDs (Page 0x07) or the XKB
Alphanumeric grid (AD01, LSGT) to represent the physical keys.2 USB HID is the only global
standard that points to an immutable physical switch on a printed circuit board.3
The schema should utilize the 16-bit integers corresponding to HID Usage IDs as the primary
dictionary keys (e.g., "0x0014": {... } for the AD01 position). When parsing this model into an
OS-specific format, the compiler will translate 0x0014 into the appropriate scancode, kVK, or
evdev integer required by the target platform.
8.2 Abstracting Modifiers and Shift Levels
The layout format must not rely on the OS's native modifier implementation. Simulating
Windows' 16-bit shift masks or XKB's procedural type evaluation within an agnostic file format
is excessively complex and brittle. Instead, the model should adopt a flat matrix of explicit,
zero-indexed "Shift Levels" directly tied to specific combinatory states.
● Level 1: Base (No modifiers)
● Level 2: Shift
● Level 3: AltGr / Option / Right-Alt
● Level 4: Shift + AltGr
● Level 5: Extended multilingual layer (if applicable)
The AltGr Directive: The model must abstract AltGr purely as a Level 3 selector and explicitly
ignore the fake Left Control injection manufactured by Windows (KLLF_ALTGR flag). The
OS-independent format should only map physical outputs. If a downstream parser translates
the OS-independent model into a Windows .klc equivalent or C-struct, that parser itself must
synthesize the fake Left Control requirements to satisfy Windows internals, completely
shielding the specification author from this legacy quirk.6
8.3 Handling the Physical Geometry Traps (ISO/JIS/ABNT)
A universal format cannot assume a 104-key ANSI baseline. It must explicitly declare the
physical geometry it models to ensure parsers generate the correct artifacts.
● The macOS ISO Swap: A portable format compiling down to macOS .keylayout XMLs or

handling Raw Input on macOS must be aware of Apple's kVK_ISO_Section and
kVK_ANSI_Grave swap.63 If the portable model maps 0x35 (HID Grave) to a backtick, the
macOS parser must output this onto 0x0A (Section) if an ISO physical keyboard flag is
detected.64
● The ABNT Isolation: The model must explicitly define the mapping for HID 0x87
(International 1). Applications blindly mapping European ISO logic will misidentify the
ABNT2 slash key, breaking the input.33 The model must allow assigning a unique
codepoint list to HID 0x87 independently of the ISO <LSGT> mapping.
● JIS IME Keys: The model must provide explicit configuration dictionaries for the 5
dedicated JIS keys (Muhenkan, Henkan, Katakana/Hiragana, Ro, and Yen) without
conflating them with generic OEM fallbacks, as their HID usage IDs (0x8A, 0x8B, etc.) are
globally unique.41
8.4 Modeling Dead Keys State Machines
Because the Windows ToUnicodeEx function is destructive to thread state 60 and the macOS
UCKeyTranslate function is an opaque black box 55, an OS-independent layout cannot rely on
the operating system to handle composition sequences cleanly if the application monitors
input globally (such as in a remote desktop protocol, a game engine, or a virtualization client).
An open layout format must explicitly map dead key logic as deterministic trees or dictionaries
attached directly to the key definition.
For example, a key pressed at Level 3 does not map to a string; it maps to a state identifier (e.g.,
dead_tilde). The layout model then defines a standalone dictionary evaluating the sequence:
{"dead_tilde": {"a": "ã", "n": "ñ", "default": "~"}}. This explicitly instructs cross-platform software to
capture the keystrokes, suppress the OS-level character injection, and resolve the composition
purely in user-space. This guarantees identical dead key behavior across Windows, macOS,
and Linux regardless of backend bugs or destructive API calls.
9. Conclusion
The journey of a keystroke from a physical mechanical switch to a rendered character is
fraught with decades of legacy code, hardware protocols patched with software workarounds,
and undocumented operating system behaviors. By understanding the PS/2 architectural
remnants lingering in the Windows kernel, the Carbon-era Virtual Key swaps hardcoded into
macOS, and the rigorous mapping of evdev to XKB in Linux, systems engineers can bypass
superficial application layers.
An open, OS-independent keyboard layout model is entirely feasible. However, its success
relies entirely on strictly anchoring to physical USB HID Usage IDs, abstracting modifier states
into standardized, flat shift levels, explicitly tracking dead-key state machines in user-space,
and defensively guarding against international geometry traps like the ABNT2 Ro key and the
macOS ISO swap. By modeling the physical hardware rather than the OS abstraction, true
portability can be achieved.
Sources des citations

1. Keyboard Scan Code Specification, consulté le juin 7, 2026,
https://si.blaisepascal.fr/wp-content/uploads/2024/06/scancode.pdf
2. HID Usage Tables - USB-IF, consulté le juin 7, 2026,
https://www.usb.org/sites/default/files/hut1_5.pdf
3. Hid Keyboard Device, consulté le juin 7, 2026,
https://e.huawei.com/topic/2024-demo-cn-jiangxi-liwen-expressway/index.html?
html5=always&type=html&pano=/\/cdn.wsscript.com/huawei/topic/hid-keyboard-
device.txt
4. MacOSX-SDKs/MacOSX10.6.sdk/System/Library/Frameworks/Carbon.framework/
Versions/A/Frameworks/HIToolbox.framework/Versions/A/Headers/Events.h at
master · phracker/MacOSX-SDKs · GitHub, consulté le juin 7, 2026,
https://github.com/phracker/MacOSX-SDKs/blob/master/MacOSX10.6.sdk/System
/Library/Frameworks/Carbon.framework/Versions/A/Frameworks/HIToolbox.fram
ework/Versions/A/Headers/Events.h
5. Why do evdev keycodes and X11 keycodes differ by 8? - Unix & Linux Stack
Exchange, consulté le juin 7, 2026,
https://unix.stackexchange.com/questions/537982/why-do-evdev-keycodes-and-
x11-keycodes-differ-by-8
6. UI::KeyboardLayout - Module for designing keyboard layouts ..., consulté le juin 7,
2026, https://metacpan.org/pod/UI::KeyboardLayout
7. Virtual-Key Codes (Winuser.h) - Win32 apps | Microsoft Learn, consulté le juin 7,
2026,
https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
8. libxkbcommon/include/xkbcommon/xkbcommon-keysyms.h at master - GitHub,
consulté le juin 7, 2026,
https://github.com/xkbcommon/libxkbcommon/blob/master/include/xkbcommon/
xkbcommon-keysyms.h
9. Layout independent keys with Linux & X11 - Alex Baines, consulté le juin 7, 2026,
https://abaines.me.uk/updates/linux-x11-keys
10. Keyboard Matrix Scanning and Debouncing - Frog in the Well, consulté le juin 7,
2026,
https://summivox.wordpress.com/2016/06/03/keyboard-matrix-scanning-and-de
bouncing/
11. The Keyboard - Part 2 : The Matrix - Daire Quinlan, consulté le juin 7, 2026,
https://www.dairequinlan.com/2020/12/the-keyboard-part-2-the-matrix/
12. Keyboard Matrix Help - dribin.org, consulté le juin 7, 2026,
https://www.dribin.org/dave/keyboard/one_html/
13. How a Keyboard Matrix Works - QMK Firmware, consulté le juin 7, 2026,
https://docs.qmk.fm/how_a_matrix_works
14. Is there any functional difference between a matrix with a diode per switch and a
matrix with only one diode per run of switches? : r/AskElectronics - Reddit,
consulté le juin 7, 2026,
https://www.reddit.com/r/AskElectronics/comments/hcx313/is_there_any_function
al_difference_between_a/
15. Developing Keyboard and Mouse HID Client Drivers - Windows drivers | Microsoft

Learn, consulté le juin 7, 2026,
https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/keyboard-and-
mouse-hid-client-drivers
16. linux/include/uapi/linux/input-event-codes.h at master · torvalds/linux - GitHub,
consulté le juin 7, 2026,
https://github.com/torvalds/linux/blob/master/include/uapi/linux/input-event-code
s.h
17. Key Code Mappings | SharpHook, consulté le juin 7, 2026,
https://sharphook.tolik.io/articles/keycodes.html
18. macos - Where can I find a list of Mac virtual key codes? - Stack Overflow,
consulté le juin 7, 2026,
https://stackoverflow.com/questions/3202629/where-can-i-find-a-list-of-mac-vir
tual-key-codes
19. xkbcommon.h File Reference, consulté le juin 7, 2026,
https://xkbcommon.org/doc/current/xkbcommon_8h.html
20. UCKeyTranslate - Apple Developer, consulté le juin 7, 2026,
https://developer.apple.com/documentation/coreservices/1390584-uckeytranslat
e
21. The XKB keymap text format, V1 and V2 - xkbcommon, consulté le juin 7, 2026,
https://xkbcommon.org/doc/current/keymap-text-format-v1-v2.html
22. Arrow keys - Grokipedia, consulté le juin 7, 2026,
https://grokipedia.com/page/Arrow_keys
23. keyCode | Apple Developer Documentation, consulté le juin 7, 2026,
https://developer.apple.com/documentation/uikit/uikey/keycode?language=objc
24. Keyboard/Keypad Page (0x07) - GitHub Gist, consulté le juin 7, 2026,
https://gist.github.com/mildsunrise/4e231346e2078f440969cdefb6d4caa3
25. ISO version §/± key in VIA : r/Keychron - Reddit, consulté le juin 7, 2026,
https://www.reddit.com/r/Keychron/comments/1gi8xdh/iso_version_key_in_via/
26. Do the FILCOs support PS/2 scan code set 3? - Geekhack, consulté le juin 7, 2026,
https://geekhack.org/index.php?topic=6458.0
27. Windows Platform Design Notes - Christopher Vickery, consulté le juin 7, 2026,
https://christophervickery.com/babbage/courses/cs345/ms_scancodes.pdf
28. GitHub - alex/what-happens-when: An attempt to answer the age old interview
question "What happens when you type google.com into your browser and press
enter?", consulté le juin 7, 2026, https://github.com/alex/what-happens-when
29. Windows Virtual Key Codes | IndieGameDev, consulté le juin 7, 2026,
https://indiegamedev.net/2020/02/08/windows-virtual-key-codes-and-how-to-u
se-them/
30. Knowing the layout doesn't mean knowing how to lay it out.... - Miloush.net,
consulté le juin 7, 2026,
http://archives.miloush.net/michkap/archive/2011/03/24/10145161.html
31. Windows-driver-samples/input/layout/fe_kbds/jpn/106/kbd106.c at main -
GitHub, consulté le juin 7, 2026,
https://github.com/microsoft/Windows-driver-samples/blob/main/input/layout/fe_
kbds/jpn/106/kbd106.c

32. What is the C++ key scan code for the "Windows" button? - Stack Overflow,
consulté le juin 7, 2026,
https://stackoverflow.com/questions/28964684/what-is-the-c-key-scan-code-for
-the-windows-button
33. The "?" "/" key from ABNT2 (Brazilian Portuguese) Keyboard is never sent from
client to host (Unhandled button event: 135) · Issue #1789 - GitHub, consulté le
juin 7, 2026, https://github.com/moonlight-stream/moonlight-qt/issues/1789
34. List of Virtual Key Codes - KbdEdit, consulté le juin 7, 2026,
http://www.kbdedit.com/manual/low_level_vk_list.html
35. IOHIDSystem | Apple Developer Documentation, consulté le juin 7, 2026,
https://developer.apple.com/documentation/kernel/iohidsystem/
36. macos - OSX Leopard keyboard input API other than cocoa - Stack, consulté le
juin 7, 2026,
https://stackoverflow.com/questions/3849644/osx-leopard-keyboard-input-api-o
ther-than-cocoa
37. Introduction to XKB - xkbcommon, consulté le juin 7, 2026,
https://xkbcommon.org/doc/current/xkb-intro.html
38. macos - < and ^ keys are swapped - Ask Different - Apple StackExchange,
consulté le juin 7, 2026,
https://apple.stackexchange.com/questions/239395/and-keys-are-swapped
39. Keycodes file problem? - SheepShaver - E-Maculation, consulté le juin 7, 2026,
https://www.emaculation.com/forum/viewtopic.php?t=11316
40. FAQ Keymap · tmk/tmk_keyboard Wiki - GitHub, consulté le juin 7, 2026,
https://github.com/tmk/tmk_keyboard/wiki/FAQ-Keymap
41. Keyboard scancodes: Japanese keyboards, consulté le juin 7, 2026,
https://aeb.win.tue.nl/linux/kbd/scancodes-8.html
42. Citrix Workspace™ app for Linux, consulté le juin 7, 2026,
https://docs.citrix.com/en-us/citrix-workspace-app-for-linux/downloads/citrix-wo
rkspace-app-for-linux-2508-10.pdf
43. Mac Keyboards for UK AGAIN Locales etc - Raspberry Pi Forums, consulté le juin
7, 2026, https://forums.raspberrypi.com/viewtopic.php?t=312618
44. Xorg/Keyboard configuration - ArchWiki, consulté le juin 7, 2026,
https://wiki.archlinux.org/title/Xorg/Keyboard_configuration
45. Hello & XKB / Newbie Corner / Arch Linux Forums, consulté le juin 7, 2026,
https://bbs.archlinux.org/viewtopic.php?id=213958
46. Make your own custom keyboard layout for Linux - Ubuntu MATE Community,
consulté le juin 7, 2026,
https://ubuntu-mate.community/t/make-your-own-custom-keyboard-layout-for-l
inux/19733
47. Custom keyboard layout with xkb and ibus (the poor man's QMK) - The web site
of Vas, consulté le juin 7, 2026,
https://vas.neocities.org/custom_keyboard_layout_xkb_ibus
48. Make CapsLock+A print Ä, et. al. : `/usr/share/X11/xkb/symbols/us` - GitHub Gist,
consulté le juin 7, 2026,
https://gist.github.com/lalten/1341c08d8acc9f9eda9d53667133ad0b

49. What are the exact steps towards remapping the Japanese keys on a Japanese
keyboard in xkb? - Ask Ubuntu, consulté le juin 7, 2026,
https://askubuntu.com/questions/1077870/what-are-the-exact-steps-towards-re
mapping-the-japanese-keys-on-a-japanese-keybo
50. keyboard layout - How to map LSGT to left control with xkb? - Unix & Linux Stack
Exchange, consulté le juin 7, 2026,
https://unix.stackexchange.com/questions/563798/how-to-map-lsgt-to-left-cont
rol-with-xkb
51. xkb options overriding special keyboard layout - Ask Ubuntu, consulté le juin 7,
2026,
https://askubuntu.com/questions/1385832/xkb-options-overriding-special-keyboa
rd-layout
52. XKB layout, remaping key LSGT is disabling the less key - Super User, consulté le
juin 7, 2026,
https://superuser.com/questions/1764521/xkb-layout-remaping-key-lsgt-is-disabli
ng-the-less-key
53. Modifying keyboard layout in ubuntu 20 - xkb, consulté le juin 7, 2026,
https://askubuntu.com/questions/1258066/modifying-keyboard-layout-in-ubuntu
-20
54. UCKeyTranslate | Apple Developer Documentation, consulté le juin 7, 2026,
https://developer.apple.com/documentation/coreservices/1390584-uckeytranslat
e?language=objc
55. How to capture Unicode from key events without an NSTextView - Stack
Overflow, consulté le juin 7, 2026,
https://stackoverflow.com/questions/22566665/how-to-capture-unicode-from-k
ey-events-without-an-nstextview
56. macOS Chinese IME certain control keys are directly displayed by kitty #4062 -
GitHub, consulté le juin 7, 2026, https://github.com/kovidgoyal/kitty/issues/4062
57. Difference between WH_KEYBOARD and WH_KEYBOARD_LL? - Stack Overflow,
consulté le juin 7, 2026,
https://stackoverflow.com/questions/10718009/difference-between-wh-keyboar
d-and-wh-keyboard-ll
58. [SOLVED] Win API question: AttachThreadI - C++ Forum - cplusplus .com,
consulté le juin 7, 2026, https://cplusplus.com/forum/windows/5210/
59. The switch of keyboard layout on Windows: synchronization with the
multistage-processing of character input - Stack Overflow, consulté le juin 7,
2026,
https://stackoverflow.com/questions/78171026/the-switch-of-keyboard-layout-o
n-windows-synchronization-with-the-multistage-pr
60. terminal/src/terminal/input/terminalInput.cpp at main - GitHub, consulté le juin 7,
2026,
https://github.com/microsoft/terminal/blob/master/src/terminal/input/terminalInpu
t.cpp
61. Compose and dead-keys support in libxkbcommon, consulté le juin 7, 2026,
https://wayland-devel.freedesktop.narkive.com/N3rwOVoT/compose-and-dead-k

eys-support-in-libxkbcommon
62. ui/events/keycodes/keyboard_code_conversion_mac.mm - chromium/src - Git at
Google, consulté le juin 7, 2026,
https://chromium.googlesource.com/chromium/src/+/lkgr/ui/events/keycodes/key
board_code_conversion_mac.mm
63. ISO Keyboards: Backslash and IntlBackslash "swapped" · Issue #24153 ·
microsoft/vscode, consulté le juin 7, 2026,
https://github.com/microsoft/vscode/issues/24153
64. MacOSX-SDKs/MacOSX10.6.sdk/System/Library/Frameworks/Carbon.framework/
Versions/A/Frameworks/HIToolbox.framework/Versions/A/Headers/Keyboards.h
at master · phracker/MacOSX-SDKs · GitHub, consulté le juin 7, 2026,
https://github.com/phracker/MacOSX-SDKs/blob/master/MacOSX10.6.sdk/System
/Library/Frameworks/Carbon.framework/Versions/A/Frameworks/HIToolbox.fram
ework/Versions/A/Headers/Keyboards.h
65. USB HID Keyboard scan codes - GitHub Gist, consulté le juin 7, 2026,
https://gist.github.com/MightyPork/6da26e382a7ad91b5496ee55fdc73db2