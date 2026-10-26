{
    'name': "My Apps Dashboard",

    'summary': """
        Personal My Apps home screen for Odoo: square app tiles, favorite apps,
        admin-curated priority apps, usage-based ordering, drag-to-reorder,
        quick app search and a per-user or database-wide starting screen.
    """,

    'description': """
Adds a "My Apps" dashboard showing a tile for every app the user can already
open in the native app menu. Users pin favorite apps with a star, filter apps
by name, drag tiles to reorder them, and choose the dashboard as their home
screen in My Preferences (Home Screen: Default Menu / Apps Dashboard).
Administrators can curate a database-wide list of Priority Apps shown first
for everyone, and set the Apps Dashboard as the default home screen for all
users from Settings > General Settings. Apps a user has not pinned, prioritized
or manually reordered are sorted by how often that user opens them.
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro",
    'support': "support@odomate.pro",

    'category': 'Productivity',
    'version': '20.0.1.0.5',
    'license': 'LGPL-3',

    'depends': ['base', 'web', 'base_setup'],

    'data': [
        'security/ir.access.csv',
        'views/views.xml',
        'views/app_dashboard_priority_app_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'app_dashboard/static/src/js/**/*.js',
            'app_dashboard/static/src/xml/**/*.xml',
            'app_dashboard/static/src/css/**/*.scss',
        ],
    },
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
