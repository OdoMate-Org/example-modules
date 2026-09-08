import base64

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import format_date


@tagged('post_install', '-at_install')
class TestOdomateHrDocumentsCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref('base.main_company')
        cls.today = fields.Date.context_today(cls.env['odomate.hr.document'])

        cls.manager_user = cls.env['res.users'].create({
            'name': 'Doc Manager',
            'login': 'odomate_doc_manager',
            'email': 'doc.manager@example.com',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        cls.employee_user = cls.env['res.users'].create({
            'name': 'Doc Employee',
            'login': 'odomate_doc_employee',
            'email': 'doc.employee@example.com',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        cls.other_user = cls.env['res.users'].create({
            'name': 'Doc Colleague',
            'login': 'odomate_doc_colleague',
            'email': 'doc.colleague@example.com',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

        cls.manager = cls.env['hr.employee'].create({
            'name': 'Doc Manager',
            'user_id': cls.manager_user.id,
            'work_email': 'doc.manager@example.com',
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Doc Employee',
            'user_id': cls.employee_user.id,
            'work_email': 'doc.employee@example.com',
            'parent_id': cls.manager.id,
        })
        cls.other_employee = cls.env['hr.employee'].create({
            'name': 'Doc Colleague',
            'user_id': cls.other_user.id,
            'work_email': 'doc.colleague@example.com',
        })

        cls.type_before = cls.env['odomate.hr.document.type'].create({
            'name': 'Test Work Permit',
            'reminder_days': 10,
            'chasing_pattern': 'before_expiry',
        })
        cls.type_on_expiry = cls.env['odomate.hr.document.type'].create({
            'name': 'Test Residence Permit',
            'reminder_days': 0,
            'chasing_pattern': 'on_expiry',
        })
        cls.type_daily_before = cls.env['odomate.hr.document.type'].create({
            'name': 'Test Driving Licence',
            'reminder_days': 5,
            'chasing_pattern': 'daily_before',
        })
        cls.type_daily_after = cls.env['odomate.hr.document.type'].create({
            'name': 'Test Forklift Certificate',
            'reminder_days': 5,
            'chasing_pattern': 'daily_after',
        })

    def _make_document(self, document_type=None, date_expiry=None, state='draft', employee=None):
        document = self.env['odomate.hr.document'].create({
            'employee_id': (employee or self.employee).id,
            'document_type_id': (document_type or self.type_before).id,
            'date_issued': self.today - relativedelta(years=1),
            'date_expiry': date_expiry if date_expiry is not None else self.today + relativedelta(days=30),
        })
        if state != 'draft':
            document.state = state
        return document

    def _make_attachment(self, record):
        return self.env['ir.attachment'].create({
            'name': 'scan.pdf',
            'datas': base64.b64encode(b'scan'),
            'res_model': record._name,
            'res_id': record.id,
        })


@tagged('post_install', '-at_install')
class TestOdomateHrDocumentsDemoData(TransactionCase):

    def test_demo_data_loaded(self):
        self.assertGreaterEqual(
            self.env['odomate.hr.document.type'].sudo().search_count([]), 6)
        self.assertGreaterEqual(
            self.env['odomate.hr.form.template'].sudo().search_count([]), 3)
        self.assertGreaterEqual(
            self.env['odomate.hr.document'].sudo().search_count([]), 6)
        self.assertGreaterEqual(
            self.env['odomate.hr.document.history'].sudo().search_count([]), 1)

    def test_demo_covers_every_chasing_pattern(self):
        patterns = set(self.env['odomate.hr.document.type'].sudo().search([]).mapped(
            'chasing_pattern'))
        self.assertEqual(
            patterns,
            {'on_expiry', 'before_expiry', 'daily_before', 'daily_after'})

    def test_demo_covers_every_state(self):
        states = set(
            self.env['odomate.hr.document'].sudo().search([]).mapped('state'))
        self.assertEqual(states, {'draft', 'valid', 'expired'})

    def test_name_search_on_document_type(self):
        found = self.env['odomate.hr.document.type'].name_search('', limit=5)
        self.assertIsInstance(found, list)
        self.assertTrue(found)

    def test_name_search_on_history(self):
        found = self.env['odomate.hr.document.history'].name_search('', limit=5)
        self.assertIsInstance(found, list)

    def test_reminder_template_and_cron_installed(self):
        self.assertTrue(self.env.ref(
            'odomate_hr_documents.mail_template_document_reminder'))
        cron = self.env.ref('odomate_hr_documents.ir_cron_odomate_hr_document_expiry')
        self.assertTrue(cron.active)
        self.assertEqual(cron.interval_type, 'days')


@tagged('post_install', '-at_install')
class TestOdomateHrDocumentCrud(TestOdomateHrDocumentsCommon):

    def test_create_assigns_sequence_reference(self):
        document = self._make_document()
        self.assertTrue(document.reference.startswith('EMPDOC/'))
        self.assertEqual(document.state, 'draft')
        self.assertEqual(document.company_id, self.employee.company_id)

    def test_copy_does_not_reuse_reference(self):
        document = self._make_document()
        copy = document.copy()
        self.assertNotEqual(copy.reference, document.reference)
        self.assertEqual(copy.state, 'draft')

    def test_display_name_is_the_reference(self):
        document = self._make_document()
        self.assertEqual(document.display_name, document.reference)

    def test_name_search_on_reference(self):
        document = self._make_document()
        other = self._make_document(document_type=self.type_on_expiry)
        found = self.env['odomate.hr.document'].name_search(document.reference)
        found_ids = [item[0] for item in found]
        self.assertIn(document.id, found_ids)
        self.assertNotIn(other.id, found_ids)
        self.assertFalse(
            self.env['odomate.hr.document'].name_search('EMPDOC/ZZZZZ'))

    def test_write_and_unlink(self):
        document = self._make_document()
        document.description = 'Updated description'
        self.assertEqual(document.description, 'Updated description')
        document_id = document.id
        document.unlink()
        self.assertFalse(self.env['odomate.hr.document'].browse(document_id).exists())

    def test_document_type_negative_reminder_days_rejected(self):
        with self.assertRaises(ValidationError):
            self.env['odomate.hr.document.type'].create({
                'name': 'Test Bad Type',
                'reminder_days': -1,
                'chasing_pattern': 'before_expiry',
            })

    def test_form_template_crud(self):
        template = self.env['odomate.hr.form.template'].create({
            'name': 'Test Expense Form',
            'note': 'Fill and return to HR.',
        })
        self.assertTrue(template.active)
        template.note = 'Updated'
        self.assertEqual(template.note, 'Updated')
        found = self.env['odomate.hr.form.template'].name_search('Test Expense')
        self.assertIn(template.id, [item[0] for item in found])
        template.unlink()


@tagged('post_install', '-at_install')
class TestOdomateHrDocumentState(TestOdomateHrDocumentsCommon):

    def test_mark_valid_from_draft(self):
        document = self._make_document()
        document.action_mark_valid()
        self.assertEqual(document.state, 'valid')

    def test_mark_valid_allowed_when_expiry_is_today(self):
        document = self._make_document(date_expiry=self.today)
        document.action_mark_valid()
        self.assertEqual(document.state, 'valid')

    def test_mark_valid_refused_when_expiry_in_the_past(self):
        document = self._make_document(date_expiry=self.today - relativedelta(days=1))
        with self.assertRaises(ValidationError):
            document.action_mark_valid()
        self.assertEqual(document.state, 'draft')

    def test_past_expiry_can_be_saved_in_draft(self):
        document = self._make_document(date_expiry=self.today - relativedelta(years=2))
        self.assertEqual(document.state, 'draft')

    def test_set_to_draft_from_valid_and_expired(self):
        document = self._make_document()
        document.action_mark_valid()
        document.action_set_to_draft()
        self.assertEqual(document.state, 'draft')

        expired = self._make_document(
            document_type=self.type_on_expiry,
            date_expiry=self.today - relativedelta(days=3),
            state='expired',
        )
        expired.action_set_to_draft()
        self.assertEqual(expired.state, 'draft')

    def test_only_one_valid_document_per_employee_and_type(self):
        first = self._make_document()
        first.action_mark_valid()
        second = self._make_document()
        with self.assertRaises(ValidationError):
            second.action_mark_valid()

    def test_duplicate_valid_blocked_on_direct_write(self):
        first = self._make_document()
        first.action_mark_valid()
        second = self._make_document()
        with self.assertRaises(ValidationError):
            second.write({'state': 'valid'})

    def test_duplicate_valid_blocked_on_create(self):
        first = self._make_document()
        first.action_mark_valid()
        with self.assertRaises(ValidationError):
            self.env['odomate.hr.document'].create({
                'employee_id': self.employee.id,
                'document_type_id': self.type_before.id,
                'date_expiry': self.today + relativedelta(days=90),
                'state': 'valid',
            })

    def test_draft_and_expired_copies_may_coexist(self):
        valid = self._make_document()
        valid.action_mark_valid()
        draft = self._make_document()
        expired = self._make_document()
        expired.write({'state': 'expired'})
        self.assertEqual(draft.state, 'draft')
        self.assertEqual(expired.state, 'expired')


@tagged('post_install', '-at_install')
class TestOdomateHrDocumentComputed(TestOdomateHrDocumentsCommon):

    def test_days_remaining_label_wording(self):
        Document = self.env['odomate.hr.document']
        expired = self._make_document(date_expiry=self.today - relativedelta(days=4))
        self.assertIn('4', expired.days_remaining_label)
        self.assertNotEqual(expired.days_remaining_label, '4')

        today_doc = self._make_document(
            document_type=self.type_on_expiry, date_expiry=self.today)
        self.assertEqual(today_doc.days_remaining_label, 'Today')

        tomorrow_doc = self._make_document(
            document_type=self.type_daily_before,
            date_expiry=self.today + relativedelta(days=1))
        self.assertEqual(tomorrow_doc.days_remaining_label, 'Tomorrow')

        future_doc = self._make_document(
            document_type=self.type_daily_after,
            date_expiry=self.today + relativedelta(days=12))
        self.assertEqual(future_doc.days_remaining_label, '12')

        self.assertFalse(Document.create({
            'employee_id': self.employee.id,
            'document_type_id': self.type_before.id,
        }).days_remaining_label)

    def test_days_remaining_label_search_translates_to_date_domain(self):
        near = self._make_document(date_expiry=self.today + relativedelta(days=3))
        far = self._make_document(
            document_type=self.type_on_expiry,
            date_expiry=self.today + relativedelta(days=60))
        results = self.env['odomate.hr.document'].search([
            ('days_remaining_label', '>=', 0),
            ('days_remaining_label', '<=', 7),
        ])
        self.assertIn(near, results)
        self.assertNotIn(far, results)

    def test_history_count_and_employee_document_count(self):
        document = self._make_document()
        self.assertEqual(document.history_count, 0)
        self.assertGreaterEqual(
            self.employee.with_user(self.env.user).document_count, 1)


@tagged('post_install', '-at_install')
class TestOdomateHrDocumentRenewal(TestOdomateHrDocumentsCommon):

    def _renew(self, document, date_expiry=None, date_issued=None, reason='Renewed at town hall'):
        attachment = self.env['ir.attachment'].create({
            'name': 'new_scan.pdf',
            'datas': base64.b64encode(b'new scan'),
        })
        wizard = self.env['odomate.hr.document.renew'].create({
            'document_id': document.id,
            'new_date_issued': date_issued if date_issued is not None else self.today,
            'new_date_expiry': date_expiry if date_expiry is not None else self.today + relativedelta(years=1),
            'new_attachment_ids': [(6, 0, attachment.ids)],
            'reason': reason,
        })
        return wizard.action_confirm()

    def test_renew_moves_dates_and_attachments_to_history(self):
        document = self._make_document()
        document.action_mark_valid()
        old_attachment = self._make_attachment(document)
        old_issued, old_expiry = document.date_issued, document.date_expiry

        self._renew(document)

        self.assertEqual(len(document.history_ids), 1)
        history = document.history_ids
        self.assertEqual(history.date_issued, old_issued)
        self.assertEqual(history.date_expiry, old_expiry)
        self.assertEqual(history.renewed_by, self.env.user)
        self.assertTrue(history.renewed_date)
        self.assertEqual(history.reason, 'Renewed at town hall')

        old_attachment.invalidate_recordset()
        self.assertEqual(old_attachment.res_model, 'odomate.hr.document.history')
        self.assertEqual(old_attachment.res_id, history.id)
        self.assertEqual(history.attachment_count, 1)

    def test_renew_repoints_new_attachments_to_document(self):
        document = self._make_document()
        document.action_mark_valid()
        self._renew(document)
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'odomate.hr.document'),
            ('res_id', '=', document.id),
        ])
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments.name, 'new_scan.pdf')

    def test_renew_sets_new_dates_and_valid_state(self):
        document = self._make_document(
            date_expiry=self.today - relativedelta(days=5), state='expired')
        new_expiry = self.today + relativedelta(years=2)
        self._renew(document, date_expiry=new_expiry)
        self.assertEqual(document.state, 'valid')
        self.assertEqual(document.date_expiry, new_expiry)
        self.assertEqual(document.date_issued, self.today)

    def test_renew_posts_chatter_message_with_old_and_new_expiry(self):
        document = self._make_document()
        document.action_mark_valid()
        old_expiry = document.date_expiry
        before = len(document.message_ids)
        self._renew(document, reason='Licence renewed')
        self.assertGreater(len(document.message_ids), before)
        bodies = ''.join(document.message_ids.mapped('body'))
        self.assertIn('Licence renewed', bodies)
        self.assertIn(format_date(self.env, old_expiry), bodies)

    def test_renew_refused_from_draft(self):
        document = self._make_document()
        with self.assertRaises(UserError):
            self._renew(document)

    def test_renew_refused_when_new_expiry_not_in_future(self):
        document = self._make_document()
        document.action_mark_valid()
        with self.assertRaises(ValidationError):
            self._renew(document, date_expiry=self.today)

    def test_renew_refused_when_expiry_not_after_issue(self):
        document = self._make_document()
        document.action_mark_valid()
        with self.assertRaises(ValidationError):
            self._renew(
                document,
                date_issued=self.today + relativedelta(days=30),
                date_expiry=self.today + relativedelta(days=10),
            )

    def test_renew_closes_open_manager_activity(self):
        document = self._make_document(date_expiry=self.today + relativedelta(days=10))
        document.action_mark_valid()
        document.action_send_reminder_now()
        open_activities = document.sudo().activity_ids
        self.assertTrue(open_activities)
        self._renew(document)
        self.assertFalse(document.sudo().activity_ids)

    def test_set_to_draft_closes_open_manager_activity(self):
        document = self._make_document(date_expiry=self.today + relativedelta(days=10))
        document.action_mark_valid()
        document.action_send_reminder_now()
        self.assertTrue(document.sudo().activity_ids)
        document.action_set_to_draft()
        self.assertFalse(document.sudo().activity_ids)


@tagged('post_install', '-at_install')
class TestOdomateHrDocumentCron(TestOdomateHrDocumentsCommon):

    def test_cron_expires_valid_documents_past_expiry(self):
        document = self._make_document(date_expiry=self.today + relativedelta(days=30))
        document.action_mark_valid()
        document.write({'date_expiry': self.today - relativedelta(days=1)})
        self.env['odomate.hr.document']._cron_process_documents()
        self.assertEqual(document.state, 'expired')

    def test_cron_does_not_expire_document_expiring_today(self):
        document = self._make_document(
            document_type=self.type_on_expiry, date_expiry=self.today)
        document.action_mark_valid()
        self.env['odomate.hr.document']._cron_process_documents()
        self.assertEqual(document.state, 'valid')

    def test_cron_never_touches_draft_documents(self):
        document = self._make_document(date_expiry=self.today - relativedelta(days=10))
        self.env['odomate.hr.document']._cron_process_documents()
        self.assertEqual(document.state, 'draft')
        self.assertFalse(document.sudo().last_reminder_sent_date)

    def test_reminder_due_on_expiry_pattern(self):
        document = self._make_document(
            document_type=self.type_on_expiry, date_expiry=self.today, state='valid')
        self.assertTrue(document._is_reminder_due(self.today))
        self.assertFalse(document._is_reminder_due(self.today - relativedelta(days=1)))
        self.assertFalse(document._is_reminder_due(self.today + relativedelta(days=1)))

    def test_reminder_due_before_expiry_pattern_fires_once(self):
        expiry = self.today + relativedelta(days=10)
        document = self._make_document(
            document_type=self.type_before, date_expiry=expiry, state='valid')
        self.assertTrue(document._is_reminder_due(self.today))
        self.assertFalse(document._is_reminder_due(self.today + relativedelta(days=1)))
        self.assertFalse(document._is_reminder_due(expiry))

    def test_reminder_due_daily_before_pattern(self):
        expiry = self.today + relativedelta(days=5)
        document = self._make_document(
            document_type=self.type_daily_before, date_expiry=expiry, state='valid')
        for offset in range(0, 6):
            self.assertTrue(document._is_reminder_due(self.today + relativedelta(days=offset)))
        self.assertFalse(document._is_reminder_due(self.today - relativedelta(days=1)))
        self.assertFalse(document._is_reminder_due(expiry + relativedelta(days=1)))

    def test_reminder_due_daily_after_pattern(self):
        expiry = self.today - relativedelta(days=2)
        document = self._make_document(
            document_type=self.type_daily_after, date_expiry=expiry, state='expired')
        for offset in range(0, 6):
            self.assertTrue(document._is_reminder_due(expiry + relativedelta(days=offset)))
        self.assertFalse(document._is_reminder_due(expiry - relativedelta(days=1)))
        self.assertFalse(document._is_reminder_due(expiry + relativedelta(days=6)))

    def test_cron_sends_once_per_day_and_stamps_date(self):
        document = self._make_document(date_expiry=self.today + relativedelta(days=10))
        document.action_mark_valid()
        self.env['odomate.hr.document']._cron_process_documents()
        document.invalidate_recordset()
        self.assertEqual(document.sudo().last_reminder_sent_date, self.today)

        mail_domain = [('model', '=', 'odomate.hr.document'), ('res_id', '=', document.id)]
        sent_after_first = self.env['mail.mail'].sudo().search_count(mail_domain)
        self.env['odomate.hr.document']._cron_process_documents()
        self.assertEqual(
            self.env['mail.mail'].sudo().search_count(mail_domain), sent_after_first)

    def test_cron_creates_manager_activity_dated_on_expiry(self):
        expiry = self.today + relativedelta(days=10)
        document = self._make_document(date_expiry=expiry)
        document.action_mark_valid()
        self.env['odomate.hr.document']._cron_process_documents()
        activities = document.sudo().activity_ids
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities.user_id, self.manager_user)
        self.assertEqual(activities.date_deadline, expiry)

    def test_no_manager_means_email_only(self):
        expiry = self.today + relativedelta(days=10)
        document = self._make_document(date_expiry=expiry, employee=self.other_employee)
        document.action_mark_valid()
        self.env['odomate.hr.document']._cron_process_documents()
        self.assertFalse(document.sudo().activity_ids)
        self.assertEqual(document.sudo().last_reminder_sent_date, self.today)

    def test_manual_reminder_stamps_date(self):
        document = self._make_document(date_expiry=self.today + relativedelta(days=10))
        document.action_mark_valid()
        document.action_send_reminder_now()
        self.assertEqual(document.sudo().last_reminder_sent_date, self.today)


@tagged('post_install', '-at_install')
class TestOdomateHrDocumentSecurity(TestOdomateHrDocumentsCommon):

    def test_employee_reads_own_document_only(self):
        own = self._make_document()
        own.action_mark_valid()
        colleague = self._make_document(employee=self.other_employee)

        Document = self.env['odomate.hr.document'].with_user(self.employee_user)
        visible = Document.search([])
        self.assertIn(own.id, visible.ids)
        self.assertNotIn(colleague.id, visible.ids)

    def test_employee_cannot_open_colleague_document_directly(self):
        colleague = self._make_document(employee=self.other_employee)
        with self.assertRaises(AccessError):
            colleague.with_user(self.employee_user).read(['reference'])

    def test_employee_cannot_write_own_document(self):
        own = self._make_document()
        with self.assertRaises(AccessError):
            own.with_user(self.employee_user).write({'description': 'hacked'})

    def test_employee_cannot_create_document(self):
        with self.assertRaises(AccessError):
            self.env['odomate.hr.document'].with_user(self.employee_user).create({
                'employee_id': self.employee.id,
                'document_type_id': self.type_before.id,
            })

    def test_employee_can_read_document_types_and_form_templates(self):
        self.type_before.with_user(self.employee_user).read(['name', 'chasing_pattern'])
        template = self.env['odomate.hr.form.template'].create({'name': 'Test Public Form'})
        template.with_user(self.employee_user).read(['name', 'note'])

    def test_employee_cannot_write_document_type(self):
        with self.assertRaises(AccessError):
            self.type_before.with_user(self.employee_user).write({'reminder_days': 99})

    def test_history_is_read_only_in_the_ui(self):
        History = self.env['odomate.hr.document.history']
        for field_name in ('date_issued', 'date_expiry', 'renewed_by',
                           'renewed_date', 'reason'):
            self.assertTrue(
                History._fields[field_name].readonly,
                "%s must be readonly on the history model" % field_name,
            )
        for view_xmlid in ('view_odomate_hr_document_history_list',
                           'view_odomate_hr_document_history_form'):
            arch = self.env.ref('odomate_hr_documents.' + view_xmlid).arch
            self.assertIn('create="false"', arch)

    def test_employee_cannot_write_own_history(self):
        document = self._make_document()
        document.action_mark_valid()
        history = self.env['odomate.hr.document.history'].sudo().create({
            'document_id': document.id,
            'reason': 'Manual',
            'renewed_date': fields.Datetime.now(),
        })
        history.with_user(self.employee_user).read(['reason'])
        with self.assertRaises(AccessError):
            history.with_user(self.employee_user).write({'reason': 'tampered'})

    def test_colleague_cannot_read_history(self):
        colleague_document = self._make_document(employee=self.other_employee)
        history = self.env['odomate.hr.document.history'].sudo().create({
            'document_id': colleague_document.id,
            'reason': 'Manual',
            'renewed_date': fields.Datetime.now(),
        })
        with self.assertRaises(AccessError):
            history.with_user(self.employee_user).read(['reason'])
