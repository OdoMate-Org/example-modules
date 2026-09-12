{
    'name': "HR Notices, Announcements & Acknowledgements",

    'summary': """
        Odoo HR Notices, Announcements & Acknowledgements module publishes
        company notices to a chosen audience with an approval step and
        acknowledgement tracking, so HR can show who was told and who has not
        responded. hr announcements | employee notice board | acknowledgement
        tracking | internal communication | announcement approval workflow |
        audience targeting | hr date reminders | systray notification counter |
        company policy notices
    """,

    'description': """
HR Notices, Announcements & Acknowledgements
============================================

Publish HR announcements to a precisely targeted audience, track who pressed
Acknowledge, and keep HR-only saved reminders over any date field on
employees, contract versions, applicants or time off.

Key capabilities
----------------

* Draft -> Waiting for Approval -> Published approval workflow, with Refused
  and Expired as terminal branches.
* Audience targeting: everyone, selected employees, selected departments
  (exact match, no hierarchy walk) or selected job positions.
* Acknowledgement tracking with a has-not-acknowledged list for HR.
* Saved date reminders with a live matching-record count.
* Systray counter showing announcements addressed to you that you have not
  acknowledged yet.
* Multi-company record rules on every model.
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro/m/notices?v=site",
    'support': "support@odomate.pro",

    'category': 'Generic Modules/Human Resources',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'images': ['static/description/banner.gif'],

    'depends': ['base', 'mail', 'hr'],

    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'views/odomate_hr_announcement_category_views.xml',
        'views/odomate_hr_announcement_views.xml',
        'views/odomate_hr_reminder_views.xml',
        'views/hr_employee_views.xml',
        'wizard/odomate_hr_announcement_refuse_views.xml',
        'views/odomate_hr_notices_menus.xml',
    ],
    'demo': [
        'demo/odomate_hr_notices_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odomate_hr_notices/static/src/**/*',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
