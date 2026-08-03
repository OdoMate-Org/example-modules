from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    so_order_approval = fields.Boolean(string="Sale Discount Approval")
    so_double_validation = fields.Selection(
        related='company_id.so_double_validation',
        string="Discount Approval Level",
        readonly=False,
    )
    so_double_validation_limit = fields.Float(
        related='company_id.so_double_validation_limit',
        string="Discount Approval Limit",
        readonly=False,
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        res['so_order_approval'] = (
            self.env.company.so_double_validation == 'two_step'
        )
        return res

    def set_values(self):
        super().set_values()
        self.company_id.so_double_validation = (
            'two_step' if self.so_order_approval else 'one_step'
        )
