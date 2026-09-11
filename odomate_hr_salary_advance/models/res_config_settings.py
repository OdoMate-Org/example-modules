from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    advance_max_percent = fields.Float(
        related="company_id.advance_max_percent",
        readonly=False,
    )
    advance_max_amount = fields.Monetary(
        related="company_id.advance_max_amount",
        currency_field="advance_currency_id",
        readonly=False,
    )
    advance_allow_multiple = fields.Boolean(
        related="company_id.advance_allow_multiple",
        readonly=False,
    )
    advance_journal_id = fields.Many2one(
        related="company_id.advance_journal_id",
        readonly=False,
    )
    advance_currency_id = fields.Many2one(
        related="company_id.currency_id",
        string="Salary Advance Currency",
        readonly=True,
    )
