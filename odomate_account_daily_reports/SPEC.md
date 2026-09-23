# SPEC.md — the specification this module was generated from

This is the specification the module in this folder was generated from, exactly as it was
submitted to OdoMate. It is written at the level of an Odoo business analyst: it names the
menus, dialogs, groups and reports the user sees and states the acceptance criteria in
Section 12. Everything in `models/`, `report/`, `views/`, `security/` and `tests/` was
produced by OdoMate from it.

**Provenance, stated plainly.** This specification was written by the OdoMate team.

**What was verified before publication.** Installed on a freshly created Odoo 19 Community
database with demo data and the six shipped languages loaded, alongside its dependency
`odomate_account_ledger_reports`, the module installs with no errors and its 25 tests pass —
no failure, no error, and no ERROR or CRITICAL line in either log. The three books were
rendered in all six languages and the figures compared version against version. It ships no
`.pot`, no demo data, defines no group of its own, adds no field to any standard model, uses
no raw SQL and no elevated access, and writes nothing to the accounts.

**Four generated versions, and no hand correction to the code.** Version 1 was generated from
this document. Version 2 came from one enhancement round that moved three calls into the
sibling module's internals back inside the fence Section 2 draws, and renumbered the test
docstrings against Section 12. Version 3 came from a second enhancement round that restored
the printed header's entry-selection label, which version 2 had left in English in all six
languages. Version 4 came from a third enhancement round that took the report's own grand
total out of the table's repeating footer, so it prints once, where the report ends, set off
from the day and account totals rather than looking like one of them. Nothing in the module
was written or corrected by hand. The publication changes in
this folder are the store listing page (`static/description/index.html`) and this file.

**Known gaps, disclosed rather than fixed.** Measured against this document, the published
version departs from it in these places. None changes a figure.

- Four option labels in the Cash Book and Bank Book dialogs differ from the wording in
  Section 3.1. Those two dialogs offer "All Accounts", "With Movements" and "With Balance Not
  Equal To Zero" where this document writes "All", "With movements" and "With balance not
  equal to 0", and "Journal and Partner" where it writes "Journal & Partner". A reader meets
  these labels only in those two dialogs: none of them is printed on any of the three books,
  whose header carries company, entries, period and journals. Each option behaves as this
  document specifies.
- The day book's table carries an eighth column heading, "Difference". It is empty on every
  item row and filled only on the day-total and report-total rows, where Section 5.5 lists
  seven row columns and Section 5.6 puts the difference in the per-day totals.
- In the cash book and the bank book an account's heading can print at the foot of a page with
  that account's own rows overleaf: neither book carries a page-break rule on that heading,
  where the day book's day headings do. No figure is affected.
- Section 2 lists `_odomate_line_domain(date_field='date', date_from=None, date_to=None)` as
  the sibling member that supplies the base journal-item domain. That method is record-bound,
  and Sections 5.1 and 6.1 of this same document require the report to rebuild the filter from
  `data`, where no dialog record exists. The module therefore calls the options-bound form of
  the same rule at two places. This is an imprecision in this document, not in the module.
- Section 12 criterion 7's second sentence cannot be satisfied by any correct module. It asks
  that a day book narrowed to the sales journal alone show days whose difference is not zero;
  every journal item carries its own move's journal and every posted move balances, so such a
  day book necessarily has debit equal to credit on every day. The criterion's first clause —
  every journal, posted entries, every day's difference zero — is correct and was measured
  true. This is an error in this document, not in the module.
- Five criteria of Section 12 — 3, 5, 13, 18 and 20 — have no dedicated test of their own in
  the shipped suite. They were measured by hand instead. Leaving them uncovered was a
  deliberate decision taken when the test docstrings were renumbered, and is recorded here so
  the gap is not mistaken for full coverage.
- Two criteria admit two readings, and the reading has not been settled. Criterion 1 says the
  company field "cannot be set to a company the user is not allowed to work in": a foreign
  company can be written to the field and is refused when Print is pressed, not before.
  Criterion 14 says `movement` hides an account with no item in the period: an account holding
  an opening balance and no movement is shown when an opening balance was asked for and hidden
  when it was not.

**Not verified:** no dialog was clicked by hand in a rendered browser session. Every criterion
was measured through the database and against rendered report content; two PDFs were rendered
end to end. Criterion 12's "whatever the company's fiscal year" limb was measured on one
fiscal-year boundary placement, and the read-only user's ability to print was measured as
report values rather than as a rendered PDF.

---

# Daily Books — Specification (Level 2: Odoo Business Analyst)

**Module:** `odomate_account_daily_reports` · **Name:** "Daily Books: Day Book, Cash Book, Bank Book" · **Target:** Odoo 19.0 Community
**Version:** `19.0.1.0.0` · **License:** LGPL-3 · **Category:** Accounting · **Application:** False · **Author:** OdoMate
**Website:** https://odomate.pro · **Support:** support@odomate.pro · **Images:** `['static/description/icon.png']`
**Depends on:** `account` and `odomate_account_ledger_reports`. The second is a hard dependency — this module shares that module's filter dialog, its page header, its paper format and its report menu folder, and cannot be installed without it.

---

## 1. Business goal

Three printouts Odoo Community does not ship. The **day book** hands an auditor everything booked on a given day. The **cash book** is the cash account's own ledger with a running balance, so the last figure is what should be in the drawer. The **bank book** is the same for bank and credit-card accounts, opened from last period's close. All three are asked for the same way as the general ledger, printed as PDF, and scoped to one company.

**This module writes nothing.** It creates, changes, posts and deletes no accounting record of any kind, so all three books print in a locked period. It adds no persistent model: the only records it defines are transient dialogs.

---

## 2. What this module takes from `odomate_account_ledger_reports`

Only the members listed here are used. Nothing else in that module may be referenced, subclassed or extended — not its five dialogs' own fields, not its row-builder methods, not its `report.odomate_account_ledger_reports.*` report models, and no template of its other than its page-header block.

| Member | Kind | How this module uses it |
|---|---|---|
| `odomate.account.report.filter` | model | The base of all three dialogs here, each by `_inherit` on that name together with its own `_name` |
| `company_id`, `date_from`, `date_to`, `journal_ids`, `target_move` | fields | Inherited unchanged. `journal_ids` keeps its meaning — **empty means every journal of `company_id`** — narrowed here by journal type |
| `_odomate_journals()` | method | The resolved journal set, then filtered by `_odomate_journal_types` |
| `_odomate_state_domain()` | method | Posted-only or posted-and-draft, with cancelled entries never included |
| `_odomate_line_domain(date_field='date', date_from=None, date_to=None)` | method | The base journal-item domain of all three books |
| `_odomate_check_filter()` | method | Extended by each dialog here with a call to `super()` |
| `_odomate_report_data()` | method | Extended by each dialog here with a call to `super()` |
| `_odomate_print(report_xmlid=None)` and the class attribute `_odomate_report_xmlid` | method | The Print button's body; each dialog sets `_odomate_report_xmlid` to its own report action |
| `action_odomate_print()` | method | The Print button itself |
| `_odomate_options_from_data(data)` | model method | Rebuilds the filter on the report side from `data` |
| `_odomate_check_report_access()` | model method | Called first in every `_get_report_values` here |
| The opening balance `odomate_account_ledger_reports` derives — everything booked to an account before a start date, for a company, a journal set and an entry selection | model method | The opening balance of the cash book and the bank book |
| The filter dialog form view `odomate_account_ledger_reports` defines | view | The `inherit_id` of all three dialog forms |
| `//field[@name='journal_ids']` and `//field[@name='target_move']` | xpath anchors | The only two anchors used in those three inherited views |
| The page-header block `odomate_account_ledger_reports` defines, rendered at the top of each document | QWeb template | Called at the top of all three report documents |
| The landscape paper format `odomate_account_ledger_reports` defines | `report.paperformat` | The `paperformat_id` of all three report actions |
| The "Audit Reports" menu folder `odomate_account_ledger_reports` places under Invoicing › Reporting | menu | The parent of all three menu items |

This module defines **no filter field of its own on the shared five** and duplicates none of the above.

---

## 3. Data model — three dialogs and one shared base

Every model here is a `TransientModel`. There is no persistent model, no `res.config.settings` extension, no scheduled job and no hook.

### 3.1 `odomate.account.liquidity.book.wizard` — the shared base

A concrete `TransientModel` with `_inherit = 'odomate.account.report.filter'`, `_description` "Liquidity Book". It is given **no action and no menu**; it exists so the cash and bank dialogs share their fields, their view and their report builder. It is internal to this module and no sibling module may depend on it.

| Field | Definition |
|---|---|
| `display_account` | Selection `all` "All" / `movement` "With movements" / `not_zero` "With balance not equal to 0", required, default `movement`, string "Display Accounts" |
| `sortby` | Selection `sort_date` "Date" / `sort_journal_partner` "Journal & Partner", required, default `sort_date`, string "Sort by" |
| `initial_balance` | Boolean, string "Include Opening Balance" |
| `amount_currency` | Boolean, string "With Currency", `groups="base.group_multi_currency"` |

Two class attributes, not fields: **`_odomate_journal_types`**, the journal types the book covers, and **`_odomate_account_types`**, the account types it treats as liquidity.

`journal_ids` keeps its inherited definition and gains, in each concrete dialog's own view, a domain limiting it to journals of the dialog's `company_id` whose `type` is in that dialog's `_odomate_journal_types`.

**`_odomate_journals()` is overridden** to return the result of `super()` filtered to journals whose `type` is in `_odomate_journal_types`. So an empty `journal_ids` yields every journal of the right kind for that company, and a filled one yields the journals of the right kind among those chosen.

**`_odomate_check_filter()` is extended**, after `super()`, with two refusals in this order:

1. any journal in `journal_ids` whose `type` is not in `_odomate_journal_types` → `UserError` **"This book only covers %(kinds)s journals."**, where the substitution is the translated literal **"cash"** for the cash book and **"bank and credit card"** for the bank book;
2. `initial_balance` set with no `date_from` → `UserError` **"Set a start date to print an opening balance."**

**`_odomate_report_data()` is extended** to add `display_account`, `sortby`, `initial_balance` and `amount_currency` to the dictionary handed to the report.

### 3.2 The two liquidity dialogs

Both inherit `odomate.account.liquidity.book.wizard` and declare their own `_name`. Neither adds a field.

| Model | `_description` | `_odomate_journal_types` | `_odomate_account_types` | `_odomate_report_xmlid` |
|---|---|---|---|---|
| `odomate.account.cash.book.wizard` | "Cash Book" | `cash` | `asset_cash` | `odomate_account_daily_reports.action_report_odomate_cash_book` |
| `odomate.account.bank.book.wizard` | "Bank Book" | `bank`, `credit` | `asset_cash`, `liability_credit_card` | `odomate_account_daily_reports.action_report_odomate_bank_book` |

**The bank book covers the `credit` journal type as well as `bank`.** Odoo 19's `credit` type is "Credit Card" — a liquidity journal whose money belongs in a bank book, and whose accounts are of `account_type` `liability_credit_card`. The account types follow the journal types: the cash book treats only `asset_cash` accounts as liquidity, the bank book treats `asset_cash` and `liability_credit_card`.

### 3.3 `odomate.account.day.book.wizard` — the day book dialog

`_inherit = 'odomate.account.report.filter'` with its own `_name`, `_description` "Day Book", and `_odomate_report_xmlid` set to `odomate_account_daily_reports.action_report_odomate_day_book`.

`date_from` and `date_to` are inherited but made **required** on this dialog, each defaulting to `fields.Date.context_today` — never to a value evaluated when the module is imported.

**It adds no other field.** There is no `display_account`, no `sortby`, no `initial_balance`, no `amount_currency` and no account selector. `journal_ids` keeps the inherited meaning without any type narrowing: empty means **every journal of the company**, of every `type` — `sale`, `purchase`, `cash`, `bank`, `credit` and `general`.

`_odomate_check_filter()` is extended, after `super()`, with one refusal: a missing `date_from` or `date_to` → `UserError` **"Set both a start and an end date for the day book."** `_odomate_report_data()` is inherited unchanged.

---

## 4. Which accounts a liquidity book covers

**One rule, on the shared report mixin, used by both liquidity books and by nothing else.** `_odomate_book_accounts(journals, account_types, lines)` returns an `account.account` recordset ordered by `code`, being the union of:

- the `default_account_id` of those journals;
- their `suspense_account_id`;
- the accounts returned by `_get_journal_inbound_outstanding_payment_accounts()` on those journals;
- the accounts returned by `_get_journal_outbound_outstanding_payment_accounts()` on those journals;
- **plus every account whose `account_type` is in `account_types` that the period's items in those journals actually touch** — read from the `account_id` of `lines`.

The result is then narrowed to the chosen company: the account's `company_ids` must contain that company.

**The last term is what makes the book work on a real database.** A journal whose `default_account_id` and `suspense_account_id` were never configured, and which has no payment-method-line accounts, still prints its book, because the accounts its own entries used are picked up. The first four terms are why an account with no movement in the period can still be listed under `display_account` `all`.

Never use the payment-method-line relations directly; the two journal helper methods named above are the supported route to the outstanding-payment accounts.

---

## 5. The day book

**Report model** `report.odomate_account_daily_reports.report_day_book`, whose `_get_report_values(docids, data=None)`:

1. Calls `_odomate_check_report_access()` on `odomate.account.report.filter` first, then `_odomate_options_from_data(data)` on the same model to rebuild company, journals, dates and `target_move`.
2. **Items.** `_odomate_line_domain()` rebuilt from those options — the company, `display_type` not in `line_section` / `line_subsection` / `line_note`, `journal_id` in the resolved journals, the state domain, `date` at or after `date_from` and at or before `date_to`. **One `search` over `account.move.line`**, never one query per day.
3. **Order:** `date, journal_id, move_name, id`, passed explicitly, because `account.move.line` has `_order` `date desc, move_name desc, id` and would otherwise arrive newest first. Days therefore come out **oldest first**, and within a day the items sit grouped by journal and then by entry.
4. **Grouping.** Rows are bucketed by `date` from that one ordered recordset. Days are taken from the data, never from a calendar walk over the range, so **a day with no item produces no block at all**.
5. **Columns of a row:** Journal (`journal_id.code`), Entry (`move_name`), Partner (`partner_id.display_name`), Reference (`ref`), Label (`name`), Debit (`debit`), Credit (`credit`), and the optional Currency column (`amount_currency` with `currency_id`). The date is the block heading, not a column.
6. **Per day, three totals:** total `debit`, total `credit`, and **`difference` = debit − credit**.
7. **Per report:** the same three totals summed over the days shown.
8. **No opening balance and no running balance anywhere in this report.** A day book is a listing of what was booked, not an account's history; a running total across a mixture of journals and accounts would not be a meaningful figure, and no rule in this document produces one.
9. When nothing matches, the values carry an empty list of days and the template prints **"No entries in this period."** instead of a table.

**The difference is the day book's own self-check.** Every posted entry balances, so over *every* journal of one company, with `target_move` `posted`, each day's debit equals its credit and the difference reads zero down the whole report; a day that does not is a day to look at. Narrowed to one journal the difference is genuinely non-zero and simply reports that journal's net movement for the day.

---

## 6. The cash book and the bank book

**One shared Python mixin** — an `AbstractModel` named `report.odomate_account_daily_reports.report_liquidity_book_mixin`, which is not itself a report — and two concrete report models inheriting it:

| Report model | `_odomate_journal_types` | `_odomate_account_types` | Title |
|---|---|---|---|
| `report.odomate_account_daily_reports.report_cash_book` | `cash` | `asset_cash` | "Cash Book" |
| `report.odomate_account_daily_reports.report_bank_book` | `bank`, `credit` | `asset_cash`, `liability_credit_card` | "Bank Book" |

`_get_report_values(docids, data=None)`:

1. `_odomate_check_report_access()` first, then the options from `_odomate_options_from_data(data)`; the journals are the options' journals filtered to `_odomate_journal_types`.
2. **Items.** The base domain from `_odomate_line_domain()` narrowed to those journals, plus a term restricting `account_id` to the accounts from `_odomate_book_accounts`. The account set is resolved from an unrestricted first pass over the period's items in those journals, then the account term is applied — two searches, no more.
3. **Order.** `sortby` `sort_date` gives `date, move_name, id`; `sortby` `sort_journal_partner` gives `journal_id, partner_id, date, id`. Ordering on a Many2one follows the comodel's own `_order`.
4. **Opening balance**, only when `initial_balance` is ticked: one `_read_group` over the opening-balance domain `odomate_account_ledger_reports` derives for this company, `date_from`, those journals and `target_move`, plus the same `account_id` term, grouped by `account_id`, aggregating `debit`, `credit` and `balance`. Both books' accounts are balance-sheet accounts whose `include_initial_balance` is True, so the opening figure is **everything booked to that account before `date_from`** — these accounts carry money forward and do not reset at the fiscal year end.
5. **Which accounts are printed**, from the `_odomate_book_accounts` set in `code` order: `all` prints every account in the set; `movement` prints an account with at least one item in the period; `not_zero` prints an account whose opening plus period debit less period credit is not zero at the company currency's rounding, tested with `is_zero` on `company.currency_id`.
6. **Columns of a row:** Date (`date`), Journal (`journal_id.code`), Entry (`move_name`), Partner (`partner_id.display_name`), Reference (`ref`), Label (`name`), Debit (`debit`), Credit (`credit`), **Balance**, and the optional Currency column.
7. **The Balance column is a true running balance**, per account: each row is the previous row's balance plus that row's `debit` less its `credit`, starting from the opening balance, or from zero when no opening balance was asked for. It is never the opening balance added to every row, and it is never read from the core `cumulated_balance` field, whose value depends on the caller's ordering.
8. **Totals.** Per account: `debit`, `credit`, and a closing balance computed as opening plus the summed `debit` less the summed `credit` — summed, never read off the last row. Per report: the summed debit, credit and closing balance of the accounts shown.
9. **The opening-balance row** prints the label **"Opening Balance"** with its debit, credit and balance, and leaves date, journal, entry, partner, reference and currency empty.

---

## 7. Accounting rules — exact

| Rule | Contract |
|---|---|
| **Which items** | `account.move.line` is the only data source. `display_type` not in `line_section`, `line_subsection`, `line_note`; `company_id` equal to the dialog's `company_id`; `journal_id` in the book's journals |
| **Which journals — day book** | Every journal of the company, of every `type` (`sale`, `purchase`, `cash`, `bank`, `credit`, `general`), unless the user picks some |
| **Which journals — cash book** | `type` equal to `cash` only |
| **Which journals — bank book** | `type` in `bank` and `credit` |
| **Which accounts — day book** | **Every account.** A day book is a journal listing, not an account listing; there is no account filter on the dialog and none in the domain |
| **Which accounts — cash and bank book** | `_odomate_book_accounts`: the journals' `default_account_id`, `suspense_account_id`, inbound and outbound outstanding-payment accounts, **plus** every account of the book's `_odomate_account_types` carrying an item in those journals in the period; narrowed to accounts whose `company_ids` contains the company |
| **Posted or all** | `target_move` `posted` means `parent_state` is `posted`; `target_move` `all` means `parent_state` is `draft` or `posted`. **A cancelled entry never appears in any of the three books** |
| **What "All entries" changes** | *Every* figure: the rows, each day's debit, credit and difference, each account's debit and credit, the running balance, the closing balance — **and the opening balance**, because the opening balance `odomate_account_ledger_reports` derives is taken with the same `target_move`. A draft entry dated before `date_from` shifts the whole balance column beneath it |
| **Dates** | `date` everywhere. `date_maturity` is not used by this module |
| **Opening balance — day book** | **None.** Neither an opening balance nor a running balance exists in the day book |
| **Opening balance — cash and bank book** | The opening balance `odomate_account_ledger_reports` derives, for this company, `date_from`, those journals and `target_move`, per account. Everything booked before `date_from`, whatever the fiscal year. Never shown without `date_from` |
| **Running balance** | Cash and bank books only, per account; starts at the opening balance or zero; each row adds `debit` less `credit` |
| **Closing balance** | Opening plus summed `debit` less summed `credit`, rounded with `company.currency_id` |
| **Day totals** | Per day: summed `debit`, summed `credit`, and **difference = debit − credit**, over the items shown for that day |
| **Report totals** | Day book: the three day totals summed over the days shown. Liquidity books: debit, credit and closing balance summed over the accounts shown |
| **Ordering — day book** | `date, journal_id, move_name, id`, always passed explicitly. Days ascending; the user has no choice |
| **Ordering — cash and bank book** | `sort_date` gives `date, move_name, id`; `sort_journal_partner` gives `journal_id, partner_id, date, id` |
| **Account ordering** | By `code`, following `account.account`'s own `_order`. **`code` is company-dependent** — an account may carry a code in one company and none in another — so it is read with the chosen company in the environment |
| **Multi-currency** | Every printed figure is in `company.currency_id` and **nothing is ever converted**. The Currency column shows the item's own `amount_currency` and `currency_id`, printed **whenever `currency_id` differs from `company.currency_id`, negative amounts included** — a payment out of 500 in a foreign currency prints −500 and its currency, not a blank. The cell is always rendered so the columns never misalign; it is empty when there is nothing to show. The column carries `groups="base.group_multi_currency"`, and on the two liquidity books it also requires `amount_currency` to be ticked |
| **Rounding** | Comparisons to zero use `is_zero` on `company.currency_id`; display uses the monetary widget with `company.currency_id` |
| **The company on the page** | The dialog's `company_id`, passed into the template values as `company`. The templates never read `res_company` and never read `env.company`, because QWeb injects `res_company` as the *active* company, not the one being printed |
| **Empty result** | Day book: "No entries in this period." Liquidity books: an account with no row is governed by `display_account`; when no account survives, the same sentence |
| **Writes** | **None.** This module creates, changes and deletes nothing outside its own transient dialogs, and is therefore unaffected by lock dates |
| **Analytic** | **No analytic column in any of the three books.** `account.move.line` has no `analytic_account_id` field in Odoo 19, and an analytic distribution is not a meaningful column on a day or cash listing |

---

## 8. Views

Use `list`, never `tree`. No kanban view, no JavaScript, no `static/src`.

All three dialog forms set `inherit_id` to the filter dialog form view `odomate_account_ledger_reports` defines **and `mode="primary"`**, because the model differs from the inherited view's model. They use **only** the two stable anchors `//field[@name='journal_ids']` and `//field[@name='target_move']`.

- **`view_odomate_day_book_wizard_form`:** `date_from` and `date_to` become required. Nothing is added at either anchor beyond that.
- **`view_odomate_cash_book_wizard_form` and `view_odomate_bank_book_wizard_form`:** after `//field[@name='target_move']`, add `sortby` with `widget="radio"`, `display_account` with `widget="radio"`, then `initial_balance` and `amount_currency`. At `//field[@name='journal_ids']`, set the type-narrowed domain and the placeholder — "All cash journals" and "All bank and credit card journals" respectively.

**Every field that drives a report is visible and editable.** No field that the report reads is hidden, and no required field is made invisible.

**QWeb.** Three documents, each wrapping `web.html_container` around `web.internal_layout`, each opening with a call to the page-header block `odomate_account_ledger_reports` defines, followed by its own title heading, and each holding the whole document inside **one** page div — the header block and the table included. The templates `report_cash_book` and `report_bank_book` are thin wrappers that set the title and call a shared `report_liquidity_book_body`. Amount cells use `t-out` with the monetary widget and `company.currency_id`; date cells use `format_date`. `t-esc` is deprecated in Odoo 19 and `t-raw` is forbidden. Overflowing text is handled with CSS such as a fixed table layout and word breaking, never by slicing strings in Python. Totals are computed in Python and printed; they are never accumulated inside a loop. Closing footers are `tfoot`.

---

## 9. Menus and navigation

All three menus must be reachable by an accounting **Administrator without "Show Full Accounting Features"**, whose visible root is the Invoicing app.

**The parent of all three is the "Audit Reports" folder `odomate_account_ledger_reports` already places under `account.menu_finance_reports`.** This module creates **no menu folder of its own**: a second, near-identical folder holding three printouts of the same kind would sit two rows from the first.

| Menu | Label | Sequence | Action |
|---|---|---|---|
| `menu_odomate_day_book` | "Day Book" | 30 | `action_odomate_day_book_wizard` |
| `menu_odomate_cash_book` | "Cash Book" | 40 | `action_odomate_cash_book_wizard` |
| `menu_odomate_bank_book` | "Bank Book" | 50 | `action_odomate_bank_book_wizard` |

**Every one of the three carries `groups="account.group_account_manager,account.group_account_user,account.group_account_readonly"`** — the same list the access rights grant, so no user is ever offered a menu that cannot open.

No top-level menu is claimed under `account.menu_finance`. No core menu is hidden, replaced, re-sequenced or re-labelled.

**Dialog actions.** `action_odomate_day_book_wizard` "Day Book", `action_odomate_cash_book_wizard` "Cash Book" and `action_odomate_bank_book_wizard` "Bank Book", each on its own wizard model, `view_mode` `form`, `target` `new`, with the matching form view above and no binding.

**Report actions**, all `report_type` `qweb-pdf`, all with `paperformat_id` set to the landscape paper format `odomate_account_ledger_reports` defines, and each with `report_name` and `report_file` naming its template in this module:

| Report action | Title | Model | Template |
|---|---|---|---|
| `action_report_odomate_day_book` | "Day Book" | `odomate.account.day.book.wizard` | `report_day_book` |
| `action_report_odomate_cash_book` | "Cash Book" | `odomate.account.cash.book.wizard` | `report_cash_book` |
| `action_report_odomate_bank_book` | "Bank Book" | `odomate.account.bank.book.wizard` | `report_bank_book` |

Each dialog's footer carries a **"Print"** button calling `action_odomate_print` and a **"Cancel"** button.

---

## 10. Security

**Invent no group and add no feature switch.** Use the core accounting groups only.

| Model | `account.group_account_manager` | `account.group_account_user` | `account.group_account_readonly` |
|---|---|---|---|
| `odomate.account.liquidity.book.wizard` | read, write, create | read, write, create | read, write, create |
| `odomate.account.cash.book.wizard` | read, write, create | read, write, create | read, write, create |
| `odomate.account.bank.book.wizard` | read, write, create | read, write, create | read, write, create |
| `odomate.account.day.book.wizard` | read, write, create | read, write, create | read, write, create |

- **No `unlink` right on any of the four models:** transient records are cleared by the ORM's own vacuum.
- **`account.group_account_invoice` alone gets nothing** — no access line and no menu.
- **No `ir.rule`.** Every model here is transient and holds no company data of its own. The company is enforced in the inherited `_odomate_check_filter`, which refuses a `company_id` outside the user's allowed companies, and in every domain.
- **Every `_get_report_values` calls `_odomate_check_report_access()` first**, so a PDF cannot be rendered by a user who may not read accounting data.
- **No `sudo()` anywhere in this module.** Every figure is read as the printing user, so access rights apply to the PDF exactly as they do on screen.
- **No record grants any group to any user.** The module creates no `res.groups` record and writes no `user_ids`, `implied_ids` or `privilege_id`, and **the strings `base.user_admin` and `base.user_root` appear nowhere in the module** — not in the security files, not in data, not in a test. Tests create their own users.

---

## 11. Packaging

**Languages.** Ship `i18n/uk.po`, `pl.po`, `de.po`, `es.po`, `fr.po` and `pt_BR.po` from an `en_US` source, each covering every user-visible string: model descriptions, field labels and selection labels, every menu, action, button and dialog title, all four messages, **and every heading, column title and label inside the three QWeb templates** — including "Opening Balance", "Difference", "Total", "Day total", "Account total", "Balance", "Currency" and "No entries in this period." Column headings are plain heading text in the templates so the extractor picks them up; none is built by string concatenation in Python, and the one message with a placeholder takes its two substitutions from translated literals rather than from a joined list. Mark every Python-sourced entry `#. odoo-python`. **Ship no `.pot` file** — delete any the build generates. Each `.po` must pass `msgfmt -c`.

**Tests.** One test method per acceptance criterion 1–21 that runs without a browser, named `test_criterion_XX_<slug>`, **each with a docstring naming the criterion number it covers**. No test is imported from the module's `__init__.py`. Tests use fixed past dates.

**Tests build their own data, because a stock database does not contain it.** Assume none of the following exists and create all of it: a second company; a **cash** journal, and a bank journal both with and without a configured `default_account_id`; liquidity accounts of `account_type` `asset_cash` and `liability_credit_card`; a partner; entries in several journals across several days; **a draft entry dated before the start date**; **a cancelled entry**; and **a foreign-currency item, including one whose `amount_currency` is negative**. Draft entries, cancelled entries, cash journals and foreign-currency items are exactly what a demo database lacks, and no criterion may rely on finding them.

Report content is asserted on rendered HTML through `_render_qweb_html` on `ir.actions.report`, parsed for the figures a criterion names; one further test renders a PDF through `_render_qweb_pdf` as a smoke test. Tests cover four users: an accounting Administrator without "Show Full Accounting Features", an Invoicing-only user, a read-only accounting user, and a user carrying `base.group_multi_currency`.

**Demo data. The module ships none, and this is explicit, not an omission:** no `demo` key in the manifest and no demo folder. These are printouts over whatever the database already holds, and every acceptance criterion is exercised by records the tests create.

**Other packaging rules.** No raw SQL of any kind — no cursor execution, no string-built conditions, no query rewriting; everything is `search`, `_read_group` and `read`. Any count uses `search_count`, never the length of a limited batch. Every refusal is a `UserError` with a translated message, so the user reads our sentence; **no database `CHECK`, `UNIQUE` or `EXCLUDE` constraint** is added. No `pre_init_hook`, `post_init_hook` or `uninstall_hook`.

---

## 12. Acceptance criteria

The tester is an accounting **Administrator without "Show Full Accounting Features"**, unless a criterion says otherwise. Dates are examples; tests use fixed past dates.

1. Each of the three dialogs shows `company_id`, `date_from`, `date_to`, `journal_ids` and `target_move`, and a **Print** button that returns a PDF. `company_id` defaults to the user's current company and cannot be set to a company the user is not allowed to work in.
2. Leaving `journal_ids` empty prints every journal the book covers for that company; picking one journal prints only its items. The **Cash Book** offers only `cash` journals, the **Bank Book** only `bank` and `credit` journals, and the **Day Book** every journal of the company. Choosing a journal of the wrong `type` is refused with "This book only covers %(kinds)s journals."
3. With `date_from` 1 March 2026 and `date_to` 31 March 2026, an item dated 28 February 2026 is absent and one dated 31 March 2026 is present.
4. With `target_move` `posted` a draft entry is absent; with `target_move` `all` it is present. **A cancelled entry is absent from both, in all three books.**
5. Every PDF's header shows the company name, the period, the journals and the entry selection; printing for a second company while working in the first gives the **second** company's name, amounts and currency on the page.
6. The **day book** prints one block per day, oldest day first; each row shows Journal, Entry, Partner, Reference, Label, Debit and Credit; each day ends with its debit total, its credit total and the difference; the report ends with the totals for the whole range.
7. With every journal of the company and `target_move` `posted`, **every day's difference is zero**. Narrowing the same day book to the sales journal alone gives days whose difference is not zero, and the report still prints correctly.
8. A day with no item is not printed. A range with no item in any journal prints **"No entries in this period."** and no table.
9. The day book shows **no opening balance and no running balance** anywhere — no such column, no such row and no such total.
10. The **cash book** prints one block per account in `code` order; each movement shows Date, Journal, Entry, Partner, Reference, Label, Debit, Credit and a **running Balance**; each block ends with the account's debit, credit and closing balance; the report ends with the totals of the accounts shown. The **bank book** does the same over `bank` and `credit` journals and their `asset_cash` and `liability_credit_card` accounts.
11. Ticking `initial_balance` with no `date_from` is refused with "Set a start date to print an opening balance." With a `date_from`, each account opens with an **"Opening Balance"** row and the running balance starts from that figure.
12. For a bank account with 5,000 booked before 1 March 2026, a book started on 1 March 2026 opens at 5,000 — whatever the company's fiscal year, and whether or not the fiscal year boundary falls inside the period before it.
13. With `target_move` `all`, a **draft** entry of 200 dated before `date_from` raises that account's opening balance by 200, and with it every running balance beneath it and the closing balance. With `target_move` `posted` the same entry changes nothing.
14. `display_account` `movement` hides an account with no item in the period; `not_zero` hides an account whose closing balance is zero at the company currency's rounding; `all` shows both.
15. `sortby` `sort_journal_partner` reorders the movements inside each account by journal then partner; `sort_date` orders them by date.
16. A bank journal whose **`default_account_id` was never configured**, with no `suspense_account_id` and no payment-method-line accounts, still prints its bank book, because every account of a liquidity `account_type` that its entries touched in the period is included.
17. To a user holding `base.group_multi_currency`, with `amount_currency` ticked, each row can show the item's own `amount_currency` and `currency_id`, and only when that `currency_id` differs from `company.currency_id`. **A payment out of 500 in a foreign currency shows −500 and its currency, not a blank cell**, and a row with nothing to show still renders the cell so the columns stay aligned. No figure anywhere is converted.
18. The three menu entries sit under **Invoicing › Reporting › Audit Reports**, in the "Audit Reports" folder `odomate_account_ledger_reports` defines, alongside the General Ledger; all three are visible to an Administrator without "Show Full Accounting Features"; and **no second report folder is created by this module**.
19. Signed in as a user holding **`account.group_account_invoice` only**, none of the three menus is visible and none of the three dialogs can be opened by its address. A user holding `account.group_account_readonly` can open and print all three.
20. Printing any of the three for a locked period produces the PDF and changes nothing: no journal entry, journal item or any other record is created, modified or deleted anywhere.
21. Installing this module installs `odomate_account_ledger_reports` first; all three dialog forms inherit the filter dialog form view `odomate_account_ledger_reports` defines; all three report actions use the landscape paper format `odomate_account_ledger_reports` defines; all three documents render the page-header block `odomate_account_ledger_reports` defines; and the opening balance of the cash and bank books is produced by the way `odomate_account_ledger_reports` derives an opening balance, not by one built here.
22. With Odoo in Ukrainian, the menus, the dialogs, the refusal messages and the headings and labels inside all three PDFs appear in Ukrainian. The same check passes in **Polish, German, Spanish, French and Brazilian Portuguese**.
