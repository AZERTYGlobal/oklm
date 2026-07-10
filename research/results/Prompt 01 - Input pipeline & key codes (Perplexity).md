# From Switch to Character: A Complete Technical Reference for Keyboard Input Pipelines and OS-Independent Layout Modeling
---
## Executive Summary
A single key press traverses at least seven distinct code-translation stages before a Unicode character appears in an application. Each stage uses a different identifier scheme, and no two major operating systems share the same scheme end-to-end. This report dissects every stage, catalogues every code system, cross-references ten representative keys across Windows, macOS, and Linux/X11, and derives the implications for engineers building a portable, OS-independent keyboard layout model.

Primary sources cited throughout: USB HID Usage Tables v1.21 (USB-IF, 2023), Microsoft Win32 documentation, Apple `CGKeyCode` / `UCKeyTranslate` documentation, Linux kernel `input-event-codes.h`, Arch Wiki Keyboard Input, libxkbcommon documentation, and ISO/IEC 9995-1.[^1][^2][^3][^4][^5][^6][^7][^8][^9][^10][^11][^12]

***
## 1. The Full Input Pipeline: Stage by Stage
The diagram below represents the logical flow from mechanical actuation to application-visible character. Each stage is described in detail after the diagram.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  HARDWARE / FIRMWARE (inside the keyboard device)                              │
│                                                                                 │
│  (1)  Key switch actuates                                                        │
│        │  Physical contact closure (mechanical, optical, capacitive, etc.)     │
│        ▼                                                                        │
│  (2)  Matrix scan                                                                │
│        │  MCU detects row/column intersection; debounce applied                │
│        ▼                                                                        │
│  (3)  Firmware key event                                                         │
│        │  Maps matrix position → internal keycode (firmware-defined)           │
│        │  Applies layers, macros, tap-hold logic (e.g., QMK)                   │
│        ▼                                                                        │
│  (4)  USB HID Report (Keyboard/Keypad Page 0x07 Usage IDs)                      │
│        │  8-byte Boot Report: [Modifier byte][Reserved][Keycode × 6]           │
│        │  Modifier keys: Usage IDs 0xE0–0xE7 (Dynamic Flags)                  │
│        │  Regular keys: Usage IDs 0x04–0xDD (Selectors)                        │
└────────────────────────────┬────────────────────────────────────────────────────┘
                             │  USB interrupt transfer (~1 ms polling or HID interrupt)
                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  OS KERNEL / DRIVER                                                             │
│                                                                                 │
│  (5)  HID driver receives USB report                                             │
│        │  Windows: hidclass.sys + kbdhid.sys → WDM keyboard stack              │
│        │  macOS:   IOHIDFamily kext / DriverKit → IOHIDSystem                  │
│        │  Linux:   usbhid.ko → input subsystem → /dev/input/eventN             │
│        ▼                                                                        │
│  (6)  HID Usage ID → OS-native keycode                                          │
│        │  Windows: Usage ID → PS/2-compatible scancode (Set 1)                 │
│        │           → Virtual Key code (via kbd*.dll layout driver)             │
│        │  macOS:   Usage ID → CGKeyCode (virtual key, hardware-position-based) │
│        │  Linux:   Usage ID → evdev keycode (KEY_* from input-event-codes.h)   │
│        ▼                                                                        │
│  (7)  Layout mapping: keycode + modifier state → character/action               │
│        │  Windows: VK + shift state → WM_CHAR via ToUnicodeEx()/kbd*.dll       │
│        │  macOS:   CGKeyCode → UCKeyTranslate() → UniChar (dead-key state)     │
│        │  Linux/X11: evdev keycode + 8 → X11 keycode → XKB keysym             │
│        │  Wayland:  evdev keycode + 8 → xkbcommon keysym → UTF-8              │
└────────────────────────────┬────────────────────────────────────────────────────┘
                             │  Window system message / event
                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  APPLICATION                                                                    │
│  Receives: WM_KEYDOWN + WM_CHAR (Windows)                                      │
│            NSEvent / CGEvent (macOS)                                            │
│            KeyPress XEvent / wl_keyboard.key (Linux)                           │
│  → Unicode codepoint or control action                                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```
### Stage 1 – Physical Switch Actuation
A key switch is a binary sensor. When a mechanical switch closes (or an optical beam breaks, or a capacitive plate threshold is crossed), it pulls a row or column line in a resistive matrix to a known logic level. No code is generated yet; only a voltage level changes.
### Stage 2 – Matrix Scan and Debounce
The keyboard microcontroller (MCU) continuously cycles through rows, driving each row low and reading all column lines. When a coincident row/column is detected, the firmware registers a key event. Because switch contacts bounce (multiple rapid open/close cycles), the firmware applies a debounce algorithm (typically 5–10 ms timing filter or a counter-based approach). The output of this stage is a `(row, column)` coordinate — a raw *matrix position* that has no standardized meaning outside this specific keyboard's firmware.[^13][^14]
### Stage 3 – Firmware Internal Keycode and Layer Mapping
The firmware maps the `(row, column)` pair to an internal keycode via a compile-time keymap table. In open-source firmware such as QMK, this table is called the *keymap*, organized in layers. Layers allow one physical key to produce different USB usage IDs depending on which layer is active (activated via layer-switch keys, tap-hold, etc.). The firmware can also synthesize multi-key macro sequences from a single physical key press.[^15]
### Stage 4 – USB HID Report
The firmware encodes pressed key state into a USB HID Input Report using Usage IDs from the *Keyboard/Keypad* usage page (0x07). The standard Boot Protocol keyboard report is 8 bytes:[^2][^16][^17][^11]

```
Byte 0: Modifier bitmask (bits: RightGUI, RightAlt, RightShift, RightCtrl,
                                LeftGUI, LeftAlt, LeftShift, LeftCtrl)
Byte 1: Reserved (0x00)
Bytes 2–7: Up to 6 simultaneously pressed key Usage IDs
```

Modifier keys (LeftCtrl through RightGUI) have their own Usage IDs in the range 0xE0–0xE7 and are also separately reported in the modifier bitmask. The host OS polls the keyboard (Full Speed USB: up to 1 ms interval; HID interrupt endpoint).

**⚠ Key design principle of HID Usage IDs**: Usage IDs identify *key positions*, not characters. The HID specification explicitly states: "Rather than changing the keyboard firmware to put the Z Usage into that place in the descriptor list, the vendor should use the Y Usage on both the North American and German keyboards." A German keyboard's "Z" key (physically where "Y" is on ANSI) reports Usage ID `0x1C` (the "Keyboard y and Y" usage), not a "Z" usage. Character assignment is the host OS's responsibility.[^2]
### Stage 5 – OS HID Driver
**Windows**: `hidclass.sys` and `kbdhid.sys` receive the HID report. `kbdhid.sys` translates HID Usage IDs into PS/2-compatible scan codes (Set 1 format) for backward compatibility with the existing keyboard driver stack. These synthetic scan codes then travel up the `kbdclass.sys` driver stack.[^6]

**macOS**: `IOHIDFamily` (kernel extension) or its DriverKit successor processes the HID report. The IOHIDSystem framework creates `IOHIDEvent` objects which travel up to `CGEventTap`-accessible events. The macOS pipeline exposes three levels to userspace: IOKit (hardware), CGEvent (Quartz), and NSEvent (AppKit/Cocoa).[^18][^19]

**Linux**: `usbhid.ko` maps HID Usage IDs to evdev `KEY_*` codes (defined in `linux/input-event-codes.h`) and emits `input_event` structures via the kernel input subsystem. These appear as `EV_KEY` events on `/dev/input/eventN` devices.[^20][^8]
### Stage 6 – Keycode Generation (OS-Native Codes)
This is the stage where the three OSes diverge completely:

- **Windows** generates a *scan code* (Set 1 / "virtual scan code", VSC). The scan code is a position-based identifier rooted in the original IBM PC XT keyboard. Extended keys are prefixed with `0xE0`. The `kbdhid.sys` driver constructs these from a fixed HID-to-scancode mapping table.[^6][^21]
- **macOS** generates a `CGKeyCode` (also called a *virtual key code*). These are defined in `<HIToolbox/Events.h>` as `kVK_*` constants and are position-based relative to a reference ANSI US layout.[^4][^22]
- **Linux** generates an *evdev keycode* (`KEY_*`), a small integer defined in `input-event-codes.h`. These are also position-based.[^3][^8]
### Stage 7 – Layout Mapping: Keycode → Character
This is where locale and user layout configuration is applied:

**Windows**: The keyboard layout DLL (`kbd*.dll`, e.g., `KBDUS.DLL`, `KBDFR.DLL`) is selected by the active input language. The DLL's `KbdLayerDescriptor()` function returns a `KBDTABLES` structure that contains: (a) a VSC-to-VK table (`pusVSCtoVK`), (b) a VK-to-WChar table (`pVkToWcharTable`) indexed by shift state (modifier combination), and (c) a dead-key composition table (`pDeadKey`). `ToUnicodeEx()` is the API that applications call to perform the final VK + shift state → Unicode translation.[^23][^24]

**macOS**: The active keyboard input source (set in System Settings → Keyboard → Input Sources) provides a `UCKeyboardLayout` data structure accessible via `TISGetInputSourceProperty(source, kTISPropertyUnicodeKeyLayoutData)`. The `UCKeyTranslate()` function maps a `CGKeyCode` plus modifier state to a Unicode character, maintaining a `deadKeyState` between calls for dead key composition.[^12][^25]

**Linux / X11**: The X server maps evdev keycodes (adding an offset of +8) to X11 keycodes, then uses the XKB keymap to translate X11 keycode + modifier state to a *keysym*. The XKB keymap is loaded via the RMLVO system (Rules, Model, Layout, Variant, Options) which compiles into the internal KcCGST representation. `xkb_state_key_get_syms()` (libxkbcommon) and `XLookupKeysym()` / `Xutf8LookupString()` (Xlib) perform the final translation.[^3][^26][^27][^5][^7][^28]

**Linux / Wayland**: The compositor sends the XKB keymap to clients via the `wl_keyboard.keymap` event. Clients use libxkbcommon directly with the keymap to translate evdev keycodes (adding +8 for XKB compatibility) into keysyms and Unicode.[^29][^30]

**Layout logic ownership**: On Windows, layout logic lives in `kbd*.dll`, loaded per input language. On macOS, layout logic lives in the `UCKeyboardLayout` structure of the active input source. On Linux/X11/Wayland, layout logic lives in the XKB keymap, typically compiled from xkeyboard-config data files in `/usr/share/X11/xkb/`.[^28]

***
## 2. Key Code Systems: Precise Definitions and Relationships
### 2.1 USB HID Usage IDs (Keyboard/Keypad Page 0x07)
Defined in the USB HID Usage Tables document (current version: v1.21, 2023). Each key position is assigned a Usage ID, a 16-bit unsigned integer. On usage page 0x07:[^11]

- Usage IDs 0x00–0x03: Reserved / error codes
- Usage IDs 0x04–0xDD: Key selectors (type: Sel)
- Usage IDs 0xE0–0xE7: Modifier keys (type: DV — Dynamic Variable)

Representative values:[^2]
| Usage ID (hex) | Name |
|---|---|
| 0x04 | Keyboard a and A |
| 0x14 | Keyboard q and Q |
| 0x29 | Keyboard Escape |
| 0x2C | Keyboard Spacebar |
| 0x28 | Keyboard Return (ENTER) |
| 0x39 | Keyboard Caps Lock |
| 0x35 | Keyboard Grave Accent and Tilde |
| 0x64 | Keyboard Non-US `\` and `|` (ISO extra key, LSGT) |
| 0xE0 | Keyboard LeftControl |
| 0xE4 | Keyboard RightControl |
| 0xE6 | Keyboard RightAlt (AltGr) |

The naming "Keyboard a and A" intentionally lists both cases without specifying which is "default" — that determination is the OS's responsibility.[^2]
### 2.2 PS/2 Scan Code Sets
Three scan code sets exist, all originating from IBM hardware:[^31][^32]

**Set 1 ("XT scancodes")**: The original IBM PC/XT keyboard protocol. For a key press (make), the scan code is a single byte `c`; for a release (break), the code is `c + 0x80`. Extended keys use an `0xE0` prefix. Set 1 is what Windows and Linux present to legacy software internally — even on modern USB keyboards, `kbdhid.sys` (Windows) and the kernel (Linux raw mode) maintain Set 1 semantics.[^32][^31]

**Set 2 ("AT scancodes")**: The IBM PC AT and PS/2 interface default. All modern PS/2 keyboards transmit Set 2 over the wire. Break codes are indicated by an `0xF0` prefix rather than setting bit 7. The keyboard controller (originally Intel 8042) translates Set 2 to Set 1 for OS backward compatibility.[^33][^31]

**Set 3**: Introduced with IBM 3270 PC terminals. More regular coding but rarely used. Linux activates Set 3 on keyboards that fully support it. Break codes also use `0xF0` prefix, but by default most keys do not generate break codes in Set 3 unless explicitly enabled.[^33][^31]

**The term "scancode"** in modern software typically refers to the *Set 1 / XT scan code value* exposed by the OS, not the electrical signal sent over the PS/2 wire. On USB keyboards, there is no physical scan code; the OS driver synthesizes a "virtual scan code" (VSC) from the HID Usage ID for compatibility.[^6][^21]
### 2.3 Windows Virtual Key Codes (VK_*)
Defined in `<winuser.h>` (current documentation: Microsoft Learn, updated October 2025). VK codes are device-independent, OS-defined integers (UINT, 8 bits significant) that identify the logical function of a key:[^1]

- `VK_ESCAPE` = 0x1B, `VK_SPACE` = 0x20, `VK_RETURN` = 0x0D
- `VK_Q` = 0x51 (letter keys use ASCII values of the uppercase letter)
- `VK_OEM_*` codes (0xBA–0xE2) identify locale-specific punctuation keys by their typical QWERTY US position
- `VK_OEM_102` = 0xE2 identifies the ISO extra key (between Left Shift and Z on ISO keyboards)
- `VK_ABNT_C1` = 0xC1 and `VK_ABNT_C2` = 0xC2 identify the ABNT/ABNT2 Brazilian extra keys[^34][^35]

The scan-code-to-VK mapping is performed by the active keyboard layout DLL. The `pusVSCtoVK` array in `KBDTABLES` is indexed by scan code and yields a VK code. For French AZERTY, scan code 0x10 maps to `VK_A` (because the "A" key on AZERTY is where "Q" is on QWERTY). A modifier state then determines whether the result is `a`, `A`, `à`, `@`, etc., via the `pVkToWcharTable`.[^24]

**Important limitation**: `VK_SHIFT` (0x10), `VK_CONTROL` (0x11), `VK_MENU` (0x12) do not distinguish left from right. The left/right distinction requires using `VK_LSHIFT`/`VK_RSHIFT` etc., or inspecting the extended-key bit in the scan code.[^36]
### 2.4 macOS Virtual Key Codes (CGKeyCode / kVK_*)
Defined in `<HIToolbox/Events.h>` (Carbon framework, still present as of macOS 15 Sequoia). The constants are `kVK_ANSI_*` and `kVK_*`:[^37][^4][^22]

- `kVK_ANSI_Q` = 0x0C
- `kVK_ANSI_A` = 0x00
- `kVK_Space` = 0x31
- `kVK_Return` = 0x24
- `kVK_CapsLock` = 0x39
- `kVK_ANSI_Grave` = 0x32 (backtick/tilde key)

The prefix `ANSI_` in constant names signals that the key is labeled according to an ANSI US reference keyboard. The header comment states: "Those constants with 'ANSI' in the name are labeled according to the key position on an ANSI-standard US keyboard. For example, `kVK_ANSI_A` indicates the virtual keycode for the key with the letter 'A' in the US keyboard layout. Other keyboard layouts may have the 'A' key label on a different physical key; in this case, pressing 'A' will generate a different virtual keycode."[^22]

This means `CGKeyCode` is *position-based* — it reflects the physical key location relative to an ANSI-US reference, not the character produced. The macOS system does not translate HID Usage IDs to characters; `UCKeyTranslate()` with the active `UCKeyboardLayout` performs the final layout mapping.[^12][^25]
### 2.5 Linux: evdev Keycodes, Kernel Keycodes, X11 Keycodes, and Keysyms
Linux operates with three distinct "keycode" namespaces plus a keysym layer:[^3][^27]

**evdev keycode** (`KEY_*`): Defined in `/usr/include/linux/input-event-codes.h` (kernel source). These are small integers emitted in `input_event.code` for `EV_KEY` events on `/dev/input/eventN`. Examples: `KEY_A` = 30, `KEY_Q` = 16, `KEY_SPACE` = 57, `KEY_ENTER` = 28, `KEY_CAPSLOCK` = 58, `KEY_GRAVE` = 41. The HID driver maps HID Usage IDs to these values; the mapping is largely one-to-one for standard keys.[^21][^20][^8]

**Kernel keycode**: The term sometimes used for the internal kernel-to-scancode mapping used in virtual console mode. The `showkey --keycodes` utility reveals these. For USB keyboards, the kernel directly uses evdev codes.[^3]

**X11 keycode**: The X server adds an offset of 8 to the evdev keycode. So evdev `KEY_A` = 30 becomes X11 keycode 38; evdev `KEY_ESCAPE` = 1 becomes X11 keycode 9. The offset exists for historical reasons: the X11 protocol originally used Set 1 scan codes as keycodes, where byte 0 and byte 1 were reserved and scan codes started at 8. The xkbcli toolchain accepts `--without-x11-offset` to suppress this offset for non-X11 consumers.[^38][^39][^40][^30]

X11 keycodes are 8-bit values (range 8–255). This hard limit causes issues with keyboards that emit evdev keycodes above 247 (after adding 8 the result exceeds 255).[^40][^41]

**X11/XKB keysym** (`xkb_keysym_t`): A 32-bit integer representing a *symbol* or *action* rather than a physical key position. The XKB keymap maps (keycode, group, level) → keysym. Level is determined by the active modifiers. Well-known keysyms: `XKB_KEY_q` = 0x0071, `XKB_KEY_Q` = 0x0051, `XKB_KEY_Return` = 0xFF0D, `XKB_KEY_space` = 0x0020, `XKB_KEY_dead_grave` = 0xFE60. The libxkbcommon library (current version: 1.8.1, March 2025) provides `xkb_keysym_to_utf32()` and `xkb_keysym_to_utf8()` for keysym → Unicode conversion.[^5][^42][^43]

**The evdev→X11 keycode translation**: evdev code + 8 = X11 keycode. In Wayland, this same offset applies: the `wl_keyboard.key` event carries the raw evdev scancode, and the application or compositor adds 8 before feeding it to xkbcommon.[^30]

**The scancode→evdev keycode mapping**: Controlled by the udev hwdb (`/etc/udev/hwdb.bin`). For standard USB keyboards, the mapping is the identity function from HID Usage ID to evdev code (USB-HID defines a one-to-one mapping for standard keys).[^27][^3]
### 2.6 The Relationship: Physical Position vs. Logical Key vs. Produced Character
Three orthogonal concepts must be kept distinct:

1. **Physical position**: The row/column coordinate of a switch in the keyboard matrix, or equivalently, the stable geometric location on the keyboard surface. USB HID Usage IDs encode this (with caveats — see Section 5).
2. **Logical key**: The OS-assigned identity after driver processing. VK codes, CGKeyCodes, and evdev `KEY_*` codes are all "logical key" identifiers. They are position-based by design but expressed in OS-specific numbering.
3. **Produced character**: The Unicode codepoint (or control action) resulting from applying a keyboard layout to a logical key given a specific modifier state. This is entirely layout- and locale-dependent.

The critical observation is that "the Q key" on a QWERTY and AZERTY keyboard produces the *same* HID Usage ID (0x14, "Keyboard q and Q"), the *same* evdev keycode (`KEY_Q` = 16), and roughly the *same* Windows VK (0x51 = VK_Q), but produces *different characters* (`q` vs `a`) because the layout mapping differs.[^44][^45]

***
## 3. Modifiers and Levels
### 3.1 Modifier Keys and Their Physical USB Usage IDs
The USB HID spec defines eight modifier keys as Dynamic Variable flags in the modifier byte:[^2][^16]

| Bit | Usage ID | Key |
|-----|---------|-----|
| 0 | 0xE0 | Left Control |
| 1 | 0xE1 | Left Shift |
| 2 | 0xE2 | Left Alt |
| 3 | 0xE3 | Left GUI (Windows/Command/Super) |
| 4 | 0xE4 | Right Control |
| 5 | 0xE5 | Right Shift |
| 6 | 0xE6 | Right Alt (AltGr) |
| 7 | 0xE7 | Right GUI |
### 3.2 Shift Levels and the ISO/XKB Level Model
ISO/IEC 9995-1 defines a *shift level* model for keyboards:[^46][^9][^10]

- **Level 1**: Unshifted (base character)
- **Level 2**: Level 2 Select (traditional Shift key; ISO 9995 deprecates the term "Shift" in favor of "Level 2 Select")
- **Level 3**: Level 3 Select (AltGr / Right Alt on European keyboards). Accessing this level is via a dedicated *Level 3 Shift* key
- **Level 4**: Level 3 + Level 2 (AltGr + Shift)
- **Level 5**: Level 5 Select (rare; accessible via a dedicated Level 5 Shift key)

XKB implements this model directly. The `ISO_Level3_Shift` keysym identifies the AltGr key as a level-3 selector, and `ISO_Level5_Shift` is used for level-5 selectors. The `level3(ralt_switch)` XKB option maps the Right Alt key to `ISO_Level3_Shift`.[^47][^48][^28][^46]

Windows models the same concept differently. A `KBDTABLES.pCharModifiers` structure maps combinations of VK modifier flags (Shift = bit 0, Control = bit 1, Alt = bit 2) to a column index in the `pVkToWcharTable`. AltGr is represented as `KLLF_ALTGR`, and when set, Right Alt is treated as Ctrl+Alt internally. The French AZERTY DLL defines modifier column 3 as Alt+Control (= AltGr), allowing keys like `VK_4` → `{` when AltGr is held.[^24]

macOS does not have an explicit "AltGr" concept. The Option (⌥) key serves a similar role; `UCKeyTranslate()` receives modifier state as a bitmask where `optionKey` is bit 11. The `UCKeyboardLayout` structure in the keyboard resource defines which modifier combinations map to which Unicode characters for each virtual keycode.[^12][^25]
### 3.3 Caps Lock Behavior: OS and Locale Differences
Caps Lock behavior is one of the most variable aspects across locales and OSes:

**Standard behavior (most Latin layouts)**: Caps Lock applies only to alphabetic keys. Pressing A with Caps Lock active yields `A`; pressing `1` still yields `1`. This is *alphabetic-lock* mode.

**Shift Lock behavior (some non-Latin-centric layouts)**: Caps Lock acts as a persistent Shift, affecting all keys including number row. French AZERTY historically uses this model on Windows, where with Caps Lock on, pressing `5` yields `(` (the Shift+5 character) rather than `5`. This is controlled by the `KLLF_SHIFTLOCK` flag in the Windows keyboard layout DLL.[^49][^50][^24]

**Turkish locale**: Turkish has two distinct `i` characters: `i` (dotted) and `ı` (dotless). Caps Lock must map `i` → `İ` (dotted uppercase) and `ı` → `I` (dotless uppercase) — the *opposite* of naive ASCII uppercasing. This is handled by locale-specific uppercasing rules at the layout level.[^51]

**XKB Caps Lock behavior**: libxkbcommon documentation specifies: "If the Caps Lock modifier is active and was not consumed by the translation process, keysyms are transformed to their upper-case form (if applicable)." The XKB `capslock` type definition controls exactly which key types are affected by Caps Lock. libxkbcommon 1.8.1 updated keysym case mappings to Unicode 16.0, including proper handling of title-cased keysyms and the German ß → ẞ mapping.[^5][^43]

**⚠ OS-version-specific behavior**: On Windows 10 and earlier, a registry-accessible UI existed to toggle between "CapsLock toggles" and "Shift cancels CapsLock" modes; this UI was removed in later Windows 10 builds and is now typically only available via OEM software. The underlying registry key (`HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Keyboard Layout\CapsLock`) still functions.[^52]
### 3.4 Mode_switch and XKB Groups
The X11/XKB concept of *groups* (keyboard groups) is distinct from shift levels. A group is essentially an alternate keymap active when a group-switch key is held or toggled. `Mode_switch` is an old X11 mechanism (pre-XKB) that activated group 2. Modern XKB replaces it with group selectors and the `xkb_symbols` group notation. Wayland represents the active group in the `wl_keyboard.modifiers` event's `group` field.[^53][^28][^30]

***
## 4. Dead Keys and Composition
### 4.1 What Are Dead Keys
A dead key is a key that produces no immediate character output but sets a *pending accent state*. The character is produced only when a subsequent base character is pressed. Examples: pressing `^` (circumflex dead key) followed by `e` produces `ê`; on French AZERTY, `^` is a dead key on the same physical key as `¨`.[^54][^55][^24]
### 4.2 Dead Keys on Linux / X11 / XKB
In XKB, dead keys are represented as keysyms with the prefix `dead_*` (e.g., `dead_grave`, `dead_acute`, `dead_circumflex`). The composition engine — historically part of Xlib (`Xutf8LookupString()`) and now provided by libxkbcommon's compose module — uses a *Compose file* (e.g., `/usr/share/X11/locale/en_US.UTF-8/Compose`) that lists valid sequences. The sequence `<dead_acute> <a>` → `á` is defined in this file.[^54][^29]

**Chained dead keys**: Multiple dead keys can be chained. The Compose file can define sequences of arbitrary length, e.g., `<dead_grave> <dead_grave>` producing a standalone grave accent. The libxkbcommon compose module maintains a state machine that processes these sequences.[^55][^54]

**The Compose key** (`Multi_key` in XKB): A dedicated key that initiates a compose sequence. Unlike dead keys (which are layout-defined), the Compose key is typically user-configured via XKB options (e.g., `compose:ralt` maps Right Alt to Compose). Sequences after the Compose key are also resolved from the Compose file.[^47]

**⚠ Sequence failure behavior**: XKB/libxkbcommon behavior on an undefined dead-key sequence (e.g., `<dead_grave> <x>`) historically produced a beep and no output. GTK as of 2021 changed this to instead commit the individual keys. This is an application-layer concern, not an OS-layer one.[^55]
### 4.3 Dead Keys on Windows
Windows dead keys are stored in the `pDeadKey` table within `kbd*.dll`. Each entry in `DEADKEY` contains `dwBoth` (high 16 bits: dead character; low 16 bits: base character), `wchComposed` (result), and flags. When `ToUnicodeEx()` is called for a dead key, it returns -1 and sets an internal dead-key buffer in the thread's keyboard state. The next call to `ToUnicodeEx()` with the base key produces the composed character. If no valid combination exists, `ToUnicodeEx()` produces two characters (the dead key's spacing equivalent + the base key).[^23][^24]

**Ligatures**: Windows additionally supports ligatures via `pLigature` in `KBDTABLES` — a single key press producing multiple Unicode codepoints. Arabic layouts use this for combined glyphs.[^24]
### 4.4 Dead Keys on macOS
macOS dead keys are defined in the `UCKeyboardLayout` resource's `ucKeyStateRecords` and `ucKeyStateTerminators` tables. `UCKeyTranslate()` takes a `deadKeyState` pointer; if a dead key is pressed, it sets `*deadKeyState` to a non-zero value and returns 0 output characters. The next `UCKeyTranslate()` call with `*deadKeyState != 0` performs the lookup. A Space keypress after a dead key typically produces the spacing equivalent of the accent.[^12][^25]

**⚠ macOS dead key visual feedback**: Modern macOS (post-10.9) shows an underlined placeholder character immediately when a dead key is pressed, which is replaced when the composed character is produced. This visual feedback is at the AppKit/InputMethodKit layer; not all applications implement it.[^56]

***
## 5. Physical Geometries and Key Naming
### 5.1 Physical Keyboard Geometries
Four major physical keyboard form factors exist:[^57][^58][^59]

**ANSI (American National Standards Institute)**: 104 keys (full), 87 keys (TKL). The Enter key is a wide horizontal rectangle occupying one row. Left Shift is a single wide key spanning the position of Left Shift only. There is no key between Left Shift and Z. Standard US layout uses ANSI geometry.

**ISO (International Organization for Standardization)**: 105 keys (full), 88 keys (TKL). The Enter key is an inverted-L shape spanning two rows. Left Shift is narrower to accommodate an extra key between Left Shift and Z — this is the *ISO 102nd key* (`<LSGT>` in XKB; HID Usage ID 0x64 "Keyboard Non-US `\` and `|`"; VK_OEM_102 in Windows[^60][^34]). ISO geometry is standard across Europe and much of the world.

**JIS (Japanese Industrial Standards)**: 109 keys (full). Adds keys specific to Japanese input: `変換` (Henkan, convert), `無変換` (Muhenkan, non-convert), `ひらがな/カタカナ` (Hiragana/Katakana toggle), `¥` (Yen sign key), and `|` (pipe key)[^61]. The spacebar is shorter to accommodate these additional keys in the bottom row. HID Usage IDs 0x87–0x8D cover International keys (International1 = JIS `\`/`_` key, International2 = Japanese Katakana/Hiragana, International3 = Japanese Yen, etc.)[^2].

**ABNT / ABNT2 (Brazilian)**: 107 keys (ABNT), 108 keys (ABNT2). Adds `VK_ABNT_C1` (scan code 0x73) — a key between the Right Shift and `/` keys that carries `/` and `?` — and `VK_ABNT_C2` (scan code 0x7E) — a separator key on the numpad.[^34][^35][^62]
### 5.2 Standard Key Naming: XKB / ISO 9995
**XKB key names** are the primary standard for position-based, layout-independent key identification. They follow the convention `<RRNN>` where `RR` is a two-letter row identifier and `NN` is a two-digit column number:[^26][^63]

- **Row E** (top alphanumeric row, digit row): `<AE01>` through `<AE12>` (digits 1–0, `-`, `=`), `<AE00>` for the `\`` key left of `1`
- **Row D** (QWERTY top letter row): `<AD01>` = Q, `<AD02>` = W, … `<AD10>` = P, `<AD11>` = `[`, `<AD12>` = `]`
- **Row C** (QWERTY home row): `<AC01>` = A, `<AC02>` = S, … `<AC10>` = `'`
- **Row B** (QWERTY bottom row): `<AB01>` = Z, … `<AB10>` = `/`
- **Row A** (bottom row): `<SPCE>` = Space, `<LALT>`, `<LCTL>`, etc.
- Special XKB names: `<LSGT>` = ISO extra key (left of Z, right of Left Shift), `<BKSL>` = backslash, `<CAPS>` = Caps Lock, `<RTRN>` = Enter, `<BKSP>` = Backspace[^40][^65][^17]

**ISO 9995-1 key naming** uses a similar grid convention. Row letters (A = Space row, B = bottom letter row, C = home row, D = top letter row, E = number row) and column numbers from left to right. XKB key names are largely derived from this standard.[^46][^9][^10]

The XKB name `<LSGT>` (left of Z, next to left Shift) has no ANSI equivalent, making it a key that requires explicit handling in cross-platform layouts.

***
## 6. Cross-Reference Table: 10 Representative Keys
The following table gives the code values for 10 representative keys. HID Usage IDs from USB HID Usage Tables v1.21; Windows scan codes and VK from Microsoft documentation and kbdlayout.info; macOS virtual keycodes from HIToolbox Events.h; Linux evdev from `input-event-codes.h`; X11 keysym from libxkbcommon / X11 keysym definitions.[^1][^2][^26][^37][^5][^64][^20][^8][^60][^11]

| Key (QWERTY position) | XKB Name | HID Usage ID | Win Scan Code (Set 1) | Win VK | macOS CGKeyCode | evdev KEY_* | evdev code | X11 keycode (evdev+8) | X11 keysym (base/unshifted, US) |
|---|---|---|---|---|---|---|---|---|---|
| Q | `<AD01>` | 0x14 | 0x10 | VK_Q (0x51) | kVK_ANSI_Q (0x0C) | KEY_Q | 16 | 24 | XKB_KEY_q (0x0071) |
| Backtick/Tilde (left of 1) | `<TLDE>` | 0x35 | 0x29 | VK_OEM_3 (0xC0) | kVK_ANSI_Grave (0x32) | KEY_GRAVE | 41 | 49 | XKB_KEY_grave (0x0060) |
| ISO extra key (right of Left Shift) | `<LSGT>` | 0x64 | 0x56 | VK_OEM_102 (0xE2) | *no standard kVK* | KEY_102ND | 86 | 94 | XKB_KEY_less (0x003C) |
| Space | `<SPCE>` | 0x2C | 0x39 | VK_SPACE (0x20) | kVK_Space (0x31) | KEY_SPACE | 57 | 65 | XKB_KEY_space (0x0020) |
| Enter (main) | `<RTRN>` | 0x28 | 0x1C | VK_RETURN (0x0D) | kVK_Return (0x24) | KEY_ENTER | 28 | 36 | XKB_KEY_Return (0xFF0D) |
| Caps Lock | `<CAPS>` | 0x39 | 0x3A | VK_CAPITAL (0x14) | kVK_CapsLock (0x39) | KEY_CAPSLOCK | 58 | 66 | XKB_KEY_Caps_Lock (0xFF20) |
| Left Shift | `<LFSH>` | 0xE1 | 0x2A | VK_LSHIFT (0xA0) | kVK_Shift (0x38) | KEY_LEFTSHIFT | 42 | 50 | XKB_KEY_Shift_L (0xFFE1) |
| Left Alt | `<LALT>` | 0xE2 | 0x38 | VK_LMENU (0xA4) | kVK_Option (0x3A) | KEY_LEFTALT | 56 | 64 | XKB_KEY_Alt_L (0xFFE9) |
| Escape | `<ESC>` | 0x29 | 0x01 | VK_ESCAPE (0x1B) | kVK_Escape (0x35) | KEY_ESC | 1 | 9 | XKB_KEY_Escape (0xFF1B) |
| A | `<AC01>` | 0x04 | 0x1E | VK_A (0x41) | kVK_ANSI_A (0x00) | KEY_A | 30 | 38 | XKB_KEY_a (0x0061) |

**Notes on the ISO `<LSGT>` key**:
- The macOS `kVK_*` constants do not define a standard constant for this key because Apple's keyboards use ANSI geometry. On ISO keyboards used with macOS, the key is accessible as `kVK_ISO_Section` = 0x0A.[^37]
- The X11 keysym for this key depends on the active layout. `XKB_KEY_less` (0x003C, `<`) is the base character on the German, French, and many other European layouts.

**Notes on numpad Enter**:
- It shares `VK_RETURN` with main Enter on Windows, distinguished only by the `KBDEXT` flag (extended scan code 0xE0 0x1C).[^36][^60]
- On Linux it is `KEY_KPENTER` = 96, a separate evdev code.

***
## 7. Glossary
| Term | Precise One-Line Definition |
|---|---|
| **Matrix scan** | The MCU process of sequentially driving keyboard matrix rows and reading column intersections to detect key state changes |
| **Scan code** | A byte (or multi-byte sequence) emitted by PS/2 keyboard hardware, or synthesized by OS drivers, identifying a physical key position; three sets exist (Set 1 XT, Set 2 AT, Set 3)[^31][^32] |
| **Virtual Scan Code (VSC)** | Windows-specific term for the Set-1-compatible scan code presented to the Windows keyboard driver stack, synthesized from USB HID Usage IDs by `kbdhid.sys`[^6] |
| **HID Usage ID** | A 16-bit identifier within a HID Usage Page (0x07 for keyboards) that names a key position in a hardware-independent, position-based scheme; defined by USB-IF[^2][^11] |
| **Virtual Key Code (VK_*)** | Windows-only 8-bit integer identifying the logical function of a key, independent of physical hardware; produced by the keyboard layout DLL's VSC-to-VK mapping[^1][^6] |
| **CGKeyCode** | macOS integer (typedef uint16_t) identifying a physical key position relative to the ANSI US reference layout; defined in HIToolbox `<Events.h>` as `kVK_*` constants[^4][^22] |
| **evdev keycode** | Linux kernel integer (`KEY_*`) defined in `linux/input-event-codes.h`, emitted in `input_event.code` for `EV_KEY` events; maps HID Usage IDs to small integers[^8][^20] |
| **X11 keycode** | An 8-bit integer (range 8–255) used by the X Window System to identify a physical key; equals the evdev keycode + 8 for evdev-based keyboards[^39][^40] |
| **Keysym** | A 32-bit integer (`xkb_keysym_t`) representing a *symbol* or *action* produced by a key; the result of applying XKB layout rules to an X11 keycode plus modifier state[^5] |
| **XKB key name** | An alphanumeric string (e.g., `<AD01>`, `<LSGT>`) used in XKB configuration files to denote a physical key position in a layout-independent way[^26][^63] |
| **Shift level** | A dimension of key output indexing; Level 1 = unshifted, Level 2 = Shift, Level 3 = AltGr/Level3Shift, Level 4 = AltGr+Shift; defined in ISO/IEC 9995[^46][^9] |
| **Dead key** | A key that produces no immediate output but sets a pending composition state, modified by the next key press to produce a combined character (e.g., `^` + `e` → `ê`)[^54][^55] |
| **Compose key** | A key that, when pressed and released, begins a multi-character composition sequence resolved against a Compose file; conceptually similar to a dead key but user-configurable[^47][^29] |
| **RMLVO** | XKB configuration parameters: Rules, Model, Layout, Variant, Options; the user-facing specification from which XKB compiles its internal KcCGST keymap representation[^28][^65] |
| **KcCGST** | The five internal XKB keymap components: Keycodes, Compat, Geometry, Symbols, Types; compiled from RMLVO[^28] |
| **UCKeyTranslate** | macOS API (`<Carbon/Carbon.h>`) that translates a CGKeyCode plus modifier state to a Unicode string, maintaining dead-key state across calls[^12] |
| **ToUnicodeEx** | Windows API (`<winuser.h>`) that translates a VK code plus keyboard state array to a Unicode character string, honoring dead-key state[^23] |
| **AltGr** | Common abbreviation for *Alternate Graphic* or Right Alt key; acts as Level 3 Select in ISO/XKB terminology; treated as Ctrl+Alt on Windows when `KLLF_ALTGR` is set[^46][^24] |

***
## 8. Implications for an OS-Independent Layout Model
### 8.1 Choice of Physical Key Identifier
An OS-independent layout model needs a *stable, position-based key identifier* that:
1. Is not derived from any OS's numbering scheme (to avoid platform lock-in)
2. Covers ANSI, ISO, JIS, ABNT, and other geometries
3. Has a clear, documented mapping to every OS's native keycode

**Recommended approach: USB HID Usage IDs as primary identifiers, with XKB names as human-readable aliases.**

HID Usage IDs on page 0x07 are the *lowest common denominator* — they are generated by the firmware before any OS code runs. Every OS maps HID Usage IDs to its native codes. A layout model built on HID Usage IDs is the closest available to "physical position" without requiring knowledge of a specific keyboard's internal matrix.[^2][^11]

XKB key names (e.g., `<AD01>` for Q) serve as readable, unambiguous aliases for these positions and are used in existing cross-platform tooling (libxkbcommon, xkeyboard-config). The combination of HID Usage ID (machine-readable stable identifier) + XKB name (human-readable, tool-compatible alias) covers all standard cases.[^26][^63][^28]

**For ISO/JIS/ABNT extra keys**:
- `<LSGT>` / HID 0x64: ISO 102nd key — must be explicitly included; absent on ANSI[^2]
- JIS International keys: HID 0x87–0x8D — must be supported for Japanese keyboards[^2]
- ABNT extra keys: no standardized HID codes beyond `VK_ABNT_C1/C2`; these require a geometry-specific extension[^35]
### 8.2 Modifier / Level Model
The portable format should adopt the ISO/IEC 9995 / XKB *shift-level* model with at minimum four levels:[^46][^9]

- **Level 1**: Base (no modifier)
- **Level 2**: Shift
- **Level 3**: Level3Shift (AltGr / Right Alt)
- **Level 4**: Shift + Level3Shift
- **Level 5 and Level 6** (optional): Level5Shift and Shift + Level5Shift

Modifiers should be named by their *function* (Level2Shift, Level3Shift, Level5Shift, CapsLock, NumLock) rather than their physical key, because the physical key used to activate them is itself a layout choice.

**Groups** (XKB notion) should be modeled separately from levels, as they represent alternate complete keymaps (e.g., for multiple script support) rather than shifted variants within a single keymap.
### 8.3 Dead Key and Composition Model
The model should represent dead keys as producing a special *dead-key token* at a given level rather than a Unicode character. The composition table (equivalent to XKB Compose file or Windows `pDeadKey`) is a separate, ordered list of `(dead-key-token, base-character) → output-character-sequence` mappings. This separation allows:
- The same dead-key key position to compose differently across layouts
- Multi-step composition chains (dead key + dead key + base)

The format should distinguish between:
- *Dead keys defined in the layout* (XKB `dead_*` keysyms, macOS `ucKeyStateRecords`)
- *Compose sequences defined externally* (Compose file entries)
- *Ligatures* (Windows `pLigature`-style one-key → multi-codepoint output)
### 8.4 Known Traps and Ambiguities
**Trap 1 – The AltGr / Ctrl+Alt ambiguity**: On Windows, layouts with `KLLF_ALTGR` treat Right Alt as Ctrl+Alt. This means a shortcut `Ctrl+Alt+E` conflicts with the AltGr+E sequence (e.g., the Euro sign on some keyboards). A portable format must flag whether Level 3 is accessed by Right Alt alone or by Ctrl+Right Alt, and applications must be aware of this.[^24][^45]

**Trap 2 – macOS has no native AltGr concept**: macOS uses the Option key as its Level 3 analog but the `UCKeyboardLayout` encodes it as arbitrary modifier bitmask combinations, not an ISO Level 3 concept. Cross-platform tools must explicitly map `kVK_Option` + key to Level 3 when generating macOS layouts from a portable representation.[^66][^12]

**Trap 3 – The X11 keycode 8-offset**: Any tool that consumes raw evdev codes and XKB keymaps simultaneously must consistently add/subtract 8. Mixing evdev and XKB namespace values without tracking the offset is a common source of bugs.[^39][^40][^30]

**Trap 4 – The 255-keycode ceiling on X11**: X11 keycodes are 8-bit values; any keyboard emitting evdev codes above 247 cannot be represented faithfully in X11. Wayland + libxkbcommon relaxes this limit (libxkbcommon supports extended keycodes beyond 255). A portable model targeting X11 must cap the key identifier range or detect overflow.[^40][^41]

**Trap 5 – Caps Lock semantics are layout-dependent**: A portable model must specify whether Caps Lock is *alphabetic lock* (only affects alphabetic keys) or *shift lock* (affects all keys). French AZERTY requires shift lock behavior; Turkish requires locale-specific uppercase rules. The default behavior of the model should be alphabetic lock, with a per-layout override.[^49][^50][^51]

**Trap 6 – VK code reuse across OSes is coincidental**: VK_A = 0x41 matches ASCII 'A', but macOS `kVK_ANSI_A` = 0x00. `KEY_A` evdev = 30. These numbers are entirely unrelated. A portable model must *not* assume any numeric correspondence across OS namespaces.[^45]

**Trap 7 – macOS scan codes are inaccessible**: Qt documentation notes "On Mac OS/X, this function is not useful, because there is no way to get the scan code from Carbon or Cocoa." macOS exposes only CGKeyCodes (which are position-based) and character output, never the underlying HID Usage ID directly to application code without using IOKit at the kernel level. A portable identifier cannot rely on scan codes being available on macOS.[^19][^45]

**Trap 8 – JIS and ABNT require geometry-specific extensions**: The portable model must include a *geometry* field that informs the consumer which extra keys exist. A layout declared for ISO geometry must define `<LSGT>`; a layout for JIS geometry must define the additional Japanese keys; ABNT layouts require the two ABNT-specific keys. Omitting geometry metadata leads to silently missing or wrong key bindings.

**Trap 9 – Input Method Editor (IME) bypass**: On Japanese, Chinese, and Korean systems, key events are often intercepted by an IME before reaching the application. The IME performs its own multi-keystroke composition (reading → conversion → commit). The portable layout model described here covers the *pre-IME* key-to-character mapping only; IME integration is an orthogonal problem.

**Trap 10 – Dead-key state is per-thread (Windows) / per-process**: On Windows, `ToUnicodeEx()` with the standard flags modifies the thread's keyboard state dead-key buffer as a side effect. Callers that merely want to *query* the character without affecting state must use the `MAPVK_VK_TO_CHAR` flag or set bit 2 of `wFlags` (available since Windows 10 version 1607) to suppress state modification.[^23]
### 8.5 Recommended Portable Format Structure
A minimal OS-independent keyboard layout record should contain:

```
KeyboardLayout {
  metadata: {
    geometry: ANSI | ISO | JIS | ABNT | ABNT2 | custom
    locale: BCP 47 tag (e.g., "fr-FR", "de-DE")
    caps_lock_behavior: alphabetic | shift_lock | locale_specific
    altgr_mode: right_alt | ctrl_alt_both | none
  }
  
  keys: [
    {
      id: HID_Usage_ID  // primary stable identifier (uint16, page 0x07)
      xkb_name: string  // e.g., "<AD01>" — human-readable alias
      levels: [
        { modifier: "none",          output: char | dead_token | action },
        { modifier: "shift",         output: char | dead_token | action },
        { modifier: "level3",        output: char | dead_token | action },
        { modifier: "shift+level3",  output: char | dead_token | action },
        // ... additional levels as needed
      ]
    },
    ...
  ]
  
  composition: [
    { sequence: [dead_token, char], result: char_or_string },
    ...
  ]
  
  os_mappings: {           // optional: per-OS keycode cross-reference
    windows: { scan_code: hex, vk: hex },
    macos:   { cg_keycode: hex },
    linux:   { evdev_code: int }
  }
}
```

This structure is complete (covers all standard cases), portable (HID Usage IDs are OS-independent), extensible (geometry variants, additional levels, IME hooks), and maps cleanly to each OS's native model via the documented translations described in this report.

***

*Sources consulted include: USB HID Usage Tables v1.21 (USB-IF, 2023); Microsoft Win32 documentation (Virtual-Key Codes, Keyboard Input Overview, ToUnicodeEx — all retrieved June 2026); Apple CGKeyCode documentation and HIToolbox Events.h; Linux kernel input-event-codes.h (kernel.org); libxkbcommon documentation and source (xkbcommon 1.8.1, March 2025); Arch Linux Wiki — Keyboard Input and X Keyboard Extension; ISO/IEC 9995-1:2009 and ISO/IEC 9995-1:2026; xkeyboard-config (freedesktop.org); Synacktiv "Writing a decent win32 keylogger" series (2023); QMK Firmware documentation.*

---

## References

1. [Virtual-Key Codes (Winuser.h) - Win32 apps | Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes) - The following table shows the symbolic constant names, hexadecimal values, and mouse or keyboard equ...

2. [Keyboard/Keypad Page (0x07) - GitHub Gist](https://gist.github.com/mildsunrise/4e231346e2078f440969cdefb6d4caa3) - This section is the Usage Page for key codes to be used in implementing a USB keyboard. The usage ty...

3. [Keyboard input - ArchWiki](https://wiki.archlinux.org/title/Keyboard_input)

4. [CGKeyCode | Apple Developer Documentation](https://developer.apple.com/documentation/coregraphics/cgkeycode) - In macOS, the hardware scan codes generated by keyboards are mapped to a set of virtual key codes th...

5. [libxkbcommon: Keysyms](https://xkbcommon.org/doc/current/group__keysyms.html)

6. [Keyboard Input Overview - Win32 apps | Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/inputdev/about-keyboard-input) - The keyboard device driver interprets a scan code and translates (maps) it to a virtual-key code, a ...

7. [Keyboard State - libxkbcommon](https://xkbcommon.org/doc/current/group__state.html)

8. [libevdev/include/linux/input-event-codes.h at master](https://github.com/whot/libevdev/blob/master/include/linux/input-event-codes.h) - mirror of libevdev. Contribute to whot/libevdev development by creating an account on GitHub.

9. [ISO/IEC 9995-1:2009](https://www.iso.org/standard/51645.html) - Information technology — Keyboard layouts for text and office systems — Part 1: General principles g...

10. [ISO/IEC 9995 - Wikipedia](https://en.wikipedia.org/wiki/ISO/IEC_9995)

11. [HID Usage Tables](https://usb.org/sites/default/files/hut1_21.pdf)

12. [UCKeyTranslate issue](https://discussions.apple.com/thread/2023302)

13. [qmk_firmware/docs/custom_matrix.md at master · qmk/qmk_firmware](https://github.com/qmk/qmk_firmware/blob/master/docs/custom_matrix.md) - Open-source keyboard firmware for Atmel AVR and Arm USB families - qmk/qmk_firmware

14. [qmk_firmware/quantum/matrix_common.c at master · qmk/qmk_firmware](https://github.com/qmk/qmk_firmware/blob/master/quantum/matrix_common.c) - Open-source keyboard firmware for Atmel AVR and Arm USB families - qmk/qmk_firmware

15. [Understanding QMK's Code](https://docs.qmk.fm/understanding_qmk) - Documentation for QMK Firmware

16. [HID keyboard/mouse combo report ID](https://forums.obdev.at/viewtopic4d0c.html?t=10780) - Ok the problem was that usbSetInterrupt can only send 8 bytes at a time and my keyboard descriptor t...

17. [Keyboard HID report - Stack Overflow](https://stackoverflow.com/questions/65385100/keyboard-hid-report) - Bluetooth HID Boot Protocol keyboard reports are 9 octets (1-octet Report ID + standard 8-octet keyb...

18. [macOS keyboard event intercepted three ways - R0uter's Blog](https://www.logcg.com/en/archives/2902.html) - This article has detailed instructions,Pass it over here,How do we have focused on addressing key us...

19. [macOS - keylogging through HID device interface - The Evil Bit Blog](http://theevilbit.blogspot.com/2019/02/macos-keylogging-through-hid-device.html) - The built in keyboard on a MacBook Pro is also connecting through the USB / IOHID interface. That ma...

20. [python-evdev Documentation](https://manpages.ubuntu.com/manpages/jammy/man7/python-evdev.7.html)

21. [Keyboard inputs - scancodes, raw input, text input, key names](https://handmade.network/forums/t/2011-keyboard_inputs_-_scancodes,_raw_input,_text_input,_key_names) - The driver and Windows use those codes to generate key messages (WM_KEYDOWN, WM_KEYUP...) and virtua...

22. [mac开发之监听拦截键盘输入keycode - Ro.bber](https://robberjj.github.io/2017/11/04/KeyCodes/) - 最近在自己写一个mac上图片预览的功能，仿系统的预览，想要在预览的时候，加入快捷键，实现放大、缩小、前一张、后一张等功能。

23. [ToUnicodeEx function (winuser.h) - Win32 apps - Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-tounicodeex) - ToUnicodeEx will translate scancodes marked as key break events in addition to its usual treatment o...

24. [Writing a decent win32 keylogger [2/3]](https://www.synacktiv.com/publications/writing-a-decent-win32-keylogger-23) - Writing a decent win32 keylogger [2/3]

25. [Convert virtual keycode to Unicode string - Stack Overflow](https://stackoverflow.com/questions/8263618/convert-virtual-keycode-to-unicode-string) - So try that: Turn off kUCKeyTranslateNoDeadKeysBit , and if UCKeyTranslate sets the dead-key state, ...

26. [Layout independent keys with Linux & X11 - Alex Baines](https://abaines.me.uk/updates/linux-x11-keys) - To give some context, X11 has two indentifiers related to keys: KeySyms and KeyCodes. KeySyms are 32...

27. [How to translate X11 keycode back to scancode or hid usage id ...](https://stackoverflow.com/questions/45774113/how-to-translate-x11-keycode-back-to-scancode-or-hid-usage-id-reliably) - X11 keycode. xev command prints keycode and keysym and I observed keycode does not change regardless...

28. [Who-T](http://who-t.blogspot.com/2020/08/)

29. [XKB, briefly](https://wayland-book.com/seat/xkb.html)

30. [Keyboard input - The Wayland Protocol](https://wayland-book.com/seat/keyboard.html)

31. [Scancode - Wikipedia](https://en.wikipedia.org/wiki/Scancode)

32. [Scancode](https://deskthority.net/wiki/Scancode)

33. [Keyboard-internal scancodes](https://www.scs.stanford.edu/10wi-cs140/pintos/specs/kbd/scancodes-9.html)

34. [Portuguese (Brazil ABNT) / Portuguese (Brazil ABNT2) - Virtual Keys - Keyboard Layout Info](https://kbdlayout.info/KBDBR/virtualkeys) - See virtual keys of Portuguese (Brazil ABNT) / Portuguese (Brazil ABNT2) as defined in KBDBR.DLL.

35. [Extension for Brazilian keyboards (Windows)](https://forum.colemak.com/topic/2091-extension-for-brazilian-keyboards-windows/)

36. [Properly handling keyboard input - Molecular Musings](https://blog.molecular-matters.com/2011/09/05/properly-handling-keyboard-input/) - Looking at the WM_KEYDOWN message, we can see that it will be sent for non-system keys (“Alt” is not...

37. [ASCII and Mac Virtual Key codes for editing com.apple ... - GitHub Gist](https://gist.github.com/jimratliff/227088cc936065598bedfd91c360334e) - These constants are the virtual keycodes defined originally in Inside Mac Volume V, pg. V-191. They ...

38. [xkbcli-interactive-evdev(1) - Arch manual pages](https://man.archlinux.org/man/xkbcli-interactive-evdev.1.en)

39. [[PATCH 1/2] Explain offset by 8 when mapping from evdev to XKB](https://lists.sr.ht/~sircmpwn/public-inbox/%3C20240316160413.14944-1-ariel@arieldon.com%3E)

40. [xkbcommon::xkb::Keycode - Rust](https://hid-io.github.io/xkbcommon/xkb/type.Keycode.html) - Historically, the X11 protocol, and consequentially the XKB protocol, assign only 8 bits for keycode...

41. [xkb mapping for keycodes higher than 255 : r/swaywm - Reddit](https://www.reddit.com/r/swaywm/comments/exlcof/xkb_mapping_for_keycodes_higher_than_255/) - I have a keyboard (Logitech K350) that has keys which emit keycodes higher than 255 (using evdev). X...

42. [How to map a X11 KeySym to a Unicode character?](https://stackoverflow.com/questions/8970098/how-to-map-a-x11-keysym-to-a-unicode-character) - This is an exact duplicate of this question; however the code linked in the accepted answer is nearl...

43. [libxkbcommon/NEWS.md at xkbcommon-1.8.1 · xkbcommon/libxkbcommon](https://github.com/xkbcommon/libxkbcommon/blob/xkbcommon-1.8.1/NEWS.md) - keymap handling library for toolkits and window systems - xkbcommon/libxkbcommon

44. [A Win32 Virtual Keycode reference • /r/ASCII : r/programming - Reddit](https://www.reddit.com/r/programming/comments/2jgie0/a_win32_virtual_keycode_reference_rascii/) - VKs have functionality associated to them, so if you write a custom layout driver, you can map the S...

45. [Dealing with keyboard layouts for input on multiple platforms](https://forum.qt.io/topic/95527/dealing-with-keyboard-layouts-for-input-on-multiple-platforms) - Dealing with keyboard layouts for input on multiple platforms · Problem 1: Different codes on differ...

46. [Re: Keyboard layouts (ISO 9995)](https://www.unicode.org/mail-arch/unicode-ml/Archives-Old/UML018/0213.html)

47. [xmonad-conf/xkb/README.md at master · nakal/xmonad-conf](https://github.com/nakal/xmonad-conf/blob/master/xkb/README.md) - Nakal's Xmonad (plus desktop) configuration. Contribute to nakal/xmonad-conf development by creating...

48. [X windows keyboard notes](http://www.pixelbeat.org/docs/xkeyboard/)

49. [Caps lock and number line - Fedora Discussion](https://discussion.fedoraproject.org/t/caps-lock-and-number-line/73954) - Hi guys. So i use a azerty TKL keyboard on my desktop, and when i press “caps lock” it allow to type...

50. [Issue with Caps lock and number line on AZERTY Keyboard - Desktop](https://discourse.gnome.org/t/issue-with-caps-lock-and-number-line-on-azerty-keyboard/5053) - I use a AZERTY TKL keyboard on my desktop (Fedora 33), and when i press “caps lock” it allow to type...

51. [Turkish Keyboard "Caps Lock" and "i" Keys - Oracle Forums](https://forums.oracle.com/ords/apexds/post/turkish-keyboard-caps-lock-and-i-keys-0227) - Using the Sun Turkish Q (Type 6 USB) keyboard with the "Caps Lock" key engaged, pressing the (dotted...

52. [Caps Lock behavior setting - Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/3217466/caps-lock-behavior-setting) - Default behavior: Caps Lock is toggled on/off by pressing capslock key. Alternate: Caps Lock is togg...

53. [The X Keyboard Extension:](https://www.x.org/releases/X11R7.6/doc/libX11/specs/XKB/xkblib.html) - The X Keyboard Extension makes it possible to clearly and explicitly specify most aspects of keyboar...

54. [uxkb: add Compose (dead-key) support · bluetech/kmscon@89aeb0f](https://github.com/bluetech/kmscon/commit/89aeb0f6cbabf928ec9526d8c92138a42d48c61a) - Dead keys are special keys which have no immediate effect when pressed, but instead they modify the ...

55. [Input, revisited](https://blog.gtk.org/2021/03/24/input-revisited/) - My last update talked about better visual feedback for Compose sequences in GTK's input methods. I d...

56. [macOS dead keys immediately show an underlined version, any ...](https://groups.google.com/g/ukelele-users/c/S59c-oljQNs) - On macOS however you immediately see the dead key (underlined or otherwise highlighted), which then ...

57. [ANSI VS ISO Keyboard Layouts: A Comprehensive Guide](https://akkogear.eu/blogs/news/ansi-vs-iso-keyboard-layouts-a-comprehensive-guide) - ANSI and ISO are physical keyboard layout determine the size, shape, and position of the keys on the...

58. [Unlocking the Mystery of Unusual Keyboard Layouts - Ranked](https://ranked.gg/blogs/news/unlocking-the-mystery-of-unusual-keyboard-layouts-a-comprehensive-guide-to-ansi-iso-jis-abnt-ks-and-more) - The ANSI layout features 104 keys. The ISO layout features 105 keys. In the ISO layout, the "Enter" ...

59. [Understanding Different Physical Layouts For Keyboards: ANSI Vs ...](https://mechkeys.com/blogs/guide/understanding-different-physical-layouts-for-keyboards-ansi-vs-iso-vs-jis) - We are going to discuss physical keyboard layouts like ANSI, ISO, JIS, and more. These are different...

60. [Virtual Keys](https://kbdlayout.info/KBDSW/virtualkeys) - See virtual keys of Swedish as defined in KBDSW.DLL.

61. [USB: HID Usage Table · tmk/tmk_keyboard Wiki - GitHub](https://github.com/tmk/tmk_keyboard/wiki/USB:-HID-Usage-Table) - Keyboard Keypad Page (0x07) ; 0A, Keyboard g and G · Sel ; 0B, Keyboard h and H · Sel ; 0C, Keyboard...

62. [Support special keys VK_ABNT_C1 and VK_ABNT_C2 of ...](https://bugzilla.mozilla.org/show_bug.cgi?id=896362) - RESOLVED (masayuki) in Core - Widget: Win32. Last updated 2013-07-29.

63. [All you need to know about KBD keyboard files (and nothing more)](https://www.bestov.io/blog/all-you-need-to-know-about-kbd-keyboard-files/) - key <AC01> means that we are defining the mapping for keycode <AC01> . This keycode corresponds to t...

64. [Querying macOS if a key is pressed - GitHub Gist](https://gist.github.com/chipjarred/cbb324c797aec865918a8045c4b51d14) - static let kVK_ANSI_C : CGKeyCode = 0x08. static let kVK_ANSI_V : CGKeyCode = 0x09. static let kVK_A...

65. [Data Fields](https://xkbcommon.org/doc/0.5.0/structxkb__rule__names.html)

66. [Virtual key codes on Apple OS X - Sorin Sbarnea's Crib](https://sbarnea.com/p/virtual-key-codes-on-apple-os-x/) - In this case all we have to do is to look after VK_A virtual key. VK_A code is present on any keyboa...

