from odoo import fields, models


class SampleRequestOutcomeWizard(models.TransientModel):
    _name = 'sample.request.outcome.wizard'
    _description = 'Log Sample Request Follow-up Outcome'

    request_id = fields.Many2one('sample.request', string='Sample Request', required=True, ondelete='cascade')
    partner_id = fields.Many2one(related='request_id.partner_id', string='Customer')
    follow_up_outcome = fields.Selection(
        [
            ('ordered', 'Ordered'),
            ('still_thinking', 'Still Thinking'),
            ('not_interested', 'Not Interested'),
        ], string='Outcome', required=True)
    sale_order_id = fields.Many2one('sale.order', string='Sales Order')

    def action_confirm(self):
        self.ensure_one()
        sale_order = self.sale_order_id if self.follow_up_outcome == 'ordered' else False
        self.request_id.action_log_outcome(self.follow_up_outcome, sale_order=sale_order)
        return {'type': 'ir.actions.act_window_close'}
