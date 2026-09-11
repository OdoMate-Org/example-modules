from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOdomateHrLeaveEmail(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Log = cls.env['odomate.hr.leave.email.log']
        cls.Leave = cls.env['hr.leave']
        cls.company = cls.env.company

        cls.leave_type = cls.env['hr.leave.type'].create({
            'name': "Email Time Off",
            'company_id': cls.company.id,
            'requires_allocation': False,
            'employee_requests': True,
            'request_unit': 'day',
            'leave_validation_type': 'hr',
        })

        cls.sender_user = cls.env['res.users'].create({
            'name': "Olena Bondar",
            'login': 'olena.bondar@example.com',
            'email': 'olena.bondar@example.com',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': "Olena Bondar",
            'user_id': cls.sender_user.id,
            'company_id': cls.company.id,
        })
        cls.employee_no_user = cls.env['hr.employee'].create({
            'name': "Petro Marchenko",
            'company_id': cls.company.id,
            'work_email': 'petro.marchenko@example.com',
        })

        cls.company.write({
            'leave_email_enabled': True,
            'leave_email_type_id': cls.leave_type.id,
            'leave_email_reply_on_failure': True,
        })

        cls.start = date.today() + relativedelta(days=14, weekday=0)
        cls.end = cls.start + relativedelta(days=1)

    @classmethod
    def _msg(cls, body, email_from='olena.bondar@example.com', subject="Time off"):
        return {
            'email_from': email_from,
            'subject': subject,
            'body': body,
            'to': 'timeoff-request@example.com',
            'message_id': '<test@example.com>',
        }

    def _last_log(self, email_from):
        return self.Log.search([('email_from', '=', email_from)], order='id desc', limit=1)

    # ------------------------------------------------------------------
    # Model basics
    # ------------------------------------------------------------------

    def test_demo_data_loaded(self):
        self.assertTrue(
            self.Log.search_count([]) > 0,
            "Demo data should provide at least one email request log row.")

    def test_create_record(self):
        log = self.Log.create({
            'email_from': 'someone@example.com',
            'subject': "Two days off",
            'state': 'rejected',
            'failure_reason': 'no_date',
        })
        self.assertTrue(log.exists())
        self.assertTrue(log.id > 0)
        self.assertTrue(log.received_date, "received_date must default to now.")

    def test_write_record(self):
        log = self.Log.create({'email_from': 'someone@example.com', 'state': 'rejected'})
        log.write({'notes': "Checked by HR"})
        self.assertEqual(log.notes, "Checked by HR")

    def test_unlink_record(self):
        log = self.Log.create({'email_from': 'someone@example.com', 'state': 'rejected'})
        log_id = log.id
        log.unlink()
        self.assertFalse(self.Log.browse(log_id).exists())

    def test_name_search(self):
        self.assertIsInstance(self.Log.name_search('', limit=5), list)

    def test_display_name(self):
        log = self.Log.create({
            'email_from': 'someone@example.com',
            'subject': "Two days off",
            'state': 'rejected',
        })
        self.assertIn('someone@example.com', log.display_name)
        self.assertIn("Two days off", log.display_name)

    # ------------------------------------------------------------------
    # Date extraction
    # ------------------------------------------------------------------

    def test_extract_dates_iso(self):
        dates = self.Leave._odomate_leave_email_extract_dates(
            '<p>Off from 2026-03-09 until 2026-03-13, thanks.</p>')
        self.assertEqual(dates, [date(2026, 3, 9), date(2026, 3, 13)])

    def test_extract_dates_european(self):
        dates = self.Leave._odomate_leave_email_extract_dates(
            '<div>09/03/2026 - 13/03/2026</div>')
        self.assertEqual(dates, [date(2026, 3, 9), date(2026, 3, 13)])

    def test_extract_dates_single(self):
        dates = self.Leave._odomate_leave_email_extract_dates('<p>Just 2026-03-09 please</p>')
        self.assertEqual(dates, [date(2026, 3, 9)])

    def test_extract_dates_ignores_impossible_date(self):
        dates = self.Leave._odomate_leave_email_extract_dates(
            '<p>2026-13-45 is not a date but 2026-03-09 is</p>')
        self.assertEqual(dates, [date(2026, 3, 9)])

    def test_extract_dates_none(self):
        self.assertEqual(
            self.Leave._odomate_leave_email_extract_dates('<p>Some time next month</p>'), [])

    # ------------------------------------------------------------------
    # Employee resolution
    # ------------------------------------------------------------------

    def test_resolve_employee_by_user_login(self):
        employee = self.Leave._odomate_leave_email_find_employee('olena.bondar@example.com')
        self.assertEqual(employee, self.employee)

    def test_resolve_employee_by_work_email(self):
        employee = self.Leave._odomate_leave_email_find_employee('petro.marchenko@example.com')
        self.assertEqual(employee, self.employee_no_user)

    def test_resolve_employee_unknown(self):
        self.assertFalse(self.Leave._odomate_leave_email_find_employee('nobody@example.com'))

    def test_resolve_employee_prefers_user_own_company(self):
        other_company = self.env['res.company'].create({'name': "Second Company"})
        self.sender_user.write({'company_ids': [(4, other_company.id)]})
        other_employee = self.env['hr.employee'].create({
            'name': "Olena Bondar",
            'user_id': self.sender_user.id,
            'company_id': other_company.id,
        })
        self.assertTrue(other_employee.exists())
        resolved = self.Leave._odomate_leave_email_find_employee('olena.bondar@example.com')
        self.assertEqual(
            resolved.company_id, self.sender_user.company_id,
            "With one employee per company, the sender's own company wins.")

    # ------------------------------------------------------------------
    # message_new — happy path
    # ------------------------------------------------------------------

    def test_message_new_creates_leave(self):
        body = '<p>Hello, I would like %s to %s off.</p>' % (
            self.start.strftime('%Y-%m-%d'), self.end.strftime('%Y-%m-%d'))
        leave = self.Leave.message_new(self._msg(body))
        self.assertTrue(leave, "A Time Off request should have been created.")
        self.assertEqual(leave.employee_id, self.employee)
        self.assertEqual(leave.holiday_status_id, self.leave_type)
        self.assertEqual(leave.request_date_from, self.start)
        self.assertEqual(leave.request_date_to, self.end)

        log = self._last_log('olena.bondar@example.com')
        self.assertEqual(log.state, 'created')
        self.assertFalse(log.failure_reason)
        self.assertEqual(log.leave_id, leave)
        self.assertEqual(log.employee_id, self.employee)
        self.assertEqual(log.company_id, self.employee.company_id)

    def test_message_new_single_date_is_one_day(self):
        body = '<p>Off on %s.</p>' % self.start.strftime('%d/%m/%Y')
        leave = self.Leave.message_new(self._msg(body))
        self.assertEqual(leave.request_date_from, self.start)
        self.assertEqual(leave.request_date_to, self.start)

    # ------------------------------------------------------------------
    # message_new — refusals
    # ------------------------------------------------------------------

    def test_message_new_unknown_sender(self):
        leave = self.Leave.message_new(self._msg(
            '<p>2026-03-09 to 2026-03-13</p>', email_from='stranger@example.org'))
        self.assertFalse(leave)
        log = self._last_log('stranger@example.org')
        self.assertEqual(log.state, 'rejected')
        self.assertEqual(log.failure_reason, 'unknown_sender')
        self.assertFalse(log.employee_id)
        self.assertFalse(
            log.company_id,
            "An unresolved sender leaves company_id empty so HR of any company sees the row.")

    def test_message_new_no_date(self):
        leave = self.Leave.message_new(self._msg('<p>I need a break soon.</p>'))
        self.assertFalse(leave)
        log = self._last_log('olena.bondar@example.com')
        self.assertEqual(log.failure_reason, 'no_date')
        self.assertEqual(log.company_id, self.company)

    def test_message_new_reversed_dates(self):
        leave = self.Leave.message_new(self._msg('<p>From 13/03/2026 to 09/03/2026</p>'))
        self.assertFalse(leave)
        self.assertEqual(
            self._last_log('olena.bondar@example.com').failure_reason, 'reversed_dates')

    def test_message_new_no_leave_type_when_unset(self):
        self.company.leave_email_type_id = False
        leave = self.Leave.message_new(self._msg(
            '<p>%s</p>' % self.start.strftime('%Y-%m-%d')))
        self.assertFalse(leave)
        self.assertEqual(
            self._last_log('olena.bondar@example.com').failure_reason, 'no_leave_type')

    def test_message_new_no_leave_type_when_archived(self):
        self.leave_type.active = False
        leave = self.Leave.message_new(self._msg(
            '<p>%s</p>' % self.start.strftime('%Y-%m-%d')))
        self.assertFalse(leave)
        self.assertEqual(
            self._last_log('olena.bondar@example.com').failure_reason, 'no_leave_type',
            "A type archived after being configured must refuse, not crash.")

    def test_message_new_never_raises(self):
        broken = {'email_from': 'olena.bondar@example.com', 'subject': None, 'body': None}
        leave = self.Leave.message_new(broken)
        self.assertFalse(leave)
        self.assertTrue(self._last_log('olena.bondar@example.com'))

    # ------------------------------------------------------------------
    # message_new — feature switched off
    # ------------------------------------------------------------------

    def test_message_new_disabled_logs_nothing(self):
        self.company.leave_email_enabled = False
        before = self.Log.search_count([])
        self.Leave.message_new(self._msg(
            '<p>%s</p>' % self.start.strftime('%Y-%m-%d'),
            email_from='olena.bondar@example.com'))
        self.assertEqual(
            self.Log.search_count([]), before,
            "With the feature off, no log row may be written.")

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------

    def test_plain_internal_user_has_no_access(self):
        with self.assertRaises(AccessError):
            self.Log.with_user(self.sender_user).search([], limit=1)

    def test_holidays_user_can_read_but_not_write(self):
        officer = self.env['res.users'].create({
            'name': "Iryna Officer",
            'login': 'iryna.officer@example.com',
            'company_id': self.company.id,
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('hr_holidays.group_hr_holidays_user').id,
            ])],
        })
        log = self.Log.create({'email_from': 'someone@example.com', 'state': 'rejected'})
        self.assertTrue(log.with_user(officer).read(['subject']))
        with self.assertRaises(AccessError):
            log.with_user(officer).write({'notes': "not allowed"})

    def test_unresolved_rows_visible_across_companies(self):
        log = self.Log.create({
            'email_from': 'stranger@example.org',
            'state': 'rejected',
            'failure_reason': 'unknown_sender',
        })
        self.assertFalse(log.company_id)
        officer = self.env['res.users'].create({
            'name': "Bohdan Officer",
            'login': 'bohdan.officer@example.com',
            'company_id': self.company.id,
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('hr_holidays.group_hr_holidays_user').id,
            ])],
        })
        found = self.Log.with_user(officer).search([('id', '=', log.id)])
        self.assertEqual(found, log)

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def test_alias_is_shipped_and_points_at_hr_leave(self):
        alias = self.env.ref('odomate_hr_leave_email.mail_alias_hr_leave_request')
        self.assertEqual(alias.alias_model_id.model, 'hr.leave')
        self.assertEqual(alias.alias_contact, 'employees')
        self.assertEqual(self.company.leave_email_alias_id, alias)

    def test_settings_warns_when_address_has_no_domain(self):
        alias = self.env.ref('odomate_hr_leave_email.mail_alias_hr_leave_request')
        alias.alias_domain_id = False
        self.company.alias_domain_id = False
        settings = self.env['res.config.settings'].create({})
        self.assertTrue(
            settings.leave_email_domain_missing,
            "Without an alias domain the address cannot receive anything and the "
            "settings screen must say so.")
        self.assertEqual(settings.leave_email_address, alias.alias_name)

    def test_settings_shows_full_address_once_a_domain_exists(self):
        alias = self.env.ref('odomate_hr_leave_email.mail_alias_hr_leave_request')
        alias.alias_domain_id = self.env['mail.alias.domain'].create({
            'name': 'timeoff.example.com',
            'bounce_alias': 'bounce-timeoff',
            'catchall_alias': 'catchall-timeoff',
        })
        settings = self.env['res.config.settings'].create({})
        self.assertFalse(settings.leave_email_domain_missing)
        self.assertEqual(
            settings.leave_email_address, '%s@timeoff.example.com' % alias.alias_name)

    def test_settings_round_trip(self):
        settings = self.env['res.config.settings'].create({
            'leave_email_enabled': True,
            'leave_email_reply_on_failure': False,
        })
        settings.execute()
        self.assertTrue(self.company.leave_email_enabled)
        self.assertFalse(self.company.leave_email_reply_on_failure)
