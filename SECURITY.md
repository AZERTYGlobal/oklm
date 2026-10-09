# Security policy

## What this project is, security-wise

OKLM is a specification, JSON Schemas and command-line tools (Python). It runs
no server and no network service, has no accounts, and keeps no secrets. The
tools read files that you give them (manifests, conversion reports, LDML
Keyboard XML) and write files in the directory you choose; they fetch nothing
from the network. The site [oklm.org](https://oklm.org) is a static page that
loads the example manifests published with it.

Problems that count as security issues include, for example: a crafted input
file that makes a tool write outside the output directory, run code, or consume
unbounded memory or time; and a script injection in the site page.

## Supported versions

Only the current `main` branch is maintained. The schema draft 0.1 is frozen
and receives no fixes. No versioned release has been tagged yet.

## Reporting a vulnerability

Please do not open a public issue for a vulnerability.

1. Use GitHub's private vulnerability reporting: on the repository page
   [AZERTYGlobal/oklm](https://github.com/AZERTYGlobal/oklm), open the
   **Security** tab and choose **Report a vulnerability**.
2. If that option is not available, open a public issue titled "Security
   contact request" that contains **no technical detail**, so that a maintainer
   can arrange a private channel.

Say which file or command is affected, how to reproduce the problem, and what
you expect to happen. The project is maintained by volunteers: there is no
guaranteed response time, and no bug bounty.

For anything that is not a vulnerability, use the issues as described in
[CONTRIBUTING.md](CONTRIBUTING.md).
