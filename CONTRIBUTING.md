# Contributing to privacy-taxonomy

Thanks for your interest in improving `privacy-taxonomy`! Contributions of all sizes are welcome —
bug reports, classification-guide improvements, validator fixes, and docs.

## Ground rules

- Be respectful — see [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).
- Keep the plugin **atomic**: runtime code must use only the Python standard library, with **no
  network access and no third-party install step**. (`PyYAML` may be used *opportunistically* but a
  stdlib fallback must remain.)
- Don't hand-edit the taxonomy JSON. It is a generated snapshot — see *Updating the taxonomy* below.

## Project layout

The shared skill lives under `skills/privacy-datamap/`:

- `SKILL.md` — the agent workflow.
- `scripts/dump_taxonomy.py` — prints the bundled taxonomy.
- `scripts/validate_manifest.py` — validates a manifest against the snapshot.
- `references/taxonomy/` — vendored Fideslang snapshot (CC BY 4.0) + `SOURCE.md`.
- `references/classification-guide.md` — field-name → category heuristics.
- `references/example-datamap.yml` — the canonical valid example.

Host-specific plugin metadata lives in `.codex-plugin/plugin.json` and
`.claude-plugin/plugin.json`. Keep their names, versions, descriptions, and discovery metadata
aligned when changing a release. Codex marketplace discovery metadata lives in
`.agents/plugins/marketplace.json`; Claude marketplace metadata remains under `.claude-plugin/`.

## Development & testing

There is no build step. Verify changes with the bundled tooling:

```bash
SKILL=skills/privacy-datamap

# 1. taxonomy prints
python3 "$SKILL/scripts/dump_taxonomy.py" | head

# 2. the example validates (expect "OK")
python3 "$SKILL/scripts/validate_manifest.py" "$SKILL/references/example-datamap.yml"

# 3. a deliberately broken manifest fails (expect non-zero exit + suggestions)
#    (edit a copy of the example to introduce a bogus key and run the validator)

# 4. atomicity: the validator still works without PyYAML
#    (run it in an environment where `import yaml` fails — it must use the fallback loader)
```

If you change the validator, please confirm all four checks above. If you add a new field-name
mapping to `classification-guide.md`, make sure the target key actually exists in the snapshot
(`rg` it in `references/taxonomy/data_categories.json`).

## Updating the taxonomy snapshot

Follow the recipe in `skills/privacy-datamap/references/taxonomy/SOURCE.md`. It re-fetches the
upstream Fideslang source and regenerates the JSON with the standard library `ast` module, then asks
you to update the recorded commit/version/date. Bump the version in both plugin manifests when you
do.

## Pull requests

1. Fork and create a topic branch.
2. Make focused changes with clear commit messages.
3. Run the verification steps above.
4. Update `CHANGELOG.md` under an *Unreleased* heading.
5. Open a PR describing the change and its motivation.

## Style

- Python: standard-library only, readable, no external deps.
- Markdown/YAML: keep lines reasonably wrapped; match the surrounding style.

By contributing, you agree that your code contributions are licensed under the project's MIT license,
and that any taxonomy-data contributions remain under CC BY 4.0.
