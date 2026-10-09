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
- `tools/tests/run_all.py` runs every check of the repository in one command
  (`ccf973a`); `requirements.txt` lists the one third-party dependency
  (`jsonschema`); a GitHub Actions workflow is prepared, nothing is pushed.
- Validator codes `E_INTERNAL`, `E_DUPLICATE_JSON_KEY`, `E_JSON_CONSTANT`,
  `E_SURROGATE`, `E_LEVEL_RANGE`, `E_CONTROL_CHAR`, `E_DUPLICATE_DEADKEY_ID`,
  `W_DUPLICATE_HID`, `W_DUPLICATE_XKB`, `W_FEATURE_UNREGISTERED` and
  `W_LEVEL_NO_SELECTOR`; the full list is in `SPEC.md`.
- `tools/oklm_keyboard_tables.py`: the QWERTY Global conversion tables, now in
  a tracked module (`a0f7adf`).

### Fixed

- Validator: no more crash on a value of an unexpected type (one `E_INTERNAL`
  per failed stage, the batch goes on); duplicated JSON member names, `NaN`,
  `Infinity`, lone surrogates and control characters refused; level, group and
  `levelSelectors` keys out of range refused; `layers` found at any depth;
  duplicated dead-key ids refused; UTF-8 output and BOM accepted on input;
  wildcards expanded by the validator itself (PowerShell 5.1 does not).
- Schemas: `conformsTo` limited to 45-48, official SemVer 2.0.0 pattern, lists
  without duplicates, `modifier` requires `role: "modifier"`, `role: "key"`
  requires `levels`; a pattern ending in `$` no longer accepts a final line
  feed; the conversion report schema checks that `lossless-core` and `failed`
  agree with the lists.
- Migration 0.1 to 0.2: migrates 0.1 only, never overwrites a value (stops
  with `error: <file>: <message>`, status 1, file untouched), validates its
  output before writing, keeps the old `version` text in `metadata.versionLabel`
  when the SemVer does not say it back.
- LDML export: `<displays>` before `<keys>` (CLDR DTD order, checked against the
  DTD in the tests); derived locale valid under RFC 6497 (short subtags merged
  or padded, long ones cut, declared as lossy); `\m{x}(.)` fallback written as
  a transform after the compositions; `/` escaped in `from`; `authors` written
  to `info@author`; escaping independent of the Python `unicodedata` version.
- Exporters: a CapsLock level a key does not define takes the output of the
  matching level without CapsLock (warning in the LDML and keylayout reports);
  control characters and unwritable text refused with a clear error; `conformsTo`
  outside the DTD and duplicated HID refused; one standalone character per dead
  key shared by keylayout and klc, unique KBD names; the BÉPO `superscript` dead
  key usable in xkb; losses declared in the reports; the Stream Deck zip is
  identical on every system (stored entries); `export.py` creates `--out` and
  no longer treats `unsupported` as a failure.
- QWERTY Global: `build`, `check` and `import` validate everything before
  writing, and an unknown key or diff field stops the run instead of
  disappearing; the tests no longer need a private path.
- CI floor: Python 3.11 is the lowest version the workflow checks.

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
