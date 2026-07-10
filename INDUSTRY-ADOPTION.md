# Industry Adoption Strategy

## Positioning

OKLM should not be framed as a niche format for keyboard-layout hobbyists.

The correct framing is:

> OKLM is an interoperability model for the keyboard layer of modern computing.

Independent layout authors are the fastest first users, but the target adopters are:

- operating-system vendors;
- laptop and keyboard OEMs;
- dynamic-key device makers;
- browser and application vendors;
- remote desktop, virtualization and cloud PC vendors;
- enterprise IT tooling vendors;
- accessibility and education platforms;
- AI assistant and local-agent platforms.

## Why Industry Would Care

### Operating-System Vendors

Pain points:

- keyboard layouts are platform-specific and hard to compare;
- locale support remains uneven;
- assistive technologies need layout metadata;
- AI assistants need deterministic answers about typing;
- new AI keys and command palettes need semantic actions, not only scan codes.

OKLM value:

- verified metadata for layouts;
- export to LDML Keyboard and platform formats;
- import LDML Keyboard files for enrichment and validation;
- conformance tests;
- command metadata for companion apps and AI keys;
- accessibility labels and "how to type" knowledge.

### Keyboard and Laptop Manufacturers

Pain points:

- regional SKUs multiply production complexity;
- keycap legends, packaging and software profiles often diverge;
- dynamic keyboards and control surfaces need structured labels;
- global QWERTY hardware still needs local language support.

OKLM value:

- one model for print legends, keycaps, stickers and dynamic displays;
- language-pack metadata;
- ANSI/ISO geometry support;
- QWERTY Global-style modular layouts;
- validation that physical legends match software output.

### Application Vendors

Pain points:

- shortcuts are shown as if every user had a US keyboard;
- IDEs, games and creative apps confuse physical keys and characters;
- tutorials and onboarding rarely adapt to the user's layout;
- remote apps often mishandle keyboard intent.

OKLM value:

- physical-key and character-layer metadata;
- correct shortcut display;
- layout-aware tutorials;
- remote desktop keyboard negotiation;
- developer-friendly APIs and fixtures.

### Enterprise IT

Pain points:

- keyboard layout deployment is hard to audit;
- training material diverges from installed layouts;
- multilingual fleets mix ANSI, ISO and national layouts;
- accessibility and compliance needs are poorly documented.

OKLM value:

- deployment manifests;
- auditable layout identity;
- training and migration metadata;
- conformance tests;
- admin-readable documentation.

### AI and Local Agents

Pain points:

- assistants guess shortcuts from generic web knowledge;
- they confuse layouts and OS conventions;
- character insertion must remain deterministic;
- global key capture is unacceptable.

OKLM value:

- local assistant knowledge files;
- explicit command definitions;
- deterministic "how to type" answers;
- no need for background keylogging;
- privacy-aware companion workflows.

## Adoption Wedge

The path to industry adoption should be practical, not declarative.

### Step 1 - Reference Layouts

Use AZERTY Global and QWERTY Global as serious reference implementations.

Minimum proof:

- one OKLM manifest for AZERTY Global;
- one OKLM manifest for QWERTY Global base;
- at least two generated outputs;
- validation tests proving outputs match the manifest.

### Step 2 - Developer Tooling

Build tools that save time immediately:

- validator;
- static keyboard map exporter;
- web tester data exporter;
- LDML Keyboard exporter;
- LDML Keyboard importer;
- dynamic legend exporter.

### Step 3 - Public Compatibility Demonstrations

Demonstrate OKLM against visible industry use cases:

- "correct shortcut display outside US QWERTY";
- "one QWERTY chassis, multiple language modules";
- "dynamic legends from the same manifest";
- "assistant answers how to type characters without guessing";
- "layout conformance report for enterprise deployment".

### Step 4 - Standards and Vendor Outreach

After the reference implementation works:

- discuss the LDML mapping publicly;
- submit feedback or compatibility notes to relevant open communities;
- approach Linux/XKB and keyboard communities first;
- then approach dynamic-key vendors and tooling vendors;
- only approach major OS/OEM players with working demos and usage signals.

## What OKLM Must Not Do

- Claim to replace Unicode CLDR/LDML Keyboard.
- Claim industry-standard status before adoption.
- Depend on AZERTY Global only.
- Depend on one OS key such as Copilot.
- Depend on one hardware vendor.
- Become a speculative spec without working exporters.

## Success Criteria

Early success:

- AZERTY Global can generate at least two artifacts from OKLM.
- QWERTY Global can demonstrate one base chassis and one module.
- A validator catches real divergence between artifacts.

Credibility success:

- LDML export exists.
- Dynamic legend export exists.
- At least one external layout can be described in OKLM.

Industry signal:

- one third-party tool consumes OKLM;
- one hardware/dynamic-key vendor shows interest;
- one open-source ecosystem discussion references OKLM seriously;
- one enterprise or education deployment benefits from OKLM-generated docs or tests.

---

*Last updated: 2026-06-03*
