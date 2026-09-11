from odoo import api, models

LOAN_RULE_XMLID = "odomate_hr_loan.hr_salary_rule_loan_repayment"


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    @api.model
    def _odomate_assign_loan_deduction_category(self):
        rule = self.env.ref(LOAN_RULE_XMLID, raise_if_not_found=False)
        if not rule or rule.category_id:
            return False
        category = self.env["hr.salary.rule.category"].search(
            [("code", "=", "DED")], limit=1
        )
        if not category:
            category = self.env["hr.salary.rule.category"].create(
                {"name": "Deduction", "code": "DED"}
            )
        rule.category_id = category
        return True
