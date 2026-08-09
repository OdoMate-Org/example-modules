{
    'name': "Sale Warehouse Auto Fulfillment",

    'summary': (
        "Odoo Sale Warehouse Auto Fulfillment module automates order "
        "fulfillment per warehouse by validating the delivery, creating "
        "the customer invoice and posting it the moment a sales order is "
        "confirmed, all inside one transaction so a failure leaves nothing "
        "half-done. "
        "warehouse automation | sales order automation | auto validate delivery | "
        "automatic delivery validation | sale auto invoice | "
        "automatic invoice posting | one click fulfillment | "
        "auto ship sales order | per warehouse settings"
    ),

    'description': """
Sale Warehouse Auto Fulfillment
===============================

Three per-warehouse switches turn a single Confirm click on a sales order into
a complete fulfillment run: the delivery is validated in full, the customer
invoice is created and the invoice is posted. Everything runs in one savepoint,
so a failure leaves the order as a quotation with nothing half-done.
    """,

    'author': "OdoMate",
    'website': "https://www.odomate.pro",
    'support': "support@odomate.pro",

    'category': 'Sales/Sales',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',

    'depends': [
        'sale_stock',
        'account',
        'mail',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/stock_warehouse_views.xml',
    ],
    'demo': [
        'demo/warehouses.xml',
        'demo/products.xml',
        'demo/sale_orders.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': ['static/description/banner.jpg'],
}
