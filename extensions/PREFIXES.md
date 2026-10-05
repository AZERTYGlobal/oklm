# Extension prefixes

Since schema 0.2 the manifest schema is open. Data outside the core goes in an
`extensions` object, which exists on every object of the manifest. Each key of
`extensions` is a namespace of the form `<PREFIX>_<name>`:

```text
^(OKLM|EXT|[A-Z][A-Z0-9]*)_[A-Za-z0-9]+$
```

A member that matches this pattern is valid only inside `extensions`. Anywhere
else the schema rejects it (D34, D38), so a typo cannot silently become data.

## Prefixes

| Prefix | Owner | Use |
|---|---|---|
| `OKLM_` | the OKLM project | namespaces defined by this repository (for example `OKLM_geometry`, `OKLM_siteView`) |
| `EXT_` | anyone | experimental namespaces, no registration, no stability promise |
| `<VENDOR>_` | one organisation | uppercase letters and digits, starting with a letter (for example `ACME_`); registered below |

## Rules

1. List every namespace a file uses in the root array `extensionsUsed`.
2. List in `extensionsRequired` (a subset of `extensionsUsed`) the namespaces that a reader must understand to use the file correctly. A reader that does not know one of them refuses the file (`E_EXTENSIONS_REQUIRED`). Otherwise it ignores the block and keeps it intact.
3. Core features needed by a file go in `featuresRequired`, not in an extension.
4. Exporters never write extensions into the target format. The conversion report lists them in `skippedFields` (E19).
5. The content of an extension is its owner's business. OKLM validates the namespace name, not the content.

## Registry

| Prefix | Owner | Contact or source | Since |
|---|---|---|---|
| `OKLM_` | OKLM project | this repository | 2026-10-05 |
| `EXT_` | open | none | 2026-10-05 |

To register a `<VENDOR>_` prefix, open an issue on the repository with the
prefix, the owner and a link to the documentation of the namespaces. A prefix is
granted when it is unused and not a trademark of someone else.
