{
    'name': "Product Kind — Manufacturing Classification",
    'summary': "Hierarchical Product Kind classification with snapshot freezing "
               "across product, sale and manufacturing",
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
    'website': "https://odomate.pro",
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
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': '_post_init_hook',
    'uninstall_hook': '_uninstall_hook',
}
