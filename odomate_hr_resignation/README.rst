==================================
OdoMate HR Resignation & Clearance
==================================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge2| image:: https://img.shields.io/badge/odoo-19.0-purple.png
    :alt: Odoo 19.0

|badge1| |badge2|

Resignation and exit clearance tracking for the Odoo Employees app. A
resignation is followed from the day notice is given, through manager and HR
approval, across an exit clearance checklist, to the final release of the
employee — and the release is blocked while the ``odomate_hr_custody``
register still shows company property in that employee's hands.

The custody register is read, never written: this module never marks anything
as returned. It re-reads it live at every release attempt rather than trusting
the snapshot taken at HR approval, so the two are allowed to disagree and the
live read always wins.

Features
========

* Full state machine: draft, confirmed, manager approved, clearance, released,
  with refused and withdrawn as terminal branches.
* Notice period read from the employee's current ``hr.version`` and a proposed
  last working day that stops mirroring the moment a human edits it.
* Configurable clearance checklist, with per-company or globally shared items.
* Two independent, distinctly-worded release blockers: outstanding company
  property, and an incomplete checklist.
* Post-release immutability enforced in ``write()``, not merely on the view.
* Daily scheduled action that auto-releases records once the last working day
  has passed and both checks pass — the same checks as the button.
* Exit interview through the standard ``survey.invite`` flow.
* Multi-company record rules on every model; no new security groups.

Installation
============

``odomate_hr_custody`` is a hard dependency; ``hr``, ``mail`` and ``survey``
are pulled in automatically. Install from **Apps**, then update the app list
if the module is not yet listed.

Configuration
=============

* **Settings → Employees → Resignation & Clearance** — turn manager approval
  on or off per company (on by default).
* **Employees → Configuration → Clearance Items** — maintain the checklist
  entries. Five starter items ship with the module, shared across all
  companies.

Usage
=====

Go to **Employees → Resignations**. Full documentation, including a worked
example of the notice-period calculation and the complete permission matrix,
is in ``doc/USER_GUIDE.md``.

Known limitations
=================

* No "reset to proposed" action once the last working day is set manually.
* The linked login is not archived when it is the Odoo superuser or the user
  performing the release; Odoo forbids both writes.
* No settlement, payslip, dismissal workflow, handover-task model,
  exit-interview reporting, self-service or document generation.

Credits
=======

Authors
-------

* OdoMate

Maintainers
-----------

This module is maintained by OdoMate — https://odomate.pro

For support: support@odomate.pro
