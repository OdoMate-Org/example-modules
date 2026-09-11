from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    loan_allow_multiple = fields.Boolean(
        string="Allow Multiple Running Loans",
        default=False,
        help="When disabled, an employee cannot get a second loan approved "
        "while an earlier one still has an outstanding balance.",
    )
    loan_max_amount = fields.Monetary(
        string="Maximum Loan Amount",
        currency_field="currency_id",
        default=0.0,
        help="Largest principal that may be approved. Zero means no cap.",
    )
