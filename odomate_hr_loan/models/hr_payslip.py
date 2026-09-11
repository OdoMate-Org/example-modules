from odoo import _, fields, models

LOAN_RULE_INPUT_XMLID = "odomate_hr_loan.hr_rule_input_loan_repayment"


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def _get_loan_rule_input_code(self):
        rule_input = self.env.ref(LOAN_RULE_INPUT_XMLID, raise_if_not_found=False)
        return rule_input.code if rule_input else False

    def _get_loan_input_vals(self, contracts, date_from, date_to):
        self.ensure_one()
        if not self.employee_id or not date_from or not date_to:
            return []
        code = self._get_loan_rule_input_code()
        if not code:
            return []
        contract = self.contract_id
        if not contract and contracts:
            contract = contracts[:1]
        if not contract:
            return []
        instalments = (
            self.env["odomate.hr.loan.instalment"]
            .sudo()
            .search(
                [
                    ("loan_id.employee_id", "=", self.employee_id.id),
                    ("loan_id.state", "=", "approved"),
                    ("state", "=", "scheduled"),
                    ("due_date", ">=", fields.Date.to_date(date_from)),
                    ("due_date", "<=", fields.Date.to_date(date_to)),
                ]
            )
        )
        vals_list = []
        for instalment in instalments:
            vals_list.append(
                {
                    "name": _(
                        "Loan repayment — %(loan)s #%(number)s",
                        loan=instalment.loan_id.name,
                        number=instalment.sequence,
                    ),
                    "code": code,
                    "amount": instalment.total_amount,
                    "contract_id": contract.id,
                    "loan_instalment_id": instalment.id,
                    "sequence": 100 + instalment.sequence,
                }
            )
        return vals_list

    def get_inputs(self, contracts, date_from, date_to):
        res = super().get_inputs(contracts, date_from, date_to)
        for payslip in self:
            res = res + payslip._get_loan_input_vals(contracts, date_from, date_to)
        return res

    def _refresh_loan_inputs(self):
        self.ensure_one()
        if self.state not in ("draft", "verify"):
            return
        stale = self.input_line_ids.filtered(lambda line: line.loan_instalment_id)
        if stale:
            stale.unlink()
        vals_list = self._get_loan_input_vals(
            self._get_employee_contracts(), self.date_from, self.date_to
        )
        if vals_list:
            self.write(
                {"input_line_ids": [(0, 0, vals) for vals in vals_list]}
            )

    def compute_sheet(self):
        for payslip in self:
            payslip._refresh_loan_inputs()
        return super().compute_sheet()

    def _recover_loan_instalments(self):
        loans = self.env["odomate.hr.loan"].sudo()
        for payslip in self:
            instalments = payslip.input_line_ids.loan_instalment_id.sudo().filtered(
                lambda instalment: instalment.state == "scheduled"
            )
            if not instalments:
                continue
            instalments.write({"state": "recovered", "payslip_id": payslip.id})
            loans |= instalments.loan_id
        if loans:
            loans._close_if_fully_recovered()
        return True

    def action_payslip_done(self):
        res = super().action_payslip_done()
        self._recover_loan_instalments()
        return res
