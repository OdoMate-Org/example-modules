{
    'name': "Office Equipment Tracker",

    'summary': "Track office equipment assigned to employees: laptops, "
               "phones, monitors, check-out and return, condition notes",

    'description': """
Office Equipment Tracker
========================

Track company office equipment and who currently holds each item.
Manage a simple check-out / return lifecycle for laptops, phones,
monitors and peripherals, record condition notes, and keep equipment
isolated per company.

Keywords: office equipment, asset tracking, IT asset management,
employee equipment, check-out, hardware inventory, device assignment.
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro",
    'support': "support@odomate.pro",

    'category': 'Human Resources',
    'version': '19.0.1.0.2',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr'],

    # always loaded
    'data': [
        'security/equipment_security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
