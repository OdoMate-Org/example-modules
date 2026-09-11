from odoo import models


class OdomateHrLoanSettle(models.TransientModel):
    _inherit = "odomate.hr.loan.settle"

    def action_settle(self):
        """Post the settlement entry around the host module's own settlement.

        ``odomate_hr_loan`` applies the settlement inside this wizard method and
        exposes no loan-side hook, so this is the only seam available. The work
        itself lives on ``odomate.hr.loan``: the outstanding balance is read
        before ``super()`` cancels the remaining instalments, and the
        configuration is checked before the loan reaches ``closed`` so a missing
        journal leaves the loan untouched.
        """
        self.ensure_one()
        loan = self.loan_id
        pending = loan.instalment_ids.filtered(
            lambda instalment: instalment.state == "scheduled"
        )
        principal = sum(pending.mapped("principal_amount"))
        interest = sum(pending.mapped("interest_amount"))
        if pending and loan.state == "approved":
            loan._check_loan_accounting_setup()
            loan._get_loan_partner()
        result = super().action_settle()
        if pending:
            loan._post_loan_settlement_entry(
                self.settlement_date, principal, interest
            )
        return result
