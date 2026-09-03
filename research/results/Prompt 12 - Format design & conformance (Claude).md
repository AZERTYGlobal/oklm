# Engineering a Durable, Hand-Maintainable JSON Layout Format: Lessons from Long-Lived Data Standards

## TL;DR
- **Version the specification with SemVer 2.0.0 and version each file with a single required string field** (glTF's `asset.version` model), commit to **additive-only evolution with a strict "ignore unknown fields" rule**, and use a **namespaced, registry-backed extension mechanism** (glTF's `KHR_`/`EXT_`/vendor tiers plus `extensionsUsed`/`extensionsRequired`) — these three choices are the load-bearing decisions for a decades-long format.
- **Target JSON Schema 2020-12** (the dialect glTF 2.0 and OpenAPI 3.1 both adopted, and the base for the JSON Schema project's forthcoming stable spec), keep files **hand-diffable** (stable key order, one item per line, raw UTF-8, human-readable string identifiers, no base64/bit-packed/magic-number blobs), require **UTF-8 with no BOM and NFC normalization**, and localize strings via **objects keyed by BCP 47 tags**.
- **Ship the conformance regime with the v1.0 spec, not after**: an official test suite of positive/negative fixtures in the JSON-Schema-Test-Suite manifest style, a single **reference validator as the ecosystem anchor** (the glTF-Validator model), and round-trip + canonical-form tests. The formats that skipped this (OpenAPI, OpenType historically) suffered years of interoperability divergence.

## Key Findings

1. **A format's durability comes from its evolution rules, not its initial cleverness.** USB HID descriptors from the 1990s still work because of self-describing tagged items and unknown-tolerance — but their opaque binary encoding produced buggy descriptors that OSes must "quirk" around to this day (the Linux kernel ships a `hid-quirks.c` with device-specific workarounds). The lesson: keep the tolerance and self-description, drop the opacity.
2. **Two version numbers, two jobs.** Successful formats separate *spec version* (SemVer, for implementers) from *file version* (a field in each document, for processors deciding whether they can load it). glTF's `asset.version` + optional `asset.minVersion` is the cleanest realization.
3. **"Processors MUST ignore unknown fields" is the single most important compatibility rule.** It is Postel's law operationalized; HTML, OpenAPI (`x-`), and glTF (`extras`/`extensions`) all rely on it. But it must be paired with an explicit "required capability" declaration so old processors *fail loudly* rather than silently misinterpret — glTF's `extensionsRequired` is the exemplar.
4. **A registry with tiers prevents forking.** glTF (KHR/EXT/vendor), OpenType (lowercase registered vs uppercase private tags), and USB HID (vendor pages 0xFF00–0xFFFF) all let vendors innovate without collisions. The registry, not the spec text, is what keeps the ecosystem coherent.
5. **Profiles fragment ecosystems.** SVG's Tiny/Basic/Full split and the failed SVG 1.2 Full are cautionary tales; keep conformance levels to a minimum (ideally just "core" and "full").
6. **The test suite is part of the specification.** JSON Schema's language-agnostic test suite (+ Bowtie), CLDR's `NormalizationTest.txt`, and the glTF-Validator are why those ecosystems interoperate. OpenAPI's and (historically) OpenType's lack of official suites caused measurable divergence.

## Details

### 1. Schema & file-design best practices for longevity

**Choice of JSON Schema draft.** The meaningful options are the older Draft 4/6/7 family (ubiquitous tooling, no vocabularies, no `$dynamicRef`/`unevaluatedProperties`), the transitional 2019-09, and **2020-12** (current best-supported modern draft). 2020-12 introduced/settled `unevaluatedProperties` (which solves the notorious `additionalProperties: false` + `$ref` composition problem that ran to 500+ GitHub comments in the OpenAPI community), `$dynamicRef`/`$dynamicAnchor`, and a formal vocabulary mechanism (`$vocabulary`). Two data points strongly favor 2020-12 for a new long-lived format: **glTF 2.0's schema files declare `"$schema": "https://json-schema.org/draft/2020-12/schema"`**, and **OpenAPI 3.1.0 (released 2021-02-15) achieved 100% compatibility with JSON Schema draft 2020-12** — per the OpenAPI Initiative's announcement, it "now supports 100% compatibility with the latest draft (2020-12) of JSON Schema" — ending years of an incompatible "subset-superset" dialect.

Critically, the **JSON Schema project's own direction is toward a single stable spec, not more drafts.** Their blog ("Towards a stable JSON Schema") states the next release "will be a long-lived version that is stable, but evolving," with "strict backward and forward compatibility requirements." The IETF working group charter (JSONSCHEMA) aims "to produce a stable, reference specification of JSON Schema as a Proposed Standard." The team explored and then in Nov 2023 pulled back from some aggressive ideas (disallowing unknown keywords), settling on allowing unknown keywords with an `x-` prefix. **Recommendation: author your schema against 2020-12, pin the exact `$schema` URI in every schema file, and treat the dialect as frozen for your format** — do not chase future drafts. The tradeoff: Draft-07 has wider legacy tooling, but 2020-12 is where the standard is stabilizing and where glTF/OpenAPI have already committed.

**Stable field ordering for clean diffs.** Per **RFC 8259 (the JSON standard, Dec 2017)**, "An object is an unordered collection" — so key order is semantically meaningless but *textually* critical for human diffs. Two disciplines help: (a) define a **canonical key order** in the spec (e.g., metadata first, then structural fields) and have your reference formatter enforce it; (b) for hashing/signing use cases, adopt **RFC 8785 JSON Canonicalization Scheme (JCS)**, which sorts object keys by UTF-16 code-unit order, strips insignificant whitespace, and fixes number serialization to produce byte-identical output. Note the tension: **JCS's lexicographic key sort is optimal for signatures but often worse for humans** than a curated semantic order. Recommendation: use a **curated canonical order for the hand-edited source form**, and reserve JCS for a separate canonical/signing form used in round-trip comparison.

**Explicit naming, shallow nesting, no opaque encodings.** The USB HID cautionary tale is decisive here: HID's bit-packed, magic-number binary items are compact and self-describing to machines but *not hand-maintainable*, and "there's an infinite number of ways to describe the same reports," producing ambiguous corner cases and buggy descriptors. For a hand-maintained JSON format: prefer **human-readable string identifiers from an enumerated vocabulary over numeric IDs**, avoid **base64 blobs, bit-packed integers, magic numbers, and hashed IDs**, keep nesting shallow, and prefer verbose-but-clear over compact-but-cryptic. The KLE (keyboard-layout-editor.com) format is the negative example in this exact domain: its "serialized" format is a compact positional array mixing label-strings with property-objects, is not even strict JSON (it uses JSON5-style unquoted keys and strips the outer brackets), and its own `kle-serial` parser README admits "the format has evolved considerably… As a result, third-party parsing implementations aren't always 100% compatible with KLE itself, particularly with respect to certain corner-cases or older/deprecated properties." That is precisely the durability failure to avoid.

**Comments.** JSON has no comment syntax (RFC 8259). Provide sanctioned metadata fields instead: a **`$comment`** convention (borrowed from JSON Schema) and/or first-class **`description`/`notes`** fields on objects. On JSON5/JSONC/YAML: JSON5 and JSONC allow comments and trailing commas but are **not RFC 8259 JSON** and fragment tooling; YAML adds significant complexity and known footguns (the "Norway problem," indentation sensitivity). **Recommendation: keep the canonical interchange format strict RFC 8259 JSON, add `$comment`/`description` fields for human annotation, and — if authors demand comments — permit a JSONC *authoring* superset that is stripped to canonical JSON on save, never shipped as the interchange form.**

### 2. Versioning & evolution

**Version the SPEC with SemVer; version each FILE with a field.** Adopt **Semantic Versioning 2.0.0** (semver.org) for the specification document: MAJOR for incompatible changes, MINOR for backward-compatible additions, PATCH for backward-compatible fixes; and per SemVer rule 8, MINOR "MUST be incremented if any public API functionality is marked as deprecated." Separately, every file carries a version field. Survey of how real formats do the file field:

| Format | File version mechanism |
|---|---|
| glTF 2.0 | `asset.version` (required, e.g. `"2.0"`, pattern `^[0-9]+\.[0-9]+$`) + optional `asset.minVersion` |
| OpenAPI | top-level `openapi` string (e.g. `"3.1.0"`) |
| CLDR keyboards | `conformsTo` attribute (e.g. `"45"`) |
| SVG | `version` attribute (`"1.0"`/`"1.1"`) — **now deprecated** |
| JSON Schema | `$schema` URI identifying the dialect |

**The single most instructive pattern is glTF's `version` + `minVersion`.** The spec says clients "should first check whether a minVersion property is specified and ensure both major and minor versions can be supported. If no minVersion is specified, then clients should check the version property and ensure the major version is supported." This gives you graceful degradation: a file can target 2.3 but declare `minVersion: 2.1`, telling a 2.1-era processor it can still load it.

**SVG's `version` attribute is the anti-pattern:** it was "purely advisory and has no influence on rendering or processing," and SVG 2 removed `baseProfile` and `version` entirely. Lesson: a version field must have defined processing semantics (like glTF's), or it becomes dead weight.

**Additive-only evolution + "ignore unknown fields."** Bake in the rule that within a major version, only additions are allowed, and **processors MUST ignore fields they do not recognize** rather than erroring. This is Postel's law and is how HTML tolerates unknown elements/attributes, how OpenAPI tolerates `x-` fields, and how glTF tolerates `extras`. In JSON Schema terms, do **not** set `additionalProperties: false` at the top level of your document schema (that would forbid forward-compatible additions); reserve strictness for leaf objects where you want typo-detection. Note glTF's own schemas often use `additionalProperties: false` on defined objects but route all extension data through the dedicated `extensions`/`extras` objects — a good hybrid.

**Feature detection so old processors fail gracefully.** The critical companion to "ignore unknowns" is a way to say "this file *needs* capability X." glTF's `extensionsUsed` (everything present) vs `extensionsRequired` (subset that must be supported or the load should fail) is the model: "An extension is considered required if a typical glTF loader would fail to load the asset in the absence of support for that extension." Adopt an analogous `featuresUsed`/`featuresRequired` (or `extensionsRequired`) top-level array so an old processor can *detect* it cannot faithfully render a file and refuse, rather than silently misinterpreting it.

**Deprecation policy: deprecate, never remove.** Follow **Unicode's stability policy**, the gold standard for a decades-long data standard. From the Unicode Character Encoding Stability Policies page: "Once a character is encoded, it will not be moved or removed… The Unicode Standard may deprecate the character… but it will not reallocate, remove, or reassign the character"; and properties, once defined in the UCD, "will never be removed." CLDR keyboards apply the same principle to the format itself — UTS #35 Part 7 states: "keyboards which conform to a CLDR version automatically are conformant to all future versions… a layout with `conformsTo="45"` could be changed to `conformsTo="46"` with no other changes and the layout would remain conformant." OpenAPI similarly deprecates rather than removes (e.g., `discriminator` was flagged, and 3.x releases from 3.2 onward are backward-compatible with 3.1; **OpenAPI 3.2.0 shipped 2025-09-19** as an additive feature release where "your existing 3.1 descriptions keep working while you opt into new ergonomics"). **Recommendation: mark fields `deprecated: true`, keep them parseable forever within the major version, and only ever remove at a MAJOR bump — which, ideally, you never do.**

### 3. Extensibility & namespacing

**Allow vendor/private extensions without forking, via prefixes + a registry.** The proven mechanisms:

| Format | Namespacing mechanism | Tiers |
|---|---|---|
| glTF | `PREFIX_name` in `extensions`/`extensionsUsed` | `KHR_` (Khronos-ratified), `EXT_` (multi-vendor), `VENDOR_` (single-vendor) |
| OpenAPI | `x-` prefix on any field (3.0); 3.1 also allows arbitrary keywords | specification extensions |
| OpenType | 4-char tags | lowercase = Microsoft-registered; **four uppercase letters (A–Z) reserved as private vendor space** |
| USB HID | Usage Pages | vendor-defined range **0xFF00–0xFFFF** |
| Unicode | Private Use Areas | e.g., U+E000–U+F8FF |
| XML/SVG | XML namespaces / `foreignObject` | — |

**Recommendation: adopt glTF's exact scheme.** Route all non-core data through a top-level `extensions` object (and per-object `extensions`), reserve an `extras`/`x-` mechanism for freeform application data that requires *no* registration, and use prefixed names with three tiers.

**Run the registry the way glTF runs its extension registry** (the KhronosGroup/glTF repo, `extensions/` directory, with the vendor-prefix list maintained in `extensions/Prefixes.md`). Its documented process:
- **Vendor extensions** (`VENDOR_`): any vendor — "not just Khronos members" — can request an extension prefix by submitting a GitHub issue, then opens a PR adding the extension. Not ratified, not covered by any IP framework.
- **Multi-vendor** (`EXT_`): when implemented by more than one vendor, promote via PR; still not ratified.
- **Ratified** (`KHR_`): submitted for ratification, voted by the Khronos Board of Promoters, covered by the Khronos IP framework.
- glTF's published lifecycle stages: **Proposal → Initial Draft → Review Draft → Release Candidate → Ratified**, with a Release Candidate requirement that "the feature… be incorporated into the Khronos Sample Viewer and supported by the Khronos Asset Validator" — i.e., **an extension is not done until the validator and samples support it.** The set of registered vendor prefixes is large (see the live `Prefixes.md` for the current count rather than a fixed number).

Other registry models worth borrowing from: **OpenType's tag registry** at Microsoft Typography (registered lowercase tags require a distinct single function; uppercase reserved for private use, with Microsoft explicitly warning it "cannot ensure that two font vendors will not choose the same tag for a private feature") and the **IANA registry model** (media types, the Language Subtag Registry) with its expert-review process. **The transferable lesson: reserve a private/unregistered namespace that needs no permission (so vendors never fork), plus a low-friction promotion path (issue → PR → multi-vendor → ratified), and make registry acceptance contingent on validator + fixture support.**

### 4. Internationalization of the format itself

**Localized names/descriptions.** The two dominant patterns are (a) an **object keyed by BCP 47 tags** (`{"en": "...", "fr": "..."}`) and (b) an **array of `{lang, value}`**. The Web App Manifest uses the object-keyed form (`*_localized` members whose keys are "a BCP 47 language tag"); glTF/OpenType `name` tables use numeric language IDs; CLDR is itself the source data. **Recommendation: object-keyed-by-BCP-47** for hand-maintainability (deduplicated keys, easy to diff, natural fallback), with an OPTIONAL default/root value.

**Locale tagging via BCP 47.** Require **BCP 47** tags per **RFC 5646** (syntax) and **RFC 4647** (matching), drawn from the **IANA Language Subtag Registry**, and specify canonicalization per **UTS #35 / CLDR**. RFC 5646 recommends putting "the most significant information… in the most significant (left-most) subtags" and handling truncation gracefully.

**UTF-8, no BOM.** Mandate **UTF-8** per **RFC 8259 §8.1**: "JSON text exchanged between systems that are not part of a closed ecosystem MUST be encoded using UTF-8," and "Implementations MUST NOT add a byte order mark." State both as MUST-level requirements.

**Unicode normalization.** Specify **NFC** for string values, citing **UAX #15** and the **W3C Character Model for the Web (Charmod-Norm)**. This matters enormously for a keyboard/identifier format because key and identifier comparison must be well-defined: two visually identical strings in NFC vs NFD are different byte sequences and will fail naive equality. Note the instructive contrast: **CLDR keyboards process everything in NFD internally** ("in processing they are converted to NFD") because decomposed form is easier to pattern-match for input transforms — so **be explicit about which normalization form applies where** (NFC for stored/compared string values is the safe default; document any internal NFD processing). Leverage the **Unicode Normalization Stability Policy** (4.1+): a string normalized under one Unicode version yields identical results under all later versions, so "once a character is encoded, its canonical combining class and decomposition mapping will not be changed."

**Escaped vs raw non-ASCII.** RFC 8259 makes `\uXXXX` escapes optional; raw UTF-8 bytes are equally valid. For hand-maintainability and clean diffs, **require raw UTF-8 in the canonical form and forbid gratuitous `\u` escaping** (a French "é" should appear as `é`, not `\u00e9`). This is the single biggest readability win for an i18n-heavy format.

**Unicode version stability.** State the minimum Unicode version your format assumes and rely on the encoding-stability guarantees (characters never move/removed) so files remain valid as Unicode grows.

### 5. Conformance design

**Normative language.** Use **RFC 2119** keywords (MUST/SHOULD/MAY/etc.) with the **RFC 8174** clarification that "The words have the meanings specified herein only when they are in all capitals" — include the standard boilerplate verbatim. This eliminates the ambiguity that plagued specs before 2017.

**Conformance levels/profiles — keep them minimal.** SVG is the cautionary tale: it split into **Tiny / Basic / Full** profiles (SVG Tiny required `baseProfile="tiny"`), the **SVG 1.2 Full effort was abandoned**, SVG Tiny 1.2 became a "deprecated branch," and SVG 2 removed `baseProfile` altogether. The W3C QA Framework's "Variability in Specifications" work warns that too many profiles/optional features fragment interoperability. Contrast with the simpler, durable dichotomies: **XML's "well-formed" vs "valid,"** and **glTF's deliberate choice to avoid profiles.** **Recommendation: define at most two levels — "core" (MUST support) and "full" (core + registered extensions) — and resist any further subdivision.**

**"Conforming FILE" vs "conforming PROCESSOR" are different products.** The W3C QA Framework's "classes of products" concept is essential: define conformance separately for (1) a **conforming document/file**, and (2) each **processor class** — at minimum an **exporter/generator**, an **importer/interpreter**, and a **validator**. SVG explicitly defines conformance classes for documents, generators, interpreters, and viewers; XML separates conforming documents from conforming processors; OpenType separates font conformance from rasterizer conformance. **Recommendation: enumerate your product classes (file, exporter, importer, validator) up front and write separate MUST-lists for each** — an exporter MUST emit canonical form; an importer MUST ignore unknown fields; a validator MUST implement the reference test suite.

### 6. Test-suite & validation design

This is where formats live or die, and where you should invest early.

**Golden/fixture files.** Ship **positive fixtures** (minimal valid, maximal "kitchen-sink" valid) and **negative fixtures** (each violating exactly one rule). Model the manifest format on the **JSON-Schema-Test-Suite** (`json-schema-org/JSON-Schema-Test-Suite`): `tests/<draft>/*.json`, each file an array of test-case objects `{description, schema, tests:[{description, data, valid:boolean}]}`, with an `optional/` subdirectory for non-core features. This structure is language-agnostic (requires "only a JSON parser") and is exactly what you want for a format meant to be implemented by many independent parties.

**Round-trip and canonical-form tests.** Require **export → import → export idempotence**: re-exporting an imported file must yield byte-identical canonical output. Compare using your canonical form (curated key order, or JCS per RFC 8785 for a signing/hash form). This catches the silent data-loss bugs that plague ad-hoc converters — e.g., the QMK `kle2json` converter "does not transfer the rotational data across," a classic lossy round-trip.

**A reference validator as the ecosystem anchor.** The **glTF-Validator** (KhronosGroup/glTF-Validator) is the model: it validates against the spec, emits a **JSON report** with **severity levels** (its config documents "0 - Error, 1 - Warning, 2 - Info, 3 - Hint"), stable **issue codes** (e.g., `ACCESSOR_INDEX_TRIANGLE_DEGENERATE`, `NODE_EMPTY`), and **JSON-pointer locations**; its report schema is itself published. Crucially, "300+" unit tests each pair "an asset and its validation report," and Khronos requires new extensions to be validator-supported before Release Candidate — the validator is *the* gatekeeper. **Recommendation: fund one authoritative reference validator, keep it in lockstep with the schema (same repo, CI that fails if schema and validator diverge), publish its report format as a versioned JSON schema, and use stable machine-readable issue codes.**

**Single reference vs multiple implementations.** There's a genuine tradeoff. A **single reference validator** guarantees one interpretation but risks "the implementation *is* the spec" ambiguity. The **W3C model** demands the opposite: to exit Candidate Recommendation, "there must be… at least two independent, interoperable implementations of each feature" ("Independent" = different codebase; "Interoperable" = passing the official test suite). **Recommendation: do both — one blessed reference validator as the anchor, plus a language-agnostic test suite that lets independent implementations prove interoperability, and (borrowing JSON Schema's Bowtie) a harness that runs all implementations against the suite and publishes a comparison report.**

**How mature standards ship test data (borrow directly):**
- **CLDR/Unicode:** conformance test files like `NormalizationTest.txt` and `BidiTest.txt`, plus ICU/CLDR test-data directories — plain, versioned, machine-readable.
- **JSON Schema:** the test suite + **Bowtie** meta-validator (Docker harness per implementation, runs the official suite, publishes a report).
- **W3C:** web-platform-tests with metadata; implementation reports; the two-implementations CR exit criterion.
- **glTF:** **glTF-Sample-Assets** (formerly Sample-Models) + the validator — samples double as fixtures.
- **OpenType (cautionary):** historically had **no official test suite**, leaving the ecosystem to depend on de-facto tools — the **OpenType Sanitizer (ots)**, **fontTools/fontbakery**, and **Microsoft Font Validator** — and on "whatever Windows accepts" as the real spec. The consequence was inconsistent conformance for years.
- **USB HID (cautionary):** the USB-IF compliance program and the HID Descriptor Tool exist, but buggy descriptors are so common the Linux kernel ships a `hid-quirks.c` with device-specific workarounds. Cautionary tale: a validator that isn't mandatory and authoritative won't prevent a long tail of broken files.
- **OpenAPI (cautionary):** **no official test suite**, which the community repeatedly cites as a cause of interoperability divergence among validators.

### 7. Transferable lessons from long-lived formats

**Unicode/CLDR** — the model for a decades-long data standard. Stability policies (encode-once-never-remove, name stability, normalization stability), versioned data releases with deprecated-but-retained items, and a directly relevant case study: **UTS #35 Part 7 (Keyboards)**, itself a keyboard-layout format inside a long-lived standard. Its **"Keyboard 3.0" redesign shipped in CLDR v45 (released 2024-04-17)** after an 18-month effort (Public Review Issue #476, closed 2023-07-15) — and notably, per the spec, "A major rewrite of this specification, called 'Keyboard 3.0', was introduced in CLDR v45. The changes required were too extensive to maintain compatibility… the ldmlKeyboard3.dtd DTD is not compatible with DTDs from prior versions of CLDR such as v43 and prior." **Lesson: even the most stability-obsessed body sometimes needs a clean break — but it isolated it to a major redesign, kept old files archivable, and preserved forward-conformance for new files (`conformsTo`).** On **cldr-json** (`unicode-org/cldr-json`): CLDR's authoritative source is LDML XML, and JSON is *programmatically generated* from it, only from data at `draft="contributed"`/`"approved"` status. Two deliberate design decisions carry a lesson: the JSON is "based on the fully resolved form" (no complex fallback needed by consumers), and "there is no goal to convert JSON data back to XML" — **the conversion is intentionally one-way.** A concrete naming gotcha they hit: they originally prefixed non-distinguishing attributes with `@`, then switched to `_` because "`@` can't be used as the first character in a JavaScript identifier." **Lesson: choose identifiers that are friendly to the consuming languages.** The `-modern` packages are being deprecated/removed (scheduled v46, CLDR-16465) — even data packaging needs a deprecation policy.

**OpenType** — the sfnt table structure is a masterclass in extensibility: **tagged, independently versioned tables**, and unknown-table tolerance ("If the major version is not recognized, the implementation must not read the table… treat the table as missing"). The `.fea` feature-file syntax gives a human-authorable layer. But 30+ years accreted mistakes to learn from: **OS/2 table version sprawl**, the **CFF vs CFF2 split** (CFF2 "cannot be used as a stand-alone font program"), the **variable-fonts retrofit** bolted onto a static format, the **`name` table's platform/encoding-ID complexity**, and the **four-competing-color-font-formats problem**. **Lessons: independently versioned, tagged sub-objects with unknown-tolerance are excellent; but retrofitting major capabilities and permitting multiple competing solutions to the same problem creates permanent complexity — decide once, centrally.**

**USB HID** — self-describing tagged item encoding with vendor-defined ranges means 1990s devices still work. But the downside is the whole cautionary spine of this report: **opaque binary that is not hand-maintainable, ambiguous corner cases** ("an infinite number of ways to describe the same reports"), and **buggy descriptors that OSes quirk around**. Directly relevant because a keyboard format could easily fall into HID's trap of being machine-optimal but human-hostile.

**glTF** — the positive template throughout: JSON + a tiered extension registry + `extensionsUsed`/`extensionsRequired` + a validator as ecosystem anchor + sample assets as fixtures. The **glTF 1.0 → 2.0 break** (2.0 replaced the 1.0 GLSL-technique material model with physically-based rendering) shows that one decisive, well-communicated major break is survivable and preferable to endless compatibility hacks. **Lesson: it's the best all-around model for a new JSON format to emulate.**

**OpenAPI** — the **Swagger 2.0 → OpenAPI 3.0 → 3.1** evolution, and specifically 3.1's alignment with JSON Schema 2020-12 after years of an incompatible subset/superset, is the definitive lesson in **not inventing your own dialect of an existing standard.** OpenAPI even **broke from strict SemVer numbering** to make the alignment: per the OpenAPI Initiative, "Technically, using semantic versioning with the new full alignment with JSON Schema would require this change to be denoted as 4.0.0… but to force it into a major release numbering would have created a mismatch of expectations." The **Moonwalk/4.0** discussion (backing compatible ideas into 3.2, released 2025-09-19, rather than forcing a 4.0 break) shows a maturing preference for additive evolution. **Lessons: reuse JSON Schema rather than forking it; be deliberate about SemVer; prefer additive minors.**

**SVG** — the **1.0 → 1.1 → Tiny 1.2 → SVG 2** saga is the profile-fragmentation cautionary tale: profiles fragmented the ecosystem, **SVG 1.2 Full failed**, SVG 2 stalled for years, browsers became the de-facto spec, and the **`version` attribute was deprecated** as useless. The positive takeaways are **namespaces and `foreignObject` for extensibility.** **Lessons: minimize profiles; give version fields real semantics or omit them; beware letting a dominant implementation become the real spec.**

**Ad-hoc keyboard JSON formats (domain-specific cautionary set):**
- **KLE (keyboard-layout-editor.com):** compact positional arrays, JSON5 non-strict syntax, no schema, no version field; third-party parsers are "not always 100% compatible" (per the official `kle-serial` README). Community requests for "a correct and complete JSON document instead of raw partial Javascript array definition" were filed to make it parseable by other tools.
- **QMK:** `info.json`/`keymap.json`/`keyboard.json` with no user-visible schema-version field; versioning handled out-of-band via a formal "Breaking Changes" cycle. Notable forced migrations: layout definitions in `info.json` became **mandatory (May 2023)**, and a new `keyboard.json` was introduced (**May 2024**, PR #22891). They eventually added **strong versioning for keycodes** (Nov 2022) precisely because the loose approach was fragile — "keycode values now have strong versioning… published online and will not change." **Lesson: retrofitting versioning after the fact is painful; design it in from v1.**
- **VIA:** the **v2 → v3 keyboard-definition break** is a textbook forward-compat failure: v3 added `menus`/`keycodes` properties that **v2 parsers reject** ("should NOT have additional properties"), version is negotiated by firmware **protocol version** (v3 required if `VIA_PROTOCOL_VERSION` ≥ 11) rather than declared in the file, and "V1 and V2 definitions are not interchangeable." **Lesson: this is exactly what "ignore unknown fields" + a real in-file version field would have prevented.**
- **Vial** (`vial.json`) reuses much of VIA's format but stores the compressed definition in firmware flash and transmits it at runtime, sidestepping VIA's central-repo submission — a different durability strategy (self-describing device) worth noting.
- **Kanata (S-expressions), ZMK (Devicetree):** not JSON at all — useful contrast showing the domain has no dominant interchange format, which is the gap a well-engineered JSON format could fill. ZMK's compile-time-only devicetree and its terse syntax (spawning helper-macro projects like `zmk-nodefree-config`) reinforce the value of a hand-maintainable, self-documenting format.

## Deliverable A — Concrete Format-Design Checklist

**Versioning**
- [ ] SemVer 2.0.0 for the specification document; changelog per release.
- [ ] Required top-level `formatVersion` string in every file; optional `minVersion` with glTF's processing semantics (check `minVersion` first for both major+minor; else check major of `version`).
- [ ] Version field has *defined processing semantics* (not advisory like SVG's).

**Unknown-field / compatibility policy**
- [ ] MUST-level "processors ignore unknown fields."
- [ ] No top-level `additionalProperties: false`; use it only on leaf objects for typo detection.
- [ ] Top-level `extensionsRequired` (or `featuresRequired`) array so processors fail loudly on unsupported required capabilities.
- [ ] Additive-only evolution within a major version; deprecate-never-remove (Unicode/CLDR model).

**Extension / namespacing mechanism**
- [ ] Top-level and per-object `extensions` object; prefixed names in three tiers (`VENDOR_` / `EXT_` / ratified).
- [ ] Unregistered `extras`/`x-` escape hatch requiring no permission (prevents forking).
- [ ] Public registry (GitHub, glTF-style: issue for prefix → PR → multi-vendor → ratified); acceptance gated on validator + fixture support.

**Conformance**
- [ ] RFC 2119 + RFC 8174 boilerplate verbatim.
- [ ] Exactly two levels: "core" and "full." No further profiles.
- [ ] Separate MUST-lists for file / exporter / importer / validator product classes.

**Internationalization & encoding**
- [ ] UTF-8, no BOM (RFC 8259 §8.1, MUST).
- [ ] Raw non-ASCII in canonical form; forbid gratuitous `\u` escapes.
- [ ] NFC for stored/compared strings (UAX #15 / Charmod-Norm); document any internal NFD.
- [ ] Localized strings as objects keyed by BCP 47 tags (RFC 5646/4647), optional root value.
- [ ] State the assumed minimum Unicode version.

**Hand-maintainability**
- [ ] Curated canonical key order; one array item per line.
- [ ] Human-readable string identifiers from an enumerated vocabulary; no numeric magic IDs.
- [ ] No base64 blobs, bit-packed integers, or hashed IDs.
- [ ] `$comment` / `description` / `notes` fields instead of comments; strict RFC 8259 JSON as interchange form (JSONC only as an authoring superset).

## Deliverable B — Proposed Conformance + Test-Suite Model (the minimum to be trustworthy)

1. **Fixtures** (in a `tests/` tree, JSON-Schema-Test-Suite manifest style — `{description, schema/subject, tests:[{description, data, valid}]}`, with `optional/` for extensions):
   - ≥1 **minimal valid** file (smallest legal document).
   - ≥1 **maximal valid** file exercising every core field.
   - ≥1 **valid file per registered extension**, contributed *with* the extension PR.
   - **Negative fixtures**, each violating exactly one rule, with the expected validator issue code.
2. **Reference validator** (same repo as the schema; CI fails on schema/validator drift): emits a versioned **JSON report** with severity levels (error/warning/info/hint), stable issue codes, and JSON-pointer locations.
3. **Round-trip tests:** export → import → export must be byte-identical in canonical form; a separate JCS (RFC 8785) canonical form for hashing/signing.
4. **Independent-implementation gate:** ≥2 independent, interoperable implementations (different codebases) passing the suite before declaring v1.0 stable (W3C CR criterion), surfaced via a Bowtie-style comparison harness.
5. **Sample assets** doubling as real-world fixtures (glTF-Sample-Assets model).

## Deliverable C — How 4–5 Successful Formats Handled Versioning & Extensibility

| Format | Spec versioning | File versioning | Extensibility & namespacing | Unknown-field rule | Transferable lesson |
|---|---|---|---|---|---|
| **glTF 2.0** | Khronos-ratified, decisive 1.0→2.0 break | `asset.version` (req.) + `asset.minVersion` (opt.) with real processing semantics | `extensions`/`extras`; `KHR_`/`EXT_`/`VENDOR_` tiers; registry gated on validator support; `extensionsUsed`/`extensionsRequired` | Ignore unknowns; required-set declared explicitly | **The all-around model: tiered registry + required-capability flag + validator/sample anchor.** |
| **OpenAPI 3.x** | SemVer-ish; deliberately numbered 3.1 (not 4.0) to align with JSON Schema 2020-12; additive 3.2 (2025) | Top-level `openapi` string | `x-` extensions (3.0); arbitrary keywords (3.1) | Ignore/allow unknown `x-` fields | **Don't fork an existing standard — reuse JSON Schema. No official test suite → interop divergence.** |
| **Unicode/CLDR** | Versioned data releases; strict stability policies | LDML `conformsTo`; forward-conformance guaranteed | Private Use Areas; registry-driven subtags | Encode-once, deprecate-never-remove | **Stability policy is the durability engine; isolate breaks (Keyboard 3.0 in v45) to major redesigns.** |
| **OpenType** | ISO/IEC 14496-22; per-table major versions | sfnt tagged tables, independently versioned | 4-char tags: lowercase registered vs uppercase private; USB-style vendor space | Unknown-table tolerance ("treat as missing") | **Tagged, independently versioned sub-objects are excellent; avoid competing formats & retrofits (color fonts, CFF/CFF2).** |
| **SVG** | 1.0→1.1→Tiny 1.2→SVG 2 (stalled) | `version`/`baseProfile` — **deprecated/removed** | XML namespaces, `foreignObject` | Ignore unknown elements/attributes | **Minimize profiles; give version fields real semantics or omit them; don't let one implementation become the spec.** |

## Recommendations

**Stage 1 — Lock the foundational decisions before writing any schema (highest leverage):**
1. **Versioning:** SemVer 2.0.0 for the spec; a **required top-level `formatVersion` string** in every file plus an **optional `minVersion`** with glTF's exact processing semantics.
2. **Unknown-field policy:** MUST-level "processors ignore unknown fields," paired with a top-level **`extensionsRequired`** (or `featuresRequired`) array.
3. **Extension mechanism:** a top-level and per-object **`extensions`** object with **`VENDOR_`/`EXT_`/`KHR_`-style tiered prefixes**, plus an unregistered **`extras`** escape hatch.
4. **Dialect:** author the schema against **JSON Schema 2020-12**, pin `$schema` in every file, and freeze the dialect for your format.

**Stage 2 — Design the file form for humans:**
5. UTF-8, no BOM; raw non-ASCII, no gratuitous `\u` escapes; NFC for stored strings; document any internal NFD.
6. Curated canonical key order + one-array-item-per-line; human-readable string identifiers; no opaque encodings; `$comment`/`description` fields; strict RFC 8259 JSON as interchange form.
7. Localized strings as **objects keyed by BCP 47 tags**, with an optional root value.

**Stage 3 — Ship conformance + tests WITH v1.0 (do not defer):**
8. RFC 2119 + RFC 8174 boilerplate; **exactly two conformance levels**; separate MUST-lists per product class.
9. One authoritative **reference validator** (CI-linked to the schema), emitting a versioned JSON report with severity levels, stable issue codes, JSON-pointer locations.
10. A **language-agnostic test suite** (positive minimal + maximal, negative one-rule-per-file, `optional/` for extensions), **round-trip idempotence tests**, and a Bowtie-style harness; require **two independent interoperable implementations** before declaring stable.

**Stage 4 — Governance for the long haul:**
11. A public **extension registry** (glTF-style promotion path) with **acceptance gated on validator + fixture support.**
12. **Deprecate-never-remove** within a major version; reserve MAJOR bumps for true breaks and communicate them as glTF did 1.0→2.0.

**Benchmarks that would change these recommendations:** If JSON Schema ships its stable (post-2020-12) spec and tooling catches up, re-pin to it. If your ecosystem stays single-vendor, defer the multi-tier registry (but keep the `extensions` object). If files will be cryptographically signed, promote RFC 8785 JCS from "signing form only" to a first-class canonical form. If profile pressure emerges, resist past two levels unless you can point to two independent implementations of each proposed profile.

## Caveats
- **JSON Schema's "stable spec" is a direction, not a shipped artifact.** The project has publicly committed to stability and chartered an IETF WG, but 2020-12 remains the current stable target and the team has reversed course on some specifics (e.g., unknown-keyword handling). Treat "no more drafts" as intent, and pin to 2020-12 today.
- **The CLDR JSON Bindings spec page is flagged by Unicode as out of date**; its detailed conversion rules are historical design intent, though the "fully-resolved form" and "one-way conversion" philosophy remain operative in the current `cldr-json` repo.
- **Some keyboard-format claims rest partly on community sources** (blogs, third-party fix repos). Load-bearing facts (VIA v2/v3 incompatibility, QMK migration dates, KLE parser incompatibility) are anchored to official docs, changelogs, or GitHub issues/PRs, but the "VIA is abandoned" characterization is contested and should not be relied upon.
- **JCS vs curated key order is a genuine, unresolved tradeoff**; this report recommends using each for a different purpose rather than declaring one universally correct.
- **The "single reference validator" carries a spec-capture risk** (the tool becomes the de-facto spec, as happened with OpenType/Windows). The two-independent-implementations rule is the mitigation and should be treated as mandatory, not optional.
- Dates and version numbers (e.g., OpenAPI 3.2.0 on 2025-09-19, OpenAPI 3.1.0 on 2021-02-15, CLDR v45 released 2024-04-17 for Keyboard 3.0) are as reported by the cited sources as of the research date (September 2026). The exact count of glTF vendor prefixes should be read from the live `extensions/Prefixes.md` registry rather than a fixed number.