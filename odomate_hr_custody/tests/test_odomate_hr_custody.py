from dateutil.relativedelta import relativedelta
from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestOdomateHrCustodyCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Custody = cls.env['odomate.hr.custody']
        cls.Item = cls.env['odomate.hr.custody.item']
        cls.company = cls.env.company
        cls.today = fields.Date.context_today(cls.Custody)

        cls.employee = cls.env['hr.employee'].create({
            'name': "Custody Tester",
            'company_id': cls.company.id,
            'work_contact_id': cls.env['res.partner'].create({
                'name': "Custody Tester",
                'email': "custody.tester@example.com",
            }).id,
        })
        cls.other_employee = cls.env['hr.employee'].create({
            'name': "Custody Colleague",
            'company_id': cls.company.id,
        })

        cls.laptop = cls.Item.create({
            'name': "ThinkPad X1",
            'description': "14\" business laptop",
            'company_id': cls.company.id,
        })
        cls.phone = cls.Item.create({
            'name': "iPhone 15",
            'company_id': cls.company.id,
        })

        cls.basic_user = cls.env['res.users'].create({
            'name': "Custody Basic User",
            'login': "custody_basic_user",
            'email': "custody_basic_user@example.com",
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
        })
        # This database has `hr_auto_create_employee` enabled, so creating the
        # user above may already have created the matching employee. Reuse it —
        # hr.employee carries a unique (user_id, company_id) constraint.
        cls.basic_employee = cls.env['hr.employee'].search(
            [('user_id', '=', cls.basic_user.id)], limit=1,
        )
        if not cls.basic_employee:
            cls.basic_employee = cls.env['hr.employee'].create({
                'name': "Custody Basic Employee",
                'company_id': cls.company.id,
                'user_id': cls.basic_user.id,
            })

        cls.hr_user = cls.env['res.users'].create({
            'name': "Custody HR Officer",
            'login': "custody_hr_officer",
            'email': "custody_hr_officer@example.com",
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('hr.group_hr_user').id,
            ])],
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
        })

    @classmethod
    def _make_request(cls, item=None, employee=None, days=7, **values):
        vals = {
            'employee_id': (employee or cls.employee).id,
            'item_id': (item or cls.laptop).id,
            'reason': "Field work",
            'request_date': cls.today,
            'return_date': cls.today + relativedelta(days=days),
        }
        vals.update(values)
        return cls.Custody.create(vals)


class TestCustodyItem(TestOdomateHrCustodyCommon):

    def test_item_crud(self):
        item = self.Item.create({'name': "Projector"})
        self.assertTrue(item.id)
        self.assertEqual(item.company_id, self.env.company)
        item.write({'description': "Full HD"})
        self.assertEqual(item.description, "Full HD")
        self.assertTrue(self.Item.name_search("Projector"))
        item.unlink()

    def test_item_available_when_no_approved_request(self):
        self.assertTrue(self.phone.is_available)
        self.assertFalse(self.phone.current_custody_id)
        self.assertFalse(self.phone.current_holder_id)

    def test_item_holder_reflects_approved_request(self):
        request = self._make_request(item=self.phone)
        request.action_send_for_approval()
        request.action_approve()
        self.phone.invalidate_recordset()
        self.assertFalse(self.phone.is_available)
        self.assertEqual(self.phone.current_custody_id, request)
        self.assertEqual(self.phone.current_holder_id, self.employee)

    def test_item_becomes_available_after_return(self):
        request = self._make_request(item=self.phone)
        request.action_send_for_approval()
        request.action_approve()
        request.action_returned()
        self.phone.invalidate_recordset()
        self.assertTrue(self.phone.is_available)
        self.assertFalse(self.phone.current_holder_id)

    def test_item_onchange_product_fills_name(self):
        product = self.env['product.product'].create({'name': "Barcode Scanner"})
        item = self.Item.new({'product_id': product.id})
        item._onchange_product_id()
        self.assertEqual(item.name, product.display_name)


class TestCustodyRequest(TestOdomateHrCustodyCommon):

    def test_reference_sequence_is_generated(self):
        request = self._make_request()
        self.assertTrue(request.name.startswith('CUST/'))
        self.assertEqual(len(request.name), len('CUST/00001'))

    @mute_logger('odoo.sql_db')
    def test_return_date_before_request_date_is_rejected(self):
        # The invariant is backed by a database CHECK constraint, which fires on
        # the INSERT itself — before the Python @api.constrains gets a turn.
        with self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self._make_request(days=-3)

    def test_state_flow_draft_to_returned(self):
        request = self._make_request()
        self.assertEqual(request.state, 'draft')
        request.action_send_for_approval()
        self.assertEqual(request.state, 'waiting_approval')
        request.action_approve()
        self.assertEqual(request.state, 'approved')
        request.action_returned()
        self.assertEqual(request.state, 'returned')

    def test_returned_stamps_actual_date_without_touching_promised_date(self):
        request = self._make_request()
        promised = request.return_date
        request.action_send_for_approval()
        request.action_approve()
        request.action_returned()
        self.assertEqual(request.actual_return_date, self.today)
        self.assertEqual(request.return_date, promised)

    def test_only_one_approved_holder_per_item(self):
        first = self._make_request()
        first.action_send_for_approval()
        first.action_approve()
        second = self._make_request(employee=self.other_employee)
        second.action_send_for_approval()
        with self.assertRaises(UserError):
            second.action_approve()

    def test_approve_rejected_when_not_waiting_approval(self):
        request = self._make_request()
        with self.assertRaises(UserError):
            request.action_approve()

    def test_set_to_draft_from_waiting_approval(self):
        request = self._make_request()
        request.action_send_for_approval()
        request.action_set_to_draft()
        self.assertEqual(request.state, 'draft')

    def test_set_to_draft_blocked_once_approved(self):
        request = self._make_request()
        request.action_send_for_approval()
        request.action_approve()
        with self.assertRaises(UserError):
            request.action_set_to_draft()

    def test_set_to_draft_blocked_during_extension(self):
        request = self._make_request()
        request.action_send_for_approval()
        request.action_approve()
        self._extend(request, days=30)
        self.assertTrue(request.is_extension)
        with self.assertRaises(UserError):
            request.action_set_to_draft()

    def test_is_overdue_compute(self):
        request = self._make_request(
            request_date=self.today - relativedelta(days=30),
            return_date=self.today - relativedelta(days=2),
        )
        request.action_send_for_approval()
        request.action_approve()
        request.invalidate_recordset(['is_overdue'])
        self.assertTrue(request.is_overdue)
        request.return_date = self.today + relativedelta(days=5)
        request.invalidate_recordset(['is_overdue'])
        self.assertFalse(request.is_overdue)

    def test_draft_request_is_never_overdue(self):
        request = self._make_request(
            request_date=self.today - relativedelta(days=30),
            return_date=self.today - relativedelta(days=10),
        )
        request.invalidate_recordset(['is_overdue'])
        self.assertFalse(request.is_overdue)

    @classmethod
    def _extend(cls, request, days):
        wizard = cls.env['odomate.hr.custody.extend'].with_context(
            active_id=request.id, active_model='odomate.hr.custody',
        ).create({'new_return_date': request.return_date + relativedelta(days=days)})
        wizard.action_confirm()
        return wizard


class TestCustodyExtension(TestOdomateHrCustodyCommon):

    def setUp(self):
        super().setUp()
        self.request = self._make_request()
        self.request.action_send_for_approval()
        self.request.action_approve()

    def _extend_wizard(self, new_date):
        return self.env['odomate.hr.custody.extend'].with_context(
            active_id=self.request.id, active_model='odomate.hr.custody',
        ).create({'new_return_date': new_date})

    def test_extension_puts_request_back_in_waiting_approval(self):
        promised = self.request.return_date
        new_date = promised + relativedelta(days=14)
        self._extend_wizard(new_date).action_confirm()
        self.assertEqual(self.request.state, 'waiting_approval')
        self.assertTrue(self.request.is_extension)
        self.assertEqual(self.request.extend_new_return_date, new_date)
        self.assertEqual(self.request.return_date, promised)

    def test_extension_rejects_date_before_request_date(self):
        wizard = self._extend_wizard(self.request.request_date - relativedelta(days=1))
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_extension_approval_applies_new_date_and_clears_flags(self):
        new_date = self.request.return_date + relativedelta(days=14)
        self._extend_wizard(new_date).action_confirm()
        self.request.action_approve()
        self.assertEqual(self.request.state, 'approved')
        self.assertEqual(self.request.return_date, new_date)
        self.assertFalse(self.request.extend_new_return_date)
        self.assertFalse(self.request.is_extension)

    def test_extension_refusal_keeps_original_date_and_records_reason(self):
        promised = self.request.return_date
        self._extend_wizard(promised + relativedelta(days=14)).action_confirm()
        wizard = self.env['odomate.hr.custody.refuse'].with_context(
            active_id=self.request.id, active_model='odomate.hr.custody',
        ).create({'reason': "Project ends next week"})
        wizard.action_confirm()
        self.assertEqual(self.request.state, 'approved')
        self.assertEqual(self.request.return_date, promised)
        self.assertEqual(self.request.extension_refusal_reason, "Project ends next week")
        self.assertFalse(self.request.refusal_reason)
        self.assertFalse(self.request.extend_new_return_date)
        self.assertFalse(self.request.is_extension)


class TestCustodyRefusal(TestOdomateHrCustodyCommon):

    def test_plain_refusal_records_reason_and_sets_state(self):
        request = self._make_request()
        request.action_send_for_approval()
        wizard = self.env['odomate.hr.custody.refuse'].with_context(
            active_id=request.id, active_model='odomate.hr.custody',
        ).create({'reason': "Item reserved for onboarding"})
        wizard.action_confirm()
        self.assertEqual(request.state, 'refused')
        self.assertEqual(request.refusal_reason, "Item reserved for onboarding")
        self.assertFalse(request.extension_refusal_reason)

    def test_refuse_wizard_default_request_from_context(self):
        request = self._make_request()
        request.action_send_for_approval()
        wizard = self.env['odomate.hr.custody.refuse'].with_context(
            active_id=request.id, active_model='odomate.hr.custody',
        ).create({'reason': "No"})
        self.assertEqual(wizard.request_id, request)


class TestCustodyReminders(TestOdomateHrCustodyCommon):

    def test_cron_targets_due_and_overdue_approved_requests(self):
        due_soon = self._make_request(item=self.laptop, days=1)
        due_soon.action_send_for_approval()
        due_soon.action_approve()

        far_future = self._make_request(item=self.phone, days=45)
        far_future.action_send_for_approval()
        far_future.action_approve()

        before = self.env['mail.mail'].search_count([])
        self.Custody._cron_send_return_reminders()
        after = self.env['mail.mail'].search_count([])
        self.assertGreaterEqual(after, before)

        due = self.Custody._get_requests_due_for_reminder()
        self.assertIn(due_soon, due)
        self.assertNotIn(far_future, due)

    def test_manual_reminder_on_approved_request(self):
        request = self._make_request()
        request.action_send_for_approval()
        request.action_approve()
        self.assertTrue(request.action_send_reminder())


class TestCustodyAccess(TestOdomateHrCustodyCommon):

    def test_basic_user_can_create_own_request(self):
        request = self.Custody.with_user(self.basic_user).create({
            'employee_id': self.basic_employee.id,
            'item_id': self.laptop.id,
            'reason': "Remote work",
            'request_date': self.today,
            'return_date': self.today + relativedelta(days=10),
        })
        self.assertTrue(request.id)

    def test_basic_user_cannot_read_other_requests(self):
        other = self._make_request()
        found = self.Custody.with_user(self.basic_user).search([('id', '=', other.id)])
        self.assertFalse(found)

    def test_basic_user_cannot_approve(self):
        request = self._make_request(employee=self.basic_employee)
        request.action_send_for_approval()
        with self.assertRaises(AccessError):
            request.with_user(self.basic_user).action_approve()

    def test_basic_user_cannot_return(self):
        request = self._make_request(employee=self.basic_employee)
        request.action_send_for_approval()
        request.action_approve()
        with self.assertRaises(AccessError):
            request.with_user(self.basic_user).action_returned()

    def test_hr_user_can_approve(self):
        request = self._make_request()
        request.action_send_for_approval()
        request.with_user(self.hr_user).action_approve()
        self.assertEqual(request.state, 'approved')

    def test_basic_user_can_read_items(self):
        self.assertTrue(self.Item.with_user(self.basic_user).search([('id', '=', self.laptop.id)]))


class TestCustodyEmployeeSmartButtons(TestOdomateHrCustodyCommon):

    def test_custody_counts(self):
        first = self._make_request(item=self.laptop)
        first.action_send_for_approval()
        first.action_approve()
        second = self._make_request(item=self.phone)

        self.employee.invalidate_recordset()
        self.assertEqual(self.employee.custody_count, 2)
        self.assertEqual(self.employee.custody_current_count, 1)

        second.unlink()
        self.employee.invalidate_recordset()
        self.assertEqual(self.employee.custody_count, 1)

    def test_smart_button_actions_return_filtered_domains(self):
        action = self.employee.action_open_custody_requests()
        self.assertEqual(action['res_model'], 'odomate.hr.custody')
        self.assertIn(('employee_id', '=', self.employee.id), action['domain'])

        current = self.employee.action_open_current_custody()
        self.assertIn(('state', '=', 'approved'), current['domain'])


class TestCustodyReport(TestOdomateHrCustodyCommon):

    def test_handover_report_renders_with_empty_employee_details(self):
        request = self._make_request()
        request.action_send_for_approval()
        request.action_approve()
        report = self.env.ref('odomate_hr_custody.action_report_custody_handover')
        html, _dummy = self.env['ir.actions.report']._render_qweb_html(
            report.report_name, request.ids,
        )
        self.assertIn(request.name.encode(), html)
        self.assertNotIn(b'False', html)
