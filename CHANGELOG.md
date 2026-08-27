# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-08-27

### Changed
- **Superseded by [`noru-tech/noru-grc-engineering`](https://github.com/noru-tech/noru-grc-engineering).**
  Development moves there, where the `privacy-datamap` skill is a full last-mile piece with
  `:scan` / `:diff` / `:push` and lands the data map in Noru. The skill name is unchanged, so
  existing invocations keep working; the plugin name and the install path change from
  `privacy-taxonomy@privacy-taxonomy` to `privacy-datamap@noru-grc-engineering`.

  No functional change to the code in this repository. It still installs and still works. It will
  not receive fixes — including the two already fixed upstream: the bundled YAML fallback loader
  here resolves `yes` / `no` / `on` / `off` as strings rather than booleans, and mishandles
  block-scalar chomping.

  The Fideslang snapshot under `skills/privacy-datamap/references/taxonomy/` is byte-identical to
  the one now canonical at `contract/lib/taxonomy/` in the monorepo, where a drift check keeps every
  vendored copy in step. That duplication — the same 85 entries pinned to the same upstream commit
  in two repositories, with two refresh recipes that had already diverged in wording and no check
  able to see across the boundary — is the reason the two were merged.

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
