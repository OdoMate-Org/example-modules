{
    'name': "My Apps Dashboard",

    'summary': """
        Odoo My Apps Dashboard module turns the app menu into a personal home
        screen of app tiles, with pinned favourites, company priority apps and
        usage-based ordering, so every user reaches their daily apps in one click.
        odoo app dashboard | home screen | app launcher | favorite apps |
        app tiles | quick app search | drag and drop apps | user start page |
        priority apps
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
    'website': "https://odomate.pro/m/my-apps?v=site",
    'support': "support@odomate.pro",

    'category': 'Productivity',
    'version': '20.0.1.0.5',
    'images': ['static/description/banner.gif'],
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
