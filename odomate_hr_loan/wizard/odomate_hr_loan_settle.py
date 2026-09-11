from odoo import _, fields, models
from odoo.exceptions import UserError


class OdomateHrLoanSettle(models.TransientModel):
    _name = "odomate.hr.loan.settle"
    _description = "Settle a Loan Early"

    loan_id = fields.Many2one(
        comodel_name="odomate.hr.loan",
        string="Loan",
        required=True,
        ondelete="cascade",
    )
    settlement_date = fields.Date(
        string="Settlement Date",
        required=True,
        default=fields.Date.context_today,
    )
    payment_reference = fields.Char(string="Payment Reference", required=True)

    def action_settle(self):
        self.ensure_one()
        loan = self.loan_id
        if loan.state != "approved":
            raise UserError(
                _(
                    "Only an approved loan can be settled early (%s is not).",
                    loan.name,
                )
            )
        outstanding = loan.instalment_ids.filtered(
            lambda instalment: instalment.state == "scheduled"
        )
        if not outstanding:
            raise UserError(
                _(
                    "Loan %s has no outstanding instalment left to settle.",
                    loan.name,
                )
            )
        settled_amount = sum(outstanding.mapped("total_amount"))
        outstanding.write({"state": "cancelled"})
        loan.write(
            {
                "settlement_date": self.settlement_date,
                "settlement_reference": self.payment_reference,
            }
        )
        if loan.instalments_remaining == 0:
            loan.write({"state": "closed"})
        loan.message_post(
            body=_(
                "Loan settled early on %(date)s for %(amount)s covering "
                "%(count)s remaining instalment(s). Reference: %(reference)s",
                date=self.settlement_date,
                amount=settled_amount,
                count=len(outstanding),
                reference=self.payment_reference,
            )
        )
        return {"type": "ir.actions.act_window_close"}
