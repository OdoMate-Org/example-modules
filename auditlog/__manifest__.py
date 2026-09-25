{
    'name': "Audit Log",

    'summary': """
    Odoo Audit Log module tracks who created, modified, deleted, read or
    exported records across the models you choose, keeping old and new
    field values so past activity always stays answerable.
    audit trail odoo | audit log | field change history | change tracking |
    user activity log | data export tracking | compliance audit |
    record deletion snapshot | log retention policy
    """,

    'description': """
Audit Log
=========
Record creations, modifications, deletions, reads and exports on the models you choose.

* One rule per model (Draft / Confirmed), with Log Creates / Writes / Deletes / Reads / Exports
* Full log (before/after diff of all stored fields) or Fast log (only submitted values)
* Users to Exclude, Fields to Exclude, Capture Record (snapshot on delete)
* On Logging Failure: block the operation or skip the log
* Readable old/new values (relational fields shown by name), "View logs" action on audited records
* Export logs with an Exported Records smart button; flat, read-only Log Lines view
* User sessions (SHA-256 fingerprint) and HTTP requests linked to each log
* Multi-company isolation of logs, lines, sessions and requests
* Optional auto-vacuum scheduled action (180 days, ships inactive) and a Delete Old Logs dialog
* Logs smart button on each rule
* Groups: Auditlog User (read) and Auditlog Manager (full); Settings admins are managers
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro/m/audit-20?v=site",
    'support': "support@odomate.pro",
    'images': ['static/description/banner.gif'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/20.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Tools',
    'version': '20.0.1.0.0',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.access.csv',
        'data/ir_cron.xml',
        'views/auditlog_rule_views.xml',
        'views/auditlog_log_views.xml',
        'views/auditlog_http_views.xml',
        'views/auditlog_autovacuum_views.xml',
        'views/auditlog_menus.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
