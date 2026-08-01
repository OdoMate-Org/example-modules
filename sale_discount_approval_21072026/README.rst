=====================
Sale Discount Approval
=====================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

|badge1|

Apply a single order-level or invoice-level discount (percent or fixed amount)
that fans out to every line, with an optional company-level approval gate for
large discounts.

Features
========

* Order-level and invoice-level discount, by **Percent** or fixed **Amount**,
  spread evenly across all lines.
* Informational **Discount** total on orders, invoices, printed documents and
  the customer portal.
* Optional **two-step approval**: an order whose average line discount exceeds a
  company limit moves to a *Waiting Approval* state and must be approved by a
  Sales Manager.
* **Approve** / **Reject** buttons restricted to ``sales_team.group_sale_manager``.
* Discount type, rate and amount are carried over automatically when the order
  is invoiced.
* Negative rates act as a surcharge (no floor validation).
* ``account.invoice.report`` gains a **Discount %** column for pivot/graph views.

Configuration
=============

The discount inputs require the standard **Discounts** feature
(``sale.group_discount_per_so_line``). Enable it under
*Settings → Sales → Pricing → Discounts*, then turn on **Sale Discount Approval**
in the same page and set the approval limit.

Usage
=====

See ``doc/USER_GUIDE.md`` (English) and ``doc/USER_GUIDE.uk.md`` (Ukrainian) for
step-by-step instructions and worked examples.

Known limitations
=================

* Amount discounts are approximate, not exact-to-the-cent, when lines carry
  different taxes.
* The approval average is unweighted and includes 0% and negative lines.
* ``margin_test`` is populated only when the *Sale Margin* app is installed.

Credits
=======

Author: **OdoMate** — https://www.odomate.com

License: LGPL-3.
