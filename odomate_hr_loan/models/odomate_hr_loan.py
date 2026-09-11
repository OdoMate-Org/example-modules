from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

SCHEDULE_FIELDS = (
    "amount",
    "interest_percentage",
    "instalment_count",
    "first_instalment_date",
)


class OdomateHrLoan(models.Model):
    _name = "odomate.hr.loan"
    _description = "Employee Loan"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        copy=False,
        index=True,
        default="/",
    )
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True,
        index=True,
        tracking=True,
        default=lambda self: self.env.user.employee_id,
    )
    department_id = fields.Many2one(
        comodel_name="hr.department",
        string="Department",
        related="employee_id.department_id",
        store=False,
        readonly=True,
        copy=False,
    )
    job_id = fields.Many2one(
        comodel_name="hr.job",
        string="Job Position",
        related="employee_id.job_id",
        store=False,
        readonly=True,
        copy=False,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        related="employee_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        related="company_id.currency_id",
        store=True,
        readonly=True,
    )
    amount = fields.Monetary(
        string="Loan Amount",
        currency_field="currency_id",
        required=True,
        tracking=True,
        help="Principal lent to the employee. Interest is added on top of it.",
    )
    purpose = fields.Char(
        string="Purpose",
        required=True,
        help="One sentence describing why the loan is requested.",
    )
    instalment_count = fields.Integer(
        string="Number of Instalments",
        required=True,
        default=1,
        tracking=True,
    )
    first_instalment_date = fields.Date(
        string="First Instalment Date",
        required=True,
        tracking=True,
        help="Month in which the first instalment falls due.",
    )
    interest_percentage = fields.Float(
        string="Interest (%)",
        default=0.0,
        tracking=True,
        help="Flat rate applied once to the whole loan amount, then spread "
        "evenly over the instalments.",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("refused", "Refused"),
            ("cancelled", "Cancelled"),
            ("closed", "Closed"),
        ],
        string="Status",
        default="draft",
        required=True,
        copy=False,
        index=True,
        tracking=True,
    )
    refusal_reason = fields.Text(string="Refusal Reason", readonly=True, copy=False)
    settlement_date = fields.Date(string="Settlement Date", readonly=True, copy=False)
    settlement_reference = fields.Char(
        string="Settlement Reference", readonly=True, copy=False
    )
    instalment_ids = fields.One2many(
        comodel_name="odomate.hr.loan.instalment",
        inverse_name="loan_id",
        string="Repayment Schedule",
        copy=False,
    )
    has_schedule = fields.Boolean(
        string="Has a Schedule", compute="_compute_has_schedule"
    )
    total_amount = fields.Monetary(
        string="Total Repayable",
        currency_field="currency_id",
        compute="_compute_total_amount",
        store=True,
        help="Principal plus interest, as scheduled.",
    )
    recovered_amount = fields.Monetary(
        string="Recovered",
        currency_field="currency_id",
        compute="_compute_recovered_amount",
        store=True,
    )
    outstanding_amount = fields.Monetary(
        string="Outstanding",
        currency_field="currency_id",
        compute="_compute_outstanding_amount",
        store=True,
        help="Sum of the instalments still to be recovered. Cancelled "
        "instalments are excluded.",
    )
    instalments_remaining = fields.Integer(
        string="Instalments Remaining",
        compute="_compute_instalments_remaining",
        store=True,
    )

    _uniq_name = models.Constraint(
        "UNIQUE(name)",
        "The loan reference must be unique.",
    )

    @api.depends("instalment_ids")
    def _compute_has_schedule(self):
        for loan in self:
            loan.has_schedule = bool(loan.instalment_ids)

    @api.depends("instalment_ids.total_amount")
    def _compute_total_amount(self):
        for loan in self:
            loan.total_amount = sum(loan.instalment_ids.mapped("total_amount"))

    @api.depends("instalment_ids.state", "instalment_ids.total_amount")
    def _compute_recovered_amount(self):
        for loan in self:
            loan.recovered_amount = sum(
                loan.instalment_ids.filtered(
                    lambda instalment: instalment.state == "recovered"
                ).mapped("total_amount")
            )

    @api.depends("total_amount", "instalment_ids.state", "instalment_ids.total_amount")
    def _compute_outstanding_amount(self):
        for loan in self:
            loan.outstanding_amount = sum(
                loan.instalment_ids.filtered(
                    lambda instalment: instalment.state == "scheduled"
                ).mapped("total_amount")
            )

    @api.depends("instalment_ids.state")
    def _compute_instalments_remaining(self):
        for loan in self:
            loan.instalments_remaining = len(
                loan.instalment_ids.filtered(
                    lambda instalment: instalment.state == "scheduled"
                )
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("odomate.hr.loan") or "/"
                )
        return super().create(vals_list)

    def write(self, vals):
        touched_schedule_fields = [
            field_name for field_name in SCHEDULE_FIELDS if field_name in vals
        ]
        if touched_schedule_fields or "employee_id" in vals:
            for loan in self:
                if touched_schedule_fields and loan.state in ("approved", "closed"):
                    raise UserError(
                        _(
                            "Loan %(loan)s is %(state)s: its amount, interest, "
                            "number of instalments and first instalment date can "
                            "no longer be changed.",
                            loan=loan.name,
                            state=loan.state,
                        )
                    )
                if (
                    "employee_id" in vals
                    and loan.state != "draft"
                    and vals["employee_id"] != loan.employee_id.id
                ):
                    raise UserError(
                        _(
                            "Loan %(loan)s has left the draft stage: the borrower "
                            "can no longer be changed.",
                            loan=loan.name,
                        )
                    )
        result = super().write(vals)
        if touched_schedule_fields:
            stale = self.filtered(
                lambda loan: loan.state == "draft" and loan.instalment_ids
            )
            if stale:
                stale.instalment_ids.unlink()
        return result

    def unlink(self):
        for loan in self:
            if loan.state in ("approved", "closed"):
                raise UserError(
                    _(
                        "Loan %(loan)s is %(state)s and cannot be deleted. Settle "
                        "it instead, so the repayment history is kept.",
                        loan=loan.name,
                        state=loan.state,
                    )
                )
        return super().unlink()

    def _prepare_instalment_vals(self):
        self.ensure_one()
        count = self.instalment_count
        currency = self.currency_id or self.env.company.currency_id
        total_interest = currency.round(self.amount * self.interest_percentage / 100.0)
        principal_share = currency.round(self.amount / count)
        interest_share = currency.round(total_interest / count)
        vals_list = []
        for index in range(count):
            if index == count - 1:
                principal = currency.round(self.amount - principal_share * (count - 1))
                interest = currency.round(
                    total_interest - interest_share * (count - 1)
                )
            else:
                principal = principal_share
                interest = interest_share
            vals_list.append(
                {
                    "sequence": index + 1,
                    "due_date": self.first_instalment_date
                    + relativedelta(months=index),
                    "principal_amount": principal,
                    "interest_amount": interest,
                    "total_amount": currency.round(principal + interest),
                }
            )
        return vals_list

    def action_build_schedule(self):
        for loan in self:
            if loan.state != "draft":
                raise UserError(
                    _(
                        "The repayment schedule of loan %s can only be built "
                        "while it is still a draft.",
                        loan.name,
                    )
                )
            if loan.instalment_count < 1:
                raise UserError(
                    _("Loan %s needs at least one instalment.", loan.name)
                )
            if not loan.first_instalment_date:
                raise UserError(
                    _(
                        "Set the first instalment date on loan %s before "
                        "building its schedule.",
                        loan.name,
                    )
                )
            loan.instalment_ids.unlink()
            loan.instalment_ids = [
                (0, 0, vals) for vals in loan._prepare_instalment_vals()
            ]
        return True

    def action_submit(self):
        for loan in self:
            if loan.state != "draft":
                raise UserError(
                    _("Only a draft loan can be submitted (%s is not).", loan.name)
                )
            loan._check_schedule_present()
        self.write({"state": "submitted"})
        return True

    def _check_schedule_present(self):
        self.ensure_one()
        if not self.instalment_ids:
            raise UserError(
                _(
                    "Loan %s has no repayment schedule. Use 'Build the "
                    "schedule' before submitting it for approval.",
                    self.name,
                )
            )

    def _check_single_active_loan(self):
        self.ensure_one()
        if self.company_id.loan_allow_multiple:
            return
        running = self.search(
            [
                ("id", "!=", self.id),
                ("employee_id", "=", self.employee_id.id),
                ("state", "=", "approved"),
                ("outstanding_amount", ">", 0.0),
            ],
            limit=1,
        )
        if running:
            raise UserError(
                _(
                    "%(employee)s already has a running loan (%(running)s) with "
                    "an outstanding balance. Settle it first, or allow multiple "
                    "concurrent loans in the loan policy settings.",
                    employee=self.employee_id.name,
                    running=running.name,
                )
            )

    def _check_maximum_amount(self):
        self.ensure_one()
        maximum = self.company_id.loan_max_amount
        if maximum > 0 and self.amount > maximum:
            raise UserError(
                _(
                    "Loan %(loan)s asks for %(amount)s, which is above the "
                    "maximum loan amount of %(maximum)s set for %(company)s.",
                    loan=self.name,
                    amount=self.amount,
                    maximum=maximum,
                    company=self.company_id.display_name,
                )
            )

    def action_approve(self):
        for loan in self:
            if loan.state != "submitted":
                raise UserError(
                    _(
                        "Only a submitted loan can be approved (%s is not).",
                        loan.name,
                    )
                )
            loan._check_schedule_present()
            loan._check_single_active_loan()
            loan._check_maximum_amount()
        self.write({"state": "approved"})
        return True

    def action_refuse(self):
        for loan in self:
            if loan.state != "submitted":
                raise UserError(
                    _("Only a submitted loan can be refused (%s is not).", loan.name)
                )
            if not (loan.refusal_reason or "").strip():
                raise UserError(
                    _(
                        "Give a refusal reason on loan %s before refusing it.",
                        loan.name,
                    )
                )
        self.write({"state": "refused"})
        return True

    def action_cancel(self):
        for loan in self:
            if loan.state not in ("draft", "submitted"):
                raise UserError(
                    _(
                        "Loan %(loan)s is %(state)s: only a draft or submitted "
                        "loan can be cancelled.",
                        loan=loan.name,
                        state=loan.state,
                    )
                )
        self.write({"state": "cancelled"})
        return True

    def _close_if_fully_recovered(self):
        for loan in self:
            if (
                loan.state == "approved"
                and loan.instalment_ids
                and loan.instalments_remaining == 0
            ):
                loan.write({"state": "closed"})
                loan.message_post(
                    body=_(
                        "Every instalment has been recovered. The loan is now "
                        "closed."
                    )
                )
        return True

    def _action_open_loan_wizard(self, res_model, name):
        self.ensure_one()
        if self.state != "approved":
            raise UserError(
                _(
                    "Loan %s must be approved before this operation.",
                    self.name,
                )
            )
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": res_model,
            "view_mode": "form",
            "target": "new",
            "context": {"default_loan_id": self.id},
        }

    def action_open_defer_wizard(self):
        return self._action_open_loan_wizard(
            "odomate.hr.loan.defer", _("Defer an Instalment")
        )

    def action_open_settle_wizard(self):
        return self._action_open_loan_wizard(
            "odomate.hr.loan.settle", _("Settle the Loan Early")
        )

    def _demo_build_payslip(self, employee, due_date):
        period_start = due_date.replace(day=1)
        period_end = period_start + relativedelta(months=1, days=-1)
        return self.env["hr.payslip"].create(
            {
                "employee_id": employee.id,
                "date_from": period_start,
                "date_to": period_end,
                "name": "Salary Slip of %s for %s"
                % (employee.name, period_start.strftime("%B %Y")),
            }
        )

    def _demo_create_loan(self, employee, vals, state):
        loan = self.create(dict(vals, employee_id=employee.id))
        loan.action_build_schedule()
        if state != "draft":
            loan.write({"state": state})
        return loan

    def _demo_recover(self, loan, count):
        recovered = loan.instalment_ids.sorted("due_date")[:count]
        for instalment in recovered:
            payslip = self._demo_build_payslip(
                loan.employee_id, instalment.due_date
            )
            instalment.write({"state": "recovered", "payslip_id": payslip.id})
        return recovered

    @api.model
    def _generate_demo_loans(self):
        if self.search_count([]):
            return False
        employees = self.env["hr.employee"].search([], limit=8, order="id")
        if not employees:
            return False

        def borrower(index):
            return employees[index % len(employees)]

        month_start = fields.Date.today().replace(day=1)

        running = self._demo_create_loan(
            borrower(0),
            {
                "amount": 3000.0,
                "purpose": "Relocation costs after moving closer to the office",
                "instalment_count": 6,
                "first_instalment_date": month_start - relativedelta(months=3),
                "interest_percentage": 0.0,
            },
            "approved",
        )
        self._demo_recover(running, 2)

        self._demo_create_loan(
            borrower(1),
            {
                "amount": 5000.0,
                "purpose": "Home renovation before the winter season",
                "instalment_count": 10,
                "first_instalment_date": month_start + relativedelta(months=1),
                "interest_percentage": 6.5,
            },
            "approved",
        )

        settled = self._demo_create_loan(
            borrower(2),
            {
                "amount": 1200.0,
                "purpose": "Replacement of a broken laptop used for study",
                "instalment_count": 4,
                "first_instalment_date": month_start - relativedelta(months=4),
                "interest_percentage": 0.0,
            },
            "approved",
        )
        recovered = self._demo_recover(settled, 2)
        (settled.instalment_ids - recovered).write({"state": "cancelled"})
        settled.write(
            {
                "settlement_date": month_start - relativedelta(months=1),
                "settlement_reference": "BNK/2024/SETTLE/0043",
                "state": "closed",
            }
        )

        self._demo_create_loan(
            borrower(3),
            {
                "amount": 2500.0,
                "purpose": "Deposit for a new rental flat",
                "instalment_count": 5,
                "first_instalment_date": month_start + relativedelta(months=1),
                "interest_percentage": 0.0,
                "refusal_reason": "A loan settled less than six months ago is "
                "still on file for this employee. Re-apply after the next "
                "review cycle.",
            },
            "refused",
        )
        return True
