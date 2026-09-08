# Employee Document Expiry Tracking — User Guide

Technical name: `odomate_hr_documents` · Version `19.0.1.0.0` · Odoo 19 Community

## Table of contents

1. [What this module does](#1-what-this-module-does)
2. [Installation](#2-installation)
3. [Configuration](#3-configuration)
4. [Daily use](#4-daily-use)
5. [The chasing patterns, with worked examples](#5-the-chasing-patterns-with-worked-examples)
6. [Renewing a document](#6-renewing-a-document)
7. [Who can see and do what](#7-who-can-see-and-do-what)
8. [Forms & Templates](#8-forms--templates)
9. [Reference: models and fields](#9-reference-models-and-fields)
10. [Limitations](#10-limitations)

---

## 1. What this module does

It keeps one record per expiring employee document — a work permit, a driving
licence, a first-aid certificate — and makes sure nobody discovers the expiry
the week after it happened.

Three things happen automatically, once a day, in one scheduled run:

1. Any **Valid** document whose expiry date is now in the past becomes **Expired**.
2. Each **Valid** or **Expired** document is checked against its document type's
   *chasing pattern*. If today is a chase day, the employee gets an email and
   their manager gets a To-Do activity dated on the expiry date.
3. Drafts are never chased, never expired, and never emailed about.

Scans live in the standard Odoo chatter of each document — there is no separate
file field and no separate storage model, so attachments, followers and the
message history all behave exactly like everywhere else in Odoo.

## 2. Installation

1. Copy `odomate_hr_documents` into your addons path.
2. **Apps → Update Apps List**.
3. Search for *Employee Document Expiry Tracking* and click **Install**.

Dependencies `hr` and `mail` install automatically if they are not present.

After installation the administrator holds **Officer: Manage all employees**
(`hr.group_hr_manager`), which is what makes the **Document Types** menu visible.

## 3. Configuration

### 3.1 Document types — Employees → Employee Documents → Document Types

Visible to HR managers only. Each type carries two settings that decide when
reminders fire:

| Field | Meaning |
|---|---|
| **Name** | What the type is called, e.g. `Work permit`. Must be unique. |
| **Chasing Pattern** | One of the four patterns in [section 5](#5-the-chasing-patterns-with-worked-examples). |
| **Reminder Days** | The *N* used by the pattern. Hidden and ignored for *On the expiry date only*; must be greater than zero for the other three. |
| **Active** | Uncheck to archive a type you no longer issue. Existing documents keep it. |

The demo data ships six types covering all four patterns:
`Work permit` (60 days, once before expiry), `First-aid certificate` (14 days,
once before expiry), `Driving licence` (21 days, daily before),
`Forklift certificate` (7 days, daily after), `Residence permit` (on expiry
only) and `Professional licence` (30 days, once before expiry).

### 3.2 The scheduled action

**Settings → Technical → Scheduled Actions → Employee Documents: expire and
chase**. It runs once a day and calls
`odomate.hr.document._cron_process_documents()`. You can change the interval or
run it manually from that screen; running it twice in one day will not send a
second email, because each document stamps the date of its last automatic
reminder.

## 4. Daily use

### 4.1 Recording a document

**Employees → Employee Documents → Documents → New**.

Fill in the employee, the document type, the issue date and the expiry date,
then drag the scan into the chatter's attachment area at the bottom of the
form. The **Reference** (`EMPDOC/00001`, `EMPDOC/00002`, …) is assigned
automatically and cannot be edited.

The record starts in **Draft**. A draft is deliberately inert: it is not chased,
not expired, and does not block a second document of the same type. Use drafts
for documents you are still waiting on.

Press **Mark Valid** when the paperwork is in hand. Two rules apply:

- If the expiry date is *strictly before* today, the transition is refused with
  an error telling you to use **Renew** instead. An expiry date of exactly
  today is accepted.
- An employee may hold only **one Valid document per document type**. A second
  one is refused, on create and on write, and the same rule is enforced by a
  partial unique index in the database, so two simultaneous imports cannot slip
  a duplicate through.

Draft and Expired copies of the same type may coexist freely — only *Valid* is
exclusive.

### 4.2 Finding what needs attention

The **Documents** list colours expired rows red and bold, and greys out drafts,
so a problem is visible without reading a single date. The **Days Remaining**
column spells out the distance in words: `Expired 12 days`, `Today`,
`Tomorrow`, or a plain number such as `43`.

Filters: **Valid**, **Expired**, **Draft**, **Expiring within 7 days**,
**Expiring within 30 days**. Group by **Employee**, **Document Type**,
**Status** or **Expiry Month**.

The two "expiring within" filters are translated into a plain date range on
`date_expiry` behind the scenes, so they stay correct without any stored
day-counter that could go stale overnight.

### 4.3 The employee's own view

Every internal user sees the **Documents** menu and finds their own documents
there, read-only. They cannot see a colleague's document — not through the
list, and not by opening its address directly.

### 4.4 From the employee form

The employee form carries a **Documents** smart button (HR officers and above)
showing the count and opening that person's documents, with the employee
pre-filled on the New button.

### 4.5 Chasing by hand

**Send Reminder Now** on the document form sends the reminder email and
creates or refreshes the manager's To-Do immediately, whatever the chasing
pattern says. It also stamps today's date, so that evening's scheduled run
will not send a duplicate — but tomorrow's run is unaffected. The button is
refused on a draft.

## 5. The chasing patterns, with worked examples

All four compare **today** with the document's **expiry date**. Assume a
document expiring on **15 June** with **Reminder Days = 5**.

| Pattern | Fires when | For our example |
|---|---|---|
| **On the expiry date only** | today = expiry | 15 June only. `Reminder Days` is ignored. |
| **Once, N days before expiry** | today = expiry − N | 10 June only. Nothing on 11–15 June. |
| **Every day from N days before expiry until expiry** | expiry − N ≤ today ≤ expiry | 10, 11, 12, 13, 14 and 15 June — six sends. |
| **Every day from expiry until N days after expiry** | expiry ≤ today ≤ expiry + N | 15, 16, 17, 18, 19 and 20 June — six sends. |

Each fire does two things:

1. **Email to the employee**, using the *Employee Document: Expiry Reminder*
   template, addressed to the work email (falling back to the private email).
   No email address on file means no email — the run does not fail.
2. **A To-Do activity on the manager** (`employee_id.parent_id.user_id`), dated
   on the document's expiry date. If a To-Do from a previous run is still open,
   its deadline and summary are refreshed rather than a second one created. An
   employee with no manager on file gets the email only.

`Last Reminder Sent` (visible with developer mode on) is what stops a second
automatic send on the same calendar day. It never suppresses the *next* day's
send in a daily pattern.

## 6. Renewing a document

**Renew** is available on Valid and Expired documents — not on drafts.

The wizard asks for exactly four things: the new issue date, the new expiry
date, one or more new scans, and a reason. It refuses to continue if:

- no scan is attached,
- the new expiry date is not strictly in the future, or
- the new expiry date is not strictly after the new issue date.

On success, in one step:

- the document's **current** issue and expiry dates are copied into a new
  **Renewal History** row, together with who renewed it, when, and why;
- the scans that were on the document are **re-pointed** to that history row —
  the same `ir.attachment` records, moved, not copied, so nothing is duplicated
  and nothing is lost;
- the new scans are attached to the document;
- the document takes the new dates and returns to **Valid**;
- a chatter note records `old expiry → new expiry` and the reason;
- any open manager To-Do is marked done with a completion note.

The **Renewals** smart button and the *Renewal History* page on the form show
every past cycle: renewal date, who did it, the superseded issue and expiry
dates, the reason, and how many superseded scans that row holds. History rows
are read-only in the interface — they are only ever written by the wizard.

**Set to Draft** (Valid or Expired → Draft) also closes any open manager To-Do,
because the expiry date that To-Do was chasing no longer applies once the
document is back to unverified.

## 7. Who can see and do what

| | Documents | Renewal History | Document Types | Forms & Templates |
|---|---|---|---|---|
| Internal user (`base.group_user`) | read own only | read own only | read | read |
| HR Officer (`hr.group_hr_user`) | read / write / create, all employees | read, all | read | read / write / create |
| HR Manager (`hr.group_hr_manager`) | + delete | + delete | full | + delete |

Menu visibility: **Documents** and **Forms & Templates** are visible to every
internal user; **Document Types** only to HR managers. The action buttons
(**Mark Valid**, **Renew**, **Send Reminder Now**, **Set to Draft**) are
hidden — not merely blocked — for users below HR Officer.

An internal user's read access is narrowed by a record rule to
`employee_id.user_id = user.id`. Renewal history is narrowed the same way
through `document_id.employee_id.user_id`.

A global multi-company rule
(`['|', ('company_id','=',False), ('company_id','in', company_ids)]`) applies to
documents and to renewal history for everyone, including HR managers.
`company_id` is derived from the employee, so it always matches the holder.

## 8. Forms & Templates

**Employees → Employee Documents → Forms & Templates** holds blank paperwork
every employee can download: an expense claim form, a change-of-address
notification, an equipment loan agreement. Name, a note explaining when to use
it, and the file itself in the chatter. No dates, no status, no expiry chasing.

Everyone can read them; HR officers create and edit; HR managers delete.

## 9. Reference: models and fields

### `odomate.hr.document.type`

`name`, `reminder_days`, `chasing_pattern`
(`on_expiry` / `before_expiry` / `daily_before` / `daily_after`), `active`.
Shared across all companies — one list for the whole database.

### `odomate.hr.document`

`reference`, `employee_id`, `document_type_id`, `description`, `date_issued`,
`date_expiry`, `state` (`draft` / `valid` / `expired`), `company_id` (related
from the employee, stored), `days_remaining_label` (computed and searchable),
`last_reminder_sent_date`, `history_ids`, `history_count`.
Inherits `mail.thread` and `mail.activity.mixin`.

### `odomate.hr.document.history`

`document_id`, `employee_id`, `date_issued`, `date_expiry`, `renewed_by`,
`renewed_date`, `reason`, `company_id`, `attachment_count`.

### `odomate.hr.form.template`

`name`, `note`, `active`. Inherits `mail.thread`.

### `odomate.hr.document.renew` (wizard)

`document_id`, `new_date_issued`, `new_date_expiry`, `new_attachment_ids`,
`reason`.

## 10. Limitations

Deliberately out of scope — do not expect these:

- **No approval workflow.** Marking a document valid is a single action by an
  HR officer; nobody countersigns it.
- **No blocking.** An expired document does not stop scheduling, payroll or
  leave. It raises a flag; acting on it is a human decision.
- **No employee self-service.** Employees can read their own documents but
  cannot upload a scan or start a renewal — HR does both.
- **No OCR.** Scans are stored as attachments; no data is extracted from them,
  so expiry dates are always typed in by hand.
- **No escalation ladder.** One email to the employee plus one To-Do for the
  direct manager. Nothing goes further up if both are ignored.
- **No printable report.** There is no PDF of the document register.
- **The standard `hr` fields are left alone.** `identification_id`,
  `passport_id` and `work_permit_expiration_date` on `hr.employee` are not read,
  written or superseded by this module — a document recorded here is a separate
  record from those fields, by design.
- **The daily pattern volume is real.** *Every day from expiry until N days
  after expiry* with `Reminder Days = 30` means thirty emails. Choose the
  reminder delay accordingly.
- **Reminders depend on the scheduled action running.** If the Odoo cron is
  disabled, nothing expires and nothing is chased.
