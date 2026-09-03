# Engineering a Durable, Extensible, and Trustworthy JSON Format

## Executive architecture

For a JSON-based interchange format intended to survive for decades and be implemented independently, the central design goal should be **semantic stability under partial knowledge**. A processor written today should still be able to read tomorrow’s files when the new material is optional; a future processor should be able to read old files without migration; an editor that does not understand an extension should not destroy it; and validation should distinguish “this file is invalid” from “this implementation does not support a capability this valid file requires.”

The strongest precedents all use some combination of these techniques. Unicode CLDR freezes published releases and requires stable structural evolution; glTF separates its compact core from explicitly declared extensions and distinguishes extensions merely used from those required; OpenAPI separates the `major.minor` feature set from patch-level specification corrections; OpenType preserves long-lived registries of semantic tags and gives vendors a private tag space; SVG combines “ignore unknown foreign content” with explicit feature/extension detection. citeturn24search2turn24search0turn20view2turn20view0turn25search6turn16search0

The recommended architecture is therefore:

| Concern | Recommended rule |
|---|---|
| Specification version | Semantic Versioning `MAJOR.MINOR.PATCH` |
| File version | Required string `schemaVersion: "MAJOR.MINOR"` |
| Patch versions | Clarifications/errata only; no new file semantics |
| Minor versions | Additive-only within a major |
| Major versions | May make incompatible semantic or structural changes |
| Unknown ordinary fields | Consumers MUST ignore them; validators SHOULD warn |
| Unknown fields when rewriting | Editors/round-trippers MUST preserve them |
| Behavior-changing future features | MUST be explicitly feature-detectable |
| Extensions | Only inside an `extensions` namespace object |
| Extension discovery | Top-level `extensionsUsed` and `extensionsRequired` |
| Extension IDs | Registered prefix plus stable extension name |
| Deprecation | Accepted for the lifetime of the major version; never repurposed |
| Text encoding | UTF-8; producers do not emit a BOM |
| Locales | BCP 47 tags |
| Human-facing text | NFC |
| Conformance | Role + version + profile, never an unqualified “conformant” |
| Test regime | Machine-readable requirement-linked fixtures plus round-trip tests |
| Stability gate | At least two independent implementations before a feature is declared stable |

Semantic Versioning defines major versions for incompatible API changes, minor versions for backward-compatible additions, and patch versions for backward-compatible fixes; it also requires released versions to be immutable. A data-format specification has a sufficiently API-like public contract for this model to be useful. citeturn22search1 OpenAPI provides a particularly relevant precedent: its `major.minor` portion denotes the feature set, while patch versions address specification errors and clarifications and should not cause tooling to distinguish, for example, `3.1.0` from `3.1.1`. citeturn19view1turn20view0

A concrete top-level skeleton should look approximately like this:

```json
{
  "schemaVersion": "1.2",
  "id": "example-layout",
  "displayName": "Example",
  "displayNameLocalizations": {
    "fr": "Exemple",
    "de-CH": "Beispiel"
  },

  "featuresRequired": [],

  "extensionsUsed": [
    "ACME_annotations"
  ],
  "extensionsRequired": [],
  "extensions": {
    "ACME_annotations": {
      "reviewState": "approved"
    }
  }
}
```

The exact domain fields will differ, but the envelope should be defined in version 1.0 even if most lists initially remain empty. **Retrofitting feature detection after incompatible extensions already exist is much harder than carrying a few empty arrays from the beginning.**

The most important compatibility invariant should be:

> **A newly introduced construct that an older processor may safely ignore may be additive. A construct whose absence of understanding can alter the meaning or correct processing of the file must be explicitly declared as required.**

That rule makes “ignore unknown fields” safe rather than reckless. glTF uses precisely this separation for extensions: every extension is declared in `extensionsUsed`, while extensions necessary to load or render an asset also appear in `extensionsRequired`; the latter is a subset of the former. citeturn19view3turn19view4turn20view2

The format should also publish a **stability contract** more explicit than SemVer alone. CLDR is an excellent model: every published release is frozen; structural changes are required to remain backward-compatible; deprecated elements remain valid; and complex structural changes are expected to go through design review and, where appropriate, prototype implementation. citeturn24search0turn24search2 That kind of institutional promise is what turns a version number into a decades-long interoperability guarantee.

## Schema and source-file design

**Use JSON Schema Draft 2020-12 as the normative schema dialect, but deliberately use a conservative subset of it.** As of September 2026, Draft 2020-12 remains the current published JSON Schema version. It introduced `prefixItems`, `$dynamicRef`/`$dynamicAnchor`, improved `unevaluated*` behavior, Unicode expectations for regular expressions, and separated `format` annotation from `format` assertion. citeturn22search0turn22search4

Every published schema document should identify the dialect explicitly:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.org/schemas/layout-1.2.schema.json",
  "type": "object"
}
```

The **schema document's** `$schema` and the **instance file's** `schemaVersion` have completely different jobs. `$schema` says which JSON Schema language the schema itself uses. `schemaVersion` says which feature set of your interchange format the data file uses. Do not overload one for the other. JSON Schema describes `$schema` as identifying the schema dialect and `$id` as establishing a schema resource identifier. citeturn22search8turn25search4

A conservative 2020-12 profile should heavily favor:

`type`, `properties`, `required`, `items`, `$ref`, `$defs`, `enum`, `const`, `minimum`/`maximum`, string lengths/patterns, and straightforward `allOf`/`anyOf` where genuinely necessary.

It should use `oneOf` sparingly, and should normally prefer an explicit discriminator such as:

```json
{
  "kind": "literal",
  "value": "..."
}
```

over deciding variants by subtle combinations of present and absent properties. Explicit discriminators produce clearer errors, simpler implementations, cleaner source files, and less ambiguous future extension.

Avoid making fundamental interoperability depend on the more sophisticated corners of the dialect—particularly `$dynamicRef`, complicated recursive evaluation, or `unevaluatedProperties` interactions—unless the data model genuinely needs them. The JSON Schema project itself has acknowledged that the transition between 2019-09 and 2020-12 contained breaking schema-language changes such as the transition from recursive-reference keywords to dynamic-reference keywords and the restructuring of tuple validation. citeturn9search2turn22search0 A file format expected to outlive individual validator libraries benefits from using the least exotic sufficient schema vocabulary.

There is an especially important interaction between JSON Schema and forward compatibility: **do not make the normative compatibility schema globally closed with `additionalProperties: false` or `unevaluatedProperties: false`.** That would directly contradict the requirement that an older implementation accept future optional members.

Instead, separate **conformance** from **linting**:

* The normative schema remains open to future properties.
* The reference validator knows the properties defined in its current specification release and emits an `UNKNOWN_MEMBER` warning for unrecognized ones.
* A `--strict-authoring` or equivalent lint mode may elevate unknown-current-version fields to errors for authors, but that mode must explicitly not define cross-version file conformance.

This solves a real tension. A typo such as `"descripton"` should be visible to an author, but an implementation from 2031 must not reject a perfectly legitimate field introduced in 2034 merely because it did not exist when that implementation's schema was written.

JSON Schema should consequently be treated as **one layer of validation, not the entire specification**. It is excellent for local structure and types, but relationships such as cross-object references, registry lookup, feature support, canonical BCP 47 processing, deprecation rules, and many conditional semantic invariants belong in a second semantic-validation stage. OpenAPI's standards infrastructure similarly distinguishes its textual specification from machine schemas rather than assuming a schema expresses every rule, while glTF supplies a dedicated validator in addition to its JSON schemas. citeturn18view0turn26search1

**Object-member order must never carry semantics.** JSON Schema's data model explicitly treats object properties as unordered, while arrays are ordered. citeturn22search8 Nevertheless, source files should have a defined **canonical presentation order** because humans review diffs, resolve merge conflicts, and diagnose errors.

A good non-normative but exporter-required presentation order is:

1. format/version identification;
2. stable object identity;
3. human-readable metadata;
4. core semantic content;
5. required-feature declarations;
6. extension declarations;
7. extension payloads.

For example, `schemaVersion` should conventionally be the first member, not because a parser is allowed to depend on this, but because it is the first thing a human reviewer needs to see. Generated files SHOULD follow the prescribed presentation order; importers MUST behave identically regardless of object-member ordering.

For generated maps whose member order has no human meaning, a deterministic lexicographic order is desirable. For explicitly authored domain objects, follow the specification's documented property order instead of blindly alphabetizing every property. These two policies minimize diff churn without sacrificing readability.

Do **not** confuse human source ordering with cryptographic canonicalization. RFC 8785's JSON Canonicalization Scheme sorts object property names and defines deterministic JSON serialization specifically for cases such as hashing and signatures. If canonical cryptographic bytes are eventually needed, use such a separate canonicalization procedure rather than forcing cryptographic sorting rules onto hand-maintained source files. citeturn10search1

The recommended source-format presentation profile is therefore:

```text
UTF-8
2-space indentation
LF line endings
newline at end of file
one property per line for nontrivial objects
minimal necessary character escaping
prescribed property presentation order
no trailing commas
no comments
```

The last two points matter because the format should remain **actual JSON**, not “JSON plus whatever a preferred parser accepts.” RFC 8259 defines the interoperable JSON grammar; departing into JSONC, JavaScript object literal syntax, or parser-specific trailing-comma/comment behavior fragments implementations immediately. JSON texts exchanged between systems are to be encoded as UTF-8. citeturn10search0turn11view0 Comments that authors genuinely need should be modeled as explicit data—`description`, `notes`, or an extension—so another implementation can preserve them.

The specification should strengthen JSON's weak guidance on duplicate object names: **a conforming file MUST NOT contain duplicate member names, and a conforming parser/validator MUST detect and reject them before a conventional JSON library can silently collapse them.** RFC 8259 says object member names should be unique and warns that duplicate handling differs among implementations. citeturn10search0 For a trustworthy interchange format, “last value wins in parser A, first value wins in parser B” is unacceptable and can become a security problem.

For naming, prefer format-controlled identifiers that are boring and explicit:

| Prefer | Avoid | Reason |
|---|---|---|
| `schemaVersion` | `ver`, `v` | Meaning survives unfamiliar implementations |
| `displayName` | `label1` | Semantic role is explicit |
| `timeoutMs` | `timeout` | Unit cannot be misinterpreted |
| `enabled` | `notDisabled` | Avoid double negatives |
| `"automatic"` | `2` | String enums are self-explanatory |
| stable string IDs | array-index references | Insertions do not renumber references |

Field names and standardized identifiers should preferably be ASCII. This avoids normalization, casing, keyboard-entry, and confusability issues in the format's structural vocabulary while still allowing unrestricted Unicode in user data.

Use **shallow nesting based on conceptual ownership**, not on an abstract class hierarchy. A nested object is justified when it gives a concept a natural lifetime, namespace, or repeating structure. A wrapper that contains one property solely because a code generator's internal model happens to have another class is not useful format structure.

Similarly, use arrays only where order is semantically relevant or where there is a natural repeated sequence. If entities have stable identities and other entities refer to them, keyed objects or explicit stable IDs are usually more maintainable than positional array indexes. Runtime-oriented formats sometimes favor integer indexing for compactness and fast loading; an authoring/interchange format should optimize for source stability instead.

The specification should have **one preferred notation for one concept**. Avoid conveniences such as accepting both:

```json
"mode": "example"
```

and:

```json
"mode": {
  "value": "example"
}
```

for the same semantic value. Every alternate compact notation doubles parser paths, fixtures, documentation, canonicalization rules, migration cases, and ambiguous edge cases. If the verbose representation is genuinely necessary for future annotations, use it from day one.

More broadly, **do not optimize source JSON for bytes**. Repetition compresses exceptionally well at transport or archive level; obscure syntax costs maintainers forever. OpenType's feature-file ecosystem is instructive precisely because a readable textual authoring language can sit above a compact binary runtime representation. Adobe's OpenType feature-file specification provides a textual source language for authoring data that is ultimately compiled into font tables. citeturn3search7turn25search3 CLDR similarly distinguishes its structured source data from compact representations consumed by libraries. citeturn23search9

USB HID provides the counterexample to copy only where its constraints apply. HID explicitly set compactness, extensibility, unknown-item skipping, nesting, and self-description as design goals; the binary report-descriptor grammar packs item size, type, and tag into a compact encoding and uses local/global parser state. citeturn17search7turn7view1 That is rational for tiny hardware descriptors. It is an anti-pattern for hand-edited JSON. Avoid bit masks, positional tuples, inherited mutable parser state, magic numeric tags, raw byte offsets, index arithmetic, and base64-packed structures whenever ordinary named JSON fields can express the same information.

## Versioning, compatibility, and deprecation

The specification should maintain **two deliberately separate version dimensions**.

**Specification release:** `1.4.2`

**File feature version:** `"schemaVersion": "1.4"`

The specification follows SemVer. The file version is a `MAJOR.MINOR` string and must not contain a patch component. SemVer requires major/minor/patch components to be numeric and compares them numerically, which is another reason `schemaVersion` must be a string rather than a JSON number: `"1.10"` is a perfectly meaningful version that would be destroyed if interpreted as decimal `1.10`. citeturn22search1

The meanings should be fixed as follows:

| Change | Spec version | File `schemaVersion` | Compatibility |
|---|---:|---:|---|
| Typo/editorial clarification | PATCH | unchanged | No acceptance/meaning change |
| Fix non-normative example | PATCH | unchanged | No acceptance/meaning change |
| Correct schema artifact to match already normative text | PATCH | unchanged | Specification semantics unchanged |
| Add optional metadata field | MINOR | new minor | Older readers can ignore it |
| Add optional standardized capability | MINOR | new minor | Must be feature-detectable if behavior-affecting |
| Deprecate a field | MINOR | new minor | Old field remains accepted |
| Remove/repurpose a field | MAJOR | new major | Breaking |
| Change meaning of an existing token | MAJOR | new major | Breaking |
| Change default behavior of an existing valid file | MAJOR | new major | Breaking |

A specification patch should therefore **never alter the meaning of an already conforming data file** and should never turn a formerly conforming file into a nonconforming one. The OpenAPI approach of treating `major.minor` as the feature set and patches as document corrections is an excellent precedent. citeturn19view1 The proposed format should, however, be stricter than current OpenAPI on minor releases: OpenAPI explicitly acknowledges that it may occasionally make non-backward-compatible changes in minor versions when the perceived impact is low. citeturn20view0 A decades-oriented interchange format should prohibit that escape hatch.

Published artifacts should be immutable. A release should consist of one immutable bundle containing at least:

```text
specification 1.4.2
schema(s) for feature set 1.4
extension-registry snapshot
test-suite manifest
reference-validator release
release notes / migration notes
checksums
```

Do not silently replace `schema-1.4.json` with changed contents six months later. SemVer says released version contents must not be modified, and CLDR makes an even stronger promise that a published release is stable and never changes, with corrections handled explicitly. citeturn22search1turn24search2

**Backward compatibility** should be simple: an importer supporting file feature set 1.5 MUST support valid 1.0–1.5 files, subject only to explicitly documented feature/profile limits.

**Forward compatibility** requires a more careful algorithm:

```text
1. Parse schemaVersion.
2. If its major version is unsupported:
      report UNSUPPORTED_MAJOR and stop.
3. Inspect featuresRequired.
4. Inspect extensionsRequired.
5. If any required capability is unsupported:
      report UNSUPPORTED_REQUIRED_FEATURE and stop;
      do not call the file invalid.
6. Ignore unrecognized optional fields and optional extensions.
7. Process all understood semantics.
```

For a file with a higher same-major minor than the implementation understands, processing can be permitted when steps 3–6 prove it safe. That is much stronger than either “always reject newer versions” or “blindly hope all new material is optional.”

This is why a top-level `featuresRequired` mechanism should exist from version 1.0. A future minor feature that changes the correct interpretation of data cannot safely rely on `schemaVersion` alone. An old processor might see `1.7`, understand only 1.4, ignore an unfamiliar property, and produce subtly wrong output. With feature detection, a behavior-affecting addition can say:

```json
{
  "schemaVersion": "1.7",
  "featuresRequired": [
    "core.some-new-semantic-rule"
  ]
}
```

An implementation that does not know that feature then fails honestly instead of silently producing an incorrect result.

There are consequently two categories of additions:

**Ignorable additions** are information whose absence of interpretation cannot change the correct meaning of the understood core. Examples include descriptive metadata and nonessential annotations. These can be ordinary new fields.

**Required semantic additions** change what a correct processor must do. They must have a required feature identifier or required extension identifier.

This interpretation makes the unknown-field rule precise:

> A conforming processor MUST ignore any unrecognized field whose semantics are not declared required. Encountering such a field MUST NOT, by itself, make the file invalid.

SVG 1.1 applied a closely related model: foreign-namespace elements and attributes can be retained while otherwise ignored, while `requiredExtensions` and conditional processing provide a way to say that support is needed. citeturn16search0 HID likewise designed its usage model so software can skip unknown information, demonstrating how long-lived registries benefit from unknown-item tolerance. citeturn17search7turn8view0

There is one additional rule that matters enormously for editors:

> **Ignoring and preserving are different obligations.**

A read-only consumer can ignore an unknown field. A conforming editor, transcoder, or importer→exporter round-tripper MUST preserve unknown fields and unknown optional extensions when it writes the document again, except when the user explicitly requests a lossy conversion or “strip unknown data” operation.

Without that rule, the format is forward-readable but not forward-editable: opening a 1.7 document in a 1.5 editor would silently destroy 1.7 information.

Deprecation must likewise favor preservation. JSON Schema 2020-12 defines `deprecated` as metadata/annotation rather than a validation failure. citeturn0search4 Use that feature, but supplement it with specification metadata:

```json
{
  "oldField": {
    "type": "string",
    "deprecated": true,
    "description": "Deprecated since 1.4; use newField."
  }
}
```

The normative policy should be:

* Importers MUST continue accepting a deprecated field for the remainder of its major version.
* Validators SHOULD emit a deprecation warning with a replacement.
* Exporters SHOULD NOT generate deprecated constructs by default after their replacement is standardized.
* An exporter targeting an older compatibility version MAY generate them when necessary.
* A deprecated identifier is never reassigned to a different meaning.
* Removal is allowed only at a major-version boundary.
* Migration tooling should be available before removal.

CLDR's structural policy is a strong precedent: deprecated elements remain and their use is discouraged, while stable structural evolution remains backward-compatible. citeturn24search0 glTF's extension process similarly retains historical/archived extensions because existing assets still need their definitions. citeturn2search3

The worst evolution mistakes are **repurposing** and **silent semantic drift**. Do not redefine an existing field, enum value, extension ID, default, unit, or identifier to mean something subtly different. Introduce a new spelling and deprecate the old one. A few extra names in a schema cost almost nothing; ambiguous historical interpretation costs every implementation forever.

## Extensions, registries, and internationalization

Extensions should be **structurally namespaced**, not sprinkled through the normal property namespace.

The recommended mechanism is directly inspired by glTF:

```json
{
  "extensionsUsed": [
    "ACME_reviewMetadata",
    "EXT_sharedCapability"
  ],
  "extensionsRequired": [
    "EXT_sharedCapability"
  ],
  "extensions": {
    "ACME_reviewMetadata": {
      "status": "verified"
    },
    "EXT_sharedCapability": {
      "mode": "example"
    }
  }
}
```

Nested objects that need extension points may also carry their own `extensions` object:

```json
{
  "id": "item-a",
  "extensions": {
    "ACME_reviewMetadata": {
      "source": "internal"
    }
  }
}
```

glTF permits an optional `extensions` property on its objects and separately requires all used extensions to be enumerated at the top level; extensions necessary for correct loading/rendering also appear in `extensionsRequired`. citeturn20view2turn19view3turn19view4 This is preferable to free-standing `x-*` properties for this particular format because every extension payload has a well-defined preservation boundary and tools can distinguish “unknown future core field” from “unknown extension payload” without heuristics.

OpenAPI demonstrates the lighter alternative: specification-extension field names begin with `x-`, with some `x-oai-` and `x-oas-` namespaces reserved and registries maintained for extensions and extension namespaces. citeturn21view0 That works well when extension metadata naturally occurs beside many fixed fields. For a long-lived hand-maintained format, a single `extensions` container is cleaner: it reduces accidental collisions, keeps diffs legible, and gives unaware editors an obvious subtree to preserve.

A glTF-like prefix convention is a good compromise between human readability and collision avoidance:

| Prefix class | Example | Meaning |
|---|---|---|
| Standards-body | `STD_feature` | Ratified extension |
| Multi-implementation | `EXT_feature` | Public extension supported by multiple parties |
| Registered vendor | `ACME_feature` | Vendor/project-controlled extension |

The actual reserved standards prefix should of course use the project's real name rather than literal `STD`.

glTF reserves `KHR` for Khronos extensions, `EXT` for multi-vendor extensions, and maintains a registry of vendor prefixes; requesting a vendor prefix is deliberately lightweight, via a public issue, rather than requiring the extension itself to be standardized. citeturn26search0 OpenType has used a comparable registry concept for decades: registered feature tags occupy a controlled space, while four-uppercase-letter tags are reserved as a private vendor space. citeturn25search6

That suggests an important registry-governance principle: **namespace allocation should be cheap; semantic standardization should be rigorous.** A vendor should not need committee approval merely to avoid collisions.

The registry should be machine-readable and record, for every extension:

```json
{
  "id": "ACME_reviewMetadata",
  "status": "vendor",
  "owner": "Acme",
  "specificationVersion": "1.1.0",
  "introducedWithSchemaVersion": "1.2",
  "dependencies": [],
  "conflicts": [],
  "supersededBy": null,
  "deprecated": false,
  "schema": "...",
  "testSuite": "..."
}
```

A real registry entry also needs durable human contact/ownership information and pointers to the immutable extension specification and schema artifacts. The registry itself should preserve history rather than merely showing the current state.

A useful extension lifecycle is:

| State | Admission requirement | Stability expectation |
|---|---|---|
| Vendor/private | Registered prefix + published identifier | Owner controlled |
| Experimental | Public specification + schema | May evolve |
| Multi-vendor | At least two independent implementations + tests | Backward-compatible evolution |
| Ratified | Governance review + complete conformance suite | Full stability policy |
| Deprecated | Replacement/migration documented | Still readable |
| Archived | No new use recommended | Identifier and historical specification retained forever |

glTF's registry distinguishes Khronos-ratified, multi-vendor, and vendor extensions and uses public repository processes for extension development and promotion. citeturn2search3turn26search0 The key transferable lesson is not the exact names; it is that extension maturity is visible and that experimental success can lead to standardization **without changing the representation mechanism**.

Extensions should obey several invariants:

**An extension MUST NOT redefine the meaning of a core property.** It may add information or behavior at explicitly extensible points.

**An extension MUST NOT depend on a parser interpreting an unknown ordinary field magically.** Required behavior is declared.

**An extension identifier MUST never be reused.**

**Deprecated and archived extension specifications remain available indefinitely.**

**Every standardizing extension ships schema and conformance tests before promotion.**

**Extension dependencies and conflicts are declared rather than buried in prose.**

The format's own internationalization needs the same degree of explicitness.

JSON files should be UTF-8. RFC 8259 requires UTF-8 for interoperable JSON exchange and says generators must not add a byte-order mark, while parsers may choose to tolerate one. citeturn11view0 The format should turn that into:

* Producers MUST emit UTF-8.
* Producers MUST NOT emit a BOM.
* Consumers SHOULD accept and ignore a UTF-8 BOM as a robustness measure, but SHOULD warn.
* Validators MUST reject malformed UTF-8 and invalid Unicode scalar-value sequences rather than letting different language runtimes reinterpret them differently.

Localized metadata should use **BCP 47 language tags**, not home-grown `language_country` strings. RFC 5646 defines the language-tag structure, registration model, private-use mechanism, and case-insensitive semantics. citeturn22search2turn22search6 CLDR's LDML similarly bases its stable language and locale identifiers on BCP 47. citeturn23search3

A hand-maintainable representation is:

```json
{
  "displayName": "Example",
  "displayNameLocalizations": {
    "en-GB": "Example",
    "fr": "Exemple",
    "sr-Latn": "Primer"
  },

  "description": "A human-readable description.",
  "descriptionLocalizations": {
    "fr": "Une description lisible."
  }
}
```

This is preferable to a field whose type changes between a string and an object depending on whether translations exist. A fixed type makes schemas, editors, APIs, and diffs simpler.

The base `displayName`/`description` serves as an explicit fallback. It should not be assigned an invented locale automatically. Keys in localization maps MUST be syntactically valid BCP 47 tags. Producers SHOULD use canonical/preferred BCP 47 casing and values; processors compare tags case-insensitively because case does not carry language-tag semantics. citeturn22search2 Deprecated but otherwise valid language tags are better handled by warnings plus canonical replacements than by turning historical files invalid.

The specification should also define its localization fallback algorithm instead of saying merely “choose the nearest locale.” At minimum:

```text
exact requested language tag
→ explicitly defined parent/fallback rule
→ base unlocalized value
```

If sophisticated language negotiation is required, standardize one algorithm rather than letting each implementation invent one.

For Unicode normalization, **NFC is the right default for format metadata intended for humans.** Unicode Normalization Form C is designed to give canonically equivalent text a stable composed representation, and Unicode maintains strong normalization-stability guarantees across versions. citeturn22search3 Thus:

* Human-facing names, descriptions, registry labels, and similar metadata SHOULD be NFC.
* Standardized field names and machine identifiers should be ASCII where practical.
* A validator SHOULD warn when human-facing text is not NFC and MAY offer an explicit normalization fix.
* A processor MUST NOT silently apply NFKC to arbitrary user content. Compatibility normalization can erase distinctions that may be meaningful.
* Domain-specific string fields whose exact Unicode sequence matters must state their own normalization semantics. There should be no blanket rule that rewrites every string in a file.

The broad principle is: **normalize format metadata deliberately; preserve semantic payload deliberately.**

## Conformance contracts

The specification should adopt BCP 14 normative language. RFC 2119 defines the familiar requirement terms such as MUST, SHOULD, and MAY; RFC 8174 updates that convention by making the special normative interpretation apply only when those terms appear in uppercase. citeturn0search2turn16search1 OpenAPI's current specification uses the combined RFC 2119/RFC 8174 formulation. citeturn20view0

Use those words sparingly. A `MUST` should correspond to something necessary for interoperability, safety, or the defined semantics, not merely the authors' preferred style. Diff formatting, for example, normally deserves an exporter `SHOULD`, while rejecting duplicate property names deserves a `MUST`.

The specification should not define a single ambiguous notion of “conforming implementation.” It should define separate **conformance roles**.

| Role | Conformance means |
|---|---|
| File | The bytes, JSON structure, feature declarations, and semantics satisfy the requirements for the declared schema version/profile |
| Importer | Accepts every conforming file in its claimed capabilities and interprets supported semantics correctly |
| Processor | Performs the processing behavior required by its claimed profile and features |
| Exporter | Every file it emits conforms to its declared target version/profile and advertises required capabilities accurately |
| Editor / round-tripper | Is a conforming importer and exporter **and** preserves unknown optional data and extensions across edits |
| Validator | Correctly distinguishes valid, invalid, unsupported, deprecated, and noncanonical cases for its claimed versions |

This lets an implementation truthfully say:

```text
Importer: Core 1.0–1.4
Exporter: Core 1.4
Editor preservation: yes
Extensions:
  EXT_example 1.0
  ACME_annotations 2.1
```

instead of the meaningless statement “supports the format.”

A **conforming file** is not synonymous with “a file that this implementation understands.” Consider:

```json
{
  "schemaVersion": "1.3",
  "extensionsUsed": ["ACME_feature"],
  "extensionsRequired": ["ACME_feature"],
  "extensions": {
    "ACME_feature": {
      "mode": "x"
    }
  }
}
```

An importer without `ACME_feature` should return something equivalent to:

```text
file validity: valid
processing status: unsupported
reason: required extension ACME_feature is not implemented
```

It must not claim the file itself is malformed.

Likewise, a file containing an unknown optional extension can be:

```text
file validity: valid
processing status: success-with-ignored-optional-extension
```

This distinction should appear in the machine-readable validator API, not merely in prose.

Profiles should also be explicit, but avoid creating a permanently moving target named simply “Full.” A better structure is:

**Core profile.** The minimum interoperable feature set that every general-purpose processor must implement.

**Full-X.Y profile.** All standardized, non-vendor features defined for a particular `schemaVersion`, for example `Full-1.4`.

**Extension capabilities.** Claimed individually by stable extension IDs.

Pinning “Full” to a feature version prevents the statement “full support” from becoming false whenever the standard gains a new feature.

SVG's history demonstrates both the usefulness of profiles and the need to name them precisely: its implementation reports distinguish Full and Tiny-profile implementations rather than treating every renderer as one undifferentiated conformance class. citeturn26search6 CLDR's conformance approach is similarly feature-specific: its specification and conformance work identify particular sections/features rather than assuming all software necessarily implements the whole CLDR universe. The current CLDR Conformance Testing Working Group explicitly maintains test data and scores implementations against UTS #35 behavior. citeturn23search5

The proposed Core profile should include, from day one:

| Core obligation | Why it belongs in Core |
|---|---|
| UTF-8 parsing and duplicate-member rejection | Deterministic input model |
| `schemaVersion` handling | Evolution |
| Unknown optional field tolerance | Forward compatibility |
| `featuresRequired` handling | Safe feature detection |
| Extension envelope parsing | Extensibility |
| `extensionsRequired` failure behavior | Prevent silent misprocessing |
| BCP 47 handling for localized metadata | International interoperability |
| Required Unicode normalization checks | Stable text interchange |
| Structured diagnostic model | Cross-tool trust |

Preservation of unknown data should be mandatory for the **Editor** role rather than for every processor. A one-shot compiler has no reason to retain an extension it does not use; an editor that writes the file back absolutely does.

The specification should assign stable IDs to normative requirements, for example:

```text
CORE-FILE-001
CORE-FILE-002
CORE-IMPORT-001
CORE-EXPORT-003
I18N-004
EXT-007
```

Then the normative text, test manifest, validator diagnostics, and conformance report can all point to the same requirement. This is much more maintainable than a suite whose test names have no traceable connection to normative clauses.

Finally, separate **validity** from **canonicality**:

```text
ERROR    → file is not conforming
UNSUPPORTED → file may be conforming, processor lacks required capability
WARNING  → conforming but discouraged/deprecated/suspicious
INFO     → canonicalization or presentation advice
```

Examples:

```text
E_DUPLICATE_MEMBER
E_WRONG_TYPE
E_SEMANTIC_REFERENCE
U_REQUIRED_FEATURE
U_REQUIRED_EXTENSION
W_UNKNOWN_MEMBER
W_DEPRECATED_MEMBER
W_NONCANONICAL_BCP47
W_NON_NFC_METADATA
W_NONCANONICAL_ORDER
```

This diagnostic vocabulary should itself be versioned and machine-readable.

## Validation and test-suite regime

A standards document and JSON Schema are not enough to make a multi-implementation ecosystem trustworthy. The test suite needs to be treated as a **first-class standards artifact** and released at the same time as the specification and schemas.

JSON Schema provides perhaps the cleanest transferable model: its official Test Suite uses language-neutral JSON test data, allowing the same cases to be run against implementations written in different languages. The JSON Schema project's Bowtie tooling then runs the official suite across numerous independent implementations and makes differences visible. citeturn2search1turn25search0 That is precisely the architecture an open keyboard-layout format should seek.

The reference validator should use a staged pipeline:

```text
raw byte validation
        ↓
JSON lexical/parsing validation
        ↓
JSON Schema validation
        ↓
format semantic validation
        ↓
feature/extension capability analysis
        ↓
registry validation
        ↓
lint/canonicalization diagnostics
```

This ordering matters. A conventional JSON parser often loses information such as duplicate member names before an application can inspect them, so duplicate-name detection has to occur at the raw JSON parsing stage. BCP 47 canonicality, cross-reference integrity, extension dependencies, and required-feature support cannot reliably be delegated to ordinary JSON Schema.

JSON Schema's `format` facility deserves special caution: in Draft 2020-12, format handling is split into annotation and assertion vocabularies, and format is not automatically a universally portable assertion mechanism. citeturn0search4turn22search0 Therefore do not assume that writing:

```json
{
  "format": "bcp47"
}
```

would somehow create interoperable BCP 47 validation. If a `bcp47` format annotation is useful for documentation/tooling, use it, but the reference semantic validator still needs normative BCP 47 validation behavior.

The validator's output should be JSON as well as human-readable:

```json
{
  "valid": true,
  "processable": false,
  "schemaVersion": "1.4",
  "diagnostics": [
    {
      "code": "U_REQUIRED_EXTENSION",
      "severity": "unsupported",
      "pointer": "/extensionsRequired/0",
      "requirement": "EXT-007",
      "extension": "ACME_example"
    }
  ]
}
```

Diagnostics should always include, where applicable, a stable code, severity, JSON Pointer, normative requirement ID, and enough structured data for IDEs and CI systems. glTF's ecosystem demonstrates the usefulness of providing a dedicated validator accessible through CLI/editor/web workflows rather than leaving every implementer to invent validation independently. citeturn26search1

The reference validator must nevertheless **not become the normative specification**. When validator behavior and the written standard disagree, that is a validator bug or specification issue that must be resolved openly. Otherwise implementers end up reverse-engineering an executable oracle rather than implementing an open standard.

The minimum pre-1.0 fixture corpus should contain the following cross-cutting cases in addition to domain-specific tests:

| Fixture family | Minimum cases | Required result |
|---|---|---|
| Minimal positive | Smallest valid Core file | Valid |
| Maximal positive | Every Core optional field represented | Valid |
| Historical | Representative file for every released minor | Valid in all later same-major processors |
| Wrong primitive type | String/object/number mismatch | Invalid |
| Missing required member | One per required-rule class | Invalid |
| Duplicate member | Same property repeated | Invalid before normal parse |
| Encoding | Malformed UTF-8; BOM case | Invalid / warning as specified |
| Semantic relationship | Schema-valid but semantically impossible reference | Invalid |
| Unknown optional member | Top-level and nested | Valid + warning |
| Future same-major minor | Unknown optional additions only | Processable |
| Unsupported major | Future major | Unsupported |
| Unknown optional extension | Present in `extensionsUsed` only | Valid and processable |
| Unknown required extension | Listed in `extensionsRequired` | Valid but unsupported |
| Known extension | Valid and invalid payload | Correct extension result |
| Feature detection | Unsupported `featuresRequired` token | Valid but unsupported |
| BCP 47 | Canonical, noncanonical-equivalent, deprecated, malformed | Valid/warning/error as defined |
| Unicode normalization | NFC and canonically equivalent NFD metadata | Correct warning/normalization policy |
| Deprecated field | Historical deprecated field | Valid + deprecation warning |
| Unknown preservation | Edit known value while unknown field exists | Unknown data survives |
| Unknown extension preservation | Edit core data around unknown extension | Extension survives |
| Core round-trip | import→export→import | Semantic equivalence |
| Historical round-trip | Older minor through current editor | No semantic loss |
| Canonical formatting | Noncanonical input→export | Stable expected presentation |

The stronger general rule is:

> **Every machine-testable normative MUST/MUST NOT has at least one positive or applicability test and at least one failure/boundary test.**

That creates traceability between specification development and conformance development. A normative clause that cannot be mapped to any test deserves special review: either it is inherently observational, or it may be underspecified.

Round-trip testing needs multiple definitions of equivalence.

For ordinary import/export:

```text
parse(file A)
→ semantic model A
→ export(file B)
→ parse(file B)
→ semantic model B

semantic model A == semantic model B
```

Byte equality is inappropriate because whitespace, escaping, and object-member ordering are not semantic in JSON. JSON Schema's own data model treats object ordering as insignificant. citeturn22search8

For an editor, add:

```text
unknown JSON data before edit
== unknown JSON data after edit
```

at the JSON data-model level.

And separately, for deterministic exporters:

```text
canonicalExport(parse(canonicalExport(x)))
== canonicalExport(x)
```

That second property detects unstable property ordering and formatting rules.

Do not require editors to preserve the exact original whitespace of unknown extension data unless there is a compelling use case. Requiring semantic JSON preservation is far more implementable. If an extension genuinely carries byte-significant signed content, it should define an explicit signed/canonicalized representation rather than assuming generic JSON editors preserve its lexical byte stream.

The machine-readable test-suite format can itself stay extremely simple:

```json
{
  "suiteVersion": "1.4.0",
  "tests": [
    {
      "id": "forward.unknown-optional-member",
      "requirement": "CORE-IMPORT-012",
      "profile": "core",
      "roles": ["importer", "editor"],
      "input": "forward/unknown-optional.json",
      "expect": {
        "fileValid": true,
        "processable": true,
        "diagnosticCodes": ["W_UNKNOWN_MEMBER"]
      }
    }
  ]
}
```

Do not encode tests in one implementation's unit-test language. The JSON Schema Test Suite's language-agnostic fixture model is specifically valuable because independent implementations consume the same source corpus. citeturn2search1turn25search0

For a mature test regime, add a public cross-implementation results matrix. W3C's SVG 1.1 suite was accompanied by implementation reports; its Second Edition Candidate Recommendation process sought evidence that each part of the specification was implementable, with tests passing in at least two implementations. citeturn26search2turn26search6 That is a powerful governance gate:

> A new standardized feature should not advance from experimental to stable until its normative tests pass in at least two independent implementations whose relevant code does not share the same underlying parser/validator library.

CLDR has reached a similar modern approach: its Conformance Testing Working Group is explicitly responsible for code and test data that compare independent implementations of UTS #35 behavior and publishes conformance results. citeturn23search5

For extension promotion, require the same package:

```text
extension specification
+ schema fragment
+ positive fixtures
+ negative fixtures
+ feature-detection fixture
+ round-trip fixture
+ migration/deprecation rules where relevant
+ two independent implementations for multi-vendor/stable status
```

Sample/golden files serve a second role beyond conformance. glTF maintains sample assets and a dedicated validator because realistic end-to-end artifacts exercise combinations that isolated schema tests do not. citeturn12search2 Your project should therefore keep two corpora distinct:

**Conformance fixtures** are usually tiny and atomic; each demonstrates one requirement.

**Golden examples** are realistic, documented, human-readable complete files. They exercise feature combinations and are used by tutorials, regression tests, implementations, and review.

Finally, every released version of the test suite must remain runnable. Do not continuously mutate a single `tests/latest/` corpus so that an implementation cannot reproduce its 1.2 conformance result five years later. Version the suite alongside the standard, and preserve release artifacts permanently, following the immutability philosophy used by CLDR. citeturn24search2

## Lessons from long-lived formats and adoption checklist

The most transferable lessons emerge when the successful properties and the historical compromises are considered together.

| Format | Versioning and extensibility approach | What to copy | What not to copy |
|---|---|---|---|
| **Unicode / CLDR** | Immutable releases; stable BCP 47-based identifiers; structural changes expected to remain backward-compatible; deprecated structures retained. citeturn24search0turn24search2turn23search3 | Publish an explicit stability policy stronger than “we use versions.” Preserve old identifiers and structures. Require design review/prototypes for complex changes. | Do not let the source grammar become as sprawling as a decades-old internationalization data model if a shallower JSON model suffices. Keep conversion/runtime representations separate from authoring source. |
| **glTF** | Stable core plus object-level `extensions`; top-level `extensionsUsed` / `extensionsRequired`; KHR, EXT, and registered vendor prefixes. citeturn20view2turn26search0 | Copy required-vs-optional capability detection almost directly. Maintain a public prefix/extension registry and promotion lifecycle. Preserve archived definitions. | glTF is deliberately runtime-oriented and has binary/index-oriented structures; those optimizations are inappropriate defaults for a hand-edited interchange source. |
| **OpenAPI** | `major.minor` denotes feature set; patch is clarification/error correction; `x-` extensions and extension registries. citeturn19view1turn21view0 | Copy the distinction between feature version and specification patch version. Copy explicit extension namespace reservation. | Do **not** copy OpenAPI's stated allowance for occasional non-backward-compatible minor changes. A decades-oriented format should make minors strictly additive. citeturn20view0 |
| **OpenType** | Long-lived registries of compact semantic tags; controlled registered space plus vendor-private tag space; textual feature source can compile to binary font structures. citeturn25search2turn25search6turn3search7 | Copy stable tag/namespace registries and the principle that human authoring syntax can be different from compact runtime encoding. | Binary offsets, packed flags, positional structures, and compact tags are justified in font binaries but are poor source-language defaults. Do not expose compilation artifacts just because implementations ultimately need them. |
| **USB HID** | Compact self-describing report descriptors; separately evolving usage registries; software designed to skip unknown information. citeturn17search7turn17search0 | Copy the separation between stable grammar and extensible registries, and the principle that unknown optional information should not break old implementations. | HID's size/type/tag packing and parser state are appropriate to device descriptors, not hand maintenance. Avoid stateful or opaque encoding in JSON. citeturn7view1 |

SVG contributes two additional lessons that are worth retaining even though it is not needed as another row in the compact comparison. First, foreign namespaces demonstrated that a base format can carry application-private data while unaware implementations retain/ignore it; conditional processing and `requiredExtensions` supplied capability detection when ignorance would not be safe. citeturn16search0 Second, W3C treated a public test suite and implementation report as evidence of interoperable implementability, not as an afterthought after the Recommendation was complete. citeturn16search4turn26search2turn26search6

OpenType offers a particularly relevant source-vs-runtime lesson. Its compact binary format has succeeded extraordinarily well as a deployment artifact, but its ecosystem also needs higher-level textual feature descriptions for humans. citeturn25search2turn3search7 USB HID makes the same point from another direction: its official goals explicitly emphasize compactness to save device storage as well as self-description and extensibility. citeturn17search7 Those are not the constraints of this JSON source format. **Do not import an optimization merely because it proved successful under a different cost model.**

CLDR's strongest lesson is organizational rather than syntactic. It states that published releases are immutable reference points, requires structural evolution to remain backward-compatible, leaves deprecated structures available, and routes nontrivial design changes through explicit review/prototyping. citeturn24search0turn24search2 That is what allows an ecosystem to trust that today's files will remain intelligible decades later.

The resulting concrete adoption checklist is:

| Area | Rule to adopt before version 1.0 |
|---|---|
| **JSON dialect** | Use strict RFC 8259 JSON and UTF-8. Reject duplicate member names. No comments or trailing commas in the interchange syntax. citeturn10search0turn11view0 |
| **Schema dialect** | Publish JSON Schema Draft 2020-12 schemas with explicit `$schema`/`$id`; use a conservative vocabulary subset. citeturn22search0turn22search8 |
| **Schema openness** | Do not close extensible core objects with `additionalProperties: false`; catch unknown-current fields through lint warnings instead. |
| **File version** | Require `schemaVersion` as a `MAJOR.MINOR` string. Conventionally place it first. |
| **Spec version** | Release the specification as SemVer `MAJOR.MINOR.PATCH`; patch never changes file meaning. citeturn22search1turn19view1 |
| **Minor evolution** | Additive-only. Existing properties, enum tokens, units, defaults, and IDs never change meaning. |
| **Major evolution** | Breaking changes only when unavoidable, with published migration tooling and transition documentation. |
| **Unknown fields** | Consumers MUST ignore unknown optional fields. Validators SHOULD warn rather than reject. |
| **Unknown preservation** | Editors and round-tripping transcoders MUST preserve unknown fields and extension payloads. |
| **Required feature detection** | Define `featuresRequired` in 1.0. Any future standardized addition that can change correct behavior must advertise a feature ID. |
| **Extensions** | Put payloads under `extensions`; declare `extensionsUsed` and `extensionsRequired`, following the proven glTF distinction. citeturn20view2 |
| **Namespaces** | Reserve standards and multi-vendor prefixes and operate a cheap public vendor-prefix registry. Never recycle identifiers. citeturn26search0turn25search6 |
| **Extension registry** | Record ownership, status, version, dependencies, replacement/deprecation, schemas, and tests. Preserve archived entries indefinitely. |
| **Deprecation** | Deprecated constructs stay valid through the major version; exporters stop generating them by default; replacements are explicit. citeturn0search4turn24search0 |
| **Field names** | Prefer explicit ASCII `lowerCamelCase`; spell out concepts; encode units in names where units are not intrinsically fixed. |
| **References** | Prefer stable string IDs over positional array indexes wherever source stability matters. |
| **Notation** | Use one explicit representation per concept. Avoid scalar-vs-object shorthand, positional tuples, bitfields, and generated opaque encodings. |
| **Nesting** | Nest only for conceptual ownership, repeated structures, or namespace boundaries; avoid code-generator-driven wrapper levels. |
| **Formatting** | Specify a canonical exporter presentation order, indentation, line-ending, and escaping style, while declaring member order semantically irrelevant. citeturn22search8 |
| **Signatures/hashing** | If eventually required, define canonicalization separately—e.g. RFC 8785-style canonical JSON—rather than turning cryptographic ordering into authoring style. citeturn10search1 |
| **Localization** | Use BCP 47 keys for localized names/descriptions; canonical forms SHOULD be emitted and comparisons are case-insensitive. citeturn22search2 |
| **Unicode** | Human-readable format metadata SHOULD be NFC; arbitrary semantic content is not silently compatibility-normalized. citeturn22search3 |
| **Normative prose** | Use BCP 14 terminology via RFC 2119 plus RFC 8174; uppercase normative keywords only. citeturn0search2turn16search1 |
| **Profiles** | Define `Core` plus version-pinned `Full-X.Y`; extensions are claimed individually. Never publish an unqualified “Full forever” profile. |
| **Conformance roles** | Separately define File, Importer/Processor, Exporter, Editor, and Validator conformance. |
| **Requirement IDs** | Give machine-testable normative clauses stable IDs and link tests and diagnostics to those IDs. |
| **Reference validator** | Validate bytes → JSON → schema → semantics → features/extensions → lint. Emit structured JSON diagnostics. |
| **Fixtures** | Ship atomic valid/invalid fixtures, historical-version fixtures, unknown-field cases, extension cases, BCP 47/Unicode cases, and realistic golden examples. |
| **Round trips** | Require semantic import→export→import equality; separately test unknown-data preservation and canonical-output idempotence. |
| **Test format** | Keep conformance vectors implementation-neutral and machine-readable, following the JSON Schema Test Suite pattern. citeturn2search1turn25search0 |
| **Interoperability gate** | Before declaring a standard feature stable, require its tests to pass in at least two genuinely independent implementations, following the spirit of W3C implementation reports. citeturn26search6 |
| **Release discipline** | Release immutable specification, schemas, test suite, registry snapshot, validator, changelog, and checksums together. CLDR's frozen-release discipline is the model. citeturn24search2 |

The overarching engineering choice is therefore **not to make the JSON as compact as possible, nor the schema as clever as possible**. It is to minimize the amount of historical knowledge that a future implementer needs in order to interpret an old file correctly.

A durable format should be intentionally boring at the syntax layer: explicit names, ordinary objects, stable IDs, shallow structures, UTF-8, BCP 47, straightforward JSON Schema, and a visible extension envelope. Sophistication belongs instead in the format's **governance mechanisms**: strict additive evolution, immutable releases, explicit feature negotiation, never-reused registry identifiers, role-specific conformance, unknown-data preservation, machine-readable tests, and cross-implementation evidence.

That combination is what the strongest precedents demonstrate. Unicode/CLDR shows that stability promises can survive decades of functional growth. glTF shows how an extension system can grow rapidly without fragmenting the core. OpenAPI provides an unusually clear model for separating specification patch revisions from document feature versions. OpenType shows the value of permanent semantic registries and of keeping human authoring representations distinct from optimized runtime structures. USB HID shows both how powerful unknown-item tolerance can be and why compact stateful representations should not be copied outside severely constrained environments. SVG shows the payoff from pairing extensibility with explicit capability tests and from making implementation test results part of the standards process. citeturn24search0turn20view2turn19view1turn25search6turn17search7turn16search0turn26search6