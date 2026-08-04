from odoo.exceptions import AccessError
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
        cls.salesperson = cls.env['res.users'].create({
            'name': "Non-Manager Salesperson",
            'login': 'discount_test_salesperson',
            'group_ids': [(6, 0, [cls.env.ref('sales_team.group_sale_salesman').id])],
        })
        cls.manager = cls.env['res.users'].create({
            'name': "Discount Approval Manager",
            'login': 'discount_test_manager',
            'group_ids': [(6, 0, [cls.env.ref('sales_team.group_sale_manager').id])],
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

    def test_action_approve_reject_denied_for_non_manager(self):
        self.company.so_double_validation = 'two_step'
        self.company.so_double_validation_limit = 15.0
        order = self._make_order('percent', 20.0, [(5, 100.0)])
        order._apply_order_discount()
        order.action_confirm()
        self.assertEqual(order.state, 'waiting')

        order_as_salesperson = order.with_user(self.salesperson)
        with self.assertRaises(AccessError):
            order_as_salesperson.action_approve()
        self.assertEqual(order.state, 'waiting')
        with self.assertRaises(AccessError):
            order_as_salesperson.action_reject()
        self.assertEqual(order.state, 'waiting')

    def test_action_approve_noop_when_not_waiting(self):
        order = self._make_order('percent', 5.0, [(5, 100.0)])
        order._apply_order_discount()
        self.assertEqual(order.state, 'draft')
        order.action_approve()
        self.assertEqual(order.state, 'draft')

    def test_action_reject_noop_when_not_waiting(self):
        self.company.so_double_validation = 'one_step'
        order = self._make_order('percent', 5.0, [(5, 100.0)])
        order._apply_order_discount()
        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        order.action_reject()
        self.assertEqual(order.state, 'sale')

    # --- skip_discount_approval bypass hardening -----------------------------

    def test_action_confirm_flag_ignored_for_non_manager(self):
        self.company.so_double_validation = 'two_step'
        self.company.so_double_validation_limit = 15.0
        order = self._make_order('percent', 20.0, [(5, 100.0)])
        order._apply_order_discount()
        order.user_id = self.salesperson
        order.with_user(self.salesperson).with_context(skip_discount_approval=True).action_confirm()
        self.assertEqual(order.state, 'waiting')

    def test_action_approve_with_explicit_manager(self):
        self.company.so_double_validation = 'two_step'
        self.company.so_double_validation_limit = 15.0
        order = self._make_order('percent', 20.0, [(5, 100.0)])
        order._apply_order_discount()
        order.action_confirm()
        self.assertEqual(order.state, 'waiting')
        order.with_user(self.manager).action_approve()
        self.assertEqual(order.state, 'sale')

    def test_action_confirm_mixed_batch_splits(self):
        self.company.so_double_validation = 'two_step'
        self.company.so_double_validation_limit = 15.0
        over_limit = self._make_order('percent', 20.0, [(5, 100.0)])
        over_limit._apply_order_discount()
        under_limit = self._make_order('percent', 5.0, [(5, 100.0)])
        under_limit._apply_order_discount()
        (over_limit | under_limit).action_confirm()
        self.assertEqual(over_limit.state, 'waiting')
        self.assertEqual(under_limit.state, 'sale')

    def test_action_confirm_flag_ignored_when_not_waiting_even_for_manager(self):
        # Even a manager can't collapse confirm+approve into one step on an
        # order that never actually visited 'waiting' - that would skip the
        # audit trail two-step validation exists to produce.
        self.company.so_double_validation = 'two_step'
        self.company.so_double_validation_limit = 15.0
        order = self._make_order('percent', 20.0, [(5, 100.0)])
        order._apply_order_discount()
        self.assertEqual(order.state, 'draft')
        order.with_user(self.manager).with_context(skip_discount_approval=True).action_confirm()
        self.assertEqual(order.state, 'waiting')

    def test_action_confirm_flag_honoured_for_manager_on_waiting_order(self):
        self.company.so_double_validation = 'two_step'
        self.company.so_double_validation_limit = 15.0
        order = self._make_order('percent', 20.0, [(5, 100.0)])
        order._apply_order_discount()
        order.action_confirm()
        self.assertEqual(order.state, 'waiting')
        order.with_user(self.manager).with_context(skip_discount_approval=True).action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_action_confirm_sudo_without_flag_still_gated(self):
        # Mirrors the customer-portal acceptance path: sudo() alone, with no
        # flag, must not bypass the gate.
        self.company.so_double_validation = 'two_step'
        self.company.so_double_validation_limit = 15.0
        order = self._make_order('percent', 20.0, [(5, 100.0)])
        order._apply_order_discount()
        order.with_user(self.salesperson).sudo().action_confirm()
        self.assertEqual(order.state, 'waiting')

    def test_action_confirm_on_confirmed_order_is_noop(self):
        self.company.so_double_validation = 'one_step'
        order = self._make_order('percent', 5.0, [(5, 100.0)])
        order._apply_order_discount()
        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        self.company.so_double_validation = 'two_step'
        self.company.so_double_validation_limit = 15.0
        order.order_line.write({'discount': 50.0})
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_action_confirm_mixed_batch_with_existing_waiting_order(self):
        self.company.so_double_validation = 'two_step'
        self.company.so_double_validation_limit = 15.0
        over_limit = self._make_order('percent', 20.0, [(5, 100.0)])
        over_limit._apply_order_discount()
        over_limit.action_confirm()
        self.assertEqual(over_limit.state, 'waiting')

        under_limit = self._make_order('percent', 5.0, [(5, 100.0)])
        under_limit._apply_order_discount()

        (over_limit | under_limit).action_confirm()
        self.assertEqual(over_limit.state, 'waiting')
        self.assertEqual(under_limit.state, 'sale')

    def test_section_and_note_lines_excluded_from_fan_out_and_average(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'discount_type': 'percent',
            'discount_rate': 20.0,
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'display_type': 'line_section',
            'name': "Section A",
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 5,
            'price_unit': 100.0,
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'display_type': 'line_note',
            'name': "Note A",
        })
        order._apply_order_discount()
        section = order.order_line.filtered(lambda l: l.display_type == 'line_section')
        note = order.order_line.filtered(lambda l: l.display_type == 'line_note')
        product_line = order.order_line.filtered(lambda l: not l.display_type)
        self.assertEqual(section.discount, 0.0)
        self.assertEqual(note.discount, 0.0)
        self.assertEqual(product_line.discount, 20.0)

        # If section/note lines diluted the average, 20/3 = 6.67% would stay under the 15% limit.
        self.company.so_double_validation = 'two_step'
        self.company.so_double_validation_limit = 15.0
        self.assertTrue(order._discount_needs_approval())

    def test_sale_report_discount_measure(self):
        # sale.report ships its own 'discount' measure natively (feeding its
        # discount_amount); this pins that it reflects our order-level fan-out.
        self.company.so_double_validation = 'one_step'
        order = self._make_order('percent', 12.0, [(4, 150.0)])
        order._apply_order_discount()
        order.action_confirm()
        self.env.flush_all()  # sale.report is a raw SQL view; force pending writes to the DB first.
        report_lines = self.env['sale.report'].search([]).filtered(
            lambda r: r.order_reference == order
        )
        self.assertTrue(report_lines)
        self.assertAlmostEqual(report_lines[0].discount, 12.0, places=2)

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
