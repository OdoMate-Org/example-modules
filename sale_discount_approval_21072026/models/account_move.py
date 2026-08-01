from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

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

    @api.depends(
        'invoice_line_ids.discount',
        'invoice_line_ids.price_unit',
        'invoice_line_ids.quantity',
        'discount_type',
        'discount_rate',
    )
    def _compute_amount_discount(self):
        for move in self:
            lines = move.invoice_line_ids
            base_total = sum(line.quantity * line.price_unit for line in lines)
            if move.discount_type == 'amount' and base_total:
                move.amount_discount = move.discount_rate
            else:
                move.amount_discount = sum(
                    line.quantity * line.price_unit * line.discount / 100.0
                    for line in lines
                )

    def _apply_invoice_discount(self):
        """Fan the invoice-level discount out to every invoice line."""
        for move in self:
            lines = move.invoice_line_ids
            if not lines:
                continue
            if move.discount_type == 'percent':
                for line in lines:
                    line.discount = move.discount_rate
            else:
                base_total = sum(
                    line.quantity * line.price_unit for line in lines
                )
                if not base_total:
                    continue
                percentage = move.discount_rate / base_total * 100.0
                for line in lines:
                    line.discount = percentage

    @api.onchange('discount_type', 'discount_rate', 'invoice_line_ids')
    def _onchange_apply_discount(self):
        self._apply_invoice_discount()
