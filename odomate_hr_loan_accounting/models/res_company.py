from odoo import fields, models

LOAN_JOURNAL_DOMAIN = "[('type', 'in', ('bank', 'cash', 'general'))]"


class ResCompany(models.Model):
    _inherit = "res.company"

    loan_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Employee Loan Journal",
        domain=LOAN_JOURNAL_DOMAIN,
        help="Journal used for the disbursement, recovery and settlement "
        "entries of employee loans. Sale and purchase journals are excluded "
        "because these entries carry no customer or vendor document.",
    )
    loan_receivable_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Employee Loan Receivable Account",
        help="Asset account carrying what employees still owe. It is debited "
        "when a loan is paid out and credited as instalments come back.",
    )
    loan_interest_income_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Employee Loan Interest Income Account",
        help="Income account credited with the interest part of every "
        "recovered instalment. Only needed for loans that carry interest.",
    )
