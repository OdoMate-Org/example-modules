================
OdoMate HR Suite
================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge2| image:: https://img.shields.io/badge/odoo-19.0-brightgreen.png
    :alt: Odoo 19.0

|badge1| |badge2|

One install for the complete OdoMate HR suite. This is a data-only
meta-module: it declares no models, no fields and no permissions of its own.
Installing it installs the eight member modules listed below, then groups
their menus into an **HR Suite** folder in the Employees app and a second
**HR Suite** folder under **Employees → Configuration**, so the top level of
the Employees app does not grow eight new entries.

What gets installed
===================

+-------------------------------------------+---------------------------------------------+---------------------------------------------------------------------------------------------+
| Module                                    | Title on the Store                          | One line                                                                                    |
+===========================================+=============================================+=============================================================================================+
| ``odomate_hr_employee_info_06092026_2``   | Employee Dependants & Identity Documents    | Family members, dependants and identity document details on the employee record             |
+-------------------------------------------+---------------------------------------------+---------------------------------------------------------------------------------------------+
| ``odomate_hr_documents``                  | Employee Document Expiry Tracking           | Documents that expire, with advance warning and a renewal history                           |
+-------------------------------------------+---------------------------------------------+---------------------------------------------------------------------------------------------+
| ``odomate_hr_custody``                    | Employee Custody Management                 | Company property held by employees, with request, approval and return                       |
+-------------------------------------------+---------------------------------------------+---------------------------------------------------------------------------------------------+
| ``odomate_hr_transfer``                   | Employee Transfer                           | Moves between departments, locations or companies, keeping the history                      |
+-------------------------------------------+---------------------------------------------+---------------------------------------------------------------------------------------------+
| ``odomate_hr_leave_email``                | Time Off Requests by Email                  | Turns an incoming email into a time-off request                                             |
+-------------------------------------------+---------------------------------------------+---------------------------------------------------------------------------------------------+
| ``odomate_hr_notices``                    | HR Notices, Announcements & Acknowledgements| Company announcements and personal reminders, with a count in the top bar                   |
+-------------------------------------------+---------------------------------------------+---------------------------------------------------------------------------------------------+
| ``odomate_hr_dashboard``                  | Employee Turnover & Absence Dashboard       | Headcount, turnover, absence concentration and pending approvals in one screen              |
+-------------------------------------------+---------------------------------------------+---------------------------------------------------------------------------------------------+
| ``odomate_hr_resignation``                | Employee Resignation & Clearance            | Resignation requests, a clearance checklist and an exit interview                           |
+-------------------------------------------+---------------------------------------------+---------------------------------------------------------------------------------------------+

``hr`` (Employees) is declared as a dependency too, because both HR Suite
folders attach to the Employees app menu.

``odomate_hr_leave_email`` contributes no menu of its own — it is configured
through an incoming mail alias, not a dedicated screen. Eight modules, ten
re-parented menu entries.

Installation
============

#. Copy ``odomate_hr_bundle`` into your addons path, together with the eight
   member modules if they are not already there.
#. Go to **Apps → Update Apps List**.
#. Search for **OdoMate HR Suite** and click **Install**.

Odoo resolves the dependency list and installs any member module that is
missing. Members already installed, and all of their data, are left untouched.

Configuration
=============

None. There is nothing to set up after the install.

What it changes
===============

Nothing but menu placement. Each of the ten re-parented entries is rewritten
with ``parent_id`` and ``sequence`` only — never its name, action, groups,
active flag or icon — so every entry keeps its own screen, records,
permissions and translated label.

The module ships no ``ir.model.access`` rows, no record rules and no security
groups, and grants nothing to any user or existing group. **Installing it
changes no user's permissions.** The two folders carry no action and no group
of their own, so Odoo hides a folder automatically when every entry beneath it
is hidden from the current user.

Known behaviour
===============

**Upgrading one member module on its own.** The menu data file is
deliberately not ``noupdate``, so the arrangement re-applies on every upgrade
of ``odomate_hr_bundle``. If you upgrade a single member module by itself,
that member's own XML puts its own menu back at its native top-level position.
Upgrade ``odomate_hr_bundle`` afterwards to restore the grouping.

**On uninstall.** Nothing is destroyed. ``ir.ui.menu.parent_id`` is declared
``ondelete="restrict"``, so uninstalling this module can never delete a member
module's menu as a side effect; the eight members and their data keep working
individually. Uninstall does not move the member menus back to their native
positions — each returns there the next time its own module is upgraded or
reinstalled. Whether the two HR Suite folder records owned by this module are
themselves removed on uninstall, or linger as empty folders because a
still-installed member's menu still points at one, is an open detail we have
not verified against the Odoo source; we state it as unverified rather than
claim it either way.

Documentation
=============

See ``doc/USER_GUIDE.md`` (English) and ``doc/USER_GUIDE.uk.md`` (Ukrainian).

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

Website: https://www.odomate.pro
