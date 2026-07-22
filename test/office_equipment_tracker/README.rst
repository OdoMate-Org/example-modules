========================
Office Equipment Tracker
========================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

|badge1|

Track office equipment assigned to employees — who currently holds each
item, its check-out and return dates, and its condition. Manage a simple
status lifecycle (Available, Checked Out, In Repair, Retired) for laptops,
phones, monitors and peripherals.

**Table of contents**

.. contents::
   :local:

Features
========

* Current-holder tracking through a Many2one link to ``hr.employee``.
* Status workflow with Check Out, Return, Send to Repair and Retire actions.
* Automatic check-out and return date handling.
* Serial numbers kept unique across all active (non-retired) equipment.
* Role-based access: Equipment Administrator vs. read-only internal users.
* Per-company data isolation via a record rule.
* 15 realistic demo records covering every status.

Installation
============

#. Copy the ``office_equipment_tracker`` folder into your Odoo addons path.
#. Update the apps list and install **Office Equipment Tracker**.
#. The ``hr`` module is installed automatically as a dependency.

Configuration
=============

Assign the **Equipment Administrator** group (Settings > Users & Companies >
Users) to the people who manage equipment. All other internal users can see
only the equipment currently assigned to them.

Usage
=====

Open **Equipment > All Equipment**, create a record, set a current holder,
and use the status-bar buttons to check out, return, send to repair, or
retire each item. See ``doc/USER_GUIDE.md`` for the full walkthrough.

Bug Tracker
===========

For support, contact support@odomate.pro.

Credits
=======

Authors
~~~~~~~

* OdoMate

Maintainers
~~~~~~~~~~~

This module is maintained by OdoMate (https://odomate.pro).
