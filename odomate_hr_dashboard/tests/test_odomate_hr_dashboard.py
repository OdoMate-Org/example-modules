from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOdomateHrDashboard(TransactionCase):
    """Self-contained fixtures: the suite never relies on --with-demo."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.today()
        cls.company = cls.env['res.company'].create({'name': 'OdoMate Overview Test Co'})
        cls.env.user.company_ids = [(4, cls.company.id)]

        attendances = []
        for dayofweek in range(7):
            attendances.append((0, 0, {
                'name': 'Morning',
                'dayofweek': str(dayofweek),
                'hour_from': 8.0,
                'hour_to': 12.0,
                'day_period': 'morning',
            }))
            attendances.append((0, 0, {
                'name': 'Afternoon',
                'dayofweek': str(dayofweek),
                'hour_from': 13.0,
                'hour_to': 17.0,
                'day_period': 'afternoon',
            }))
        cls.calendar = cls.env['resource.calendar'].create({
            'name': 'Overview Test 7/7',
            'company_id': cls.company.id,
            'tz': 'UTC',
            'hours_per_day': 8.0,
            'attendance_ids': attendances,
        })

        cls.hr_manager = cls.env['res.users'].create({
            'name': 'Overview HR Manager',
            'login': 'odomate_overview_hr_manager',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('hr.group_hr_manager').id,
                cls.env.ref('hr_holidays.group_hr_holidays_manager').id,
            ])],
        })
        cls.plain_user = cls.env['res.users'].create({
            'name': 'Overview Plain User',
            'login': 'odomate_overview_plain_user',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        auto_employees = cls.env['hr.employee'].with_context(active_test=False).search([
            ('user_id', 'in', (cls.hr_manager | cls.plain_user).ids),
        ])
        auto_employees.unlink()

        cls.dept_ops = cls.env['hr.department'].with_company(cls.company).create({'name': 'Overview Ops'})
        cls.dept_care = cls.env['hr.department'].with_company(cls.company).create({'name': 'Overview Care'})
        cls.departure_reason = cls.env['hr.departure.reason'].create({'name': 'Overview Test Resignation'})

        cls.leave_type = cls.env['hr.leave.type'].create({
            'name': 'Overview Test Time Off',
            'company_id': cls.company.id,
            'requires_allocation': False,
            'employee_requests': True,
            'leave_validation_type': 'hr',
            'request_unit': 'day',
        })

        long_ago = cls.today - timedelta(days=500)
        cls.emp_old = cls._make_employee('Overview Old', cls.today - timedelta(days=400), department=cls.dept_ops)
        cls.emp_j1 = cls._make_employee('Overview Joiner One', cls.today - timedelta(days=30), department=cls.dept_ops)
        cls.emp_j2 = cls._make_employee('Overview Joiner Two', cls.today - timedelta(days=20), department=cls.dept_care)
        cls.emp_bradford = cls._make_employee('Overview Bradford', long_ago, department=cls.dept_ops)
        cls.emp_long = cls._make_employee('Overview Long Absence', long_ago, department=cls.dept_care)
        cls.emp_confirm = cls._make_employee('Overview Unapproved', long_ago, department=cls.dept_ops)
        cls.emp_future = cls._make_employee('Overview Future Leave', long_ago, department=cls.dept_ops)
        cls.emp_off_today = cls._make_employee('Overview Off Today', long_ago, department=cls.dept_care)
        cls.emp_nostart = cls._make_employee('Overview No Start Date', None, department=cls.dept_ops)

        cls.emp_leaver = cls._make_employee('Overview Leaver', cls.today - timedelta(days=300), department=cls.dept_care)
        cls.emp_leaver.version_id.write({
            'departure_date': cls.today - timedelta(days=10),
            'departure_reason_id': cls.departure_reason.id,
        })
        cls.emp_leaver.action_archive()

        # occurrences 4, days 1 + 1 + 1 + 3 = 6, factor 4 * 4 * 6 = 96
        for offset in (40, 35, 30):
            cls._make_leave(cls.emp_bradford, cls.today - timedelta(days=offset),
                            cls.today - timedelta(days=offset), 'validate')
        cls._make_leave(cls.emp_bradford, cls.today - timedelta(days=25),
                        cls.today - timedelta(days=23), 'validate')

        # occurrences 1, days 10, factor 1 * 1 * 10 = 10 -> more days, lower factor
        cls._make_leave(cls.emp_long, cls.today - timedelta(days=60),
                        cls.today - timedelta(days=51), 'validate')

        # never approved -> excluded entirely
        cls._make_leave(cls.emp_confirm, cls.today - timedelta(days=40),
                        cls.today - timedelta(days=40), 'confirm')

        # approved but starts next week -> excluded entirely
        cls._make_leave(cls.emp_future, cls.today + timedelta(days=7),
                        cls.today + timedelta(days=8), 'validate')

        # approved but not finished -> off today, excluded from the Bradford view
        cls._make_leave(cls.emp_off_today, cls.today - timedelta(days=1),
                        cls.today + timedelta(days=1), 'validate')

        cls.date_from = cls.today - timedelta(days=35)
        cls.date_to = cls.today

    @classmethod
    def _make_employee(cls, name, contract_start, department=None):
        employee = cls.env['hr.employee'].with_company(cls.company).create({
            'name': name,
            'company_id': cls.company.id,
        })
        employee.resource_id.calendar_id = cls.calendar
        employee.version_id.write({
            'resource_calendar_id': cls.calendar.id,
            'contract_date_start': contract_start or False,
            'department_id': department.id if department else False,
        })
        return employee

    @classmethod
    def _make_leave(cls, employee, day_from, day_to, state):
        leave = cls.env['hr.leave'].with_user(cls.hr_manager).with_company(cls.company).create({
            'employee_id': employee.id,
            'holiday_status_id': cls.leave_type.id,
            'request_date_from': day_from,
            'request_date_to': day_to,
        })
        if state != 'confirm':
            leave.write({'state': state})
        return leave

    def _movement(self):
        return self.env['odomate.hr.movement'].with_context(
            active_test=False, allowed_company_ids=[self.company.id])

    def _absence(self):
        return self.env['odomate.hr.absence.factor'].with_context(
            allowed_company_ids=[self.company.id])

    def _overview(self, date_from=None, date_to=None, user=None):
        model = self.env['odomate.hr.dashboard'].with_user(user or self.hr_manager)
        return model.with_context(allowed_company_ids=[self.company.id]).get_overview(
            str(date_from or self.date_from), str(date_to or self.date_to))

    def _count_action(self, action):
        context = dict(action.get('context') or {})
        context['allowed_company_ids'] = [self.company.id]
        model = self.env[action['res_model']].with_user(self.hr_manager).with_context(**context)
        return model.search_count(action['domain'])

    # ------------------------------------------------------------------
    # odomate.hr.movement
    # ------------------------------------------------------------------
    def test_movement_join_rows(self):
        rows = self._movement().search([
            ('company_id', '=', self.company.id), ('direction', '=', 'join')])
        self.assertEqual(len(rows), 9, "Every employee carrying contract_date_start is one join row")
        self.assertNotIn(self.emp_nostart, rows.employee_id,
                         "An employee without contract_date_start is not a joiner")

    def test_movement_primary_key_formula(self):
        join_row = self._movement().search([
            ('employee_id', '=', self.emp_j1.id), ('direction', '=', 'join')])
        leave_row = self._movement().search([
            ('employee_id', '=', self.emp_leaver.id), ('direction', '=', 'leave')])
        self.assertEqual(join_row.id, self.emp_j1.id * 10 + 1)
        self.assertEqual(leave_row.id, self.emp_leaver.id * 10 + 2)

    def test_movement_leave_row_carries_reason_and_archived_employee(self):
        leave_row = self._movement().search([
            ('company_id', '=', self.company.id), ('direction', '=', 'leave')])
        self.assertEqual(len(leave_row), 1)
        self.assertEqual(leave_row.employee_id, self.emp_leaver)
        self.assertEqual(leave_row.date, self.today - timedelta(days=10))
        self.assertEqual(leave_row.departure_reason_id, self.departure_reason)
        self.assertFalse(leave_row.employee_id.active, "The leaver is archived on hr.employee")

    def test_movement_department_comes_from_version(self):
        row = self._movement().search([
            ('employee_id', '=', self.emp_j2.id), ('direction', '=', 'join')])
        self.assertEqual(row.department_id, self.dept_care)

    def test_movement_join_rows_never_carry_a_departure_reason(self):
        rows = self._movement().search([
            ('company_id', '=', self.company.id), ('direction', '=', 'join')])
        self.assertFalse(rows.departure_reason_id)

    def test_movement_has_no_company_less_row(self):
        self.assertFalse(
            self.env['odomate.hr.movement'].with_context(active_test=False).search(
                [('company_id', '=', False)]),
            "Every movement row must carry a company")

    # ------------------------------------------------------------------
    # odomate.hr.absence.factor
    # ------------------------------------------------------------------
    def test_absence_factor_values(self):
        row = self._absence().search([('employee_id', '=', self.emp_bradford.id)])
        self.assertEqual(len(row), 1)
        self.assertEqual(row.id, self.emp_bradford.id, "Primary key is the employee id")
        self.assertEqual(row.occurrence_count, 4)
        self.assertEqual(row.day_count, 6.0)
        self.assertEqual(row.bradford_factor, 96)
        self.assertEqual(row.department_id, self.dept_ops)
        self.assertEqual(row.company_id, self.company)

    def test_absence_factor_sort_order_is_factor_not_days(self):
        rows = self._absence().search([('company_id', '=', self.company.id)])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].employee_id, self.emp_bradford)
        self.assertEqual(rows[1].employee_id, self.emp_long)
        self.assertGreater(rows[1].day_count, rows[0].day_count,
                           "The second row has MORE days but a LOWER factor")
        self.assertEqual(rows[1].bradford_factor, 10)

    def test_absence_factor_excludes_unapproved_and_unfinished(self):
        employees = self._absence().search([('company_id', '=', self.company.id)]).employee_id
        self.assertNotIn(self.emp_confirm, employees, "state=confirm is not approved")
        self.assertNotIn(self.emp_future, employees, "an approved future leave has not happened yet")
        self.assertNotIn(self.emp_off_today, employees, "a leave still running is not finished")
        self.assertNotIn(self.emp_old, employees, "INNER JOIN: no zero-absence rows")

    def test_name_search_on_both_analysis_models(self):
        movements = self._movement().name_search('', limit=5)
        absences = self._absence().name_search('', limit=5)
        self.assertIsInstance(movements, list)
        self.assertIsInstance(absences, list)
        self.assertTrue(movements)
        self.assertTrue(absences)

    def test_analysis_models_are_read_only_sql_views(self):
        for model_name in ('odomate.hr.movement', 'odomate.hr.absence.factor'):
            self.assertFalse(self.env[model_name]._auto)
            writable = self.env['ir.model.access'].search([
                ('model_id.model', '=', model_name),
            ]).filtered(lambda a: a.perm_write or a.perm_create or a.perm_unlink)
            self.assertFalse(writable, "%s must be read-only for every group" % model_name)

    def test_absence_factor_is_not_summable(self):
        field = self.env['odomate.hr.absence.factor']._fields['bradford_factor']
        self.assertIsNone(field.aggregator, "Summing Bradford factors across employees is meaningless")

    # ------------------------------------------------------------------
    # odomate.hr.dashboard.get_overview
    # ------------------------------------------------------------------
    def test_overview_figures(self):
        payload = self._overview()
        self.assertEqual(payload['headcount'], 9)
        self.assertEqual(payload['joined'], 2)
        self.assertEqual(payload['left'], 1)
        self.assertEqual(payload['off_today'], 1)

    def test_overview_turnover_arithmetic(self):
        payload = self._overview()
        self.assertEqual(payload['turnover_rate'], 13.3)
        detail = payload['turnover_detail']
        self.assertIn('7.5', detail)
        self.assertIn(str(self.date_from), detail)
        self.assertIn(str(self.date_to), detail)
        self.assertTrue(payload['turnover_definition'])
        self.assertNotEqual(payload['turnover_definition'], detail)

    def test_overview_point_in_time_figures_ignore_the_period(self):
        wide = self._overview(self.today - timedelta(days=900), self.today)
        narrow = self._overview(self.today, self.today)
        self.assertEqual(wide['headcount'], narrow['headcount'])
        self.assertEqual(wide['off_today'], narrow['off_today'])
        self.assertEqual(narrow['joined'], 0)
        self.assertEqual(narrow['left'], 0)

    def test_overview_drilldown_parity(self):
        payload = self._overview()
        actions = payload['actions']
        self.assertEqual(self._count_action(actions['headcount']), payload['headcount'])
        self.assertEqual(self._count_action(actions['joined']), payload['joined'])
        self.assertEqual(self._count_action(actions['left']), payload['left'])
        self.assertEqual(self._count_action(actions['off_today']), payload['off_today'])
        self.assertEqual(self._count_action(actions['turnover']), payload['left'],
                         "Turnover drills into its numerator, the departures list")

    def test_overview_movement_actions_disable_active_test(self):
        actions = self._overview()['actions']
        for key in ('joined', 'left', 'turnover'):
            self.assertEqual(actions[key]['res_model'], 'odomate.hr.movement')
            self.assertFalse(actions[key]['context']['active_test'])

    def test_overview_pending_never_returns_a_zero_row(self):
        payload = self._overview()
        self.assertIsInstance(payload['pending'], list)
        for entry in payload['pending']:
            self.assertGreater(entry['count'], 0)
            self.assertIn(entry['model'], self.env)
            self.assertTrue(entry['label'])
            self.assertEqual(entry['action']['res_model'], entry['model'])

    # ------------------------------------------------------------------
    # security
    # ------------------------------------------------------------------
    def test_plain_internal_user_has_no_access(self):
        with self.assertRaises(AccessError):
            self.env['odomate.hr.movement'].with_user(self.plain_user).search([])
        with self.assertRaises(AccessError):
            self.env['odomate.hr.absence.factor'].with_user(self.plain_user).search([])
        with self.assertRaises(AccessError):
            self._overview(user=self.plain_user)

    def test_hr_user_can_read_both_analysis_models(self):
        hr_user = self.env['res.users'].create({
            'name': 'Overview HR User',
            'login': 'odomate_overview_hr_user',
            'company_id': self.company.id,
            'company_ids': [(6, 0, [self.company.id])],
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('hr.group_hr_user').id,
            ])],
        })
        movements = self.env['odomate.hr.movement'].with_user(hr_user).with_context(
            active_test=False, allowed_company_ids=[self.company.id]).search([])
        self.assertTrue(movements)
        absences = self.env['odomate.hr.absence.factor'].with_user(hr_user).with_context(
            allowed_company_ids=[self.company.id]).search([])
        self.assertTrue(absences)

    def test_module_grants_no_group_to_anybody(self):
        granting = self.env['ir.model.data'].search([
            ('module', '=', 'odomate_hr_dashboard'),
            ('model', 'in', ('res.users', 'res.groups')),
        ])
        self.assertFalse(granting, "This module must not grant or define any group")

    def test_no_acl_widens_payroll_or_contract_access(self):
        acls = self.env['ir.model.access'].search([
            ('model_id.model', 'in', ('hr.payslip', 'hr.version')),
        ]).filtered(lambda a: a.get_external_id().get(a.id, '').startswith('odomate_hr_dashboard.'))
        self.assertFalse(acls, "This module must not widen payroll or contract access")
