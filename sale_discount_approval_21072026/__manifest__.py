{
    'name': "Sale Discount Approval",

    'summary': (
        "Odoo Sale Discount Approval module streamlines order and invoice "
        "discounting by applying a single percent or fixed-amount rate "
        "across every line and routing large discounts through an "
        "approval gate before confirmation, keeping pricing consistent "
        "without manual line-by-line edits. "
        "sales discount module | odoo pricing control | order line discount | "
        "invoice discount automation | discount approval workflow | "
        "sales manager approval | percent amount discount | "
        "discount approval gate | sale order surcharge"
    ),

    'description': """
Sale Discount Approval
======================

Apply a single order-level or invoice-level discount (percent or fixed
amount) that fans out to every line, with an optional company-level
approval gate for large discounts.

Key features
------------
* Percent or fixed Amount discount applied to all sale order / invoice lines.
* Informational ``amount_discount`` total on orders and invoices.
* Two-step validation: orders whose average line discount exceeds a
  company threshold move to a "Waiting Approval" state and must be
  approved by a Sales Manager.
* Discount is carried over automatically when the order is invoiced.
* Discount row injected into printed and portal quotation / invoice
  documents and analysis reports.
    """,

    'author': "OdoMate",
    'website': "https://www.odomate.pro",
    'support': "support@odomate.pro",

    'category': 'Sales/Sales',
    'version': '19.0.1.0.3',
    'license': 'LGPL-3',

    'depends': [
        'sale_management',
        'account',
        'sales_team',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
        'report/sale_report_templates.xml',
        'report/account_report_templates.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': ['static/description/banner.jpg'],
}
