# Classification guide

How to map source-code artifacts to Fideslang resources. The bundled taxonomy snapshot
(`references/taxonomy/*.json`, also printed by `scripts/dump_taxonomy.py`) is the **only** source of
valid keys — never invent a key. When unsure between two keys, prefer the **more specific** (leaf)
one; when genuinely unsure whether a field is personal data at all, leave `data_categories` off and
add a `# TODO: verify` comment rather than guessing.

## Core principles

1. **Most-specific wins.** A column literally named `email` → `user.contact.email`, not `user.contact`.
2. **One field can carry several categories.** A `billing_address` text blob may warrant
   `user.contact.address.street` + `.city` + `.postal_code`.
3. **Non-personal / operational columns** (surrogate PKs, timestamps, soft-delete flags, row
   versions) → `system.operations`, or leave uncategorized. Do not force a `user.*` label onto them.
4. **Foreign keys** that point at a person record can take `user.unique_id`; pure join keys to
   non-person tables are `system.operations`.
5. **Specificity beats coverage.** It's better to leave a `# TODO: verify` than to apply a confident
   wrong label — wrong privacy labels are worse than missing ones.

## Field-name → data_category cheat-sheet

| Field name signal | data_category |
| --- | --- |
| `email`, `email_address`, `e_mail` | `user.contact.email` |
| `phone`, `mobile`, `tel`, `phone_number` | `user.contact.phone_number` |
| `fax` | `user.contact.fax_number` |
| `url`, `website`, `homepage` | `user.contact.url` |
| `first_name`, `given_name` | `user.name.first` |
| `last_name`, `surname`, `family_name` | `user.name.last` |
| `name`, `full_name`, `display_name` | `user.name` |
| `username`, `handle`, `login` | `user.account.username` |
| `password`, `passwd`, `pwd`, `password_hash`, `pw_hash` | `user.authorization.password` |
| `token`, `api_key`, `secret`, `access_token`, `refresh_token` | `user.authorization.credentials` |
| `fingerprint`, `faceid`, `face_id` | `user.biometric.fingerprint` / `user.authorization.biometric` |
| `street`, `address1`, `address_line1` | `user.contact.address.street` |
| `city`, `town` | `user.contact.address.city` |
| `state`, `province`, `region` | `user.contact.address.state` |
| `zip`, `zipcode`, `postal_code`, `postcode` | `user.contact.address.postal_code` |
| `country` | `user.contact.address.country` |
| `lat`, `lng`, `latitude`, `longitude`, `geo`, `coordinates` | `user.location.precise` |
| `ip`, `ip_address`, `client_ip`, `last_login_ip` | `user.device.ip_address` |
| `device_id`, `udid`, `idfa`, `gaid` | `user.device.device_id` |
| `cookie`, `cookie_id` | `user.device.cookie_id` |
| `dob`, `date_of_birth`, `birth_date`, `birthday` | `user.demographic.date_of_birth` |
| `age`, `age_range` | `user.demographic.age_range` |
| `gender`, `sex` | `user.demographic.gender` |
| `language`, `locale`, `lang` | `user.demographic.language` |
| `marital_status` | `user.demographic.marital_status` |
| `race`, `ethnicity` | `user.demographic.race_ethnicity` |
| `religion`, `religious_*` | `user.demographic.religious_belief` |
| `political_*` | `user.demographic.political_opinion` |
| `sexual_orientation` | `user.demographic.sexual_orientation` |
| `ssn`, `social_security`, `national_id`, `tax_id`, `nino` | `user.government_id.national_identification_number` |
| `passport`, `passport_number` | `user.government_id.passport_number` |
| `drivers_license`, `dl_number`, `license_number` | `user.government_id.drivers_license_number` |
| `card_number`, `cc_number`, `pan`, `credit_card` | `user.financial.credit_card` |
| `iban`, `account_number`, `bank_account`, `routing` | `user.financial.bank_account` |
| `salary`, `income`, `payment`, `amount_paid` | `user.financial` / `user.payment` |
| `job_title`, `title`, `position`, `role` (employment) | `user.job_title` |
| `employer`, `company`, `organization` | `user.contact.organization` |
| `search_query`, `query_history` | `user.behavior.search_history` |
| `viewed`, `clicks`, `events`, `activity`, `pageviews` | `user.behavior` |
| `purchase_history`, `orders` | `user.behavior.purchase_history` |
| `bio`, `about`, `notes`, `comment`, `post`, `message` | `user.content.public` / `user.content.private` |
| `avatar`, `profile_picture`, `photo` | `user.content.self_image` |
| `heart_rate`, `diagnosis`, `medical_*`, `health_*` | `user.health_and_medical` |
| `genetic_*`, `dna` | `user.health_and_medical.genetic` |
| `user_id`, `account_id`, `customer_id`, `member_id` | `user.unique_id` |
| `id` (surrogate PK), `created_at`, `updated_at`, `deleted_at`, `version`, `_v` | `system.operations` *(or leave off)* |

If a name doesn't match anything above, read the surrounding model/comments for intent, then pick the
closest snapshot key — or leave a `# TODO: verify`.

## Where data_categories live in a dataset

`collections` ≈ tables / models / message types; `fields` ≈ columns / attributes (nest `fields` for
JSON, embedded docs, or protobuf sub-messages). Apply categories at the **field** level by default;
use collection- or dataset-level categories only for a label that truly applies to everything below.

## Building `system` resources

One System per deployable service / app (in a monorepo, usually one per top-level service dir).

- **`system_type`** — free text; conventional values: `Application`, `Service`, `Database`,
  `Data Warehouse`, `Third Party`, `Integration`.
- **`dataset_references`** — list the `fides_key`s of datasets this system reads/writes.
- **`privacy_declarations`** — one per distinct *purpose*. Each needs:
  - `name` — human label for the purpose.
  - `data_use` — from `data_uses.json`. Common picks:
    | Intent in code | data_use |
    | --- | --- |
    | login, sessions, core CRUD the product needs | `essential.service` / `essential.service.authentication` |
    | usage metrics, dashboards, reporting | `analytics.reporting` |
    | email/SMS campaigns, ads, retargeting | `marketing.advertising` |
    | recommendations, personalized feed | `personalize.content` |
    | recruiting / HR | `employment.recruitment` |
    | billing, invoicing, tax | `finance` |
    | sending data to a 3rd-party processor | `third_party_sharing` |
    | training/fine-tuning a model on user data | `train_ai_system` |
  - `data_categories` — the categories actually processed for that purpose.
  - `data_subjects` — from `data_subjects.json`. Infer from context:
    | App context | data_subject |
    | --- | --- |
    | storefront / SaaS end users | `customer` (and `anonymous_user` for un-authed traffic) |
    | not-yet-customers, leads | `prospect` |
    | HR / payroll / internal tooling | `employee` |
    | applicant tracking | `job_applicant` |
    | healthcare | `patient` |
    | marketplace/B2B suppliers | `supplier_vendor` |

## Spotting systems & third-party data flows from code

- Third-party SDK imports/clients imply an **egress** flow and often `third_party_sharing`:
  Stripe/Braintree (payments), Segment/Amplitude/Mixpanel/GA (analytics), Sentry (telemetry),
  Twilio/SendGrid/Mailgun (comms), Salesforce/HubSpot (CRM), OpenAI/Anthropic (AI).
- Env vars / config keys (`*_API_KEY`, `*_DSN`, `*_WEBHOOK`) hint at integrated systems.
- A monorepo's `services/*`, `apps/*`, or separate `Dockerfile`s usually each map to one System.
