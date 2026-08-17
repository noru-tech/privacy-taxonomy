# privacy-taxonomy

> Generate a [Fideslang](https://github.com/ethyca/fideslang) **privacy data map** for any repository — straight from its source code.

[![License: MIT](https://img.shields.io/badge/Code-MIT-blue.svg)](./LICENSE)
[![Taxonomy: CC BY 4.0](https://img.shields.io/badge/Taxonomy-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-plugin-da7756.svg)](https://code.claude.com/docs/en/plugins)
[![Codex Plugin](https://img.shields.io/badge/Codex-plugin-111827.svg)](https://developers.openai.com/plugins/build/plugins)

`privacy-taxonomy` is a plugin for [Claude Code](https://claude.com/claude-code) and
[Codex](https://developers.openai.com/codex/). Its shared `privacy-datamap` skill reads a codebase —
ORM models, migrations, SQL DDL, API/GraphQL/protobuf schemas, DTOs — and emits a **validated Fides
data map manifest**: `dataset` resources (collections → fields tagged with `data_categories`) plus
`system` resources (`privacy_declarations` with `data_use` and `data_subjects`).

Think of it as the source-code counterpart to Ethyca's `fides generate dataset` (which inspects a
*live database* and leaves the privacy labels **blank**): this reads **code** in any language and
**auto-suggests** the labels for you.

## Why

Building a Record of Processing Activities (RoPA) / data map by hand is slow and goes stale the
moment the schema changes. Classifying which columns are personal data — and *what kind* — is exactly
the kind of semantic judgement an LLM is good at, while the **set of valid labels** is a fixed
taxonomy that should never be guessed. This plugin combines the two: the agent does the
classification, and a bundled, deterministic validator guarantees every emitted key is a real
Fideslang key.

## What you get

```yaml
# .fides/datamap.yml  (excerpt)
dataset:
  - fides_key: app_postgres
    collections:
      - name: users
        fields:
          - name: email
            data_categories: [user.contact.email]
          - name: last_login_ip
            data_categories: [user.device.ip_address]
          - name: password_hash
            data_categories: [user.authorization.password]
system:
  - fides_key: web_app
    system_type: Application
    dataset_references: [app_postgres]
    privacy_declarations:
      - name: Provide the service
        data_use: essential.service
        data_categories: [user.contact.email, user.name]
        data_subjects: [customer]
```

A complete, valid example lives at
[`skills/privacy-datamap/references/example-datamap.yml`](skills/privacy-datamap/references/example-datamap.yml).

## How it works

1. **Load the taxonomy** — the canonical, allowed keys are read from a bundled snapshot (see below),
   not invented.
2. **Discover** data-bearing artifacts across the repo (ORMs, migrations, DDL, OpenAPI/GraphQL/proto,
   DTOs) and system/third-party hints (env vars, SDK imports, service directories).
3. **Classify** each field to the most-specific applicable `data_categories`, guided by a curated
   field-name → category cheat-sheet. Genuinely ambiguous fields are left with a `# TODO: verify`
   comment instead of a confident guess.
4. **Assemble** datasets, first-party systems, and named external-vendor systems (with `data_use`
   and `data_subjects` inferred from context).
5. **Reconcile vendors** so every material integration is represented, grouped by name, or excluded
   with a reason.
6. **Validate** taxonomy keys and run deterministic System coverage checks until both are clean.
7. **Report** system/vendor coverage, counts, exclusions, unresolved review items, and
   low-confidence labels.

## Atomic & offline

The plugin is fully self-contained. It needs only `python3` (standard library) — **no `pip install`,
no virtualenv, and no network at runtime.**

- Valid keys come from a vendored snapshot in
  [`skills/privacy-datamap/references/taxonomy/`](skills/privacy-datamap/references/taxonomy/).
- The validator uses `PyYAML` if it happens to be importable and otherwise falls back to a small
  built-in block-YAML loader, so it runs anywhere Python does.

## Install

### Codex

Add the repository as a marketplace:

```bash
codex plugin marketplace add noru-tech/privacy-taxonomy
```

Then enter `/plugins` in Codex CLI (or open **Plugins** in the desktop app), select the
`privacy-taxonomy` marketplace, and install the plugin. Start a new Codex session after installing
so the bundled skill is available.

### Claude Code

```bash
# add this repo as a marketplace, then install the plugin
/plugin marketplace add noru-tech/privacy-taxonomy
/plugin install privacy-taxonomy@privacy-taxonomy
```

(For either host, replace `noru-tech/privacy-taxonomy` with wherever you host the repo.)

### Manual (skill only)

Copy the skill into the user skills directory for your agent:

```bash
# Codex
cp -R skills/privacy-datamap ~/.codex/skills/privacy-datamap

# Claude Code
cp -R skills/privacy-datamap ~/.claude/skills/privacy-datamap
```

## Usage

In any repository, ask Codex or Claude Code:

> Generate a Fides data map for this repo.

Or invoke the skill directly using the syntax for your agent:

```text
$privacy-datamap   # Codex
/privacy-datamap   # Claude Code
```

It writes `.fides/datamap.yml` (override the path by saying where you want it), validates it,
and summarizes what it found.

### Run the bundled tools directly

```bash
SKILL=skills/privacy-datamap

# Print the taxonomy you're allowed to classify against
python3 "$SKILL/scripts/dump_taxonomy.py"            # categories | uses | subjects

# Validate a manifest against the bundled snapshot
python3 "$SKILL/scripts/validate_manifest.py" .fides/datamap.yml

# Check that discovered external vendors have a named System or reasoned exclusion
python3 "$SKILL/scripts/check_system_coverage.py" . .fides/datamap.yml
```

The taxonomy validator exits `0` on success, `1` on validation errors (each unknown key comes with a
"did you mean …?" suggestion), and `2` on usage/parse errors. The coverage checker exits `1` when a
material discovered vendor is unresolved and `2` for invalid arguments or exclusion configuration.

## Repository layout

```
privacy-taxonomy/
├── .agents/
│   └── plugins/
│       └── marketplace.json     # native Codex marketplace
├── .codex-plugin/
│   └── plugin.json              # Codex plugin manifest
├── .claude-plugin/
│   ├── plugin.json              # plugin manifest
│   └── marketplace.json         # self-referential marketplace (source ./)
├── skills/
│   └── privacy-datamap/
│       ├── SKILL.md             # the agent workflow
│       ├── scripts/
│       │   ├── check_system_coverage.py
│       │   ├── dump_taxonomy.py
│       │   └── validate_manifest.py
│       ├── references/
│       │   ├── taxonomy/        # vendored Fideslang snapshot (CC BY 4.0) + SOURCE.md
│       │   ├── classification-guide.md
│       │   ├── vendor-system-guide.md
│       │   └── example-datamap.yml
│       └── tests/               # standard-library coverage-checker regressions + fixtures
├── README.md  LICENSE  NOTICE  SECURITY.md  CONTRIBUTING.md  CODE_OF_CONDUCT.md  CHANGELOG.md
```

## Refreshing the taxonomy

The snapshot is pinned to a specific Fideslang revision. To update it to a newer release, follow the
recipe in
[`skills/privacy-datamap/references/taxonomy/SOURCE.md`](skills/privacy-datamap/references/taxonomy/SOURCE.md)
(it re-fetches the upstream source and regenerates the JSON using only the standard library).

## Accuracy & limitations

The validator guarantees every emitted key is **valid**, not that every judgement is **correct**.
Field classification is a model inference: review the `# TODO: verify` items and spot-check the rest
before treating the output as authoritative for compliance purposes. This tool accelerates a data
map; it does not replace privacy/legal review.

Vendor discovery is static and intentionally conservative. Dynamic imports, runtime-only secrets,
proprietary wrappers, remotely configured integrations, and vendors absent from the built-in alias
table can require manual reconciliation. The coverage checker reports evidence and gaps; it never
invents a vendor System.

## Licensing & attribution

- **Code** (skill, scripts, docs, examples): [MIT](./LICENSE).
- **Taxonomy data** under `skills/privacy-datamap/references/taxonomy/`: a modified redistribution of
  the **Fideslang** taxonomy by Ethyca, Inc., licensed under
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See [`NOTICE`](./NOTICE) for the full
  attribution.

This project is not affiliated with or endorsed by Ethyca, Inc.

## Contributing & security

- Contributions: see [CONTRIBUTING.md](./CONTRIBUTING.md).
- Reporting a vulnerability: see [SECURITY.md](./SECURITY.md).
- Community expectations: see [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).
