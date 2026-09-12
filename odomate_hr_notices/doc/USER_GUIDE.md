# HR Notices, Announcements & Acknowledgements — User Guide

Module: `odomate_hr_notices` · Odoo 19.0 · Version 19.0.1.0.0

## Table of contents

1. [What this module does](#1-what-this-module-does)
2. [Installation](#2-installation)
3. [Roles and access](#3-roles-and-access)
4. [Configuration](#4-configuration)
5. [Publishing an announcement](#5-publishing-an-announcement)
6. [Acknowledgement tracking](#6-acknowledgement-tracking)
7. [Audience rules](#7-audience-rules)
8. [Date reminders](#8-date-reminders)
9. [The systray counter](#9-the-systray-counter)
10. [Automatic expiry](#10-automatic-expiry)
11. [Field reference](#11-field-reference)
12. [Limitations](#12-limitations)

## 1. What this module does

HR publishes announcements to a chosen audience. Employees see only the
announcements addressed to them, and only while those announcements are
published and inside their display window. Employees can press
**Acknowledge**, and HR can see exactly who has and has not pressed it.

Separately, HR can save **date reminders** — a saved question such as
"which work permits expire in the next 30 days" — and see a live count of
matching records.

## 2. Installation

1. Copy `odomate_hr_notices` into your Odoo addons path.
2. Activate developer mode, then **Apps → Update Apps List**.
3. Search for *HR Notices* and click **Install**.

The module depends on `base`, `mail` and `hr`. Odoo installs any missing
dependency automatically.

## 3. Roles and access

The module invents no new security groups. It reuses three standard ones:

| Group | Announcements | Categories | Reminders |
|---|---|---|---|
| `base.group_user` (every internal user) | Read only, and only published, in-window announcements addressed to them | Read only | **No access at all** |
| `hr.group_hr_user` (HR Officer) | Read, write, create; send for approval; refuse | Read, write, create | Read, write, create |
| `hr.group_hr_manager` (HR Administrator) | Everything above, plus **Publish** and delete | Full | Full |

Two protections are worth calling out:

- **Publishing is checked in the method**, not just hidden in the view. An HR
  Officer who calls `action_publish` directly gets an `AccessError`.
- The acknowledgement fields (`acknowledged_employee_ids`,
  `acknowledged_count`, `audience_count`, `pending_employee_ids`) carry
  `groups='hr.group_hr_user'` **on the field itself**, so a non-HR user
  cannot read them even through a direct ORM call.

Employees never get write access to announcements. Acknowledgement happens
through the **Acknowledge** button, which performs one narrowly-scoped
privileged write and nothing else.

## 4. Configuration

**Employees → Configuration → Announcement Categories**

Create the categories you want to sort announcements by. The demo data ships
four: Policy, Safety, Social and Benefits. Each category has a colour used by
the colour picker. Deleting a category never deletes announcements — the
announcement's **Category** field is simply emptied (`ondelete='set null'`).

## 5. Publishing an announcement

**Employees → Notices → All Announcements → New**

1. Fill in **Title**, pick a **Category** and a **Priority** (Low / Normal /
   High / Urgent, shown as the standard star widget).
2. Set **Display From** and **Display Until**. A start date in the past is
   allowed — you can correct yesterday's announcement.
3. Choose the **Audience** (see section 7). The form reveals only the field
   that matches your choice.
4. Write the announcement body.
5. Click **Send for Approval**. The status moves to *Waiting for Approval*
   and a To-Do activity is scheduled for an HR Administrator.
6. An HR Administrator clicks **Publish** — or **Refuse**, which asks for a
   mandatory reason. The reason is stored in **Refusal Reason** and posted to
   the chatter.

The status bar shows Draft → Waiting for Approval → Published, with Refused
and Expired as side branches. No transition skips a step: you cannot publish
a draft directly.

A reference such as `NOTICE/00001` is assigned automatically on creation.

## 6. Acknowledgement tracking

An employee opening a published announcement sees an **Acknowledge** button.
Pressing it is idempotent — pressing it twice records one acknowledgement.
The button disappears once pressed.

HR sees an **Acknowledgements** tab with:

- **Acknowledged** — how many people pressed the button.
- **Audience Size** — how many people the announcement is addressed to.
- **Has Not Acknowledged** — the difference, as a list of employees.

> **Acknowledged is not "read and understood."** It is a record of a button
> press, nothing more. This wording appears in the module's own UI help text
> as well as here.

Worked example: an announcement addressed to a department of 12 people, of
whom 5 have pressed the button, shows Acknowledged = 5, Audience Size = 12,
and 7 names under Has Not Acknowledged.

## 7. Audience rules

One method resolves audience membership, and the record rule, the systray,
the employee smart button and the has-not-acknowledged list all reuse it.

| Audience | Who it resolves to |
|---|---|
| **Everyone** | Every *active* employee of the announcement's own company, resolved at read time — someone hired after publication is included |
| **Selected Employees** | Exactly the employees listed in **Employees** |
| **Selected Departments** | Employees whose department is exactly one of the listed departments — **there is no sub-department walk** |
| **Selected Job Positions** | Employees whose job position is one of the listed ones |

A user with no employee record at all still sees **Everyone** announcements
for their own company, and nothing else. It never raises an error.

**The visibility gate is identical everywhere.** Outside HR, an announcement
is visible only when its status is *Published* **and** today falls between
Display From and Display Until. Not to its own audience, not to an HR Officer
who happened to write it — the record rule enforces it for everyone in
`base.group_user`.

## 8. Date reminders

**Employees → Configuration → Date Reminders**

A reminder answers a date question and nothing else. It never filters on an
amount, a state or a status.

1. **Model** — limited to a whitelist: `hr.employee`, `hr.version`,
   `hr.applicant`, `hr.leave`. Models that are not installed are filtered out
   of the list, so a missing `hr_recruitment` cannot break the form.
2. **Date Field** — only fields of type `date` or `datetime` on that model.
3. **Time Window** — one of:
   - *Today* — the field value is today.
   - *Within the next N days* — between today and today + N.
   - *Between two dates* — between the fixed **From** and **To** dates.

The **Matching** stat button shows the live count and opens the matching
records. Both the count and the button use the same domain builder, and both
run **as you** — you never see records you have no right to read.

Worked example: Model `hr.employee`, Date Field `work_permit_expiration_date`,
window *Within the next N days* with N = 30, evaluated on 9 September 2026,
counts employees whose permit expires between 2026-09-09 and 2026-10-09.

## 9. The systray counter

A bullhorn icon in the top bar shows how many published, in-window
announcements are addressed to you that you have **not** acknowledged. Open
it to see the list, plus — for HR users only — any saved reminder with a
non-zero count. Clicking an entry opens the record.

The counter refreshes when the page loads and each time you open the
dropdown. There is no polling and no background traffic.

Everything reachable from the systray is also reachable from the menus. The
module works completely with `static/src` deleted.

## 10. Automatic expiry

A daily scheduled action, **HR Notices: Expire Published Announcements**,
moves published announcements whose Display Until has passed to *Expired*.
It touches nothing in Draft, Waiting for Approval, Refused or already
Expired, and has no other side effects — no mail, no activity, no change to
acknowledgements.

Expired announcements stay fully visible in HR's records and disappear from
employees' lists.

## 11. Field reference

### `odomate.hr.announcement`

| Field | Type | Notes |
|---|---|---|
| `reference` | Char | `NOTICE/00001`, from `ir.sequence`, read-only |
| `title` | Char | Required |
| `body` | Html | The announcement text |
| `category_id` | Many2one | `ondelete='set null'` |
| `priority` | Selection | `0` Low, `1` Normal, `2` High, `3` Urgent |
| `date_start` / `date_end` | Date | Required; `date_start <= date_end` enforced by a DB constraint |
| `state` | Selection | draft / to_approve / published / refused / expired, tracked |
| `audience` | Selection | all / employee / department / job |
| `employee_ids`, `department_ids`, `job_ids` | Many2many | Audience targets, restricted to the announcement's company |
| `acknowledged_employee_ids` | Many2many | HR-only field |
| `acknowledged_count`, `audience_count` | Integer | Computed, HR-only |
| `pending_employee_ids` | Many2many | Computed, HR-only |
| `is_acknowledged_by_me` | Boolean | Computed per user; drives the Acknowledge button |
| `is_for_me` | Boolean | Computed + searchable; backs the record rule |
| `company_id` | Many2one | Required |
| `refuse_reason` | Text | Set only by the refusal wizard |

### `odomate.hr.reminder`

| Field | Type | Notes |
|---|---|---|
| `name` | Char | Required |
| `model_id` | Many2one | Whitelisted models only |
| `field_id` | Many2one | Date/datetime fields of that model |
| `window` | Selection | today / days_ahead / period |
| `days_ahead` | Integer | Used when window = days_ahead |
| `date_from`, `date_to` | Date | Used when window = period |
| `preview_count` | Integer | Computed, never stored, always evaluated as you |

### `hr.employee` (extension)

| Field | Type | Notes |
|---|---|---|
| `notice_count` | Integer | Every currently published, in-window announcement addressed to this employee, **regardless of acknowledgement** — deliberately different from the systray count |

## 12. Limitations

- **Acknowledged means "pressed the button."** It is not evidence that the
  person read or understood anything, and should not be used as one.
- **Departments do not cascade.** An announcement sent to a parent department
  does not reach its sub-departments. Add each department explicitly.
- **Reminders answer date questions only.** There is no way to add an amount,
  state or status condition to a reminder.
- **Reminder time zones.** For `datetime` fields the day boundaries are
  computed as plain 00:00:00–23:59:59 without a per-user time-zone shift, the
  same convention Odoo's own date filters use. Records within a few hours of
  midnight may fall on either side of a boundary for users far from the
  server's time zone.
- **The systray does not live-update.** It refreshes on page load and on
  dropdown open; there is no bus or websocket subscription.
- **Non-admin verification is out of scope for OdoMate's test environment**,
  which has no least-privileged account. The employee-visibility, acknowledge
  and HR-officer-cannot-publish paths are covered by automated tests, but
  should also be confirmed on your own install with a real non-HR user.
