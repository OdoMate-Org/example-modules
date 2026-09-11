from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.exceptions import UserError


class OdomateHrLoanDefer(models.TransientModel):
    _name = "odomate.hr.loan.defer"
    _description = "Defer a Loan Instalment"

    loan_id = fields.Many2one(
        comodel_name="odomate.hr.loan",
        string="Loan",
        required=True,
        ondelete="cascade",
    )
    instalment_id = fields.Many2one(
        comodel_name="odomate.hr.loan.instalment",
        string="Instalment to Defer",
        required=True,
        ondelete="cascade",
        domain="[('loan_id', '=', loan_id), ('state', '=', 'scheduled')]",
    )
    reason = fields.Text(string="Reason", required=True)

    def action_defer(self):
        self.ensure_one()
        loan = self.loan_id
        target = self.instalment_id
        if loan.state != "approved":
            raise UserError(
                _(
                    "Only an approved loan can have instalments deferred "
                    "(%s is not).",
                    loan.name,
                )
            )
        if target.loan_id != loan:
            raise UserError(
                _("Instalment %(instalment)s does not belong to loan %(loan)s.",
                  instalment=target.display_name,
                  loan=loan.name)
            )
        if target.state != "scheduled":
            raise UserError(
                _(
                    "Instalment %(instalment)s is %(state)s and can no longer "
                    "be deferred.",
                    instalment=target.display_name,
                    state=target.state,
                )
            )
        to_defer = loan.instalment_ids.filtered(
            lambda instalment: instalment.state == "scheduled"
            and (
                instalment.id == target.id
                or instalment.due_date > target.due_date
            )
        )
        for instalment in to_defer:
            instalment.due_date = instalment.due_date + relativedelta(months=1)
        loan.message_post(
            body=_(
                "Instalment #%(number)s and the %(count)s scheduled "
                "instalment(s) after it were deferred by one month. "
                "Reason: %(reason)s",
                number=target.sequence,
                count=len(to_defer) - 1,
                reason=self.reason,
            )
        )
        return {"type": "ir.actions.act_window_close"}
