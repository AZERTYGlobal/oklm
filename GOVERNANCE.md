# Governance

## Stewardship

Open Keyboard Layout Model is stewarded by the AMCF (the French association
behind [AZERTY Global](https://azerty.global)) through its two layout
projects, AZERTY Global and QWERTY Global. One person writes most of it
today; that is a fact about the project's size, not a design.

The intended end state is a neutral open specification usable by anyone
who describes, validates or ships keyboard layouts. Getting there is
measured by the four gates of [ROADMAP.md](ROADMAP.md), and the last gate
(two independent implementations or usages) is the one that would justify
a governance broader than this file.

## Role

OKLM is a **bridge and tooling layer**. It does not compete with Unicode
CLDR/LDML Keyboard, operating-system layout formats or USB HID: it
describes a layout once, in a file a human can read and correct, and
exports it to those targets with an explicit loss report. Where LDML
Keyboard represents something cleanly, OKLM maps to it rather than
inventing a parallel concept. The boundary is spelled out in
[CLDR-LDML.md](CLDR-LDML.md).

The first users are the project's own layouts. Serving them well is the
test of the model; external adoption is observed at gate 4, not solicited
before it.

## Principles

1. The format must stay usable without proprietary hardware.
2. The format must support existing ANSI and ISO keyboards first.
3. Dynamic keyboards are an export target, not a requirement.
4. OS-native formats remain first-class outputs.
5. A valid OKLM manifest must remain readable, correctable and
   versionable by a human without a proprietary generator.
6. Nothing is silently discarded: every conversion produces a
   machine-readable report of what was mapped, skipped or approximated.
7. Accessibility and multilingual input are core use cases.
8. Implementations should avoid cloud dependencies for core typing
   functions.
9. Adoption requires working exporters, validators and reference
   implementations, not only a written specification.

## How decisions are made and recorded

- **Design decisions** are numbered (D1, D2, …) and recorded with their
  evidence in the research journal under [`research/`](research/), in
  French. Forty-four are recorded as of September 2026. `SPEC.md` cites
  them by number.
- **Order of work and gates** live in [ROADMAP.md](ROADMAP.md). A work
  item is not reopened once decided there; a new fact goes into the
  journal first, and the roadmap changes when a gate is passed or a
  decision is revised in writing.
- **Reference documents** for conformance and alignment are named with
  their edition: LDML Keyboard (UTS #35 Part 7) 48.2, ISO/IEC 9995-1:2026,
  W3C UI Events `KeyboardEvent.code` (2025), USB HID Usage Tables 1.7. When
  a reference has been read from a public preview rather than its full
  text, the document that relies on it says so.

## Version and compatibility policy

- **0.1 is frozen.** It is the draft described by `SPEC.md` and
  `schemas/oklm-manifest.schema.json` today. Bugs in the prose are fixed;
  the schema is not changed.
- **0.2 is the next revision, and the only one planned before 1.0.** Its
  structural choices are already decided (see ROADMAP.md, item 4): open
  schema plus a strict validator mode, prefixed extension namespaces with a
  public registry, capability arrays at the root. It absorbs the gate 1
  findings and what the first real uses teach.
- Before 1.0, breaking changes are allowed, must be documented in
  `SPEC.md`, and every example manifest and committed export is updated
  in the same change.
- After 1.0, breaking changes require a major version bump, exporters
  declare the schema versions they support, and deprecated fields stay
  documented for at least one major cycle.
- No release is called a "candidate standard", and no announcement is
  made, before gate 4 is passed.

## Contribution model

There is no formal contribution process for the 0.1 draft. Use GitHub
issues on the public repository for:

- schema and specification issues;
- example manifests of other layouts;
- exporter and importer implementations;
- conformance tests;
- documentation fixes;
- compatibility reports from OS, hardware, application, remote-desktop,
  education or enterprise contexts.

With schema 0.2, extension prefixes will be registered by pull request in
a public registry file; until then, propose a namespace in an issue.

## Licensing

Specification and documentation (`*.md`): CC BY 4.0. Schemas, validators,
tooling and reference exporters: EUPL 1.2. A layout described with OKLM
keeps its own license, declared in the manifest's `license` field.

## Naming

Public name: OKLM. Full name: Open Keyboard Layout Model. Canonical
manifest name: OKLM Manifest. Canonical file extension: `.oklm.json`.
Domains: `oklm.org` (canonical) and `openkeyboardlayoutmodel.org`
(redirect).

---

*Last updated: 2026-09-15*
