from odoo import fields, models


class HrPayslipInput(models.Model):
    _inherit = "hr.payslip.input"

    advance_id = fields.Many2one(
        comodel_name="odomate.hr.salary.advance",
        string="Salary Advance",
        ondelete="set null",
        index="btree_not_null",
    )
