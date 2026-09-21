# SPEC.md — the specification this module was generated from

This is the specification the module in this folder was generated from, exactly as it was
submitted to OdoMate. It is written at the level of an Odoo business analyst: it names the
menus, dialogs, groups and reports the user sees and states the acceptance criteria in
Section 15. Everything in `models/`, `report/`, `views/`, `security/` and `tests/` was
produced by OdoMate from it.

**Provenance, stated plainly.** This specification was written by the OdoMate team.

**What was verified before publication.** Installed on a freshly created Odoo 19 Community
database with demo data and the six shipped languages loaded, the module installs with no
errors, and OdoMate's own run reports its 30 tests passing. It ships no `.pot`, no demo data,
defines no group of its own and adds no field to any standard model.

**Two generated versions, and no hand correction to the code.** Version 1 was generated from
this document. Version 2 came from one enhancement round that corrected the partner ledger
(a part-paid invoice now prints its payment row and closes at what is still owed) and the
manifest category. Nothing in the module was written or corrected by hand. The publication
changes are the store listing page, the banner, the icon, the user-guide PDFs, the
screenshots, and the manifest metadata that points at them (`summary`, `website`, `images`).

**Known gaps, disclosed rather than fixed.** Measured against this document, the published
version departs from it in these places. None changes a figure.

- The ageing column headings read "1 - 30", "31 - 60" and so on, with a first column headed
  "Not Due", where the specification writes "1-30" and "Not due". The amounts sit in the
  right columns.
- The Opening Balance row of the General Ledger prints its debit and credit as 0.00; its
  balance is correct.
- The tax table under each journal in the Journals Audit has no "Tax Declaration" heading.
- In the landscape reports, the narrow Entry column can wrap an entry number onto a second
  line.
- The Journal Entry PDF downloads under the default file name instead of
  "Journal Entry - <name>".
- Some field and option labels differ from the wording in Sections 2.1 and 3.
- `analytic` is listed in `depends` although this document says `account` only; Odoo's own
  `account` module already depends on it.
- The shipped tests number their criteria differently from Section 15.
- Criterion 16 in Section 15 says a period length of 15 relabels all six ageing headings,
  while Section 14 defines "Not due" as a heading that never changes. The criterion as
  written cannot be met; this is an error in this document, not in the module.

**Not verified:** the optional Currency column with several currencies in use, and every
dialog clicked by hand in a browser. Figures and reports were checked against the database
and against rendered PDFs.

---

# Ledger and Audit Reports — Specification (Level 2: Odoo Business Analyst)

**Module:** `odomate_account_ledger_reports` · **Name:** "Ledger and Audit Reports" · **Target:** Odoo 19.0 Community
**Version:** `19.0.1.0.0` · **License:** LGPL-3 · **Category:** `Accounting` · **Application:** False · **Author:** OdoMate
**Website:** `https://odomate.pro` · **Support:** `support@odomate.pro`
**Depends on:** `account` only.

Every exact name in this document — model, field, method, group, menu, action, view, report, template, paper format and search filter — is part of the requirement. Where a rule and a name appear in one sentence, build that rule with that name.

Two further modules, `odomate_account_financial_statements` and `odomate_account_daily_reports`, are written against this one. Section 2 marks what they may call and what they may not.

---

## 1. Business goal

Odoo Community holds every figure an accountant needs and prints none of them. This module adds the six standard printouts — general ledger, partner ledger, aged partner balance, tax report, journals audit and a printout of one journal entry — plus two on-screen lists of journal items. Every report is asked for through the same dialog, reads `account.move.line` and nothing else, and **writes nothing**: no record is created, changed, posted or deleted outside the module's own transient dialogs.

There is no report engine to reuse. The model `account.report` exists in Community but its viewer ships with Enterprise, and no action or menu points at it. This module builds its own reports and **creates no action, menu or record on `account.report`**.

---

## 2. The shared filter contract

This section is the interface the two sibling modules build against. Everything under "Stable" keeps its name and behaviour for the life of the 19.0 series. Everything under "Internal" may change and must not be called from another module.

### 2.1 `odomate.account.report.filter` — stable

A **concrete `TransientModel`** named `odomate.account.report.filter`, `_description` "Accounting Report Filter". It never gets an action and never gets a menu. It exists so each dialog can declare `_inherit = 'odomate.account.report.filter'` together with its own `_name` — prototype inheritance, a separate table per dialog — and so its form view can be inherited.

| Field | Definition |
|---|---|
| `company_id` | Many2one `res.company`, required, string "Company", default the current company, domain limited to `allowed_company_ids` |
| `date_from` | Date, string "Start Date" |
| `date_to` | Date, string "End Date" |
| `journal_ids` | Many2many `account.journal`, **not required**, string "Journals", domain `company_id` equal to the dialog's `company_id`. **Empty means every journal of `company_id`** |
| `target_move` | Selection `posted` "All Posted Entries" / `all` "All Entries", required, default `posted`, string "Target Moves" |

### 2.2 The stable methods

| Member | Contract |
|---|---|
| `_odomate_journals()` | Ensure-one. Returns `journal_ids` when set; otherwise every `account.journal` whose `company_id` is the dialog's `company_id` |
| `_odomate_state_domain()` | For `posted`, restricts `parent_state` to `posted`; for `all`, to `draft` and `posted`. **`cancel` is never included, under either setting** |
| `_odomate_line_domain(date_field='date', date_from=None, date_to=None)` | The base journal-item filter (2.3). `date_from` and `date_to` default to the dialog's own fields; a caller passes them explicitly to widen or narrow the range |
| `_odomate_check_filter()` | Validates the dialog and raises `UserError`. A dialog adding checks extends it through `super()` |
| `_odomate_report_data()` | The JSON-safe dictionary handed to `report_action`. A dialog adding fields extends it through `super()` |
| `_odomate_print(report_xmlid=None)` | Calls `_odomate_check_filter()`, then `report_action` on `report_xmlid` or on `_odomate_report_xmlid`, passing `data=_odomate_report_data()` |
| `action_odomate_print()` | The Print button's method; returns `_odomate_print()` |
| `_odomate_report_xmlid` | A class attribute, not a field. Each dialog sets it to the full xml id of its own report action |
| `_odomate_options_from_data(data)` | Model method. Rebuilds the filter on the report side, returning the keys `company`, `journals`, `date_from`, `date_to`, `target_move`, `target_move_label`, `journals_label` and `date_label` as recordsets and date objects. Raises `UserError` when `data` is absent; runs `_odomate_check_report_access()` |
| `_odomate_check_report_access()` | Model method. Raises `AccessError` unless the user holds `account.group_account_manager`, `account.group_account_user` or `account.group_account_readonly`. **Every `_get_report_values` in this module and in the two sibling modules calls it first** |
| `_odomate_initial_balance_domain(company, date_from, journals=None, target_move='posted')` | Model method. The opening-balance filter (2.5) |

### 2.3 The base journal-item filter

`_odomate_line_domain` restricts `account.move.line` to all of the following, and nothing else:

- `company_id` equal to the dialog's `company_id`;
- `display_type` **not** one of `line_section`, `line_subsection`, `line_note`;
- `journal_id` in the result of `_odomate_journals()`;
- the state restriction from `_odomate_state_domain()`;
- `date_field` on or after `date_from`, and on or before `date_to`, each applied only when that date is set.

`date_field` is `date` for every report; only the aged partner balance passes a different field, and only for bucketing (section 5).

`account.move.line` has `_order` `date desc, move_name desc, id`, so **every search in this module passes an explicit `order`**. Counts use `search_count`, never the length of a fetched batch.

### 2.4 The refusals, and the data handed to the report

`_odomate_check_filter` raises `UserError` in this order:

1. `company_id` is not among the user's allowed companies → "You cannot print a report for a company you are not allowed to work in."
2. `date_from` and `date_to` are both set and `date_from` is after `date_to` → "The start date cannot be after the end date."
3. a journal in `journal_ids` whose `company_id` is not the dialog's `company_id` → "Every journal must belong to %(company)s."

`_odomate_report_data` returns exactly these keys: `company_id` (an id), `date_from` and `date_to` (ISO date strings or False), `journal_ids` (the ids from `_odomate_journals()`), `explicit_journals` (True when the user picked journals), `target_move`, and `wizard_model` (the dialog's `_name`). **This dictionary crosses the browser: every value is an id, an ISO date string, a boolean or a plain string** — never a recordset, never a date object.

### 2.5 The opening balance, by account kind

`_odomate_initial_balance_domain(company, date_from, journals, target_move)` restricts `account.move.line` to:

- `company_id` equal to `company`;
- `display_type` not one of `line_section`, `line_subsection`, `line_note`;
- `date` strictly **before** `date_from`;
- **and either** `account_id.include_initial_balance` is True **or** `date` is on or after the first day of the fiscal year containing `date_from`;
- plus the state restriction for `target_move`, and `journal_id` in `journals` when journals are given.

`include_initial_balance` is a computed field on `account.account`, True for every account whose `internal_group` is neither `income` nor `expense` and whose `account_type` is not `equity_unaffected`. **Its search method accepts the `in` operator only: test it as equal to True, never as not equal to False.** The fiscal year's first day comes from `res.company.compute_fiscalyear_dates`, which takes a date and returns the bounds of the fiscal year containing it.

A balance-sheet account therefore opens with everything booked before the start date; an income or expense account, and Current Year Earnings, open with what was booked since the start of the fiscal year containing the start date.

### 2.6 Other stable artefacts

| Artefact | Full xml id | Promise |
|---|---|---|
| Filter form view | `odomate_account_ledger_reports.view_odomate_account_report_filter_form` | Keeps the fields `target_move`, `date_from`, `date_to`, `journal_ids`, `company_id` and the footer button `action_odomate_print`. **The two anchors an inheriting view may target are the `journal_ids` field node and the `target_move` field node** |
| Report header template | `odomate_account_ledger_reports.report_filter_header` | Callable from another module's template; takes `company`, `date_from`, `date_to`, `journals` and `target_move_label` and renders the header block of every report in the suite |
| Landscape paper format | `odomate_account_ledger_reports.paperformat_odomate_ledger_landscape` | A `report.paperformat` record: A4, landscape, margins top 10, bottom 10, left 10, right 10 |
| Menu folder | `odomate_account_ledger_reports.menu_odomate_account_reports_audit` | "Audit Reports", parent `account.menu_finance_reports`, sequence 30 |

### 2.7 Internal — no other module may depend on it

The five dialogs' own extra fields and methods; every row-building method on the report models; the six `report.odomate_account_ledger_reports.*` model names; every template other than `report_filter_header`; the wording of any label or message; the order of keys inside a report's values dictionary.

---

## 3. The general ledger

**Dialog** `odomate.account.general.ledger.wizard`, `_inherit = 'odomate.account.report.filter'`, `_description` "General Ledger", `_odomate_report_xmlid = 'odomate_account_ledger_reports.action_report_odomate_general_ledger'`.

| Field | Definition |
|---|---|
| `account_ids` | Many2many `account.account`, string "Accounts", domain `company_ids` containing the dialog's `company_id` |
| `partner_ids` | Many2many `res.partner`, string "Partners" |
| `analytic_account_ids` | Many2many `account.analytic.account`, string "Analytic Accounts", `groups="analytic.group_analytic_accounting"` |
| `display_account` | Selection `all` "All" / `movement` "With movements" / `not_zero` "With balance not equal to 0", required, default `movement`, string "Display Accounts" |
| `initial_balance` | Boolean, string "Include Opening Balance" |
| `sortby` | Selection `sort_date` "Date" / `sort_journal_partner` "Journal & Partner", required, default `sort_date`, string "Sort by" |

`_odomate_check_filter` extension: `initial_balance` set without a `date_from` → `UserError` "Set a start date to print an opening balance." `_odomate_report_data` extension adds `account_ids`, `partner_ids`, `analytic_account_ids`, `display_account`, `initial_balance` and `sortby`.

**Report model** `report.odomate_account_ledger_reports.report_general_ledger`; report action `action_report_odomate_general_ledger` "General Ledger", `report_type` `qweb-pdf`, `report_name` and `report_file` `odomate_account_ledger_reports.report_general_ledger`, `model` `odomate.account.general.ledger.wizard`, `paperformat_id` the landscape format of 2.6.

`_get_report_values` works in this order:

1. Rebuild the options through `_odomate_options_from_data`, which performs the access check.
2. Items: the base filter of 2.3, narrowed by `account_id` in `account_ids`, `partner_id` in `partner_ids` and `analytic_distribution` **`in`** `analytic_account_ids`, each applied only when that field was filled. The `in` operator on the Json field `analytic_distribution` is the one core's own journal-item search view uses.
3. Order: `date, move_name, id` for `sort_date`; `journal_id, partner_id, date, id` for `sort_journal_partner`.
4. Opening balance, only when `initial_balance` is set: one grouped read over `_odomate_initial_balance_domain` plus the same account, partner and analytic terms, grouped by `account_id`, summing `debit`, `credit` and `balance`.
5. Accounts shown: the candidates are the accounts with at least one item in the period, the accounts carrying an opening balance, and — for `all` only — every account whose `company_ids` contains the company. `all` prints every candidate; `movement` those with at least one item **in the period**; `not_zero` those whose opening plus period debit minus period credit is not zero at `company.currency_id`'s rounding. Accounts print in `code` order.
6. One block per account, its rows in the chosen order, with these columns: Date (`date`) · Journal (`journal_id.code`) · Partner (`partner_id.display_name`) · Reference (`ref`) · Entry (`move_name`) · Label (`name`) · Debit (`debit`) · Credit (`credit`) · Balance · Currency · Analytic.
   - **Balance** is running: the previous balance plus `debit` minus `credit`, starting at the opening balance, or at zero when none was asked for.
   - **Currency** carries `groups="base.group_multi_currency"` and shows `amount_currency` with `currency_id`, only on items whose `currency_id` differs from `company.currency_id`.
   - **Analytic** carries `groups="analytic.group_analytic_accounting"` and renders `analytic_distribution` as account name and percentage per entry, the referenced analytic accounts read in one batch.

7. The opening-balance row prints the label **"Opening Balance"** with its debit, credit and balance, and no date, journal, partner, reference or entry.
8. Totals per account: `debit`, `credit`, and a closing balance of opening plus debit minus credit. Report totals: the same three, summed over the accounts printed.

**The running balance is computed by the report.** The core field `cumulated_balance` on `account.move.line` is never read.

---

## 4. The partner ledger

**Dialog** `odomate.account.partner.ledger.wizard`, `_description` "Partner Ledger", `_odomate_report_xmlid = 'odomate_account_ledger_reports.action_report_odomate_partner_ledger'`.

| Field | Definition |
|---|---|
| `partner_ids` | Many2many `res.partner`, string "Partners" |
| `result_selection` | Selection `customer` "Receivable Accounts" / `supplier` "Payable Accounts" / `customer_supplier` "Receivable and Payable Accounts", required, default `customer`, string "Partner's" |
| `reconciled` | Boolean, default False, string "Include Settled Items" |
| `amount_currency` | Boolean, string "With Currency", `groups="base.group_multi_currency"` |

`result_selection` maps to `account_id.account_type`: `customer` to `asset_receivable`, `supplier` to `liability_payable`, `customer_supplier` to both.

**Report model** `report.odomate_account_ledger_reports.report_partner_ledger`; report action `action_report_odomate_partner_ledger` "Partner Ledger", template `odomate_account_ledger_reports.report_partner_ledger`, landscape.

1. Items: the base filter, plus `account_id.account_type` in the mapped types, plus `partner_id` set, plus `partner_id` in `partner_ids` when given, plus `reconciled` equal to False unless "Include Settled Items" is ticked.
2. Order `partner_id, date, move_name, id`; blocks print in partner `display_name` order.
3. Columns: Date (`date`) · Journal (`journal_id.code`) · Account (`account_code` and `account_name`) · Entry (`move_name`) · Reference (`ref`) · Label (`name`) · Debit · Credit · Balance (running, per partner, starting at zero) · Currency (`amount_currency` with `currency_id`, only when "With Currency" is ticked and the item's currency differs from the company's).
4. Totals per partner: total debit, total credit, closing balance, and **"Amount owed"**, the sum of `amount_residual` over the printed items. The report's own totals are the same four sums.
5. A part-paid invoice prints at its own debit and credit, with its payment on its own row, so the partner's closing balance is what is still outstanding.
6. There is no partner-less block: items without a `partner_id` are excluded and belong to the general ledger.

**Printing from the partner.** The action `action_odomate_partner_ledger_print` "Partner Ledger" opens this dialog from the Print menu of a customer or vendor: `binding_model_id` `base.model_res_partner`, `binding_type` `report`, `group_ids` `account.group_account_manager`, `account.group_account_user` and `account.group_account_readonly`, target new, context defaulting `partner_ids` to the selected records, `result_selection` to `customer_supplier` and `reconciled` to True.

---

## 5. The aged partner balance

**Dialog** `odomate.account.aged.partner.wizard`, `_description` "Aged Partner Balance", `_odomate_report_xmlid = 'odomate_account_ledger_reports.action_report_odomate_aged_partner'`.

| Field | Definition |
|---|---|
| `date_to` | Inherited, made **required**, default today, relabelled **"As of Date"** |
| `period_length` | Integer, required, default 30, string "Period Length (days)" |
| `result_selection` | As on the partner ledger, default `customer` |
| `partner_ids` | Many2many `res.partner`, string "Partners" |

`date_from` and `journal_ids` are invisible here and carry no value: the ageing covers everything up to the as-of date, in every journal of the company. `_odomate_check_filter` extension: `period_length` of zero or less → "The period length must be at least one day."; no `date_to` → "Set the date the ageing is measured at."

**Report model** `report.odomate_account_ledger_reports.report_aged_partner_balance`; report action `action_report_odomate_aged_partner` "Aged Partner Balance", template `odomate_account_ledger_reports.report_aged_partner_balance`, landscape.

1. Items: the base filter with no `date_from` and `date_to` equal to the as-of date **D**, plus `account_id.account_type` in the mapped types, plus `partner_id` in `partner_ids` when given. Items with no `partner_id` are kept.
2. **The residual as it stood on D**, per item: `balance`, minus the `amount` of every `account.partial.reconcile` whose `debit_move_id` is that item, plus the `amount` of every partial whose `credit_move_id` is that item, counting only partials whose `max_date` is on or before D. Every partial for every printed item is fetched in **one** search. An item whose residual is zero at `company.currency_id`'s rounding is dropped. The live field `amount_residual` is **not** used here: it is the residual today, not on D.
3. **Due date** is `date_maturity` when set, otherwise the item's `date`. **Age** is D minus the due date, in whole days.
4. Buckets, with P being `period_length`:

| Column | Rule | Label |
|---|---|---|
| Not due | age ≤ 0 | "Not due" |
| 1 | 1 ≤ age ≤ P | "1-P" |
| 2 | P+1 ≤ age ≤ 2P | "P+1 - 2P" |
| 3 | 2P+1 ≤ age ≤ 3P | "2P+1 - 3P" |
| 4 | 3P+1 ≤ age ≤ 4P | "3P+1 - 4P" |
| 5 | age > 4P | "+4P" |

**The column labels and the column amounts are produced from this one table, from the same numbers.** With P of 30 the labels read "Not due", "1-30", "31-60", "61-90", "91-120", "+120"; an item whose age is exactly 0 is **Not due**, one whose age is exactly 30 is in **1-30**, one whose age is 121 is in **+120**.

5. Rows: one per partner, in `display_name` order, with items carrying no partner gathered into a last row labelled **"Unknown Partner"**. A partner whose six columns are all zero is dropped. Columns: Partner · Not due · the five buckets · Total, the row's own sum.
6. A totals row closes the report: each of the six columns summed, and the grand total.
7. **No currency conversion anywhere.** Every figure derives from `balance` and is already in `company.currency_id`.

**Two preset actions** open the same dialog and the same view with the partner kind fixed: `action_odomate_aged_receivable` "Aged Receivable" defaults `result_selection` to `customer`, `action_odomate_aged_payable` "Aged Payable" defaults it to `supplier`; both set the context key `odomate_hide_result_selection`, which the view reads to hide the field.

---

## 6. The tax report

**Dialog** `odomate.account.tax.report.wizard`, `_description` "Tax Report", `_odomate_report_xmlid = 'odomate_account_ledger_reports.action_report_odomate_tax_report'`. It carries the five shared fields and nothing more, with `date_from` and `date_to` made **required**, defaulting to the first day of the current month and to today.

**Report model** `report.odomate_account_ledger_reports.report_tax_report`; report action `action_report_odomate_tax_report` "Tax Report", template `odomate_account_ledger_reports.report_tax_report`, portrait.

1. Taxes: every `account.tax` whose `company_id` is the chosen company, `active` is True and `type_tax_use` is `sale` or `purchase`, in `sequence, id` order. **Only the chosen company's taxes are listed.**
2. A tax that has `children_tax_ids` is represented by **its children, each listed under the parent's `type_tax_use`**; the group itself is not a row. A tax without children is its own row.
3. Per row: **Tax amount** is the sum of `balance` over the base filter narrowed to items whose `tax_line_id` is that tax; **Net amount** is the sum of `balance` over the base filter narrowed to items whose `tax_ids` contain that tax. Each measure is obtained in one grouped read covering every tax at once, not one query per tax.
4. **Signs.** In the **Sales** section both figures are multiplied by −1; in the **Purchases** section both are kept as they are. A credit note therefore **reduces** its section. **No figure is ever passed through an absolute value.**
5. Layout: two sections, "Sales" and "Purchases", each a table of **Tax · Net · Tax amount** in tax sequence, with a section total for the two money columns. A row whose net and tax are both zero at `company.currency_id`'s rounding is omitted. A section with no row prints "No tax movement in this period."

---

## 7. The journals audit

**Dialog** `odomate.account.journal.audit.wizard`, `_description` "Journals Audit", `_odomate_report_xmlid = 'odomate_account_ledger_reports.action_report_odomate_journal_audit'`.

| Field | Definition |
|---|---|
| `journal_ids` | Inherited, made **required** on this dialog, defaulting to the `sale` and `purchase` journals of the current company |
| `sort_selection` | Selection `date` "Date" / `move_name` "Journal Entry Number", required, default `move_name`, string "Entries Sorted by" |
| `amount_currency` | Boolean, string "With Currency", `groups="base.group_multi_currency"` |

**Report model** `report.odomate_account_ledger_reports.report_journal_audit`; report action `action_report_odomate_journal_audit` "Journals Audit", template `odomate_account_ledger_reports.report_journal_audit`, landscape.

1. One section per selected journal, journals in their own `_order`, `sequence, type, code`.
2. Items: the base filter narrowed to that journal, ordered `date, move_name, id` or `move_name, date, id` according to `sort_selection`.
3. Columns: Entry (`move_name`) · Date (`date`) · Account (`account_code` and `account_name`) · Partner (`partner_id.display_name`) · Label (`name`) · Debit · Credit · Currency, the last gated on `base.group_multi_currency`.
4. Totals per journal: total debit and total credit.
5. A **tax declaration** table follows each journal's items: for every tax appearing in that journal's items, **Tax · Base amount · Tax amount**, computed exactly as in section 6 — two grouped reads scoped to the journal — under the same sign rule, sales journals negated and every other journal kept, with a totals row. The block is omitted for a journal whose items carry no tax.

---

## 8. The journal-entry printout

An `ir.actions.report` on **`account.move`** with no dialog: `action_report_odomate_journal_entry` "Journal Entry", `report_type` `qweb-pdf`, `report_name` and `report_file` `odomate_account_ledger_reports.report_journal_entry`, `print_report_name` "Journal Entry - " followed by the record's `name` or its id, `binding_model_id` `account.model_account_move`, `binding_type` `report`, `group_ids` `account.group_account_manager`, `account.group_account_user` and `account.group_account_readonly`. Portrait, no paper format override. It prints any number of selected entries, **one page each**.

**Report model** `report.odomate_account_ledger_reports.report_journal_entry` runs `_odomate_check_report_access()` and returns the entries; each page takes its company from that entry's own `company_id`.

- Layout: the standard external layout, one page per entry.
- Header: `name`, the journal, `date`, `partner_id`, `ref` and the label of `state`.
- Items: every line of `line_ids` whose `display_type` is not `line_section`, `line_subsection` or `line_note`, in `sequence, id` order. Columns: Account (`account_code` and `account_name`) · Label (`name`) · Partner · Analytic, gated on `analytic.group_analytic_accounting` and rendered from `analytic_distribution` · Debit · Credit · Currency, gated on `base.group_multi_currency`.
- Totals row: the sum of `debit` and the sum of `credit`, in the entry's own `company_id.currency_id`. They are equal for any posted entry.
- **`account.move.line` carries no `analytic_account_id` field in Odoo 19.** The analytic column reads `analytic_distribution`.

---

## 9. The two ledger list screens

Two `ir.actions.act_window` on `account.move.line`, both `view_mode` `list,pivot,graph`, both with `search_view_id` `account.view_account_move_line_filter`, both domained to `display_type` not one of `line_section`, `line_subsection`, `line_note`.

| Action | Name | `view_id` | Context |
|---|---|---|---|
| `action_odomate_account_ledger_by_account` | "Journal Items by Account" | `account.view_move_line_tree_grouped_general` | `search_default_group_by_account`, `search_default_posted` |
| `action_odomate_account_ledger_by_partner` | "Journal Items by Partner" | `account.view_move_line_tree_grouped_partner` | `search_default_group_by_partner`, `search_default_posted`, `search_default_trade_receivable`, `search_default_trade_payable`, `search_default_unreconciled` |

The filter names above — `group_by_account`, `group_by_partner`, `posted`, `trade_receivable`, `trade_payable`, `unreconciled` — are the ones Odoo 19's journal-item search view defines. Both screens are this module's own actions; **no core action, menu or view is modified, re-sequenced or re-labelled.**

---

## 10. Rules every report obeys

| Rule | Contract |
|---|---|
| Currency | Every figure is in `company.currency_id`. **No conversion is ever performed.** The optional Currency column shows the item's own `amount_currency` and `currency_id`, and only where they differ from the company's. Comparisons against zero, and money cells, use `company.currency_id` |
| The company on the page | The dialog's `company_id`, or for the entry printout the entry's `company_id`. **Every template receives that company in its values and never reads `res_company`**, which the framework sets to the reader's own active company |
| Reading rights | **No `sudo()` anywhere in this module.** Every figure is read as the printing user, so access rights and record rules apply to the PDF exactly as they do on screen |
| Writes | **None.** Nothing outside the module's own transient dialogs is created, changed or deleted, so every report runs unaffected in a locked period |
| Queries | `search`, grouped reads and `read` only. **No raw SQL, no cursor execution, no string-built conditions.** `account.move.line` has no `_query_get` method in Odoo 19 and none is written |

---

## 11. Views

Use `list`, never the legacy element name. No kanban, no JavaScript, no assets, no `static/src` beyond the Apps Store description files.

- **`view_odomate_account_report_filter_form`**, on `odomate.account.report.filter`: a group holding `target_move` as a radio, `date_from` and `date_to`; then a group holding `journal_ids` with the many2many-tags widget, creation disabled, placeholder "All journals", and `company_id` gated on `base.group_multi_company`; a footer with **Print** (`action_odomate_print`, highlighted) and **Cancel**.
- **Each dialog's own form** inherits that view with `mode="primary"`, because the model differs, and targets only the two stable anchors, the `journal_ids` node and the `target_move` node:
  - *General ledger:* after `journal_ids` — `account_ids`, `partner_ids`, and `analytic_account_ids` gated on `analytic.group_analytic_accounting`, all many2many-tags; after `target_move` — `sortby` and `display_account` as radios, then `initial_balance`.
  - *Partner ledger:* after `journal_ids` — `partner_ids`; after `target_move` — `result_selection` as a radio, `reconciled`, `amount_currency`.
  - *Aged partner balance:* after `target_move` — `result_selection` as a radio, hidden on the context key `odomate_hide_result_selection`, then `period_length`; `date_from` and `journal_ids` hidden; `date_to` relabelled "As of Date" and required.
  - *Tax report:* `date_from` and `date_to` required; nothing added. *Journals audit:* after `target_move` — `sort_selection` as a radio and `amount_currency`; `journal_ids` required.
- **QWeb templates:** `report_filter_header` plus one document template per report, each wrapping the html container and the internal layout — except the journal entry, which uses the external layout. Money cells use the monetary widget with `company.currency_id`; dates go through the framework's date formatter. **Output directives are `t-out`; the deprecated escape directive and the raw directive are never used.** Long text is contained with fixed table layout and word breaking in CSS — **no string is ever truncated in Python**. Every column heading is plain text in the template, never assembled by concatenation, so the extractor picks it up.

---

## 12. Menus

Everything here must be reachable by an accounting **Administrator without "Show Full Accounting Features"** — a user holding `account.group_account_manager` and **not** `account.group_account_user`. A menu placed under a parent that user cannot see is a defect.

| xml id | Label | Parent xml id | Sequence | Action |
|---|---|---|---|---|
| `menu_odomate_account_reports_audit` | Audit Reports | **`account.menu_finance_reports`** | 30 | — (folder) |
| `menu_odomate_general_ledger` | General Ledger | `menu_odomate_account_reports_audit` | 10 | `action_odomate_general_ledger_wizard` |
| `menu_odomate_journal_audit` | Journals Audit | `menu_odomate_account_reports_audit` | 20 | `action_odomate_journal_audit_wizard` |
| `menu_odomate_partner_ledger` | Partner Ledger | **`account.account_reports_partners_reports_menu`** | 10 | `action_odomate_partner_ledger_wizard` |
| `menu_odomate_aged_partner_balance` | Aged Partner Balance | **`account.account_reports_partners_reports_menu`** | 20 | `action_odomate_aged_partner_wizard` |
| `menu_odomate_aged_receivable` | Aged Receivable | **`account.account_reports_partners_reports_menu`** | 30 | `action_odomate_aged_receivable` |
| `menu_odomate_aged_payable` | Aged Payable | **`account.account_reports_partners_reports_menu`** | 40 | `action_odomate_aged_payable` |
| `menu_odomate_tax_report` | Tax Report | **`account.account_reports_taxes_and_fiscal_menu`** | 10 | `action_odomate_tax_report_wizard` |
| `menu_odomate_ledger_by_account` | Journal Items by Account | **`account.account_reports_management_menu`** | 30 | `action_odomate_account_ledger_by_account` |
| `menu_odomate_ledger_by_partner` | Journal Items by Partner | **`account.account_reports_management_menu`** | 40 | `action_odomate_account_ledger_by_partner` |

**Every menu in that table carries `groups="account.group_account_manager,account.group_account_user,account.group_account_readonly"`.**

`account.account_reports_partners_reports_menu` (Reporting › Partner Reports) and `account.account_reports_taxes_and_fiscal_menu` (Reporting › Taxes & Fiscal) hold no visible child today and so do not appear; they appear for this Administrator as soon as this module puts a child under them.

**Forbidden parents.** `account.account_reports_legal_statements_menu` (Reporting › Statement Reports) requires `account.group_account_basic`, and `account.menu_finance_entries` (Accounting) has its own group: both are invisible to this Administrator, and **neither may parent anything in this module**. The module also claims **no** top-level menu under `account.menu_finance`.

**Dialog actions**, each on its own dialog model, `view_mode` `form`, `target` new, named as in the table above: `action_odomate_general_ledger_wizard` on `view_odomate_general_ledger_wizard_form`; `action_odomate_partner_ledger_wizard` on `view_odomate_partner_ledger_wizard_form`; `action_odomate_aged_partner_wizard` on `view_odomate_aged_partner_wizard_form`; `action_odomate_tax_report_wizard` on `view_odomate_tax_report_wizard_form`; `action_odomate_journal_audit_wizard` on `view_odomate_journal_audit_wizard_form`. `action_odomate_aged_receivable` and `action_odomate_aged_payable` reuse the aged view as in section 5, and `action_odomate_partner_ledger_print` reuses the partner-ledger view, bound to `res.partner` as in section 4.

---

## 13. Security

**Invent no group.** Use the core accounting groups only, spelled exactly.

| Model | `account.group_account_manager` | `account.group_account_user` | `account.group_account_readonly` |
|---|---|---|---|
| `odomate.account.report.filter` | read, write, create | read, write, create | read, write, create |
| each of the five dialogs | read, write, create | read, write, create | read, write, create |

- **No `unlink` right on any model**: the records are transient and the framework's own vacuum clears them.
- **`account.group_account_invoice` alone receives nothing** — no access right, no menu, no Print binding. So does `base.group_user`.
- **No `ir.rule`.** Every model here is transient and holds no company data; the company is enforced in `_odomate_check_filter`, which requires `company_id` to be among the user's allowed companies, and in every report's filter, which pins `company_id` to the chosen company. (A stated departure from the suite convention on record rules, which governs persistent models.)
- **Every `_get_report_values` calls `_odomate_check_report_access()` before anything else**, so no report renders for a user who may not read accounting data. Its refusal reads "Only accounting users can print accounting reports."
- **This module creates no `res.groups` record and writes no `user_ids`, `implied_ids` or `privilege_id`. The strings `base.user_admin` and `base.user_root` appear nowhere in the module** — not in `security/`, not in `data/`, nowhere. Tests create their own users.
- Every refusal is a `UserError` or `AccessError` raised in Python with a translated message. **The module adds no database check, unique or exclusion constraint.**

---

## 14. Packaging

**Languages.** Ship `i18n/uk.po`, `pl.po`, `de.po`, `es.po`, `fr.po` and `pt_BR.po` from an `en_US` source — exactly six files. Each covers every user-visible string: model descriptions, field labels, selection labels, menu labels, action names, the Print and Cancel buttons, every `UserError` and `AccessError` message, **and every heading, column title, section title and label inside all six QWeb templates**, including "Opening Balance", "Amount owed", "Not due", "Unknown Partner", "Tax Declaration", "Sales", "Purchases" and "No tax movement in this period." Mark every Python-sourced entry `#. odoo-python`. **Ship no `.pot` file** — delete any the build produces. Each `.po` must pass `msgfmt -c`.

**Tests.** Under `tests/`, **never imported from the module's `__init__.py`**. One test method per acceptance criterion that runs without a browser, named for its criterion, **each with a docstring naming the criterion number it covers**. Tests build their own fixtures with fixed past dates: a second company with its own journals and accounts, partners, customer invoices, a payment part-paying one of them, a tax and a credit note, a draft and a cancelled entry, an Administrator without full accounting features, an Invoicing-only user, a read-only accounting user, and a user holding `analytic.group_analytic_accounting`. Report content is asserted by rendering to HTML and reading the figures the criterion names; one further test renders a PDF as a smoke test. Asserted exactly: the opening balance for a balance-sheet account and for an income account; the aged buckets at ages 0, 1, P, P+1 and 4P+1; the residual as of a date where a payment falls after it; the tax signs with a credit note.

**Demo data.** The module ships **no demo data** — no `demo` key in the manifest, no `demo/` folder. These are reports over whatever the database already holds, and every criterion is exercised by records the tests create.

**Manifest.** `images` is `['static/description/icon.png']`, and that file ships. No settings page, no `res.config.settings` extension, no scheduled job, no initialisation hook, no persistent model, no model without a table behind it.

---

## 15. Acceptance criteria

The actor is an accounting **Administrator without "Show Full Accounting Features"** — holding `account.group_account_manager`, not `account.group_account_user` — unless a criterion says otherwise. Dates are illustrative; tests use fixed past dates.

1. Each of the five dialogs shows `company_id`, `target_move` and a **Print** button returning a PDF. `company_id` defaults to the current company and cannot be set outside `allowed_company_ids`; a start date after the end date is refused; a journal of another company is refused. The general ledger, partner ledger, tax report and journals audit dialogs also show `date_from`, `date_to` and `journal_ids`; the aged dialog shows `date_to` as "As of Date" and hides `date_from` and `journal_ids`.
2. Leaving `journal_ids` empty prints every journal of the chosen company; picking one prints only its items.
3. With `date_from` 1 March 2026 and `date_to` 31 March 2026, an item dated 28 February 2026 is absent and one dated 31 March 2026 present; an empty `date_from` includes everything up to `date_to`.
4. With `target_move` `posted` an item on a draft entry is absent and with `all` present; an item on a cancelled entry is absent under both.
5. Every PDF header shows the company name, the date range, the journals (or "All journals") and the entry selection. Printing for a second company while working in the first gives that second company's name, amounts and currency.
6. The general ledger prints accounts in `code` order; each row shows date, journal, partner, reference, entry, label, debit, credit and a running balance; each block ends with its debit, credit and closing balance, and the report with the totals of the accounts printed.
7. `initial_balance` without a `date_from` is refused with "Set a start date to print an opening balance."; with a start date each account opens with an **"Opening Balance"** row and the running balance starts from it.
8. With `date_from` 1 March 2026 in a January-to-December fiscal year, a bank account's opening balance is everything booked before 1 March 2026, while a sales-income account's is January and February 2026 only.
9. `display_account` `movement` hides an account with no item in the period; `not_zero` hides one whose closing balance is zero; `all` shows both.
10. Filling `account_ids` with two accounts, `partner_ids` with one partner, or `analytic_account_ids` with one analytic account narrows the general ledger to matching items.
11. `sortby` `sort_journal_partner` reorders the rows inside each account by journal then partner; `sort_date` orders them by date.
12. For a user holding `analytic.group_analytic_accounting` the general ledger and the journal-entry printout show an Analytic column carrying each item's distribution as names and percentages; without that group the column is absent from both.
13. The partner ledger prints one block per partner with a running balance, a total per partner and a report total; `result_selection` `customer_supplier` includes receivable and payable items.
14. A customer invoice of 1,000 part-paid by 400 prints as two rows — 1,000 and 400 — and that partner's totals read a closing balance of 600 and **"Amount owed"** of 600. Once fully paid both rows disappear, unless `reconciled` is ticked.
15. From a customer's Print menu, **Partner Ledger** opens the dialog with that partner preselected, `result_selection` `customer_supplier` and `reconciled` True, and prints their statement.
16. The aged balance as of 8 February 2026 with `period_length` 30 shows the headings "Not due", "1-30", "31-60", "61-90", "91-120", "+120"; an item due 9 January 2026 falls in **1-30**, one due 8 February 2026 under **Not due**, one due 1 January 2025 under **+120**. A `period_length` of 15 relabels all six headings and moves the figures to match. Zero or less is refused.
17. An invoice paid on 20 February still shows its full amount in an aged balance measured as of 8 February.
18. **Aged Receivable** opens for receivable accounts only and **Aged Payable** for payable accounts only, with `result_selection` hidden on both.
19. The aged balance's bottom row totals each of the six columns, the Total column sums across each row, items with no partner appear as **"Unknown Partner"**, and a partner whose six columns are all zero is absent.
20. The tax report prints a **Sales** and a **Purchases** section, each listing its taxes with a net and a tax amount and a section total. In a two-company database only the chosen company's taxes are listed, and a tax with `children_tax_ids` appears as its children under the parent's `type_tax_use`, not as the group.
21. A 1,000 sale with a 15% tax and a 200 credit note carrying the same tax print as net 800 and tax 120 — the credit note reduces both figures, and neither is an absolute value.
22. The journals audit prints one section per selected journal with its debit and credit totals and a tax declaration table of base and tax amounts under the same sign rule; `sort_selection` `date` and `move_name` both reorder the items.
23. Print on a journal entry gives one page carrying `name`, journal, `date`, partner, `ref`, state and every line, with equal debit and credit totals; printing three entries at once gives three pages.
24. **Journal Items by Account** opens grouped by account showing posted items; **Journal Items by Partner** opens grouped by partner showing unreconciled trade receivable and payable items. Both can be re-filtered and re-grouped, and both offer list, pivot and graph.
25. Signed in as the Administrator without full accounting features: **Audit Reports** with General Ledger and Journals Audit under Reporting; Partner Ledger, Aged Partner Balance, Aged Receivable and Aged Payable under Reporting › Partner Reports; Tax Report under Reporting › Taxes & Fiscal; the two list screens under Reporting › Management — and every one of those screens opens and prints.
26. Signed in as an **Invoicing-only** user holding `account.group_account_invoice` alone: none of those menus is visible, the partner carries no Partner Ledger print entry and the journal entry no Journal Entry print entry, and opening any dialog or rendering any report is refused. A user holding `account.group_account_readonly` can open and print every report.
27. Printing any report for a period closed by a lock date produces the same PDF and changes nothing: after a pass over all six reports, no journal entry, journal item, partner or account has been created, modified or deleted.
28. With Odoo in Ukrainian, the menus, the dialogs, the error messages and every heading and label inside all six PDFs appear in Ukrainian. The same check passes in Polish, German, Spanish, French and Brazilian Portuguese.
