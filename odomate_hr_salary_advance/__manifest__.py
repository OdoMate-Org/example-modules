{
    'name': "Employee Salary Advance",

    'summary': "Employee salary advance requests, approvals and payroll "
               "recovery. Salary advance, payroll advance, wage advance, "
               "employee loan alternative, HR advance policy, payslip "
               "deduction, advance payment, salary advance limit",

    'description': """
Employee Salary Advance
=======================

Record a salary advance request, check it against company policy, disburse it
through a real ``account.payment`` and recover the outstanding balance on the
next payslip.
    """,

    'author': "OdoMate",
    'website': "https://odomate.pro",
    'support': "support@odomate.pro",

    'category': 'Human Resources/Payroll',
    'version': '19.0.1.0.3',
    'license': 'LGPL-3',

    'depends': [
        'hr',
        'payroll',
        'account',
        'mail',
    ],

    'data': [
        'security/odomate_hr_salary_advance_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/hr_salary_rule_data.xml',
        'views/odomate_hr_salary_advance_views.xml',
        'wizard/odomate_hr_salary_advance_wizard_views.xml',
        'views/hr_employee_views.xml',
        'views/res_config_settings_views.xml',
        'views/odomate_hr_salary_advance_menus.xml',
    ],
    'demo': [
        'demo/odomate_hr_salary_advance_demo.xml',
    ],

    'post_init_hook': 'post_init_hook',

    'installable': True,
    'application': False,
    'auto_install': False,
}
