# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-02

### Added
- Initial release of the `privacy-taxonomy` Claude Code plugin.
- `privacy-datamap` skill: scans a repository and generates a Fides data map manifest
  (`dataset` + `system` resources) written to `.fides/datamap.yml`.
- Bundled, offline taxonomy snapshot (vendored from Fideslang, CC BY 4.0) under
  `skills/privacy-datamap/references/taxonomy/`.
- `scripts/dump_taxonomy.py` — prints the bundled taxonomy (standard library only).
- `scripts/validate_manifest.py` — validates a manifest against the snapshot with structural and
  cross-reference checks and "did you mean …?" suggestions; uses PyYAML if present, otherwise a
  built-in fallback loader (no install, no network).
- `references/classification-guide.md` and `references/example-datamap.yml`.
- Plugin and self-referential marketplace manifests under `.claude-plugin/`.
- Project scaffolding: README, LICENSE (MIT), NOTICE (CC BY 4.0 attribution), SECURITY,
  CONTRIBUTING, CODE_OF_CONDUCT.

[Unreleased]: https://github.com/noru-tech/privacy-taxonomy/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/noru-tech/privacy-taxonomy/releases/tag/v0.1.0
