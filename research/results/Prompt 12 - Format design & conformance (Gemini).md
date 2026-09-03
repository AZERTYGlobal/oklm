# **Architectural Principles for Decadal JSON Specification Engineering**

Designing an open, JSON-based data interchange format intended to serve as an industry standard for decades requires balancing immediate expressiveness with long-term structural stability. Data formats that endure across decades—such as Unicode, OpenType, glTF, and USB HID—succeed not because they anticipate every future requirement, but because their meta-architecture gracefully accommodates evolution without breaking existing implementations1.  
When engineering an open schema for data interchange, format designers must establish clear boundaries between core semantics, extensibility mechanisms, and conformance regimes. This technical report provides concrete schema engineering directives, versioning strategies, extensibility models, internationalization rules, and test-suite designs for an open, machine-readable format optimized for long-term durability and hand-maintainability.

## **Schema Architecture and File Design for Longevity**

### **Meta-Schema Selection: JSON Schema Draft 7 versus Draft 2020-12**

The choice of JSON Schema meta-schema governs how tools across heterogeneous language ecosystems validate instances. While newer iterations exist, selecting the correct draft requires evaluating compiler support across legacy, embedded, and modern application environments.

| Evaluation Metric | JSON Schema Draft 7 | JSON Schema Draft 2020-12 |
| :---- | :---- | :---- |
| **Ecosystem Adoption** | Universal across C++, Rust, Go, Python, Java, and JavaScript4. | Moderate and growing; limited in native C/embedded validators6. |
| **Unknown Property Evaluation** | Evaluated via additionalProperties within single subschemas4. | Evaluated dynamically via unevaluatedProperties across adjacent schemas8. |
| **Dynamic Reference Resolution** | Restricted to basic static $ref and $id URI targets4. | Supports dynamic runtime scoping via $dynamicRef and $dynamicAnchor8. |
| **Validation Pipeline Complexity** | Direct, deterministic constraint evaluation4. | Requires decoupled applicator and annotation processing stages8. |

JSON Schema Draft 7 remains the most universally supported schema version across enterprise, web, and system-level languages4. Standard libraries in C++, Rust, Go, Python, and Java possess mature, production-grade Draft 7 validators4. Conversely, Draft 2020-12 introduces keywords such as unevaluatedProperties and unevaluatedItems, which alter how subschemas evaluate unknown properties across allOf or $ref boundaries6. While Draft 2020-12 simplifies complex schema inheritance8, its adoption in low-level systems programming languages (such as C/C++ parser libraries used in microcontrollers or desktop drivers) remains uneven.  
To maximize parser interoperability across diverse runtime targets, a long-lived format specification MUST provide a canonical JSON Schema Draft 7 meta-schema as its primary compliance baseline4. The specification MAY additionally publish an official Draft 2020-12 schema translation for modern toolchains that utilize advanced applicator evaluation6.

### **Human Maintainability, Canonical Sorting, and Diff-Friendliness**

Structured data files are frequently edited directly by humans and tracked in version control systems. Formatting noise in pull requests severely impairs long-term maintainability. Although JSON object key ordering is semantically unordered under RFC 825910, serializers MUST default to a deterministic key order. Adopting the ordering rules of RFC 8785 (JSON Canonicalization Scheme \- JCS) guarantees that keys are sorted lexicographically by their UTF-16 code unit representations11. This prevents arbitrary key reordering across different export tools from polluting source control diffs11.  
Field names MUST use full, descriptive camelCase identifiers (such as primaryLegend, actuationDistance, or matrixRow) rather than compact or truncated names. Micro-optimizations in string length yield negligible bandwidth savings compared to the cognitive burden placed on developers and hand-maintainers. Furthermore, data hierarchies MUST NOT exceed four levels of structural depth. Deeply nested objects increase schema rigidity and complicate code paths in lightweight parsers.  
Formats that pack multiple domain values into single string attributes (for example, "matrix": "0x01;12;press;toggle") force implementers to write secondary parsers outside the JSON Schema validation engine. All domain primitives MUST be explicitly typed as native JSON objects, arrays, integers, booleans, or strings.

## **Specification Evolution, Versioning, and Compatibility Lifecycles**

### **Decoupling Specification SemVer from File Schema Versioning**

A critical design mistake in long-lived specifications is confusing the version of the written standard with the structural schema version embedded within instances. The format MUST distinguish between these two version concepts:

* **Specification Version**: Follows Semantic Versioning 2.0.0 (MAJOR.MINOR.PATCH). It indexes the overall release of the specification document, test suites, and reference implementations.  
* **File Schema Version (schemaVersion)**: A top-level integer field (for example, "schemaVersion": 1\) inside the JSON instance. This value increments **only** when a breaking structural change occurs that renders legacy parsers fundamentally incapable of safely processing the document.

Minor and patch updates to the specification MUST NOT increment the schemaVersion requirement in data files.

### **Compatibility Directives and Deprecation Policies**

To maintain forward and backward compatibility across decades, specification authors and parser engineers MUST adhere to four core directives:

#### **Additive-Only Evolution**

All fields introduced in minor specification revisions MUST be optional. The addition of a new property MUST NOT alter the semantic interpretation of pre-existing fields.

#### **The Unknown Field Processing Rule**

Parsers MUST ignore unknown JSON properties encountered in objects1. An unknown field MUST NOT cause a parser to halt, fail validation, or discard the file1. Furthermore, non-destructive editing tools (such as visual configurators) MUST preserve unrecognised top-level and property-level fields during import-export cycles to prevent stripping metadata authored by newer or extended tools2.

#### **Deprecation Lifecycle**

Drawing from the Unicode Stability Policy, structural definitions and attributes are never removed or reassigned once finalized3. When a field is superseded:

> 1. The field is marked "deprecated": true in the JSON Schema.  
> 2. The specification maintains the field as optional for at least one major specification lifecycle.  
> 3. Deprecated fields are never repurposed for new semantics; their names remain permanently retired3.

#### **Feature Detection over Version Checking**

Conforming tools MUST evaluate document capabilities by inspecting the presence of specific fields or extension declarations rather than performing strict schemaVersion equality checks1.

## **Extensibility Frameworks and Registry Mechanics**

JSON  
{  
  "schemaVersion": 1,  
  "extensionsUsed": \[  
    "LOGI\_lightsync",  
    "EXT\_analog\_actuation"  
  \],  
  "extensionsRequired": \[  
    "EXT\_analog\_actuation"  
  \],  
  "primaryLegend": "A",  
  "extensions": {  
    "LOGI\_lightsync": {  
      "rgbZone": 2  
    }  
  },  
  "extras": {  
    "internalAssetId": 89210  
  }  
}

### **Dual-Layer Extensibility Architecture**

To allow hardware vendors and open-source communities to innovate without forking the base standard, the format MUST adopt a dual-layer extensibility structure modeled on glTF 2.02:

* **The extensions Object**: Reserved for structured, namespaced extensions that possess formal schemas1. Every core JSON object in the schema MAY contain an optional extensions map1.  
* **The extras Object**: Reserved for unstructured application-specific metadata2. Storage in extras carries no structural validation guarantees and MUST NOT affect core layout rendering or functional behavior across independent implementations2.

### **Extension Naming and Lifecycle Progression**

Extensions follow a three-tier naming hierarchy designed to allow features to mature naturally from single-vendor experiments into core specification features1:

| Tier | Prefix Pattern | Governance and IP Scope | Example Identifier |
| :---- | :---- | :---- | :---- |
| **Vendor Extension** | VENDOR\_ | Controlled by a single vendor or entity. Registered via prefix2. | LOGI\_lightsync |
| **Multi-Vendor Extension** | EXT\_ | Approved and maintained by two or more independent vendors2. | EXT\_analog\_actuation |
| **Ratified Standard** | STD\_ (or Core) | Ratified by specification working group; candidate for core inclusion1. | STD\_display\_matrix |

### **Dependency Signalling via extensionsUsed and extensionsRequired**

To allow ingestion engines to determine support before parsing an entire document, the format MUST mandate two top-level string array properties1:

* **extensionsUsed**: Lists all extensions present anywhere within the JSON document1.  
* **extensionsRequired**: Lists a subset of extensionsUsed that are mandatory for correct parsing and operational processing1. If a parser encounters an unknown extension name in extensionsRequired, it MUST decline to process the file or enter an explicit, safe fallback mode1.

### **Central Extension Registry Governance**

A central, open-source repository MUST maintain two registry files:

> 1. PREFIXES.md: Maps uppercase alphanumeric prefixes (such as LOGI or RAZR) to vendor contact details and repositories1. Prefix registration requires only a pull request, ensuring low friction1.  
> 2. EXTENSIONS.md: Index linking extension identifiers to their public technical specifications and JSON Schemas1.

## **Internationalization and Encoding Infrastructure**

### **Character Encoding Requirements**

Conforming data files MUST be encoded exclusively in UTF-8 without a Byte Order Mark (BOM), complying with RFC 8259 Section 8.110. Parsers MUST reject streams containing non-UTF-8 byte sequences or invalid surrogate pairs11.

### **Unicode Normalization**

Keycap legends, display strings, and identifier strings often contain combining characters or diacritics. To guarantee that byte-level string comparisons yield identical results across operating systems, all string fields MUST be stored in Unicode Normalization Form C (NFC). Parsers MUST normalize un-normalized input strings prior to internal indexing or comparison.

### **Localized Text Dictionary Pattern**

Human-readable properties (such as layout titles, key descriptions, and legends) MUST support multi-language localizations using BCP 47 (RFC 5646\) language tags19. Rather than using plain strings, localizable fields accept a language map object:

JSON  
{  
  "label": {  
    "en": "Shift",  
    "fr": "Maj",  
    "ja": "シフト",  
    "zh-Hant": "上檔"  
  }  
}

If a plain string is provided instead of a dictionary, processors MUST interpret it as unlocalized fallback text (equivalent to the i-default language tag).

## **Conformance Design and Normative Profiles**

### **RFC 2119 Normative Language Enforcement**

The specification text MUST apply RFC 2119 / RFC 8174 normative keywords (**MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **MAY**, and **OPTIONAL**) strictly to define operational boundaries.

### **Conformance Target Definitions**

To avoid ambiguity, the specification MUST distinguish between four distinct targets of conformance:

| Conformance Target | Primary Compliance Responsibility |
| :---- | :---- |
| **Conforming File** | Validates against JSON Schema; uses NFC UTF-8; adheres to mandatory structural keys11. |
| **Conforming Importer** | Parses valid files; ignores unknown keys; enforces extensionsRequired checks1. |
| **Conforming Exporter** | Generates valid JSON; preserves unhandled extensions and extras payloads; applies JCS ordering2. |
| **Conforming Processor** | Accurately converts valid layout primitives into physical, visual, or functional runtime outputs. |

### **Conformance Profiles**

To enable lightweight implementations (such as embedded firmware configurators) alongside comprehensive desktop suites, the standard defines two functional profiles:

* **Core Profile**: Covers physical key geometries, matrix coordinates, basic legends, and standard keycodes. Implementing the Core Profile requires zero extension overhead.  
* **Full Profile**: Implements the Core Profile plus support for advanced features including dynamic lighting layers, behavior graphs, analog actuation curves, and multi-language dictionary maps.

## **Conformance Test Suite and Validation Infrastructure**

### **Machine-Readable Test Data Repository**

A specification without a comprehensive test suite inevitably drifts into fragmented implementation behaviors. The standard MUST distribute an official test suite stored in a neutral, version-controlled repository structured into three core fixture domains:

* **Valid Fixtures (/fixtures/valid/)**: Test cases covering minimal core instances, complete multi-language BCP 47 dictionaries, valid vendor extensions, and boundary value primitives2.  
* **Invalid Fixtures (/fixtures/invalid/)**: Negative test cases containing duplicate object keys, invalid UTF-8 byte sequences, schema type mismatches, and unregistered required extension strings11.  
* **Warning Fixtures (/fixtures/warning/)**: Test cases containing deprecated fields or non-canonical key orderings that should trigger linter warnings without halting execution3.

A central manifest.json file MUST index every fixture, specifying its relative path, expected validation outcome (pass, fail, warn), expected failure class (for example, INVALID\_UTF8 or DUPLICATE\_KEY), and the exact section of the normative specification being evaluated11.

### **Round-Trip Integrity Verification Framework**

Conforming editing tools MUST preserve content integrity during export-import operations. Validation harnesses verify losslessness via an automated three-stage pipeline.  
First, the original JSON document (![][image1]) is ingested by the importer under test to build an internal memory representation. Second, the internal representation is written out by the exporter under test to create a secondary JSON document (![][image2]). Third, an RFC 8785 canonicalizer is applied to both instances11.  
![][image3]  
If non-schema fields inside extensions or extras are stripped or corrupted during this execution loop, the tool fails export conformance2.

## **Comparative Analysis and Transferable Lessons from Legacy Formats**

Analyzing long-lived formats yields critical engineering lessons regarding which structural choices foster multi-decade success and which lead to operational friction.

| Format | Versioning Strategy | Extensibility Mechanism | Primary Transferable Lesson for Schema Design |
| :---- | :---- | :---- | :---- |
| **glTF 2.0** | Frozen core major version; extensions evolve features2. | Top-level and property-level extensions / extras maps1. | Decoupling mandatory and optional extensions via extensionsRequired prevents silent execution failures1. |
| **Unicode / CLDR** | SemVer specification; strict backward-compatibility guarantees3. | Custom locale keys; supplemental data transform rules21. | Character and structural definitions are never deleted; deprecated properties remain stable indefinitely3. |
| **OpenType** | Table versioning; major/minor increments per feature table. | Modular 4-character table tags (GSUB, GPOS). | Decoupling physical geometry tables from behavioral lookup tables ensures structural longevity. |
| **OpenAPI** | Major/Minor version strings at document root7. | Vendor extensions prefixed with x-7. | Explicit root version declaration paired with pattern properties enables robust tooling validation7. |
| **USB HID** | Class specification revisions with backwards compatibility. | Itemized report descriptors; vendor usage pages. | Dense bitfield packing creates severe parsing friction; human-readable, typed fields are vastly superior. |

### **Architectural Lessons Applied**

The glTF 2.0 format achieved rapid, widespread adoption by freezing its core specification and routing all feature expansion through a structured extension registry2. Its dual mechanisms for optional and required extensions allow applications to negotiate capabilities deterministically1. Similarly, Unicode's absolute stability policy guarantees that valid documents from twenty years ago remain valid today3.  
In contrast, formats that rely on compact binary packing or opaque string encodings (such as early USB HID descriptors) impose heavy parsing overhead and frequently suffer from subtle implementation bugs. For a modern, JSON-based format, clarity, explicit typing, and formal schema governance must always take precedence over micro-optimizations in file size.

## **Architectural Checklist and Recommendations**

### **Architectural Rules Checklist**

* **Schema Base**: The standard MUST publish a canonical JSON Schema Draft 7 definition for universal ecosystem validation4.  
* **File Encoding**: Data files MUST be encoded in UTF-8 without Byte Order Mark (BOM)10. Invalid sequences MUST be rejected11.  
* **String Normalization**: All string primitives MUST be normalized using Unicode Normalization Form C (NFC) prior to processing or serialization.  
* **Canonical Formatting**: Official tools MUST format JSON using RFC 8785 (JCS) deterministic property ordering (UTF-16 code unit order) to produce clean source diffs11.  
* **Nesting Depth**: Object structures MUST NOT exceed four levels of hierarchy.  
* **Explicit Schema Versioning**: Data files MUST include an integer schemaVersion field. This field increments ONLY during breaking structural changes.  
* **Unknown Field Tolerance**: Parsers MUST ignore unknown properties during read operations and MUST NOT strip them during round-trip edit cycles1.  
* **Deprecation Policy**: Fields marked "deprecated": true MUST remain valid in the schema for at least one full major version cycle before removal3.  
* **Extension Namespacing**: Extensions MUST reside inside object-level extensions maps and use registered uppercase vendor prefixes (for example, LOGI\_)1.  
* **Extension Requirements**: Extensions that alter fundamental layout interpretation MUST be declared in the top-level extensionsRequired array1.  
* **Localization**: Multi-language text strings MUST use BCP 47 language tags as keys inside a localized dictionary object19.  
* **Normative Language**: Specifications MUST adhere strictly to RFC 2119 requirement keyword semantics.

### **Proposed Conformance and Test-Suite Model**

To achieve trustworthy interoperability across independent implementations, the specification authority MUST publish and maintain an official validation package consisting of:

> 1. **Core Validation Engine**: A CLI reference validator built on JSON Schema Draft 7 that enforces UTF-8, NFC normalization, RFC 8785 key ordering, and unknown field preservation checks4.  
> 2. **Standard Test Fixture Bundle**: A complete suite of valid, invalid, and edge-case JSON documents covering all normative requirements, complete with a machine-readable manifest.json index11.  
> 3. **Automated CI Integration Harness**: A GitHub Actions workflow template that independent implementers can integrate into their repositories to run compliance suites and round-trip verification tests automatically11.

By establishing strict meta-schema validation4, clear extension mechanics1, rigorous internationalization standards16, and an automated conformance regime11, the resulting JSON format will serve as a durable, hand-maintainable, and trustworthy open standard for decades to come.

#### **Sources des citations**

> 1. glTF/extensions/README.md at main \- GitHub, [https://github.com/KhronosGroup/glTF/blob/master/extensions/README.md](https://github.com/KhronosGroup/glTF/blob/master/extensions/README.md)  
> 2. glTF Extension Registry, [https://kcoley.github.io/glTF/extensions/](https://kcoley.github.io/glTF/extensions/)  
> 3. Unicode® Character Encoding Stability Policies, [https://www.unicode.org/policies/stability\_policy.html](https://www.unicode.org/policies/stability_policy.html)  
> 4. draft 2020-12 \- Ajv JSON schema validator, [https://ajv.js.org/json-schema.html](https://ajv.js.org/json-schema.html)  
> 5. jsonschema.validators, [https://python-jsonschema.readthedocs.io/en/latest/api/jsonschema/validators/](https://python-jsonschema.readthedocs.io/en/latest/api/jsonschema/validators/)  
> 6. Announcing JSON::Schema::Validate: a lightweight, fast, 2020-12, [https://www.reddit.com/r/perl/comments/1p6c1i4/announcing\_jsonschemavalidate\_a\_lightweight\_fast/](https://www.reddit.com/r/perl/comments/1p6c1i4/announcing_jsonschemavalidate_a_lightweight_fast/)  
> 7. Schema: Is draft 07 strictly followed? \#1196 \- GitHub, [https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/1196](https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/1196)  
> 8. Draft 2020-12 \- JSON Schema, [https://json-schema.org/draft/2020-12](https://json-schema.org/draft/2020-12)  
> 9. unevaluatedProperties (2020-12) \- Learn JSON Schema, [https://www.learnjsonschema.com/2020-12/unevaluated/unevaluatedproperties/](https://www.learnjsonschema.com/2020-12/unevaluated/unevaluatedproperties/)  
> 10. RFC 8259: The JSON Data Interchange Format | by Lince Mathew, [https://medium.com/@linz07m/rfc-8259-the-json-data-interchange-format-5e8fe8c01dd2](https://medium.com/@linz07m/rfc-8259-the-json-data-interchange-format-5e8fe8c01dd2)  
> 11. A Strict RFC 8785 Implementation in Go for Deterministic JSON, [https://dev.to/lenny321/json-canon-a-strict-rfc-8785-implementation-in-go-for-deterministic-json-3mfg](https://dev.to/lenny321/json-canon-a-strict-rfc-8785-implementation-in-go-for-deterministic-json-3mfg)  
> 12. RFC 8785: JSON Canonicalization Scheme (JCS), [https://www.rfc-editor.org/info/rfc8785/](https://www.rfc-editor.org/info/rfc8785/)  
> 13. The JSON Canonicalisation Scheme (RFC 8785\) in action and how, [https://connect2id.com/blog/how-to-secure-json-objects-with-hmac](https://connect2id.com/blog/how-to-secure-json-objects-with-hmac)  
> 14. glTF (GL Transmission Format) 2.0 \- Library of Congress, [https://www.loc.gov/preservation/digital/formats/fdd/fdd000500.shtml](https://www.loc.gov/preservation/digital/formats/fdd/fdd000500.shtml)  
> 15. Khronos glTF Registry, [https://kcoley.github.io/glTF/specification/](https://kcoley.github.io/glTF/specification/)  
> 16. JSON character encoding \- is UTF-8 well-supported by browsers or, [https://stackoverflow.com/questions/583562/json-character-encoding-is-utf-8-well-supported-by-browsers-or-should-i-use-nu](https://stackoverflow.com/questions/583562/json-character-encoding-is-utf-8-well-supported-by-browsers-or-should-i-use-nu)  
> 17. RFC 8259: The JavaScript Object Notation (JSON) Data Interchange, [https://www.rfc-editor.org/rfc/rfc8259](https://www.rfc-editor.org/rfc/rfc8259)  
> 18. How to process JSON with strings containing invalid UTF-8, [https://unix.stackexchange.com/questions/757832/how-to-process-json-with-strings-containing-invalid-utf-8](https://unix.stackexchange.com/questions/757832/how-to-process-json-with-strings-containing-invalid-utf-8)  
> 19. Les étiquettes de langues en HTML et XML \- W3C, [https://www.w3.org/International/articles/language-tags/index.fr.html](https://www.w3.org/International/articles/language-tags/index.fr.html)  
> 20. BCP 47 \- IETF Datatracker, [https://datatracker.ietf.org/doc/bcp47/](https://datatracker.ietf.org/doc/bcp47/)  
> 21. Unicode Common Locale Data Repository \- CLDR 28 Release Note, [https://sites.google.com/site/cldr/cldr-releasesdownloads/cldr-28-release-note](https://sites.google.com/site/cldr/cldr-releasesdownloads/cldr-28-release-note)  
> 22. Unicode's Transliteration Rules Are Turing-Complete \- Nicolas Seriot, [https://seriot.ch/computation/uts35/](https://seriot.ch/computation/uts35/)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACoAAAAaCAYAAADBuc72AAAB5klEQVR4Xu2WzytEURTHj6QIoRRWIhs2kq1/QGIhC0WyY6EUC7KjLCxsLEmilL2ShZiyUTY2SsqClCxQYovvt3PvuHN7M/PMz6fmU5+6c8998868e965I1KixP+iH27DK/gAb+Au3DQuw4746iLSCkfgPryHk+azlXPfcA1W6CXFZcPoUw0PRJOd92IFpx0+wU4/YKiF56LJFpUh0SQa/IChBsYkAomuSuokGuG1pF6Td8I8LZbEi6Rek3fstl/6AUMZ3BFdc+zFwsBOsQgnRL8rY+y2B73xpA0+iq4Z9WJhaIJ38ES0g2SEu+1jiaE4C6LxQ1jlxcJSDyv9yb9g2xLrL1lreoO3ogeDD7c120OgXEL8iC3Rp8Uj08KLuuEe/ILNTswyDY9EnzDlmHPkE87AAXhq5pZEd447yFIYNvN9omWRtCSYyLtokkF+iL5AXfYCB/Zavni8uYVjzjH2LJqAC8snJppoLxw08xy/mnHOaRE9/3lzC8ecY4x/bJiAi5sonRXtAOPw4ndZbrHNn93CwrF9oukSZWmtiCa4LsGllTP458TWKG9+ZuZIukTrYI/o02e9ZvsyhiKTt54HjNvm2KennM+RYU4STyiOORc5uPXsKDzlKFsj5yIJa5U1SjkuURB+AK1QYw9l0+L+AAAAAElFTkSuQmCC>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAaCAYAAADFTB7LAAABzklEQVR4Xu2WvyuFURjHHyGKSER+TLLIgBQLm8Iig0IMyuAPEMpgkcEqGVAy+QMMDCYLsjDYDJfFZKBM8uP77Tkn5z64Su897nA/9an3vM977/v0nPOc84rkyZNbtMJNeAbvnMdwK3AGVvgfxKYGjsBF+AaX4ahzHO7BV/jsf/BfDMEUbDT3SRu8hX02EIsy0WllFX+iCz6ILonoNMN72GsDAUzwRTI/kzWG4bvoevwJJsY12m8DMVgVTbDIBgJmRRuFlYwK1xTXVqYuZeOk4AYsSA9ln0nR6l3bQAC3Gz7Dbo7OjujLd23AUQlPRJ+JXr0qeCH6clbSwoQWROM8USy1sNDeTJJ50Zdfwmp3j0k1iDbFI5yQr0lwvzxy19OixyQr3S26XXFXqIdN7hnC5hoLxlOwMxin0Q6fRJP7Th5t56IbuIVbEdfrmmgSA6KnDP+T8MU3cN+NPUww3AGYPHePxGFSTGjFXdM6WOziJfBAPivssQmWi57ziePX7boNODjNrB6rGDaVTTBrFSRz8Mpds3JLolVsgdui67FH0j8umNxgMM64BpOCXeyn9jd8BUslQvf/BTvFOUUHPISnot+dOQen0zdMpg+SPInwAT+YUUG2mOUYAAAAAElFTkSuQmCC>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAAAwCAYAAACsRiaAAAAFPklEQVR4Xu3cTahuVRkH8CUmaYUiiiUlXiUMMciKFKEPkAgd6ECEogIHIgpCA0OlRok0bJBFgRXRqBRRQfxARA46sI9JQSEIoYkRESqGCiam6+/ey3e96+5z77nvPUfugd8PHt691n4/9xmcP8/ae5cCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA5bRxYo+cOE7sMyfUOm6c3GX5DABgHzqv1p1dHVjbW8o3a71d6/la95bpn/513f5La70616dq/arb9/OyHhI+Uuv+Mr3Xn8vqMz/ZPedoPDNO7LLflNV3vnbYd2atf9Z6qdbrtU6q9Vi3P+Mcoxdq3VHrl92+U2p9rxvHz8p0nFLbfeYmnip7HwwBgD2SUJZA1SRoZe4T3Vz+0Wfu9Hn83VoXr3aX39b6wrx9Rq0frHa956Nleo/e72rdPsxtIsGnD0J74e+1rhzmnqh12zD3xzIFs8hxzXOac2o92Y3/3W33cpw+3o0vqPVGN97EB2ptjZMAwLFvKURlvNT5SoeoGV9zfVl1b7bK8jLlTeXgwJBAM77Xpl4cJ3bZGGwfqHV3N26uqnX+vP3rWld0+3JcWuhLIGvBrvfhsnxMXiur993U38oU3ACAfeTWsr5899OyHsx6V3fb/6/1Vq1vd3PNUtiI52p9dZg7tWz//COVZctzx8kydQyzbLld7UTCVf89W9BdCj995zGBLM/7cTk4xP6w1meGuUigS7AavVkOPn5HKn/vL46TAMCx7bmyHgISxL7VjbeT87L+WqYwkvpst+9f3XYvzxtDS8JJPnM3pMvXd7N2U4LOg904QWy73zn6UVkdp0e7+a0yBdbRVpl+S29ckt5U/tb5LQDAPjKGqIw/342bnEP1oXl7DBk5dyzdrTi+1j+6fU06X0vBLN28G8bJBTvpwiWsLQW2dLHaSfxLtRMJZ32w3ZpryY3z4xhOzyrrv+P3ZX2JtVkKZt+o9Z9hbhP52wpsAHCMO7vWy/N2QlSW2XoJUJcNc9GfKH9ftx1ZRr2kG/+3226y/HfPMHdRWb+6M12kpQCzJMuc460qEkQuH+Y21TpabclzXP5MgHq6Gze3lNXz+o5cZBk1Ia3Zmud6S0vE7bv0vzcXdmwigTbnEgIAx7AEp+/M2wluCU29XG2ZcHDyPE7H7A+r3e92frI/S6JxoKyfAxdj4Mh75LO+Mo8TyrI0+JP3njF18D49b+dk/shrspyYANTOq3t2fvxLObiDlUA4dqYi55SNXbXDddgSZh+ft9utNUb5frn1SZPbc3ysG6ej+PV5O6Ert/bob6uR4DSeT3ZzmW57EnlulkZfKdMxbB6ZH1v4S/cv5+K1q3pze5HI+YX9UnXk73+0Fy4AAO+DL5epQ3Soe3J9rUzPGUNRC1UHal1Tlm+Om1t8LAWnQ8mSauuu5WrI2Jofoy2zJqjley9dnfm/ceIoZQkz5/Plqs3tHCjTcRhDUAJWXpeuWI5jjvko4Xjswh1Ogllug5LH1p37YFmFuGghNMezLVU3e30lLQCwTySktC7ZTqUT1MJgOzF/a36MFtjuKlNY6TtOkQ7deI+0/SD3bDtUcF6S0Brfnx9/UaYu4pfm8XYdtiyj5v55AADvylLruNx6ODs5hy1LevG5sroIIK97aN7ej1oAOxKHOoctHbZ0RsdQ+6dhDACwJx4u0/3g8jhedEApF5bpHMLduvgCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAN5X7wCHZdIg1F9UKgAAAABJRU5ErkJggg==>