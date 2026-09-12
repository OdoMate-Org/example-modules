from datetime import date, timedelta

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestOdomateHrTransfer(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Transfer = cls.env['odomate.hr.transfer']
        cls.company_a = cls.env.company
        cls.company_b = cls.env['res.company'].create({'name': 'Transfer Test Company B'})

        cls.dept_sales = cls.env['hr.department'].create({
            'name': 'Transfer Test Sales',
            'company_id': cls.company_a.id,
        })
        cls.dept_support = cls.env['hr.department'].create({
            'name': 'Transfer Test Support',
            'company_id': cls.company_a.id,
        })
        cls.job_agent = cls.env['hr.job'].create({
            'name': 'Transfer Test Agent',
            'company_id': cls.company_a.id,
        })
        cls.location_hq = cls.env['hr.work.location'].create({
            'name': 'Transfer Test HQ',
            'company_id': cls.company_a.id,
            'location_type': 'office',
            'address_id': cls.company_a.partner_id.id,
        })

        cls.past = date.today() - timedelta(days=400)
        cls.yesterday = date.today() - timedelta(days=1)
        cls.tomorrow = date.today() + timedelta(days=1)

        cls.employee = cls._make_employee('Transfer Test Employee', cls.dept_sales)
        cls.manager_employee = cls._make_employee('Transfer Test Boss', cls.dept_support)

        cls.hr_officer = cls.env['res.users'].create({
            'name': 'Transfer Test HR Officer',
            'login': 'transfer_test_officer',
            'company_id': cls.company_a.id,
            'company_ids': [(6, 0, [cls.company_a.id])],
            'group_ids': [(6, 0, [cls.env.ref('hr.group_hr_user').id])],
        })
        cls.hr_manager = cls.env['res.users'].create({
            'name': 'Transfer Test HR Manager',
            'login': 'transfer_test_manager',
            'company_id': cls.company_a.id,
            'company_ids': [(6, 0, [cls.company_a.id])],
            'group_ids': [(6, 0, [cls.env.ref('hr.group_hr_manager').id])],
        })
        cls.plain_user = cls.env['res.users'].create({
            'name': 'Transfer Test Plain User',
            'login': 'transfer_test_plain',
            'company_id': cls.company_a.id,
            'company_ids': [(6, 0, [cls.company_a.id])],
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

    @classmethod
    def _make_employee(cls, name, department=None, company=None):
        employee = cls.env['hr.employee'].create({
            'name': name,
            'company_id': (company or cls.company_a).id,
        })
        if department:
            employee.version_ids.department_id = department.id
        employee.version_ids.write({'date_version': cls.past})
        employee.invalidate_recordset()
        return employee

    def _new_transfer(self, **vals):
        base_vals = {
            'employee_id': self.employee.id,
            'effective_date': self.yesterday,
            'new_department_id': self.dept_support.id,
        }
        base_vals.update(vals)
        return self.Transfer.create(base_vals)

    # ------------------------------------------------------------------
    # Reference / computed fields
    # ------------------------------------------------------------------
    def test_create_assigns_sequence_reference(self):
        transfer = self._new_transfer()
        self.assertTrue(transfer.name.startswith('TRF/'))
        self.assertNotEqual(transfer.name, '/')

    def test_current_values_mirror_employee(self):
        transfer = self._new_transfer()
        self.assertEqual(transfer.current_department_id, self.dept_sales)
        self.assertEqual(transfer.current_company_id, self.company_a)
        self.assertEqual(transfer.current_parent_id, self.employee.parent_id)

    def test_copy_resets_reference_and_state(self):
        transfer = self._new_transfer()
        transfer.action_send_for_approval()
        copied = transfer.copy()
        self.assertNotEqual(copied.name, transfer.name)
        self.assertEqual(copied.state, 'draft')

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    def test_constraint_requires_at_least_one_target(self):
        with self.assertRaises(ValidationError):
            self.Transfer.create({
                'employee_id': self.employee.id,
                'effective_date': self.yesterday,
            })

    def test_constraint_target_must_differ_from_current(self):
        with self.assertRaises(ValidationError):
            self._new_transfer(new_department_id=self.dept_sales.id)

    def test_constraint_effective_date_after_latest_version(self):
        latest = max(self.employee.version_ids.mapped('date_version'))
        with self.assertRaises(ValidationError) as err:
            self._new_transfer(effective_date=latest)
        self.assertIn(str(latest), str(err.exception))

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def test_workflow_draft_to_approved(self):
        transfer = self._new_transfer()
        self.assertEqual(transfer.state, 'draft')
        transfer.action_send_for_approval()
        self.assertEqual(transfer.state, 'to_approve')
        transfer.action_approve()
        self.assertEqual(transfer.state, 'approved')

    def test_send_for_approval_rejected_outside_draft(self):
        transfer = self._new_transfer()
        transfer.action_send_for_approval()
        with self.assertRaises(UserError):
            transfer.action_send_for_approval()

    def test_approve_rejected_outside_to_approve(self):
        transfer = self._new_transfer()
        with self.assertRaises(UserError):
            transfer.action_approve()

    def test_cancel_from_approved(self):
        transfer = self._new_transfer()
        transfer.action_send_for_approval()
        transfer.action_approve()
        transfer.action_cancel()
        self.assertEqual(transfer.state, 'cancelled')

    def test_cancel_rejected_when_applied(self):
        transfer = self._new_transfer()
        transfer.action_send_for_approval()
        transfer.action_approve()
        transfer.action_apply()
        with self.assertRaises(UserError):
            transfer.action_cancel()

    # ------------------------------------------------------------------
    # Approval gate (criterion 6 — method called directly)
    # ------------------------------------------------------------------
    def test_approve_refuses_hr_officer_calling_method_directly(self):
        transfer = self._new_transfer()
        transfer.action_send_for_approval()
        with self.assertRaises(AccessError):
            transfer.with_user(self.hr_officer).action_approve()
        self.assertEqual(transfer.state, 'to_approve')

    def test_approve_allowed_for_hr_manager(self):
        transfer = self._new_transfer()
        transfer.action_send_for_approval()
        transfer.with_user(self.hr_manager).action_approve()
        self.assertEqual(transfer.state, 'approved')

    def test_approve_refuses_cross_company_without_access(self):
        transfer = self._new_transfer(new_company_id=self.company_b.id)
        transfer.action_send_for_approval()
        with self.assertRaises(AccessError) as err:
            transfer.with_user(self.hr_manager).action_approve()
        self.assertIn(self.company_b.name, str(err.exception))

    # ------------------------------------------------------------------
    # Apply
    # ------------------------------------------------------------------
    def test_apply_creates_version_without_touching_employee_identity(self):
        employee_count_before = self.env['hr.employee'].search_count([])
        version_count_before = len(self.employee.version_ids)
        transfer = self._new_transfer()
        transfer.action_send_for_approval()
        transfer.action_approve()
        transfer.action_apply()

        self.employee.invalidate_recordset()
        self.assertEqual(transfer.state, 'applied')
        self.assertTrue(transfer.version_id)
        self.assertTrue(transfer.applied_date)
        self.assertEqual(len(self.employee.version_ids), version_count_before + 1)
        self.assertEqual(
            self.env['hr.employee'].search_count([]), employee_count_before)
        self.assertEqual(transfer.version_id.employee_id, self.employee)
        self.assertEqual(transfer.version_id.date_version, self.yesterday)
        self.assertEqual(transfer.version_id.department_id, self.dept_support)
        self.assertEqual(self.employee.department_id, self.dept_support)
        self.assertTrue(self.employee.active)

        # The "from" side of the before/after pair must keep showing the
        # pre-transfer department, not the one the employee just moved to.
        self.assertEqual(transfer.current_department_id, self.dept_sales)
        self.assertEqual(transfer.new_department_id, self.dept_support)

        # A later, unrelated change to the employee must not overwrite the
        # frozen snapshot on the already-applied transfer.
        other_department = self.env['hr.department'].create({
            'name': 'Transfer Test Other',
            'company_id': self.company_a.id,
        })
        self.employee.version_ids.sorted('date_version')[-1].department_id = other_department.id
        transfer.invalidate_recordset(['current_department_id'])
        self.assertEqual(transfer.current_department_id, self.dept_sales)
        self.assertEqual(transfer.new_department_id, self.dept_support)

    def test_apply_copies_untouched_values_from_previous_version(self):
        self.employee.version_ids.write({'job_id': self.job_agent.id})
        transfer = self._new_transfer()
        transfer.action_send_for_approval()
        transfer.action_approve()
        transfer.action_apply()
        self.assertEqual(transfer.version_id.job_id, self.job_agent)

    def test_apply_writes_manager_on_employee(self):
        transfer = self._new_transfer(
            new_department_id=False, new_parent_id=self.manager_employee.id)
        transfer.action_send_for_approval()
        transfer.action_approve()
        transfer.action_apply()
        self.employee.invalidate_recordset()
        self.assertEqual(self.employee.parent_id, self.manager_employee)

    def test_apply_refuses_future_effective_date(self):
        transfer = self._new_transfer(effective_date=self.tomorrow)
        transfer.action_send_for_approval()
        transfer.action_approve()
        with self.assertRaises(UserError):
            transfer.action_apply()
        self.assertEqual(transfer.state, 'approved')

    def test_apply_refuses_when_not_approved(self):
        transfer = self._new_transfer()
        with self.assertRaises(UserError):
            transfer.action_apply()

    def test_applied_is_terminal_on_write(self):
        transfer = self._new_transfer()
        transfer.action_send_for_approval()
        transfer.action_approve()
        transfer.action_apply()
        for vals in (
            {'state': 'draft'},
            {'effective_date': self.tomorrow},
            {'employee_id': self.manager_employee.id},
            {'new_department_id': self.dept_sales.id},
        ):
            with self.assertRaises(UserError):
                transfer.write(vals)
        self.assertEqual(transfer.state, 'applied')

    def test_applied_still_allows_unrelated_write(self):
        transfer = self._new_transfer()
        transfer.action_send_for_approval()
        transfer.action_approve()
        transfer.action_apply()
        transfer.write({'reason': 'Documented after the fact'})
        self.assertEqual(transfer.reason, 'Documented after the fact')

    # ------------------------------------------------------------------
    # Cron
    # ------------------------------------------------------------------
    def test_cron_applies_due_transfer_only(self):
        due = self._new_transfer()
        due.action_send_for_approval()
        due.action_approve()

        future = self._new_transfer(
            employee_id=self.manager_employee.id,
            effective_date=self.tomorrow,
            new_department_id=self.dept_sales.id,
        )
        future.action_send_for_approval()
        future.action_approve()

        self.Transfer._cron_apply_due_transfers()
        self.assertEqual(due.state, 'applied')
        self.assertEqual(future.state, 'approved')

    # ------------------------------------------------------------------
    # Refuse wizard
    # ------------------------------------------------------------------
    def test_refuse_wizard_sets_reason_and_leaves_employee_untouched(self):
        transfer = self._new_transfer()
        transfer.action_send_for_approval()
        action = transfer.action_refuse()
        self.assertEqual(action['res_model'], 'odomate.hr.transfer.refuse')

        wizard = self.env['odomate.hr.transfer.refuse'].with_context(
            action['context']).create({'refuse_reason': 'Headcount frozen'})
        self.assertEqual(wizard.transfer_id, transfer)
        wizard.action_confirm_refuse()

        self.employee.invalidate_recordset()
        self.assertEqual(transfer.state, 'refused')
        self.assertEqual(transfer.refuse_reason, 'Headcount frozen')
        self.assertEqual(self.employee.department_id, self.dept_sales)
        self.assertFalse(transfer.version_id)

    def test_refuse_rejected_when_approved(self):
        transfer = self._new_transfer()
        transfer.action_send_for_approval()
        transfer.action_approve()
        with self.assertRaises(UserError):
            transfer.action_refuse()

    # ------------------------------------------------------------------
    # Activities
    # ------------------------------------------------------------------
    def test_send_for_approval_schedules_activity_per_hr_manager(self):
        transfer = self._new_transfer()
        transfer.action_send_for_approval()
        self.assertTrue(transfer.activity_ids)
        self.assertIn(self.hr_manager, transfer.activity_ids.mapped('user_id'))
        self.assertNotIn(self.hr_officer, transfer.activity_ids.mapped('user_id'))
        self.assertEqual(
            len(transfer.activity_ids),
            len(set(transfer.activity_ids.mapped('user_id').ids)),
        )

    def test_approval_activity_closed_on_approve(self):
        transfer = self._new_transfer()
        transfer.action_send_for_approval()
        transfer.action_approve()
        self.assertFalse(transfer.activity_ids)

    def test_approval_activity_closed_on_cancel(self):
        transfer = self._new_transfer()
        transfer.action_send_for_approval()
        transfer.action_cancel()
        self.assertFalse(transfer.activity_ids)

    # ------------------------------------------------------------------
    # Access (criterion 17)
    # ------------------------------------------------------------------
    def test_plain_internal_user_has_no_access(self):
        transfer = self._new_transfer()
        with self.assertRaises(AccessError):
            self.Transfer.with_user(self.plain_user).search([])
        with self.assertRaises(AccessError):
            transfer.with_user(self.plain_user).read(['name'])

    def test_hr_officer_can_create_and_send(self):
        transfer = self.Transfer.with_user(self.hr_officer).create({
            'employee_id': self.employee.id,
            'effective_date': self.yesterday,
            'new_job_id': self.job_agent.id,
        })
        transfer.action_send_for_approval()
        self.assertEqual(transfer.state, 'to_approve')

    def test_hr_officer_cannot_unlink(self):
        transfer = self._new_transfer()
        with self.assertRaises(AccessError):
            transfer.with_user(self.hr_officer).unlink()

    def test_record_rule_hides_other_company_transfer(self):
        employee_b = self._make_employee(
            'Transfer Test Employee B', company=self.company_b)
        dept_b = self.env['hr.department'].create({
            'name': 'Transfer Test Dept B',
            'company_id': self.company_b.id,
        })
        transfer_b = self.Transfer.create({
            'employee_id': employee_b.id,
            'effective_date': self.yesterday,
            'new_department_id': dept_b.id,
        })
        visible = self.Transfer.with_user(self.hr_manager).search([])
        self.assertNotIn(transfer_b, visible)

    # ------------------------------------------------------------------
    # Employee smart button
    # ------------------------------------------------------------------
    def test_employee_transfer_count_and_action(self):
        self.employee.invalidate_recordset()
        before = self.employee.odomate_transfer_count
        self._new_transfer()
        self.employee.invalidate_recordset()
        self.assertEqual(self.employee.odomate_transfer_count, before + 1)
        action = self.employee.action_open_odomate_transfers()
        self.assertEqual(action['res_model'], 'odomate.hr.transfer')
        self.assertIn(('employee_id', '=', self.employee.id), action['domain'])
