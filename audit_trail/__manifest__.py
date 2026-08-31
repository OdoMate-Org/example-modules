{
    'name': "Audit Trail",

    'summary': "Odoo Audit Trail module records who created, changed, deleted, "
               "exported or opened any record, storing before and after field "
               "values, deletion snapshots and session context, so past "
               "activity stays answerable. "
               "audit trail odoo | audit log | change tracking | "
               "field history tracking | record change history | "
               "deletion snapshot | export tracking | user activity log | "
               "data retention cleanup | compliance audit odoo",

    'description': """
Audit Trail
===========

Record who did what to which record, with before/after field values, without
slowing down or bloating the rest of the system.

Watch settings are declared per model and per company (``audit.rule``). Nothing
is recorded until a rule is confirmed, and each rule chooses exactly which of
the five actions to record: create, write, unlink, export and read.
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro/m/audit?v=site",
    'support': "support@odomate.pro",

    'category': 'Tools',
    'version': '19.0.1.0.5',
    'license': 'LGPL-3',

    'depends': ['base', 'web'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/audit_rule_views.xml',
        'views/audit_log_views.xml',
        'views/audit_session_views.xml',
        'views/audit_config_views.xml',
        'views/res_partner_views.xml',
        'views/audit_menus.xml',
    ],
    'demo': [
        'demo/demo_watch_setup.xml',
        'demo/demo_audit_history.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
