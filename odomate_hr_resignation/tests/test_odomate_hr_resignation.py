from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOdomateHrResignation(TransactionCase):

    @classmethod
    def _employee_for_user(cls, user):
        """This database creates an employee automatically with every user."""
        employee = cls.env['hr.employee'].with_context(active_test=False).search(
            [('user_id', '=', user.id)], limit=1
        )
        if not employee:
            employee = cls.env['hr.employee'].create({
                'name': user.name,
                'user_id': user.id,
                'company_id': user.company_id.id,
            })
        cls._prepare_version(employee)
        return employee

    @classmethod
    def _prepare_version(cls, employee):
        """hr.version refuses a contract end date without a start date."""
        employee.version_id.write({
            'contract_date_start': fields.Date.today() - timedelta(days=400),
            'notice_period': 30,
        })
        return employee

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref('base.main_company')
        cls.today = fields.Date.context_today(cls.env['odomate.hr.resignation'])

        cls.departure_reason = cls.env['hr.departure.reason'].create({
            'name': "Resigned (test)",
        })

        cls.hr_user = cls.env['res.users'].create({
            'name': "HR Officer",
            'login': 'test_hr_officer',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, cls.company.ids)],
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('hr.group_hr_manager').id,
            ])],
        })
        cls.manager_user = cls.env['res.users'].create({
            'name': "Team Lead",
            'login': 'test_team_lead',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, cls.company.ids)],
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        cls.bystander_user = cls.env['res.users'].create({
            'name': "Unrelated Colleague",
            'login': 'test_bystander',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, cls.company.ids)],
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        cls.it_user = cls.env['res.users'].create({
            'name': "IT Responsible",
            'login': 'test_it_responsible',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, cls.company.ids)],
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

        cls.manager_employee = cls._employee_for_user(cls.manager_user)
        cls.employee = cls.env['hr.employee'].create({
            'name': "Rita Resigner",
            'parent_id': cls.manager_employee.id,
            'company_id': cls.company.id,
        })
        cls._prepare_version(cls.employee)

        cls.clearance_item_it = cls.env['odomate.hr.clearance.item'].create({
            'name': "Test IT Accounts",
            'sequence': 5,
            'responsible_user_id': cls.it_user.id,
            'company_id': False,
        })
        cls.clearance_item_finance = cls.env['odomate.hr.clearance.item'].create({
            'name': "Test Finance",
            'sequence': 6,
            'company_id': cls.company.id,
        })
        # Not visible to this run: archived items must never produce a line.
        cls.clearance_item_archived = cls.env['odomate.hr.clearance.item'].create({
            'name': "Test Archived Item",
            'sequence': 7,
            'company_id': False,
            'active': False,
        })

        cls.custody_item = cls.env['odomate.hr.custody.item'].create({
            'name': "Test Projector",
            'company_id': cls.company.id,
        })

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _new_resignation(self, employee=None, **values):
        vals = {
            'employee_id': (employee or self.employee).id,
            'date_notified': self.today,
            'reason': "Moving on to a new challenge.",
            'departure_reason_id': self.departure_reason.id,
            'company_id': self.company.id,
        }
        vals.update(values)
        return self.env['odomate.hr.resignation'].create(vals)

    def _new_custody(self, employee=None, state='approved', return_date=None):
        return self.env['odomate.hr.custody'].create({
            'name': "HO/TEST/0001",
            'employee_id': (employee or self.employee).id,
            'item_id': self.custody_item.id,
            'reason': "Field work",
            'request_date': self.today,
            'return_date': return_date or (self.today + timedelta(days=10)),
            'state': state,
            'company_id': self.company.id,
        })

    def _clear_all_lines(self, resignation):
        resignation.clearance_line_ids.write({
            'state': 'cleared',
            'cleared_date': self.today,
        })

    # ------------------------------------------------------------------
    # Creation, sequence and notice period
    # ------------------------------------------------------------------
    def test_create_assigns_sequence_and_defaults(self):
        resignation = self._new_resignation()
        self.assertNotEqual(resignation.name, "New")
        self.assertTrue(resignation.name.startswith("RES/"))
        self.assertEqual(resignation.state, 'draft')
        self.assertEqual(resignation.department_id, self.employee.department_id)

    def test_notice_period_read_from_current_version(self):
        resignation = self._new_resignation()
        self.assertEqual(resignation.notice_period_days, 30)
        self.assertEqual(
            resignation.proposed_last_working_day,
            self.today + timedelta(days=30),
        )

    def test_last_working_day_mirrors_proposal_until_edited(self):
        resignation = self._new_resignation()
        self.assertFalse(resignation.last_working_day_manual)
        self.assertEqual(
            resignation.last_working_day, resignation.proposed_last_working_day
        )

        resignation.date_notified = self.today + timedelta(days=2)
        self.assertEqual(
            resignation.last_working_day, resignation.proposed_last_working_day
        )

    def test_manual_last_working_day_is_never_overwritten(self):
        resignation = self._new_resignation()
        chosen = self.today + timedelta(days=45)
        resignation.last_working_day = chosen

        self.assertTrue(resignation.last_working_day_manual)

        resignation.date_notified = self.today + timedelta(days=3)
        self.assertEqual(resignation.last_working_day, chosen)
        self.assertNotEqual(
            resignation.last_working_day, resignation.proposed_last_working_day
        )

    def test_last_working_day_cannot_precede_notification(self):
        resignation = self._new_resignation()
        with self.assertRaises(ValidationError):
            resignation.last_working_day = self.today - timedelta(days=1)

    # ------------------------------------------------------------------
    # One open resignation per employee
    # ------------------------------------------------------------------
    def test_only_one_open_resignation_per_employee(self):
        self._new_resignation()
        with self.assertRaises(ValidationError):
            self._new_resignation()

    def test_second_resignation_allowed_after_withdrawal(self):
        first = self._new_resignation()
        first.action_withdraw()
        self.assertEqual(first.state, 'withdrawn')
        second = self._new_resignation()
        self.assertEqual(second.state, 'draft')

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def test_confirm_schedules_manager_activity(self):
        self.company.resignation_manager_approval_required = True
        resignation = self._new_resignation()
        resignation.action_confirm()

        self.assertEqual(resignation.state, 'confirmed')
        self.assertIn(self.manager_user, resignation.activity_ids.user_id)

    def test_manager_approve_moves_to_manager_approved(self):
        self.company.resignation_manager_approval_required = True
        resignation = self._new_resignation()
        resignation.action_confirm()
        resignation.with_user(self.manager_user).action_manager_approve()

        self.assertEqual(resignation.state, 'manager_approved')

    def test_manager_approve_refused_for_unrelated_user(self):
        self.company.resignation_manager_approval_required = True
        resignation = self._new_resignation()
        resignation.action_confirm()
        with self.assertRaises(AccessError):
            resignation.with_user(self.bystander_user).action_manager_approve()

    def test_hr_approve_skips_manager_step_when_disabled(self):
        self.company.resignation_manager_approval_required = False
        resignation = self._new_resignation()
        resignation.action_confirm()
        self.assertEqual(resignation.state, 'confirmed')

        resignation.with_user(self.hr_user).action_hr_approve()
        self.assertEqual(resignation.state, 'clearance')

    def test_hr_approve_builds_checklist_from_visible_items(self):
        resignation = self._new_resignation()
        resignation.action_confirm()
        resignation.with_user(self.hr_user).action_manager_approve()
        resignation.with_user(self.hr_user).action_hr_approve()

        items = resignation.clearance_line_ids.clearance_item_id
        self.assertIn(self.clearance_item_it, items)
        self.assertIn(self.clearance_item_finance, items)
        self.assertNotIn(self.clearance_item_archived, items)

        it_line = resignation.clearance_line_ids.filtered(
            lambda line: line.clearance_item_id == self.clearance_item_it
        )
        self.assertEqual(it_line.responsible_user_id, self.it_user)

        finance_line = resignation.clearance_line_ids.filtered(
            lambda line: line.clearance_item_id == self.clearance_item_finance
        )
        self.assertEqual(finance_line.responsible_user_id, self.hr_user)
        self.assertEqual(finance_line.employee_id, self.employee)
        self.assertEqual(finance_line.company_id, self.company)

    def test_hr_approve_snapshots_outstanding_custody_as_blocked_line(self):
        custody = self._new_custody()
        resignation = self._new_resignation()
        resignation.action_confirm()
        resignation.with_user(self.hr_user).action_manager_approve()
        resignation.with_user(self.hr_user).action_hr_approve()

        blocked = resignation.clearance_line_ids.filtered(
            lambda line: line.state == 'blocked'
        )
        self.assertEqual(len(blocked), 1)
        self.assertIn(self.custody_item.name, blocked.remark)
        self.assertIn(custody.name, blocked.remark)
        self.assertIn(fields.Date.to_string(custody.return_date), blocked.remark)

    def test_hr_approve_without_custody_creates_no_blocked_line(self):
        resignation = self._new_resignation()
        resignation.action_confirm()
        resignation.with_user(self.hr_user).action_manager_approve()
        resignation.with_user(self.hr_user).action_hr_approve()

        self.assertFalse(
            resignation.clearance_line_ids.filtered(lambda line: line.state == 'blocked')
        )

    def test_hr_approve_schedules_activity_per_responsible(self):
        resignation = self._new_resignation()
        resignation.action_confirm()
        resignation.with_user(self.hr_user).action_manager_approve()
        resignation.with_user(self.hr_user).action_hr_approve()

        it_line = resignation.clearance_line_ids.filtered(
            lambda line: line.clearance_item_id == self.clearance_item_it
        )
        self.assertIn(self.it_user, it_line.activity_ids.user_id)

    # ------------------------------------------------------------------
    # Refuse / withdraw
    # ------------------------------------------------------------------
    def test_refuse_wizard_requires_reason_and_closes_activities(self):
        resignation = self._new_resignation()
        resignation.action_confirm()
        self.assertTrue(resignation.activity_ids)

        wizard = self.env['odomate.hr.resignation.refuse'].create({
            'resignation_id': resignation.id,
            'reason': "Counter-offer accepted.",
        })
        wizard.action_confirm_refusal()

        self.assertEqual(resignation.state, 'refused')
        self.assertEqual(resignation.refusal_reason, "Counter-offer accepted.")
        self.assertFalse(resignation.activity_ids)

    def test_withdraw_leaves_employee_untouched(self):
        resignation = self._new_resignation()
        resignation.action_confirm()
        resignation.action_withdraw()

        self.assertEqual(resignation.state, 'withdrawn')
        self.assertFalse(resignation.activity_ids)
        self.assertTrue(self.employee.active)
        self.assertFalse(self.employee.departure_date)

    def test_withdraw_blocked_after_release(self):
        resignation = self._release_ready_resignation()
        resignation.with_user(self.hr_user).action_release()
        with self.assertRaises(UserError):
            resignation.action_withdraw()

    # ------------------------------------------------------------------
    # Release
    # ------------------------------------------------------------------
    def _release_ready_resignation(self, employee=None):
        resignation = self._new_resignation(employee=employee)
        resignation.action_confirm()
        resignation.with_user(self.hr_user).action_manager_approve()
        resignation.with_user(self.hr_user).action_hr_approve()
        self._clear_all_lines(resignation)
        return resignation

    def test_release_blocked_by_live_custody(self):
        resignation = self._release_ready_resignation()
        self._new_custody()
        with self.assertRaises(UserError) as capture:
            resignation.with_user(self.hr_user).action_release()
        self.assertIn(self.custody_item.name, str(capture.exception))

    def test_release_blocked_by_pending_clearance_line(self):
        resignation = self._new_resignation()
        resignation.action_confirm()
        resignation.with_user(self.hr_user).action_manager_approve()
        resignation.with_user(self.hr_user).action_hr_approve()

        with self.assertRaises(UserError) as capture:
            resignation.with_user(self.hr_user).action_release()
        self.assertIn("clearance", str(capture.exception).lower())

    def test_release_updates_employee_and_version(self):
        resignation = self._release_ready_resignation()
        last_day = resignation.last_working_day
        resignation.with_user(self.hr_user).action_release()

        self.assertEqual(resignation.state, 'released')
        self.assertEqual(resignation.release_date, last_day)
        self.assertEqual(self.employee.departure_date, last_day)
        self.assertEqual(self.employee.departure_reason_id, self.departure_reason)
        self.assertEqual(self.employee.version_id.contract_date_end, last_day)
        self.assertFalse(self.employee.active)

    def test_release_archives_linked_user(self):
        user = self.env['res.users'].create({
            'name': "Leaver With Login",
            'login': 'test_leaver_login',
            'company_id': self.company.id,
            'company_ids': [(6, 0, self.company.ids)],
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        employee = self._employee_for_user(user)
        resignation = self._release_ready_resignation(employee=employee)
        resignation.with_user(self.hr_user).action_release()

        self.assertEqual(resignation.state, 'released')
        self.assertFalse(user.active)

    def test_post_release_record_is_immutable(self):
        resignation = self._release_ready_resignation()
        resignation.with_user(self.hr_user).action_release()

        with self.assertRaises(UserError):
            resignation.date_notified = self.today - timedelta(days=5)
        with self.assertRaises(UserError):
            resignation.reason = "Rewritten history."

    def test_post_release_clearance_lines_are_immutable(self):
        resignation = self._release_ready_resignation()
        resignation.with_user(self.hr_user).action_release()

        line = resignation.clearance_line_ids[0]
        with self.assertRaises(UserError):
            line.remark = "Changed after the fact."

    # ------------------------------------------------------------------
    # Cron
    # ------------------------------------------------------------------
    def test_cron_releases_when_everything_is_clear(self):
        resignation = self._release_ready_resignation()
        resignation.date_notified = self.today - timedelta(days=90)
        resignation.last_working_day = self.today - timedelta(days=1)

        self.env['odomate.hr.resignation']._cron_release_resignations()
        self.assertEqual(resignation.state, 'released')

    def test_cron_skips_records_with_outstanding_property(self):
        resignation = self._release_ready_resignation()
        resignation.date_notified = self.today - timedelta(days=90)
        resignation.last_working_day = self.today - timedelta(days=1)
        self._new_custody()

        self.env['odomate.hr.resignation']._cron_release_resignations()
        self.assertEqual(resignation.state, 'clearance')

    def test_cron_skips_future_last_working_day(self):
        resignation = self._release_ready_resignation()
        self.env['odomate.hr.resignation']._cron_release_resignations()
        self.assertEqual(resignation.state, 'clearance')

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------
    def test_outstanding_property_count_is_live(self):
        resignation = self._new_resignation()
        self.assertEqual(resignation.outstanding_property_count, 0)

        self._new_custody()
        resignation.invalidate_recordset(['outstanding_property_count'])
        self.assertEqual(resignation.outstanding_property_count, 1)

    def test_returned_custody_is_not_outstanding(self):
        resignation = self._new_resignation()
        self._new_custody(state='returned')
        resignation.invalidate_recordset(['outstanding_property_count'])
        self.assertEqual(resignation.outstanding_property_count, 0)

    def test_clearance_progress(self):
        resignation = self._new_resignation()
        resignation.action_confirm()
        resignation.with_user(self.hr_user).action_manager_approve()
        resignation.with_user(self.hr_user).action_hr_approve()

        total = len(resignation.clearance_line_ids)
        self.assertTrue(total)
        self.assertEqual(resignation.clearance_progress, 0.0)

        resignation.clearance_line_ids[0].state = 'cleared'
        self.assertAlmostEqual(resignation.clearance_progress, 100.0 / total, places=4)

        self._clear_all_lines(resignation)
        self.assertAlmostEqual(resignation.clearance_progress, 100.0, places=4)

    # ------------------------------------------------------------------
    # Clearance line permissions
    # ------------------------------------------------------------------
    def test_responsible_user_can_clear_own_line(self):
        resignation = self._new_resignation()
        resignation.action_confirm()
        resignation.with_user(self.hr_user).action_manager_approve()
        resignation.with_user(self.hr_user).action_hr_approve()

        line = resignation.clearance_line_ids.filtered(
            lambda candidate: candidate.clearance_item_id == self.clearance_item_it
        )
        line.with_user(self.it_user).action_set_cleared()
        self.assertEqual(line.state, 'cleared')
        self.assertEqual(
            line.cleared_date,
            fields.Date.context_today(line.with_user(self.it_user)),
        )

    def test_unrelated_user_cannot_see_clearance_line(self):
        resignation = self._new_resignation()
        resignation.action_confirm()
        resignation.with_user(self.hr_user).action_manager_approve()
        resignation.with_user(self.hr_user).action_hr_approve()

        visible = self.env['odomate.hr.resignation.clearance.line'].with_user(
            self.bystander_user
        ).search([('resignation_id', '=', resignation.id)])
        self.assertFalse(visible)

    def test_responsible_user_sees_only_own_lines(self):
        resignation = self._new_resignation()
        resignation.action_confirm()
        resignation.with_user(self.hr_user).action_manager_approve()
        resignation.with_user(self.hr_user).action_hr_approve()

        visible = self.env['odomate.hr.resignation.clearance.line'].with_user(
            self.it_user
        ).search([])
        self.assertTrue(visible)
        self.assertEqual(visible.responsible_user_id, self.it_user)

    # ------------------------------------------------------------------
    # Record rules on the resignation itself
    # ------------------------------------------------------------------
    def test_line_manager_sees_own_team_resignation_only(self):
        mine = self._new_resignation()
        other_employee = self.env['hr.employee'].create({
            'name': "Somebody Else",
            'company_id': self.company.id,
        })
        theirs = self._new_resignation(employee=other_employee)

        visible = self.env['odomate.hr.resignation'].with_user(
            self.manager_user
        ).search([])
        self.assertIn(mine, visible)
        self.assertNotIn(theirs, visible)

    def test_bystander_sees_no_resignation(self):
        self._new_resignation()
        visible = self.env['odomate.hr.resignation'].with_user(
            self.bystander_user
        ).search([])
        self.assertFalse(visible)

    # ------------------------------------------------------------------
    # Clearance item configuration
    # ------------------------------------------------------------------
    def test_clearance_item_name_search(self):
        found = self.env['odomate.hr.clearance.item'].name_search("Test IT")
        self.assertIn(self.clearance_item_it.id, [item[0] for item in found])

    def test_clearance_item_crud(self):
        item = self.env['odomate.hr.clearance.item'].create({
            'name': "Test Badge Return",
            'company_id': self.company.id,
        })
        self.assertTrue(item.active)
        item.write({'sequence': 99})
        self.assertEqual(item.sequence, 99)
        item.unlink()
        self.assertFalse(item.exists())

    def test_custody_register_is_never_written(self):
        custody = self._new_custody()
        resignation = self._new_resignation()
        resignation.action_confirm()
        resignation.with_user(self.hr_user).action_manager_approve()
        resignation.with_user(self.hr_user).action_hr_approve()

        self.assertEqual(custody.state, 'approved')
        self.assertFalse(custody.actual_return_date)
