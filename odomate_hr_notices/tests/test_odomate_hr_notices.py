from datetime import date, timedelta

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestOdomateHrNotices(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Announcement = cls.env['odomate.hr.announcement']
        cls.Category = cls.env['odomate.hr.announcement.category']
        cls.Reminder = cls.env['odomate.hr.reminder']
        cls.Refuse = cls.env['odomate.hr.announcement.refuse']

        cls.company = cls.env.company
        cls.today = date.today()

        cls.category = cls.Category.create({
            'name': 'Internal Communication',
            'company_id': cls.company.id,
        })

        cls.department = cls.env['hr.department'].create({
            'name': 'Notices Test Department',
            'company_id': cls.company.id,
        })
        cls.other_department = cls.env['hr.department'].create({
            'name': 'Notices Other Department',
            'company_id': cls.company.id,
        })
        cls.job = cls.env['hr.job'].create({
            'name': 'Notices Test Job',
            'company_id': cls.company.id,
        })

        cls.user_employee = cls._create_user('nina_notices', 'Nina Notices', [
            cls.env.ref('base.group_user').id,
        ])
        cls.user_outsider = cls._create_user('otto_notices', 'Otto Outsider', [
            cls.env.ref('base.group_user').id,
        ])
        cls.user_no_employee = cls._create_user('nemo_notices', 'Nemo NoEmployee', [
            cls.env.ref('base.group_user').id,
        ])
        cls.user_hr_officer = cls._create_user('hana_notices', 'Hana Officer', [
            cls.env.ref('base.group_user').id,
            cls.env.ref('hr.group_hr_user').id,
        ])
        cls.user_hr_manager = cls._create_user('mina_notices', 'Mina Manager', [
            cls.env.ref('base.group_user').id,
            cls.env.ref('hr.group_hr_manager').id,
        ])

        cls.employee = cls._create_employee('Nina Notices', cls.user_employee,
                                            cls.department, cls.job)
        cls.employee_outsider = cls._create_employee('Otto Outsider', cls.user_outsider,
                                                     cls.other_department, False)

    @classmethod
    def _create_user(cls, login, name, group_ids):
        return cls.env['res.users'].create({
            'name': name,
            'login': login,
            'company_id': cls.company.id,
            'company_ids': [Command.set([cls.company.id])],
            'group_ids': [Command.set(group_ids)],
        })

    @classmethod
    def _create_employee(cls, name, user, department, job):
        employee = cls.env['hr.employee'].create({
            'name': name,
            'company_id': cls.company.id,
            'user_id': user.id,
        })
        version_vals = {'department_id': department.id if department else False}
        if job:
            version_vals['job_id'] = job.id
        employee.version_id.write(version_vals)
        return employee

    def _make_announcement(self, **overrides):
        vals = {
            'title': 'Quarterly update',
            'category_id': self.category.id,
            'audience': 'all',
            'company_id': self.company.id,
            'date_start': self.today - timedelta(days=1),
            'date_end': self.today + timedelta(days=7),
        }
        vals.update(overrides)
        return self.Announcement.create(vals)

    # ------------------------------------------------------------------
    # Demo data and CRUD
    # ------------------------------------------------------------------

    def test_demo_data_loaded(self):
        self.assertGreaterEqual(self.Category.search_count([]), 4)
        self.assertGreaterEqual(self.Announcement.search_count([]), 3)
        self.assertGreaterEqual(self.Reminder.search_count([]), 2)

    def test_create_record(self):
        announcement = self._make_announcement()
        self.assertTrue(announcement.exists())
        self.assertGreater(announcement.id, 0)
        self.assertEqual(announcement.state, 'draft')

    def test_reference_uses_sequence(self):
        announcement = self._make_announcement()
        self.assertTrue(
            announcement.reference.startswith('NOTICE/'),
            f"Unexpected reference {announcement.reference!r}",
        )

    def test_write_record(self):
        announcement = self._make_announcement()
        announcement.write({'title': 'Revised quarterly update'})
        self.assertEqual(announcement.title, 'Revised quarterly update')

    def test_unlink_record(self):
        announcement = self._make_announcement()
        announcement_id = announcement.id
        announcement.unlink()
        self.assertFalse(self.Announcement.browse(announcement_id).exists())

    def test_name_search(self):
        self.assertIsInstance(self.Announcement.name_search('', limit=5), list)
        self.assertIsInstance(self.Category.name_search('', limit=5), list)
        self.assertIsInstance(self.Reminder.name_search('', limit=5), list)

    def test_category_ondelete_sets_null(self):
        category = self.Category.create({'name': 'Temporary'})
        announcement = self._make_announcement(category_id=category.id)
        category.unlink()
        self.assertFalse(announcement.category_id)
        self.assertTrue(announcement.exists())

    def test_wizard_create_record(self):
        announcement = self._make_announcement()
        wizard = self.Refuse.create({
            'announcement_id': announcement.id,
            'reason': 'Needs legal review',
        })
        self.assertTrue(wizard.exists())

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    @mute_logger('odoo.sql_db')
    def test_constraint_date_order(self):
        with self.assertRaises(Exception):
            with self.cr.savepoint():
                self._make_announcement(
                    date_start=self.today + timedelta(days=5),
                    date_end=self.today,
                )

    def test_past_start_date_is_allowed(self):
        announcement = self._make_announcement(
            date_start=self.today - timedelta(days=30),
            date_end=self.today + timedelta(days=1),
        )
        self.assertTrue(announcement.exists())

    @mute_logger('odoo.sql_db')
    def test_constraint_reminder_period(self):
        with self.assertRaises(Exception):
            with self.cr.savepoint():
                self.Reminder.create({
                    'name': 'Broken period',
                    'window': 'period',
                    'date_from': self.today + timedelta(days=5),
                    'date_to': self.today,
                })

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------

    def test_state_flow(self):
        announcement = self._make_announcement()
        announcement.action_send_for_approval()
        self.assertEqual(announcement.state, 'to_approve')
        announcement.with_user(self.user_hr_manager).action_publish()
        self.assertEqual(announcement.state, 'published')

    def test_publish_skipping_approval_is_refused(self):
        announcement = self._make_announcement()
        with self.assertRaises(UserError):
            announcement.with_user(self.user_hr_manager).action_publish()

    def test_publish_requires_hr_manager(self):
        announcement = self._make_announcement()
        announcement.action_send_for_approval()
        with self.assertRaises(AccessError):
            announcement.with_user(self.user_hr_officer).action_publish()
        self.assertEqual(announcement.state, 'to_approve')

    def test_send_for_approval_only_from_draft(self):
        announcement = self._make_announcement(state='published')
        with self.assertRaises(UserError):
            announcement.action_send_for_approval()

    def test_refuse_wizard_sets_reason(self):
        announcement = self._make_announcement()
        announcement.action_send_for_approval()
        wizard = self.Refuse.create({
            'announcement_id': announcement.id,
            'reason': 'Wrong audience',
        })
        wizard.action_confirm_refusal()
        self.assertEqual(announcement.state, 'refused')
        self.assertEqual(announcement.refuse_reason, 'Wrong audience')
        self.assertTrue(
            announcement.message_ids.filtered(
                lambda m: 'Wrong audience' in (m.body or '')),
            "The refusal reason should be posted in the chatter",
        )

    # ------------------------------------------------------------------
    # Acknowledgement
    # ------------------------------------------------------------------

    def test_acknowledge_is_idempotent(self):
        announcement = self._make_announcement(state='published')
        announcement.with_user(self.user_employee).action_acknowledge()
        announcement.with_user(self.user_employee).action_acknowledge()
        self.assertEqual(announcement.acknowledged_count, 1)
        self.assertIn(self.employee, announcement.acknowledged_employee_ids)

    def test_acknowledge_sets_is_acknowledged_by_me(self):
        announcement = self._make_announcement(state='published')
        as_user = announcement.with_user(self.user_employee)
        self.assertFalse(as_user.is_acknowledged_by_me)
        as_user.action_acknowledge()
        self.assertTrue(
            announcement.with_user(self.user_employee).is_acknowledged_by_me)

    def test_acknowledge_denied_outside_audience(self):
        announcement = self._make_announcement(
            state='published',
            audience='employee',
            employee_ids=[Command.set([self.employee.id])],
        )
        with self.assertRaises(AccessError):
            announcement.with_user(self.user_outsider).action_acknowledge()

    # ------------------------------------------------------------------
    # Audience resolution and visibility
    # ------------------------------------------------------------------

    def _visible_to(self, user):
        return self.Announcement.with_user(user).search([])

    def test_audience_all_is_visible_to_employee(self):
        announcement = self._make_announcement(state='published')
        self.assertIn(announcement, self._visible_to(self.user_employee))

    def test_audience_all_resolves_employees_hired_later(self):
        announcement = self._make_announcement(state='published')
        newcomer_user = self._create_user('late_notices', 'Late Joiner', [
            self.env.ref('base.group_user').id])
        self._create_employee('Late Joiner', newcomer_user, self.department, False)
        self.assertIn(announcement, self._visible_to(newcomer_user))

    def test_audience_employee_exact_membership(self):
        announcement = self._make_announcement(
            state='published',
            audience='employee',
            employee_ids=[Command.set([self.employee.id])],
        )
        self.assertIn(announcement, self._visible_to(self.user_employee))
        self.assertNotIn(announcement, self._visible_to(self.user_outsider))

    def test_audience_department_has_no_hierarchy_walk(self):
        child_department = self.env['hr.department'].create({
            'name': 'Notices Child Department',
            'parent_id': self.department.id,
            'company_id': self.company.id,
        })
        child_user = self._create_user('child_notices', 'Child Member', [
            self.env.ref('base.group_user').id])
        self._create_employee('Child Member', child_user, child_department, False)

        announcement = self._make_announcement(
            state='published',
            audience='department',
            department_ids=[Command.set([self.department.id])],
        )
        self.assertIn(announcement, self._visible_to(self.user_employee))
        self.assertNotIn(
            announcement, self._visible_to(child_user),
            "A child department must NOT inherit its parent's announcements",
        )

    def test_audience_job_membership(self):
        announcement = self._make_announcement(
            state='published',
            audience='job',
            job_ids=[Command.set([self.job.id])],
        )
        self.assertIn(announcement, self._visible_to(self.user_employee))
        self.assertNotIn(announcement, self._visible_to(self.user_outsider))

    def test_draft_is_invisible_to_audience(self):
        announcement = self._make_announcement(state='draft')
        self.assertNotIn(announcement, self._visible_to(self.user_employee))

    def test_out_of_window_is_invisible(self):
        announcement = self._make_announcement(
            state='published',
            date_start=self.today - timedelta(days=30),
            date_end=self.today - timedelta(days=10),
        )
        self.assertNotIn(announcement, self._visible_to(self.user_employee))

    def test_user_without_employee_sees_only_audience_all(self):
        everyone = self._make_announcement(state='published')
        targeted = self._make_announcement(
            state='published',
            audience='employee',
            employee_ids=[Command.set([self.employee.id])],
        )
        visible = self._visible_to(self.user_no_employee)
        self.assertIn(everyone, visible)
        self.assertNotIn(targeted, visible)

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------

    def test_computed_fields_audience_and_pending(self):
        announcement = self._make_announcement(
            state='published',
            audience='employee',
            employee_ids=[Command.set([self.employee.id, self.employee_outsider.id])],
        )
        self.assertEqual(announcement.audience_count, 2)
        self.assertEqual(announcement.acknowledged_count, 0)
        self.assertEqual(len(announcement.pending_employee_ids), 2)

        announcement.with_user(self.user_employee).action_acknowledge()
        announcement.invalidate_recordset()
        self.assertEqual(announcement.acknowledged_count, 1)
        self.assertEqual(announcement.pending_employee_ids, self.employee_outsider)

    def test_employee_notice_count_ignores_acknowledgement(self):
        announcement = self._make_announcement(
            state='published',
            audience='employee',
            employee_ids=[Command.set([self.employee.id])],
        )
        self.employee.invalidate_recordset()
        before = self.employee.notice_count
        self.assertGreaterEqual(before, 1)

        announcement.with_user(self.user_employee).action_acknowledge()
        self.employee.invalidate_recordset()
        self.assertEqual(
            self.employee.notice_count, before,
            "notice_count counts addressed notices regardless of acknowledgement",
        )

    def test_employee_notice_action_returns_domain(self):
        action = self.employee.action_open_notices()
        self.assertEqual(action['res_model'], 'odomate.hr.announcement')
        self.assertTrue(action['domain'])

    # ------------------------------------------------------------------
    # Expiry cron
    # ------------------------------------------------------------------

    def test_cron_expires_only_outdated_published(self):
        outdated = self._make_announcement(
            state='published',
            date_start=self.today - timedelta(days=20),
            date_end=self.today - timedelta(days=2),
        )
        live = self._make_announcement(state='published')
        draft = self._make_announcement()
        waiting = self._make_announcement()
        waiting.action_send_for_approval()

        self.Announcement._cron_expire_announcements()

        self.assertEqual(outdated.state, 'expired')
        self.assertEqual(live.state, 'published')
        self.assertEqual(draft.state, 'draft')
        self.assertEqual(waiting.state, 'to_approve')

    def test_cron_does_not_touch_acknowledgements(self):
        announcement = self._make_announcement(state='published')
        announcement.with_user(self.user_employee).action_acknowledge()
        announcement.write({'date_end': self.today - timedelta(days=1)})
        self.Announcement._cron_expire_announcements()
        self.assertEqual(announcement.state, 'expired')
        self.assertEqual(announcement.acknowledged_count, 1)

    # ------------------------------------------------------------------
    # Systray
    # ------------------------------------------------------------------

    def test_systray_returns_addressed_unacknowledged(self):
        announcement = self._make_announcement(state='published')
        result = self.Announcement.with_user(self.user_employee).get_systray_notices()
        titles = [entry['title'] for entry in result['announcements']]
        self.assertIn(announcement.title, titles)

        announcement.with_user(self.user_employee).action_acknowledge()
        result = self.Announcement.with_user(self.user_employee).get_systray_notices()
        self.assertNotIn(
            announcement.id, [entry['id'] for entry in result['announcements']])

    def test_systray_reminders_empty_without_hr_role(self):
        result = self.Announcement.with_user(self.user_employee).get_systray_notices()
        self.assertEqual(result['reminders'], [])

    def test_systray_does_not_raise_without_employee(self):
        result = self.Announcement.with_user(self.user_no_employee).get_systray_notices()
        self.assertIsInstance(result['announcements'], list)
        self.assertEqual(result['reminders'], [])

    def test_systray_reminders_visible_to_hr(self):
        self.Reminder.create({
            'name': 'Employee records created today',
            'model_id': self.env['ir.model']._get('hr.employee').id,
            'field_id': self.env['ir.model.fields']._get('hr.employee', 'create_date').id,
            'window': 'today',
            'company_id': self.company.id,
        })
        result = self.Announcement.with_user(self.user_hr_officer).get_systray_notices()
        self.assertTrue(result['reminders'])
        for entry in result['reminders']:
            self.assertGreater(entry['count'], 0, "Zero-count reminders are omitted")

    # ------------------------------------------------------------------
    # Reminders
    # ------------------------------------------------------------------

    def _make_reminder(self, **overrides):
        vals = {
            'name': 'Employee records',
            'model_id': self.env['ir.model']._get('hr.employee').id,
            'field_id': self.env['ir.model.fields']._get('hr.employee', 'create_date').id,
            'window': 'today',
            'company_id': self.company.id,
        }
        vals.update(overrides)
        return self.Reminder.create(vals)

    def test_reminder_window_today(self):
        reminder = self._make_reminder()
        domain = reminder._get_match_domain()
        self.assertEqual(len(domain), 2)
        self.assertEqual(domain[0][0], 'create_date')
        self.assertGreater(reminder.preview_count, 0)

    def test_reminder_window_days_ahead(self):
        reminder = self._make_reminder(window='days_ahead', days_ahead=15)
        domain = reminder._get_match_domain()
        self.assertEqual(domain[0][1], '>=')
        self.assertEqual(domain[1][1], '<=')
        self.assertGreater(reminder.preview_count, 0)

    def test_reminder_window_period(self):
        reminder = self._make_reminder(
            window='period',
            date_from=self.today - timedelta(days=1),
            date_to=self.today + timedelta(days=1),
        )
        self.assertGreater(reminder.preview_count, 0)

    def test_reminder_incomplete_period_yields_zero(self):
        reminder = self._make_reminder(window='period', date_from=False, date_to=False)
        self.assertIsNone(reminder._get_match_domain())
        self.assertEqual(reminder.preview_count, 0)

    def test_reminder_open_matching_records(self):
        reminder = self._make_reminder()
        action = reminder.action_open_matching_records()
        self.assertEqual(action['res_model'], 'hr.employee')
        self.assertTrue(action['domain'])

    def test_reminder_open_without_field_raises(self):
        reminder = self._make_reminder(field_id=False)
        with self.assertRaises(UserError):
            reminder.action_open_matching_records()

    def test_reminder_model_whitelist(self):
        domain = self.Reminder._reminder_model_domain()
        allowed = domain[0][2]
        self.assertIn('hr.employee', allowed)
        self.assertNotIn('res.partner', allowed)

    def test_reminder_write_and_unlink(self):
        reminder = self._make_reminder()
        reminder.write({'name': 'Renamed reminder'})
        self.assertEqual(reminder.name, 'Renamed reminder')
        reminder_id = reminder.id
        reminder.unlink()
        self.assertFalse(self.Reminder.browse(reminder_id).exists())

    def test_reminder_not_readable_by_plain_employee(self):
        self._make_reminder()
        with self.assertRaises(AccessError):
            self.Reminder.with_user(self.user_employee).search([])
