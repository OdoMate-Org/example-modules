# Employee Loans — Accounting Entries

Technical name: `odomate_hr_loan_accounting` · Version `19.0.1.0.1` · Odoo 19

## Table of contents

1. [What this module does](#1-what-this-module-does)
2. [Installation](#2-installation)
3. [Configuration](#3-configuration)
4. [Daily use](#4-daily-use)
5. [The three entries, in full](#5-the-three-entries-in-full)
6. [Worked example](#6-worked-example)
7. [Field reference](#7-field-reference)
8. [Access rights](#8-access-rights)
9. [Limitations and deliberate choices](#9-limitations-and-deliberate-choices)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. What this module does

`odomate_hr_loan` runs the employee loan workflow: request, approval,
repayment schedule, payslip recovery, early settlement. It stores every figure
it needs — and posts nothing to the general ledger.

This module is the accounting half. It posts three kinds of journal entry, and
nothing else:

| Moment | Entry |
|---|---|
| A loan is approved | one **disbursement** entry |
| Payroll recovers one instalment | one **recovery** entry for that instalment |
| A loan is settled early | one **settlement** entry |

Every amount is read off the record that already stores it — the loan's
`amount` for the disbursement, the instalment's own `principal_amount`,
`interest_amount` and `total_amount` for the recovery. Nothing is recalculated,
so a deferred or hand-adjusted instalment posts exactly what it shows.

It adds **no new models**, no new menus, no new security groups and no demo
data. It adds three fields to the loan, one to the instalment, three to the
company, and two view extensions.

## 2. Installation

Requires `account` and `odomate_hr_loan`. Without `odomate_hr_loan` installed,
Odoo will refuse to install this module — it is a genuine dependency, not a
soft one.

1. Copy `odomate_hr_loan_accounting` into your addons path.
2. **Apps → Update Apps List**.
3. Search for *Employee Loans - Accounting Entries* and click **Activate**.

Nothing is posted retroactively. Loans already approved before installation
keep an empty **Journal Entries** counter; only loans approved from now on get
a disbursement entry.

## 3. Configuration

**Accounting → Configuration → Settings → Employee Loans** (visible to users in
*Billing Administrator* / `account.group_account_manager`).

Three settings, per company:

| Setting | What it is |
|---|---|
| **Loan Journal** | The journal the three entries are posted in. Only bank, cash and miscellaneous journals can be picked — a loan entry carries no customer or vendor document, so sale and purchase journals are excluded. **Its Default Account must be set**; that account is the counterpart of every line. |
| **Loan Receivable Account** | The asset account carrying what employees still owe. Debited on disbursement, credited as instalments come back. |
| **Loan Interest Income Account** | The income account credited with the interest part of each instalment. Only needed for loans that carry interest. |

A typical setup: a miscellaneous journal named *Employee Loans* whose default
account is the salary/payroll payable account, a *Loans to Employees* asset
account, and an *Interest Income* account.

These three become the defaults on every new loan. Each loan can override them
on its own **Accounting** tab — useful when one loan is paid straight from a
bank account while the rest run through payroll.

## 4. Daily use

### 4.1 Approving a loan (disbursement)

Nothing new to click. Open the loan, press **Approve** as usual.

Before the loan changes state, the module checks that the journal, its default
account and the receivable account are set — plus the interest account when the
loan carries interest — and that the employee has a contact to post against
(**Work Contact**, or the contact of the employee's linked user). If anything
is missing, approval is refused with a message naming exactly what to fix, and
the loan stays **Submitted**. Nothing is half-done.

Once approved, the entry is posted and linked. The **Journal Entries** smart
button at the top of the loan opens it.

### 4.2 Payslip recovery

Also nothing new to click. When payroll confirms a payslip and
`odomate_hr_loan` marks an instalment **Recovered**, this module posts that
instalment's entry, dated the payslip's **End Date** (`date_to`) so it lands in
the payroll period it belongs to.

The instalment's **Journal Entry** column in the repayment schedule fills in.
That link is the guard: an instalment that already has an entry never gets a
second one, so re-confirming or recomputing a payslip cannot double-post.

### 4.3 Early settlement

Press **Settle early**, fill in the settlement date and payment reference as
usual. The same configuration check runs *before* the loan closes, so a missing
journal leaves the loan approved and untouched rather than closing it without
an entry. The entry is dated the settlement date you typed, not today.

Cancelled instalments never produce an entry — not at settlement, not later.

## 5. The three entries, in full

Below, *counterpart* means the **Default Account of the loan journal**.

**Disbursement** — dated the approval day, ref `Loan LOAN/00007 - Disbursement`

| Line | Debit | Credit |
|---|---|---|
| Loan receivable *(employee as partner)* | loan amount | |
| Counterpart | | loan amount |

**Recovery** — dated the payslip's end date, ref
`Loan LOAN/00007 - Instalment March 2026`

| Line | Debit | Credit |
|---|---|---|
| Counterpart | instalment total | |
| Loan receivable *(employee as partner)* | | instalment principal |
| Interest income *(employee as partner)* | | instalment interest |

The interest line is omitted entirely when the instalment carries no interest,
leaving a plain two-line entry.

**Settlement** — dated the settlement date, ref `Loan LOAN/00007 - Settlement`

| Line | Debit | Credit |
|---|---|---|
| Counterpart | outstanding balance | |
| Loan receivable *(employee as partner)* | | principal still open |
| Interest income *(employee as partner)* | | interest still open |

The three entries are designed to net the receivable to zero once a loan is
finished, whether it ran to term or was settled early.

## 6. Worked example

Loan **LOAN/00007**, 12 000.00 for Olena Borrower, 4 monthly instalments, 10 %
interest, first instalment March 2026.

`odomate_hr_loan` builds the schedule: total interest 12 000 × 10 % = 1 200,
spread over 4 instalments. Each instalment stores principal 3 000.00, interest
300.00, total 3 300.00.

**2 March 2026 — approved.**

| Account | Debit | Credit |
|---|---|---|
| Loans to Employees | 12 000.00 | |
| Salary Payable *(journal default)* | | 12 000.00 |

**31 March 2026 — March payslip confirmed.**

| Account | Debit | Credit |
|---|---|---|
| Salary Payable | 3 300.00 | |
| Loans to Employees | | 3 000.00 |
| Interest Income | | 300.00 |

**30 April 2026 — April payslip confirmed.** Same three lines again.

**10 June 2026 — Olena settles the rest early.** Two instalments are still
scheduled, so the outstanding balance is 2 × 3 300.00 = 6 600.00.

| Account | Debit | Credit |
|---|---|---|
| Salary Payable | 6 600.00 | |
| Loans to Employees | | 6 000.00 |
| Interest Income | | 600.00 |

**Where that leaves the ledger:**

- Loans to Employees: 12 000 − 3 000 − 3 000 − 6 000 = **0.00**. The loan is
  fully accounted for.
- Interest Income: 300 + 300 + 600 = **1 200.00** — exactly the interest the
  schedule charged.
- The **Journal Entries** button on the loan now reads **4**.

## 7. Field reference

**On the loan (`odomate.hr.loan`), Accounting tab**

| Field | Type | Notes |
|---|---|---|
| `journal_id` | Many2one → `account.journal` | Defaults from the company. Bank, cash or miscellaneous only. |
| `receivable_account_id` | Many2one → `account.account` | Defaults from the company. |
| `interest_account_id` | Many2one → `account.account` | Shown and required only when **Interest (%)** is not zero. |
| `disbursement_move_id` | Many2one → `account.move` | Read-only, set once on approval, never copied. |
| `settlement_move_id` | Many2one → `account.move` | Read-only, set once on settlement, never copied. |
| `account_move_count` | Integer, computed | Disbursement + settlement + every instalment entry. Drives the smart button. |

**On the instalment (`odomate.hr.loan.instalment`)**

| Field | Type | Notes |
|---|---|---|
| `account_move_id` | Many2one → `account.move` | Read-only, set once when the row is recovered. Blank for scheduled and cancelled rows, for ever. |

**On the company (`res.company`)**

`loan_journal_id`, `loan_receivable_account_id`,
`loan_interest_income_account_id` — surfaced on the Accounting settings page
through `res.config.settings`.

## 8. Access rights

No new groups are created, and no group is granted to any user on install.

| Who | Sees / does |
|---|---|
| `account.group_account_invoice` or `account.group_account_readonly` (any Invoicing/Accounting access, including *Billing Administrator*) | The **Accounting** tab, the **Journal Entries** button, the **Journal Entry** column on the schedule, and the entries themselves. |
| `account.group_account_manager` (*Billing Administrator*) | The three company defaults on the settings page. |
| Everyone else | The loan exactly as `odomate_hr_loan` shows it — no accounting fields, no counter. |

The restriction is not just a hidden tab: `journal_id`, `receivable_account_id`,
`interest_account_id`, `account_move_count`, `disbursement_move_id` and
`settlement_move_id` carry that same access requirement on the field itself.
A user outside those two groups gets nothing real back for any of the six —
not through the form, not through an API call, not through an export — and
the posted `account.move` records themselves stay outside their reach the
same way any other journal entry is.

HR and payroll officers still do **not** need accounting rights to trigger
the postings, and this is deliberate: approving a loan or having payroll
recover an instalment has to decide whether and how to post, then link what
it posted, and that decision reads exactly those six fields. The loan's own
posting methods read and write them through a narrow, purpose-built
elevation — never through a blanket `sudo()` on the loan, the instalment,
the employee record, or any search. Everything else about the loan — its
state, amount, employee and instalments — is read on the officer's own
rights, unchanged. An HR officer therefore approves a loan and posts its
disbursement entry, yet still cannot read `journal_id` or the entry itself
afterwards through the ORM.

## 9. Limitations and deliberate choices

**No demo data is shipped, on purpose.** Demo records would have to name
accounts from a chart of accounts this module does not control, and would fail
on any customer whose chart differs. The three-field setup in section 3 plus
the walkthrough in section 6 is the intended verification path.

**Nothing is ever reversed, unlinked or edited.** Reopening or cancelling a
loan leaves its posted entries exactly as they are. If an entry is wrong, undo
it the accounting way — a manual reversal in Accounting — not by editing the
loan.

**A locked accounting period stops the posting, and is meant to.** If the
period of a payslip's end date is locked, the recovery entry is refused and the
error reaches the user. The module never silently re-dates an entry to today to
force it through: that would file the entry in the wrong period.

**Configuration cleared after approval is skipped, not raised.** Recovery runs
inside the payslip confirmation, sometimes for a whole batch of employees. If a
loan's journal or accounts were cleared after it was approved, that one
instalment is skipped silently: it stays **Recovered**, its stored figures are
untouched, and its **Journal Entry** column stays blank. The payslip run is not
aborted for that employee or any other. The gap is visible — the schedule shows
a recovered row with no entry, and the **Journal Entries** counter is lower than
the number of recovered instalments. Restore the configuration and post the
missing entry manually in Accounting; the module will not backfill it, because
the instalment's link is a once-only guard.

**Two departures from the original specification**, both to keep the ledger
self-consistent — worth knowing if you are comparing against the spec document:

1. *Recovery direction.* The spec described the recovery entry as debiting the
   receivable and interest accounts and crediting the counterpart. That is the
   reverse of what recovering money does: it would grow the receivable with
   every repayment, leaving a fully repaid loan showing twice its principal as
   still owed. The entry is posted the other way round, as shown in section 5,
   so recovery clears the receivable the disbursement raised.
2. *Settlement split.* The spec described a two-line settlement crediting the
   receivable with the whole outstanding balance. Since only the principal was
   ever debited to the receivable, that would leave the unearned interest of
   every early-settled loan as a permanent credit balance on the receivable
   account. The credit is therefore split into principal and interest. For a
   loan with no interest the two versions are identical.

**The settlement hook.** `odomate_hr_loan` applies early settlement inside its
own `odomate.hr.loan.settle` wizard and exposes no loan-side method to extend,
so the wizard's `action_settle` is where this module attaches. All the
accounting logic itself lives on `odomate.hr.loan`; the wizard override only
reads the outstanding balance before the instalments are cancelled and hands it
over.

**Single currency.** Entries are posted in the company currency, which is what
`odomate_hr_loan` already uses for every loan figure. Loans denominated in a
foreign currency are out of scope.

## 10. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Approval refused: *"Loan … has no journal"* | Set **Loan Journal** in Accounting settings, or pick one on the loan's Accounting tab. |
| Approval refused: *"The journal … has no default account"* | Open **Accounting → Configuration → Journals**, pick that journal, set its **Default Account**. |
| Approval refused: *"… carries interest, so it needs an interest income account"* | Either set the interest account, or set **Interest (%)** back to 0. |
| Approval refused: *"… has neither a work contact nor a linked user with a contact"* | Open the employee, **HR Settings** tab, set **Work Contact**. |
| I cannot see the Accounting tab or the smart button | You hold no accounting access (`account.group_account_invoice` / `account.group_account_readonly` or higher). Ask an administrator to grant Invoicing or Accounting rights. |
| A recovered instalment has no journal entry | The loan's accounting configuration was missing when payroll confirmed the payslip. See section 9. |
| The counter says 0 on an old loan | Loans approved before this module was installed are not backfilled. |
| Posting refused with a lock-date error | The period is closed. Reopen it, or post the entry manually in an open period. |

---

*OdoMate — https://odomate.pro — support@odomate.pro*
