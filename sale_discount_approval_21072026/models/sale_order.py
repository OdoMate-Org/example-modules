from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(
        selection_add=[('waiting', "Waiting Approval"), ('sale',)],
        ondelete={'waiting': 'set default'},
    )
    discount_type = fields.Selection(
        selection=[
            ('percent', "Percent"),
            ('amount', "Amount"),
        ],
        string="Discount Type",
        default='percent',
    )
    discount_rate = fields.Float(string="Discount Rate", digits=(16, 2))
    amount_discount = fields.Monetary(
        string="Discount",
        compute='_compute_amount_discount',
        store=True,
        readonly=True,
    )
    margin_test = fields.Float(
        string="Margin Test",
        compute='_compute_margin_test',
        help="Mirrors the order margin when the Sale Margin app is installed; "
             "otherwise stays at zero.",
    )

    @api.depends(
        'order_line.discount',
        'order_line.price_unit',
        'order_line.product_uom_qty',
        'order_line.display_type',
    )
    def _compute_amount_discount(self):
        for order in self:
            order.amount_discount = sum(
                line.product_uom_qty * line.price_unit * line.discount / 100.0
                for line in order.order_line
                if not line.display_type
            )

    @api.depends('order_line')
    def _compute_margin_test(self):
        for order in self:
            order.margin_test = order['margin'] if 'margin' in order._fields else 0.0

    def _apply_order_discount(self):
        """Fan the order-level discount out to every real order line."""
        for order in self:
            lines = order.order_line.filtered(lambda line: not line.display_type)
            if not lines:
                continue
            if order.discount_type == 'percent':
                for line in lines:
                    line.discount = order.discount_rate
                    line.total_discount = 0.0
            else:
                base_total = sum(
                    line.product_uom_qty * line.price_unit for line in lines
                )
                if not base_total:
                    continue
                percentage = order.discount_rate / base_total * 100.0
                for line in lines:
                    line.discount = percentage
                    line.total_discount = line.price_unit * (1 - percentage / 100.0)

    @api.onchange('discount_type', 'discount_rate', 'order_line')
    def _onchange_apply_discount(self):
        self._apply_order_discount()

    def button_dummy(self):
        self._apply_order_discount()
        return True

    def _discount_needs_approval(self):
        self.ensure_one()
        company = self.company_id or self.env.company
        if company.so_double_validation != 'two_step':
            return False
        lines = self.order_line.filtered(lambda line: not line.display_type)
        if not lines:
            return False
        average_discount = sum(lines.mapped('discount')) / len(lines)
        return average_discount > company.so_double_validation_limit

    def action_confirm(self):
        if not self.env.context.get('skip_discount_approval'):
            waiting = self.filtered(lambda order: order._discount_needs_approval())
            if waiting:
                waiting.write({'state': 'waiting'})
                self = self - waiting
        if not self:
            return True
        return super().action_confirm()

    def action_approve(self):
        self.filtered(lambda order: order.state == 'waiting').write({'state': 'sent'})
        return self.with_context(skip_discount_approval=True).action_confirm()

    def action_reject(self):
        self.write({'state': 'draft'})
        return True

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        vals.update({
            'discount_type': self.discount_type,
            'discount_rate': self.discount_rate,
        })
        return vals
