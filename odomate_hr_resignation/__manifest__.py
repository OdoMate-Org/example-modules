{
    'name': "Employee Resignation & Clearance",

    'summary': "Odoo Employee Resignation & Clearance module records an "
               "employee's notice, routes the exit clearance checklist to the "
               "people who own each item and blocks the final release while "
               "company property is still outstanding, so nobody leaves with "
               "unreturned equipment or an unfinished handover. "
               "employee resignation | exit clearance checklist | hr offboarding "
               "| notice period tracking | resignation approval workflow | "
               "employee exit process | company property clearance | exit "
               "interview survey | employee offboarding checklist",

    'description': """
Resignation and exit clearance tracking for the Odoo Employees app.

Records a resignation from the day the employee gives notice through manager
approval, HR approval, the exit clearance checklist and the final release.
The release is gated on the odomate_hr_custody register: an employee who still
holds approved company property cannot be released, and the check is re-run
live at every attempt rather than trusting a stored snapshot.
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro/m/resignation?v=site",
    'support': "support@odomate.pro",

    'category': 'Generic Modules/Human Resources',
    'version': '19.0.1.0.1',
    'license': 'LGPL-3',
    'images': ['static/description/banner.gif'],

    'depends': [
        'hr',
        'mail',
        'survey',
        'odomate_hr_custody',
    ],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/odomate_hr_clearance_item_data.xml',
        'data/ir_cron_data.xml',
        'wizard/odomate_hr_resignation_refuse_views.xml',
        'views/odomate_hr_clearance_item_views.xml',
        'views/odomate_hr_resignation_clearance_line_views.xml',
        'views/odomate_hr_resignation_views.xml',
        'views/hr_employee_views.xml',
        'views/res_config_settings_views.xml',
        'views/odomate_hr_resignation_menus.xml',
    ],
    'demo': [
        'demo/odomate_hr_resignation_demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
