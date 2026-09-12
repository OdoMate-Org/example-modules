from odoo import _, fields, models
from odoo.exceptions import UserError


class OdomateHrResignationRefuse(models.TransientModel):
    _name = 'odomate.hr.resignation.refuse'
    _description = 'Refuse Resignation'

    resignation_id = fields.Many2one(
        comodel_name='odomate.hr.resignation',
        string="Resignation",
        required=True,
        ondelete='cascade',
    )
    reason = fields.Text(string="Refusal Reason", required=True)

    def action_confirm_refusal(self):
        self.ensure_one()
        if not (self.reason or '').strip():
            raise UserError(_("Please explain why this resignation is refused."))
        self.resignation_id._apply_refusal(self.reason)
        return {'type': 'ir.actions.act_window_close'}
