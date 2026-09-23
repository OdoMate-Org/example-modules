# Accounting Daily Reports — User Guide

Day Book, Cash Book and Bank Book PDF printouts for Odoo 19 Community.

## Table of contents

1. [Overview](#1-overview)
2. [Installation](#2-installation)
3. [Who can use it](#3-who-can-use-it)
4. [Day Book](#4-day-book)
5. [Cash Book](#5-cash-book)
6. [Bank Book](#6-bank-book)
7. [How the figures are computed](#7-how-the-figures-are-computed)
8. [Multi-company](#8-multi-company)
9. [Limitations](#9-limitations)
10. [Support](#10-support)

## 1. Overview

This module adds three printable accounting books to **Accounting → Reporting → Audit Reports**:

| Report | What it lists | Journals covered |
|---|---|---|
| **Day Book** | Every journal item of the period, grouped into one block per calendar day | All journal types |
| **Cash Book** | Cash movements per account, with running balance | `cash` journals |
| **Bank Book** | Bank and credit card movements per account, with running balance | `bank` and `credit` journals |

All three are **read-only**. They never create, modify or delete a record, so they are unaffected by lock dates and can safely be run by a read-only accountant.

The module reuses the shared filter dialog, page header and landscape paper format of **Accounting Audit Reports** (`odomate_account_ledger_reports`), so all six reports look and behave consistently.

The printed header — company, period, journals, and the *Entries* selection (*Posted Entries Only* / *All Entries*) — displays in your session's language, using this module's own translations (`uk`, `pl`, `de`, `es`, `fr`, `pt_BR`).

## 2. Installation

1. Copy `odomate_account_daily_reports` into your Odoo addons path.
2. **Apps → Update Apps List**.
3. Search for *Accounting Daily Reports* and click **Install**.

`account` and `odomate_account_ledger_reports` are installed automatically if they are not present yet.

## 3. Who can use it

The three menus and the three dialogs are available to:

- `account.group_account_manager` — Accounting Administrator
- `account.group_account_user` — full accounting features
- `account.group_account_readonly` — read-only accounting

Users with only `account.group_account_invoice` (Invoicing) get no menu and no access: printing raises *"Only accounting users can print accounting reports."*

The module creates **no new security group** and modifies no user.

## 4. Day Book

**Accounting → Reporting → Audit Reports → Day Book**

| Field | Meaning |
|---|---|
| **Entries** | *Posted Entries Only* or *All Entries* (adds drafts). Cancelled entries never appear. |
| **Start Date** / **End Date** | Both are **required**. They default to today. |
| **Journals** | Leave empty to cover every journal of the company. |
| **Company** | Visible in multi-company setups. |

Click **Print** to get the PDF, or **Cancel** to close.

The printout groups items into one block per day. Columns are *Journal, Entry, Partner, Reference, Label, Debit, Credit, Difference* (plus *Currency* for multi-currency users). Each day closes with a **Day total** row. The report's own **Total** row prints exactly once, at the very end of the report — never repeated partway through, even on a printout that spans several pages — and is set apart from the **Day total** rows by a shaded background and a heavier top rule, so you can tell the two apart at a glance.

Days with no items produce no block — the report never prints an empty day. If nothing matches, the PDF says *"No entries in this period."*

The Day Book has **no opening balance and no running balance**: it is a chronological recap, not a ledger.

## 5. Cash Book

**Accounting → Reporting → Audit Reports → Cash Book**

Same filters as the Day Book, plus:

| Field | Meaning |
|---|---|
| **Sort by** | *Date* or *Journal and Partner* — changes the order of the items inside each account. |
| **Display Accounts** | *All Accounts*, *With Movements* (default), or *With Balance Not Equal To Zero*. |
| **Include Opening Balance** | Prints an **Opening Balance** row per account. Requires a Start Date. |
| **With Currency** | Adds the *Currency* column. Only visible to users in **Multi-Currency**. |

The **Journals** field only accepts cash journals. Picking a bank journal raises *"This book only covers cash journals."*

The printout has one block per account, ordered by account code, with columns *Date, Journal, Entry, Partner, Reference, Label, Debit, Credit, Balance*. Each block closes with an **Account total** row. The report's own **Total** row prints exactly once, at the very end of the report — never repeated partway through, even on a printout that spans several pages — and is set apart from the **Account total** rows by a shaded background and a heavier top rule, so you can tell the two apart at a glance.

### Which accounts appear

The Cash Book does not simply list "everything the cash journals touched". It resolves the account set from:

- each journal's **default account** and **suspense account**,
- each journal's **outstanding receipts / outstanding payments** accounts,
- plus every `asset_cash` account actually touched by an item in the period.

Accounts belonging to another company are dropped. This means a cash journal with no default account configured still prints correctly.

## 6. Bank Book

**Accounting → Reporting → Audit Reports → Bank Book**

Identical to the Cash Book, except that it covers **bank** and **credit card** journals, and its account set also includes `liability_credit_card` accounts. Picking a cash journal raises *"This book only covers bank and credit card journals."*

## 7. How the figures are computed

### Opening balance

With **Include Opening Balance** ticked, the opening row sums everything booked on that account **before the Start Date**, using the same fiscal-year-correct rule as the General Ledger of *Accounting Audit Reports*. For cash and credit card accounts — which always carry their balance forward — this is simply every earlier item.

### Running balance

The **Balance** column is a true running total per account:

```
balance of a row = balance of the previous row + this row's debit − this row's credit
```

The first row starts from the opening balance, or from zero when the opening is not printed.

### Closing balance

```
Account total = Opening + Σ debit − Σ credit
```

It is summed from the items, never read off the last row.

### Worked example

Account **101100 Cash A**, period 01/03/2024 → 31/03/2024, opening balance ticked.

| Row | Debit | Credit | Balance |
|---|---:|---:|---:|
| Opening Balance | 1,000.00 | 0.00 | **1,000.00** |
| 05/03/2024 CASH-IN | 200.00 | 0.00 | **1,200.00** |
| 10/03/2024 CASH-OUT | 0.00 | 50.00 | **1,150.00** |
| **Account total** | **200.00** | **50.00** | **1,150.00** |

Check: `1,000.00 + 200.00 − 50.00 = 1,150.00`.

The same period in the Day Book, for 05/03/2024 — a 200.00 cash receipt and a 300.00 bank receipt:

| | Debit | Credit | Difference |
|---|---:|---:|---:|
| **Day total** | 500.00 | 500.00 | **0.00** |

In a balanced ledger the **Difference** column is always 0.00; a non-zero value points at an unbalanced entry.

### Currency

Every figure is printed in the **company currency** — nothing is converted. The optional *Currency* column shows the item's own amount in its own currency whenever that currency differs from the company currency, negative amounts included.

## 8. Multi-company

Each printout covers exactly one company — the one chosen in the dialog. Items of other companies never appear. Choosing a company you are not allowed to work in raises *"You cannot print a report for a company you are not allowed to work in."*

The four dialog models are transient and hold no company data of their own, so no record rule is needed: the company filter lives in the validation step and in every domain.

## 9. Limitations

- **PDF and HTML only.** There is no XLSX or CSV export, and no interactive on-screen version.
- **No drill-down.** The PDF is a printout; clicking a figure does not open the underlying entry.
- **One company per printout.** Consolidated multi-company books are not supported.
- **No currency conversion.** Foreign-currency items are shown at their booked company-currency value; the report does not re-translate them at a chosen rate.
- **No analytic columns.** Use the General Ledger of *Accounting Audit Reports* if you need analytic distribution.
- **The Day Book has no balances** by design — use the Cash Book or Bank Book for running and closing balances.
- **No demo data.** These reports print whatever your database already contains.

## 10. Support

- Author: OdoMate — <https://odomate.pro>
- Support: <support@odomate.pro>

Translated versions of this guide: `USER_GUIDE.uk.md`, `USER_GUIDE.pl.md`, `USER_GUIDE.de.md`, `USER_GUIDE.es.md`, `USER_GUIDE.fr.md`, `USER_GUIDE.pt_BR.md`.
