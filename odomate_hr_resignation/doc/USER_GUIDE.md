# OdoMate HR Resignation & Clearance — User Guide

Resignation and exit clearance tracking for the Odoo 19 **Employees** app,
gated on outstanding company property read live from `odomate_hr_custody`.

## Table of contents

1. [What this module does](#1-what-this-module-does)
2. [Installation](#2-installation)
3. [Configuration](#3-configuration)
4. [The resignation workflow](#4-the-resignation-workflow)
5. [The exit clearance checklist](#5-the-exit-clearance-checklist)
6. [Releasing an employee](#6-releasing-an-employee)
7. [Exit interview](#7-exit-interview)
8. [Who can see and do what](#8-who-can-see-and-do-what)
9. [The daily scheduled action](#9-the-daily-scheduled-action)
10. [Field reference](#10-field-reference)
11. [Limitations](#11-limitations)

---

## 1. What this module does

It adds three configurable records to the Employees app:

| Model | Purpose |
|---|---|
| `odomate.hr.resignation` | One resignation per employee, from notice to release |
| `odomate.hr.clearance.item` | The reusable checklist entries (IT Accounts, Finance, …) |
| `odomate.hr.resignation.clearance.line` | One checklist entry attached to one resignation |

The single idea that shapes the whole module: **an employee is not released
while the custody register still shows company property in their hands.** That
register (`odomate.hr.custody`) is read, never written — this module never
marks anything as returned.

## 2. Installation

`odomate_hr_custody` is a hard dependency. The module also pulls in `hr`,
`mail` and `survey`. Install from **Apps → Update Apps List → OdoMate HR
Resignation & Clearance**.

No new security groups are created. The module reuses `hr.group_hr_user`
(HR Officer) and `hr.group_hr_manager` (HR Manager), so anyone who already
administers Employees can use it the moment it installs.

## 3. Configuration

### 3.1 Manager approval

**Settings → Employees → Resignation & Clearance → Manager Approval on
Resignations** (field `resignation_manager_approval_required`, per company,
**on by default**).

- **On** — a confirmed resignation waits for the employee's manager
  (`employee_id.parent_id.user_id`) before HR opens the clearance.
- **Off** — HR approval moves the record straight from `confirmed` to
  `clearance`; the `manager_approved` step is skipped entirely.

### 3.2 Clearance items

**Employees → Configuration → Clearance Items** (HR Manager only).

Five starter items ship with the module and are available to **every**
company because their Company field is left empty:

| Sequence | Name |
|---|---|
| 10 | IT Accounts |
| 20 | Company Property |
| 30 | Handover Notes |
| 40 | Finance |
| 50 | Keys & Passes |

They are ordinary records — rename, reorder, archive or delete them. Nothing
in the code depends on them existing, with one exception noted in
[section 5](#5-the-exit-clearance-checklist).

Set **Default Responsible** to route an item to a specific user. Leave it
empty and the line falls back to the HR user who approved the resignation.
Leave **Company** empty to share the item across companies; set it to pin the
item to one company.

## 4. The resignation workflow

**Employees → Resignations**. The list opens filtered to `In Progress`
(draft / confirmed / manager approved / clearance). The `Released`, `Refused`
and `Withdrawn` filters are one click away — nothing is hidden permanently.

```
draft → confirmed → manager_approved → clearance → released
             ↘ refused        ↘ withdrawn (any time before released)
```

### 4.1 Draft

Pick the **Employee**; Department and Job Position fill in automatically.
Enter the **Notification Date**, the **Reason** and the **Departure Reason**
(the standard `hr.departure.reason` records — no parallel list is introduced).

**Notice Period (Days)** is read from the employee's current `hr.version`
record at this moment and stored on the resignation. **Proposed Last Working
Day** = Notification Date + Notice Period.

> **Worked example.** Rita gives notice on 8 September 2026. Her current
> version carries a 30-day notice period, so Proposed Last Working Day is
> **8 October 2026**, and Last Working Day is set to the same date.
>
> HR later negotiates 20 October and types it into **Last Working Day**. From
> that instant the record is flagged as manually set. If the Notification Date
> is afterwards corrected to 10 September, Proposed Last Working Day moves to
> 10 October — but Last Working Day stays at **20 October**. There is no
> value-comparison guessing: one boolean, set the moment a human writes the
> field.

### 4.2 Confirm

**Confirm** moves the record to `confirmed` and raises a To-Do activity. If
manager approval is required for the company and the employee has a manager
with a user account, the activity goes to that manager
("Approve the resignation of Rita Resigner"). Otherwise it goes straight to
the HR responsible.

### 4.3 Manager Approve

Visible while the record is `confirmed`. It can be run by the employee's own
manager or by any HR officer. It closes the pending approval activity, moves
to `manager_approved`, and raises a new activity on HR
("Start the exit clearance for …").

### 4.4 Approve (HR)

Available to HR from either `confirmed` or `manager_approved`. It fixes the
Last Working Day if it is still empty, builds the clearance checklist, and
moves the record to `clearance`. See the next section.

### 4.5 Refuse and Withdraw

**Refuse** (HR, before HR approval) opens a small wizard that demands a
reason. On confirm it cancels every open approval activity, stores the text in
**Refusal Reason** and sets the state to `refused`.

**Withdraw** is available to anyone who can see the record, at any point
before `released`. It cancels open activities and sets `withdrawn`. It leaves
the employee record completely untouched — no departure date, no archiving.

Both are terminal. Because the uniqueness rule only counts resignations that
are neither refused nor withdrawn, a refused or withdrawn record frees the
employee to have a new one recorded.

## 5. The exit clearance checklist

HR approval builds one line per active clearance item visible to the
resignation's company (its own items **plus** the global blank-company ones),
in sequence order. Each line gets a To-Do activity on its responsible user.

### 5.1 The property snapshot line

If the custody register shows anything `approved` for this employee at the
moment of HR approval, **one additional line** is created in the `blocked`
state on the *Company Property* item. Its remark names every outstanding
item, its handover reference and its due date:

```
Company property still registered to this employee when HR approved
the resignation:
- Projector (handover HO/2026/0007, due 2026-09-18)
```

This is a **snapshot**. It is deliberately not refreshed. The authoritative
check happens again at release time (section 6), and the two are allowed to
disagree — that disagreement is the signal that something changed after
approval.

If no company property is outstanding, no such line is created at all.

If the *Company Property* item has been deleted and no clearance items exist
at all, the snapshot line cannot be created; the module posts a note in the
chatter saying so. The live release check is unaffected.

### 5.2 Working the checklist

Blocked lines are shown with a red badge and a red row in the embedded list,
so they stand out from ordinary pending work. Above the list, a progress bar
shows cleared lines ÷ total lines.

The responsible user can open their own line (from the activity in their
inbox) and use **Mark as Cleared**, **Mark as Blocked** (a remark is
mandatory) or **Reset to Pending**. HR officers can do the same on any line.
Nobody else can, even if they somehow reach the record.

## 6. Releasing an employee

**Release** appears on a record in `clearance` for HR officers. It is a
single, all-or-nothing step, blocked by two independent checks with distinctly
worded messages:

1. **Live custody re-read.** `odomate.hr.custody` is queried again for
   `state = approved`. If anything comes back, the error names each item, its
   handover reference and its due date. This ignores the snapshot line — the
   live read wins.
2. **Checklist completeness.** Any line not in `cleared` blocks the release,
   and the error lists each open entry with its status and responsible user.

When both pass, in one transaction:

- `departure_date`, `departure_reason_id` and `departure_description` are
  written on the employee (which stores them on the current `hr.version`),
- the current version's `contract_date_end` is set to the release date,
- the employee is archived,
- the linked login (`res.users`) is archived — this is the only place the
  module elevates privileges, and it does so for that single write.

Afterwards the record is **immutable in code, not merely read-only in the
view**: `write()` rejects changes to the dates, the reason, the departure
reason and the checklist, on the resignation and on its clearance lines alike.

## 7. Exit interview

The **Exit Interview** tab holds the survey picker plus **Exit Interview
Sent** and **Exit Interview Answered** indicators. From `manager_approved`
onward, **Send Exit Interview** opens the standard `survey.invite` wizard
pre-filled with the chosen survey and the employee's contact.

The answer is located by matching the selected survey against the employee's
partner, so **Open Answer** works even if the invitation was sent from the
Surveys app rather than from here.

## 8. Who can see and do what

| Role | Resignations | Clearance items | Clearance lines |
|---|---|---|---|
| HR Officer (`hr.group_hr_user`) | read / write / create, all state transitions | read only | read / write / create |
| HR Manager (`hr.group_hr_manager`) | the above **+ delete** | full configuration | the above **+ delete** |
| The resigning employee's own manager | read / write **that one record only** | read only | — |
| Any other internal user | **nothing** | read only | only lines they are responsible for |

There is **no menu entry** for resignations outside HR. A manager reaches the
one record they are entitled to through the approval activity in their inbox;
the record rule `[('employee_id.parent_id.user_id', '=', user.id)]` means every
other ordinary user matches zero rows.

Responsible users reach their clearance line the same way. The clearance-line
form deliberately shows only the employee name, the item, the status and the
remark — no field on it walks back into the parent resignation, so a
responsible user never needs (nor gets) access to the rest of the file.

All three models carry multi-company record rules. Clearance items use the
standard optional-company domain, so blank-company items are visible
everywhere.

The module ships **zero** `res.groups` and `res.users` records.

## 9. The daily scheduled action

**Settings → Technical → Scheduled Actions → "Resignation: release cleared
employees"** runs once a day. It picks up resignations in `clearance` whose
Last Working Day has arrived or passed, and runs the **exact same two checks**
as the Release button — the same method, no elevated bypass. Records that
still have outstanding property or open checklist entries are skipped and
retried the next day.

Activities are raised on state transitions only. The cron never re-notifies
about a condition that simply persists.

## 10. Field reference

### `odomate.hr.resignation`

| Field | Type | Notes |
|---|---|---|
| `name` | Char | `RES/2026/0001`, from the `odomate.hr.resignation` sequence |
| `employee_id` | Many2one | required, editable in draft only |
| `department_id`, `job_id` | Many2one | related to the employee, stored for list and search |
| `date_notified` | Date | required, defaults to today |
| `notice_period_days` | Integer | computed + stored from `employee_id.version_id.notice_period` |
| `proposed_last_working_day` | Date | computed + stored, `date_notified + notice_period_days` |
| `last_working_day` | Date | editable; mirrors the proposal until edited |
| `last_working_day_manual` | Boolean | technical; `True` the instant a human writes the field |
| `reason` | Text | required |
| `departure_reason_id` | Many2one | required, standard `hr.departure.reason` |
| `state` | Selection | draft / confirmed / manager_approved / clearance / released / refused / withdrawn |
| `outstanding_property_count` | Integer | computed, **not stored** — live custody count |
| `clearance_progress` | Float | computed, not stored — cleared ÷ total, as a percentage |

### `odomate.hr.resignation.clearance.line`

| Field | Type | Notes |
|---|---|---|
| `clearance_item_id` | Many2one | required |
| `employee_id`, `company_id` | Many2one | related to the resignation, stored |
| `responsible_user_id` | Many2one | required; from the item, else the approving HR user |
| `state` | Selection | pending / cleared / blocked |
| `remark` | Text | mandatory before a line can be marked blocked |

## 11. Limitations

Honest scope notes for v1:

- **No "reset to proposed" action.** Once Last Working Day is set by hand it
  stays that way. Clearing `last_working_day_manual` requires a developer or
  the Odoo shell.
- **The custody register is read-only here.** Releasing an employee does not
  mark their custody records returned; somebody must do that in
  `odomate_hr_custody` first, or the release stays blocked. That is deliberate.
- **User archiving is skipped in two cases** — when the linked login is the
  Odoo superuser, or when it is the very user pressing Release. Odoo forbids
  both writes; everything else in the release still completes.
- **No contract end date without a contract start date.** `hr.version` has a
  database check constraint that forbids it, so when the current version has
  no start date the module skips that write and posts a chatter note instead.
- **Demo resignations are attached at load time**, not by static XML ID,
  because demo employee XML IDs differ between Odoo builds. They bind to
  whichever demo employees the database actually has, with the property-blocked
  line copied from the live custody demo record.
- **Clearance item names are plain `Char` fields.** Following Odoo 19 guidance
  they are not marked `translate=True` (that switches storage to JSONB and
  causes display bugs), so the Ukrainian entries for the five starter names in
  `i18n/uk.po` are record names, not field labels, and only ever show in
  Ukrainian if that specific record's `name` value itself is translated by an
  administrator — the shipped `.po` entry is a reference translation, not a
  live one.
- **Ukrainian (`uk`) is the only shipped language pack.** On an install with
  language `uk_UA`, every field label, both menu items (**Resignations** and
  **Clearance Items**), all seven resignation states, all three clearance-line
  states, every button and every validation/activity message raised from
  Python render in Ukrainian. There is no `.pot` template shipped in the
  module — only the finished `i18n/uk.po` — so translators extending this to
  another language should generate a fresh template from **Settings →
  Translations → Export Translations** rather than looking for one on disk.
- **Out of scope entirely:** settlement, payslips, dismissal workflows, a
  handover-task model, exit-interview reporting, employee self-service and
  document generation.

---

*OdoMate — https://odomate.pro — support@odomate.pro*
