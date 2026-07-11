# OKLM examples

Six manifests, all validating against `schemas/oklm-manifest.schema.json`
(check with `python validators/validate.py examples/*.oklm.json`).

| Manifest | Layout | Keys / levels / dead keys | Provenance | License of the layout |
|---|---|---|---|---|
| `azerty-global.oklm.json` | AZERTY Global 2026 | 49 / 8 / 29 | Generated from the layout's source of truth, verified field-by-field | EUPL-1.2 |
| `azerty-afnor.oklm.json` | AZERTY option of AFNOR NF Z71-300:2019 | 49 / 8 / 22 | Generated from the azerty.global web tester data, verified field-by-field | NOASSERTION (standard document (c) AFNOR; no standalone license published for the mapping; community drivers carry their own licenses) |
| `bepo.oklm.json` | BÉPO (ergonomic option of NF Z71-300) | 49 / 8 / 21 | Generated from the azerty.global web tester data, verified field-by-field | CC-BY-SA / GFDL (bepo.fr community) |
| `azerty-traditionnel.oklm.json` | Legacy Windows French AZERTY | 49 / 5 / 4 | Generated from the azerty.global web tester data, verified field-by-field | NOASSERTION (no license published by Microsoft) |
| `qwerty-us.oklm.json` | US QWERTY (ANSI baseline) | 48 / 3 / 0 | Hand-written | Public-domain heritage; manifest under CC0-1.0 |
| `azerty-global-minimal.oklm.json` | Illustrative 6-key subset | 6 / 2 / 2 | Hand-written teaching example, cited by `SPEC.md` | EUPL-1.2 |

Together they exercise the draft 0.1 schema across its range: ISO and ANSI
geometries (with and without the B00 key), 2 to 8 ISO levels including
CapsLock variants via `levelSelectors`, zero to 29 dead keys (up to 1016
compositions), scoped conformance declarations, and four different licensing
situations for the described layouts.

None of these files is the authoritative source of the layout it describes;
each manifest's `metadata.description` states its provenance.

## Exports

[`exports/`](exports/) holds committed reference exports of all six
manifests to the three v1 exporter targets (`ldml/`, `xkb/`, `keylayout/`),
each with its conversion report. Regenerate with:

```bash
python tools/export.py --target ldml|xkb|keylayout --out examples/exports/<target> examples/*.oklm.json
```

`tools/tests/run_tests.py` fails if a fresh export no longer matches these
committed files (regression) or if a report stops validating against
`schemas/oklm-conversion-report.schema.json`.
