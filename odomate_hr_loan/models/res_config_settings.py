from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    loan_currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        readonly=True,
    )
    loan_allow_multiple = fields.Boolean(
        related="company_id.loan_allow_multiple",
        readonly=False,
    )
    loan_max_amount = fields.Monetary(
        related="company_id.loan_max_amount",
        currency_field="loan_currency_id",
        readonly=False,
    )
