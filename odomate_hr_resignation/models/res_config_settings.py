from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    resignation_manager_approval_required = fields.Boolean(
        related='company_id.resignation_manager_approval_required',
        string="Manager Approval on Resignations",
        readonly=False,
    )
