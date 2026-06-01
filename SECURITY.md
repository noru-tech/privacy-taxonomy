# Security Policy

## Supported versions

This project is pre-1.0; security fixes are applied to the latest release on the `main` branch.

| Version | Supported |
| ------- | --------- |
| 0.1.x   | ✅        |

## Reporting a vulnerability

Please report security issues **privately** — do not open a public issue for an unfixed
vulnerability.

- Email: **security@noru.tech** with a subject line beginning `[SECURITY] privacy-taxonomy`.
- If the repository is hosted on GitHub, you may instead use **Private vulnerability reporting**
  (Security → *Report a vulnerability*).

Please include: a description of the issue, the affected file(s) and version/commit, reproduction
steps or a proof of concept, and the impact you foresee.

We aim to acknowledge reports within **5 business days** and to provide a remediation timeline after
triage. We will credit reporters who wish to be named once a fix is released.

## Scope and threat model

This plugin runs **locally** and is designed to be self-contained:

- It uses only the Python standard library and performs **no network calls at runtime**.
- It **reads** source files in the target repository and **writes** a single manifest
  (`.fides/datamap.yml` by default).
- The bundled scripts execute under your own permissions. As with any tool you run on a codebase,
  review it before running it against sensitive repositories.

Out of scope: the accuracy of generated privacy classifications (this is a productivity aid, not a
compliance guarantee — see the README), and vulnerabilities in upstream Fideslang.

### A note on generated output

The generated data map describes where personal data lives in a codebase. Treat the output as
**sensitive**: it can be a roadmap to PII. Store and share `datamap.yml` accordingly.
