---
name: privacy-datamap
version: 0.1.0
description: Generate a Fides/Fideslang privacy data map (dataset + system manifest YAML) for the current repository by scanning source code and classifying fields against the fideslang taxonomy. Use when the user wants to create a fides data map, a fideslang metadata file, a privacy manifest, or to annotate data categories / data uses / data subjects for a repo.
requires:
  bins: ["python3"]
---

# Fideslang data map generator

Produce a **Fides data map manifest** for the repository you are currently in by reading its source
code, classifying each data-bearing field against the Fideslang taxonomy, and emitting a validated
YAML file with `dataset` and `system` resources.

This is the source-code analog of Ethyca's `fides generate dataset` (which inspects a *live
database* and leaves labels blank): here you read **code** in any language and **auto-suggest** the
privacy labels.

## Self-contained / atomic

Everything needed ships inside this skill. **Do not** `pip install fideslang`, create a venv, or hit
the network. The only runtime requirement is `python3` (standard library only). Valid taxonomy keys
come from the bundled snapshot in `references/taxonomy/` (provenance in
`references/taxonomy/SOURCE.md`).

## Output format

A YAML file (default `.fides/datamap.yml` in the target repo) with two top-level lists:

```yaml
dataset:
  - fides_key: <store>            # collections = tables/models, fields = columns/attributes
    name: <human-readable store name>
    collections:
      - name: <table>
        fields:
          - name: <column>
            data_categories: [user.contact.email]
system:
  - fides_key: <service>
    name: <human-readable service name>
    system_type: Application
    dataset_references: [<store>]
    privacy_declarations:
      - name: <purpose>
        data_use: essential.service
        data_categories: [user.contact.email]
        data_subjects: [customer]
```

Always include a human-readable `name` on each dataset and system (`fides_key` is the machine ID; a
map without names is hard to review).

See `references/example-datamap.yml` for a complete worked example to pattern-match against.

## Workflow

Work through these steps in order. Prefer accuracy over coverage — a missing label is better than a
confidently wrong one.

### 1. Load the taxonomy reference
Print the canonical keys you are allowed to use, and read the mapping guidance:
```bash
python3 "$SKILL_DIR/scripts/dump_taxonomy.py"        # categories + uses + subjects (with descriptions)
```
**Read the full output — do not pipe through `head` or any other truncation.** The script prints the
total key count (e.g. `[85 keys]`) in each section header; verify that you have seen that many lines
before concluding you have the complete list. Keys near the end of the list (such as `user.unique_id`,
`user.unique_id.pseudonymous`, `user.sensor`) are silently lost if output is cut short.

Read `references/classification-guide.md` for the field-name → category cheat-sheet and for how to
infer `system_type`, `data_use`, and `data_subjects`. **Only keys printed here are valid** — never
invent a key.

### 2. Discover data-bearing artifacts
Search the repo broadly (use Glob/Grep; for a large or unfamiliar repo, dispatch an `Explore`
subagent). Look across languages for:
- **ORM models**: SQLAlchemy, Django models, Prisma `schema.prisma`, TypeORM / Sequelize entities,
  ActiveRecord, GORM structs, Ecto schemas, Mongoose schemas.
- **DB schema**: `*.sql` DDL, Alembic / Django / Rails / Liquibase / Flyway migrations.
- **API & contracts**: OpenAPI/Swagger, GraphQL SDL, `*.proto`, JSON Schema, Pydantic / Zod /
  dataclasses / TypeScript DTOs.
- **System & third-party hints**: env var names (`*_API_KEY`, `*_DSN`), SDK imports (Stripe,
  Segment, GA, Sentry, Twilio, OpenAI…), and `services/*` / `apps/*` / per-service Dockerfiles.

### 3. Build `dataset` resources
One Dataset per logical data store. Map tables/models → `collections`, columns/attributes →
`fields` (nest `fields` for JSON / embedded / sub-messages). Assign the **most-specific applicable**
`data_categories` to each field using the cheat-sheet. For genuinely ambiguous fields, omit
`data_categories` and add a `# TODO: verify` comment instead of guessing. Operational columns
(surrogate PKs, timestamps) → `system.operations` or leave off.

### 4. Build `system` resources
One System per deployable service/app. Set `system_type`, `dataset_references` (the dataset
`fides_key`s it uses), and one `privacy_declaration` per distinct purpose — each with `name`,
`data_use`, `data_categories`, and inferred `data_subjects`. Use third-party SDK usage to add
`third_party_sharing` declarations where data clearly leaves the system.

### 5. Write the manifest
Write to `.fides/datamap.yml` in the target repo (or a path the user specified). `.fides/` is the
directory the `fides` CLI conventionally reads (`fides push .fides/`). Create it if absent. Use the
`dataset:` / `system:` top-level list shape shown above. Add brief `# TODO: verify` comments on any
low-confidence labels.

**If the file already exists, do not blindly overwrite it** — a human may have hand-corrected labels.
Read it first and *merge*: add newly discovered datasets/systems/fields, fill in missing labels, and
leave existing human-set `data_categories` / `data_use` / `data_subjects` and `# verified`-style
comments intact. Only change an existing label if it is clearly wrong, and flag the change in your
report (§7) so the user can review it.

### 6. Validate (and fix until clean)
```bash
python3 "$SKILL_DIR/scripts/validate_manifest.py" .fides/datamap.yml
```
Fix every reported error (unknown keys come with a "did you mean …?" hint) and re-run until it prints
`OK: N dataset(s), N system(s), all keys valid`. Treat warnings as review items.

### 7. Report
Summarize for the user: counts (datasets, systems, collections, fields; fields categorized vs left
as TODO), the systems and their data uses/subjects, and an explicit bullet list of the low-confidence
labels you flagged so a human can confirm them. **Call out any special-category (GDPR Art. 9 / Art. 10)
data** you labelled — biometric, health/medical, race/ethnicity, religious belief, political opinion,
sexual orientation, criminal history (see the classification guide for the exact keys) — as a separate
list, since these carry the most compliance risk and warrant explicit human review.

## Notes
- `$SKILL_DIR` above is this skill's directory; substitute its real path when running commands.
- The bundled validator uses PyYAML if it is already importable, and otherwise falls back to a
  built-in loader — either way it needs no installation.
- To refresh the taxonomy snapshot to a newer fideslang release, follow
  `references/taxonomy/SOURCE.md`.
