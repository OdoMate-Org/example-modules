{
    'name': "Employee Custody Management",

    'summary': "Odoo Employee Custody Management module tracks company property "
               "handed to employees, running each item through a request, approval "
               "and return workflow with automatic overdue reminders and a printable "
               "handover document. employee custody | company property tracking | "
               "asset handover | custody request approval | overdue return reminders | "
               "hr asset register | employee equipment tracking | property handover "
               "document | borrowed equipment log",

    'description': """
Employee Custody Management
===========================

Register every asset the company hands to an employee, run the request
through an approval workflow, chase overdue returns automatically and print
a signed handover document.
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro/m/custody?v=site",
    'support': "support@odomate.pro",
    'maintainer': "OdoMate",

    'category': 'Human Resources',
    'version': '19.0.1.0.2',
    'license': 'LGPL-3',

    'depends': [
        'hr',
        'mail',
        'product',
        'odomate_hr_employee_info_06092026_2',
    ],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'report/odomate_hr_custody_report_templates.xml',
        'report/odomate_hr_custody_reports.xml',
        'wizard/odomate_hr_custody_extend_views.xml',
        'wizard/odomate_hr_custody_refuse_views.xml',
        'views/odomate_hr_custody_item_views.xml',
        'views/odomate_hr_custody_views.xml',
        'views/hr_employee_views.xml',
        'views/odomate_hr_custody_menus.xml',
    ],
    'demo': [
        'demo/odomate_hr_custody_demo.xml',
    ],
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
