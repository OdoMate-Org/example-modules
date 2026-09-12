{
    'name': "Employee Transfer",

    'summary': "Record, approve and apply dated employee transfers as hr.version history",

    'description': """
Employee Transfer
=================

Records, approves and applies dated employee moves (department, job, work
location, manager, company) as new ``hr.version`` history entries.
    """,

    'author': "OdoMate",
    'website': "https://www.odomate.com",

    'category': 'Human Resources/Employees',
    'version': '19.0.1.0.3',
    'license': 'LGPL-3',

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
