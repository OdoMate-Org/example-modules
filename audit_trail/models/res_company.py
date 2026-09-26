from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    audit_cleanup_enabled = fields.Boolean(
        string='Audit History Clean-up', default=False,
        help="When switched on, a scheduled job removes recorded audit history older than the chosen age.")
    audit_cleanup_age_months = fields.Integer(
        string='Keep Audit History (Months)', default=6,
        help="Recorded audit history older than this number of months is removed by the clean-up job.")

    _audit_cleanup_age_positive = models.Constraint(
        'CHECK(audit_cleanup_age_months > 0)',
        "The audit history age must be at least one month.",
    )

    @api.constrains('audit_cleanup_age_months')
    def _check_audit_cleanup_age_months(self):
        if any(company.audit_cleanup_age_months < 1 for company in self):
            raise ValidationError(_("The audit history age must be at least one month."))
