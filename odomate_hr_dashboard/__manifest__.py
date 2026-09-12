{
    'name': "OdoMate HR Overview Dashboard",

    'summary': "HR dashboard for Odoo 19 Employees: headcount, joiners and leavers, "
               "employee turnover rate, Bradford absence factor, "
               "cross-suite pending approvals - read-only HR analytics and reporting",

    'description': """
OdoMate HR Overview Dashboard
=============================

A read-only management overview for Odoo 19 Employees, built on two SQL-view
analysis models and one OWL client action.

* Five clickable figure tiles - Headcount, Joined, Left, Off today, Turnover.
* Every figure drills into the exact list of records it was counted from.
* Joiners and leavers analysis (list, graph, pivot) from hr.version data.
* Absence concentration by employee, ranked by the Bradford factor.
* Cross-suite pending approvals, skipped silently when a suite is not installed.

The module reads. It never writes a record, never grants a group and never
uses sudo().
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro",
    'support': "support@odomate.pro",

    'category': 'Human Resources/Employees',
    'version': '19.0.1.0.2',
    'license': 'LGPL-3',

    'depends': ['hr', 'hr_holidays', 'web'],

    'data': [
        'security/odomate_hr_dashboard_security.xml',
        'security/ir.model.access.csv',
        'views/odomate_hr_movement_views.xml',
        'views/odomate_hr_absence_factor_views.xml',
        'views/odomate_hr_dashboard_views.xml',
        'views/odomate_hr_dashboard_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odomate_hr_dashboard/static/src/**/*',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
