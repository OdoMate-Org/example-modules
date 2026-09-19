========================
Accounting Audit Reports
========================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge2| image:: https://img.shields.io/badge/Odoo-19.0-875A7B.png
    :alt: Odoo 19.0

|badge1| |badge2|

Six printable accounting audit reports — General Ledger, Partner Ledger, Aged
Partner Balance, Tax Report, Journals Audit and a per-entry Journal Entry
printout — plus two ready-made journal-item screens. Every report is built on a
single shared, read-only filter over ``account.move.line``: company, period,
journals and posted-or-all entries. The module reads through the Odoo ORM only,
uses no ``sudo()``, writes nothing outside its own wizard records, and adds no
field to any standard model.

**Table of contents**

.. contents::
   :local:

Features
========

* **General Ledger** with a correct opening balance: balance-sheet accounts open
  with everything booked before the start date, income and expense accounts with
  the fiscal year to date only.
* **Partner Ledger** with a per-partner running balance and an *Amount owed*
  total, printable straight from a contact's Print menu.
* **Aged Partner Balance** whose residual is rebuilt from the reconciliation
  history, so it stays correct when printed for a past date. Aged Receivable and
  Aged Payable presets included.
* **Tax Report** with honest signs — the Sales section is negated rather than
  made absolute, so credit notes reduce the figures.
* **Journals Audit** with one section per journal and a tax declaration recap.
* **Journal Entry** printout, one page per selected entry, each in its own
  company's letterhead and currency.
* **Journal Items by Account / by Partner** list-pivot-graph screens over
  ``account.move.line``.

Installation
============

#. Copy ``odomate_account_ledger_reports`` into your addons path.
#. Go to *Apps* and click *Update Apps List*.
#. Search for *Accounting Audit Reports* and click *Activate*.

Dependencies: ``account`` and ``analytic``, both shipped with Odoo Community.

Configuration
=============

None. The module has no settings page, no scheduled job, no init hook and no
demo data. It is usable immediately after install.

Usage
=====

* *Accounting → Reporting → Audit Reports* — General Ledger, Journals Audit
* *Accounting → Reporting → Partner Reports* — Partner Ledger, Aged Partner
  Balance, Aged Receivable, Aged Payable
* *Accounting → Reporting → Taxes* — Tax Report
* *Accounting → Reporting → Management* — Journal Items by Account / by Partner
* *Journal Entries → Print → Journal Entry* — per-entry printout
* *Contacts → Print → Partner Ledger* — customer or vendor statement

The complete user guide, with worked numerical examples, is in
``doc/USER_GUIDE.md``.

Security
========

Access is limited to three existing Odoo groups:
``account.group_account_manager``, ``account.group_account_user`` and
``account.group_account_readonly``. The module defines no group of its own and
grants nothing to ``account.group_account_invoice`` or ``base.group_user``.

Known issues / Roadmap
======================

* All figures are in the company currency; no conversion is performed.
* PDF output only — use the two journal-item screens for spreadsheet exports.
* The Aged Partner Balance covers all journals of the company by design.
* The module does not extend Odoo's dynamic ``account.report`` engine, so these
  reports do not appear in its variant selector.

Languages
=========

User interface and all six PDF templates are translated into Ukrainian, Polish,
German, Spanish, French and Brazilian Portuguese. Per-language user guides ship
as ``doc/USER_GUIDE.<lang>.md``.

Bug Tracker
===========

Please report issues to support@odomate.pro.

Credits
=======

Authors
-------

* OdoMate

Maintainers
-----------

This module is maintained by OdoMate.

* Website: https://odomate.pro
* Support: support@odomate.pro
