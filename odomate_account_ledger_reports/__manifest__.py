{
    'name': "Accounting Audit Reports (General Ledger, Partner Ledger, Aged Balance)",

    'summary': (
        "Print the six standard accounting audit reports as PDF: "
        "general ledger, partner ledger, aged receivable and aged payable "
        "balance, tax report, journals audit and journal entry printout, "
        "with opening balances, ageing buckets and multi-company support"
    ),

    'description': """
Accounting Audit Reports
========================

Six printable accounting audit reports built on a single shared, read-only
filter contract over journal items, plus two ready-made journal-item screens.

* General Ledger with a fiscal-year-correct opening balance
* Partner Ledger with a per-partner running balance and amount owed
* Aged Partner Balance whose residual is measured as of the chosen date
* Tax Report with signed Sales and Purchases sections
* Journals Audit with a per-journal tax declaration recap
* Journal Entry printout, one page per entry

Reads through the Odoo ORM only. No raw SQL, no ``sudo()``, no write outside
its own wizard records, and no field added to any standard model.
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro",
    'support': "support@odomate.pro",

    'category': 'Accounting',
    'version': '19.0.1.0.1',
    'license': 'LGPL-3',

    'depends': ['account', 'analytic'],

    'data': [
        'security/ir.model.access.csv',
        'report/odomate_report_paperformat.xml',
        'report/odomate_report_actions.xml',
        'report/report_filter_header_templates.xml',
        'report/report_general_ledger_templates.xml',
        'report/report_partner_ledger_templates.xml',
        'report/report_aged_partner_balance_templates.xml',
        'report/report_tax_report_templates.xml',
        'report/report_journal_audit_templates.xml',
        'report/report_journal_entry_templates.xml',
        'views/odomate_account_report_filter_views.xml',
        'views/odomate_account_general_ledger_views.xml',
        'views/odomate_account_partner_ledger_views.xml',
        'views/odomate_account_aged_partner_views.xml',
        'views/odomate_account_tax_report_views.xml',
        'views/odomate_account_journal_audit_views.xml',
        'views/odomate_account_move_line_actions.xml',
        'views/odomate_account_menus.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
