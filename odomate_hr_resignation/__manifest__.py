{
    'name': "OdoMate HR Resignation & Clearance",

    'summary': "Employee resignation workflow, notice period, exit clearance "
               "checklist and offboarding - HR resignation, employee exit, "
               "clearance certificate, notice period, company property handover, "
               "exit interview survey",

    'description': """
Resignation and exit clearance tracking for the Odoo Employees app.

Records a resignation from the day the employee gives notice through manager
approval, HR approval, the exit clearance checklist and the final release.
The release is gated on the odomate_hr_custody register: an employee who still
holds approved company property cannot be released, and the check is re-run
live at every attempt rather than trusting a stored snapshot.
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro",
    'support': "support@odomate.pro",

    'category': 'Human Resources',
    'version': '19.0.1.0.1',
    'license': 'LGPL-3',

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
