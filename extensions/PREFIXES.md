# Extension prefixes

Since schema 0.2 the manifest schema is open. Data outside the core goes in an
`extensions` object, which exists on every object of the manifest. Each key of
`extensions` is a namespace of the form `<PREFIX>_<name>`:

```text
^(OKLM|EXT|[A-Z][A-Z0-9]*)_[A-Za-z0-9]+$
```

A member that matches this pattern is valid only inside `extensions`. Anywhere
else the schema rejects it, so a typo cannot silently become data. (`D34` and
`D38` are decisions of the research journal in [`research/`](../research/), in French.)

## Prefixes

| Prefix | Owner | Use |
|---|---|---|
| `OKLM_` | the OKLM project | namespaces defined by this repository (for example `OKLM_frameKeys`, `OKLM_geometry`, `OKLM_ldml`) |
| `EXT_` | anyone | experimental namespaces, no registration, no stability promise |
| `<VENDOR>_` | one organisation | uppercase letters and digits, starting with a letter (for example `ACME_`); registered below |

## Rules

1. List every namespace a file uses in the root array `extensionsUsed`.
2. List in `extensionsRequired` (a subset of `extensionsUsed`) the namespaces that a reader must understand to use the file correctly. A reader that does not know one of them refuses the file. Otherwise it ignores the block and keeps it intact. The validator checks a different thing: that `extensionsRequired` is a subset of `extensionsUsed`. <!-- TODO-merge: codes -->
3. Core features needed by a file go in `featuresRequired`, not in an extension.
4. Exporters never write extensions into the target format. The conversion report lists them in `skippedFields`.
5. The content of an extension is its owner's business. OKLM validates the namespace name, not the content.

## Registry

| Prefix | Owner | Contact or source | Since |
|---|---|---|---|
| `OKLM_` | OKLM project | this repository | 2026-10-05 |
| `EXT_` | open | none | 2026-10-05 |

To register a `<VENDOR>_` prefix, open a pull request that adds a row to the
registry table above, with the prefix, the owner and a link to the documentation
of the namespaces; an issue with the same information is accepted if you cannot
open a pull request. A prefix is granted when it is unused and not a trademark
of someone else. See [CONTRIBUTING.md](../CONTRIBUTING.md).

## Namespaces defined by this repository

| Namespace | Content |
|---|---|
| `OKLM_ldml` | Written by `tools/import_ldml.py`. `source` (LDML namespace URI, original `locale`), `info` (the `info` attributes other than name and author), `unmapped` (list of `{construct, reason, xml}`: LDML constructs kept verbatim). On a dead key, `markerId` is the original LDML marker id when it was renamed. Never exported. |

The reserved names `OKLM_frameKeys`, `OKLM_firmware` and `OKLM_geometry` are
described in [SPEC.md](../SPEC.md#extensions); their content is unspecified in
0.2. No example manifest uses any of them yet. The migration tool
renames the 0.1 names `frame-keys`, `firmware`, `geometry` and `ldml` to these
prefixed names.
