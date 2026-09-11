from odoo import _, fields, models
from odoo.tools.misc import format_date


class OdomateHrLoanInstalment(models.Model):
    _inherit = "odomate.hr.loan.instalment"

    account_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Journal Entry",
        readonly=True,
        copy=False,
        index="btree_not_null",
    )

    def write(self, vals):
        result = super().write(vals)
        if vals.get("state") == "recovered":
            for instalment in self:
                instalment._post_loan_recovery_entry()
        return result

    def _post_loan_recovery_entry(self):
        """Post the recovery entry of one instalment, at most once, for ever.

        Runs inside the payslip confirmation of the host module, so it must not
        abort it: a loan whose accounting configuration was cleared after
        approval, or whose stored figures no longer add up, is skipped and
        leaves ``account_move_id`` empty rather than raising. A locked period is
        NOT swallowed — a rejected posting has to reach the user, and re-dating
        the entry to force it through would falsify the period it belongs to.

        The three amounts are read off this row and never re-derived from the
        loan header, so a deferred or hand-adjusted instalment posts exactly
        what it stores.

        Direction: the counterpart account is debited for the total while the
        receivable is credited for the principal and the interest account for
        the interest. Recovering money has to clear the receivable the
        disbursement raised; debiting it again would leave a fully repaid loan
        showing twice its principal as still owed.
        """
        self.ensure_one()
        if self.account_move_id or self.state != "recovered":
            return self.env["account.move"]

        loan = self.loan_id
        if not loan._has_loan_accounting_setup():
            return self.env["account.move"]

        config = loan._get_loan_accounting_config()
        currency = self.currency_id or loan.company_id.currency_id
        principal = self.principal_amount
        interest = self.interest_amount
        total = self.total_amount
        if currency.compare_amounts(total, principal + interest) != 0:
            return self.env["account.move"]

        partner = loan._find_loan_partner()
        ref = _(
            "Loan %(loan)s - Instalment %(period)s",
            loan=loan.name,
            period=format_date(self.env, self.due_date, date_format="MMMM yyyy"),
        )
        line_vals = [
            (
                0,
                0,
                {
                    "name": ref,
                    "account_id": config.journal_id.default_account_id.id,
                    "debit": total,
                    "credit": 0.0,
                },
            ),
            (
                0,
                0,
                {
                    "name": ref,
                    "account_id": config.receivable_account_id.id,
                    "partner_id": partner.id,
                    "debit": 0.0,
                    "credit": principal,
                },
            ),
        ]
        if not currency.is_zero(interest):
            line_vals.append(
                (
                    0,
                    0,
                    {
                        "name": ref,
                        "account_id": config.interest_account_id.id,
                        "partner_id": partner.id,
                        "debit": 0.0,
                        "credit": interest,
                    },
                )
            )

        move = config._create_and_post_move(
            self.payslip_id.date_to or self.due_date, ref, line_vals
        )
        self.account_move_id = move
        return move
