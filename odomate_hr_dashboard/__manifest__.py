{
    'name': "Employee Turnover & Absence Dashboard",

    'summary': "Odoo Employee Turnover & Absence Dashboard module brings headcount, "
               "joiners, leavers, turnover rate and Bradford absence ranking onto one "
               "read-only screen in Employees, where every figure opens the exact "
               "records it was counted from. | hr dashboard | employee turnover | "
               "headcount report | hr analytics | joiners and leavers | bradford factor | "
               "absence management | staff turnover rate | hr reporting",

    'description': """
Employee Turnover & Absence Dashboard
=====================================

A read-only management overview for Odoo 19 Employees, built on two SQL-view
analysis models and one OWL client action.

* Five clickable figure tiles - Headcount, Joined, Left, Off today, Turnover.
* Every figure drills into the exact list of records it was counted from.
* Joiners and leavers analysis (list, graph, pivot) from hr.version data.
* Absence concentration by employee, ranked by the Bradford factor.
* Cross-suite pending approvals, skipped silently when a suite is not installed.
  The rest of the OdoMate HR modules live at
  https://github.com/OdoMate-Org/example-modules - install them and this panel
  fills; without them it simply stays empty.

The module reads. It never writes a record, never grants a group and never
uses sudo().
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro/m/hr-dashboard?v=site",
    'support': "support@odomate.pro",

    'category': 'Generic Modules/Human Resources',
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
    'images': ['static/description/banner.gif'],

    'installable': True,
    'application': False,
    'auto_install': False,
}
