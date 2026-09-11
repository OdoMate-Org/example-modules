{
    'name': "Employee Loans",

    'summary': "Employee loan management with instalment repayment schedule, "
               "salary advance recovery and payroll deduction. HR loan "
               "request, approval workflow, interest, early settlement.",

    'description': """
Employee Loans
==============

Employee loan requests with an approval-time repayment schedule and automatic
recovery from payslips through the OCA ``payroll`` module.

* Loan requests with amount, purpose, instalment count and flat interest.
* Approval-time repayment schedule stored as real instalment records.
* Automatic payslip recovery via a shipped ``LOAN_REPAY`` salary rule.
* Defer an instalment by one month, or settle a loan early.
* Per-company policy: one-loan-at-a-time and a maximum loan amount.
* Record rules so employees see only their own loans; multi-company safe.

See ``doc/USER_GUIDE.md`` for the full guide, including the one-time salary
structure setup step.
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro",
    'support': "support@odomate.pro",

    'category': 'Human Resources/Payroll',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',

    'depends': ['hr', 'payroll', 'mail', 'base_setup'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/hr_salary_rule_data.xml',
        'views/odomate_hr_loan_views.xml',
        'views/odomate_hr_loan_instalment_views.xml',
        'wizard/odomate_hr_loan_defer_views.xml',
        'wizard/odomate_hr_loan_settle_views.xml',
        'views/hr_employee_views.xml',
        'views/res_config_settings_views.xml',
        'views/odomate_hr_loan_menus.xml',
    ],
    'demo': [
        'demo/odomate_hr_loan_demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
