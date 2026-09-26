from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    audit_cleanup_enabled = fields.Boolean(related='company_id.audit_cleanup_enabled', readonly=False)
    audit_cleanup_age_months = fields.Integer(related='company_id.audit_cleanup_age_months', readonly=False)
