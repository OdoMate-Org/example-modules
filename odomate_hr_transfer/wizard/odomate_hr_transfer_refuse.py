from odoo import fields, models


class OdomateHrTransferRefuse(models.TransientModel):
    _name = 'odomate.hr.transfer.refuse'
    _description = 'Refuse Employee Transfer'

    transfer_id = fields.Many2one(
        'odomate.hr.transfer',
        string='Transfer',
        required=True,
        ondelete='cascade',
    )
    refuse_reason = fields.Text(string='Refusal Reason', required=True)

    def action_confirm_refuse(self):
        self.ensure_one()
        self.transfer_id._register_refusal(self.refuse_reason)
        return {'type': 'ir.actions.act_window_close'}
