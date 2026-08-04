# SPEC.md — the specification this module was built from

**This module is not generator output.** Unlike the example modules in this
repository, `odomate_connector` is first-party OdoMate tooling: it was
specified and written by hand, because it is the component customers install
in *their own* database and must therefore be auditable line by line. It is
published here so it can be read before it is trusted, and so the Odoo Apps
Store can list it from this repository.

Written July 2026, targeting Odoo 19 Community and Enterprise.

---

## Module: odomate_connector

Export a redacted structural snapshot of an Odoo database
(`odomate_context.json`) that OdoMate can use to generate modules fitting the
customer's real environment, and to build a replica environment to test them
against.

### The governing constraint

> **Structural context, never your business records.**

Almost all of the generation-quality value lives in *metadata* — schema,
installed modules, customizations, settings. Almost all of the liability lives
in *credentials and business records*. The module is shaped to take the first
and never the second.

Consequences, all of which are requirements rather than preferences:

- **No business records.** Record *counts* only. No partner, employee or user
  rows; no names, no emails.
- **No credential custody.** The module never asks for, stores, or transmits a
  credential. It makes no network calls at all — the customer downloads a file
  and decides what to do with it.
- **No inbound path.** Nothing about this design lets OdoMate reach into the
  customer's database. The direction of travel is strictly outward,
  customer-initiated.
- **Auditable by the customer.** The output is pretty-printed JSON, and the
  code that produces it is public.

### What the snapshot contains

`schema_version: 1`, formally described by `schema/odomate_context.schema.json`.

- **instance** — Odoo version, edition (derived from whether any installed
  module carries an Enterprise licence), installed languages, multi-company
  flag, and the database UUID **as a SHA-256 hash** (identity without
  identifying).
- **modules** — every installed module with its version, author, licence,
  auto-install flag, and a derived `source` of `core | enterprise | oca |
  thirdparty | custom`. The classification drives replica building: core
  modules can be reinstalled in a sandbox, Enterprise ones cannot, and `custom`
  marks code OdoMate does not have.

  Manifest provenance travels with each module so a replica can fetch the
  source again rather than guess at it. `website` is decisive for OCA, whose
  convention is that it holds the exact repository — `purchase_request` carries
  `https://github.com/OCA/purchase-workflow`, which turns rebuilding into a
  clone. `licence` decides what may lawfully be installed into a sandbox.
  `url` and `published_version` are written by Odoo's Apps Store download path
  and are the only signal that a module came from the store rather than from a
  repository; both are empty on a repository-installed system.
- **models / fields** — the full non-transient model list with field name,
  type, selection values, relation target, required flag, and whether the field
  is a database-level customization (`ir.model.fields.state == 'manual'`).
- **views** — only views the customer created or edited: a view with no module
  external ID, or a module view whose arch has been modified.
- **settings** — boolean and selection `res.config.settings` values.
- **config_params** — an allowlisted subset of `ir.config_parameter`.
- **groups** — security groups with the number of users holding each.
- **automations** — names and models of automated actions. **No code bodies**
  in v1.
- **record_counts** — per-model row-count estimates, read from PostgreSQL
  statistics rather than by touching rows.

### Redaction rules

1. **Allowlist first.** System parameters are only considered if explicitly
   listed; everything else never leaves.
2. **Pattern second.** Any key *or* value matching
   `key|secret|token|password|api|dkim|private` (case-insensitive) is dropped,
   including allowlisted ones. An allowlist entry that this rule would always
   kill is itself a defect, and a test enforces that none exist.
3. **Type-restricted settings.** Only boolean and selection settings are read.
   This is a security boundary, not a simplification: Odoo core stores real
   secrets in *text* settings fields backed by system parameters (for example
   the reCAPTCHA private key), so reading only booleans and selections excludes
   that entire class structurally.
4. **No user detail.** Groups carry a *count*, never a membership list.

### Size limit

Roughly 5 MB, with disclosed degradation rather than silent truncation. If the
snapshot would exceed the cap it drops, in order: customized view bodies
(keeping the structural metadata), then the field lists of standard models
carrying no customizations. Whatever was dropped is listed in the file's
`truncated` array, so a consumer never has to guess whether it is complete.

### User interface

A single wizard at **Settings ▸ Technical ▸ Export OdoMate Context**, gated on
the Settings administration group. It states what will and will not be
collected, generates on demand, shows a summary of what was found, and offers
the file for download.

### Architecture note

All decisions about *what leaves the database* live in `snapshot_lib.py`, which
imports nothing but the Python standard library — no Odoo, no third-party
packages. `collector.py` only reads the environment and returns plain
dictionaries; the wizard joins the two. The split keeps the security-critical
logic reviewable and testable in isolation, which is why the test suite can
cover it without a database.

### Tests

57 tests, run with `--test-tags /odomate_connector`:

- Pure-logic tests over the redaction, classification, assembly, size-cap and
  schema-contract behaviour, including a blessed golden-file comparison that
  catches any unintended change in output shape or content.
- Database tests that build a real snapshot and assert that a seeded secret
  parameter, a created partner's name and email, and the raw database UUID are
  all absent from the output; that customizations are captured; that stock
  views are not misreported as customized; and that the wizard produces a
  valid, downloadable file.
