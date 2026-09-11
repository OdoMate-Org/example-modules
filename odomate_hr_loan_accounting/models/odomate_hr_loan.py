from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .res_company import LOAN_JOURNAL_DOMAIN


class OdomateHrLoan(models.Model):
    _inherit = "odomate.hr.loan"

    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
        check_company=True,
        domain=LOAN_JOURNAL_DOMAIN,
        default=lambda self: self.env.company.loan_journal_id,
        groups="account.group_account_invoice,account.group_account_readonly",
        help="Journal the three loan entries are posted in. Its default "
        "account carries the counterpart of every line.",
    )
    receivable_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Loan Receivable Account",
        check_company=True,
        default=lambda self: self.env.company.loan_receivable_account_id,
        groups="account.group_account_invoice,account.group_account_readonly",
        help="Account debited when the loan is paid out and credited as the "
        "instalments come back.",
    )
    interest_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Interest Income Account",
        check_company=True,
        default=lambda self: self.env.company.loan_interest_income_account_id,
        groups="account.group_account_invoice,account.group_account_readonly",
        help="Account credited with the interest part of each recovered "
        "instalment. Required as soon as the loan carries interest.",
    )
    disbursement_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Disbursement Entry",
        readonly=True,
        copy=False,
        index="btree_not_null",
        groups="account.group_account_invoice,account.group_account_readonly",
    )
    settlement_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Settlement Entry",
        readonly=True,
        copy=False,
        index="btree_not_null",
        groups="account.group_account_invoice,account.group_account_readonly",
    )
    account_move_count = fields.Integer(
        string="Journal Entries",
        compute="_compute_account_move_count",
        groups="account.group_account_invoice,account.group_account_readonly",
    )

    @api.depends(
        "disbursement_move_id",
        "settlement_move_id",
        "instalment_ids.account_move_id",
    )
    def _compute_account_move_count(self):
        for loan in self:
            loan.account_move_count = len(loan._get_account_moves())

    @api.onchange("employee_id")
    def _onchange_employee_id_accounting_defaults(self):
        for loan in self:
            company = loan.employee_id.company_id
            if not company or company == self.env.company:
                continue
            loan.journal_id = company.loan_journal_id
            loan.receivable_account_id = company.loan_receivable_account_id
            loan.interest_account_id = company.loan_interest_income_account_id

    def _get_account_moves(self):
        self.ensure_one()
        moves = self.disbursement_move_id | self.settlement_move_id
        return moves | self.instalment_ids.account_move_id

    def action_view_account_moves(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Journal Entries"),
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [("id", "in", self._get_account_moves().ids)],
            "context": {"create": False},
        }

    def _find_loan_partner(self):
        self.ensure_one()
        return self.employee_id.work_contact_id or self.employee_id.user_id.partner_id

    def _get_loan_partner(self):
        self.ensure_one()
        partner = self._find_loan_partner()
        if not partner:
            raise UserError(
                _(
                    "%(employee)s has neither a work contact nor a linked user "
                    "with a contact, so the entries of loan %(loan)s cannot name "
                    "a partner. Set a work contact on the employee first.",
                    employee=self.employee_id.display_name,
                    loan=self.name,
                )
            )
        return partner

    def _get_loan_accounting_config(self):
        """Elevated access to this loan's own posting configuration and links.

        ``journal_id``, ``receivable_account_id``, ``interest_account_id``,
        ``disbursement_move_id``, ``settlement_move_id`` and
        ``account_move_count`` are ``groups``-restricted to accounting users,
        and ``journal_id``/``receivable_account_id``/``interest_account_id``
        point at ``account.journal``/``account.account`` records an HR or
        payroll officer has no access to either. Approving a loan or
        recovering an instalment has to decide whether and how to post, and
        then link what it posted, without the officer holding any accounting
        right — so those six reads and writes go through this ``sudo()``
        copy. Nothing else about the loan is read through it: state, amount,
        employee and the partner lookup stay on the caller's own rights.
        """
        self.ensure_one()
        return self.sudo()

    def _has_loan_accounting_setup(self):
        self.ensure_one()
        config = self._get_loan_accounting_config()
        if not (config.journal_id and config.journal_id.default_account_id):
            return False
        if not config.receivable_account_id:
            return False
        if self.interest_percentage and not config.interest_account_id:
            return False
        return bool(self._find_loan_partner())

    def _check_loan_accounting_setup(self):
        self.ensure_one()
        config = self._get_loan_accounting_config()
        if not config.journal_id:
            raise UserError(
                _(
                    "Loan %s has no journal. Pick one on the Accounting tab, or "
                    "set a default journal for employee loans in the Accounting "
                    "settings.",
                    self.name,
                )
            )
        if not config.journal_id.default_account_id:
            raise UserError(
                _(
                    "The journal %(journal)s has no default account, so the "
                    "counterpart line of loan %(loan)s cannot be built. Set a "
                    "default account on that journal first.",
                    journal=config.journal_id.display_name,
                    loan=self.name,
                )
            )
        if not config.receivable_account_id:
            raise UserError(
                _(
                    "Loan %s has no loan receivable account. Pick one on the "
                    "Accounting tab, or set a default in the Accounting settings.",
                    self.name,
                )
            )
        if self.interest_percentage and not config.interest_account_id:
            raise UserError(
                _(
                    "Loan %s carries interest, so it needs an interest income "
                    "account. Pick one on the Accounting tab, or set a default "
                    "in the Accounting settings.",
                    self.name,
                )
            )
        return True

    def _create_and_post_move(self, move_date, ref, line_vals):
        """Create and post one journal entry for this loan.

        ``sudo()`` covers exactly the create + post pair, so an HR officer who
        approves a loan, or a payroll officer who confirms a payslip, posts the
        entry without holding accounting rights — and still cannot read it
        afterwards.
        """
        self.ensure_one()
        move = (
            self.env["account.move"]
            .sudo()
            .with_company(self.company_id)
            .create(
                {
                    "move_type": "entry",
                    "journal_id": self.journal_id.id,
                    "date": move_date,
                    "ref": ref,
                    "line_ids": line_vals,
                }
            )
        )
        move.action_post()
        return move

    def _post_loan_disbursement_entry(self):
        self.ensure_one()
        config = self._get_loan_accounting_config()
        if config.disbursement_move_id:
            return config.disbursement_move_id
        partner = self._get_loan_partner()
        ref = _("Loan %s - Disbursement", self.name)
        line_vals = [
            (
                0,
                0,
                {
                    "name": ref,
                    "account_id": config.receivable_account_id.id,
                    "partner_id": partner.id,
                    "debit": self.amount,
                    "credit": 0.0,
                },
            ),
            (
                0,
                0,
                {
                    "name": ref,
                    "account_id": config.journal_id.default_account_id.id,
                    "debit": 0.0,
                    "credit": self.amount,
                },
            ),
        ]
        move = config._create_and_post_move(
            fields.Date.context_today(self), ref, line_vals
        )
        config.disbursement_move_id = move
        return move

    def _post_loan_settlement_entry(self, settlement_date, principal, interest):
        """Post the entry that clears what is left of the loan.

        The debit is the outstanding balance the employee actually pays. The
        credit side is split the way the instalments themselves are split,
        because only the principal was ever debited to the receivable: crediting
        it with principal plus interest would leave every settled loan carrying
        the unearned interest as a permanent credit balance.
        """
        self.ensure_one()
        config = self._get_loan_accounting_config()
        if config.settlement_move_id:
            return config.settlement_move_id
        currency = self.currency_id or self.company_id.currency_id
        outstanding = principal + interest
        if currency.is_zero(outstanding):
            return self.env["account.move"]
        partner = self._get_loan_partner()
        ref = _("Loan %s - Settlement", self.name)
        line_vals = [
            (
                0,
                0,
                {
                    "name": ref,
                    "account_id": config.journal_id.default_account_id.id,
                    "debit": outstanding,
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
        move = config._create_and_post_move(settlement_date, ref, line_vals)
        config.settlement_move_id = move
        return move

    def action_approve(self):
        for loan in self:
            if loan.state == "submitted":
                loan._check_loan_accounting_setup()
                loan._get_loan_partner()
        result = super().action_approve()
        for loan in self:
            loan._post_loan_disbursement_entry()
        return result
