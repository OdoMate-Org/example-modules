{
    'name': "Employee Dependants & Identity Documents",

    'summary': (
        "Employee dependants, emergency contact sync, identity document expiry "
        "reminders and automatic employee creation from new logins. "
        "HR dependants, passport expiry alert, identification expiry cron, "
        "notice period, joining date, Odoo 19 Employees."
    ),

    'description': """
Employee Dependants & Identity Documents
========================================

Extends the Employees app with dependant records, identity document expiry
tracking with a daily edge-triggered reminder cron, a per-company default
notice period on employee versions, a computed joining date, and automatic
employee creation for every new internal login.
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro",
    'support': "support@odomate.pro",

    'category': 'Human Resources',
    'version': '19.0.1.0.1',
    'license': 'LGPL-3',

    'depends': ['hr', 'mail'],

    'data': [
        'security/ir.model.access.csv',
        'security/odomate_hr_security.xml',
        'data/odomate_hr_relationship_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'views/odomate_hr_relationship_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_version_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'demo': [
        'demo/odomate_hr_employee_demo.xml',
        'demo/odomate_hr_dependant_demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
