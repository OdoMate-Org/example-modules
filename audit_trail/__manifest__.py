{
    'name': "Audit Trail",

    'summary': "Configurable audit trail: track create, write, delete, export "
               "and read on any model, with before/after field values, "
               "deletion snapshots, working sessions and retention clean-up",

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
    'website': "https://odomate.pro",
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
    'installable': True,
    'application': True,
    'auto_install': False,
}
