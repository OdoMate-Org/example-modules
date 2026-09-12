=============================
OdoMate HR Overview Dashboard
=============================

.. |badge1| image:: https://img.shields.io/badge/maturity-Production%2FStable-green.png
    :target: https://odoo-community.org/page/development-status
    :alt: Production/Stable
.. |badge2| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge3| image:: https://img.shields.io/badge/odoo-19.0-875A7B.png
    :alt: Odoo 19.0

|badge1| |badge2| |badge3|

A read-only management overview for Odoo 19 Employees. One screen answers five
questions - headcount, who joined, who left, who is off today, and the turnover
rate - and every figure is clickable, opening the exact list of records it was
counted from. Below the tiles the module ranks absence concentration by the
Bradford factor and collects everything from the wider OdoMate HR suite that is
waiting for an approval.

The module creates no records, grants no security group to anybody, and never
uses ``sudo()``.

**Table of contents**

.. contents::
   :local:

Features
========

* Five clickable figure tiles: Headcount, Joined, Left, Off today, Turnover.
* Drill-down parity - the row count of every opened list equals the figure that
  opened it, because both are built from the same domain in the same call.
* A period selector defaulting to the current calendar year; point-in-time
  figures ignore it and say so on the tile.
* Worked turnover arithmetic shown on screen, not a generic sentence.
* ``odomate.hr.movement`` - SQL view, one row per arrival and per departure,
  with list, graph, pivot and search views. Archived leavers included.
* ``odomate.hr.absence.factor`` - SQL view ranking employees by the Bradford
  factor over approved, finished time off.
* Cross-suite pending approvals, skipped silently when a suite is absent or
  unreadable by the current user.
* Multi-company record rules on both analysis models.

Installation
============

#. Copy ``odomate_hr_dashboard`` into your addons path.
#. Restart the Odoo service.
#. Go to **Apps**, click **Update Apps List**, search for
   *OdoMate HR Overview Dashboard* and click **Install**.

Dependencies (``hr``, ``hr_holidays``, ``web``) install automatically.

Configuration
=============

None required. The module ships no demo data and creates no records - it
reports on the employees and time off already present in the database.

Access is limited to the standard Odoo groups ``hr.group_hr_user`` and
``hr.group_hr_manager``. No new group is defined and none is granted; whoever
already holds an HR group can use the overview the moment it installs.

Usage
=====

Open **Employees > HR Overview**. Adjust the two date inputs to change the
period. Click a tile to open its records; use the four entry points below the
tiles to reach the analysis lists unfiltered.

Full documentation ships with the module:

* ``doc/USER_GUIDE.md`` - English
* ``doc/USER_GUIDE.uk.md`` - Ukrainian

Known issues / Roadmap
======================

* Arrivals depend on ``hr.version.contract_date_start``; employees without one
  never appear as joiners and do not affect the turnover denominator.
* Headcount at a past date is reconstructed from movement rows, not from a
  stored historical snapshot.
* The Bradford figures carry no time window - the search filters select
  employees, not leave date ranges.
* Leave requests in ``validate1`` (second approval pending) are excluded by
  design.

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

This module is maintained by OdoMate - https://odomate.pro
