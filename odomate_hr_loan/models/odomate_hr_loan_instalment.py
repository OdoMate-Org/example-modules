from odoo import api, fields, models


class OdomateHrLoanInstalment(models.Model):
    _name = "odomate.hr.loan.instalment"
    _description = "Employee Loan Instalment"
    _order = "loan_id, due_date, sequence, id"

    loan_id = fields.Many2one(
        comodel_name="odomate.hr.loan",
        string="Loan",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(string="Instalment No.", default=1)
    due_date = fields.Date(string="Due Date", required=True, index=True)
    principal_amount = fields.Monetary(
        string="Principal", currency_field="currency_id", required=True
    )
    interest_amount = fields.Monetary(
        string="Interest", currency_field="currency_id", required=True
    )
    total_amount = fields.Monetary(
        string="Instalment",
        currency_field="currency_id",
        required=True,
        help="Principal plus interest. This is the amount recovered from the "
        "payslip.",
    )
    state = fields.Selection(
        selection=[
            ("scheduled", "Scheduled"),
            ("recovered", "Recovered"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="scheduled",
        required=True,
        index=True,
    )
    payslip_id = fields.Many2one(
        comodel_name="hr.payslip",
        string="Payslip",
        readonly=True,
        copy=False,
        ondelete="set null",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        related="loan_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        related="loan_id.currency_id",
        store=True,
        readonly=True,
    )

    @api.depends("loan_id.name", "sequence")
    def _compute_display_name(self):
        for instalment in self:
            instalment.display_name = "%s #%s" % (
                instalment.loan_id.name or "",
                instalment.sequence,
            )
