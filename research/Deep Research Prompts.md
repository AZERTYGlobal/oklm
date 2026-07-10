# OKLM — Prompts de deep research

> Objectif : cartographier de façon exhaustive le fonctionnement des claviers et des
> dispositions sur **tous** les supports (desktop par OS, mobile, firmware programmable,
> surfaces dynamiques, embarqué / appliances, accès distant, accessibilité), afin
> d'éclairer la conception du modèle OKLM (Open Keyboard Layout Model) : quels concepts un
> modèle ouvert doit représenter, et comment il doit s'exporter vers les formats existants.

## Mode d'emploi

- 16 prompts ciblés, **autonomes** (chacun se suffit à lui-même), rédigés en anglais pour
  maximiser la qualité des sources (l'écosystème LDML / keyboard tooling est anglophone).
- Coller **un prompt à la fois** dans l'outil de deep research (ChatGPT Deep Research,
  Gemini Deep Research, Claude, Perplexity…). Ne pas tout fusionner : la recherche est
  meilleure sur une question bien bornée.
- Chaque prompt demande déjà un **tableau / une liste structurée**, des **citations de
  sources primaires** et une section **« implications pour un modèle ouvert »** —
  directement réutilisable pour alimenter `SPEC.md` et le futur schéma.
- Note de périmètre : ces prompts sont purement techniques — pas de marque,
  pas de stratégie commerciale, pas de contexte projet. Les garder ainsi.
- Ordre suggéré, en 3 blocs :
  - **Bloc A — Fondations & interop** : **1** (codes de touches), **16** (géométrie
    physique), puis **9** et **10** (standard LDML + scripts complexes).
  - **Bloc B — Cibles techniques** : **2 → 5** (OS desktop), **6** (firmware), **7**
    (mobile), **15** (web), **8** (embarqué).
  - **Bloc C — Faire le standard** : **11** (normes de jure), **12** (conception du
    format), **13** (gouvernance & adoption), **14** (besoins industrie & fabrication).

### Carte des prompts

| # | Sujet | Bloc |
|---|-------|------|
| 1 | Pipeline d'entrée & codes de touches (fondations, multi-OS) | A |
| 2 | Dispositions clavier sous **Windows** | B |
| 3 | Dispositions clavier sous **macOS** | B |
| 4 | Dispositions clavier sous **Linux / Wayland (XKB)** | B |
| 5 | **Autres OS desktop** (BSD, ChromeOS, Haiku, illumos/Solaris, Redox…) | B |
| 6 | Firmware de claviers programmables (QMK, ZMK, KMK…) | B |
| 7 | Mobile & surfaces d'entrée périphériques | B |
| 8 | Claviers à l'écran embarqués / appliances / kiosques / auto / TV / consoles | B |
| 9 | Formats d'échange & outils d'authoring (LDML 3.0, kalamine, kbdgen…) | A |
| 10 | IME & saisie des scripts complexes (CJK, indiens, arabe, SE asiatique…) | A |
| 11 | Normes de jure existantes (ISO/IEC 9995, JIS, DIN, AFNOR…) & légendes | C |
| 12 | Conception d'un format durable + conformance & suite de tests | C |
| 13 | Gouvernance, voie de standardisation & playbook d'adoption | C |
| 14 | Besoins consolidés des parties prenantes & chaîne de fabrication | C |
| 15 | Saisie clavier sur la plateforme Web (UI Events `code`/`key`, Keyboard Map API) | B |
| 16 | Formats de géométrie physique (KLE JSON, QMK info.json, VIA, grille ISO 9995) | A |

---

## Prompt 1 — From physical key to character: the input pipeline & key codes

```text
You are a systems researcher producing a rigorous technical report for engineers who are
designing an open, OS-independent model to describe keyboard layouts.

GOAL
Explain, end to end and with precise terminology, how a physical key press becomes a
character or action across the major desktop operating systems, and map out every code
system involved along the way.

COVER IN DETAIL
1. The full input pipeline: physical switch -> matrix scan -> hardware/firmware -> USB HID
   report -> OS driver -> virtual key / keysym -> layout mapping -> produced character or
   action. Describe what happens at each stage and which component owns the layout logic.
2. Key code systems, with their exact roles and how they relate to each other:
   - USB HID Usage IDs (Keyboard/Keypad usage page 0x07): what they identify and why they
     are position-based, not character-based.
   - PS/2 scan code sets (set 1 / set 2 / set 3) and the notion of "scancode".
   - Windows virtual key codes (VK_*) and scan-code-to-VK mapping.
   - macOS virtual key codes and the Carbon/HIToolbox keycodes.
   - Linux: evdev key codes, kernel keycodes, X11 keycodes vs keysyms, the keycode->keysym
     translation.
   - The relationship "physical position vs logical key vs produced character".
3. Modifiers and levels: Shift, Caps Lock (and locale-specific caps behavior), Ctrl, Alt,
   AltGr / right-Alt, the ISO "level 3" and "level 5" selectors, Mode_switch, and how OSes
   model modifier state and shift levels differently.
4. Dead keys and composition at the OS level: how dead keys, the Compose key, and chained
   dead keys are processed, and at which layer.
5. Physical geometries and key naming: ANSI vs ISO vs JIS vs ABNT, the extra keys (ISO
   <LSGT>, JIS keys, ABNT extra key), and the standard naming conventions used to refer to
   physical positions (e.g. XKB key names like AD01/AC01, the row/column conventions).
6. How "the same physical key" is referred to consistently across OSes despite different
   code numbers, and what a stable, OS-independent physical key identifier would need.

DELIVERABLES
- A stage-by-stage diagram (described in text) of the pipeline.
- A cross-reference table: for ~10 representative keys (e.g. the QWERTY "Q", the key left of
  "1", the ISO key next to left Shift, Space, Enter, Caps Lock), list their USB HID usage,
  Windows scancode + VK, macOS keycode, and Linux evdev keycode + typical X11 keysym.
- A glossary of every code term (scancode, usage ID, keycode, keysym, virtual key) with a
  one-line precise definition.
- A section "Implications for an OS-independent layout model": what identifier scheme and
  modifier/level model a portable format should adopt, and the known traps.

REQUIREMENTS
- Cite primary/authoritative sources (USB-IF HID Usage Tables, Microsoft docs, Apple docs,
  kernel input docs, xkeyboard-config / libxkbcommon docs).
- Flag any area where behavior is OS-version-specific or ambiguous.
- Prefer precise, current information; note the version/date of key facts.
```

---

## Prompt 2 — Keyboard layouts on Windows: model, capabilities and limits

```text
You are a systems researcher producing a technical report for engineers designing an open,
human-maintainable model that must EXPORT to Windows keyboard layouts and IMPORT from them.

GOAL
Explain comprehensively how keyboard layouts work on Windows, and document EVERYTHING that is
and is not achievable in a Windows keyboard layout, so an exporter can target Windows
faithfully and flag what cannot be represented.

COVER IN DETAIL
1. The runtime model: how Windows turns a keypress into a character — scan code -> virtual
   key (VK) -> character via the active keyboard layout DLL (kbd*.dll); the role of
   ToUnicode / ToUnicodeEx; the kbd tables (VK maps, character modifier tables, dead-key
   tables, ligature tables).
2. The layout DLL itself: the kbd*.dll structure (KBDTABLES and friends), how MSKLC and the
   kbdutool compiler generate it, and the KLC source format used as input.
3. Identifiers and registration: KLID, input locale identifiers (HKL), language/locale
   association, and the registry entries under
   HKLM\SYSTEM\CurrentControlSet\Control\Keyboard Layouts.
4. What a layout CAN express:
   - shift states / modifier columns (base, Shift, Ctrl, Ctrl+Alt = AltGr, Shift+Ctrl+Alt,
     and the Kana state); how AltGr is encoded (VK_CONTROL + VK_MENU) and the "no AltGr"
     option;
   - Caps Lock behavior: the CAPLOK / SGCAPS mechanism, "Caps Lock acts as Shift",
     locale-specific caps;
   - dead keys and the limits on dead-key chaining;
   - ligatures (LIGATURE): multi-code-unit output and its hard length limit (UTF-16 units).
5. What a layout CANNOT express, and the official escape hatch: no contextual/transform
   rules, no reordering, no logic based on prior output beyond single dead keys — and how
   complex input is instead handled by the Text Services Framework (TSF) and IMEs.
6. Tooling landscape: Microsoft Keyboard Layout Creator (MSKLC) and its limits; calling
   kbdutool directly / hand-writing the kbd source; KbdEdit (commercial) and what it unlocks
   beyond MSKLC; PowerToys Keyboard Manager — and crucially the difference between runtime
   key/shortcut REMAPPING and a true layout definition.
7. Deployment: how custom layouts are installed (the MSKLC-produced .msi / setup), per-user
   vs system, signing/driver-signing considerations, and modern packaging notes.

DELIVERABLES
- A clear description of the KLC/kbd data model and the runtime resolution path.
- A capability checklist: for each feature (shift states, AltGr, dead keys, chained dead
  keys, ligature output length, caps behaviors, locale tagging) state supported / partial /
  not possible, with the exact limit/number where one exists.
- A "limits & workarounds" section mapping unsupported layout features to TSF/IME or
  companion-app approaches.
- A section "Implications for an OKLM -> Windows exporter": what the source model must
  capture to generate a faithful Windows layout, and exactly where loss is unavoidable
  (requiring an explicit loss report).

REQUIREMENTS
- Cite primary sources (Microsoft kbd.h / keyboard layout docs, MSKLC docs, ToUnicodeEx,
  TSF docs) and reputable references (e.g. Michael Kaplan's archived writings, KbdEdit docs).
- Be precise about numeric limits and Windows-version differences.
- Distinguish remapping tools from true layout definition.
```

---

## Prompt 3 — Keyboard layouts on macOS: model, capabilities and limits

```text
You are a systems researcher producing a technical report for engineers designing an open,
human-maintainable model that must EXPORT to macOS keyboard layouts and IMPORT from them.

GOAL
Explain comprehensively how keyboard layouts work on macOS, and document EVERYTHING that is
and is not achievable in a macOS layout, so an exporter can target macOS faithfully and flag
what cannot be represented.

COVER IN DETAIL
1. The .keylayout format: the XML Unicode keyboard layout, its DTD/structure and every
   element:
   - <keyboard> and the group/id/name attributes;
   - <layouts> mapping physical keyboard types (the first/last/mapSet ranges) to keyMapSets,
     and how ANSI/ISO/JIS keyboard-type detection selects a map;
   - <modifierMap> with <keyMapSelect> and <modifier> keys — how modifier combinations
     resolve to a keyMap index;
   - <keyMapSet> and <keyMap index="...">;
   - <key> with output vs action;
   - <actions>, <action>/<when state=...>, and <terminators> — i.e. the dead-key / chained
     state machine.
2. The state machine in depth: how dead keys and CHAINED dead keys are expressed via states
   and terminators, multi-character output (output strings), and why this is generally more
   expressive than the Windows dead-key model.
3. What a layout CAN express (arbitrary modifier-combo -> keyMap index, rich state machine,
   multi-char output) and what it CANNOT (true contextual transforms on prior text beyond
   states, reordering for complex scripts, per-application behavior) — and the official
   escape hatch: Input Method Kit (IMK) / input methods for complex scripts.
4. Keyboard layout bundles: the .bundle structure, Info.plist, icon (.icns), installation in
   /Library/Keyboard Layouts vs ~/Library/Keyboard Layouts, and enabling via Input Sources;
   code-signing/notarization considerations for distribution.
5. Tooling: Ukelele as the de facto editor (and its features/limits), plus any other editors
   or command-line approaches; how to validate a .keylayout.
6. Historical/system context: the relationship to older 'KCHR'/'uchr' resources, and how the
   current Unicode keylayout supersedes them.

DELIVERABLES
- A clear description of the .keylayout data model (elements, the modifier-to-keyMap mapping,
  and the action/state/terminator machine).
- A capability checklist: shift/modifier combinations, dead keys, chained dead keys,
  multi-char output, caps behavior, keyboard-type (ANSI/ISO/JIS) handling — supported /
  partial / not possible, with specifics.
- A "limits & workarounds" section mapping unsupported features to IMK/input methods.
- A section "Implications for an OKLM -> macOS exporter": what the source model must capture
  to generate a faithful .keylayout (especially the state machine for dead-key chains), and
  where loss is unavoidable.

REQUIREMENTS
- Cite primary sources (Apple's keylayout DTD / Technical documentation, Input Method Kit
  docs) and reputable references (Ukelele documentation).
- Be precise about the state/terminator mechanics, which are easy to get wrong.
- Distinguish layout definition from input methods.
```

---

## Prompt 4 — Keyboard layouts on Linux / Wayland (XKB & Compose): model, capabilities and limits

```text
You are a systems researcher producing a technical report for engineers designing an open,
human-maintainable model that must EXPORT to Linux keyboard layouts and IMPORT from them.

GOAL
Explain comprehensively how keyboard layouts work on Linux and Wayland, and document
EVERYTHING that is and is not achievable, so an exporter can target this ecosystem faithfully.

COVER IN DETAIL
1. The XKB model and its components: keycodes, types, compat, symbols, geometry; how the
   RMLVO inputs (Rules, Model, Layout, Variant, Options) resolve into the KcCGST components,
   and what each component does.
2. The xkeyboard-config database: how symbols files are structured, the layout/variant
   system, common options (e.g. lv3:ralt_switch, caps:*, compose:*), and the rules files
   that glue RMLVO together.
3. Groups and levels: multiple groups (layouts) and group switching; shift levels (including
   level3 and level5 and beyond); key types (ONE_LEVEL, TWO_LEVEL, FOUR_LEVEL, etc.); real
   vs virtual modifiers; the level3/level5 selectors; redirect/overlay features.
4. libxkbcommon as the modern consumer (Wayland compositors and others) vs the legacy X
   server path: the keymap text format, what xkbcommon supports, and practical differences.
5. Composition: XCompose / Compose files (~/.XCompose and the locale Compose tables), the
   Compose key, multi-key sequences, dead keys (dead_acute, etc.), and how Compose layers on
   top of XKB to add arbitrary multi-key composition.
6. The XKB vs Compose vs IME boundary: what XKB+Compose can do directly, and where complex
   scripts are instead handled by IBus / Fcitx / m17n input methods (reordering, contextual
   shaping).
7. Packaging custom layouts: the xkeyboard-config mechanism for shipping third-party layouts
   without patching system files (the "extension" / extra-layout directories support added in
   a recent release — find and state the exact version and date rather than assuming one) —
   how it works and why it matters for distributing a custom layout upstream or out-of-tree.
8. Wayland specifics: how compositors consume keymaps, the text-input and virtual-keyboard
   protocols, and any differences from X11 in practice.

DELIVERABLES
- A clear explanation of the RMLVO -> KcCGST resolution and the four/five XKB components.
- A capability checklist: number of levels, groups, dead keys, arbitrary Compose sequences,
  multi-char output, virtual modifiers, geometry — supported / partial / not possible.
- A section on the XKB vs Compose vs IME division of labor.
- A section "Implications for an OKLM -> XKB/Compose exporter": what the source model must
  capture, how to emit both a symbols file and a Compose table, and how to package via
  extension directories; where loss is unavoidable.

REQUIREMENTS
- Cite primary sources (freedesktop xkeyboard-config docs, libxkbcommon docs, the XKB
  protocol/specification, X Compose documentation, the xkeyboard-config release notes for
  the extension-directories feature).
- Be precise about level/group limits and the real-vs-virtual modifier model.
- Note X11 vs Wayland differences and current versions/dates.
```

---

## Prompt 5 — Keyboard layouts on other desktop operating systems

```text
You are a systems researcher producing a technical report for engineers designing an open
keyboard layout model. They already understand Windows, macOS and Linux/XKB. They now need
to map the "long tail" of OTHER desktop operating systems and lower-level layers, to know
which export targets come "for free" (because they reuse XKB) and which need bespoke work.

GOAL
Catalog how keyboard layouts are defined and what is achievable on desktop OSes beyond
Windows/macOS/Linux, plus the relevant console/low-level keymap layers.

COVER
1. ChromeOS: how keyboard layouts and input methods work (Chromium-based input, the layout
   identifiers it uses, how it relates to XKB, and what is author-customizable).
2. The BSDs (FreeBSD, OpenBSD, NetBSD): the console keymap mechanisms (e.g. kbdcontrol and
   .kbd keymaps on FreeBSD; wscons / wsconsctl / wskbd on NetBSD/OpenBSD), and how their X11
   / Wayland stacks reuse xkeyboard-config.
3. Haiku: its keymap system (the Keymap preflet and the keymap command-line tool, the binary
   keymap file format) and what it can express.
4. illumos / Solaris: keytable mechanisms.
5. Hobby / research / niche OSes where documented: Redox OS, SerenityOS, Plan 9, and any
   others with a public layout mechanism.
6. The low-level console/TTY keymap layer as a cross-cutting theme (Linux loadkeys/kbd and
   the BSD equivalents) — how it differs from the graphical layout layer.

FOR EACH, REPORT
- The layout definition mechanism and file format (if public).
- What it can express (shift levels, dead keys, composition, multi-char output).
- Whether it reuses xkeyboard-config/XKB or has its own scheme.
- The authoring tooling, if any.

DELIVERABLES
- A table: rows = each OS / layer above; columns = "layout mechanism / format", "reuses XKB?
  (yes/no/partial)", "expressiveness (dead keys, levels, multi-char)", "tooling".
- A short analysis: which targets are essentially covered by an XKB exporter, and which
  require a dedicated exporter or are effectively out of scope.
- A section "Implications for an open layout model": what minimal additional data (if any)
  these targets need beyond what Windows/macOS/Linux exporters already require.

REQUIREMENTS
- Cite primary sources (each OS's official docs / man pages / handbooks).
- Where a mechanism is undocumented or obscure, say so explicitly rather than guessing.
- Keep claims current and note versions/dates where relevant.
```

---

## Prompt 6 — Programmable keyboard firmware (QMK, ZMK & friends): the advanced feature model

```text
You are a systems researcher producing a technical report for engineers designing an open
layout model. They need to understand the feature set that programmable keyboard FIRMWARE
exposes, because firmware-level layouts go far beyond what OS layout files express.

GOAL
Map the conceptual model and feature set of the leading open keyboard firmware projects, so
the model can decide which firmware concepts to represent, reference, or deliberately leave
out of scope.

PROJECTS TO COVER
- QMK (and the QMK Configurator / info.json / keymap.json model).
- ZMK (devicetree-based keymaps, behaviors).
- KMK (CircuitPython).
- Kaleidoscope (Keyboardio).
- VIA / Vial (runtime remapping over an existing firmware) — clarify how they differ from
  compiling firmware.

FEATURES TO EXPLAIN (with how each firmware models them)
1. The keymap model itself: how a physical matrix maps to keycodes, how a keyboard is
   described (layout macros, matrix, info.json), and the QMK keycode namespace.
2. Layers: momentary (MO), toggle (TG), one-shot (OSL), layer-tap (LT), default layer,
   and how layer state resolves.
3. Dual-role and timing behaviors: mod-tap (MT), tap-hold, hold-tap flavors, tapping term,
   permissive hold, retro tapping.
4. Combos (chords), tap dance, leader key sequences, and key overrides.
5. Macros and dynamic macros; string/Unicode output; the various Unicode input modes
   (and why firmware Unicode output is OS-dependent).
6. One-shot mods, caps word, and other "smart" behaviors.
7. Encoders, RGB/lighting layers, and other non-character outputs (only as far as they
   interact with the layout/keymap model).
8. How firmware handles the host OS layout assumption (i.e. firmware sends keycodes/HID
   usages, and the host layout still applies) — this is a crucial conceptual point.

DELIVERABLES
- A feature matrix: rows = features above; columns = QMK, ZMK, KMK, Kaleidoscope, VIA/Vial;
  cells = supported / partial / no, with the feature's name in that ecosystem.
- A clear explanation of the boundary between "firmware keymap" (runs on the device, emits
  HID usages) and "OS layout" (interprets HID usages into characters) — including what each
  layer is responsible for and where features like combos or unicode live.
- A section "Implications for an open layout model": which of these concepts are layout
  concerns vs device/firmware concerns, which (if any) belong in a portable model as
  optional metadata, and which should be referenced rather than re-specified.

REQUIREMENTS
- Cite primary sources (QMK docs, ZMK docs, KMK docs, Kaleidoscope docs, Vial/VIA docs).
- Be precise about terminology differences between ecosystems (same idea, different names).
- Note where a feature is fundamentally a host-OS concern, not a firmware one.
```

---

## Prompt 7 — Mobile and peripheral input surfaces

```text
You are a systems researcher producing a technical report for engineers designing an open
keyboard layout model that should not assume a classic physical keyboard. They need to
understand how layouts, key codes and legends work on mobile and on peripheral input
surfaces (embedded/appliance screens are covered by a separate prompt).

GOAL
Document how keyboard layouts and key mappings are described and rendered on mobile operating
systems, on-screen/virtual keyboards, dynamic-legend peripherals, accessibility input, and
remote/virtualized input — and what data each of these surfaces needs.

COVER
1. Android:
   - The distinction between Key Layout files (.kl), Key Character Map files (.kcm), and the
     soft-keyboard / IME framework (InputMethodService).
   - How physical keyboards are mapped (generic.kl, vendor .kl, .kcm) vs how the on-screen
     keyboard (e.g. AOSP LatinIME, Gboard) defines its layouts (XML keyboard definitions,
     subtypes/locales, long-press/popup keys, gesture/swipe typing).
2. iOS / iPadOS:
   - How software keyboards and custom keyboard extensions work, hardware-keyboard layout
     selection, and what is and isn't author-definable.
3. On-screen / virtual keyboards in general (web and OS OSKs): how layout + legends are
   defined, touch targets, popups, and the fact that they need *display* data, not just
   character output.
4. Dynamic-legend peripherals and control surfaces: Elgato Stream Deck, Nemeio / Flux-style
   e-ink/LCD keyboards, and any keyboard with per-key displays — how profiles/legends/icons
   are described, and what metadata (label, icon, color, action) they consume.
5. Accessibility input: on-screen keyboards for AAC, scanning keyboards, switch access, and
   what layout/legend metadata accessibility tooling needs (labels, grouping, priority).
6. Remote desktop / virtualization (RDP, VNC, Citrix, SPICE, browser-based): how key events
   are transmitted (scancode vs unicode/clipboard), and the well-known problems with layout
   mismatch between client and host.

FOR EACH SURFACE, REPORT
- What unit it works in (physical position, virtual key, character, or display label).
- What data it needs that a pure character-mapping does NOT provide (legends, icons, popups,
  locales, gestures, accessibility labels, priorities).
- The file/format or API used to define it, if any is public.

DELIVERABLES
- A table: rows = surfaces above; columns = "works in (position/keycode/char/label)",
  "needs display metadata?", "needs gesture/popup data?", "needs accessibility labels?",
  "definition format/API".
- A list of the *non-character* metadata THESE surfaces specifically require (e.g. short
  label, long label, icon, color, popup/alt keys, locale, priority, a11y label). Note: the
  consolidated cross-surface superset is assembled in the stakeholder/manufacturing prompt —
  here, focus on what is specific or unusual to mobile and peripheral surfaces.
- A section "Implications for an open layout model": what display/legend/accessibility layer
  a portable model needs on top of the raw character mapping to serve these surfaces.

REQUIREMENTS
- Cite primary sources (Android key layout / key character map docs and IME docs, Apple
  custom keyboard docs, Stream Deck SDK docs, RDP/VNC protocol notes).
- Distinguish clearly between mapping data (what character) and presentation data (what is
  shown / how it is touched).
```

---

## Prompt 8 — Embedded, appliance, kiosk, automotive, TV & console on-screen keyboards

```text
You are a systems researcher producing a technical report for engineers designing an open
keyboard layout model. They need to understand on-screen text-entry keyboards on EMBEDDED
and DEDICATED-DEVICE screens — not phones, tablets or desktop PCs (those are covered
elsewhere), but the keyboards shown on appliances, vehicles, TVs, consoles, kiosks and
payment terminals.

GOAL
Document how on-screen keyboards are defined, localized and operated on embedded / dedicated
devices, the toolkits and frameworks that provide them, and the unusual constraints these
contexts impose — so an open layout/legend model can decide what data such surfaces need.

DEVICE CONTEXTS TO COVER
1. Smart home appliances and IoT screens: smart fridges (e.g. Samsung Family Hub on Tizen),
   coffee machines, ovens, washing machines, thermostats, smart-display assistants. Often
   small screens, custom UIs, embedded toolkits.
2. Smart TVs, set-top boxes and streaming devices: Android TV / Google TV (leanback IME),
   Apple tvOS, Samsung Tizen TV, LG webOS, Roku, Fire TV. On-screen keyboards navigated by
   D-pad / remote, not touch.
3. Game consoles: PlayStation, Xbox, Nintendo Switch, Steam Deck / Steam Big Picture. On-
   screen keyboards driven by gamepad, with their own layout/legend and locale handling.
4. Automotive infotainment (IVI): Android Automotive OS, QNX-based head units, others;
   on-screen keyboards under driver-distraction / safety constraints (speed lockout,
   limited input).
5. Kiosks, ticketing machines, ATMs and POS / payment terminals: touch on-screen keyboards,
   and especially SECURE PIN entry — Encrypting PIN Pads (EPP), randomized/scrambled key
   layouts, PCI requirements that affect how keys are laid out and displayed.
6. The embedded UI toolkits that supply these keyboards, and how each defines a keyboard:
   Qt Virtual Keyboard, LVGL keyboard widget, embedded Linux (Wayland + Maliit / weston /
   squeekboard), Flutter/embedded, web-based kiosk UIs in a locked-down browser, and any
   vendor SDKs.

FOR EACH CONTEXT / TOOLKIT, REPORT
- How the on-screen keyboard layout and key legends are defined (config file, XML/JSON, code,
  or vendor tool), and whether it is author-customizable at all.
- The input/navigation model: pure touch, D-pad / remote focus traversal, rotary encoder,
  gamepad, or mixed — and therefore whether a FOCUS / NAVIGATION ORDER is required in
  addition to spatial position.
- Localization: how multiple languages/scripts and locale variants are handled on these
  constrained UIs, and how layout switching is exposed.
- Constraints unique to the context: small screen / reduced key set, no physical feedback,
  safety lockouts (automotive), and security (scrambled secure PIN pads, no caching).
- What data the surface needs beyond a character mapping: display legends, icons, focus
  order, locale, grouping, key size/position for rendering, and accessibility.

DELIVERABLES
- A table: rows = the device contexts above; columns = "primary toolkit/framework",
  "layout defined by (format/tool/code)", "navigation model (touch/D-pad/encoder/gamepad)",
  "needs focus/navigation order?", "localization mechanism", "special constraint
  (safety/security/size)".
- A list of the requirements these embedded surfaces add ON TOP of mobile/desktop OSKs —
  especially non-touch navigation order, secure/scrambled layouts, safety lockouts, and very
  small reduced key sets. (The consolidated cross-surface metadata superset is assembled in
  the stakeholder/manufacturing prompt; here, report only the embedded-specific delta.)
- A section "Implications for an open layout model": what a portable model must express to
  drive an embedded on-screen keyboard (display legends + locale + focus/navigation order +
  reduced/variant layouts), and what should explicitly stay out of scope (e.g. the secure
  cryptographic behavior of a PIN pad, which is a security concern, not a layout concern).

REQUIREMENTS
- Cite primary sources where public (Qt Virtual Keyboard docs, LVGL docs, Android TV / tvOS
  on-screen keyboard guidelines, Tizen/webOS IME docs, Android Automotive input guidelines,
  PCI PIN security / EPP references).
- Where vendor details are proprietary/undocumented, say so explicitly and describe the
  general pattern instead of guessing specifics.
- Keep the focus on the keyboard/text-entry layer, not the whole device UI stack.
```

---

## Prompt 9 — Interchange formats & layout-authoring tools: the state of the art

```text
You are a systems researcher producing a comparative report for engineers who are creating a
new open, JSON-based, human-maintainable source format to describe keyboard layouts, which
must interoperate with existing standards and tools (especially Unicode CLDR/LDML Keyboard).
Be candid about overlap and redundancy risk.

GOAL
Survey the existing platform-independent interchange formats and the existing
layout-authoring source formats/tools, compare what each can express, and identify the
concrete gaps a new open model could justifiably fill.

COVER
1. Unicode CLDR / LDML Keyboard (the primary standard):
   - The current version and the major "Keyboard 3.0" redesign: its structure (keys, layers,
     forms, the "flicks", transforms, reorders, markers, display/displayMap, variables,
     import).
   - What it models well (platform-independent description, transforms for complex scripts,
     reordering for Indic/Brahmic, markers).
   - Its intended scope and explicit non-goals; what it does NOT focus on (dynamic legends,
     pedagogy, AI/assistant metadata, device-specific exports, control surfaces).
   - The state of tooling/adoption around it (who consumes LDML keyboards).
2. Other source/authoring formats and tools, for each: input syntax (JSON/YAML/DSL), what it
   can express, which OS targets it exports to, and conversion tooling:
   - kalamine (YAML-based, exports to XKB/Windows/macOS).
   - kbdgen (Divvun/SIL, YAML, multi-target including mobile).
   - KLFC (Keyboard Layout Files Creator).
   - Keyman / .kmn (and KMX) — including complex-script and mobile reach.
   - KbdEdit, and Microsoft KLC (as already covered, only for comparison).
   - Karabiner-Elements (macOS remapping/JSON) — clarify remap vs layout.
   - Any AutoHotkey / espanso / text-expansion approaches only as adjacent context.
3. Complex-script needs that any serious model must handle: dead-key chains, contextual
   transforms, reordering, normalization, and how LDML addresses them.

DELIVERABLES
- A master feature/coverage matrix: rows = capabilities (base mapping, shift levels, AltGr,
  dead keys, chained dead keys, multi-char output, transforms/contextual rules, reordering
  for complex scripts, markers/variables, per-key display legends, locale/multi-locale,
  mobile/touch output, dynamic-legend metadata, accessibility metadata, OS export targets,
  human-readable diff-friendly source, schema validation); columns = LDML Keyboard 3.0,
  kalamine, kbdgen, KLFC, Keyman, KLC/keylayout/XKB (grouped as "native OS").
- An honest "gap analysis" in TWO STEPS: (1) INDEPENDENTLY identify, from the evidence, which
  needs are already well covered by LDML and existing tools (and would be redundant to
  reinvent) and which are genuinely under-served — do not assume a conclusion; (2) THEN
  compare your independent findings against this project's hypothesis that the under-served
  areas are dynamic legends, learning/pedagogy metadata, AI-assistant typing knowledge,
  device/control-surface exports, and a single human-maintainable source that fans out to all
  targets including LDML — and state explicitly where you agree or disagree, with reasons.
- A recommendation: for a new open model, what it should DELEGATE to LDML (and map to), vs
  what higher-level layer it can legitimately add on top.

REQUIREMENTS
- Cite primary sources (the Unicode LDML Keyboard / TR35 keyboard spec, CLDR release notes,
  and each tool's official docs/repo).
- Be precise about the LDML Keyboard 3.0 vs older LDML keyboard differences and the current
  version/status.
- Explicitly call out redundancy risk: where a new format would merely duplicate LDML.
- This prompt is broad: if you must trade off, prioritize DEPTH on LDML Keyboard 3.0 and the
  gap analysis over exhaustive coverage of every minor tool; summarize the long tail briefly.
```

---

## Prompt 10 — Input Method Editors (IME) and complex-script input

```text
You are a systems researcher producing a technical report for engineers designing an open
keyboard layout model. They need to understand text input that is NOT "one key = one
character" — CJK, Indic/Brahmic, Arabic/Hebrew, Southeast Asian scripts — so the model can
decide what it represents itself, what it expresses via transforms/reordering, and what it
must DELEGATE to a stateful input method.

GOAL
Map how complex-script and multi-stage text input works across platforms, and draw a precise
boundary between the keyboard-layout layer, the transform/reorder layer, and the full IME
layer (dictionaries, candidates, conversion).

COVER IN DETAIL
1. What an IME is and why it exists: the composition / pre-edit -> candidate selection ->
   commit pipeline, and how it differs conceptually from a static keyboard layout.
2. Per-OS IME frameworks and how they relate to the layout:
   - Windows: Text Services Framework (TSF) and legacy IMM32.
   - macOS / iOS: Input Method Kit (IMK).
   - Linux: IBus, Fcitx5, m17n, uim (and legacy SCIM) — and how they sit above XKB.
   - Android: InputMethodService and the soft-keyboard IME model.
3. Major complex-script input methods and exactly what each needs:
   - Chinese: Pinyin, Wubi, Cangjie, Zhuyin/Bopomofo, stroke — phonetic vs shape-based, the
     role of a dictionary and candidate list.
   - Japanese: romaji -> kana -> kanji conversion, direct kana input, the conversion engine.
   - Korean: Hangul composition automata, jamo combining (this is algorithmic, not
     dictionary-based — clarify the difference).
   - Indic / Brahmic: InScript layouts, phonetic input, conjuncts, reordering and Unicode
     normalization, and how LDML reorder/transform models this.
   - Arabic / Hebrew: layout-level input vs rendering-level contextual shaping (make the
     distinction explicit), diacritic/harakat input, RTL handling.
   - Southeast Asian: Thai (syntactic input rules / WTT), Khmer, Myanmar, Lao — reordering
     and input validation issues.
4. The decision boundary, made explicit:
   - what belongs to the KEYBOARD LAYOUT (key -> base character or dead key);
   - what a layout STANDARD can express via TRANSFORMS and REORDERS (the LDML Keyboard 3.0
     transform/reorder/marker model) without a dictionary;
   - what genuinely requires a STATEFUL IME with dictionaries, candidate selection or
     conversion (and is therefore out of scope for a layout description, only referenceable).
5. How far LDML Keyboard 3.0 goes for complex scripts (transforms, reorders, markers,
   normalization) and where it deliberately stops. (Do not re-describe LDML's overall
   structure — that is covered by the interchange-formats prompt; focus only on its
   complex-script transform/reorder capabilities and their limits.)
6. Adjacent-but-distinct features: predictive text, autocorrect, transliteration input,
   handwriting/voice — note them and exclude from the layout-model core.

DELIVERABLES
- A table: rows = script families / languages above; columns = "typical input method(s)",
  "provided by layout layer", "expressible via transforms/reorders", "requires full IME
  (dictionary/candidates/conversion)".
- A crisp three-way decision diagram (in text): LAYOUT vs TRANSFORMS/REORDERS vs FULL IME —
  with the criteria that place a feature in each bucket.
- A section "Implications for an open layout model": concretely, how far the model should go
  (e.g. represent base mapping + dead keys + LDML-style transforms/reorders, and reference
  rather than embed full IMEs), and what declarative metadata it needs so a layout can state
  "requires IME X" or "ships transform set Y" and remain interoperable with LDML.

REQUIREMENTS
- Cite primary sources (Microsoft TSF docs, Apple IMK docs, IBus/Fcitx docs, Android IME
  docs, the Unicode LDML keyboard transforms/reorder specification, and Unicode UAX #15
  normalization).
- Keep the boundary between input methods and rendering/shaping explicit and correct.
- Be precise about which behaviors are algorithmic (e.g. Hangul) vs dictionary-driven.
```

---

## Prompt 11 — Existing de jure keyboard standards and legend/keycap standards

```text
You are a systems researcher producing a technical report for engineers designing an open
keyboard layout model. They must position the model relative to, and ideally map to or
reference, the existing OFFICIAL (de jure) keyboard standards rather than reinvent their
concepts and terminology.

GOAL
Catalog the formal national and international keyboard standards, the concepts they define,
and the standards for keycap legends/symbols, so the open model can adopt established
vocabulary, allow conformance claims, and avoid duplicating standardized terms.

COVER IN DETAIL
1. ISO/IEC 9995 ("Information technology — Keyboard layouts for text and office systems"):
   its multipart structure and what each part governs (e.g. 9995-1 general principles,
   functional sections and the key reference grid; 9995-2 alphanumeric section; 9995-3 the
   common secondary group / complementary layout; 9995-7 symbols for control functions;
   9995-8 numeric section; 9995-9, -10; 9995-11 dead keys). Define its core CONCEPTS:
   functional zones/sections, levels, groups, the secondary group selector, the key
   reference grid and key numbering. Explain how a layout claims conformance.
2. National / regional de jure standards, with edition/year and scope:
   - France: AFNOR NF Z71-300 (2019) — azerty and bépo.
   - Germany: DIN 2137 (T1 / T2 / T3, and E1).
   - Japan: JIS X 6002 / X 6004.
   - USA: the ANSI-INCITS keyboard arrangement standard — confirm its exact designation
     (e.g. INCITS 154) and its lineage rather than assuming one.
   - Others where relevant: GOST (Russia), Nordic/other national standards.
3. Physical form-factor and geometry references: ANSI vs ISO vs JIS vs ABNT physical forms,
   the ISO/IEC 9995-1 key reference grid and key numbering, and how physical positions are
   officially designated.
4. Keycap legend / symbol standards: ISO/IEC 9995-7 standardized graphic symbols for control
   functions, legend positioning conventions, multi-legend keys, and any keycap-marking
   norms.
5. Relationship to de facto OS layouts (Windows/macOS/XKB) and to Unicode LDML Keyboard:
   what each governs, where they overlap, and where they conflict.

DELIVERABLES
- A standards table: standard -> scope -> key concepts defined -> current edition/year ->
  relationship to OS layouts and to LDML.
- A glossary of ISO/IEC 9995 vocabulary (functional zone/section, level, group, secondary
  group, key reference grid, key number) with precise definitions.
- A section "Implications for an open layout model": which ISO/IEC 9995 concepts the model
  should adopt or map to (levels, groups, functional sections, key numbering), how a layout
  can DECLARE conformance to a given standard (e.g. "conforms to ISO/IEC 9995-2" or
  "AFNOR NF Z71-300"), and which terminology to reuse rather than reinvent.

REQUIREMENTS
- Cite the standards directly (ISO/IEC 9995 parts and the national bodies AFNOR, DIN, JIS,
  ANSI/INCITS, GOST) with editions/years.
- Distinguish what is normative vs informative.
- Where a standard is paywalled, rely on official summaries/abstracts and reputable secondary
  sources, and say so.
```

---

## Prompt 12 — Designing a durable, extensible format with a real conformance regime

```text
You are a systems researcher producing a technical report for engineers designing an open,
JSON-based keyboard layout format meant to last decades and be implemented by many
independent parties. They need format-engineering guidance, not keyboard specifics.

GOAL
Define how to design the format and its schema so it is durable, extensible, hand-
maintainable, and trustworthy — including its versioning, extensibility, conformance and
test-suite regime — drawing concrete lessons from successful long-lived data formats.

COVER IN DETAIL
1. Schema & file-design best practices for longevity: choice of JSON Schema draft and its
   tradeoffs, stable field ordering for clean human diffs, explicit naming, shallow nesting,
   compact-vs-verbose notation, and avoiding generator-only/opaque encodings.
2. Versioning & evolution: versioning the SPECIFICATION (semver) vs versioning FILES
   (schemaVersion); additive-only evolution; backward and forward compatibility; the
   "processors must ignore unknown fields" rule; deprecation policy; feature detection.
3. Extensibility & namespacing: how to allow vendor/private extensions without forking
   (prefix conventions, namespaced extension objects, an extension REGISTRY), and how
   successful formats run their extension registries.
4. Internationalization of the format itself: localized names/descriptions, locale tagging
   via BCP 47, UTF-8 and Unicode normalization expectations for string values.
5. Conformance design: normative language (RFC 2119 MUST/SHOULD/MAY); conformance LEVELS or
   PROFILES (e.g. core vs full); the distinct meanings of "a conforming FILE" vs "a
   conforming PROCESSOR/exporter/importer".
6. Test-suite & validation design: golden/fixture files, round-trip (export->import) tests,
   a reference validator, machine-readable conformance test data, and how mature standards
   ship test suites (e.g. CLDR test data, the JSON Schema test suite, W3C test suites,
   OpenType conformance).
7. Transferable lessons from long-lived formats: Unicode/CLDR, OpenType (and feature files),
   USB HID report descriptors, glTF (and its extension registry/process), OpenAPI, SVG —
   what made each durable and widely implemented, plus notable design mistakes to avoid.

DELIVERABLES
- A concrete checklist of format-design rules the model should adopt (versioning scheme,
  unknown-field policy, extension/namespacing mechanism, conformance levels, i18n rules).
- A proposed conformance + test-suite model: the minimum fixtures, validators and
  round-trip tests the format needs to be trustworthy.
- A compact comparison of how 4–5 successful formats handled versioning and extensibility,
  each with the transferable lesson.

REQUIREMENTS
- Cite the actual specifications (JSON Schema, BCP 47, RFC 2119, Semantic Versioning, the
  glTF extension registry, CLDR/UTS) and be concrete rather than generic.
- Prefer recommendations that keep files hand-maintainable and diff-friendly.
```

---

## Prompt 13 — Governance, the standardization path, and the adoption playbook

```text
You are a strategy researcher producing a report for the team behind a new open keyboard
layout standard. They want to understand, concretely, how to take an open format from a
single-author draft to a standard the industry treats as unavoidable.

GOAL
Map the realistic standardization venues, governance and IP/licensing models, and adoption
mechanics for an open technical standard — with case studies of what won and what failed —
and recommend a concrete path for a keyboard-layout model that bridges Unicode LDML.

COVER IN DETAIL
1. Standardization venues and their processes, costs and payoffs:
   - Unicode Consortium (how CLDR / LDML Keyboard is governed) — directly relevant since the
     model bridges LDML;
   - ISO/IEC JTC 1, especially SC 35 (User Interfaces), which owns ISO/IEC 9995 — a natural
     home for keyboard work;
   - W3C (Community Group -> Working Group -> Recommendation);
   - IETF (RFC), ECMA, OASIS.
   For each: entry requirements, IP rules, timeline, and what membership/liaison costs.
2. Governance models for an open spec: BDFL vs steering committee vs neutral foundation;
   how Unicode, W3C, the Linux Foundation / OpenJS / CNCF structure governance; membership
   tiers; decision and change-control processes; the value of a neutral host.
3. IP & licensing for a standard: royalty-free vs FRAND patent policy and why RF matters for
   adoption; copyright on the spec text (e.g. CC BY) vs on reference implementations (e.g.
   EUPL/MIT); trademarks and certification marks ("OKLM-conformant").
4. The adoption playbook & network effects: crossing the chasm with a reference
   implementation + a killer use case + early adopters; sequencing "authors first, then
   industry"; getting OS vendors, OEMs and tool authors to consume the format; bundling vs
   standalone; building an extension registry and a conformance/certification program.
5. Case studies — what won and what failed, with the transferable lesson each:
   e.g. Unicode vs legacy code pages; OpenAPI/Swagger; glTF; USB-IF; WebM/Matroska. Include
   at least one standard that struggled or failed, and analyze WHY from the evidence rather
   than assuming the cause. If you examine a national keyboard standard with weak uptake
   (e.g. AFNOR NF Z71-300), determine the actual adoption barriers from sources rather than
   presuming complexity.
6. Concrete near-term governance steps for a young project: neutral domain/home, license
   decision, contribution model (CLA/DCO), public spec repo, versioned release cadence, and
   an extension registry.

DELIVERABLES
- A venue comparison table with a recommended realistic path (noting the SC 35 / Unicode
  liaison angle) and why.
- A proposed governance + IP/licensing model suited to a royalty-free, broadly adoptable
  standard.
- A sequenced adoption playbook (milestones from draft to industry uptake) with the specific
  network-effect levers at each stage.
- 5 case-study lessons (won/failed), each reduced to one transferable principle.

REQUIREMENTS
- Cite official process documents (Unicode policies, the W3C Process, ISO/IEC JTC 1 / SC 35,
  IETF) and reputable analyses of standards adoption.
- Be candid about cost, time and failure modes; avoid hype.
```

---

## Prompt 14 — Consolidated stakeholder requirements and the physical manufacturing pipeline

```text
You are a requirements researcher producing a report for engineers designing an open
keyboard layout model. To become unavoidable, the model must satisfy the real needs of every
stakeholder that consumes a layout description, AND feed real physical production.

GOAL
Gather, stakeholder by stakeholder, what each party actually needs FROM a keyboard-layout
description, and document the physical manufacturing pipeline (keycap legends, stickers,
dynamic legends) and the data it requires — then consolidate into the MASTER superset of data
the model's metadata/legend layer must support. This prompt is the consolidator: it should
subsume and unify the surface-specific metadata findings from the mobile/peripheral and the
embedded on-screen keyboard prompts, not merely repeat them.

COVER IN DETAIL
1. Stakeholder requirements — for each, what they consume and what data they need beyond a
   bare key->character map:
   - OS vendors (verified layout metadata, shippable layouts);
   - keyboard / laptop OEMs (legend generation, keycap sets, regional variants, dynamic
     displays);
   - component makers (keycap printing/engraving, sticker producers);
   - enterprise IT / MDM (deploy, audit and standardize layouts at scale — e.g. Intune,
     Group Policy, other MDM);
   - application vendors (show correct shortcuts and physical-key hints for the user's actual
     layout);
   - remote desktop / virtualization vendors (preserve keyboard intent across platforms);
   - accessibility tooling (labels, grouping, scanning order, AAC);
   - education / typing-trainer tools (lessons, progressive disclosure, hints);
   - AI assistants / local agents (deterministic "how do I type X?" knowledge).
2. The physical manufacturing pipeline and its data needs: keycap legend methods (pad
   printing, dye-sublimation, laser etching, double-shot), engraving, sticker sheets; the
   legend positioning grid, multi-legend keys and sublegends, color/contrast; the ISO/IEC
   9995-7 control-symbol set; and dynamic/e-ink legend hardware (e.g. Stream Deck, Nemeio /
   Flux) data needs.
3. The specific data each output needs that a pure character map lacks: display legends
   (short/long), icons, colors, physical positioning and dimensions, locale, priority,
   accessibility labels, engraving vectors.
4. Where these requirements overlap and where they conflict (e.g. compact legend vs full
   info), and how a single source model can fan out to all of them.

DELIVERABLES
- A stakeholder requirements matrix: row = stakeholder; columns = "what they consume",
  "data fields needed beyond char mapping", "target output/format", "priority".
- A consolidated SUPERSET list of all non-character data fields the union of stakeholders
  requires (the fields the model's metadata/legend/accessibility layer must be able to hold).
- A manufacturing-pipeline section: each production method and the exact data it consumes.
- A section "Implications for an open layout model": the minimal metadata/legend/
  accessibility layer that satisfies the union of stakeholders, and what should be CORE vs
  OPTIONAL.

REQUIREMENTS
- Cite public sources where they exist (MDM/Intune keyboard deployment docs, keycap
  manufacturing references, ISO/IEC 9995-7, dynamic-keyboard vendor docs).
- When a requirement is inferred rather than documented, say so explicitly.
- Keep the focus on data the layout MODEL must carry, not on each vendor's internal tooling.
- This prompt is broad: prioritize a COMPLETE, well-reasoned superset of data fields over
  exhaustive per-vendor detail; if you must trade off, keep the superset and the
  manufacturing data needs, and summarize individual stakeholders concisely.
```

---

## Prompt 15 — Keyboard input on the Web platform (UI Events, Keyboard Map API)

```text
You are a systems researcher producing a technical report for engineers designing an open
keyboard layout model. The web platform is a first-class target (web-based keyboard testers,
IDEs, remote desktops and apps run in browsers), and it has its OWN keyboard input model that
differs from native OS layouts.

GOAL
Document how keyboard input and layout information work on the web platform, what a browser
exposes to JavaScript about the physical key and the produced character, and the limits — so
the model can drive web testers and web apps faithfully.

COVER IN DETAIL
1. The W3C UI Events model: KeyboardEvent.code (physical-position values from the UI Events
   "code" spec), KeyboardEvent.key (the resolved, layout-dependent value), the legacy
   keyCode/which/charCode, and the relationship between them.
2. The `code` value set: how it enumerates physical keys (e.g. KeyA, Digit1, IntlBackslash,
   IntlRo, IntlYen), its alignment with USB HID usages and with ANSI/ISO/JIS physical keys,
   and the keys it cannot distinguish.
3. The Keyboard Map API: navigator.keyboard.getLayoutMap() and KeyboardLayoutMap — what it
   returns, how it maps `code` to the current layout's produced glyph, browser support and
   gaps, and the privacy/fingerprinting considerations that limit it.
4. Keyboard Lock (navigator.keyboard.lock()) and IME interaction in the browser
   (compositionstart/update/end, isComposing) — how dead keys and composition surface to JS.
5. What the web platform does NOT expose: the full layout table, modifier resolution beyond
   the event, and why a web tester usually needs its own layout data file rather than relying
   on the browser.
6. Practical implications for a web-based keyboard tester: how to know which physical key was
   pressed regardless of layout (`code`), how to show what a given layout would produce, and
   how to reconcile this with a layout description shipped as data.

DELIVERABLES
- A precise explanation of `code` vs `key` vs keyCode, with a small table of examples across
  an ANSI, an ISO and a JIS keyboard (same physical key: what `code` and `key` report).
- A capability/limits summary of getLayoutMap() and Keyboard Lock (support, gaps, privacy).
- A section "Implications for an open layout model": what the model must provide so a browser
  tester can map physical keys (`code`) to the layout's glyphs and legends without depending
  on the OS layout, and how to align the model's physical key ids with UI Events `code`.

REQUIREMENTS
- Cite primary sources (W3C UI Events spec, the UI Events `code`/`key` value specs, MDN, the
  Keyboard Map API and Keyboard Lock specs, and browser support data).
- Distinguish clearly physical-position info (`code`) from produced-character info (`key`).
- Note browser/version differences and where support is inconsistent; if a fact is
  fast-changing, note its date.
```

---

## Prompt 16 — Physical keyboard geometry description formats

```text
You are a systems researcher producing a technical report for engineers designing an open
keyboard layout model whose schema describes physical keys with geometry (row, column,
width). They need to understand the existing de-facto formats for describing the PHYSICAL
geometry and shape of keyboards, separately from the character mapping.

GOAL
Survey how keyboard PHYSICAL geometry (key positions, sizes, shapes, rotation, matrix and
form factor) is described by existing tools and formats, compare them, and recommend what the
model should adopt or map to for its geometry layer.

COVER IN DETAIL
1. keyboard-layout-editor.com (KLE) JSON: the de-facto hobbyist format for physical layouts —
   its coordinate model, key sizes/positions, rotation, stepped/secondary keys, legend
   placement, and its known quirks and limitations.
2. QMK info.json "layout" macros and LAYOUT data: how QMK / QMK Configurator describe key
   positions and the electrical matrix, and the relationship to KLE.
3. VIA / Vial keyboard definitions: how they describe physical layout and option/variant keys
   (e.g. ISO vs ANSI bottom row, split spacebar).
4. Standardized physical references: the ISO/IEC 9995-1 key reference grid and key numbering;
   the ANSI/ISO/JIS/ABNT form factors and their differing keys; and the standard key-name
   schemes (e.g. XKB names like AD01/AC01) used to identify positions.
5. Other relevant sources: the XKB geometry component, keyboard CAD/tooling exports, and
   keycap profile data only as far as legend sizes/placement are concerned.
6. Non-character keys in geometry: how these formats represent function keys, the numeric
   keypad, navigation/media keys, and physically-present-but-OS-invisible keys (e.g. an Fn
   key) — which the layout model must also be able to place.

DELIVERABLES
- A comparison table: rows = KLE JSON, QMK info.json, VIA/Vial, XKB geometry, ISO/IEC 9995-1
  grid; columns = "coordinate/units model", "rotation / odd shapes?", "encodes matrix?",
  "form-factor / variant handling", "legend/label placement", "tooling/ecosystem".
- A clear account of how the same physical key is identified across these schemes, and how to
  reconcile them with USB HID usages and UI Events `code` values.
- A section "Implications for an open layout model": a recommended geometry representation
  (units, origin, rotation, width/height, variant keys, stable physical key ids) that is
  hand-maintainable and can export to the formats above, including how to handle ANSI/ISO/JIS
  differences and non-character keys.

REQUIREMENTS
- Cite primary sources (KLE docs/repo, the QMK info.json reference, VIA/Vial definition docs,
  ISO/IEC 9995-1, XKB geometry docs).
- Be explicit about each format's limitations and where they disagree.
- Keep geometry (physical) cleanly separated from mapping (characters) throughout; if a fact
  is fast-changing, note its date.
```

---

*Dernière mise à jour : 2026-06-07*
