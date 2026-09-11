from odoo import _, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    loan_count = fields.Integer(string="Loans", compute="_compute_loan_count")

    def _compute_loan_count(self):
        self.loan_count = 0
        persisted = self.filtered(lambda employee: employee.id)
        if not persisted:
            return
        grouped = self.env["odomate.hr.loan"]._read_group(
            [("employee_id", "in", persisted.ids)],
            groupby=["employee_id"],
            aggregates=["__count"],
        )
        counts = {employee.id: count for employee, count in grouped}
        for employee in persisted:
            employee.loan_count = counts.get(employee.id, 0)

    def action_view_employee_loans(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Loans"),
            "res_model": "odomate.hr.loan",
            "view_mode": "list,form",
            "domain": [("employee_id", "=", self.id)],
            "context": {"default_employee_id": self.id},
        }
