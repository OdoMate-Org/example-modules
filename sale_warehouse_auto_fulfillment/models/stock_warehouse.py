from odoo import api, fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    auto_ship = fields.Boolean(
        string="Ship Automatically",
        default=False,
        help="Validate the delivery of a sales order in full as soon as the order "
             "is confirmed. All lines, full ordered quantity, no backorder and no "
             "stock availability check (negative stock is allowed).",
    )
    auto_invoice_create = fields.Boolean(
        string="Create Invoice Automatically",
        default=False,
        help="Create the customer invoice as soon as the sales order is confirmed, "
             "exactly as the manual Create Invoice button does. Each product keeps "
             "its own invoicing policy (ordered or delivered quantities). When there "
             "is nothing to invoice, the step is skipped silently.",
    )
    auto_invoice_confirm = fields.Boolean(
        string="Confirm Invoice Automatically",
        default=False,
        help="Post the invoice that this automation has just created. It has no "
             "effect on its own: with Create Invoice Automatically off, there is "
             "nothing to post.",
    )

    def _has_sale_auto_fulfillment(self):
        self.ensure_one()
        return self.auto_ship or self.auto_invoice_create

    @api.model
    def _swaf_seed_demo_stock(self, warehouse_id, product_id, quantity):
        """Demo-only helper: seed on-hand stock for ``product_id`` at the given
        warehouse's own stock location, so demo deliveries dispatched from that
        warehouse can reserve their quantity and reach the ``Ready`` state.

        A warehouse other than the default one auto-creates its stock location
        with no static XML id, so the location cannot be referenced from a demo
        ``eval`` expression (which only exposes ``ref``). This helper is invoked
        from ``demo/products.xml`` via ``<function>`` and is not part of the
        order-confirmation automation.
        """
        warehouse = self.browse(warehouse_id).exists()
        product = self.env['product.product'].browse(product_id).exists()
        if not warehouse or not warehouse.lot_stock_id or not product:
            return False
        location = warehouse.lot_stock_id
        Quant = self.env['stock.quant']
        # Set on-hand to the target (delta from what is already there) so the
        # helper is idempotent across repeated demo loads.
        current = Quant._get_available_quantity(product, location)
        delta = quantity - current
        if delta:
            Quant._update_available_quantity(product, location, delta)
        return True
