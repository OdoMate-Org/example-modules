# Accounting Audit Reports — User Guide

Module: `odomate_account_ledger_reports` · Odoo 19.0 · Version 19.0.1.0.1 · License LGPL-3

## Table of contents

1. [What this module does](#1-what-this-module-does)
2. [Installation](#2-installation)
3. [Who can use it](#3-who-can-use-it)
4. [Where to find the reports](#4-where-to-find-the-reports)
5. [The shared filter](#5-the-shared-filter)
6. [General Ledger](#6-general-ledger)
7. [Partner Ledger](#7-partner-ledger)
8. [Aged Partner Balance](#8-aged-partner-balance)
9. [Tax Report](#9-tax-report)
10. [Journals Audit](#10-journals-audit)
11. [Journal Entry printout](#11-journal-entry-printout)
12. [Journal item screens](#12-journal-item-screens)
13. [Known limitations](#13-known-limitations)
14. [For developers: the stable contract](#14-for-developers-the-stable-contract)

---

## 1. What this module does

It adds the six classic accounting audit printouts that auditors and accountants ask for, as plain PDF documents, plus two ready-made journal-item screens.

| Report | Answers |
|---|---|
| General Ledger | What moved on each account, with a running balance |
| Partner Ledger | What moved on each customer/vendor account, and what they still owe |
| Aged Partner Balance | How overdue each open item is, bucketed by age |
| Tax Report | Net and tax amounts per tax, split into Sales and Purchases |
| Journals Audit | Every item of the selected journals, with a tax recap per journal |
| Journal Entry | One page per journal entry, for filing or attaching to a voucher |

Every report reads journal items through the Odoo ORM only. The module writes nothing outside its own dialog records and adds no field to any core model.

## 2. Installation

1. Copy the `odomate_account_ledger_reports` folder into your addons path.
2. **Apps → Update Apps List**.
3. Search for *Accounting Audit Reports* and click **Activate**.

The only dependencies are `account` and `analytic`, both of which ship with Odoo Community. No configuration step is required after install — there is no settings page, no scheduled job, and no demo data.

## 3. Who can use it

Three existing Odoo accounting groups may open the dialogs and print:

- `account.group_account_manager` — Billing Administrator
- `account.group_account_user` — Accountant
- `account.group_account_readonly` — read-only accounting access

The module creates no group of its own and grants nothing to any other group. A user outside these three gets `Only accounting users can print accounting reports.` if a print is attempted, and never sees the menus.

Each dialog record is a transient (wizard) record: the three groups get read, write and create on it, and nobody gets delete — Odoo's own vacuum cleans them up.

## 4. Where to find the reports

| Report | Menu path |
|---|---|
| General Ledger | Accounting → Reporting → Audit Reports → General Ledger |
| Journals Audit | Accounting → Reporting → Audit Reports → Journals Audit |
| Partner Ledger | Accounting → Reporting → Partner Reports → Partner Ledger |
| Aged Partner Balance | Accounting → Reporting → Partner Reports → Aged Partner Balance |
| Aged Receivable | Accounting → Reporting → Partner Reports → Aged Receivable |
| Aged Payable | Accounting → Reporting → Partner Reports → Aged Payable |
| Tax Report | Accounting → Reporting → Taxes → Tax Report |
| Journal Items by Account | Accounting → Reporting → Management → Journal Items by Account |
| Journal Items by Partner | Accounting → Reporting → Management → Journal Items by Partner |

*Aged Receivable* and *Aged Payable* are the same dialog as *Aged Partner Balance* with the account type pre-selected and hidden.

The Journal Entry printout has no menu: select one or more entries in **Accounting → Accounting → Journal Entries** and use **Print → Journal Entry**.

## 5. The shared filter

Every dialog starts from the same four-field filter.

| Field | Meaning |
|---|---|
| **Entries** | *Posted Entries Only* (default) or *All Entries*. Cancelled entries are never included under either option. |
| **Start Date** / **End Date** | Bound the journal items by their accounting date. Leave both empty for "all dates" where the dialog allows it. |
| **Journals** | Leave empty to cover every journal of the company. |
| **Company** | Visible only in multi-company databases. Defaults to your active company. |

Press **Print** to produce the PDF, **Cancel** to close.

The dialog refuses to print and explains why when:

- the chosen company is not one you are allowed to work in;
- the start date is after the end date;
- a selected journal belongs to a different company.

## 6. General Ledger

**Extra fields:** Accounts, Partners, Analytic Accounts (only with *Analytic Accounting*), Sort By, Display Accounts, Include Opening Balance.

**Columns:** Date · Journal · Partner · Reference · Entry · Label · Debit · Credit · Balance, plus Currency (multi-currency users, only when the item's currency differs from the company currency) and Analytic (analytic-accounting users).

**Display Accounts**

- *All Accounts* — every account of the company, even untouched ones.
- *With Movements* (default) — accounts with items in the period, or with a non-zero opening.
- *With Balance Not Equal To Zero* — drops accounts whose opening + debit − credit rounds to zero.

**Sort By** changes the order inside each account: *Date* orders by date, entry number, id; *Journal and Partner* orders by journal, then partner, then date.

### Worked example — the opening balance

Company books, fiscal year = calendar year, start date **2024-03-01**, **Include Opening Balance** ticked.

| Entry | Date | Account 121000 (Receivable) | Account 400000 (Income) |
|---|---|---|---|
| E1 | 2023-06-15 | debit 1,000.00 | credit 1,000.00 |
| E2 | 2024-02-10 | debit 500.00 | credit 500.00 |
| E3 | 2024-03-15 | debit 250.00 | credit 250.00 |

Printed openings:

- **121000** is a balance-sheet account, so it opens with *everything* booked before the start date: 1,000.00 + 500.00 = **1,500.00**.
- **400000** is an income account, so it opens with the current fiscal year only: E1 falls in the previous year and is excluded, leaving **−500.00**.

The running balance of 121000 then reads 1,500.00 on the *Opening Balance* row and 1,750.00 after E3; the account total line shows Debit 250.00, Credit 0.00, Balance 1,750.00.

## 7. Partner Ledger

**Extra fields:** Partners, Account Type, Include Settled Items, Show Amount in Currency (multi-currency users).

**Account Type** maps onto Odoo account types: *Receivable Accounts* → `asset_receivable`, *Payable Accounts* → `liability_payable`, *Receivable and Payable Accounts* → both.

**Columns:** Date · Journal · Account · Entry · Reference · Label · Debit · Credit · Balance (restarting from zero for each partner), plus Currency.

Each partner block ends with Debit, Credit, closing Balance and **Amount owed** — the sum of the items' residual amounts.

An item is hidden unless **Include Settled Items** is ticked only once it is *fully* settled — that is, once every item on the other side of its reconciliation has also been matched away and nothing remains outstanding. A part-paid invoice keeps printing both its own row and its payment's row until that happens, so the closing balance always reads what is still outstanding; a fully paid invoice and its payment both disappear together, and reappear together when **Include Settled Items** is ticked. Items without a partner are never printed here; they belong to the General Ledger.

You can also print it straight from a contact: select one or more contacts in **Contacts**, then **Print → Partner Ledger**. The dialog opens with those partners pre-filled, the account type set to *Receivable and Payable Accounts* and settled items included.

### Worked example — a part-paid invoice keeps its payment on its own row

A customer invoice of 1,000.00 is booked, then part-paid with 400.00. Printed with **Include Settled Items** unticked:

| Row | Debit | Credit | Balance |
|---|---|---|---|
| Invoice | 1,000.00 | | 1,000.00 |
| Payment | | 400.00 | 600.00 |
| **Partner total** | **1,000.00** | **400.00** | **600.00** |

**Amount owed** also reads 600.00 — both rows print because 600.00 is still outstanding on the invoice side, even though the payment itself has nothing left to match. Once the invoice is paid in full, both rows disappear from the unticked view and only reappear together when **Include Settled Items** is ticked.

## 8. Aged Partner Balance

**Extra fields:** As of Date (required, defaults to today), Period Length (days) (required, default 30), Account Type, Partners. Start Date and Journals are not used by this report and are hidden.

Each open item is placed in one of six columns by its age in whole days, where age = *As of Date* − (due date, or accounting date when there is no due date):

| Column | Age (P = Period Length) |
|---|---|
| Not Due | age ≤ 0 |
| 1 - P | 1 … P |
| P+1 - 2P | P+1 … 2P |
| 2P+1 - 3P | 2P+1 … 3P |
| 3P+1 - 4P | 3P+1 … 4P |
| +4P | age > 4P |

A row whose six columns are all zero is dropped. Items without a partner are grouped into an **Unknown Partner** row. All amounts are in the company currency; no conversion is applied anywhere.

### Worked example — bucketing at P = 30, as of 2024-06-30

| Item | Due date | Age | Amount | Column |
|---|---|---|---|---|
| A | 2024-06-30 | 0 | 10.00 | Not Due |
| B | 2024-06-29 | 1 | 20.00 | 1 - 30 |
| C | 2024-05-31 | 30 | 30.00 | 1 - 30 |
| D | 2024-05-30 | 31 | 40.00 | 31 - 60 |
| E | 2024-03-01 | 121 | 50.00 | +120 |

Printed row: Not Due 10.00 · 1-30 50.00 · 31-60 40.00 · 61-90 0.00 · 91-120 0.00 · +120 50.00 · Total 150.00.

### Worked example — residual is measured *as of* the date

An invoice of 1,000.00 is booked on 2024-03-10 and partly paid with 400.00 on 2024-05-20.

- As of **2024-04-30** the payment has not happened yet, so the report shows **1,000.00**.
- As of **2024-06-30** it shows **600.00**, and the payment line itself nets to zero and disappears.

The report recomputes the residual from the reconciliation history instead of reading today's `amount_residual`, which is what makes a back-dated ageing correct.

## 9. Tax Report

Only the shared filter applies; Start Date and End Date are required and default to the first day of the current month and today.

The report lists every active sale and purchase tax of the company in two sections. A tax group is represented by its child taxes under the parent's type; the group itself is not a row. For each tax:

- **Net Amount** — the sum of the balances of the items that carry the tax.
- **Tax Amount** — the sum of the balances of the tax lines generated by the tax.

In the **Sales** section both figures are sign-flipped so that revenue reads positive; in **Purchases** they are printed as booked. No absolute value is ever taken, so credit notes genuinely reduce the figures. Rows that are zero on both figures are omitted, and an empty section prints *No tax movement in this period.*

### Worked example — a credit note reduces the sales figures

March 2024, one 20 % sales tax:

| Document | Net | Tax |
|---|---|---|
| Customer invoice, 1,000.00 + 20 % | 1,000.00 | 200.00 |
| Credit note, 400.00 + 20 % | −400.00 | −80.00 |
| **Printed Sales row** | **600.00** | **120.00** |

## 10. Journals Audit

**Extra fields:** Journals (required — defaults to the sale and purchase journals of your company), Sort Entries By, Show Amount in Currency.

One section per selected journal, in the journals' own order. **Columns:** Entry · Date · Account · Partner · Label · Debit · Credit, plus Currency. Each section ends with the journal's Debit and Credit totals.

When the journal has taxed items a small recap table follows with Tax / Base Amount / Tax Amount, using the same sign rule as the Tax Report (sales taxes negated). Journals with no taxed items simply have no recap table.

## 11. Journal Entry printout

No dialog: select entries and use **Print → Journal Entry**. One page per entry, each printed with its own company's letterhead and currency.

The header shows the entry number, journal, date, partner, reference and status. The item table shows Account · Label · Partner · Analytic · Debit · Credit · Currency, in the entry's own line order, excluding section, sub-section and note lines. The totals row sums debit and credit in the entry's company currency — equal for any posted entry.

## 12. Journal item screens

Two saved views over `account.move.line`, both list / pivot / graph with Odoo's standard journal-item search panel, and both excluding section, sub-section and note lines:

- **Journal Items by Account** — grouped by account, posted entries only.
- **Journal Items by Partner** — grouped by partner, posted entries, pre-filtered to trade receivable, trade payable and unreconciled items.

They are ordinary Odoo list views: you can regroup, filter, export, and drill into an entry from there.

## 13. Known limitations

- **Company currency only.** Every figure is the company-currency amount. The optional Currency column shows the item's own foreign amount for reference; nothing is converted.
- **No Excel export.** The reports are PDF only. Use the two journal item screens when you need a spreadsheet.
- **Aged balance ignores journals.** By design the ageing covers all journals of the company; the Journals field is hidden on that dialog.
- **No drill-down.** The PDFs are static documents; they do not link back into Odoo.
- **`account.report` untouched.** The module does not extend Odoo's dynamic report engine, so these reports do not appear in its variant selector.
- **Tax report scope.** Only taxes whose `type_tax_use` is `sale` or `purchase` are listed; taxes set to *None* never appear.
- **Analytic column.** Analytic information is read from `analytic_distribution`; the percentages shown are the distribution percentages, not amounts.

## 14. For developers: the stable contract

Sibling modules may rely on the following and it will not change:

**Model** `odomate.account.report.filter` (concrete `TransientModel`, base for prototype inheritance) with fields `company_id`, `date_from`, `date_to`, `journal_ids`, `target_move`, and the methods:

| Member | Kind | Purpose |
|---|---|---|
| `_odomate_journals()` | record | Selected journals, or every journal of the company |
| `_odomate_state_domain()` | record | State leaf for the chosen `target_move` |
| `_odomate_line_domain(date_field='date', date_from=None, date_to=None)` | record | The base journal-item domain |
| `_odomate_check_filter()` | record | Validation; extend with `super()` |
| `_odomate_report_data()` | record | The primitives-only payload handed to the report |
| `_odomate_print(report_xmlid=None)` | record | Validate, then return the report action |
| `action_odomate_print()` | record | The dialog's Print button |
| `_odomate_report_xmlid` | class attr | Default report XML ID of the dialog |
| `_odomate_options_from_data(data)` | model | Parse the payload back into records and dates |
| `_odomate_check_report_access()` | model | Raise `AccessError` outside the three accounting groups |
| `_odomate_initial_balance_domain(company, date_from, journals=None, target_move='posted')` | model | Opening-balance domain |

**View** `odomate_account_ledger_reports.view_odomate_account_report_filter_form` — inherit with `mode="primary"` and add your own fields after the `journal_ids` node or the `target_move` node. Those two are the only supported anchors.

**QWeb** `odomate_account_ledger_reports.report_filter_header` — parameters `company`, `date_from`, `date_to`, `journals`, `target_move_label`.

**Paper format** `odomate_account_ledger_reports.paperformat_odomate_ledger_landscape` — A4 landscape, 10 mm margins.

**Menu** `odomate_account_ledger_reports.menu_odomate_account_reports_audit` — the *Audit Reports* folder.

Everything else — per-dialog fields, row-building helpers, report model names, template wording, dictionary key order — is internal and may change.

---

© OdoMate · <https://odomate.pro> · <support@odomate.pro>
