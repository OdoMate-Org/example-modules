from odoo import api, fields, models


class OdomateHrSalaryAdvancePay(models.TransientModel):
    _name = "odomate.hr.salary.advance.pay"
    _description = "Pay Salary Advance"

    advance_id = fields.Many2one(
        comodel_name="odomate.hr.salary.advance",
        string="Salary Advance",
        required=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(
        related="advance_id.company_id",
        readonly=True,
    )
    payment_date = fields.Date(
        string="Payment Date",
        required=True,
        default=fields.Date.context_today,
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Payment Journal",
        required=True,
        compute="_compute_journal_id",
        store=True,
        precompute=True,
        readonly=False,
        domain="[('type', 'in', ['bank', 'cash']), ('company_id', '=', company_id)]",
    )

    @api.depends("advance_id")
    def _compute_journal_id(self):
        for wizard in self:
            wizard.journal_id = wizard.advance_id.company_id.advance_journal_id

    def action_confirm(self):
        self.ensure_one()
        self.advance_id._process_payment(self.payment_date, self.journal_id)
        return {"type": "ir.actions.act_window_close"}
