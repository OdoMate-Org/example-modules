from odoo import fields, models

from .res_company import LOAN_JOURNAL_DOMAIN


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    loan_journal_id = fields.Many2one(
        comodel_name="account.journal",
        related="company_id.loan_journal_id",
        readonly=False,
        check_company=True,
        domain=LOAN_JOURNAL_DOMAIN,
        string="Employee Loan Journal",
    )
    loan_receivable_account_id = fields.Many2one(
        comodel_name="account.account",
        related="company_id.loan_receivable_account_id",
        readonly=False,
        check_company=True,
        string="Employee Loan Receivable Account",
    )
    loan_interest_income_account_id = fields.Many2one(
        comodel_name="account.account",
        related="company_id.loan_interest_income_account_id",
        readonly=False,
        check_company=True,
        string="Employee Loan Interest Income Account",
    )
