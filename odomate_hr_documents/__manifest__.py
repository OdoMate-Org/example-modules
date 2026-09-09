{
    'name': "Employee Document Expiry Tracking",

    'summary': "Employee document expiry tracking: work permits, licences, "
               "certificates, HR compliance reminders, renewal history with "
               "superseded scans, expiry alerts and manager to-dos",

    'description': """
Employee Document Expiry Tracking
=================================
Track work permits, licences and certificates with automatic expiry,
configurable chasing patterns, renewal-with-history and manager to-dos.

A daily scheduled action expires documents whose expiry date has passed, then
chases the employee by email and their manager with a To-Do activity, following
the chasing pattern configured on each document type.
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro/m/documents?v=site",
    'support': "support@odomate.pro",

    'category': 'Human Resources',
    'version': '19.0.1.0.3',
    'license': 'LGPL-3',

    'depends': ['hr', 'mail'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'views/odomate_hr_document_type_views.xml',
        'views/odomate_hr_document_views.xml',
        'views/odomate_hr_form_template_views.xml',
        'views/hr_employee_views.xml',
        'wizard/odomate_hr_document_renew_views.xml',
        'views/odomate_hr_documents_menus.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
