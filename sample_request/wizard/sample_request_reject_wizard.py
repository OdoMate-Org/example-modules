from odoo import fields, models


class SampleRequestRejectWizard(models.TransientModel):
    _name = 'sample.request.reject.wizard'
    _description = 'Reject Sample Request'

    request_id = fields.Many2one('sample.request', string='Sample Request', required=True, ondelete='cascade')
    rejection_reason = fields.Text(string='Rejection Reason', required=True)

    def action_confirm(self):
        self.ensure_one()
        self.request_id.action_reject(self.rejection_reason)
        return {'type': 'ir.actions.act_window_close'}
