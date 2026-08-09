{
    'name': "Sale Warehouse Auto Fulfillment",

    'summary': "Automatic delivery validation, invoice creation and invoice "
               "posting per warehouse on sales order confirmation. "
               "Sale auto ship, auto invoice, auto validate delivery, "
               "warehouse automation, one-click fulfillment.",

    'description': """
Sale Warehouse Auto Fulfillment
===============================

Three per-warehouse switches turn a single Confirm click on a sales order into
a complete fulfillment run: the delivery is validated in full, the customer
invoice is created and the invoice is posted. Everything runs in one savepoint,
so a failure leaves the order as a quotation with nothing half-done.
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro",
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
}
