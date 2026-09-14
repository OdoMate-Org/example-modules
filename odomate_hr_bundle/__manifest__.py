{
    'name': "OdoMate HR Suite",
    'summary': "Installs the complete OdoMate HR suite — eight modules for employee dependants and identity documents, document expiry, custody of company property, transfers, time off by email, notices and acknowledgements, turnover and absence analytics, and resignation with clearance — and groups their menus into one HR Suite section. odoo hr suite | hr modules bundle | all in one hr | human resources pack | employee management odoo 19 | hr suite installer | hr menu grouping",
    'description': """
OdoMate HR Suite
================

One install for the complete OdoMate HR suite. This is a meta-module: it
declares no models, no fields and no permissions of its own. Installing it
installs the eight member modules below, then groups their menus into an
"HR Suite" folder in the Employees app and a second "HR Suite" folder under
Employees > Configuration.

What gets installed
-------------------

* **Employee Dependants & Identity Documents** (``odomate_hr_employee_info_06092026_2``) — Family members, dependants and identity document details on the employee record.
* **Employee Document Expiry Tracking** (``odomate_hr_documents``) — Documents that expire, with advance warning and a renewal history.
* **Employee Custody Management** (``odomate_hr_custody``) — Company property held by employees, with request, approval and return.
* **Employee Transfer** (``odomate_hr_transfer``) — Moves between departments, locations or companies, keeping the history.
* **Time Off Requests by Email** (``odomate_hr_leave_email``) — Turns an incoming email into a time-off request.
* **HR Notices, Announcements & Acknowledgements** (``odomate_hr_notices``) — Company announcements and personal reminders, with a count in the top bar.
* **Employee Turnover & Absence Dashboard** (``odomate_hr_dashboard``) — Headcount, turnover, absence concentration and pending approvals in one screen.
* **Employee Resignation & Clearance** (``odomate_hr_resignation``) — Resignation requests, a clearance checklist and an exit interview.

Installing on a database where some members are already present adds only the
missing ones. Modules already installed, and their data, are left untouched.

What it changes
---------------

Nothing but menu placement. Each of the ten re-parented entries is rewritten
with ``parent_id`` and ``sequence`` only — never its name, action, groups or
icon — so every screen, record, permission and translated label stays exactly
as its own module defined it. No user's access rights change when this module
is installed.

Please note: upgrading one member module on its own
---------------------------------------------------

The menu arrangement is re-applied on every upgrade of this module, by design.
If you later upgrade a single member module by itself, that member's own XML
puts its own menu back at its native top-level position. Upgrade
``odomate_hr_bundle`` afterwards to restore the HR Suite grouping.

On uninstall
------------

Nothing is destroyed. The ``parent_id`` field on a menu is declared
``ondelete="restrict"``, so uninstalling this module can never delete a member
module's menu as a side effect. The eight member modules and all of their data
remain untouched and keep working individually; each member menu returns to its
native position the next time its own module is upgraded or reinstalled.

Whether the two "HR Suite" folder records that this module owns are themselves
removed on uninstall, or linger as empty folders because a still-installed
member's menu still points at one, is an open detail we have not verified
against the Odoo source. We state it as unverified rather than claim it either
way.
    """,
    'author': "OdoMate",
    'website': "https://www.odomate.pro",
    'support': "support@odomate.pro",
    'category': 'Generic Modules/Human Resources',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'hr',
        'odomate_hr_employee_info_06092026_2',
        'odomate_hr_documents',
        'odomate_hr_custody',
        'odomate_hr_transfer',
        'odomate_hr_leave_email',
        'odomate_hr_notices',
        'odomate_hr_dashboard',
        'odomate_hr_resignation',
    ],
    'data': [
        'views/odomate_hr_suite_menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
