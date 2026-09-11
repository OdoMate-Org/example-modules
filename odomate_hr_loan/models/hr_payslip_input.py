from odoo import fields, models


class HrPayslipInput(models.Model):
    _inherit = "hr.payslip.input"

    loan_instalment_id = fields.Many2one(
        comodel_name="odomate.hr.loan.instalment",
        string="Loan Instalment",
        ondelete="set null",
        copy=False,
        index=True,
    )
