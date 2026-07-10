# Roadmap

## Phase 0 - Product Framing

Target: June 2026.

- Create public product folder.
- Define scope and non-goals.
- Draft manifest vocabulary.
- Define the OKLM / CLDR-LDML boundary.
- Identify reference layouts.
- Decide public repository name.

## Phase 1 - Draft Schema

Target: after AZERTY Global final release.

- Write JSON Schema draft.
- Study Unicode CLDR/LDML Keyboard mapping and define whether OKLM is a superset, bridge or exporter layer.
- Specify OKLM -> LDML and LDML -> OKLM conversion reports.
- Create a minimal AZERTY Global example manifest.
- Validate static maps and character index generation.
- Document protected-source workflow for reference layouts.
- Define the first conformance checks that would matter to OS, hardware and app vendors.

## Phase 2 - Dynamic Legends

Target: S2 2026.

- Define dynamic legend fields.
- Create icon/label export format.
- Prototype Stream Deck-style profile data.
- Prototype accessibility labels.
- Evaluate Corsair/Elgato, Logitech, Flux and Nemeio export paths.
- Document hardware/OEM use cases: printed legends, keycaps, stickers, dynamic labels and regional packs.

## Phase 3 - OS and AI-Key Integration

Target: late 2026 / early 2027.

- Map manifest actions to OS companion apps.
- Evaluate Windows Copilot hardware key provider integration.
- Define OS-neutral command ids before binding anything to a specific AI key.
- Define "character assistant" metadata.
- Generate local assistant knowledge files.

## Phase 4 - QWERTY Global Modules

Target: 2027.

- Add QWERTY Global base manifest.
- Add French, Italian, German and Spanish modules.
- Demonstrate one physical QWERTY chassis with multiple local modules.
- Prepare public examples for makers and keyboard vendors.

## Phase 5 - Public Standard Candidate

Target: 2027+.

- Publish version 0.9 as candidate spec.
- Create conformance tests.
- Ship at least one OKLM -> LDML converter and one LDML -> OKLM importer.
- Invite feedback from layout authors, keyboard communities, open-source OS maintainers, app vendors, remote desktop tools, dynamic-key vendors and hardware manufacturers.
- Prepare 1.0 after at least two independent implementations or exporters.

---

*Last updated: 2026-06-03*
