========================================
Employee Dependants & Identity Documents
========================================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge2| image:: https://img.shields.io/badge/odoo-19.0-875A7B.png
    :alt: Odoo 19.0

|badge1| |badge2|

Adds dependant records, identity document expiry tracking and login-to-employee
integrity to the Odoo 19 Employees app. Employees get a list of dependants with a
single enforced emergency contact, identity and passport scans with a daily
edge-triggered expiry reminder, a computed joining date and a per-company default
notice period on employee versions.

**Table of contents**

.. contents::
   :local:

Features
========

* ``odomate.hr.dependant`` — dependants per employee (name, relationship, phone,
  date of birth, emergency-contact flag), on the HR-only Private Information page.
* ``odomate.hr.relationship`` — editable master list, seeded with Spouse, Father,
  Mother, Son and Daughter.
* One emergency contact per employee, enforced in ``create``/``write`` and backed by
  a partial unique index; the flagged dependant's name and phone are copied onto
  ``hr.employee.emergency_contact`` / ``emergency_phone``.
* Automatic Spouse dependant when ``spouse_complete_name`` and ``spouse_birthdate``
  are both set — idempotent, never duplicated.
* ``identification_expiry_date`` plus multi-file scan attachments for the
  identification reference and the passport.
* Daily ``ir.cron`` that warns each employee exactly once, on the day the configured
  per-company lead time is reached, using editable ``mail.template`` records. Two
  "send now" buttons trigger the same templates on demand.
* ``joining_date`` — stored, read-only, computed as the earliest ``hr.version``
  start date.
* ``notice_period`` on ``hr.version``, defaulted once from the company setting and
  editable by HR Administrators.
* Optional per-company automatic employee creation for every new internal login.

Installation
============

#. Copy ``odomate_hr_employee_info_06092026_2`` into your Odoo addons path.
#. Restart the Odoo service.
#. Open **Apps**, click **Update Apps List**, search for
   *Employee Dependants & Identity Documents* and click **Activate**.

Dependencies ``hr`` and ``mail`` are installed automatically.

Configuration
=============

#. Go to **Settings → Employees → Employee Records** and review the identification
   lead time (14 days), the passport lead time (180 days), the automatic employee
   creation switch and the default notice period (30 days). All four are per company.
#. Go to **Employees → Configuration → Dependant Relationships** to extend the seeded
   relationship list.
#. Optionally adjust **Settings → Technical → Scheduled Actions →
   HR: Identity Document Expiry Warnings** (daily, 05:00 by default).

Usage
=====

Open an employee, switch to **Private Information** and use the **Dependants**
section and the identity blocks. Full documentation, including worked examples for
the expiry cron, is in ``doc/USER_GUIDE.md`` (English) and ``doc/USER_GUIDE.uk.md``
(Ukrainian).

Known issues / Roadmap
======================

* Only the identification reference and the passport are tracked; visas, work permits
  and licences are out of scope.
* No employee self-service screen for dependants.
* The HR Officer read-only restriction on ``notice_period`` is a form-level constraint,
  not a server-side write guard.
* Seeded relationship names are data records on a plain ``Char`` field and are therefore
  not covered by the ``.po`` translations.

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
