# Industry Adoption

## Where this stands

Nobody outside this project uses OKLM. That is the honest starting point,
and [ROADMAP.md](ROADMAP.md) makes it a gate (gate 4, two independent
implementations or usages) rather than a wish. This document says who
could benefit, why, and in which order we expect to find out. It is a map
of possible adopters, not a list of partners.

The sequence is fixed: serve our own two layouts first, keep the tooling
honest (validators, loss reports, reproducible exports), demonstrate on
visible use cases, and only then talk to vendors. No outreach to OS or
hardware vendors happens before gate 4.

## What we know about the landscape (September 2026)

- The one vendor-neutral interchange format, LDML Keyboard (CLDR
  "keyboard3"), is loaded by no operating system; Keyman consumes it on
  desktop, with mobile and web planned and funding-dependent.
- Among layout tools, none exports LDML; kalamine, klfc, kbdgen and the
  firmware ecosystems each cover their own targets.
- Dynamic-key surfaces are few and uneven: Elgato Stream Deck profiles and
  the Logitech Actions SDK are documented; Flux Keyboard is alive but its
  profile format is not public; Nemeio has been silent since 2019–2020.
- National layout standards (AFNOR NF Z71-300, DIN 2137) are sold as PDFs
  with no official machine-readable file. Our AFNOR and BÉPO manifests are,
  as far as we know, the only public machine descriptions of the French
  standard.

Sources and dates are in the research journal under [`research/`](research/).

## Possible adopters and what they would get

### Layout authors

The fastest first users, because they can validate the model against a
layout they know by heart. What they get: one file instead of four or five
OS-specific ones, a validator that catches divergence between artifacts, and
exports with a report of what each target cannot express.

### Operating-system vendors

Pain points: layouts are platform-specific and hard to compare; assistive
technologies and AI assistants need layout metadata; new keys need
semantic actions, not only scan codes. What OKLM could offer: verified
layout metadata, LDML and platform exports, conformance tests, accessibility
labels and deterministic "how to type" knowledge. This is the audience we
approach last, with working demos and usage signals only.

### Keyboard and laptop manufacturers

Pain points: regional SKUs multiply production complexity; keycap legends,
packaging and software profiles diverge; dynamic keyboards need structured
labels; a global QWERTY chassis still needs local language support. What
OKLM could offer: one model for print legends, keycaps, stickers and dynamic
displays; ANSI/ISO geometry support; the QWERTY Global chassis-plus-modules
pattern; validation that physical legends match software output.

### Application vendors

Pain points: shortcuts are shown as if every user had a US keyboard; IDEs,
games and creative apps confuse physical keys and characters; tutorials
rarely adapt to the user's layout; remote apps mishandle keyboard intent.
What OKLM could offer: physical-key and character-layer metadata, correct
shortcut display, layout-aware tutorials, fixtures for tests.

### Enterprise IT and education

Pain points: layout deployment is hard to audit; training material diverges
from installed layouts; fleets mix ANSI, ISO and national layouts. What OKLM
could offer: an auditable layout identity, deployment and migration
metadata, admin-readable documentation generated from the same source as
the installed layout.

### AI assistants and local agents

Pain points: assistants guess shortcuts from generic web knowledge and
confuse layouts and OS conventions; character insertion must stay
deterministic; global key capture is unacceptable. What OKLM could offer:
local knowledge files with deterministic "how do I type É?" answers and
explicit command definitions, without keylogging or predictive models.

## Sequence

### Step 1 — Reference layouts (in progress)

- AZERTY Global manifest: exists, generated from the layout's source of
  truth and verified field by field.
- AZERTY Global website reading its layout from that manifest: next work
  item.
- QWERTY Global base manifest with one local module: after that.
- Validation tests proving the outputs match the manifest: exporter golden
  tests exist; the website build check comes with the website item.

### Step 2 — Developer tooling (partly done)

Exists: validator, LDML / xkb / keylayout exporters with loss reports.
Planned, in order: web tester data (with the website item), schema 0.2 with
a strict validator mode, Stream Deck profile export, Windows `.klc` export,
LDML importer (gate 3).

### Step 3 — Public demonstrations (not started)

Visible use cases to demonstrate once steps 1 and 2 hold: correct shortcut
display outside US QWERTY; one QWERTY chassis with several language modules;
dynamic legends from the same manifest; an assistant answering how to type a
character without guessing; a layout conformance report for a deployment.

### Step 4 — Standards and vendor outreach (after gate 4)

Discuss the LDML mapping publicly; send compatibility notes to the relevant
open communities; approach Linux/XKB and keyboard communities first, then
dynamic-key and tooling vendors, and OS/OEM players last.

## What OKLM must not do

- Claim to replace Unicode CLDR/LDML Keyboard.
- Claim industry-standard or "candidate standard" status before adoption.
- Depend on AZERTY Global only, on one OS key, or on one hardware vendor.
- Become a specification without working exporters.
- Announce itself before it has served its own authors.

## Success criteria

Early: AZERTY Global generates at least two artifacts from OKLM (the LDML,
xkb and keylayout exports already count; the website data will be the
one that matters); QWERTY Global demonstrates one chassis and one module; a
validator catches a real divergence between artifacts.

Credibility: an LDML importer closes the round trip; a dynamic-legend export
exists; at least one external layout is described in OKLM by someone else.

Industry signal (this is gate 4): one third-party tool consumes OKLM; one
hardware or dynamic-key vendor shows interest; one open-source ecosystem
discussion references OKLM seriously; one enterprise or education
deployment benefits from OKLM-generated documentation or tests.

---

*Last updated: 2026-09-15*
