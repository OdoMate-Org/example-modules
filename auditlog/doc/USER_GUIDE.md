# User Guide: Audit Log

> Record who created, changed, deleted, read or exported which records in Odoo, with old and new values for every changed field.

---

## Table of Contents

1. [What does this module do](#1-what-does-this-module-do)
2. [Where to find it in Odoo](#2-where-to-find-it-in-odoo)
3. [First-run setup: creating an audit rule](#3-first-run-setup-creating-an-audit-rule)
4. [Reading the logs](#4-reading-the-logs)
5. [Core workflows](#5-core-workflows)
6. [Full log vs fast log](#6-full-log-vs-fast-log)
7. [Failure policy, multi-company and retention](#7-failure-policy-multi-company-and-retention)
8. [Demo data](#8-demo-data)
9. [Access roles](#9-access-roles)
10. [Limitations](#10-limitations)

---

## 1. What does this module do

Audit Log keeps a tamper-evident history of operations on the Odoo models you choose. You create one **rule** per model (for example *Contact*), pick which operations to track, and confirm the rule. From then on every tracked operation produces a **log** (who, when, which record, which operation) with one **log line** per changed field showing the old and new value. Auditors, administrators and compliance officers use it to answer "who changed this, and what was it before?".

| Capability | Details |
|---|---|
| Per-model audit rules | One rule per model (`auditlog.rule`); a second rule on the same model is refused with "There is already a rule defined on this model." |
| Tracked operations | Creates, Writes, Deletes, Reads and Exports, each switched on/off individually |
| Field-level history | Each log line stores the field label, technical name, raw and human-readable old/new value |
| Readable relational values | Many2one and many2many/one2many values are shown as record names; a record that no longer exists shows as `<id> (DELETED)` |
| Deleted-record snapshot | With **Capture Record**, a delete log keeps all field values of the record as it was just before deletion |
| Export tracking | One log per export listing the exported record ids, with an **Exported Records** smart button that re-opens them |
| Exclusions | Users to Exclude (e.g. integration users) and Fields to Exclude (e.g. notes) per rule |
| Session and request trail | Each log links to the user session and the HTTP request (URL path) that produced it |
| Multi-company isolation | Logs carry the audited record's company; users only see logs of their allowed companies |
| Retention | Optional scheduled action deletes audit data older than 180 days |
| "View logs" shortcut | Confirming a rule adds a **View logs** action to the audited model's form (Actions menu) |

---

## 2. Where to find it in Odoo

The module lives in the technical settings, so **developer mode must be active** (Settings → Activate the developer mode). The parent menu **Audit** is visible only to Settings administrators (`base.group_system`).

**Path:** `Settings` → `Technical` → `Audit`

| Menu | Purpose | Who sees it |
|---|---|---|
| **Rules** | Create, confirm and reset audit rules | Auditlog User (read), Auditlog Manager (edit) |
| **Logs** | One line per audited operation; open for the field changes | Auditlog User and up |
| **Log Lines** | Flat list of every field change across all logs, searchable by old/new value | Only **Access Rights** (`base.group_erp_manager`) |
| **User sessions** | Login sessions that produced logs, with their HTTP requests | Auditlog User and up |
| **HTTP Requests** | Individual requests (URL path + root URL) and the logs they produced | Auditlog User and up |
| **Delete Old Logs** | Dialog that purges old audit data now (see [Retention](#7-failure-policy-multi-company-and-retention)) | Auditlog Manager |

Additionally, on any audited model's form view (for example a contact), **Actions (gear icon) → View logs** lists the logs of that one record.

On a rule's form, the **Logs** smart button (top right, e.g. **29 Logs**) opens every log of the rule's model.

---

## 3. First-run setup: creating an audit rule

> ⚠️ Nothing is logged until at least one rule is **Confirmed**.

**Path:** `Settings` → `Technical` → `Audit` → `Rules` → `New`

| Field | What to enter | Example |
|---|---|---|
| **Name** | Free label for the rule | `Partner audit trail` |
| **Model** | The model to audit. Transient models and the `auditlog.*` models themselves cannot be selected | `Contact` (`res.partner`) |
| **Type** | **Full log** (default) or **Fast log** — see [section 6](#6-full-log-vs-fast-log) | Full log |
| **On Logging Failure** | **Block the operation** (default) or **Skip the log** — see [section 7](#7-failure-policy-multi-company-and-retention) | Block the operation |
| **Log Creates** | Track record creation (default on) | ✅ |
| **Log Writes** | Track modifications (default on) | ✅ |
| **Log Deletes** | Track deletions (default on) | ✅ |
| **Log Reads** | Track every read/open of a record (default off — expensive) | ❌ |
| **Log Exports** | Track exports (default on) | ✅ |
| **Capture Record** | On delete, keep a full snapshot of the deleted record's values | ✅ |
| **Users to Exclude** (tab) | Users whose operations are never logged | `OdooBot`, an API integration user |
| **Fields to Exclude** (tab) | Fields of the chosen model that never produce a log line | `Notes` (`comment`) |

Then click **Confirm**. The status bar moves from **Draft** to **Confirmed**, the created "View logs" action is bound to the model's form (its technical record is shown as the read-only **Action** field in developer mode only), and auditing starts immediately. Use the **Logs** smart button to jump to the rule's logs.

**Status flow:** Draft → Confirmed (→ Set to Draft → Draft)

> 💡 Once a rule is Confirmed, all its configuration fields are read-only. To change the operations, type or exclusions, click **Set to Draft**, edit, and click **Confirm** again. While a rule is in Draft nothing is logged for that model and the "View logs" action disappears from the model's form; re-confirming reuses the same action.

---

## 4. Reading the logs

**Path:** `Settings` → `Technical` → `Audit` → `Logs`

The list shows **Date**, **Resource Name**, **Model**, **Method** (`create`, `write`, `unlink`, `read`, `export_data`) and **User**. Optional columns: Resource ID, Type and (for multi-company users) Company.

Filters: **Create**, **Write**, **Delete**, **Read**, **Export**. Group by: **User**, **Model**, **Method**, **Company**, **Date**.

Opening a log shows:

| Area | Content |
|---|---|
| **Log** group | Date, User, Method, Type, Company (multi-company only) |
| **Resource** group | Resource Name, Model, Technical Model Name, Resource ID, Resource IDs (exports only) |
| **Fields updated** tab | One line per field: Description, Old value Text, New value Text (raw values and technical name available as optional columns) |
| **Technical** tab | Session and HTTP Request that produced the log |
| **Exported Records** smart button | Only on export logs: opens the exported records (fails with a clear message if the model has been uninstalled) |

Logs, sessions and requests are read-only in the interface (no Create/Edit buttons).

**Log Lines** (`Settings` → `Technical` → `Audit` → `Log Lines`) is a flat, read-only view of every field change, useful for questions like "who ever set this email?". Search by **Old value Text** / **New value Text**, filter by Create/Write/Delete and group by User, Model, **Field** or Company.

---

## 5. Core workflows

### Journey 1: Find out who renamed a customer (worked example)

Setup: rule *Partner audit trail* on `Contact`, Full log, Log Writes enabled, Confirmed.

1. A salesperson opens the contact **Azure Interior** and changes **Name** to `Azure Interior SA`, then saves.
2. Exactly **one** `write` log is created:

   | Log field | Value |
   |---|---|
   | Resource Name | Azure Interior SA |
   | Model | Contact |
   | Method | write |
   | User | the salesperson |
   | Type | Full log |

3. Its **Fields updated** tab has one line per changed field — here the one field the user edited:

   | Description | Old value Text | New value Text |
   |---|---|---|
   | Name | Azure Interior | Azure Interior SA |

   Because a full log compares all stored fields, a stored computed field that changes as a consequence (on contacts, typically **Complete Name**) gets its own line with the same old/new text. Nothing else is listed.

4. The auditor finds it either via **Logs** → filter **Write** → search `Azure`, or directly from the contact form: **Actions → View logs**.

Fields whose value did not change produce no line; `create_date`, `write_date`, `create_uid`, `write_uid` and `display_name` are never logged.

### Journey 2: Investigate a deleted record

With **Log Deletes** and **Capture Record** enabled, deleting a contact creates an `unlink` log whose **Fields updated** tab lists every stored field with its last value in **Old value Text**. Without Capture Record the `unlink` log still records who deleted which record id, but with no lines.

### Journey 3: Check what was exported

With **Log Exports**, each export (list view → select → Actions → Export) creates one `export_data` log. **Resource IDs** holds the JSON list of exported ids; the **Exported Records** smart button (e.g. "12 Exported Records") re-opens exactly those records. Reading done internally by the export is not logged separately, so an export does not flood the log with read entries.

### Journey 4: Exclude a noisy user or field

Set the rule to Draft, add the user in **Users to Exclude** or the field in **Fields to Exclude**, and Confirm. From the next operation on, the excluded user's actions are not logged at all, and the excluded field never gets a log line (other changed fields in the same save still do).

---

## 6. Full log vs fast log

| | **Full log** (default) | **Fast log** |
|---|---|---|
| What is read | All stored, non-binary fields of the record **before and after** the operation | Nothing extra — only the values passed to create/write |
| Old values on write | Real previous values | Always shown as `False` |
| Side-effect changes (stored computed fields) | Logged | Not logged |
| Cost | Two extra reads per write | Minimal |
| Best for | Compliance, small/medium-volume models | High-volume models where "what was sent" is enough |

**Example — the same rename with Fast log:** the line shows **Old value Text** `False`, **New value Text** `Azure Interior SA`. You know what was written, but not what it replaced.

Common to both types:
- On **create**, fields with empty initial values (empty text, `False`, empty lists) are skipped, so a new contact with only Name and Email produces two lines, not forty.
- Binary fields (images, attachments) are never logged.
- Relational values are displayed by name, e.g. Tags `VIP, Wholesale`; a tag that no longer exists shows as `7 (DELETED)`.

---

## 7. Failure policy, multi-company and retention

### On Logging Failure

| Setting | If writing the audit record fails… | Use when |
|---|---|---|
| **Block the operation** (default) | The user's operation is rolled back and the user sees the error. No change without a trace. | Compliance requires a guaranteed trail |
| **Skip the log** | The user's operation completes; the error is written to the server log; **no audit record** exists for that operation | Business continuity matters more than completeness |

### Live configuration

The rule's type, exclusions, Capture Record and failure policy are read from the database at **every** logged operation, so a change becomes effective immediately in every server worker — no restart needed.

### Multi-company

- Each log stores the **company of the audited record** (when the model has a `company_id` field); exports get a company only if all exported records share one.
- Logs, log lines, the Log Lines view, user sessions and HTTP requests are visible only if their company is among the user's **allowed companies**, or if they have no company (e.g. logs of models without a company field).
- Rules themselves are global: one rule on `Contact` audits contacts of every company.
- The **Company** column/filter/group-by is hidden for single-company users and appears for users in multi-company mode.

**Example:** a Contact of *Auditlog Demo Company B* is edited. A user whose allowed companies are only the main company does not see that log in **Logs** or **Log Lines**; a user allowed in both companies does.

### Retention (auto-vacuum)

**Path:** `Settings` → `Technical` → `Automation` → `Scheduled Actions` → **Auto-vacuum audit logs**

| Property | Value |
|---|---|
| Shipped state | **Inactive** — nothing is ever deleted until you activate it |
| Frequency | Every 1 day |
| Code | `model.autovacuum(180)` — keeps 180 days |
| What is deleted | Logs (with their lines), HTTP requests and user sessions older than the retention period, oldest first |

To keep one year, change the code to `model.autovacuum(365)` and tick **Active**. Only Auditlog Managers can run the vacuum.

**Run it now:** `Settings` → `Technical` → `Audit` → **Delete Old Logs** opens a dialog with **Keep Last (Days)** (default `180`) and **Chunk Size** (`0` = no limit; otherwise the maximum number of records removed per model in this run). Click **Delete Old Logs**: a notification confirms "Audit data older than 180 days has been deleted." Example: with Keep Last (Days) = `90` on 25 Sep 2026, every log created on or before 27 Jun 2026 is deleted together with its log lines, while logs from July onwards stay.

### Sessions and requests

- **User sessions**: the **Session ID** is a SHA-256 fingerprint of the HTTP session identifier, never the raw id, so it cannot be used to hijack a session. Display name: `<user> (<date>)`.
- **HTTP Requests**: stores **Path** (e.g. `/web/dataset/call_kw/res.partner/web_save`), **Root URL**, user, session and linked logs. The user context is not stored.
- Operations done outside an HTTP request (scheduled actions, shell scripts) produce logs without session/request.

---

## 8. Demo data

When installed with demo data, the module provides:

| Record | Details |
|---|---|
| Rule **Partner audit trail** | On `Contact`, Confirmed, excludes the **Notes** (`comment`) field |
| Company **Auditlog Demo Company B** | Second company to try multi-company visibility |
| User **audit_viewer** (password `audit_viewer`) | Auditlog User, restricted to the main company — log in to see that Company B logs are hidden |
| ~20 sample logs | Mix of create/write/unlink entries to explore filters and grouping |

> ⚠️ Change or deactivate the `audit_viewer` user on any database reachable from outside.

---

## 9. Access roles

| Role | Rules | Logs / Log lines / Sessions / Requests | Log Lines menu | Auto-vacuum |
|---|---|---|---|---|
| **Auditlog User** | ✅ Read | ✅ Read (own allowed companies) | ❌ (unless also Access Rights) | ❌ |
| **Auditlog Manager** (implies User) | ✅ Read, create, edit, delete, Confirm / Set to Draft | ✅ Full (own allowed companies) | ❌ (unless also Access Rights) | ✅ |
| **Access Rights** (`base.group_erp_manager`) | — | — | ✅ Read | — |
| **Settings** (`base.group_system`) | Automatically Auditlog Manager | Automatically Auditlog Manager | ✅ (Settings implies Access Rights) | ✅ |

The admin user is made Auditlog Manager at install. Because the **Audit** menu sits under **Settings → Technical**, a user needs the Settings role and developer mode to reach it through the menu.

To assign: `Settings` → `Users & Companies` → `Users` → select user → **Auditlog Rights** field on the Access Rights tab.

---

## 10. Limitations

| Topic | Limitation |
|---|---|
| Implementation technique | The module patches ORM methods (`create`, `write`, `unlink`, `read`, `export_data`) on the audited model classes at registry level, the same technique as Odoo's `base_automation`. It is robust within a release, but budget a review/rewrite on each major Odoo upgrade. |
| Read logging | **Log Reads** writes one log per read record on every read, including list views and automatic reads. On high-traffic models (contacts, products) this grows the database fast and slows the UI. Enable only on sensitive, low-volume models. |
| Fast log | Cannot show old values (always `False`) and does not capture side-effect changes. |
| Log Lines view | A read-only database view; it cannot be edited or deleted from and is purged only via its underlying logs. |
| Read-only transactions | Logs produced during read-only requests (e.g. read logging) are written in a separate database cursor, so they persist even if the request itself later fails. |
| Direct SQL | Changes made by raw SQL, or by code that bypasses the ORM methods, are not logged. |
| Binary fields | Images and files are never logged. |
| Rule scope | One rule per model; rules cannot be restricted to a company or a record domain; `auditlog.*` and transient models cannot be audited. |
| Editing a confirmed rule | Configuration is read-only while Confirmed; use Set to Draft → edit → Confirm (nothing is logged while in Draft). |
| Tamper resistance | Auditlog Managers (and therefore Settings admins) can delete logs. The module is an audit trail, not a cryptographically sealed ledger. |
| Retention | The auto-vacuum cron ships inactive; without activating it logs grow indefinitely. |
| Integrations | No export to SIEM or external log systems; no reports (PDF). |
