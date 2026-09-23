{
    'name': "Accounting Daily Reports (Day Book, Cash Book, Bank Book)",

    'summary': (
        "Print the day book, cash book and bank book as PDF: "
        "daily journal item recap, cash and bank movements with opening "
        "balance and a true per-account running balance, multi-company"
    ),

    'description': """
Accounting Daily Reports
========================

Three printable daily accounting reports built on the shared, read-only
filter contract of *Accounting Audit Reports*.

* Day Book grouping every journal item of the period into day blocks,
  with per-day debit, credit and difference totals
* Cash Book over the cash journals, with an optional opening balance and
  a true per-account running balance
* Bank Book over the bank and credit card journals, same layout

Reads through the Odoo ORM only. No raw SQL, no ``sudo()``, no write of any
kind, and no field added to any standard model.
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro",
    'support': "support@odomate.pro",

    'category': 'Accounting',
    'version': '19.0.1.0.2',
    'license': 'LGPL-3',

    'depends': ['account', 'odomate_account_ledger_reports'],

    'data': [
        'security/ir.model.access.csv',
        'report/odomate_report_actions.xml',
        'report/report_day_book_templates.xml',
        'report/report_liquidity_book_templates.xml',
        'views/odomate_account_day_book_views.xml',
        'views/odomate_account_cash_book_views.xml',
        'views/odomate_account_bank_book_views.xml',
        'views/odomate_account_menus.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
