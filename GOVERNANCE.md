# Governance

## Stewardship

Open Keyboard Layout Model is initially stewarded by the AMCF ecosystem through the AZERTY Global and QWERTY Global projects.

The goal is to become a neutral open specification that can be used beyond these projects by software vendors, hardware manufacturers, operating-system ecosystems, enterprise tools and independent layout projects.

## Principles

1. The format must stay usable without proprietary hardware.
2. The format must support existing ANSI and ISO keyboards first.
3. Dynamic keyboards are an export target, not a requirement.
4. OS-native formats remain first-class outputs.
5. Human-readable documentation matters as much as machine readability.
6. Accessibility and multilingual input are core use cases.
7. Implementations should avoid cloud dependencies for core typing functions.
8. Industry adoption requires working exporters, validators and reference implementations, not only a written specification.
9. A valid OKLM manifest must remain readable, correctable and versionable by humans without a proprietary generator.

## Reference Implementations

Initial reference implementations:

- AZERTY Global;
- QWERTY Global.

Future reference implementations may include third-party layouts if they help validate the format.

## Compatibility Policy

Before version 1.0:

- breaking changes are allowed;
- changes must be documented in the spec;
- examples should be updated with each schema revision.

After version 1.0:

- breaking changes require a major version bump;
- exporters should declare supported schema versions;
- deprecated fields should remain documented for at least one major cycle.

## Contribution Model

To decide before public release.

Expected contribution paths:

- schema issues;
- example manifests;
- exporter implementations;
- conformance tests;
- documentation improvements;
- compatibility reports for dynamic-key devices.
- integration reports from OS, hardware, app, remote desktop, education and enterprise tooling contexts.

## Naming

Public name: OKLM.

Full name: Open Keyboard Layout Model.

Canonical manifest name: OKLM Manifest.

Canonical file extension: `.oklm.json`.

---

*Last updated: 2026-06-03*
