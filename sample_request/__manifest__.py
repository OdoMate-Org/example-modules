{
    'name': "Product Sample Requests",

    'summary': """
        Customer product sample requests with manager approval, shipping,
        automatic follow-up to-do and sample-to-order conversion reporting
        (sample management, sales samples, approval workflow, conversion rate).
    """,

    'description': """
Product Sample Requests
=======================
Sales reps request product samples for customers; sales managers approve or
reject them (with a mandatory reason) and mark approved samples as sent.
Marking a request as sent schedules a follow-up to-do for the rep 14 days
later. The rep logs the outcome (ordered / still thinking / not interested)
and can link the resulting sales order. Pivot and graph reporting slice the
sample-to-order conversion rate by rep and status.
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro",
    'support': "support@odomate.pro",

    'category': 'Sales/Sales',
    'version': '20.0.1.0.0',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['mail', 'product', 'sale'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.access.csv',
        'data/ir_sequence_data.xml',
        'wizard/sample_request_reject_wizard_views.xml',
        'wizard/sample_request_outcome_wizard_views.xml',
        'views/sample_request_views.xml',
        'views/sample_request_menus.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
