{
    'name': "OdoMate Connector",
    'summary': "Export a redacted structural snapshot of your database for OdoMate — "
               "structural context, never your business records. "
               "environment context | schema export | metadata snapshot | "
               "installed modules | customizations | privacy preserving",
    'description': """
OdoMate Connector
=================

Exports a redacted structural snapshot of this database as a human-readable
``odomate_context.json`` file, so `OdoMate <https://www.odomate.pro>`_ can
generate modules that fit your real environment and test them against a
replica of it.

Structural context, never your business records
-----------------------------------------------

**Included:** installed modules, models and fields (including Studio and
``x_`` customizations), customized views, configuration toggles, security
groups, automation names, and per-model record *counts*.

**Never included:** business records, partner/user/employee data, emails,
names, credentials, or secret configuration parameters. The database UUID is
exported only as a SHA-256 hash.

The module makes no network calls, stores nothing, and adds no third-party
dependencies. The export is plain, pretty-printed JSON — open it and inspect
exactly what leaves your system before you share it.
    """,
    'author': "OdoMate",
    'website': "https://www.odomate.pro",
    'support': "support@odomate.pro",
    'category': 'Technical',
    'version': '19.0.1.5.0',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/export_wizard_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
}
