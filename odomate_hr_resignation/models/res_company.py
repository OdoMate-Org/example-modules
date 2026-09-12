from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    resignation_manager_approval_required = fields.Boolean(
        string="Manager Approval on Resignations",
        default=True,
        help="When enabled, a resignation must be approved by the employee's "
             "manager before HR can start the clearance checklist.",
    )
