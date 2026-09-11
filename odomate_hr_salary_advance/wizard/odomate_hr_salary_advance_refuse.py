from odoo import fields, models


class OdomateHrSalaryAdvanceRefuse(models.TransientModel):
    _name = "odomate.hr.salary.advance.refuse"
    _description = "Refuse Salary Advance"

    advance_id = fields.Many2one(
        comodel_name="odomate.hr.salary.advance",
        string="Salary Advance",
        required=True,
        ondelete="cascade",
    )
    refusal_reason = fields.Text(
        string="Refusal Reason",
        required=True,
    )

    def action_confirm(self):
        self.ensure_one()
        self.advance_id._process_refusal(self.refusal_reason)
        return {"type": "ir.actions.act_window_close"}
