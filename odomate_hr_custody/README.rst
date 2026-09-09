===========================
Employee Custody Management
===========================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge2| image:: https://img.shields.io/badge/odoo-19.0-875A7B.png
    :alt: Odoo 19.0

|badge1| |badge2|

Track every piece of company property handed to an employee — laptops, phones,
tools, access cards, vehicle keys — from inside the Employees app. The module
adds a register of custody items, a request / approval / return workflow with
automatic overdue chasing, and a printable handover document.

**Table of contents**

.. contents::
   :local:

Features
========

* **Custody item register** with photo, description, optional product link and
  a live *Available / Held by* status shown on a kanban board.
* **Request workflow**: ``draft`` → ``waiting_approval`` → ``approved`` →
  ``returned``, with ``refused`` as the terminal branch. Sequence-generated
  references in the form ``CUST/00001``.
* **One holder at a time**, enforced inside the approval method itself and
  backed by a partial unique database index, so imports, RPC calls and
  concurrent approvals hit the same guard as the button.
* **Return-date extensions**: the holder proposes a new date, which is held
  apart from the promised date until an officer approves it. Refusing an
  extension records a separate reason and restores the original date.
* **Daily overdue reminders** at 05:00 to the holder, using the same email
  template as the manual *Send Reminder* button, with a direct link to the
  record.
* **QWeb PDF handover document** on Odoo's external layout, printable from the
  form and from a list selection, safe against missing employee details.
* **Employee smart buttons** for total custody records and items currently held.
* **Multi-company record rules** on both the register and the requests.
* Ukrainian (``uk``) translation included.

Installation
============

The module depends on ``hr``, ``mail``, ``product`` and
``odomate_hr_employee_info_06092026_2``. Odoo installs any missing dependency
automatically.

#. Copy ``odomate_hr_custody`` into your addons path.
#. Restart the Odoo service.
#. Go to *Apps*, click *Update Apps List*, search for
   **Employee Custody Management** and press *Install*.

Configuration
=============

No configuration is required. The install creates:

* the ``odomate.hr.custody`` sequence (prefix ``CUST/``, 5-digit padding, no reset);
* the **Custody: Return Reminder** email template;
* the **Custody: Daily Return Reminders** scheduled action, running daily at 05:00.

Access rights reuse the standard HR groups — the module defines no groups of
its own:

* ``base.group_user`` — read-only on items; read, create and edit **own**
  requests only, enforced by the record rule
  ``[('employee_id.user_id', '=', user.id)]``.
* ``hr.group_hr_user`` — full CRUD except delete, plus approve / refuse /
  extension-approve / return.
* ``hr.group_hr_manager`` — the above, plus delete and the Analysis screen.

The approval actions raise ``AccessError`` in Python for users outside
``hr.group_hr_user`` — the buttons are not merely hidden.

Usage
=====

*Employees → Custody* offers three menu items: **Custody Requests**, **Items**
and **Analysis**.

See ``doc/USER_GUIDE.md`` for the full walkthrough, and
``doc/USER_GUIDE.uk.md`` for the Ukrainian version.

Known limitations
=================

* No quantities, stock moves or Inventory integration — one register row is one
  physical item.
* No condition, damage, maintenance or repair tracking.
* No financial value, depreciation or insurance fields.
* Single-level approval only; no escalation beyond the holder.
* No barcode scanning and no on-screen signature capture.
* The reminder schedule is fixed at daily 05:00 and is not exposed in Settings.

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

This module is maintained by OdoMate — https://odomate.pro
