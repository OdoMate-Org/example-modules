from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    leave_email_enabled = fields.Boolean(
        related='company_id.leave_email_enabled',
        readonly=False,
    )
    leave_email_type_id = fields.Many2one(
        related='company_id.leave_email_type_id',
        readonly=False,
    )
    leave_email_reply_on_failure = fields.Boolean(
        related='company_id.leave_email_reply_on_failure',
        readonly=False,
    )
    leave_email_address = fields.Char(
        string="Time Off Email Address",
        compute='_compute_leave_email_address',
        help="Address employees write to. Publish it exactly as shown here.",
    )
    leave_email_domain_missing = fields.Boolean(
        string="No Alias Domain Configured",
        compute='_compute_leave_email_address',
    )

    @api.depends('company_id', 'company_id.leave_email_alias_id')
    def _compute_leave_email_address(self):
        domain_count = self.env['mail.alias.domain'].sudo().search_count([])
        for setting in self:
            alias = setting.company_id.leave_email_alias_id
            domain_name = (
                alias.alias_domain_id.name
                or setting.company_id.alias_domain_id.name
            )
            if alias.alias_name and domain_name:
                setting.leave_email_address = "%s@%s" % (alias.alias_name, domain_name)
            else:
                setting.leave_email_address = alias.alias_name or ''
            setting.leave_email_domain_missing = not domain_count or not domain_name
