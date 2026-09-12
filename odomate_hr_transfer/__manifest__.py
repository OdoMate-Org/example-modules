{
    'name': "Employee Transfer",

    'summary': "Odoo Employee Transfer module records, approves and applies dated "
               "employee moves as new version history, so department, job and "
               "location changes keep a permanent trail instead of overwriting the "
               "employee record. employee transfer | hr transfer | employee movement "
               "| department transfer | job position change | transfer approval | "
               "employee history | dated version history | internal transfer | hr records",

    'description': """
Employee Transfer
=================

Records, approves and applies dated employee moves (department, job, work
location, manager, company) as new ``hr.version`` history entries.
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro/m/transfer?v=site",
    'support': "support@odomate.pro",

    'category': 'Generic Modules/Human Resources',
    'version': '19.0.1.0.4',
    'license': 'LGPL-3',
    'images': ['static/description/banner.gif'],

    'depends': ['hr', 'mail'],

    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'wizard/odomate_hr_transfer_refuse_views.xml',
        'views/odomate_hr_transfer_views.xml',
        'views/hr_employee_views.xml',
        'views/odomate_hr_transfer_menus.xml',
    ],
    'demo': [
        'demo/odomate_hr_transfer_demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
