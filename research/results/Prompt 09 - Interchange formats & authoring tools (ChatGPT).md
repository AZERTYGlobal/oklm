# Comparative Report on Keyboard Layout Interchange and Authoring Formats

## Executive assessment

The evidence does **not** support creating a new low-level keyboard semantics format that competes with Unicode CLDR/LDML Keyboard for platform-independent layout description, complex-script transforms, reordering, marker-based dead-key state, and touch/hardware abstraction. Since CLDR v45, the Unicode specification has had a major “Keyboard 3.0” rewrite with an explicitly platform-independent model, and the current stable CLDR/UTS #35 line is **48.2**. That model already covers the hardest parts of serious keyboarding: hardware and touch forms, layered mappings, long-press/multi-tap/flick gestures, contextual transforms, reorder rules for Brahmic-style orthographic syllables, marker handling across normalisation, and backspace behaviour. Re-inventing those semantics would create considerable redundancy risk. citeturn1view0turn15view0turn10view1turn10view2turn12view1turn14view3turn13view4

Where the ecosystem is weaker is **not** the core keystroke model, but the authoring layer above it. Existing single-source tools are fragmented by target set and capability: kalamine is elegant and human-friendly but intentionally modest; kbdgen reaches many desktop and mobile targets but its public docs are dated and it still documents CLDR output as missing; KLFC is powerful for desktop-native exports and remapping actions but is not a standards-based interchange format; Keyman is extremely expressive and mature, but its classic `.kmn` language is engine-specific and its mobile model uses separate JSON touch-layout files. Public evidence of LDML tooling/adoption is strongest around Keyman; Unicode’s own CLDR keyboard intake process is still documented as being under development. citeturn18view1turn17view0turn26view0turn22view0turn25view0turn29view0turn31view0turn35view0turn35view2turn36search0turn38search4turn8search0turn8search13

The strongest justification for a new open, JSON-based, human-maintainable model is therefore as a **higher-level authoring format and metadata envelope**: something that can compile **down to LDML** for semantic interchange, while also fanning out to native OS targets and runtime-specific ecosystems, and adding metadata that LDML intentionally does not attempt to standardise. The best candidates for that added layer are dynamic legend metadata, pedagogy and typing-knowledge metadata, assistant-facing knowledge, accessibility annotations, target build/export manifests, and device/control-surface descriptions that are explicitly outside LDML’s core scope. citeturn15view0turn17view0turn22view0turn29view0turn35view4turn42search1turn42search17

## Unicode CLDR LDML Keyboard

### Current status and the Keyboard 3.0 redesign

As of **7 June 2026**, Unicode lists **CLDR 48.2** as the latest stable release; the corresponding stable keyboard specification is **UTS #35 Part 7: Keyboards, Version 48.2**. Unicode’s current spec states that a major rewrite called **“Keyboard 3.0”** was introduced in **CLDR v45**, that it was too extensive to keep compatible with earlier keyboard DTDs, and that the older `ldmlKeyboard.dtd` remains available but is no longer updated. In other words, the old keyboard format is effectively frozen, while the `keyboard3` model is the live line. citeturn1view0turn15view0

Unicode also describes the intent shift behind the redesign: the goal changed from faithfully reflecting older platform-specific artefacts toward a **platform-independent** format in which a keyboard file defines the characters that should result from typing on a given hardware arrangement. That change matters for your project, because it means LDML Keyboard 3.0 is already positioned as the standards-track interchange model rather than a mere archival mirror of native formats. citeturn0search7turn15view0

### What Keyboard 3.0 can model

The `keyboard3` model is broad. It separates **physical form** from **mapping logic**. `form` and `scanCodes` define hardware arrangements such as `us`, `iso`, `jis`, `abnt2`, `ks`, while `layers` bind a given form (or `touch`) to one or more `layer` definitions. The specification explicitly supports both hardware and touch, allows multiple touch layouts with `minDeviceWidth`, and recommends always having a hardware form because touch devices may still connect to physical keyboards. CLDR also defines implied imports for standard forms and implied key sets, which reduces boilerplate and makes reuse/import part of the model rather than an afterthought. citeturn10view2turn10view1turn15view3

At the key level, Keyboard 3.0 can express plain output, layer switches on touch keyboards, long-press menus, multi-tap cycles, and **flick** gestures. The `flicks/flick/flickSegment` model encodes directional gesture paths, while long-press and multi-tap are attached to keys by ordered references to other keys. That is important because it means LDML is not limited to a “desktop keymap plus deadkeys” conception; it already includes a significant portion of modern touch-keyboard interaction design. citeturn10view3turn10view4turn15view3

Keyboard 3.0 also includes **variables** (`string`, `set`, `uset`) and a transform system that is much richer than simple dead-key tables. `transform` rules use a regex-like matching syntax with variables and replacement syntax; `transformGroup` sequences processing stages; `reorder` rules exist specifically to convert typed order into stored order for complex orthographies; and backspace behaviour can itself be rule-driven. The spec is explicit that transforms are meant to support dead keys, character reordering, error indication, and backspace handling in a way that stays readable as source data. citeturn12view0turn12view1turn12view3turn13view0turn13view1turn13view4turn14view3

The most distinctive feature is probably **markers**. A marker is invisible state carried in context, designed especially to support dead keys and other stateful interactions without emitting visible text. The spec also defines how markers behave through normalisation: markers are stripped, text is normalised, and then markers are reattached according to a “gluing” algorithm so authors can preserve intended adjacency across combining-mark reordering. That is a serious answer to a real keyboard-engine problem, especially for combining sequences and complex scripts. citeturn13view5turn11view0turn11view3

Per-key display strings are also part of the model. The spec’s examples show `displays/display` mapping invisible output such as markers to visible labels such as `^` or `{`, allowing a keyboard to show a sensible legend without conflating what is displayed with what is inserted into text. That is useful, but it remains **static presentation data**, not a general adaptive legend system. citeturn10view3turn12view2

### What LDML does well and what it does not try to do

LDML Keyboard 3.0 is strongest where a standard should be strongest: it gives a platform-independent description of how keystrokes become Unicode text, including touch/hardware abstraction, transforms, reorder logic, normalisation interaction, and marker state. The spec’s reorder model is explicitly designed for situations where the typing order of characters differs from their stored order, including pre-base and tertiary ordering in orthographic-syllable models such as Devanagari and related Brahmic scripts. Backspace is not left to platform guesswork: there is a dedicated `transforms type="backspace"` stage, and the spec warns that relying on the implied default backspace may produce poor user experience. citeturn14view1turn14view4turn13view4

Its intended scope is also explicit. Unicode says LDML Keyboard is an **interchange format**, and therefore it is expected that implementations will compile or transform the source into a more compact runtime format. It also explicitly leaves **platform-specific frame keys** such as Fn, numpad-specific behaviour, IME swap keys, cursor keys, and similar control surfaces out of scope. Those are precisely the places where a new higher-level model could add value without duplicating LDML semantics. citeturn15view0

What LDML does **not** currently focus on is equally important. The spec says that accessibility-specific features or architectural designs are **“not yet included”** in this revision. I also do not find first-class constructs in the published Part 7 spec for pedagogical metadata, fingerings, typing difficulty, learning sequences, assistant explanations, ergonomic annotations, or rich dynamic-legend metadata beyond static display mappings and keyboard-layer state. That absence appears deliberate rather than accidental: the spec is mostly about text-generation semantics and implementation-independent structure, not teaching systems or adaptive UI policy. citeturn15view0turn15view1turn15view2turn15view4

### Tooling and adoption around LDML

Unicode maintains a **CLDR Keyboard Working Group**, and CLDR has published **keyboard intake procedures**, but that intake documentation still says the contribution guide is in development. That is a useful indicator: the standard exists, but the surrounding repository and contribution machinery are still maturing. citeturn8search13turn8search0

The clearest public consumer today is **Keyman**. Keyman’s documentation says it supports CLDR/LDML keyboards; Keyman Developer 17 introduced LDML XML editing/compilation support; current Keyman tooling can compile LDML `.xml` keyboards, and the LDML compiler generates Keyman binary output. Keyman’s docs also show LDML as a first-class file type in the product. Public evidence for other production consumers is comparatively sparse in the sources reviewed here, so the honest assessment is: **the standard is real and technically substantial, but the public multi-vendor tooling ecosystem around it is still thin**. citeturn8search3turn38search1turn38search2turn38search3turn38search9

## Other source formats and tools

### Kalamine

Kalamine is a **text-based, cross-platform keyboard layout maker**. Its current documentation centres on **TOML** source files with ASCII-art layer templates, even though some installation commands still mention “YAML/TOML”; in practice, the official examples are `.toml`, not YAML. It is especially attractive as a human-maintainable source because the source emphasises directly editable base, shift, AltGr, and dead-key layers rather than a verbose AST-like structure. citeturn17view0turn18view1turn19view0

What it can express is intentionally narrower than LDML or Keyman. It handles base and shift levels, AltGr, a library of standard dead keys, one configurable “1dk” custom dead key, and even **chained dead keys** via the `1dk` layer. But its own docs warn that chained dead keys are **not supported by MSKLC**, requiring KbdEdit for a Windows build in that case. That warning is revealing: kalamine is a practical authoring/export tool, but the moment you push into edge-case statefulness, native target differences start showing through. citeturn20view4turn20view2turn20view1

On export, kalamine is strong for native desktop targets. It builds Windows user/admin variants (`.ahk`, `.klc`), macOS `.keylayout`, Linux XKB artefacts (`.xkb_keymap`, `.xkb_symbols`), and a web JSON output. It also ships helper tools such as `wkalamine` and `xkalamine` to package or install layouts more cleanly on Windows and Linux. That makes it a very good example of the “single human-maintainable source that fans out” idea — but only across the subset of targets it supports, and without LDML output. citeturn17view0turn18view2

### kbdgen

kbdgen is explicitly pitched as a tool that builds keyboard packages for many platforms from a **single, simple text-file definition**, and its user docs say layout files are **YAML** inside `.kbdgen` bundles. A bundle contains `project.yaml`, a `layouts` folder, a `targets` folder and resources. Layout YAML can be target-specific, split by platform and layer, and keyed by BCP 47 language tag. citeturn22view0turn26view0

In documented form, kbdgen handles desktop layers, **nested dead keys**, transforms associated with dead-key termination, mobile **longpress** definitions shared by Android and iOS, and per-target configuration. Its supported outputs include Linux (X11, m17n), macOS, Windows, ChromeOS, iOS/iPadOS, Android, SVG, and even an FST hit-error model. The important caveat is that its own README still says **CLDR keyboard definitions are missing but in the pipeline**, and its published docs page is timestamped **2022-09-23**, so the public documentation appears dated. For this report, I therefore treat only the documented features as confirmed. citeturn22view0turn25view0turn26view0turn27view0turn27view1turn27view2turn27view3

kbdgen is a strong precedent for a higher-level authoring format that spans both desktop and mobile. It is weaker as an interchange standard because its semantics are tool-driven, YAML-bundle-specific, and not a published neutral standard in the way LDML is. citeturn22view0turn26view0

### KLFC

KLFC is a **JSON-based** “Keyboard Layout Files Creator”. Its README says it exports to **XKB, PKL, KLC, keylayout, TMK and AHK**, stores layouts as JSON, and can import existing layouts from XKB, PKL, or KLC. This makes KLFC particularly relevant to your brief because it is already an open, JSON-based, human-editable authoring format with conversion both in and out. citeturn29view0

Its JSON model is richer than a plain keymap. Official docs list metadata, QWERTY shortcut behaviour, filters per output, explicit shiftlevels, keys, singleton keys, **custom dead keys**, variants, and mods/permutations. The key model can emit Unicode characters, ligatures, actions, modifiers, predefined dead keys, custom dead keys, and redirected keys. KLFC even includes an option for **chained dead keys in KLC**, albeit with a note that special compilation is required. citeturn31view0turn32view0turn29view0

That said, KLFC is primarily a **desktop/native/factory tool**. It is excellent for desktop targets and mechanical-keyboard firmware adjacency such as TMK, but it is not a standards-track interchange format, it does not model LDML’s reorder/marker/normalisation semantics, and it does not target mobile IMEs in the way kbdgen or Keyman do. Its latest listed release in the official repo is **1.5.7 from December 2021**, which suggests maturity but also some staleness. citeturn29view0

### Keyman and the classic `.kmn` model

Keyman is best understood as a **keyboard engine plus language plus tooling ecosystem**, not just a file format. Its classic source format is **`.kmn`**, a plain-text keyboard source file, compiled to **`.kmx`** for desktop. The `&targets` store lets one source compile to desktop `.kmx` and/or mobile/web `.js` targets, while touch layouts are described in a separate **JSON** `.keyman-touch-layout` file referenced by `&layoutfile`. Keyman Developer explicitly supports touch-hold keys, alternative layers, platform targets, and separate iOS/Android touch layouts. citeturn33search6turn35view2turn35view3turn36search0turn36search2turn35view4turn34search13

Expressiveness is where Keyman stands out. The rule language has stores, groups, context matching, deadkeys, system stores for platform/layer state, and read-only/context-processing groups. Official docs describe deadkeys as invisible placeholders stored in context; multiple deadkeys can coexist; and groups can be used for pre- and post-processing rules such as **reordering stacked diacritics**. That makes Keyman highly capable for complex-script and stateful logic, although its model is engine-specific rather than neutral interchange. citeturn35view1turn34search15turn34search18turn34search12turn35view0

For this report, one more detail matters: current Keyman also treats **LDML XML keyboards as a first-class source type**, compiling them through its LDML compiler. That means Keyman now spans both worlds: the legacy Keyman DSL for mature engine-specific authoring, and LDML for standards-based interchange. citeturn38search2turn38search3turn38search9turn38search4

### KbdEdit, Microsoft KLC, and native OS formats

**MSKLC** is Microsoft’s official Windows keyboard-layout creator. Microsoft describes it as a tool to create new layouts from scratch, base a new layout on an existing one, modify an existing `.KLC`, and package the resulting layout for installation. Its feature list also mentions support for **ligatures in the AltGr shift state**, which is one of the few official acknowledgements that native Windows layout data can go beyond one-character-per-key mapping. citeturn28search6turn39search5

**KbdEdit** is a Windows layout editor with broader import/export ambitions. Official snippets from its site/manual say it supports ligatures, customised dead keys, install-package generation, and import/export for KBE, KLC, layout DLL, and Mac `.keylayout` files. Its FAQ also says some dead-key restrictions are built into the **Windows keyboard layout model** itself, not just the editor. That is a useful caution for any proposed “unified” model: native targets do not all have the same semantic ceiling. citeturn39search3turn39search0turn39search6turn39search4

For grouped “native OS” formats more broadly: Windows `.KLC` is Windows-specific; macOS keyboard layout resources map virtual key codes to Unicode character codes; and Linux XKB/libxkbcommon provides a text keymap format with compose/dead-key support and a compiler/runtime ecosystem. These are indispensable **targets**, but they are not platform-independent interchange formats. They embody three different native models with three different abstractions. citeturn28search6turn43search5turn43search6turn43search2

### Remappers and text expanders as adjacent context

**Karabiner-Elements** is not a keyboard-layout interchange format. Its official docs describe JSON-based **simple** and **complex modifications** that change events by conditions, capture keyboard input events, and can even switch input source or keyboard type. That is powerful, but conceptually it is a **remapping/control-surface** system on macOS, not a semantic text-layout model. It belongs in the ecosystem discussion because a future higher-level model may want an export path to remappers, but it should not be confused with a layout standard. citeturn42search1turn42search3turn42search2turn42search12turn42search16turn42search17

**AutoHotkey** and **espanso** are also adjacent rather than equivalent. AutoHotkey’s official docs emphasise remapping, hotkeys and hotstrings; espanso’s docs centre on trigger/replacement “matches” in YAML for text expansion. They can be useful export targets or companion automation layers, but they do not encode keyboard-layout semantics in the same sense as LDML, KLC, XKB, or Keyman. citeturn44search4turn44search2turn44search0turn44search1turn44search7turn44search3

## Complex-script requirements any serious model must meet

A serious model must do more than map physical keys to code points. It must handle **dead-key chains**, **contextual transforms**, **normalisation interaction**, **reordering**, and **backspace semantics**. Otherwise it will look adequate for Latin layouts and then collapse for Indic, Burmese, Khmer, visually ordered keyboards, or even advanced Latin diacritic systems. citeturn12view1turn13view4turn14view3

LDML Keyboard 3.0 addresses these requirements directly. Dead keys are not ad hoc tables but marker-based state that can survive normalisation correctly; transform groups can rewrite context using a regex-like syntax; reorder rules assign order, tertiary, tertiary-base, and pre-base behaviour to typed characters; and backspace rules are explicitly programmable. The spec even warns authors that the default backspace transform often gives unintuitive behaviour and that keyboards should usually define their own backspace rules. That is precisely the level of treatment a cross-platform interchange standard needs. citeturn13view5turn11view3turn12view1turn14view1turn13view4

Keyman is the strongest non-LDML comparator for these needs. Its deadkeys are invisible contextual placeholders; multiple deadkeys may coexist; groups can do context-only processing; and official Keyman guidance explicitly discusses using groups for pre/post-processing such as reordering. In practice, Keyman has long been one of the most capable systems for complex-script keyboarding, but it achieves that through an engine-specific rule language rather than a neutral interchange model. citeturn35view1turn34search15turn34search18

By contrast, kalamine, kbdgen, KLFC, and native OS formats vary significantly. kalamine does dead keys and one configurable dead-key layer well, but does not document a general reorder engine. kbdgen documents nested dead keys, longpresses and transform mappings, but not a published general reordering model comparable to LDML’s `reorder`. KLFC supports custom dead keys and ligatures, but again not a first-class orthographic-syllable reorder system. Native OS formats can express some dead-key and compose behaviour, and Windows can handle some ligatures, but they are inconsistent and target-specific. That is why a new model should not try to derive its complex-script semantics from the “least common denominator” of native targets. It should treat **LDML as the semantic reference** and native formats as lossy or target-specific backends where necessary. citeturn20view4turn27view3turn31view0turn32view0turn39search5turn43search6

## Master feature matrix

The matrix below synthesises the capabilities documented in Unicode TR35 Part 7, official/project documentation for kalamine, kbdgen, KLFC, Keyman, Microsoft MSKLC, KbdEdit, Apple’s keyboard-layout resources, and libxkbcommon/XKB. Because the prompt asks for a single **“native OS”** column, that column necessarily compresses substantial platform differences; where Windows, macOS, and Linux differ materially, I mark the result as **△** rather than pretending there is one unified native model. **?** means the capability was not clearly documented in the official material reviewed here. citeturn15view0turn17view0turn26view0turn29view0turn35view0turn28search6turn39search3turn43search5turn43search6

| Capability | LDML Keyboard 3.0 | kalamine | kbdgen | KLFC | Keyman | native OS |
|---|---|---:|---:|---:|---:|---:|
| Base mapping | ✔︎ | ✔︎ | ✔︎ | ✔︎ | ✔︎ | ✔︎ |
| Shift levels | ✔︎ | ✔︎ | ✔︎ | ✔︎ | ✔︎ | ✔︎ |
| AltGr / alternate levels | ✔︎ | ✔︎ | ✔︎ | ✔︎ | ✔︎ | ✔︎ |
| Dead keys | ✔︎ | ✔︎ | ✔︎ | ✔︎ | ✔︎ | ✔︎ |
| Chained dead keys | ✔︎ | ✔︎ | ✔︎ | ✔︎ | ✔︎ | △ |
| Multi-character output | ✔︎ | ? | ✔︎ | ✔︎ | ✔︎ | △ |
| Contextual transforms / rules | ✔︎ | △ | △ | △ | ✔︎ | △ |
| Reordering for complex scripts | ✔︎ | ✘ | ✘ | ✘ | ✔︎ | ✘ |
| Markers / variables | ✔︎ | ✘ | ✘ | ✘ | ✔︎ | ✘ |
| Per-key display legends | ✔︎ static | △ static | △ static | △ static | ✔︎ static / touch | △ |
| Locale / multi-locale modelling | △ | △ | ✔︎ | △ | △ | △ |
| Mobile / touch output | ✔︎ | △ web only | ✔︎ | ✘ | ✔︎ | ✘ |
| Dynamic-legend metadata | ✘ | ✘ | ✘ | ✘ | △ engine-specific | ✘ |
| Accessibility metadata | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| OS export targets | ✘ | ✔︎ | ✔︎ | ✔︎ | △ Keyman runtimes | — |
| Human-readable, diff-friendly source | △ XML | ✔︎ | ✔︎ | ✔︎ | ✔︎ | △ |
| Schema / formal validation | ✔︎ | ? | ? | ? | ✔︎ | △ |

The important pattern is not that one column “wins” everything. It is that **LDML and Keyman cover the hard semantics**, while **kalamine/kbdgen/KLFC cover authoring and export convenience**. The real gap is in combining those two strengths **without duplicating the semantic layer that LDML already standardises**. citeturn12view1turn14view3turn35view1turn17view0turn26view0turn29view0

## Gap analysis

### What is already well covered and would be redundant to reinvent

The evidence supports saying that the following are **already well covered** enough that a new model should **not** attempt to replace them at the same abstraction level.

First, **platform-independent keyboard semantics** are already LDML’s job. That includes keys, layers, forms, imports, touch/hardware description, gestures, transforms, reorder rules, markers, and backspace. A new format that re-specifies those same semantics in JSON would mostly be a transcription exercise, with all the burden of staying semantically identical to Unicode over time. citeturn10view1turn10view2turn12view1turn13view4turn14view3turn15view0

Second, **complex-script handling** is already substantively addressed in LDML and, in engine-specific form, in Keyman. If a new model invents its own rule language for contextual transforms, reordering, normalisation/marker interaction, or backspace semantics, it will immediately duplicate the hardest and least stable part of the problem. That is the highest redundancy-risk area in your brief. citeturn11view3turn13view5turn14view1turn35view1turn34search15

Third, the idea of a **single source that exports to multiple targets** is not new. kalamine, kbdgen, KLFC, and Keyman all do versions of that already, each with different target coverage and trade-offs. So the justification for a new project cannot simply be “single source fans out”; that claim is already occupied. The stronger case would be “single open source that fans out to **LDML plus** the current long tail of native/runtime targets, in a way the existing tools do not.” citeturn17view0turn22view0turn29view0turn35view2

### What appears genuinely under-served

Several areas do look genuinely under-served.

One is a **human-maintainable, open, neutral authoring layer** that can target **LDML and non-LDML ecosystems together**. kalamine, kbdgen and KLFC are all useful, but none is currently the obvious neutral hub for “author once, emit LDML + Windows + macOS + XKB + mobile + remapper/control-surface outputs”. kbdgen’s own docs still list CLDR output as missing; kalamine does not target LDML; KLFC is desktop-centric and not standards-based. citeturn22view0turn17view0turn29view0

Another is **metadata above the keystroke-semantic layer**: dynamic legends, pedagogical hints, fingerings, learning sequences, transition advice, assistant-facing explanations, and explicit accessibility annotations. In the sources reviewed here, LDML does not define those as first-class concepts, and the mainstream authoring tools do not foreground them either. Some engines can display static touch labels or alternate layers, but that is not the same thing as a portable model for tutoring, explanation, or adaptive presentation. citeturn15view0turn15view1turn15view2turn15view4turn35view4turn36search7

A third is **device/control-surface export**. LDML explicitly excludes platform-specific frame keys and control surfaces; Karabiner-Elements, TMK adjacency via KLFC, and AutoHotkey live in a different conceptual world of remapping and event manipulation. There is room for a higher-level project to describe how one keyboard “family” should project into text layout, remapper rules, firmware layers, and perhaps companion automations — as long as it keeps those concerns modular instead of smuggling them into the LDML semantic core. citeturn15view0turn29view0turn42search1turn42search17turn44search4

### Comparison with the project hypothesis

I **agree** with the hypothesis that **dynamic legends**, **learning/pedagogy metadata**, **AI-assistant typing knowledge**, and **device/control-surface exports** are under-served. I do not find them addressed as first-class interoperable concepts in LDML Keyboard 3.0, and the source-authoring tools reviewed here treat them either not at all or only in narrow engine-specific ways. That is a legitimate innovation space. citeturn15view0turn15view4turn35view4turn42search1turn44search1

I **partly agree** with the hypothesis that there is room for **a single human-maintainable source that fans out to all targets including LDML**. The important qualifier is “including LDML”. Existing tools already cover fan-out for substantial subsets of targets, so a new project is only justified if it truly becomes a **meta-authoring layer above** LDML, native OS formats, and selected runtime/remapper targets — not if it merely becomes “yet another single-source exporter” for the same desktop formats others already handle. citeturn17view0turn22view0turn29view0turn35view2turn38search3

I **disagree** with any implied hypothesis that the new model should define its **own independent low-level transform/reorder/marker semantics**. That would be the clearest case of unnecessary duplication and the hardest to keep correct across scripts, normalisation behaviour, and future Unicode/CLDR evolution. In that area, a new model should either embed/map LDML concepts directly or compile to LDML as the canonical semantic form. citeturn11view3turn12view1turn14view3turn15view0

## Recommendation

A new open model is most credible if it is designed as a **layered authoring system**, not as a replacement standard for keyboard semantics.

The **semantic core** should be delegated to LDML wherever possible. That means key identities, hardware/touch forms, layer structure, key output, long-press/multi-tap/flick semantics, imports, variables, transforms, reorder rules, markers, normalisation-sensitive behaviour, and backspace rules should either map one-to-one to LDML or be represented internally in a way that can be losslessly compiled to LDML. If the new model cannot round-trip those concepts faithfully, it is intruding into territory that Unicode already owns better. citeturn10view1turn10view2turn12view0turn12view1turn13view4turn14view3turn15view0

Above that semantic core, a new model can legitimately add a **higher-level authoring layer**. That layer should probably be JSON-based if human diffability and tooling are core goals, but it should remain declarative. The most defensible additions are: richer metadata for display policy and dynamic legends; pedagogical metadata such as fingerings, mnemonic notes, difficulty, learning order, and practice prompts; assistant-oriented metadata such as “how to type X” explanations, alternate routes, and locale/script guidance; accessibility metadata; target manifests and packaging information; and explicit export sections for remappers, firmware layers, text expanders, or control surfaces. Those are all areas where LDML is either silent or explicitly out of scope. citeturn15view0turn42search1turn42search12turn44search1turn44search7

I would also recommend a **strict separation between author intent and target lowering**. In practice that means the new model should distinguish: the abstract logical key family; the LDML-semantic projection; per-target lowering hints for Windows/macOS/XKB/Keyman; and non-layout exports such as Karabiner or AutoHotkey. That separation would make it clear when a feature is semantic, when it is presentation-only, and when it is merely an export convenience. Existing tools blur these levels in different ways; your project could add value by clarifying them. citeturn17view0turn22view0turn29view0turn35view0turn42search1

Finally, if the project proceeds, it should publish its **redundancy boundaries** explicitly:

- It is **not** a replacement for LDML transforms/reorders/markers.
- It is **not** a re-specification of native OS formats.
- It **is** a higher-level authoring and metadata model that compiles to LDML and other backends.
- Its value lies in maintainability, richer metadata, and multi-target orchestration — not in redefining keystroke semantics. citeturn15view0turn17view0turn22view0turn29view0

## Open questions and limitations

The public documentation quality is uneven. kbdgen’s published docs are dated to 2022 and may understate current capabilities; KbdEdit pages were indexable in search snippets but returned fetch errors when opened directly; and public evidence of non-Keyman LDML consumers remains sparse in the sources reviewed. Where official documentation was unclear, I have marked the matrix conservatively with **△** or **?** rather than inferring hidden capabilities. citeturn25view0turn22view0turn39search0turn39search3turn8search3