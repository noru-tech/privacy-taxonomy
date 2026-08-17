#!/usr/bin/env python3
"""Check that material third-party integrations have a System disposition.

Standard-library only; no network access. The checker scans source/config evidence,
reconciles discovered vendors against manifest System names/fides_keys and explicit
exclusions, and exits nonzero when any material vendor remains unresolved.

Usage:
    python3 check_system_coverage.py [repo] [manifest]
        [--exclusions path.json] [--exclude "Vendor=reason"]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from dataclasses import dataclass, field

from validate_manifest import load_yaml


SKIP_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "vendor", "dist", "build",
    "coverage", ".next", ".cache", "__pycache__",
}
TEXT_SUFFIXES = {
    ".c", ".cc", ".conf", ".config", ".cs", ".env", ".go", ".graphql", ".h", ".hpp",
    ".html", ".java", ".js", ".json", ".jsx", ".kt", ".mjs", ".php", ".proto", ".py",
    ".rb", ".rs", ".sh", ".sql", ".swift", ".tf", ".toml", ".ts", ".tsx", ".xml",
    ".yaml", ".yml",
}
TEXT_NAMES = {
    "Dockerfile", "Gemfile", "go.mod", "go.sum", "package.json", "package-lock.json",
    "pnpm-lock.yaml", "pyproject.toml", "requirements.txt", "yarn.lock",
}
TEST_PARTS = {"test", "tests", "spec", "specs", "__tests__", "fixtures", "examples"}
GENERIC_ENV_PREFIXES = {
    "APP", "API", "AUTH", "CI", "DATABASE", "DB", "DEV", "ENV", "INTERNAL", "LOCAL",
    "NEXT", "NEXTAUTH", "NODE", "PROD", "PUBLIC", "SECRET", "SERVER", "SERVICE", "TEST",
}


@dataclass(frozen=True)
class VendorRule:
    name: str
    aliases: tuple[str, ...]
    patterns: tuple[str, ...]


VENDOR_RULES = (
    VendorRule("HubSpot", ("hubspot",), (r"@hubspot/api-client", r"\bhubspot\b", r"HUBSPOT_")),
    VendorRule("Salesforce", ("salesforce", "sfdc"), (r"\bsalesforce\b", r"\bjsforce\b", r"SALESFORCE_", r"SFDC_")),
    VendorRule("Stripe", ("stripe",), (r"(?:^|[\"'/@])stripe(?:[\"'/@]|$)", r"STRIPE_")),
    VendorRule("Sentry", ("sentry",), (r"@sentry/", r"\bsentry_sdk\b", r"SENTRY_DSN", r"SENTRY_")),
    VendorRule("PostHog", ("posthog",), (r"\bposthog[-_a-z]*\b", r"POSTHOG_")),
    VendorRule("Twilio", ("twilio",), (r"\btwilio\b", r"TWILIO_")),
    VendorRule("OpenAI", ("openai",), (r"(?:^|[\"'/@])openai(?:[\"'/@]|$)", r"OPENAI_")),
    VendorRule("Anthropic", ("anthropic",), (r"@anthropic-ai/", r"\banthropic\b", r"ANTHROPIC_")),
    VendorRule("Google Calendar", ("google calendar", "google_calendar"), (r"calendar\.googleapis\.com", r"GOOGLE_CALENDAR_")),
    VendorRule("Microsoft Outlook Calendar", ("outlook calendar", "microsoft graph"), (r"graph\.microsoft\.com.*calendar", r"OUTLOOK_CALENDAR_", r"MICROSOFT_GRAPH_")),
    VendorRule("Zoom", ("zoom",), (r"api\.zoom\.us", r"\bzoom[_-](?:api|client|oauth)", r"ZOOM_")),
    VendorRule("Google Meet", ("google meet",), (r"meet\.google\.com", r"GOOGLE_MEET_")),
    VendorRule("SendGrid", ("sendgrid",), (r"@sendgrid/", r"\bsendgrid\b", r"SENDGRID_")),
    VendorRule("Mailgun", ("mailgun",), (r"\bmailgun\b", r"MAILGUN_")),
    VendorRule("Segment", ("segment",), (r"@segment/", r"SEGMENT_(?:KEY|TOKEN|WRITE)")),
    VendorRule("Amplitude", ("amplitude",), (r"@amplitude/", r"\bamplitude\b", r"AMPLITUDE_")),
    VendorRule("Mixpanel", ("mixpanel",), (r"\bmixpanel\b", r"MIXPANEL_")),
    VendorRule("Google Analytics", ("google analytics", "ga4"), (r"google-analytics", r"gtag\(", r"GA4_", r"GOOGLE_ANALYTICS_")),
    VendorRule("Auth0", ("auth0",), (r"@auth0/", r"\bauth0\b", r"AUTH0_")),
    VendorRule("Okta", ("okta",), (r"@okta/", r"\bokta\b", r"OKTA_")),
    VendorRule("AWS S3", ("aws s3", "amazon s3", "s3"), (r"@aws-sdk/client-s3", r"\bboto3\b.*\bs3\b", r"AWS_S3_", r"S3_BUCKET")),
    VendorRule("Algolia", ("algolia",), (r"\balgoliasearch\b", r"ALGOLIA_")),
    VendorRule("Elasticsearch", ("elasticsearch",), (r"@elastic/elasticsearch", r"\belasticsearch\b", r"ELASTICSEARCH_")),
    VendorRule("Zapier", ("zapier",), (r"hooks\.zapier\.com", r"ZAPIER_")),
    VendorRule("Slack", ("slack",), (r"@slack/", r"hooks\.slack\.com", r"SLACK_(?:TOKEN|WEBHOOK|CLIENT)")),
    VendorRule("Deepgram", ("deepgram",), (r"@deepgram/", r"\bdeepgram\b", r"DEEPGRAM_")),
    VendorRule("ElevenLabs", ("elevenlabs",), (r"\belevenlabs\b", r"ELEVENLABS_")),
)

ENV_RE = re.compile(
    r"\b([A-Z][A-Z0-9]{1,30})_(API_KEY|CLIENT_ID|CLIENT_SECRET|DSN|WEBHOOK(?:_URL)?|DATABASE_URL|DB_PASSWORD)\b"
)


@dataclass
class Evidence:
    paths: set[str] = field(default_factory=set)
    test_only: bool = True


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def is_test_path(path: pathlib.Path) -> bool:
    return bool({part.lower() for part in path.parts} & TEST_PARTS)


def iter_text_files(root: pathlib.Path):
    for path in root.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        if ".fides" in path.parts or path.name in {
            "datamap.yml", "datamap.yaml", "vendor-exclusions.json", "exclusions.json",
        }:
            continue
        if path.name not in TEXT_NAMES and path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            if path.stat().st_size > 2_000_000:
                continue
        except OSError:
            continue
        yield path


def discover(root: pathlib.Path) -> dict[str, Evidence]:
    found: dict[str, Evidence] = {}
    compiled = [(rule, [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in rule.patterns]) for rule in VENDOR_RULES]

    def record(name: str, path: pathlib.Path):
        ev = found.setdefault(name, Evidence())
        ev.paths.add(path.relative_to(root).as_posix())
        if not is_test_path(path.relative_to(root)):
            ev.test_only = False

    for path in iter_text_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for rule, patterns in compiled:
            if any(pattern.search(text) for pattern in patterns):
                record(rule.name, path)
        for match in ENV_RE.finditer(text):
            prefix = match.group(1)
            if prefix in GENERIC_ENV_PREFIXES:
                continue
            if not any(normalized(prefix) in {normalized(a) for a in rule.aliases} for rule in VENDOR_RULES):
                record(prefix.replace("_", " ").title(), path)

    # Integration/App Store/marketplace directories and generated provider registries.
    for path in root.rglob("*"):
        if not path.is_dir() or any(part in SKIP_DIRS for part in path.parts):
            continue
        lower_parts = [part.lower() for part in path.parts]
        if not any(part in {"integrations", "integration", "plugins", "providers", "app-store", "app_store", "marketplace"} for part in lower_parts):
            continue
        candidate = path.name
        candidate_norm = normalized(candidate)
        for rule in VENDOR_RULES:
            if candidate_norm and any(candidate_norm == normalized(alias) for alias in rule.aliases):
                marker = next((p for p in path.rglob("*") if p.is_file()), path)
                record(rule.name, marker)
    return found


def load_exclusions(path: pathlib.Path | None, inline: list[str]) -> tuple[dict[str, str], list[str]]:
    exclusions: dict[str, str] = {}
    errors: list[str] = []
    if path:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return {}, [f"could not load exclusions file: {exc}"]
        payload = payload.get("exclusions", payload) if isinstance(payload, dict) else payload
        if not isinstance(payload, dict):
            errors.append("exclusions must be a JSON object mapping vendor names to reasons")
        else:
            for vendor, reason in payload.items():
                if not isinstance(reason, str) or not reason.strip():
                    errors.append(f"exclusion for {vendor!r} requires a non-empty reason")
                else:
                    exclusions[normalized(str(vendor))] = reason.strip()
    for value in inline:
        vendor, sep, reason = value.partition("=")
        if not sep or not vendor.strip() or not reason.strip():
            errors.append(f"invalid --exclude {value!r}; expected Vendor=reason")
        else:
            exclusions[normalized(vendor)] = reason.strip()
    return exclusions, errors


def load_systems(manifest: pathlib.Path) -> list[dict]:
    doc, _ = load_yaml(manifest.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or not isinstance(doc.get("system", []), list):
        return []
    return [item for item in doc.get("system", []) if isinstance(item, dict)]


def system_matches(vendor: str, system: dict) -> bool:
    if normalized(str(system.get("system_type", ""))) != "third party":
        return False
    haystack = normalized(f"{system.get('fides_key', '')} {system.get('name', '')}")
    rule = next((r for r in VENDOR_RULES if r.name == vendor), None)
    aliases = (vendor,) + (rule.aliases if rule else ())
    return any(normalized(alias) in haystack for alias in aliases if normalized(alias))


def reconcile(discovered: dict[str, Evidence], systems: list[dict], exclusions: dict[str, str]):
    matches: dict[str, list[int]] = {
        vendor: [i for i, system in enumerate(systems) if system_matches(vendor, system)]
        for vendor in discovered
    }
    vendors_by_system: dict[int, list[str]] = {}
    for vendor, indices in matches.items():
        for index in indices:
            vendors_by_system.setdefault(index, []).append(vendor)

    represented, grouped, excluded, unresolved = [], [], [], []
    for vendor in sorted(discovered):
        indices = matches[vendor]
        if indices:
            if any(len(vendors_by_system[index]) > 1 for index in indices):
                grouped.append(vendor)
            else:
                represented.append(vendor)
        elif normalized(vendor) in exclusions:
            excluded.append(vendor)
        else:
            unresolved.append(vendor)
    return represented, grouped, excluded, unresolved, vendors_by_system


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("manifest", nargs="?", default=".fides/datamap.yml")
    parser.add_argument("--exclusions", type=pathlib.Path)
    parser.add_argument("--exclude", action="append", default=[], metavar="VENDOR=REASON")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = pathlib.Path(args.repo).resolve()
    manifest = pathlib.Path(args.manifest)
    if not manifest.is_absolute():
        manifest = root / manifest
    if not root.is_dir() or not manifest.is_file():
        print("error: repository directory or manifest does not exist", file=sys.stderr)
        return 2
    exclusions_path = args.exclusions
    if exclusions_path and not exclusions_path.is_absolute():
        exclusions_path = root / exclusions_path
    exclusions, errors = load_exclusions(exclusions_path, args.exclude)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 2

    discovered = discover(root)
    systems = load_systems(manifest)
    represented, grouped, excluded, unresolved, vendors_by_system = reconcile(discovered, systems, exclusions)

    for vendor in sorted(discovered):
        ev = discovered[vendor]
        qualifier = " (test/example evidence only)" if ev.test_only else ""
        print(f"DISCOVERED {vendor}{qualifier}: {', '.join(sorted(ev.paths))}")
    for index, vendors in sorted(vendors_by_system.items()):
        if len(vendors) > 1:
            system = systems[index]
            print(f"GROUPED {system.get('name') or system.get('fides_key')}: {', '.join(sorted(vendors))}")
    for vendor in excluded:
        print(f"EXCLUDED {vendor}: {exclusions[normalized(vendor)]}")
    for vendor in unresolved:
        print(f"WARN unresolved material vendor: {vendor}")

    print(
        "RECONCILIATION: "
        f"{len(discovered)} discovered, {len(represented)} represented, {len(grouped)} grouped, "
        f"{len(excluded)} excluded, {len(unresolved)} unresolved"
    )
    return 1 if unresolved else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
