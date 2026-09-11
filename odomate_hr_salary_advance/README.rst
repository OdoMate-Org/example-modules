=======================
Employee Salary Advance
=======================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge2| image:: https://img.shields.io/badge/odoo-19.0-purple.png
    :alt: Odoo 19.0

|badge1| |badge2|

Record a salary advance request, check it against company policy, disburse it
through a real ``account.payment``, and recover the full outstanding balance on
the next payslip. When the balance reaches zero the advance closes itself.

Features
========

* **Policy-driven eligibility** — a percentage of the monthly wage, an optional
  absolute ceiling, and an on/off switch for holding more than one open advance.
  The four eligibility figures (Monthly Salary, Maximum Allowed, Already
  Outstanding, Available) are computed live on the form.
* **Wage resolved by date** — the wage and the "is there an active contract"
  check both read the ``hr.version`` in force on the request date, so a
  backdated request cannot silently disagree with itself.
* **Real disbursement** — the Pay wizard creates and posts an outbound
  ``account.payment`` to the employee's work contact. If posting fails the whole
  transaction rolls back; no orphaned draft payment is left behind.
* **Automatic payroll recovery** — a ``ADV_DEDUCT`` input line is appended to
  the next payslip, and confirmation writes back whatever that line actually
  says, clamped so an advance can never be over-recovered.
* **Checks enforced in the model** — submit and approve run the same
  ``@api.constrains``, so imports and RPC calls cannot bypass the policy.
* **Multi-company** — company-scoped policy plus a global company record rule.
* **Ukrainian translation** included.

Installation
============

Depends on ``hr``, ``payroll`` (OCA), ``account`` and ``mail``; Odoo installs
any that are missing.

#. Copy the module into your addons path.
#. **Apps → Update Apps List**.
#. Search for *Employee Salary Advance* and click **Install**.

Configuration
=============

#. **Settings → Employees → Salary Advances** — set the maximum percentage, the
   optional ceiling, whether multiple open advances are allowed, and the
   **Salary Advance Journal** (required before any advance can be paid).
#. **Payroll → Configuration → Salary Structures** — add the shipped
   **Salary Advance Deduction** rule (code ``ADV_DEDUCT``) to each structure
   that should recover advances. The module ships the rule but deliberately
   never attaches it for you.

Usage
=====

**Employees → Salary Advances**. Create a request, Submit, Approve, then Pay.
The advance is recovered automatically on the employee's next confirmed
payslip.

Known limitations
=================

* No instalment schedule — the entire outstanding balance goes onto the next
  payslip unless a payroll officer edits the input line by hand.
* No interest, no bank reconciliation, and no accounting entry for the recovery
  leg.
* The "one open advance" rule is a Python check backed by a per-company
  setting, not a database constraint.
* No employee self-service requesting and no approval chain beyond one HR
  officer.

Full documentation: ``doc/USER_GUIDE.md`` (English) and ``doc/USER_GUIDE.uk.md``
(Ukrainian).

Credits
=======

Author
------

* OdoMate — https://odomate.pro

Support
-------

support@odomate.pro
