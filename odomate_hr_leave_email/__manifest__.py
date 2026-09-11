{
    'name': "Time Off Requests by Email",

    'summary': (
        "Time off request by email - leave request mail gateway, "
        "hr.leave mail alias, holiday request from email, "
        "Time Off email inbox, leave email log"
    ),

    'description': """
Time Off Requests by Email
==========================

Publishes one email address that turns an incoming message into an ordinary
Time Off request (``hr.leave``) for the employee who sent it. Dates are read
from the body of the message in ``YYYY-MM-DD`` or ``DD/MM/YYYY`` format.

Nothing is ever guessed: a message that cannot be resolved to an employee, a
date or a configured Time Off type is refused, recorded in the *Email
Requests* log under Time Off / Reporting, and answered with an explanation of
the accepted formats.
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro",
    'support': "support@odomate.pro",

    'category': 'Human Resources/Time Off',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',

    'depends': [
        'hr_holidays',
        'mail',
    ],

    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/mail_alias_data.xml',
        'data/mail_template_data.xml',
        'views/odomate_hr_leave_email_log_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
