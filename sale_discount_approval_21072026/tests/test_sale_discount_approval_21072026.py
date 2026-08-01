from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSaleDiscountApproval(TransactionCase):
    """Behavioral tests for the sale/invoice discount + approval gate."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({'name': "Discount Test Customer"})
        cls.product = cls.env['product.product'].create({
            'name': "Discount Test Product",
            'type': 'service',
            'invoice_policy': 'order',
            'list_price': 100.0,
        })

    def _make_order(self, discount_type, rate, lines):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'discount_type': discount_type,
            'discount_rate': rate,
        })
        for qty, price, *discount in lines:
            self.env['sale.order.line'].create({
                'order_id': order.id,
                'product_id': self.product.id,
                'product_uom_qty': qty,
                'price_unit': price,
                'discount': discount[0] if discount else 0.0,
            })
        return order

    # --- Order-level fan-out ------------------------------------------------

    def test_percent_fan_out(self):
        order = self._make_order('percent', 10.0, [(5, 100.0), (3, 200.0)])
        order._apply_order_discount()
        self.assertTrue(all(line.discount == 10.0 for line in order.order_line))

    def test_amount_fan_out_uniform_percentage(self):
        order = self._make_order('amount', 500.0, [(10, 300.0), (20, 100.0)])
        order._apply_order_discount()
        for line in order.order_line:
            self.assertAlmostEqual(line.discount, 10.0, places=2)
        self.assertAlmostEqual(order.order_line[0].total_discount, 270.0, places=2)

    def test_amount_zero_total_guard(self):
        order = self._make_order('amount', 500.0, [(0, 0.0)])
        order._apply_order_discount()
        self.assertEqual(order.order_line.discount, 0.0)
        self.assertEqual(order.amount_discount, 0.0)

    def test_negative_discount_is_surcharge(self):
        order = self._make_order('percent', -10.0, [(5, 100.0)])
        order._apply_order_discount()
        self.assertEqual(order.order_line.discount, -10.0)

    def test_amount_discount_computed(self):
        order = self._make_order('percent', 10.0, [(5, 100.0)])
        order._apply_order_discount()
        self.assertAlmostEqual(order.amount_discount, 50.0, places=2)

    def test_amount_discount_exact_for_amount_type(self):
        # 700 off a 3350 base rounds line discount to 20.90%, which would
        # recompute to 700.15 if amount_discount summed line discounts back up.
        order = self._make_order('amount', 700.0, [(10, 335.0)])
        order._apply_order_discount()
        self.assertAlmostEqual(order.amount_discount, 700.0, places=2)

    def test_amount_discount_zero_when_no_lines(self):
        order = self._make_order('amount', 500.0, [])
        self.assertEqual(order.amount_discount, 0.0)

    # --- Approval gate ------------------------------------------------------

    def test_gate_two_step_over_limit_goes_waiting(self):
        self.company.so_double_validation = 'two_step'
        self.company.so_double_validation_limit = 15.0
        order = self._make_order('percent', 20.0, [(5, 100.0), (3, 200.0)])
        order._apply_order_discount()
        order.action_confirm()
        self.assertEqual(order.state, 'waiting')

    def test_gate_one_step_confirms_directly(self):
        self.company.so_double_validation = 'one_step'
        order = self._make_order('percent', 20.0, [(5, 100.0)])
        order._apply_order_discount()
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_gate_average_dilution_edge_case(self):
        self.company.so_double_validation = 'two_step'
        self.company.so_double_validation_limit = 15.0
        # One steeply discounted line and one surcharge line: average = 2.5% < 15%
        order = self._make_order('percent', 25.0, [(10, 300.0, 25.0), (5, 120.0, -20.0)])
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_action_approve(self):
        self.company.so_double_validation = 'two_step'
        self.company.so_double_validation_limit = 15.0
        order = self._make_order('percent', 20.0, [(5, 100.0)])
        order._apply_order_discount()
        order.action_confirm()
        self.assertEqual(order.state, 'waiting')
        order.action_approve()
        self.assertEqual(order.state, 'sale')

    def test_action_reject(self):
        self.company.so_double_validation = 'two_step'
        self.company.so_double_validation_limit = 15.0
        order = self._make_order('percent', 20.0, [(5, 100.0)])
        order._apply_order_discount()
        order.action_confirm()
        order.action_reject()
        self.assertEqual(order.state, 'draft')

    # --- Invoice carry-over and invoice-level fan-out -----------------------

    def test_discount_carried_to_invoice(self):
        self.company.so_double_validation = 'one_step'
        order = self._make_order('percent', 10.0, [(5, 100.0)])
        order._apply_order_discount()
        order.action_confirm()
        invoice = order._create_invoices()
        self.assertEqual(invoice.discount_type, 'percent')
        self.assertAlmostEqual(invoice.discount_rate, 10.0, places=2)

    def test_invoice_level_fan_out(self):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'discount_type': 'percent',
            'discount_rate': 15.0,
            'invoice_line_ids': [
                (0, 0, {'product_id': self.product.id, 'quantity': 5, 'price_unit': 100.0}),
                (0, 0, {'product_id': self.product.id, 'quantity': 2, 'price_unit': 250.0}),
            ],
        })
        invoice._apply_invoice_discount()
        self.assertTrue(all(line.discount == 15.0 for line in invoice.invoice_line_ids))

    def test_invoice_amount_zero_total_guard(self):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'discount_type': 'amount',
            'discount_rate': 500.0,
            'invoice_line_ids': [
                (0, 0, {'product_id': self.product.id, 'quantity': 0, 'price_unit': 0.0}),
            ],
        })
        invoice._apply_invoice_discount()
        self.assertEqual(invoice.invoice_line_ids.discount, 0.0)
        self.assertEqual(invoice.amount_discount, 0.0)

    def test_invoice_amount_discount_exact_for_amount_type(self):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'discount_type': 'amount',
            'discount_rate': 700.0,
            'invoice_line_ids': [
                (0, 0, {'product_id': self.product.id, 'quantity': 10, 'price_unit': 335.0}),
            ],
        })
        invoice._apply_invoice_discount()
        self.assertAlmostEqual(invoice.amount_discount, 700.0, places=2)

    def test_invoice_amount_discount_zero_when_no_lines(self):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'discount_type': 'amount',
            'discount_rate': 500.0,
        })
        self.assertEqual(invoice.amount_discount, 0.0)
