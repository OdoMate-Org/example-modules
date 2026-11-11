from datetime import timedelta

from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestSampleRequest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rep = new_test_user(cls.env, login='sr_test_rep', lang='en_US', groups='base.group_user,sample_request.group_sample_request_user')
        cls.rep_other = new_test_user(cls.env, login='sr_test_rep2', lang='en_US', groups='base.group_user,sample_request.group_sample_request_user')
        manager_lang = 'de_DE' if cls.env['res.lang'].search([('code', '=', 'de_DE')]) else 'en_US'
        cls.manager = new_test_user(cls.env, login='sr_test_mgr', lang=manager_lang, groups='base.group_user,sample_request.group_sample_request_manager')
        cls.partner = cls.env['res.partner'].create({'name': 'Sample Test Customer'})
        cls.product_a = cls.env['product.product'].create({'name': 'Sample Widget A'})
        cls.product_b = cls.env['product.product'].create({'name': 'Sample Widget B'})
        cls.sale_order = cls.env['sale.order'].create({'partner_id': cls.partner.id})

    def _create_request(self, user=None, lines=2):
        user = user or self.rep
        vals = {
            'partner_id': self.partner.id,
            'reason_category': 'deal_in_progress',
            'line_ids': [
                (0, 0, {'product_id': product.id, 'quantity': 2.0})
                for product in (self.product_a, self.product_b)[:lines]
            ],
        }
        return self.env['sample.request'].with_user(user).create(vals)

    def _to_state(self, request, state):
        chain = ['submitted', 'approved', 'sent']
        for step in chain[:chain.index(state) + 1]:
            if step == 'submitted':
                request.with_user(self.rep).action_submit()
            elif step == 'approved':
                request.with_user(self.manager).action_approve()
            elif step == 'sent':
                request.with_user(self.manager).action_mark_sent()
        return request

    def test_create_defaults(self):
        request = self._create_request()
        self.assertEqual(request.state, 'draft')
        self.assertEqual(request.user_id, self.rep)
        self.assertNotEqual(request.name, 'New')
        self.assertEqual(request.line_count, 2)

    def test_line_count_follows_lines(self):
        request = self._create_request(lines=1)
        self.assertEqual(request.line_count, 1)
        request.write({'line_ids': [(0, 0, {'product_id': self.product_b.id, 'quantity': 1.0})]})
        self.assertEqual(request.line_count, 2)

    def test_quantity_must_be_positive(self):
        request = self._create_request(lines=0)
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'), self.cr.savepoint():
            self.env['sample.request.line'].create({
                'request_id': request.id,
                'product_id': self.product_a.id,
                'quantity': 0.0,
            })
            self.env.flush_all()

    def test_submit_requires_lines(self):
        request = self._create_request(lines=0)
        with self.assertRaises(UserError):
            request.with_user(self.rep).action_submit()

    def test_full_flow_ordered(self):
        request = self._create_request()
        request.with_user(self.rep).action_submit()
        self.assertEqual(request.state, 'submitted')

        request.with_user(self.manager).action_approve()
        self.assertEqual(request.state, 'approved')
        self.assertEqual(request.manager_id, self.manager)

        request.with_user(self.manager).action_mark_sent()
        self.assertEqual(request.state, 'sent')
        self.assertEqual(request.sent_date, fields.Date.context_today(request))
        activity = request.follow_up_activity_id
        self.assertTrue(activity)
        self.assertEqual(activity.user_id, self.rep)
        self.assertEqual(activity.summary, 'Follow up on sample request')
        self.assertEqual(activity.date_deadline, request.sent_date + timedelta(days=14))
        self.assertEqual(activity.res_id, request.id)

        request.with_user(self.rep).action_log_outcome('ordered', sale_order=self.sale_order)
        self.assertEqual(request.state, 'followed_up')
        self.assertEqual(request.follow_up_outcome, 'ordered')
        self.assertEqual(request.sale_order_id, self.sale_order)
        self.assertFalse(request.activity_ids.filtered(lambda a: a.summary == 'Follow up on sample request'))
        self.assertEqual(request.converted_count, 1)
        self.assertEqual(request.conversion_rate, 100.0)

    def test_outcome_wizard_without_order(self):
        request = self._to_state(self._create_request(), 'sent')
        wizard = self.env['sample.request.outcome.wizard'].with_user(self.rep).create({
            'request_id': request.id,
            'follow_up_outcome': 'still_thinking',
            'sale_order_id': self.sale_order.id,
        })
        wizard.action_confirm()
        self.assertEqual(request.state, 'followed_up')
        self.assertEqual(request.follow_up_outcome, 'still_thinking')
        self.assertFalse(request.sale_order_id)
        self.assertFalse(request.activity_ids)
        self.assertEqual(request.converted_count, 0)
        self.assertEqual(request.conversion_rate, 0.0)

    def test_sale_order_can_be_linked_later(self):
        request = self._to_state(self._create_request(), 'sent')
        request.with_user(self.rep).action_log_outcome('ordered')
        self.assertFalse(request.sale_order_id)
        request.with_user(self.rep).write({'sale_order_id': self.sale_order.id})
        self.assertEqual(request.sale_order_id, self.sale_order)

    def test_sent_date_kept_when_preset(self):
        request = self._to_state(self._create_request(), 'approved')
        custom = fields.Date.today() - timedelta(days=3)
        request.with_user(self.manager).write({'sent_date': custom})
        request.with_user(self.manager).action_mark_sent()
        self.assertEqual(request.sent_date, custom)
        self.assertEqual(request.follow_up_activity_id.date_deadline, custom + timedelta(days=14))

    def test_reject_requires_reason(self):
        request = self._to_state(self._create_request(), 'submitted')
        with self.assertRaises(UserError):
            request.with_user(self.manager).action_reject('')
        wizard = self.env['sample.request.reject.wizard'].with_user(self.manager).create({
            'request_id': request.id,
            'rejection_reason': 'Budget exhausted this quarter',
        })
        wizard.action_confirm()
        self.assertEqual(request.state, 'rejected')
        self.assertEqual(request.manager_id, self.manager)
        self.assertEqual(request.rejection_reason, 'Budget exhausted this quarter')

    def test_rejected_state_constraint(self):
        request = self._create_request()
        with self.assertRaises(ValidationError):
            request.with_user(self.manager).write({'state': 'rejected', 'rejection_reason': False})

    def test_rep_cannot_take_manager_actions(self):
        request = self._to_state(self._create_request(), 'submitted')
        with self.assertRaises((UserError, AccessError)):
            request.with_user(self.rep).action_approve()
        with self.assertRaises((UserError, AccessError)):
            request.with_user(self.rep).action_reject('Not allowed')
        request.with_user(self.manager).action_approve()
        with self.assertRaises((UserError, AccessError)):
            request.with_user(self.rep).action_mark_sent()

    def test_invalid_transitions(self):
        request = self._create_request()
        with self.assertRaises(UserError):
            request.with_user(self.manager).action_approve()
        with self.assertRaises(UserError):
            request.with_user(self.manager).action_mark_sent()
        with self.assertRaises(UserError):
            request.with_user(self.rep).action_log_outcome('ordered')

    def test_cancel_only_while_pending(self):
        draft = self._create_request()
        draft.with_user(self.rep).action_cancel()
        self.assertEqual(draft.state, 'cancelled')

        submitted = self._to_state(self._create_request(), 'submitted')
        submitted.with_user(self.rep).action_cancel()
        self.assertEqual(submitted.state, 'cancelled')

        approved = self._to_state(self._create_request(), 'approved')
        with self.assertRaises(UserError):
            approved.with_user(self.rep).action_cancel()

    def test_rep_read_only_after_submit(self):
        request = self._to_state(self._create_request(), 'submitted')
        with self.assertRaises(UserError):
            request.with_user(self.rep).write({'reason_note': 'Changed my mind'})
        with self.assertRaises(UserError):
            request.with_user(self.rep).write({'state': 'approved'})

    def test_rep_cannot_force_state_on_draft(self):
        request = self._create_request()
        with self.assertRaises(UserError):
            request.with_user(self.rep).write({'state': 'sent'})

    def test_record_rule_visibility(self):
        request = self._create_request()
        Request = self.env['sample.request']
        self.assertFalse(Request.with_user(self.rep_other).search([('id', '=', request.id)]))
        self.assertTrue(Request.with_user(self.rep).search([('id', '=', request.id)]))
        self.assertTrue(Request.with_user(self.manager).search([('id', '=', request.id)]))
        with self.assertRaises(AccessError):
            request.with_user(self.rep_other).read(['partner_id'])

    def test_name_search(self):
        request = self._create_request()
        results = self.env['sample.request'].name_search(request.name)
        self.assertIn(request.id, [res[0] for res in results])

    def test_unlink_only_draft_or_cancelled(self):
        request = self._to_state(self._create_request(), 'submitted')
        with self.assertRaises(UserError):
            request.with_user(self.manager).unlink()
        draft = self._create_request()
        draft.with_user(self.rep).unlink()
        self.assertFalse(draft.exists())
