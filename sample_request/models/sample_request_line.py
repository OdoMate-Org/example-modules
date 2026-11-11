from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SampleRequestLine(models.Model):
    _name = 'sample.request.line'
    _description = 'Product Sample Request Line'
    _order = 'request_id, id'

    request_id = fields.Many2one('sample.request', string='Sample Request', required=True, index=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', required=True, default=1.0, digits='Product Unit')
    user_id = fields.Many2one(related='request_id.user_id', string='Sales Rep', store=True)
    state = fields.Selection(related='request_id.state', string='Status')

    _quantity_positive = models.Constraint('CHECK(quantity > 0)', 'The sample quantity must be greater than zero.')

    def _check_requests_editable(self, requests, allowed_states=('draft',)):
        if self.env.su or self.env.user.has_group('sample_request.group_sample_request_manager'):
            return
        if any(request.state not in allowed_states for request in requests):
            raise UserError(_('Products can only be changed while the sample request is a draft.'))

    @api.model_create_multi
    def create(self, vals_list):
        request_ids = [vals['request_id'] for vals in vals_list if vals.get('request_id')]
        self._check_requests_editable(self.env['sample.request'].browse(request_ids))
        return super().create(vals_list)

    def write(self, vals):
        requests = self.request_id
        if vals.get('request_id'):
            requests |= self.env['sample.request'].browse(vals['request_id'])
        self._check_requests_editable(requests)
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_locked_request(self):
        self._check_requests_editable(self.request_id, allowed_states=('draft', 'cancelled'))
