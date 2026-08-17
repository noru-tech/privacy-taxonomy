#!/usr/bin/env python3
"""Regression tests for check_system_coverage.py (standard library only)."""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest


SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "scripts" / "check_system_coverage.py"
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"


def run_checker(fixture: str, manifest: str = "datamap.yml", *extra: str):
    root = FIXTURES / fixture
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(root), manifest, *extra],
        text=True,
        capture_output=True,
        check=False,
    )


class CoverageCheckerTests(unittest.TestCase):
    def test_named_vendor_systems_are_reconciled(self):
        result = run_checker("vendor-repo")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("3 discovered, 3 represented", result.stdout)

    def test_missing_hubspot_cannot_hide_behind_generic_system(self):
        fixture = FIXTURES / "vendor-repo"
        with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False) as handle:
            handle.write(
                "system:\n"
                "  - fides_key: external_providers\n"
                "    name: External Providers\n"
                "    system_type: Third Party\n"
            )
            manifest = pathlib.Path(handle.name)
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(fixture), str(manifest)],
                text=True, capture_output=True, check=False,
            )
        finally:
            manifest.unlink()
        self.assertEqual(result.returncode, 1)
        self.assertIn("unresolved material vendor: HubSpot", result.stdout)

    def test_vendor_name_on_first_party_app_is_not_a_vendor_system(self):
        fixture = FIXTURES / "vendor-repo"
        with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False) as handle:
            handle.write(
                "system:\n"
                "  - fides_key: app_with_hubspot_stripe_sentry\n"
                "    name: App using HubSpot, Stripe, and Sentry\n"
                "    system_type: Application\n"
            )
            manifest = pathlib.Path(handle.name)
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(fixture), str(manifest)],
                text=True, capture_output=True, check=False,
            )
        finally:
            manifest.unlink()
        self.assertEqual(result.returncode, 1)
        self.assertIn("3 unresolved", result.stdout)

    def test_app_store_directory_is_scanned(self):
        result = run_checker("monorepo-app-store")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("HubSpot", result.stdout)

    def test_optional_ai_is_inference_not_training(self):
        result = run_checker("optional-ai")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = (FIXTURES / "optional-ai" / "datamap.yml").read_text(encoding="utf-8")
        self.assertIn("data_use: third_party_sharing", manifest)
        self.assertNotIn("train_ai_system", manifest)

    def test_test_only_vendor_can_be_excluded_with_reason(self):
        exclusions = FIXTURES / "test-only" / "exclusions.json"
        result = run_checker("test-only", "datamap.yml", "--exclusions", str(exclusions))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("1 excluded, 0 unresolved", result.stdout)

    def test_exclusion_requires_reason(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            handle.write('{"Twilio": ""}')
            exclusions = pathlib.Path(handle.name)
        try:
            result = run_checker("test-only", "datamap.yml", "--exclusions", str(exclusions))
        finally:
            exclusions.unlink()
        self.assertEqual(result.returncode, 2)
        self.assertIn("requires a non-empty reason", result.stdout)

    def test_equivalent_calendars_may_be_named_group(self):
        result = run_checker("calendar-group")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("0 represented, 2 grouped", result.stdout)
        self.assertIn("Google Calendar and Microsoft Outlook Calendar", result.stdout)

    def test_realistic_saas_forward_fixture_has_no_unresolved_vendors(self):
        result = run_checker("realistic-saas")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("6 discovered", result.stdout)
        self.assertIn("0 unresolved", result.stdout)

    def test_taxonomy_validator_still_accepts_worked_example(self):
        validator = SKILL_DIR / "scripts" / "validate_manifest.py"
        example = SKILL_DIR / "references" / "example-datamap.yml"
        result = subprocess.run(
            [sys.executable, str(validator), str(example)],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
