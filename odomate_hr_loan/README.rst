==============
Employee Loans
==============

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge3| image:: https://img.shields.io/badge/odoo-19.0-875A7B.png
    :target: https://www.odoo.com
    :alt: Odoo 19.0

|badge1| |badge2| |badge3|

Employee loan requests with an approval-time repayment schedule and automatic
recovery from payslips through the OCA ``payroll`` module.

HR records a loan for an employee, builds a fixed instalment schedule, and
routes it through ``Draft → Submitted → Approved → Closed``. Once approved,
each instalment falling due in a payslip period is added to that payslip as
an input line and marked *Recovered* when the payslip is confirmed.

Features
========

* Loan requests with amount, purpose, instalment count and flat interest.
* Approval-time repayment schedule stored as real instalment records, with
  rounding remainders on the final instalment.
* Automatic payslip recovery through a shipped ``LOAN_REPAY`` salary rule
  and matching rule input; several instalments in one period collapse into
  one payslip line.
* Idempotent recovery keyed off payslip confirmation, not computation.
* Defer an instalment (and every later one) by one month, with a reason
  posted to the chatter.
* Settle a loan early: remaining instalments are cancelled, never deleted,
  so the schedule still reads as history.
* Per-company policy: optional one-loan-at-a-time rule and a maximum loan
  amount ceiling, both enforced at approval.
* Record rules so employees see only their own loans, plus multi-company
  isolation on both models.

Installation
============

#. Copy ``odomate_hr_loan`` into your Odoo addons path.
#. Update the apps list.
#. Install **Employee Loans**.

Dependencies (``hr``, ``payroll``, ``mail``, ``base_setup``) install
automatically.

Configuration
=============

**Required one-time step.** The module ships a salary rule named
**Loan Repayment** (code ``LOAN_REPAY``) in the ``DED`` category, but does
*not* attach it to any salary structure — it cannot know which structure
your company uses. Add it once:

#. Go to **Payroll → Configuration → Salary Structures**.
#. Open the structure your employees are paid on.
#. Add the **Loan Repayment** rule and save.

Optional policy settings live under **Employees → Loans → Loan Policy**:
*Allow Multiple Running Loans* and *Maximum Loan Amount* (0 = no cap).

Known limitations
=================

* The salary rule must be attached to your salary structure manually.
* No affordability check beyond the flat maximum-amount ceiling.
* Net pay is not protected — it can reach zero or go negative.
* No accounting entries are posted; the instalment table is stored so a
  future accounting module can read it.
* Nothing is triggered when an employee leaves the company.
* Flat interest only; deferring moves dates, never amounts.

Documentation
=============

See ``doc/USER_GUIDE.md`` for the full guide, and ``doc/USER_GUIDE.uk.md``
for the Ukrainian translation.

Bug Tracker
===========

Please report issues to OdoMate support at support@odomate.pro.

Credits
=======

Authors
-------

* OdoMate

Maintainers
-----------

This module is maintained by OdoMate — https://odomate.pro
