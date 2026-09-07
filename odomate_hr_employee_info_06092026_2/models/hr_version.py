from odoo import api, fields, models


class HrVersion(models.Model):
    _inherit = 'hr.version'

    notice_period = fields.Integer(
        string="Notice Period (Days)",
        help="Number of days of notice attached to this version. Filled in from the company "
             "default when the version is created; later changes to the company default do not "
             "alter versions that already exist.",
    )
    odomate_notice_period_editable = fields.Boolean(
        string="Can Edit Notice Period",
        compute='_compute_odomate_notice_period_editable',
    )

    _notice_period_positive = models.Constraint(
        'CHECK(notice_period >= 0)',
        "The notice period cannot be negative.",
    )

    @api.depends()
    @api.depends_context('uid')
    def _compute_odomate_notice_period_editable(self):
        editable = self.env.user.has_group('hr.group_hr_manager')
        for version in self:
            version.odomate_notice_period_editable = editable

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if 'notice_period' in fields_list and not defaults.get('notice_period'):
            company = self.env['res.company'].browse(
                self.env.context.get('default_company_id')
            ) or self.env.company
            defaults['notice_period'] = company.hr_default_notice_period_days
        return defaults
