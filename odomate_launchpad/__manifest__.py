{
    'name': "OdoMate Launchpad",

    'summary': """
        Personal app launcher home screen: square app icons sorted by your
        30-day usage, pinned favourite apps, instant app search, set as
        startup screen / home action - Odoo app switcher, app dashboard.
    """,

    'description': """
OdoMate Launchpad
=================
A full-screen start page that shows every app the current user can access
(standard and custom) as square tiles, ordered per user:

* pinned apps first, in pin order;
* then by number of opens in the last 30 days, computed live;
* then alphabetically.

Each tile has a pin toggle, a search box filters tiles instantly, and a
"Set as Startup Screen" button makes the Launchpad the user's own home
action. Usage logs and pins are strictly personal (per-user access rules).
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro",
    'support': "support@odomate.pro",

    'category': 'Productivity',
    'version': '20.0.1.0.0',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['web', 'mail'],

    # always loaded
    'data': [
        'security/ir.access.csv',
        'views/launchpad_menus.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odomate_launchpad/static/src/**/*',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
