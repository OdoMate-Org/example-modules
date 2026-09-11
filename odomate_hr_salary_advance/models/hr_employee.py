from odoo import _, api, fields, models

from .odomate_hr_salary_advance import OUTSTANDING_STATES


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    advance_count = fields.Integer(
        string="Outstanding Advances",
        compute="_compute_advance_count",
        compute_sudo=True,
    )

    @api.depends("name")
    def _compute_advance_count(self):
        self.advance_count = 0
        if not self.ids:
            return
        grouped = self.env["odomate.hr.salary.advance"].sudo()._read_group(
            [
                ("employee_id", "in", self.ids),
                ("state", "in", OUTSTANDING_STATES),
            ],
            groupby=["employee_id"],
            aggregates=["__count"],
        )
        counts = {employee.id: count for employee, count in grouped}
        for employee in self:
            employee.advance_count = counts.get(employee.id, 0)

    def action_view_salary_advances(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Salary Advances"),
            "res_model": "odomate.hr.salary.advance",
            "view_mode": "list,form",
            "domain": [
                ("employee_id", "=", self.id),
                ("state", "in", list(OUTSTANDING_STATES)),
            ],
            "context": {"default_employee_id": self.id},
        }
