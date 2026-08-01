from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    total_discount = fields.Float(
        string="Discounted Unit Value",
        digits='Product Price',
        default=0.0,
        help="Discounted unit value stored when an Amount-type order-level "
             "discount is fanned out across the lines.",
    )
