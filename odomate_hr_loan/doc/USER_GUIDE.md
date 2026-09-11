# Employee Loans — User Guide

`odomate_hr_loan` lets HR record loans granted to employees, build a fixed
repayment schedule at approval time, and recover the instalments
automatically from payslips through the OCA **payroll** module.

## Table of contents

1. [What this module does](#1-what-this-module-does)
2. [Installation](#2-installation)
3. [Required one-time setup](#3-required-one-time-setup)
4. [Configuration — Loan Policy](#4-configuration--loan-policy)
5. [Daily use](#5-daily-use)
6. [How the schedule is calculated](#6-how-the-schedule-is-calculated)
7. [Payslip recovery](#7-payslip-recovery)
8. [Deferring and settling](#8-deferring-and-settling)
9. [Access rights](#9-access-rights)
10. [Field reference](#10-field-reference)
11. [Limitations](#11-limitations)

---

## 1. What this module does

- Records a loan per employee with an amount, a purpose, a number of
  instalments and an optional flat interest rate.
- Builds a **repayment schedule** — one `odomate.hr.loan.instalment` row
  per instalment, with a due date, principal, interest and total.
- Moves the loan through `Draft → Submitted → Approved → Closed`, with
  `Refused` and `Cancelled` as terminal side branches.
- Adds one payslip input line per instalment falling due in the payslip
  period, and marks that instalment **Recovered** when the payslip is
  confirmed.
- Lets HR **defer** an instalment by one month or **settle** a loan early.

Two menus are added under **Employees**:

| Menu | Who sees it |
|---|---|
| **Employees → Loans → My Loans** | every internal user (own loans, read-only) |
| **Employees → Loans → Loan Requests** | HR Officers and HR Administrators |
| **Employees → Loans → Loan Policy** | HR Administrators only |

## 2. Installation

1. Copy `odomate_hr_loan` into your Odoo addons path.
2. **Apps → Update Apps List**.
3. Search for **Employee Loans** and click **Install**.

Dependencies (`hr`, `payroll`, `mail`, `base_setup`) install automatically.

## 3. Required one-time setup

> **This step is mandatory. Without it, no loan deduction ever reaches a
> payslip.**

The module ships a salary rule named **Loan Repayment** (code
`LOAN_REPAY`), placed in the `DED` (Deduction) salary rule category. It is
deliberately **not** attached to any salary structure, because the module
cannot know which structure your company actually uses.

To wire it up once:

1. Go to **Payroll → Configuration → Salary Structures**.
2. Open the structure your employees are actually paid on.
3. In **Salary Rules**, add the rule **Loan Repayment**.
4. Save.

From then on, every payslip computed on that structure picks the rule up
automatically.

To verify the wiring: approve a small loan whose first instalment falls in
the current month, create a payslip for that employee and period, click
**Compute Sheet**, and confirm a **Loan Repayment** line appears with a
negative amount.

## 4. Configuration — Loan Policy

**Employees → Loans → Loan Policy** (HR Administrator only). Both settings
are stored per company.

| Setting | Default | Meaning |
|---|---|---|
| **Allow Multiple Running Loans** | Off | When off, an employee cannot get a second loan **approved** while an earlier approved loan still has an outstanding balance. |
| **Maximum Loan Amount** | 0.00 | Largest principal that may be approved. **0 means no cap.** Checked against the principal only — interest is ignored. |

Both rules are enforced at the moment of **approval**, not when the record
is saved. A loan above the cap can be captured and submitted; it simply
cannot be approved.

## 5. Daily use

HR raises loans on behalf of the employee — there is no self-service
request form.

1. **Employees → Loans → Loan Requests → New**.
2. Pick the **Employee**. Department and Job Position fill in read-only.
3. Enter **Loan Amount**, **Purpose**, **Number of Instalments**,
   **First Instalment Date** and optionally **Interest (%)**.
4. Click **Build the schedule**. The **Repayment Schedule** table fills in.
5. Click **Submit**. (The button stays hidden until a schedule exists.)
6. An HR Officer clicks **Approve** — or **Refuse** after typing a
   **Refusal Reason**.

While the loan is still a draft, changing **Loan Amount**, **Interest (%)**,
**Number of Instalments** or **First Instalment Date** **deletes the
schedule** as a side effect. This is intentional: a stale schedule would no
longer match the terms. Rebuild it before submitting again.

Once the loan is **Approved** or **Closed**, those four fields are frozen at
the model level — ORM writes, imports and RPC calls are refused too, not
just the form. The **Employee** is frozen as soon as the loan leaves Draft.

**Deleting**: allowed only in Draft, Refused or Cancelled. Approved and
Closed loans cannot be deleted — settle them instead, so the repayment
history survives.

## 6. How the schedule is calculated

Interest is **flat**: computed once on the whole principal, then split
evenly. Rounding remainders land on the **last** instalment, so the rows
always add up exactly.

**Worked example — 1,000.00 over 4 instalments at 10%**

- Total interest = 1,000.00 × 10 / 100 = **100.00**
- Principal per instalment = 1,000.00 / 4 = **250.00**
- Interest per instalment = 100.00 / 4 = **25.00**

| No. | Due date | Principal | Interest | Instalment |
|---|---|---|---|---|
| 1 | 01 Mar | 250.00 | 25.00 | 275.00 |
| 2 | 01 Apr | 250.00 | 25.00 | 275.00 |
| 3 | 01 May | 250.00 | 25.00 | 275.00 |
| 4 | 01 Jun | 250.00 | 25.00 | 275.00 |
| | **Total** | **1,000.00** | **100.00** | **1,100.00** |

**Worked example — remainder on the last row: 1,000.00 over 3, no interest**

1,000.00 / 3 = 333.333…, rounded to 333.33. The first two rows take 333.33;
the last row takes 1,000.00 − (333.33 × 2) = **333.34**.

Due date of instalment *n* = **First Instalment Date + (n − 1) months**.

**The three balance figures** shown above the schedule:

- **Total Repayable** — sum of every instalment, whatever its state.
- **Recovered** — sum of instalments in state *Recovered*.
- **Outstanding** — sum of instalments in state *Scheduled*. Cancelled
  instalments are excluded, which is why Outstanding drops to 0 the moment
  a loan is settled early.

By construction: `Recovered + (sum of Cancelled) = Total Repayable`.

## 7. Payslip recovery

When a payslip is computed for an employee, the module looks for
instalments where:

- the loan belongs to that employee and is **Approved**,
- the instalment is **Scheduled**, and
- its **Due Date** falls inside the payslip's `date_from … date_to`.

One payslip input line is added per match, named
*"Loan repayment — LOAN/00007 #3"*, carrying the instalment's total and a
link back to the instalment. Recomputing a payslip clears the previous
loan-linked input rows and regenerates them, so nothing is ever duplicated.

If several instalments fall due in the same period, several input rows are
created and the salary rule **sums them into a single payslip line**.

Recovery happens on **Confirm**, not on Compute — a payslip can be computed
and recomputed any number of times before anyone commits to it. When the
payslip is confirmed, each linked instalment still in state *Scheduled*
becomes **Recovered** and stores the payslip reference. The filter re-checks
the state every time, so confirming twice recovers nothing the second time.

When the last scheduled instalment is recovered, the loan closes itself and
posts a note in the chatter.

> A period with nothing due produces **no payslip line at all** — the salary
> rule's condition suppresses it when the sum is zero.

## 8. Deferring and settling

**Defer an instalment** (approved loans only). Pick a *Scheduled*
instalment and give a reason. That instalment **and every later scheduled
instalment** move forward by exactly one month. Amounts never change —
dates move, money does not. There is no limit on repeat deferrals; each one
posts its own chatter message, so the history stays readable.

**Settle early** (approved loans with an outstanding balance). Give a
settlement date and a payment reference. Every *Scheduled* instalment
becomes **Cancelled** — never deleted, so the table still reads as history —
the loan is stamped and closed, and the settlement is posted to the chatter.

## 9. Access rights

| Group | Loans | Instalments | Actions |
|---|---|---|---|
| **Employee** (`base.group_user`) | read own only | read own only | none |
| **HR Officer** (`hr.group_hr_user`) | read, write, create | full | all workflow, defer, settle |
| **HR Administrator** (`hr.group_hr_manager`) | full incl. delete | full | the above + Loan Policy |

"Own" means the loan's employee is linked to the current user. This is
enforced by **record rules**, so opening a colleague's loan directly by URL
fails server-side, not just by hiding it from a list. Employees have no
create/write/unlink permission at all, so the workflow buttons are refused
server-side even if called directly.

A company record rule on both models restricts records to the user's
allowed companies.

The module creates **no security groups** and grants **no group to any
user** — it reuses the standard `hr` groups your database already has.

## 10. Field reference

**`odomate.hr.loan`**

| Field | Type | Notes |
|---|---|---|
| `name` | Char | `LOAN/00001`, from sequence, read-only |
| `employee_id` | Many2one `hr.employee` | frozen once out of Draft |
| `department_id`, `job_id` | Many2one, related | display only, not stored |
| `company_id`, `currency_id` | Many2one, related | stored; drive the record rules |
| `amount` | Monetary | principal |
| `purpose` | Char | one-sentence reason |
| `instalment_count` | Integer | number of rows to build |
| `first_instalment_date` | Date | month of instalment 1 |
| `interest_percentage` | Float | flat, on the whole amount |
| `state` | Selection | draft / submitted / approved / refused / cancelled / closed |
| `refusal_reason` | Text | required to refuse |
| `settlement_date`, `settlement_reference` | Date, Char | set by the settle wizard |
| `total_amount`, `recovered_amount`, `outstanding_amount` | Monetary, stored compute | see §6 |
| `instalments_remaining` | Integer, stored compute | count of *Scheduled* |

**`odomate.hr.loan.instalment`**

| Field | Type | Notes |
|---|---|---|
| `loan_id` | Many2one | cascade delete |
| `sequence` | Integer | instalment number |
| `due_date` | Date | moved by the defer wizard |
| `principal_amount`, `interest_amount`, `total_amount` | Monetary | plain stored columns, written once |
| `state` | Selection | scheduled / recovered / cancelled |
| `payslip_id` | Many2one `hr.payslip` | set on recovery |

## 11. Limitations

These are deliberate. Read them before rolling the module out.

- **The salary rule must be added to your salary structure by hand.** See
  §3. This is a one-time setup step the module will not do for you.
- **No affordability check.** Only the flat *Maximum Loan Amount* ceiling
  exists. Whether to lend stays a human decision.
- **Net pay can reach zero or go negative.** Nothing here prevents it;
  reviewing the payslip is a human step.
- **No accounting entries.** No journal entry is posted for the loan, the
  disbursement or the repayment. The instalment table is a real, stored
  model precisely so a future accounting module can read it.
- **Nothing fires when an employee leaves.** An outstanding loan on a
  leaver is a conversation this module does not automate.
- **Flat interest only.** No reducing balance, and deferring an instalment
  never recalculates interest — dates move, money does not.
- **No self-service requesting.** HR raises loans; *My Loans* is read-only.
- **Loans are per company.** A loan follows the employee's company and is
  invisible from other companies.
