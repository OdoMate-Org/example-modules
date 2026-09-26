{
    'name': "Audit Trail",

    'summary': """
        Odoo Audit Trail module records who created, changed, deleted,
        exported or opened any record, storing before and after field
        values, deletion snapshots and session context, so past
        activity stays answerable.
        audit trail odoo | audit log | change tracking |
        field history tracking | record change history |
        deletion snapshot | export tracking | user activity log |
        data retention cleanup | compliance audit odoo
    """,

    'description': """
Audit Trail
===========
Per-company watch rules record create, write, delete, export and list-read
events on chosen kinds of records, with field-level before/after values,
working sessions and a batch-limited scheduled clean-up.
See doc/USER_GUIDE.md for the full guide.
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro/m/audit?v=site",
    'support': "support@odomate.pro",
    'images': ['static/description/banner.gif'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/20.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Tools',
    'version': '20.0.1.0.0',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'base_setup', 'product'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.access.csv',
        'data/ir_cron_data.xml',
        'views/audit_rule_views.xml',
        'views/audit_log_views.xml',
        'views/audit_log_line_views.xml',
        'views/audit_session_views.xml',
        'views/res_config_settings_views.xml',
        'views/watched_record_views.xml',
        'views/audit_menus.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
