==================================
Employee Loans - Accounting Entries
==================================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge2| image:: https://img.shields.io/badge/odoo-19.0-875A7B.png
    :alt: Odoo 19.0

|badge1| |badge2|

The accounting half of Employee Loans. It posts a disbursement entry when a
loan is approved, one recovery entry per instalment as payroll recovers it, and
a settlement entry when a loan is settled early — reading the figures that
``odomate_hr_loan`` already stores and never recalculating them.

The module adds no new models, no menus, no security groups and no demo data:
three fields on the loan, one on the instalment, three per-company defaults, and
two view extensions.

**Table of contents**

.. contents::
   :local:

Installation
============

Requires ``account`` and ``odomate_hr_loan``; without the latter the module
will not install.

#. Copy ``odomate_hr_loan_accounting`` into your addons path.
#. Update the apps list.
#. Install *Employee Loans - Accounting Entries*.

Configuration
=============

Go to *Accounting → Configuration → Settings → Employee Loans* and set:

* **Loan Journal** — bank, cash or miscellaneous. Its *Default Account* must be
  set; it carries the counterpart of every line.
* **Loan Receivable Account** — the asset account holding what employees owe.
* **Loan Interest Income Account** — only needed for loans that carry interest.

Each loan can override the three on its own *Accounting* tab.

Usage
=====

Nothing new to click. Approving a loan, confirming a payslip that recovers an
instalment, and settling a loan early each post their entry automatically. The
*Journal Entries* smart button on the loan opens everything posted for it.

Configuration problems are reported before the loan changes state, naming
exactly what is missing.

Known issues / Roadmap
======================

* No demo data is shipped, deliberately: demo records would depend on a chart
  of accounts the module does not control.
* Loans approved before installation are not backfilled.
* Posted entries are never reversed, unlinked or edited by this module.
* Entries are posted in the company currency only.

Bug Tracker
===========

Report issues to support@odomate.pro.

Credits
=======

Authors
-------

* OdoMate

Maintainers
-----------

This module is maintained by OdoMate — https://odomate.pro
