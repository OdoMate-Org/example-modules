{
    'name': "Accounting Daily Reports (Day Book, Cash Book, Bank Book)",

    'summary': (
        "Odoo Accounting Daily Reports (Day Book, Cash Book, Bank Book) "
        "module prints the day book, cash book and bank book as PDF with "
        "opening balances and a per-account running balance, so daily entry "
        "and closing cash questions need no spreadsheet. "
        "| day book report | cash book pdf | bank book report "
        "| daily accounting reports | journal item recap "
        "| opening balance report | running balance report "
        "| cash journal printout | odoo community reports"
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
    'website': "https://odomate.pro/m/daily-books?v=site",
    'support': "support@odomate.pro",

    'category': 'Accounting',
    'version': '19.0.1.0.3',
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
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
