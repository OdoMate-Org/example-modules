# OdoMate HR Overview Dashboard — User Guide

**Technical name:** `odomate_hr_dashboard` · **Version:** 19.0.1.0.2 · **License:** LGPL-3

## Table of contents

1. [What this module does](#1-what-this-module-does)
2. [Installation](#2-installation)
3. [Access rights](#3-access-rights)
4. [The HR Overview screen](#4-the-hr-overview-screen)
5. [How each figure is calculated](#5-how-each-figure-is-calculated)
6. [Joiners and leavers analysis](#6-joiners-and-leavers-analysis)
7. [Absence by employee (Bradford factor)](#7-absence-by-employee-bradford-factor)
8. [Pending approvals from the wider HR suite](#8-pending-approvals-from-the-wider-hr-suite)
9. [Multi-company behaviour](#9-multi-company-behaviour)
10. [Field reference](#10-field-reference)
11. [Limitations](#11-limitations)

---

## 1. What this module does

`odomate_hr_dashboard` is a **read-only** management overview for Odoo 19
Employees. It adds:

* one OWL client action — **HR Overview** — with five clickable figure tiles;
* two SQL-view analysis models — `odomate.hr.movement` (arrivals and
  departures) and `odomate.hr.absence.factor` (absence concentration);
* four entry points into the underlying lists.

The module **creates no records**, **grants no security group to anybody**, and
uses **no `sudo()` anywhere**. Every figure you see is computed with your own
permissions, so two people opening the same screen can legitimately see
different numbers.

## 2. Installation

1. Copy the `odomate_hr_dashboard` folder into your addons path.
2. **Apps → Update Apps List**.
3. Search for *OdoMate HR Overview Dashboard* and click **Install**.

Dependencies (`hr`, `hr_holidays`, `web`) are installed automatically if they
are not present yet. The module ships **no demo data** — it reports on the
employees and time off that already exist in your database.

**Language.** If your Odoo instance has the Ukrainian language pack loaded,
every server-side string this module produces — the turnover definition and
worked-arithmetic sentence, the five pending-approval labels, and the
drill-down action names — renders in Ukrainian for users on that language,
alongside the already-translated field labels and menu entries.

## 3. Access rights

| Group | Can open HR Overview | Can read the two analysis models |
|---|---|---|
| `hr.group_hr_user` (Officer) | Yes | Yes, read-only |
| `hr.group_hr_manager` (Manager) | Yes | Yes, read-only |
| `base.group_user` (plain internal user) | No | No |

A plain internal user gets **no menu entry**, and cannot reach the data by
typing the action's address either: `get_overview()` raises an access error
before touching a single record.

The module contains no `res.groups` or `res.users` records. Whoever already
holds `hr.group_hr_user` in your database can use it the moment it installs.

## 4. The HR Overview screen

Menu: **Employees → HR Overview**

```
┌─────────────────────────────────────────────────────────────────────┐
│ HR Overview                              From [2026-01-01]  To [2026-12-31] │
├──────────┬──────────┬──────────┬──────────────┬─────────────────────┤
│ HEADCOUNT│  JOINED  │   LEFT   │  OFF TODAY   │      TURNOVER       │
│   122    │    14    │     2    │      3       │        1.6%         │
│as of today│2026-01-01│2026-01-01│ as of today  │ 2026-01-01 to ...   │
│          │to 2026-…│to 2026-… │              │                     │
└──────────┴──────────┴──────────┴──────────────┴─────────────────────┘
```

* The **period selector** is two plain date inputs. Changing either one
  re-runs the single server call and re-renders every figure.
* The default period is the **current calendar year**.
* **Headcount** and **Off today** are point-in-time figures. They ignore the
  period selector entirely and their caption says *as of today* so you are
  never misled.
* **Joined**, **Left** and **Turnover** are period-driven. Their captions name
  the dates you actually picked.
* Every tile is clickable. **The row count of the list that opens always equals
  the number on the tile** — the count and the drill-down are built from the
  same domain, in the same server call.

Below the tiles are four entry points:

| Entry point | Opens |
|---|---|
| Joiners and leavers | `odomate.hr.movement`, unfiltered |
| Absence by employee | `odomate.hr.absence.factor`, unfiltered |
| Headcount by department | The native Odoo Departments kanban |
| Waiting for approval | Toggles the pending-approvals panel |

## 5. How each figure is calculated

### Headcount

Active employees of the companies you currently have selected, right now.
Archived employees are excluded. Drill-down: `hr.employee`, list view.

### Joined / Left

Rows of `odomate.hr.movement` whose `date` falls inside the selected period,
with `direction = join` or `direction = leave`. Both drill-downs open with
`active_test = False`, because a leaver is normally archived on `hr.employee`.

### Off today

`hr.leave` records in state **Approved** (`validate`) that cover today —
`date_from` on or before end of today and `date_to` on or after start of today.
Not period-bound.

### Turnover

```
turnover = departures in the period / average headcount over the period
average headcount = (headcount at date_from + headcount at date_to) / 2
```

Headcount at a date is derived from the movement view: joins dated on or before
that date, minus departures dated on or before that date.

**Worked example.** A company with 122 people on 1 January and 121 on
31 December, with 2 departures during the year:

```
average headcount = (122 + 121) / 2 = 121.5
turnover          = 2 / 121.5 × 100  = 1.6%
```

The tile shows exactly that sentence:

> *2 departures / average headcount 121.5 (122 on 2026-01-01, 121 on 2026-12-31) = 1.6%*

The formula in prose (`turnover_definition`) and the worked numbers for your
call (`turnover_detail`) are both returned by the server, so the screen never
invents arithmetic of its own.

Clicking the Turnover tile opens the **departures** list — the numerator. The
denominator is shown as text on the tile, not as a second drill-down.

## 6. Joiners and leavers analysis

Menu: **Employees → HR Overview Analysis → Joiners and Leavers**

`odomate.hr.movement` is a SQL view with one row per arrival and per departure.

* An **arrival** is dated from the **earliest** `contract_date_start` across the
  employee's `hr.version` records. An employee with no contract start date
  anywhere is **not** a joiner and simply does not produce a row — the date is
  never guessed from the creation date or from today.
* A **departure** is dated from `hr.version.departure_date` and carries the
  departure reason.
* The **department** on each row is read from the version the row was built
  from, not from the employee record — so a leaver keeps the department they
  were actually in.
* Archived employees are included; the actions pass `active_test = False`.

Views: list, graph and pivot, with a search panel offering filters
(Joined, Left, This Year, Last 12 Months) and group-bys (Month, Direction,
Department, Departure Reason). **The menu opens the list unfiltered** —
narrowing is your job, exactly like Odoo's own analysis views.

## 7. Absence by employee (Bradford factor)

Menu: **Employees → HR Overview Analysis → Absence by Employee**

The Bradford factor weighs *frequency* far more heavily than *duration*, on the
premise that many short absences disrupt a team more than one long one:

```
Bradford factor = occurrences² × days
```

**Worked example.**

| Employee | Occurrences | Days | Factor |
|---|---|---|---|
| Employee A | 4 | 6 | 4² × 6 = **96** |
| Employee B | 1 | 10 | 1² × 10 = **10** |

Employee B was off *more* days, yet ranks *lower* — that is the point of the
measure. The list is sorted by factor, highest first.

**What counts.** Only `hr.leave` records where `state = validate` (Approved)
**and** `date_to` has already passed.

* A request still in **To Approve** (`confirm`) does not count.
* A request in **Second Approval** (`validate1`) does **not** count — it is not
  approved yet.
* An approved leave that starts next week does not count towards either figure.
* Employees with no qualifying absence do not appear at all (there is no
  zero row).

**Scope, stated once.** *Occurrences, days and the factor cover all approved,
finished time off, narrowed by whatever filter you apply.* There is no time
window baked into the view. The **This Year** and **Last 12 Months** filters
select *which employees* are listed, using their **Last Absence** date; the
figures on each row always cover that employee's whole approved, finished
history. This is deliberate — it keeps the ranking stable and comparable.

## 8. Pending approvals from the wider HR suite

The **Waiting for approval** panel counts records from five OdoMate HR modules.
None of them is a dependency of this module.

| Model | Counted when state is | Label |
|---|---|---|
| `odomate.hr.loan` | `submitted` | Loans to approve |
| `odomate.hr.salary.advance` | `submitted` | Salary advances to approve |
| `odomate.hr.resignation` | `confirmed`, `manager_approved` | Resignations to approve |
| `odomate.hr.transfer` | `to_approve` | Transfers to approve |
| `odomate.hr.announcement` | `to_approve` | Announcements to approve |

For each source the module checks, in order: is the model installed at all → do
*you* have read access to it → how many records match. If any check fails, the
source is skipped **silently** — no error, and no misleading zero row. A source
with a count of zero is also not shown.

## 9. Multi-company behaviour

Both analysis models carry a `company_id` and ship a record rule scoped to
`company_id in company_ids`. In addition, every server-side query in
`get_overview()` filters on `self.env.companies` — the companies you have
*selected* in the company switcher, not just your default company. Switching
companies changes every figure on the screen.

The movement view never emits a row without a company.

## 10. Field reference

### `odomate.hr.movement`

| Field | Type | Notes |
|---|---|---|
| `id` | Integer | `employee_id × 10 + 1` for arrivals, `× 10 + 2` for departures |
| `employee_id` | Many2one `hr.employee` | Includes archived employees |
| `department_id` | Many2one `hr.department` | From the version the row was built from |
| `company_id` | Many2one `res.company` | Never empty |
| `date` | Date | Arrival or departure date |
| `direction` | Selection | `join` / `leave` |
| `departure_reason_id` | Many2one `hr.departure.reason` | Departure rows only |

### `odomate.hr.absence.factor`

| Field | Type | Notes |
|---|---|---|
| `id` | Integer | The employee id |
| `employee_id` | Many2one `hr.employee` | |
| `department_id` | Many2one `hr.department` | From the employee's current version |
| `company_id` | Many2one `res.company` | |
| `occurrence_count` | Integer | Approved, finished absences |
| `day_count` | Float | Total days over the same absences |
| `bradford_factor` | Integer | occurrences² × days; not summable across rows |
| `last_absence_date` | Date | Drives the convenience filters |

### `odomate.hr.dashboard`

An abstract model with one method, `get_overview(date_from, date_to)`, returning
`headcount`, `joined`, `left`, `off_today`, `turnover_rate`,
`turnover_definition`, `turnover_detail`, `actions` and `pending`.

## 11. Limitations

Stated plainly, so nobody is surprised:

* **Read-only by design.** There is no way to correct a wrong figure from this
  screen; fix the underlying `hr.version` or `hr.leave` record instead.
* **Arrivals depend on `contract_date_start`.** Employees whose versions carry
  no contract start date never appear as joiners, and never count towards
  headcount-at-a-date, so they do not affect the turnover denominator either.
  If your data is thin here, turnover will read low.
* **Headcount-at-a-date is reconstructed from movements**, not from a historical
  snapshot. Retroactive edits to `contract_date_start` or `departure_date`
  change past figures.
* **The Bradford figures have no time window.** Filters select employees, not
  date ranges of leave. This is documented on every relevant field and in the
  list caption, but it does differ from tools that recompute the factor per
  period.
* **`validate1` is excluded on purpose.** If your leave types use two-step
  approval, absences sitting in Second Approval are invisible here until the
  second approval lands.
* **Off today uses UTC day boundaries.** In a database spread across far-apart
  time zones, an employee at the very edge of the day may be counted a few
  hours early or late.
* **No charting library.** The tiles are plain HTML and CSS; richer charts are
  the graph and pivot views on the two analysis models.
* **Pending approvals are counted, not filtered by company**, because the five
  source models are not dependencies and are not guaranteed to carry a
  `company_id`. Their own record rules apply.
