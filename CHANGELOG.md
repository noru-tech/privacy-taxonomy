# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-07-30

### Fixed
- Added a native Codex marketplace manifest under `.agents/plugins/` so Codex can discover the
  repository-root plugin without relying on Claude marketplace compatibility.

## [0.2.0] - 2026-07-30

### Added
- Codex plugin metadata under `.codex-plugin/`.
- Codex installation and invocation instructions.

### Changed
- Documented the existing skill for use from both Codex and Claude Code.

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

[Unreleased]: https://github.com/noru-tech/privacy-taxonomy/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/noru-tech/privacy-taxonomy/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/noru-tech/privacy-taxonomy/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/noru-tech/privacy-taxonomy/releases/tag/v0.1.0
