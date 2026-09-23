========================================================
Accounting Daily Reports (Day Book, Cash Book, Bank Book)
========================================================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge2| image:: https://img.shields.io/badge/Odoo-19.0-875A7B.png
    :target: https://www.odoo.com
    :alt: Odoo 19.0

|badge1| |badge2|

Three printable daily accounting books for Odoo 19 Community: a **Day Book**
that recaps every journal item of the period day by day, and a **Cash Book**
and **Bank Book** that show liquidity movements per account with an optional
opening balance and a true per-account running balance.

The reports are strictly read-only. They never create, modify or delete a
record, so they are unaffected by lock dates and are safe for a read-only
accountant to run. Everything is read through the Odoo ORM — no raw SQL, no
``sudo()``, and no field added to any standard model.

They build on the shared filter dialog, page header and landscape paper
format of *Accounting Audit Reports* (``odomate_account_ledger_reports``), so
all six reports look and behave consistently.

Features
========

* **Day Book** — one block per calendar day, with per-day debit, credit and
  difference totals. Days without items produce no block.
* **Cash Book** — cash journals, one block per account, ordered by account
  code.
* **Bank Book** — bank and credit card journals, same layout.
* **Opening balance** — optional per-account opening row, computed with the
  same fiscal-year-correct rule as the General Ledger.
* **Running balance** — a genuine per-account running total, row by row.
* **Account resolution** — the liquidity books resolve their accounts from
  each journal's default, suspense and outstanding payment accounts plus the
  liquidity accounts actually touched in the period, so a journal with no
  default account still prints correctly.
* **Multi-currency** — every figure in company currency, with an optional
  column showing each item's own amount in its own currency.
* **Multi-company** — one company per printout, enforced in validation and in
  every domain.

Installation
============

#. Copy ``odomate_account_daily_reports`` into your Odoo addons path.
#. Go to **Apps** and click **Update Apps List**.
#. Search for *Accounting Daily Reports* and click **Install**.

``account`` and ``odomate_account_ledger_reports`` are installed
automatically if they are not present yet.

Usage
=====

Open **Accounting → Reporting → Audit Reports** and pick **Day Book**,
**Cash Book** or **Bank Book**. Set the period, optionally narrow the
journals, then click **Print**.

Full documentation, including a worked numerical example, is in
``doc/USER_GUIDE.md``. Translated guides are available for Ukrainian, Polish,
German, Spanish, French and Brazilian Portuguese.

Known limitations
=================

* PDF and HTML output only — no XLSX or CSV export, no interactive view.
* No drill-down from a printed figure to the underlying entry.
* One company per printout; consolidated multi-company books are not
  supported.
* No currency conversion — foreign-currency items keep their booked
  company-currency value.
* No analytic columns; use the General Ledger of *Accounting Audit Reports*
  for analytic distribution.
* No demo data — the reports print whatever the database already holds.

Credits
=======

Authors
-------

* OdoMate

Maintainers
-----------

* OdoMate — https://odomate.pro
* Support — support@odomate.pro
