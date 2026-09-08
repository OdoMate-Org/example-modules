from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    hr_identification_expiry_warning_days = fields.Integer(
        related='company_id.hr_identification_expiry_warning_days',
        readonly=False,
    )
    hr_passport_expiry_warning_days = fields.Integer(
        related='company_id.hr_passport_expiry_warning_days',
        readonly=False,
    )
    hr_auto_create_employee = fields.Boolean(
        related='company_id.hr_auto_create_employee',
        readonly=False,
    )
    hr_default_notice_period_days = fields.Integer(
        related='company_id.hr_default_notice_period_days',
        readonly=False,
    )
