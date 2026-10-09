# Contributing

OKLM (Open Keyboard Layout Model) is a public draft, written mostly by one
person today. Contributions are welcome; this page says how to make one that
is easy to review. How decisions are taken is in [GOVERNANCE.md](GOVERNANCE.md).

## What to contribute

Use GitHub issues and pull requests on
[AZERTYGlobal/oklm](https://github.com/AZERTYGlobal/oklm) for:

- schema and specification problems (a rule that is wrong, ambiguous or
  contradicted by the schema or the validator);
- example manifests of other layouts;
- exporter and importer fixes or new targets;
- conformance tests;
- documentation fixes;
- compatibility reports from OS, hardware, application, remote-desktop,
  education or enterprise contexts.

Open an issue first for anything that changes the schema, the specification or
the exporters' output: those changes touch every example manifest and every
committed export, and they are decided in the open (see
[GOVERNANCE.md](GOVERNANCE.md#how-decisions-are-made-and-recorded)).
A typo or a clear bug can go straight to a pull request.

To register an extension prefix, add a row to the registry in
[`extensions/PREFIXES.md`](extensions/PREFIXES.md) by pull request; if you
cannot open one, an issue with the same information is accepted.

## Before you open a pull request

1. Install the dependencies: `pip install -r requirements.txt`.
2. Run the whole check from the repository root:

   ```text
   python tools/tests/run_all.py
   ```

   It must pass. Details of each check are in the [README](README.md#checks).
3. If your change alters an export, regenerate the reference files in
   `examples/exports/` and commit them with the change: the tests compare
   fresh output with them byte for byte. A change to the schema or to the
   exporters updates every example manifest and committed export in the same
   pull request.
4. Keep a pull request to one subject, and say in its description what changed
   and how you checked it.

## Language

The specification and the documentation are in English. The research journal in
[`research/`](research/) is kept in French; write there in French.

## Layout data

A manifest declares its own license in the `license` field (an SPDX identifier,
or `NOASSERTION` when none is published). Only contribute a layout that you
may share under the license you declare, and say where the data comes from in
`metadata.description`. Do not copy text or data from a source whose license
forbids it.

## License of contributions

By submitting a contribution you agree that it is licensed under the license of
the part of the repository it changes: CC BY 4.0 for the specification and the
documentation (`*.md`), EUPL 1.2 for the code, the schemas and the tooling, and
the license declared in the manifest for layout data. The table is in the
[README](README.md#licensing). You keep your copyright.

## Conduct

Be respectful and keep the discussion on the technical subject. The project has
no code of conduct document yet.

## Security problems

Do not open a public issue for a vulnerability; follow [SECURITY.md](SECURITY.md).
