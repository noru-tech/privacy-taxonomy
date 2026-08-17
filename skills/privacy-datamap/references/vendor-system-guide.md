# External vendor system guide

Use this guide when discovering, modeling, reconciling, and reporting third-party integrations.

## Discovery evidence

Inspect all of these sources before concluding that vendor coverage is complete:

- direct SDK imports and dependency manifests;
- integration, plugin, App Store, marketplace, and generated provider registries;
- OAuth callbacks, authorization URLs, webhook handlers, and API client construction;
- `*_API_KEY`, `*_CLIENT_ID`, `*_CLIENT_SECRET`, `*_DSN`, `*_WEBHOOK`, provider-specific database
  credentials, and optional-integration feature flags;
- Docker Compose services, infrastructure definitions, object-storage/search configuration; and
- tests containing realistic provider payloads when production code does not reveal transferred
  fields.

Explicitly check CRM, calendar, conferencing, payments, email/messaging, analytics/advertising,
observability, storage/search, automation/webhooks, identity, AI, and voice-processing providers.

## Modeling rules

- Create one System for each deployable first-party application or service.
- Create a `Third Party` System for every material external vendor that receives, stores, processes,
  or can access personal data. A first-party `third_party_sharing` declaration does not replace the
  receiving vendor's System.
- Preserve vendor identity. Never collapse named vendors into an anonymous system such as
  `External Providers`.
- Prefer separate systems for high-impact CRM, payment, identity, communications, analytics, AI,
  storage, and observability processors.
- Group vendors only when they perform equivalent processing, receive substantially the same data
  categories, and share the same subjects and purpose. List every grouped vendor in the System
  `name` and record the reason in the reconciliation report.
- Use `dataset_references: []` when the repository does not define the vendor's internal schema. If
  a vendor-backed store is represented by a local Dataset, reference it.

Include implemented integrations that materially process personal data even when deployment status
is unknown. Add `# TODO: verify enabled/configured in this deployment`; do not claim active use from
availability alone. Exclude only demonstrably test-only, example-only, dead, or non-data-bearing
integrations, and always record a reason.

## AI processing

Use `third_party_sharing` when personal data is sent to an external AI provider for inference,
summarization, transcription, generation, or classification. Use `train_ai_system` only when source
evidence shows personal data is used for training or fine-tuning. An OpenAI, Anthropic, or other AI
SDK alone is not evidence of model training.

## Reconciliation

Before writing the manifest, make an internal row for every discovered vendor with:

| Vendor | Evidence | Purpose | Categories | Subjects | System `fides_key` | Disposition | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| HubSpot | dependency + sync client | CRM | email, name | prospect, customer | `hubspot_crm` | included | — |

Each material vendor must be included as its own System, included in a named grouped System, or
explicitly excluded with a reason. Do not finish with a vendor lacking a disposition.

Run the deterministic checker after taxonomy validation:

```bash
python3 "$SKILL_DIR/scripts/check_system_coverage.py" . .fides/datamap.yml \
  --exclusions .fides/vendor-exclusions.json
```

The optional exclusions file is a JSON object whose keys are vendor names and values are non-empty
reasons (an `{"exclusions": {...}}` wrapper is also accepted). Repeat
`--exclude "Vendor=reason"` for inline exclusions. The checker warns rather than generating Systems
and exits nonzero when a discovered material vendor remains unresolved.

Its built-in aliases include HubSpot, Salesforce, Stripe, Sentry, PostHog, Twilio, OpenAI,
Anthropic, major calendar/conferencing providers, common communications/analytics vendors, identity
providers, storage/search services, automation services, and voice-processing providers. Treat the
alias list as a deterministic baseline, not an exhaustive vendor catalog; manually reconcile
unrecognized providers found during the broader source review.
