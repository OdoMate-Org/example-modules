from unittest.mock import patch

from odoo import SUPERUSER_ID, api
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.sale_warehouse_auto_fulfillment.models.sale_order import SaleOrder


@tagged('post_install', '-at_install')
class TestSaleWarehouseAutoFulfillment(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref('stock.warehouse0')
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.partner = cls.env.ref('base.res_partner_2')

        cls.product_ordered = cls.env['product.product'].create({
            'name': 'Auto Fulfillment Widget',
            'type': 'consu',
            'is_storable': True,
            'invoice_policy': 'order',
            'list_price': 50.0,
        })
        cls.product_delivered = cls.env['product.product'].create({
            'name': 'Auto Fulfillment Fixture',
            'type': 'consu',
            'is_storable': True,
            'invoice_policy': 'delivery',
            'list_price': 120.0,
        })
        cls.env['stock.quant']._update_available_quantity(
            cls.product_ordered, cls.stock_location, 500.0,
        )

    def _count_committed_logs(self, domain):
        """Read ir.logging from an independent transaction.

        The module writes failure logs through its own cursor so they survive the
        savepoint rollback; Odoo's REPEATABLE READ snapshot hides them from the
        test transaction, so a fresh cursor is the only way to observe them.
        """
        with self.env.registry.cursor() as check_cr:
            check_env = api.Environment(check_cr, SUPERUSER_ID, {})
            return check_env['ir.logging'].search_count(domain)

    def _set_flags(self, auto_ship=False, auto_invoice_create=False, auto_invoice_confirm=False):
        self.warehouse.write({
            'auto_ship': auto_ship,
            'auto_invoice_create': auto_invoice_create,
            'auto_invoice_confirm': auto_invoice_confirm,
        })

    def _new_order(self, product=None, qty=3.0, warehouse=None):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': (warehouse or self.warehouse).id,
            'order_line': [(0, 0, {
                'product_id': (product or self.product_ordered).id,
                'product_uom_qty': qty,
            })],
        })

    def test_warehouse_flags_default_to_false(self):
        flags = ['auto_ship', 'auto_invoice_create', 'auto_invoice_confirm']
        defaults = self.env['stock.warehouse'].default_get(flags)
        for flag in flags:
            self.assertFalse(defaults.get(flag), "%s must be off by default" % flag)

    def test_all_flags_off_is_pass_through(self):
        self._set_flags()
        order = self._new_order()
        order.action_confirm()

        self.assertEqual(order.state, 'sale')
        self.assertTrue(order.picking_ids)
        self.assertNotIn('done', order.picking_ids.mapped('state'))
        self.assertFalse(order.invoice_ids)

    def test_auto_invoice_confirm_alone_has_no_effect(self):
        self._set_flags(auto_invoice_confirm=True)
        order = self._new_order()
        order.action_confirm()

        self.assertEqual(order.state, 'sale')
        self.assertFalse(order.invoice_ids)
        self.assertNotIn('done', order.picking_ids.mapped('state'))

    def test_auto_ship_validates_delivery_in_full(self):
        self._set_flags(auto_ship=True)
        order = self._new_order(qty=7.0)
        order.action_confirm()

        self.assertEqual(order.state, 'sale')
        self.assertTrue(order.picking_ids)
        self.assertEqual(set(order.picking_ids.mapped('state')), {'done'})
        self.assertEqual(order.order_line.qty_delivered, 7.0)
        self.assertFalse(order.picking_ids.backorder_ids)
        self.assertFalse(order.invoice_ids)

    def test_auto_ship_allows_negative_stock(self):
        self._set_flags(auto_ship=True)
        available_before = self.env['stock.quant']._get_available_quantity(
            self.product_delivered, self.stock_location, allow_negative=True,
        )
        order = self._new_order(product=self.product_delivered, qty=10.0)
        order.action_confirm()

        self.assertEqual(set(order.picking_ids.mapped('state')), {'done'})
        available_after = self.env['stock.quant']._get_available_quantity(
            self.product_delivered, self.stock_location, allow_negative=True,
        )
        self.assertEqual(available_after, available_before - 10.0)
        self.assertLess(available_after, 0.0)

    def test_auto_invoice_create_leaves_invoice_in_draft(self):
        self._set_flags(auto_invoice_create=True)
        order = self._new_order(qty=4.0)
        order.action_confirm()

        self.assertEqual(len(order.invoice_ids), 1)
        self.assertEqual(order.invoice_ids.state, 'draft')
        self.assertNotIn('done', order.picking_ids.mapped('state'))

    def test_full_chain_ships_invoices_and_posts(self):
        self._set_flags(auto_ship=True, auto_invoice_create=True, auto_invoice_confirm=True)
        order = self._new_order(qty=5.0)
        order.action_confirm()

        self.assertEqual(order.state, 'sale')
        self.assertEqual(set(order.picking_ids.mapped('state')), {'done'})
        self.assertEqual(len(order.invoice_ids), 1)
        self.assertEqual(order.invoice_ids.state, 'posted')

    def test_delivered_policy_without_shipping_skips_invoicing_silently(self):
        self._set_flags(auto_invoice_create=True, auto_invoice_confirm=True)
        order = self._new_order(product=self.product_delivered, qty=2.0)
        order.action_confirm()

        self.assertEqual(order.state, 'sale')
        self.assertFalse(order.invoice_ids)
        skip_notes = order.message_ids.filtered(
            lambda message: 'Automatic invoicing skipped' in (message.body or '')
        )
        self.assertTrue(skip_notes, "A chatter note should explain the skipped invoicing step.")

    def test_delivered_policy_with_auto_ship_is_invoiced(self):
        self._set_flags(auto_ship=True, auto_invoice_create=True, auto_invoice_confirm=True)
        order = self._new_order(product=self.product_delivered, qty=3.0)
        order.action_confirm()

        self.assertEqual(order.order_line.qty_delivered, 3.0)
        self.assertEqual(len(order.invoice_ids), 1)
        self.assertEqual(order.invoice_ids.state, 'posted')

    def test_failure_rolls_everything_back_and_logs(self):
        self._set_flags(auto_ship=True, auto_invoice_create=True, auto_invoice_confirm=True)
        order = self._new_order(qty=3.0)
        log_domain = [
            ('name', '=', 'sale_warehouse_auto_fulfillment'),
            ('message', 'like', order.name),
        ]
        logs_before = self._count_committed_logs(log_domain)

        def _boom(self):
            raise UserError("Simulated carrier outage")

        with patch.object(SaleOrder, '_auto_fulfillment_validate_delivery', _boom):
            with self.assertRaises(UserError) as error:
                order.action_confirm()

        self.assertIn("Simulated carrier outage", str(error.exception))
        self.assertIn("automatic delivery validation", str(error.exception))
        self.assertEqual(order.state, 'draft')
        self.assertFalse(order.picking_ids)
        self.assertFalse(order.invoice_ids)
        self.assertEqual(self._count_committed_logs(log_domain), logs_before + 1)

    def test_failure_on_posting_rolls_back_the_whole_run(self):
        self._set_flags(auto_ship=True, auto_invoice_create=True, auto_invoice_confirm=True)
        order = self._new_order(qty=3.0)

        def _boom(self, invoices):
            raise UserError("Customer has no receivable account")

        with patch.object(SaleOrder, '_auto_fulfillment_post_invoice', _boom):
            with self.assertRaises(UserError) as error:
                order.action_confirm()

        self.assertIn("automatic invoice posting", str(error.exception))
        self.assertEqual(order.state, 'draft')
        self.assertFalse(order.picking_ids)
        self.assertFalse(order.invoice_ids)

    def test_other_warehouse_stays_manual(self):
        self._set_flags(auto_ship=True, auto_invoice_create=True, auto_invoice_confirm=True)
        manual_warehouse = self.env['stock.warehouse'].create({
            'name': 'Manual Test Warehouse',
            'code': 'MTWH',
        })
        order = self._new_order(warehouse=manual_warehouse)
        order.action_confirm()

        self.assertEqual(order.state, 'sale')
        self.assertFalse(order.invoice_ids)
        self.assertNotIn('done', order.picking_ids.mapped('state'))
