{
    'name': "Product Kind — Manufacturing Classification",
    'summary': "Odoo Product Kind — Manufacturing Classification module classifies products "
               "in a hierarchical, production-oriented catalog and freezes a snapshot on sale "
               "orders and manufacturing orders at confirmation, keeping historical documents "
               "accurate even after products are reclassified. "
               "product classification | manufacturing classification | product hierarchy | "
               "product kind odoo | sale order snapshot | manufacturing order tracking | "
               "bill of materials | route type tracking | production reporting",
    'description': """
Product Kind — hierarchical manufacturing classification
=========================================================

A draggable, multi-level "Product Kind" catalog that flows from products
through sales into manufacturing. Confirmed sale order lines and manufacturing
orders freeze a snapshot of the kind, so historical documents stay accurate
even after a product is reclassified — while products and their bills of
materials keep a live link to the current kind.

Keywords: product kind, manufacturing classification, product hierarchy,
route type, snapshot, sale order, manufacturing order, bill of materials.
    """,
    'author': "OdoMate",
    'website': "https://odomate.pro/m/kinds?v=site",
    'support': "support@odomate.pro",
    'category': 'Manufacturing',
    'version': '19.0.1.0.6',
    'license': 'LGPL-3',
    'depends': [
        'mrp',
        'sale',
        'web_hierarchy',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/product_kind_views.xml',
        'views/product_template_views.xml',
        'views/product_variant_views.xml',
        'views/sale_order_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_bom_views.xml',
    ],
    'demo': [
        'demo/product_kind_demo.xml',
        'demo/product_demo.xml',
        'demo/sale_demo.xml',
        'demo/mrp_demo.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': '_post_init_hook',
    'uninstall_hook': '_uninstall_hook',
}
