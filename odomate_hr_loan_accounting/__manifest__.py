{
    'name': "Employee Loans - Accounting Entries",

    'summary': "Journal entries for employee loans: disbursement, payroll "
               "recovery and early settlement postings. HR loan accounting, "
               "loan receivable account, interest income, payslip deduction "
               "journal entry.",

    'description': """
Employee Loans - Accounting Entries
===================================

The accounting half of Employee Loans. It posts the journal entries that the
loan workflow implies, reading the figures already stored by
``odomate_hr_loan`` and never re-deriving them.

* Disbursement entry posted on approval.
* One recovery entry per instalment, posted when payroll recovers it.
* Settlement entry posted when a loan is settled early.
* Journal and accounts configured once per company, overridable per loan.
* A "Journal Entries" smart button on the loan gathers every posted entry.

Nothing in this module reverses, unlinks or edits a posted entry.
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro",
    'support': "support@odomate.pro",

    'category': 'Human Resources/Payroll',
    'version': '19.0.1.0.1',
    'license': 'LGPL-3',

    'depends': ['account', 'odomate_hr_loan'],

    'data': [
        'security/ir.model.access.csv',
        'views/odomate_hr_loan_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
