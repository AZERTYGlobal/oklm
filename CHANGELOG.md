# Changelog

All notable changes to OKLM, newest first. No versioned release has been
tagged yet: entries are grouped by date, and by schema draft where it matters.
The short hashes are commits of this repository. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) loosely.

## Unreleased

### Changed

- Documentation brought in line with the code after the audit of 2026-10-09:
  five export targets and the LDML importer described everywhere (README,
  CLDR-LDML, INDUSTRY-ADOPTION, ROADMAP, oklm.org, `llms.txt`); gate 3 recorded
  as passed on 2026-10-05 and merged on 2026-10-06; version policy rewritten
  around draft 0.2; `SPEC.md` and `CONVERSIONS.md` corrected (prefixed
  extension namespaces, geometry families, the rule for missing CapsLock
  levels, normalization, `conformsTo` 45 to 48, validator refusals, RFC 6497
  locale subtags); licensing notice by path in the README; the 0.1 design note
  marked as historical.
- oklm.org demonstrator: keyboard operation (Tab, Enter, Space), live-region
  announcement of the inspector, text contrast raised to 4.5:1 and key
  outline contrast to 3:1, canonical link and Open Graph metadata.

### Added

- `CONTRIBUTING.md`, `SECURITY.md` and this changelog.

<!-- TODO-merge: add the entries of the other audit correction lots (validator, exporters, tests) -->

## Draft 0.2, merged 2026-10-06

### Added

- Dead keys in full in the xkb export, with a companion `.XCompose` file, and
  terminator states in the keylayout export (`f7af856`, `cde42e8`, merged in
  `1170030`).
- Merge of the schema 0.2 work, with QWERTY Global, the Stream Deck and
  `.klc` exporters and the LDML importer (`cb52fb2`).

## Draft 0.2, 2026-10-05

### Added

- Schema 0.2: open schema, SemVer `version`, `extensionsUsed`,
  `extensionsRequired` and `featuresRequired`, prefixed extension namespaces,
  a strict validator mode, a 0.1 to 0.2 migration tool, and exporters aligned
  with the gap review (`37e0109`).
- QWERTY Global: one manifest per module, composed from a shared chassis and a
  diff (`9647634`).
- Stream Deck profile export (`daf122a`) and Windows `.klc` export
  (`55d12a0`), neither verified against the vendor software.
- LDML Keyboard importer with its `OKLM_ldml` extension and a measured round
  trip on the six examples and three third-party CLDR keyboards (`9851420`).

## 2026-09-15

### Added

- `validate.py --strict`: unknown members, prefixes, HID ranges, W3C `code`
  values (`427c27d`).
- Public documents rewritten around the bridge role, the four gates and the
  known gaps against LDML Keyboard 48.2 (`26387ac`).

### Fixed

- LDML export: a level without output is written as LDML's implicit `gap`, so
  that the keys of a row no longer shift (`78f95f8`).

## 2026-09-03

### Changed

- Conformance claims in the example manifests moved from ISO/IEC 9995-1:2009
  to :2026, with an explicit note that the 2026 text was not read (`c2325a5`).
- Research journal: prompt 12 triangulated, decisions D31 to D44 recorded
  (`3ef277a`).

## 2026-07

### Added

- `robots.txt`, `sitemap.xml` and `llms.txt` for the site (2026-07-21,
  `c7eb4eb`).
- One-way exporters to LDML Keyboard, xkb and macOS keylayout with conversion
  reports, and the conversion-report schema 0.2 (2026-07-11, `cbf3fcb`,
  `54098da`, `11dbf06`).
- Example manifests for the AFNOR AZERTY, BÉPO, the legacy Windows AZERTY and
  US QWERTY, and the complete AZERTY Global manifest; oklm.org rebuilt as an
  interactive keyboard rendered from the real manifests (2026-07-10,
  `315ae16`, `ec4f50f`, `b0b05fd`).

### Changed

- Third-party license statements tightened and internal references removed
  (2026-07-10, `27fd7ce`).

## Draft 0.1, 2026-07-10

### Added

- First public draft: specification, JSON Schemas, the AZERTY Global example,
  validators and the research journal (`1e27084`).
