from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user
from odoo.tools import mute_logger
from odoo.tools.safe_eval import safe_eval


@tagged("post_install", "-at_install")
class TestSalaryAdvanceCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write({
            "advance_max_percent": 50.0,
            "advance_max_amount": 0.0,
            "advance_allow_multiple": False,
            "advance_journal_id": False,
        })
        cls.today = fields.Date.context_today(cls.env["odomate.hr.salary.advance"])
        cls.employee = cls._make_employee("Olena Kravets", 3000.0)
        cls.other_employee = cls._make_employee("Petro Shevchuk", 2000.0)
        cls.Advance = cls.env["odomate.hr.salary.advance"]

    @classmethod
    def _make_employee(cls, name, wage):
        employee = cls.env["hr.employee"].with_company(cls.company).create({
            "name": name,
        })
        version = employee.version_id
        version.write({
            "date_version": cls.today - relativedelta(years=1),
            "contract_date_start": cls.today - relativedelta(years=1),
            "wage": wage,
        })
        return employee

    def _new_advance(self, employee=None, amount=1000.0, date=None, **kwargs):
        vals = {
            "employee_id": (employee or self.employee).id,
            "amount": amount,
            "date": date or self.today,
            "reason": "Demo reason for the advance request.",
        }
        vals.update(kwargs)
        return self.Advance.create(vals)


@tagged("post_install", "-at_install")
class TestSalaryAdvanceModel(TestSalaryAdvanceCommon):

    def test_demo_data_loaded(self):
        self.assertTrue(
            self.Advance.search_count([]) > 0,
            "The demo advances should be loaded in a demo database.",
        )

    def test_name_search_returns_a_list(self):
        advance = self._new_advance()
        self.assertIsInstance(self.Advance.name_search("", limit=5), list)
        found = self.Advance.name_search(advance.name, limit=5)
        self.assertIn(advance.id, [record_id for record_id, __ in found])

    def test_unlink_record(self):
        advance = self._new_advance()
        advance_id = advance.id
        advance.unlink()
        self.assertFalse(self.Advance.browse(advance_id).exists())

    def test_reference_is_sequence_generated(self):
        advance = self._new_advance()
        self.assertTrue(advance.name.startswith("ADV/"))
        self.assertNotEqual(advance.name, "/")

    def test_reference_is_unique_across_records(self):
        first = self._new_advance()
        second = self._new_advance(employee=self.other_employee, amount=500.0)
        self.assertNotEqual(first.name, second.name)

    def test_department_is_denormalised_from_employee(self):
        department = self.env["hr.department"].create({"name": "Finance"})
        self.employee.version_id.department_id = department
        advance = self._new_advance()
        self.assertEqual(advance.department_id, department)

    def test_outstanding_amount_is_amount_minus_recovered(self):
        advance = self._new_advance(amount=800.0)
        self.assertEqual(advance.outstanding_amount, 800.0)
        advance.write({"state": "paid", "recovered_amount": 300.0})
        self.assertEqual(advance.outstanding_amount, 500.0)

    def test_outstanding_amount_is_zero_when_refused(self):
        advance = self._new_advance(amount=4500.0)
        advance.write({"state": "refused"})
        self.assertEqual(advance.outstanding_amount, 0.0)

    def test_outstanding_amount_is_zero_when_cancelled(self):
        advance = self._new_advance(amount=800.0)
        advance.action_cancel()
        self.assertEqual(advance.outstanding_amount, 0.0)

    def test_outstanding_amount_unchanged_for_approved_advance(self):
        advance = self._new_advance(amount=800.0)
        advance.write({"state": "approved"})
        self.assertEqual(advance.outstanding_amount, 800.0)

    def test_refusing_advance_recomputes_stored_outstanding_to_zero(self):
        advance = self._new_advance(amount=800.0)
        advance.action_submit()
        self.assertEqual(advance.outstanding_amount, 800.0)
        wizard = self.env["odomate.hr.salary.advance.refuse"].create({
            "advance_id": advance.id,
            "refusal_reason": "Not needed.",
        })
        wizard.action_confirm()
        self.assertEqual(advance.state, "refused")
        self.assertEqual(advance.outstanding_amount, 0.0)

    def test_already_outstanding_amount_ignores_refused_advances(self):
        paid = self._new_advance(amount=900.0)
        paid.write({
            "state": "paid",
            "payment_date": self.today,
            "recovered_amount": 350.0,
        })
        refused = self._new_advance(amount=4500.0)
        refused.write({"state": "refused"})
        fresh = self._new_advance(amount=100.0)
        self.assertEqual(fresh.already_outstanding_amount, 550.0)

    def test_monthly_wage_reads_version_in_force_on_request_date(self):
        advance = self._new_advance()
        self.assertEqual(advance.monthly_wage, 3000.0)

    def test_monthly_wage_is_zero_before_any_contract(self):
        advance = self._new_advance(date=self.today - relativedelta(years=3))
        self.assertEqual(advance.monthly_wage, 0.0)

    def test_max_allowed_follows_percentage_policy(self):
        advance = self._new_advance()
        self.assertEqual(advance.max_allowed_amount, 1500.0)
        self.assertEqual(advance.available_amount, 1500.0)

    def test_max_allowed_is_capped_by_absolute_ceiling(self):
        self.company.advance_max_amount = 900.0
        advance = self._new_advance()
        self.assertEqual(advance.max_allowed_amount, 900.0)

    def test_available_amount_nets_off_other_outstanding_advances(self):
        paid = self._new_advance(amount=1000.0)
        paid.write({"state": "paid", "payment_date": self.today})
        fresh = self._new_advance(amount=100.0)
        self.assertEqual(fresh.already_outstanding_amount, 1000.0)
        self.assertEqual(fresh.available_amount, 500.0)

    @mute_logger("odoo.sql_db")
    def test_amount_must_be_positive(self):
        with self.assertRaises(Exception), self.env.cr.savepoint():
            self._new_advance(amount=0.0)
            self.env.flush_all()


@tagged("post_install", "-at_install")
class TestSalaryAdvanceWorkflow(TestSalaryAdvanceCommon):

    def test_submit_then_approve_moves_through_states(self):
        advance = self._new_advance(amount=1000.0)
        self.assertEqual(advance.state, "draft")
        advance.action_submit()
        self.assertEqual(advance.state, "submitted")
        advance.action_approve()
        self.assertEqual(advance.state, "approved")

    def test_submit_refuses_amount_above_available(self):
        advance = self._new_advance(amount=2500.0)
        with self.assertRaises(ValidationError):
            advance.action_submit()

    def test_submit_refuses_second_advance_when_policy_forbids_it(self):
        first = self._new_advance(amount=500.0)
        first.write({"state": "paid", "payment_date": self.today})
        second = self._new_advance(amount=200.0)
        with self.assertRaises(ValidationError):
            second.action_submit()

    def test_submit_allows_second_advance_when_policy_permits_it(self):
        self.company.advance_allow_multiple = True
        first = self._new_advance(amount=500.0)
        first.write({"state": "paid", "payment_date": self.today})
        second = self._new_advance(amount=200.0)
        second.action_submit()
        self.assertEqual(second.state, "submitted")

    def test_submit_refuses_when_no_contract_covers_the_request_date(self):
        advance = self._new_advance(
            amount=100.0, date=self.today - relativedelta(years=3)
        )
        with self.assertRaises(ValidationError):
            advance.action_submit()

    def test_eligibility_is_enforced_on_a_bare_write_not_only_the_button(self):
        advance = self._new_advance(amount=2500.0)
        with self.assertRaises(ValidationError):
            advance.write({"state": "submitted"})

    def test_refuse_wizard_records_the_reason_permanently(self):
        advance = self._new_advance(amount=800.0)
        advance.action_submit()
        wizard = self.env["odomate.hr.salary.advance.refuse"].create({
            "advance_id": advance.id,
            "refusal_reason": "Budget frozen until the next quarter.",
        })
        wizard.action_confirm()
        self.assertEqual(advance.state, "refused")
        self.assertEqual(advance.refusal_reason, "Budget frozen until the next quarter.")

    def test_refused_and_cancelled_are_dead_ends(self):
        advance = self._new_advance(amount=800.0)
        advance.action_cancel()
        self.assertEqual(advance.state, "cancelled")
        self.assertFalse(hasattr(advance, "action_draft"))
        self.assertFalse(hasattr(advance, "action_set_to_draft"))

    def test_paid_advance_cannot_be_cancelled(self):
        advance = self._new_advance(amount=800.0)
        advance.write({"state": "paid", "payment_date": self.today})
        with self.assertRaises(UserError):
            advance.action_cancel()

    def test_paid_advance_amount_is_locked(self):
        advance = self._new_advance(amount=800.0)
        advance.write({"state": "paid", "payment_date": self.today})
        with self.assertRaises(UserError):
            advance.write({"amount": 900.0})

    def test_paid_advance_cannot_be_deleted(self):
        advance = self._new_advance(amount=800.0)
        advance.write({"state": "paid", "payment_date": self.today})
        with self.assertRaises(UserError):
            advance.unlink()

    def test_pay_refuses_when_no_company_journal_is_configured(self):
        advance = self._new_advance(amount=800.0)
        advance.action_submit()
        advance.action_approve()
        journal = self.env["account.journal"].search(
            [("type", "in", ("bank", "cash")), ("company_id", "=", self.company.id)],
            limit=1,
        )
        with self.assertRaises(UserError):
            advance._process_payment(self.today, journal)
        self.assertEqual(advance.state, "approved")
        self.assertFalse(advance.payment_id)

    def test_pay_refuses_when_the_employee_has_no_work_contact(self):
        journal = self.env["account.journal"].search(
            [("type", "in", ("bank", "cash")), ("company_id", "=", self.company.id)],
            limit=1,
        )
        if not journal:
            self.skipTest("No bank or cash journal available in this database.")
        self.company.advance_journal_id = journal
        self.employee.work_contact_id = False
        advance = self._new_advance(amount=800.0)
        advance.action_submit()
        advance.action_approve()
        with self.assertRaises(UserError):
            advance._process_payment(self.today, journal)
        self.assertEqual(advance.state, "approved")
        self.assertFalse(advance.payment_id)


@tagged("post_install", "-at_install")
class TestSalaryAdvanceRecovery(TestSalaryAdvanceCommon):

    def _paid_advance(self, amount=900.0):
        advance = self._new_advance(amount=amount)
        advance.write({
            "state": "paid",
            "payment_date": self.today - relativedelta(days=5),
        })
        return advance

    def test_partial_recovery_keeps_the_advance_open(self):
        advance = self._paid_advance()
        advance._register_recovery(400.0)
        self.assertEqual(advance.recovered_amount, 400.0)
        self.assertEqual(advance.outstanding_amount, 500.0)
        self.assertEqual(advance.state, "paid")

    def test_full_recovery_closes_the_advance(self):
        advance = self._paid_advance()
        advance._register_recovery(900.0)
        self.assertEqual(advance.outstanding_amount, 0.0)
        self.assertEqual(advance.state, "closed")

    def test_recovery_never_exceeds_the_advanced_amount(self):
        advance = self._paid_advance()
        advance._register_recovery(5000.0)
        self.assertEqual(advance.recovered_amount, 900.0)
        advance._register_recovery(100.0)
        self.assertEqual(advance.recovered_amount, 900.0)

    def test_get_inputs_emits_one_deduction_per_paid_advance(self):
        advance = self._paid_advance(600.0)
        date_from = self.today.replace(day=1)
        date_to = date_from + relativedelta(months=1, days=-1)
        payslip = self.env["hr.payslip"].create({
            "employee_id": self.employee.id,
            "date_from": date_from,
            "date_to": date_to,
        })
        inputs = payslip.get_inputs(self.employee.version_id, date_from, date_to)
        lines = [line for line in inputs if line.get("code") == "ADV_DEDUCT"]
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["amount"], 600.0)
        self.assertEqual(lines[0]["advance_id"], advance.id)

    def test_get_inputs_ignores_advances_paid_after_the_period(self):
        advance = self._paid_advance(600.0)
        advance.write({"payment_date": self.today + relativedelta(months=6)})
        date_from = self.today.replace(day=1)
        date_to = date_from + relativedelta(months=1, days=-1)
        payslip = self.env["hr.payslip"].create({
            "employee_id": self.employee.id,
            "date_from": date_from,
            "date_to": date_to,
        })
        inputs = payslip.get_inputs(self.employee.version_id, date_from, date_to)
        self.assertFalse([ln for ln in inputs if ln.get("code") == "ADV_DEDUCT"])

    def test_get_inputs_ignores_approved_but_unpaid_advances(self):
        advance = self._new_advance(amount=600.0)
        advance.action_submit()
        advance.action_approve()
        date_from = self.today.replace(day=1)
        date_to = date_from + relativedelta(months=1, days=-1)
        payslip = self.env["hr.payslip"].create({
            "employee_id": self.employee.id,
            "date_from": date_from,
            "date_to": date_to,
        })
        inputs = payslip.get_inputs(self.employee.version_id, date_from, date_to)
        self.assertFalse([ln for ln in inputs if ln.get("code") == "ADV_DEDUCT"])

    def test_compute_sheet_populates_deduction_without_manual_get_inputs(self):
        advance = self._paid_advance(600.0)
        date_from = self.today.replace(day=1)
        date_to = date_from + relativedelta(months=1, days=-1)
        payslip = self.env["hr.payslip"].create({
            "employee_id": self.employee.id,
            "contract_id": self.employee.version_id.id,
            "date_from": date_from,
            "date_to": date_to,
        })
        payslip.compute_sheet()
        lines = payslip.input_line_ids.filtered(lambda l: l.code == "ADV_DEDUCT")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines.amount, 600.0)
        self.assertEqual(lines.advance_id, advance)

    def test_compute_sheet_does_not_duplicate_lines_on_recompute(self):
        self._paid_advance(600.0)
        date_from = self.today.replace(day=1)
        date_to = date_from + relativedelta(months=1, days=-1)
        payslip = self.env["hr.payslip"].create({
            "employee_id": self.employee.id,
            "contract_id": self.employee.version_id.id,
            "date_from": date_from,
            "date_to": date_to,
        })
        other_line = self.env["hr.payslip.input"].create({
            "payslip_id": payslip.id,
            "contract_id": self.employee.version_id.id,
            "name": "Other Input",
            "code": "OTHER",
            "amount": 42.0,
        })
        payslip.compute_sheet()
        payslip.compute_sheet()
        lines = payslip.input_line_ids.filtered(lambda l: l.code == "ADV_DEDUCT")
        self.assertEqual(len(lines), 1)
        self.assertIn(other_line, payslip.input_line_ids)

    def test_compute_sheet_populates_deduction_for_batch_created_payslip(self):
        """A batch run (hr.payslip.run) never sets contract_id itself - only
        the form's onchange does. The deduction must still reach such a
        payslip by resolving the contract through
        hr.payslip._get_employee_contracts(), not by reading contract_id."""
        advance = self._paid_advance(600.0)
        date_from = self.today.replace(day=1)
        date_to = date_from + relativedelta(months=1, days=-1)
        payslip = self.env["hr.payslip"].create({
            "employee_id": self.employee.id,
            "date_from": date_from,
            "date_to": date_to,
        })
        self.assertFalse(payslip.contract_id)
        payslip.compute_sheet()
        lines = payslip.input_line_ids.filtered(lambda l: l.code == "ADV_DEDUCT")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines.amount, 600.0)
        self.assertEqual(lines.advance_id, advance)

    def test_deduction_rule_condition_and_amount_use_input_line_ids(self):
        self._paid_advance(600.0)
        date_from = self.today.replace(day=1)
        date_to = date_from + relativedelta(months=1, days=-1)
        payslip = self.env["hr.payslip"].create({
            "employee_id": self.employee.id,
            "date_from": date_from,
            "date_to": date_to,
        })
        inputs = payslip.get_inputs(self.employee.version_id, date_from, date_to)
        line_vals = next(v for v in inputs if v.get("code") == "ADV_DEDUCT")
        self.env["hr.payslip.input"].create({**line_vals, "payslip_id": payslip.id})

        rule = self.env.ref(
            "odomate_hr_salary_advance.hr_salary_rule_advance_deduction"
        )
        condition_localdict = {"payslip": payslip, "result": None}
        safe_eval(rule.condition_python, condition_localdict, mode="exec")
        self.assertTrue(condition_localdict["result"])

        amount_localdict = {"payslip": payslip, "result": None}
        safe_eval(rule.amount_python_compute, amount_localdict, mode="exec")
        self.assertEqual(amount_localdict["result"], -600.0)

    def test_deduction_rule_condition_is_false_without_an_input_line(self):
        date_from = self.today.replace(day=1)
        date_to = date_from + relativedelta(months=1, days=-1)
        payslip = self.env["hr.payslip"].create({
            "employee_id": self.employee.id,
            "date_from": date_from,
            "date_to": date_to,
        })
        rule = self.env.ref(
            "odomate_hr_salary_advance.hr_salary_rule_advance_deduction"
        )
        condition_localdict = {"payslip": payslip, "result": None}
        safe_eval(rule.condition_python, condition_localdict, mode="exec")
        self.assertFalse(condition_localdict["result"])


@tagged("post_install", "-at_install")
class TestSalaryAdvanceEmployee(TestSalaryAdvanceCommon):

    def test_advance_count_only_counts_outstanding_advances(self):
        self.assertEqual(self.employee.advance_count, 0)
        paid = self._new_advance(amount=500.0)
        paid.write({"state": "paid", "payment_date": self.today})
        self.employee.invalidate_recordset(["advance_count"])
        self.assertEqual(self.employee.advance_count, 1)
        paid.write({"state": "closed", "recovered_amount": 500.0})
        self.employee.invalidate_recordset(["advance_count"])
        self.assertEqual(self.employee.advance_count, 0)

    def test_smart_button_action_targets_the_employee(self):
        action = self.employee.action_view_salary_advances()
        self.assertEqual(action["res_model"], "odomate.hr.salary.advance")
        self.assertIn(("employee_id", "=", self.employee.id), action["domain"])


@tagged("post_install", "-at_install")
class TestSalaryAdvanceSecurity(TestSalaryAdvanceCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plain_user = new_test_user(
            cls.env, login="advance_plain_user", groups="base.group_user"
        )
        cls.hr_user = new_test_user(
            cls.env, login="advance_hr_user", groups="base.group_user,hr.group_hr_user"
        )

    def test_plain_employee_cannot_drive_the_workflow(self):
        advance = self._new_advance(amount=500.0)
        with self.assertRaises(AccessError):
            advance.with_user(self.plain_user).action_submit()

    def test_plain_employee_cannot_create_an_advance(self):
        with self.assertRaises(AccessError):
            self.Advance.with_user(self.plain_user).create({
                "employee_id": self.employee.id,
                "amount": 100.0,
                "date": self.today,
                "reason": "Self service is not allowed.",
            })

    def test_plain_employee_only_reads_their_own_advances(self):
        self.employee.resource_id.user_id = self.plain_user
        self.employee.invalidate_recordset(["user_id"])
        mine = self._new_advance(amount=500.0)
        theirs = self._new_advance(employee=self.other_employee, amount=400.0)
        visible = self.Advance.with_user(self.plain_user).search([])
        self.assertIn(mine, visible)
        self.assertNotIn(theirs, visible)

    def test_hr_officer_sees_every_advance(self):
        mine = self._new_advance(amount=500.0)
        theirs = self._new_advance(employee=self.other_employee, amount=400.0)
        visible = self.Advance.with_user(self.hr_user).search([])
        self.assertIn(mine, visible)
        self.assertIn(theirs, visible)

    def test_hr_officer_can_drive_the_workflow(self):
        advance = self._new_advance(amount=500.0)
        advance.with_user(self.hr_user).action_submit()
        self.assertEqual(advance.state, "submitted")


@tagged("post_install", "-at_install")
class TestSalaryAdvanceWizards(TestSalaryAdvanceCommon):

    def test_refuse_wizard_crud(self):
        advance = self._new_advance(amount=500.0)
        wizard = self.env["odomate.hr.salary.advance.refuse"].create({
            "advance_id": advance.id,
            "refusal_reason": "Not this quarter.",
        })
        self.assertTrue(wizard.exists())
        wizard.write({"refusal_reason": "Budget frozen."})
        self.assertEqual(wizard.refusal_reason, "Budget frozen.")
        wizard_id = wizard.id
        wizard.unlink()
        self.assertFalse(
            self.env["odomate.hr.salary.advance.refuse"].browse(wizard_id).exists()
        )

    def test_pay_wizard_defaults_the_company_journal(self):
        journal = self.env["account.journal"].search(
            [("type", "in", ("bank", "cash")), ("company_id", "=", self.company.id)],
            limit=1,
        )
        if not journal:
            self.skipTest("No bank or cash journal available in this database.")
        self.company.advance_journal_id = journal
        advance = self._new_advance(amount=500.0)
        wizard = self.env["odomate.hr.salary.advance.pay"].create({
            "advance_id": advance.id,
        })
        self.assertEqual(wizard.journal_id, journal)
        self.assertEqual(wizard.company_id, self.company)


@tagged("post_install", "-at_install")
class TestSalaryAdvancePayrollRule(TransactionCase):

    def test_deduction_rule_is_shipped_with_a_resolved_category(self):
        rule = self.env.ref(
            "odomate_hr_salary_advance.hr_salary_rule_advance_deduction"
        )
        self.assertEqual(rule.code, "ADV_DEDUCT")
        self.assertTrue(rule.category_id)
        self.assertEqual(rule.category_id.code, "DED")

    def test_deduction_rule_is_not_attached_to_any_structure(self):
        rule = self.env.ref(
            "odomate_hr_salary_advance.hr_salary_rule_advance_deduction"
        )
        structures = self.env["hr.payroll.structure"].search(
            [("rule_ids", "in", rule.ids)]
        )
        self.assertFalse(
            structures,
            "The ADV_DEDUCT rule must be shipped unattached; wiring it into a "
            "salary structure is the customer's own setup step.",
        )

    def test_deduction_rule_has_its_matching_input(self):
        rule = self.env.ref(
            "odomate_hr_salary_advance.hr_salary_rule_advance_deduction"
        )
        self.assertIn("ADV_DEDUCT", rule.input_ids.mapped("code"))


@tagged("post_install", "-at_install")
class TestSalaryAdvanceDemoData(TransactionCase):

    DEMO_XMLIDS = [
        "odomate_hr_salary_advance.demo_advance_paid",
        "odomate_hr_salary_advance.demo_advance_partially_recovered",
        "odomate_hr_salary_advance.demo_advance_closed",
        "odomate_hr_salary_advance.demo_advance_refused",
    ]

    def test_demo_advances_have_a_contract_in_force_on_their_date(self):
        for xmlid in self.DEMO_XMLIDS:
            advance = self.env.ref(xmlid, raise_if_not_found=False)
            if not advance:
                continue
            self.assertTrue(
                advance._get_version_at_date(),
                "%s has no hr.version in force on its request date." % xmlid,
            )
            self.assertGreater(
                advance.monthly_wage,
                0.0,
                "%s should read a nonzero monthly wage from its contract." % xmlid,
            )
