from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

ADVANCE_STATES = [
    ("draft", "Draft"),
    ("submitted", "Submitted"),
    ("approved", "Approved"),
    ("paid", "Paid"),
    ("closed", "Closed"),
    ("refused", "Refused"),
    ("cancelled", "Cancelled"),
]

OUTSTANDING_STATES = ("approved", "paid")

ADVANCE_INPUT_CODE = "ADV_DEDUCT"


class OdomateHrSalaryAdvance(models.Model):
    _name = "odomate.hr.salary.advance"
    _description = "Employee Salary Advance"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(
        string="Reference",
        readonly=True,
        copy=False,
        default="/",
        index=True,
    )
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True,
        ondelete="restrict",
        tracking=True,
        index=True,
    )
    department_id = fields.Many2one(
        comodel_name="hr.department",
        string="Department",
        related="employee_id.department_id",
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        related="company_id.currency_id",
        readonly=True,
    )
    date = fields.Date(
        string="Request Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        help="Date of the request. The wage and the contract in force are "
             "resolved against this date.",
    )
    amount = fields.Monetary(
        string="Advance Amount",
        required=True,
        currency_field="currency_id",
        tracking=True,
    )
    reason = fields.Text(
        string="Reason",
        required=True,
    )
    state = fields.Selection(
        selection=ADVANCE_STATES,
        string="Status",
        default="draft",
        required=True,
        copy=False,
        tracking=True,
        index=True,
    )
    refusal_reason = fields.Text(
        string="Refusal Reason",
        readonly=True,
        copy=False,
    )
    payment_date = fields.Date(
        string="Payment Date",
        readonly=True,
        copy=False,
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Payment Journal",
        readonly=True,
        copy=False,
        domain="[('type', 'in', ['bank', 'cash'])]",
    )
    payment_id = fields.Many2one(
        comodel_name="account.payment",
        string="Payment",
        readonly=True,
        copy=False,
        ondelete="set null",
    )
    has_payment = fields.Boolean(
        string="Has Payment",
        compute="_compute_has_payment",
        compute_sudo=True,
    )
    recovered_amount = fields.Monetary(
        string="Recovered",
        currency_field="currency_id",
        default=0.0,
        readonly=True,
        copy=False,
    )
    outstanding_amount = fields.Monetary(
        string="Outstanding",
        currency_field="currency_id",
        compute="_compute_outstanding_amount",
        store=True,
        aggregator="sum",
    )
    monthly_wage = fields.Monetary(
        string="Monthly Salary",
        currency_field="currency_id",
        compute="_compute_monthly_wage",
        compute_sudo=True,
    )
    max_allowed_amount = fields.Monetary(
        string="Maximum Allowed",
        currency_field="currency_id",
        compute="_compute_max_allowed_amount",
        compute_sudo=True,
    )
    already_outstanding_amount = fields.Monetary(
        string="Already Outstanding",
        currency_field="currency_id",
        compute="_compute_already_outstanding_amount",
        compute_sudo=True,
    )
    available_amount = fields.Monetary(
        string="Available",
        currency_field="currency_id",
        compute="_compute_available_amount",
        compute_sudo=True,
    )

    _name_uniq = models.Constraint(
        "UNIQUE(name)",
        "The salary advance reference must be unique.",
    )
    _amount_positive = models.Constraint(
        "CHECK(amount > 0)",
        "The advance amount must be strictly positive.",
    )
    _recovered_amount_positive = models.Constraint(
        "CHECK(recovered_amount >= 0)",
        "The recovered amount cannot be negative.",
    )

    # --------------------------------------------------------------------- #
    # Compute
    # --------------------------------------------------------------------- #

    @api.depends("payment_id")
    def _compute_has_payment(self):
        for advance in self:
            advance.has_payment = bool(advance.payment_id)

    @api.depends("amount", "recovered_amount")
    def _compute_outstanding_amount(self):
        for advance in self:
            advance.outstanding_amount = advance.amount - advance.recovered_amount

    @api.depends("employee_id", "date")
    def _compute_monthly_wage(self):
        for advance in self:
            version = advance._get_version_at_date()
            advance.monthly_wage = version.wage if version else 0.0

    @api.depends(
        "monthly_wage",
        "company_id",
        "company_id.advance_max_percent",
        "company_id.advance_max_amount",
    )
    def _compute_max_allowed_amount(self):
        for advance in self:
            company = advance.company_id or self.env.company
            allowed = advance.monthly_wage * (company.advance_max_percent / 100.0)
            if company.advance_max_amount > 0 and allowed > company.advance_max_amount:
                allowed = company.advance_max_amount
            advance.max_allowed_amount = max(allowed, 0.0)

    @api.depends("employee_id", "company_id", "state", "amount", "recovered_amount")
    def _compute_already_outstanding_amount(self):
        for advance in self:
            others = advance._get_other_outstanding_advances()
            advance.already_outstanding_amount = sum(
                others.mapped("outstanding_amount")
            )

    @api.depends("max_allowed_amount", "already_outstanding_amount")
    def _compute_available_amount(self):
        for advance in self:
            advance.available_amount = max(
                advance.max_allowed_amount - advance.already_outstanding_amount, 0.0
            )

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #

    def _get_version_at_date(self):
        """Return the ``hr.version`` in force for this advance's ``date``.

        Versions are chronological, so the one in force is the latest whose
        ``date_version`` is on or before the requested date; it stops applying
        once its own ``date_end`` has passed. ``date`` is required and always
        defaulted, so there is exactly one lookup path here and no separate
        "today's version" fallback to keep in sync.
        """
        self.ensure_one()
        if not self.employee_id or not self.date:
            return self.env["hr.version"]
        version = self.env["hr.version"].sudo().search(
            [
                ("employee_id", "=", self.employee_id.id),
                ("date_version", "<=", self.date),
            ],
            order="date_version desc, id desc",
            limit=1,
        )
        if version and version.date_end and version.date_end < self.date:
            return self.env["hr.version"]
        return version

    def _get_other_outstanding_advances(self):
        """Other advances of the same employee still carrying a balance."""
        self.ensure_one()
        if not self.employee_id:
            return self.browse()
        domain = [
            ("employee_id", "=", self.employee_id.id),
            ("state", "in", OUTSTANDING_STATES),
        ]
        if self.company_id:
            domain.append(("company_id", "=", self.company_id.id))
        origin_id = self._origin.id
        if origin_id:
            domain.append(("id", "!=", origin_id))
        return self.sudo().search(domain)

    def _check_hr_officer(self):
        if not self.env.su and not self.env.user.has_group("hr.group_hr_user"):
            raise AccessError(_(
                "Only HR officers can process salary advance requests."
            ))

    def _check_eligibility(self):
        """Company-policy gate, applied on submit and again on approve."""
        for advance in self:
            employee = advance.employee_id
            if not advance._get_version_at_date():
                raise ValidationError(_(
                    "%(employee)s has no contract in force on %(date)s. A salary "
                    "advance can only be granted against an active contract.",
                    employee=employee.display_name,
                    date=fields.Date.to_string(advance.date),
                ))
            company = advance.company_id
            if not company.advance_allow_multiple:
                others = advance._get_other_outstanding_advances()
                if others:
                    raise ValidationError(_(
                        "%(employee)s already has an outstanding salary advance "
                        "(%(refs)s). Enable \"Allow Multiple Open Advances\" in "
                        "the company settings to grant a second one.",
                        employee=employee.display_name,
                        refs=", ".join(others.mapped("name")),
                    ))
            currency = advance.currency_id or company.currency_id
            if currency.compare_amounts(advance.amount, advance.available_amount) > 0:
                raise ValidationError(_(
                    "The requested amount exceeds what %(employee)s may take. "
                    "Maximum allowed: %(maximum)s; already outstanding: "
                    "%(outstanding)s; still available: %(available)s.",
                    employee=employee.display_name,
                    maximum=advance.max_allowed_amount,
                    outstanding=advance.already_outstanding_amount,
                    available=advance.available_amount,
                ))

    @api.constrains("state", "amount", "employee_id", "date", "company_id")
    def _check_eligibility_on_active_states(self):
        active = self.filtered(lambda a: a.state in ("submitted", "approved"))
        if active:
            active._check_eligibility()

    @api.constrains("journal_id", "company_id")
    def _check_journal_company(self):
        for advance in self:
            journal = advance.journal_id
            if journal and journal.company_id != advance.company_id:
                raise ValidationError(_(
                    "The payment journal %(journal)s does not belong to "
                    "%(company)s.",
                    journal=journal.display_name,
                    company=advance.company_id.display_name,
                ))

    # --------------------------------------------------------------------- #
    # ORM
    # --------------------------------------------------------------------- #

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == "/":
                company_id = vals.get("company_id") or self.env.company.id
                vals["name"] = self.env["ir.sequence"].with_company(
                    company_id
                ).next_by_code("odomate.hr.salary.advance") or "/"
        return super().create(vals_list)

    def write(self, vals):
        if "amount" in vals:
            locked = self.filtered(lambda a: a.state in ("paid", "closed"))
            if locked:
                raise UserError(_(
                    "The amount of an advance that has already been paid can no "
                    "longer be changed (%s).",
                    ", ".join(locked.mapped("name")),
                ))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_disbursed(self):
        disbursed = self.filtered(lambda a: a.state in ("paid", "closed"))
        if disbursed:
            raise UserError(_(
                "A salary advance that has been disbursed cannot be deleted "
                "(%s).",
                ", ".join(disbursed.mapped("name")),
            ))

    # --------------------------------------------------------------------- #
    # Workflow
    # --------------------------------------------------------------------- #

    def action_submit(self):
        self._check_hr_officer()
        for advance in self:
            if advance.state != "draft":
                raise UserError(_(
                    "Only a draft advance can be submitted (%s).", advance.name
                ))
        self._check_eligibility()
        self.write({"state": "submitted"})
        return True

    def action_approve(self):
        self._check_hr_officer()
        for advance in self:
            if advance.state != "submitted":
                raise UserError(_(
                    "Only a submitted advance can be approved (%s).", advance.name
                ))
        self._check_eligibility()
        self.write({"state": "approved"})
        return True

    def action_cancel(self):
        self._check_hr_officer()
        for advance in self:
            if advance.state not in ("draft", "submitted", "approved"):
                raise UserError(_(
                    "A %(state)s advance can no longer be cancelled (%(name)s).",
                    state=advance._state_label(),
                    name=advance.name,
                ))
        self.write({"state": "cancelled"})
        return True

    def action_open_refuse_wizard(self):
        self.ensure_one()
        self._check_hr_officer()
        if self.state != "submitted":
            raise UserError(_("Only a submitted advance can be refused."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Refuse Salary Advance"),
            "res_model": "odomate.hr.salary.advance.refuse",
            "view_mode": "form",
            "target": "new",
            "context": {"default_advance_id": self.id},
        }

    def action_open_pay_wizard(self):
        self.ensure_one()
        self._check_hr_officer()
        if self.state != "approved":
            raise UserError(_("Only an approved advance can be paid."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Pay Salary Advance"),
            "res_model": "odomate.hr.salary.advance.pay",
            "view_mode": "form",
            "target": "new",
            "context": {"default_advance_id": self.id},
        }

    def _process_refusal(self, refusal_reason):
        self.ensure_one()
        self._check_hr_officer()
        if self.state != "submitted":
            raise UserError(_("Only a submitted advance can be refused."))
        self.write({"state": "refused", "refusal_reason": refusal_reason})
        self.message_post(body=_("Advance refused: %s", refusal_reason))
        return True

    def _process_payment(self, payment_date, journal):
        """Disburse the advance through a posted ``account.payment``.

        Everything happens in one transaction: if ``action_post()`` raises, the
        state change rolls back with it and no orphaned draft payment is left
        behind. ``sudo()`` is scoped to the create + post pair only, so an HR
        officer without an accounting role can pay an advance yet still cannot
        open the resulting journal entry.
        """
        self.ensure_one()
        self._check_hr_officer()
        if self.state != "approved":
            raise UserError(_("Only an approved advance can be paid."))

        company = self.company_id
        if not company.advance_journal_id:
            raise UserError(_(
                "No salary advance journal is configured for %(company)s. Set "
                "\"Salary Advance Journal\" under Settings > Employees > Salary "
                "Advances before disbursing an advance.",
                company=company.display_name,
            ))
        if journal.company_id != company:
            raise UserError(_(
                "The journal %(journal)s does not belong to %(company)s.",
                journal=journal.display_name,
                company=company.display_name,
            ))

        partner = self.employee_id.work_contact_id
        if not partner:
            raise UserError(_(
                "%(employee)s has no work contact. A work contact is required to "
                "disburse a salary advance; set it on the employee's HR Settings "
                "tab first.",
                employee=self.employee_id.display_name,
            ))

        payment = self.env["account.payment"].sudo().with_company(company).create({
            "payment_type": "outbound",
            "partner_type": "supplier",
            "partner_id": partner.id,
            "journal_id": journal.id,
            "amount": self.amount,
            "date": payment_date,
            "memo": self.name,
        })
        payment.action_post()

        self.write({
            "payment_id": payment.id,
            "payment_date": payment_date,
            "journal_id": journal.id,
            "state": "paid",
        })
        self.message_post(body=_(
            "Advance disbursed on %(date)s through journal %(journal)s.",
            date=fields.Date.to_string(payment_date),
            journal=journal.display_name,
        ))
        return True

    def _register_recovery(self, amount):
        """Book ``amount`` recovered by a confirmed payslip.

        Called from ``hr.payslip.action_payslip_done`` as a side effect of the
        host workflow, so it never raises: an advance that has drifted out of
        the recoverable states is simply skipped, and the recovered figure is
        clamped so a re-confirm can never over-recover.
        """
        self.ensure_one()
        advance = self.sudo()
        if advance.state not in ("paid", "closed"):
            return False
        currency = advance.currency_id
        recovered = min(advance.amount, advance.recovered_amount + amount)
        if currency.compare_amounts(recovered, advance.recovered_amount) <= 0:
            return False
        vals = {"recovered_amount": recovered}
        if advance.state == "paid" and currency.is_zero(advance.amount - recovered):
            vals["state"] = "closed"
        advance.write(vals)
        return True

    def _state_label(self):
        self.ensure_one()
        return dict(ADVANCE_STATES).get(self.state, self.state)

    # --------------------------------------------------------------------- #
    # Smart buttons
    # --------------------------------------------------------------------- #

    def action_view_payment(self):
        """Open the disbursement payment.

        Deliberately *not* sudo'd: a user without accounting rights gets an
        AccessError rather than a view of the books.
        """
        self.ensure_one()
        if not self.payment_id:
            raise UserError(_("This advance has no payment yet."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Payment"),
            "res_model": "account.payment",
            "res_id": self.payment_id.id,
            "view_mode": "form",
        }

    def action_view_journal_entry(self):
        self.ensure_one()
        move = self.payment_id.sudo().move_id
        if not move:
            raise UserError(_("This advance has no journal entry yet."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Journal Entry"),
            "res_model": "account.move",
            "res_id": move.id,
            "view_mode": "form",
        }
