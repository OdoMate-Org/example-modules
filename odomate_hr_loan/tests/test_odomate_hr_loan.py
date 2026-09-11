from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestOdomateHrLoanCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write({"loan_allow_multiple": False, "loan_max_amount": 0.0})
        cls.employee = cls.env["hr.employee"].create({"name": "Loan Borrower"})
        cls.other_employee = cls.env["hr.employee"].create({"name": "Second Borrower"})
        cls.contract = cls.employee.version_id
        cls.month_start = fields.Date.today().replace(day=1)
        cls.Loan = cls.env["odomate.hr.loan"]

    def _new_loan(self, employee=None, **overrides):
        vals = {
            "employee_id": (employee or self.employee).id,
            "amount": 1200.0,
            "purpose": "Test loan",
            "instalment_count": 4,
            "first_instalment_date": self.month_start,
            "interest_percentage": 0.0,
        }
        vals.update(overrides)
        return self.Loan.create(vals)

    def _approved_loan(self, employee=None, **overrides):
        loan = self._new_loan(employee=employee, **overrides)
        loan.action_build_schedule()
        loan.action_submit()
        loan.action_approve()
        return loan


class TestLoanSchedule(TestOdomateHrLoanCommon):
    def test_sequence_reference_assigned_on_create(self):
        loan = self._new_loan()
        self.assertTrue(loan.name.startswith("LOAN/"))
        self.assertNotEqual(loan.name, "/")

    def test_build_schedule_splits_principal_with_remainder_on_last_row(self):
        loan = self._new_loan(amount=1000.0, instalment_count=3)
        loan.action_build_schedule()
        instalments = loan.instalment_ids.sorted("due_date")
        self.assertEqual(len(instalments), 3)
        self.assertEqual(
            instalments.mapped("principal_amount"), [333.33, 333.33, 333.34]
        )
        self.assertEqual(sum(instalments.mapped("principal_amount")), 1000.0)

    def test_build_schedule_spreads_flat_interest(self):
        loan = self._new_loan(amount=1000.0, instalment_count=4,
                              interest_percentage=10.0)
        loan.action_build_schedule()
        instalments = loan.instalment_ids
        self.assertEqual(sum(instalments.mapped("interest_amount")), 100.0)
        self.assertEqual(sum(instalments.mapped("total_amount")), 1100.0)
        self.assertEqual(loan.total_amount, 1100.0)

    def test_due_dates_advance_one_month_per_row(self):
        loan = self._new_loan(instalment_count=3)
        loan.action_build_schedule()
        due_dates = loan.instalment_ids.sorted("due_date").mapped("due_date")
        self.assertEqual(due_dates[1], self.month_start + relativedelta(months=1))
        self.assertEqual(due_dates[2], self.month_start + relativedelta(months=2))

    def test_rebuilding_replaces_the_previous_schedule(self):
        loan = self._new_loan(instalment_count=4)
        loan.action_build_schedule()
        loan.action_build_schedule()
        self.assertEqual(len(loan.instalment_ids), 4)

    def test_build_schedule_rejected_outside_draft(self):
        loan = self._approved_loan()
        with self.assertRaises(UserError):
            loan.action_build_schedule()


class TestLoanComputedFields(TestOdomateHrLoanCommon):
    def test_totals_split_recovered_cancelled_and_outstanding(self):
        loan = self._approved_loan(amount=400.0, instalment_count=4)
        instalments = loan.instalment_ids.sorted("due_date")
        instalments[0].state = "recovered"
        instalments[1].state = "cancelled"
        self.assertEqual(loan.total_amount, 400.0)
        self.assertEqual(loan.recovered_amount, 100.0)
        self.assertEqual(loan.outstanding_amount, 200.0)
        self.assertEqual(loan.instalments_remaining, 2)

    def test_cancelled_instalments_excluded_from_outstanding(self):
        loan = self._approved_loan(amount=400.0, instalment_count=4)
        loan.instalment_ids.write({"state": "cancelled"})
        self.assertEqual(loan.outstanding_amount, 0.0)
        self.assertEqual(loan.total_amount, 400.0)

    def test_has_schedule_gates_submission(self):
        loan = self._new_loan()
        self.assertFalse(loan.has_schedule)
        loan.action_build_schedule()
        self.assertTrue(loan.has_schedule)

    def test_employee_loan_count(self):
        self._new_loan()
        self._new_loan()
        self.assertEqual(self.employee.loan_count, 2)


class TestLoanWorkflow(TestOdomateHrLoanCommon):
    def test_submit_requires_a_schedule(self):
        loan = self._new_loan()
        with self.assertRaises(UserError):
            loan.action_submit()
        self.assertEqual(loan.state, "draft")

    def test_full_happy_path(self):
        loan = self._new_loan()
        loan.action_build_schedule()
        loan.action_submit()
        self.assertEqual(loan.state, "submitted")
        loan.action_approve()
        self.assertEqual(loan.state, "approved")

    def test_refuse_requires_a_reason(self):
        loan = self._new_loan()
        loan.action_build_schedule()
        loan.action_submit()
        with self.assertRaises(UserError):
            loan.action_refuse()
        loan.refusal_reason = "Outstanding advance already on file."
        loan.action_refuse()
        self.assertEqual(loan.state, "refused")

    def test_cancel_allowed_from_draft_and_submitted(self):
        draft = self._new_loan()
        draft.action_cancel()
        self.assertEqual(draft.state, "cancelled")
        approved = self._approved_loan(employee=self.other_employee)
        with self.assertRaises(UserError):
            approved.action_cancel()

    def test_editing_a_draft_clears_the_schedule(self):
        loan = self._new_loan()
        loan.action_build_schedule()
        self.assertTrue(loan.instalment_ids)
        loan.amount = 2000.0
        self.assertFalse(loan.instalment_ids)
        self.assertFalse(loan.has_schedule)

    def test_schedule_fields_frozen_after_approval(self):
        loan = self._approved_loan()
        for field_name, value in [
            ("amount", 999.0),
            ("interest_percentage", 3.0),
            ("instalment_count", 9),
            ("first_instalment_date", self.month_start),
        ]:
            with self.assertRaises(UserError):
                loan.write({field_name: value})

    def test_borrower_frozen_once_out_of_draft(self):
        loan = self._new_loan()
        loan.action_build_schedule()
        loan.action_submit()
        with self.assertRaises(UserError):
            loan.write({"employee_id": self.other_employee.id})

    def test_unlink_blocked_for_approved_and_closed(self):
        loan = self._approved_loan()
        with self.assertRaises(UserError):
            loan.unlink()

    def test_unlink_allowed_for_draft(self):
        loan = self._new_loan()
        loan.unlink()
        self.assertFalse(loan.exists())


class TestLoanPolicy(TestOdomateHrLoanCommon):
    def test_one_loan_at_a_time_blocks_second_approval(self):
        self._approved_loan()
        second = self._new_loan()
        second.action_build_schedule()
        second.action_submit()
        with self.assertRaises(UserError):
            second.action_approve()

    def test_multiple_loans_allowed_when_policy_permits(self):
        self._approved_loan()
        self.company.loan_allow_multiple = True
        second = self._approved_loan()
        self.assertEqual(second.state, "approved")

    def test_settled_loan_no_longer_blocks_a_new_approval(self):
        first = self._approved_loan()
        first.instalment_ids.write({"state": "cancelled"})
        self.assertEqual(first.outstanding_amount, 0.0)
        second = self._approved_loan()
        self.assertEqual(second.state, "approved")

    def test_maximum_amount_checked_against_principal_only(self):
        self.company.loan_max_amount = 1000.0
        loan = self._new_loan(amount=1200.0)
        loan.action_build_schedule()
        loan.action_submit()
        with self.assertRaises(UserError):
            loan.action_approve()

    def test_maximum_amount_ignores_interest(self):
        self.company.loan_max_amount = 1000.0
        loan = self._new_loan(amount=1000.0, interest_percentage=50.0)
        loan.action_build_schedule()
        loan.action_submit()
        loan.action_approve()
        self.assertEqual(loan.state, "approved")
        self.assertEqual(loan.total_amount, 1500.0)

    def test_zero_maximum_means_no_cap(self):
        self.company.loan_max_amount = 0.0
        loan = self._approved_loan(amount=999999.0)
        self.assertEqual(loan.state, "approved")


class TestLoanDeferWizard(TestOdomateHrLoanCommon):
    def _defer(self, loan, instalment, reason="Cash flow this month"):
        wizard = self.env["odomate.hr.loan.defer"].create(
            {
                "loan_id": loan.id,
                "instalment_id": instalment.id,
                "reason": reason,
            }
        )
        return wizard.action_defer()

    def test_defer_moves_target_and_every_later_instalment(self):
        loan = self._approved_loan(instalment_count=4)
        instalments = loan.instalment_ids.sorted("due_date")
        before = instalments.mapped("due_date")
        self._defer(loan, instalments[1])
        after = loan.instalment_ids.sorted("sequence").mapped("due_date")
        self.assertEqual(after[0], before[0])
        self.assertEqual(after[1], before[1] + relativedelta(months=1))
        self.assertEqual(after[2], before[2] + relativedelta(months=1))
        self.assertEqual(after[3], before[3] + relativedelta(months=1))

    def test_defer_does_not_change_any_amount(self):
        loan = self._approved_loan(instalment_count=3, interest_percentage=12.0)
        total_before = loan.total_amount
        self._defer(loan, loan.instalment_ids.sorted("due_date")[0])
        self.assertEqual(loan.total_amount, total_before)

    def test_defer_rejected_on_recovered_instalment(self):
        loan = self._approved_loan(instalment_count=3)
        target = loan.instalment_ids.sorted("due_date")[0]
        target.state = "recovered"
        with self.assertRaises(UserError):
            self._defer(loan, target)

    def test_defer_posts_a_thread_message(self):
        loan = self._approved_loan(instalment_count=3)
        before = len(loan.message_ids)
        self._defer(loan, loan.instalment_ids.sorted("due_date")[0], "Medical bills")
        self.assertGreater(len(loan.message_ids), before)

    def test_repeated_deferrals_are_allowed(self):
        loan = self._approved_loan(instalment_count=3)
        target = loan.instalment_ids.sorted("due_date")[0]
        original = target.due_date
        self._defer(loan, target)
        self._defer(loan, target)
        self._defer(loan, target)
        self.assertEqual(target.due_date, original + relativedelta(months=3))


class TestLoanSettleWizard(TestOdomateHrLoanCommon):
    def _settle(self, loan):
        wizard = self.env["odomate.hr.loan.settle"].create(
            {
                "loan_id": loan.id,
                "settlement_date": fields.Date.today(),
                "payment_reference": "BNK/TEST/0001",
            }
        )
        return wizard.action_settle()

    def test_settle_cancels_remaining_and_closes_the_loan(self):
        loan = self._approved_loan(amount=400.0, instalment_count=4)
        loan.instalment_ids.sorted("due_date")[0].state = "recovered"
        self._settle(loan)
        self.assertEqual(loan.state, "closed")
        self.assertEqual(loan.outstanding_amount, 0.0)
        self.assertEqual(loan.instalments_remaining, 0)
        self.assertEqual(loan.settlement_reference, "BNK/TEST/0001")

    def test_settle_keeps_instalments_as_history(self):
        loan = self._approved_loan(amount=400.0, instalment_count=4)
        self._settle(loan)
        self.assertEqual(len(loan.instalment_ids), 4)
        self.assertEqual(
            set(loan.instalment_ids.mapped("state")), {"cancelled"}
        )

    def test_recovered_plus_cancelled_equals_total(self):
        loan = self._approved_loan(amount=400.0, instalment_count=4)
        loan.instalment_ids.sorted("due_date")[0].state = "recovered"
        self._settle(loan)
        cancelled = sum(
            loan.instalment_ids.filtered(
                lambda i: i.state == "cancelled"
            ).mapped("total_amount")
        )
        self.assertEqual(loan.recovered_amount + cancelled, loan.total_amount)

    def test_settle_rejected_when_nothing_outstanding(self):
        loan = self._approved_loan(amount=400.0, instalment_count=4)
        self._settle(loan)
        with self.assertRaises(UserError):
            self._settle(loan)


class TestLoanPayslipRecovery(TestOdomateHrLoanCommon):
    def _payslip_for(self, loan, due_date):
        period_start = due_date.replace(day=1)
        return self.env["hr.payslip"].create(
            {
                "employee_id": loan.employee_id.id,
                "contract_id": loan.employee_id.version_id.id,
                "date_from": period_start,
                "date_to": period_start + relativedelta(months=1, days=-1),
                "name": "Test payslip",
            }
        )

    def test_get_inputs_returns_one_row_per_due_instalment(self):
        loan = self._approved_loan(amount=400.0, instalment_count=4)
        first = loan.instalment_ids.sorted("due_date")[0]
        payslip = self._payslip_for(loan, first.due_date)
        vals = payslip._get_loan_input_vals(
            payslip.contract_id, payslip.date_from, payslip.date_to
        )
        self.assertEqual(len(vals), 1)
        self.assertEqual(vals[0]["amount"], first.total_amount)
        self.assertEqual(vals[0]["loan_instalment_id"], first.id)
        self.assertEqual(vals[0]["code"], "LOAN_REPAY")

    def test_get_inputs_skips_periods_with_nothing_due(self):
        loan = self._approved_loan(amount=400.0, instalment_count=2)
        far_future = self.month_start + relativedelta(months=24)
        payslip = self._payslip_for(loan, far_future)
        vals = payslip._get_loan_input_vals(
            payslip.contract_id, payslip.date_from, payslip.date_to
        )
        self.assertEqual(vals, [])

    def test_several_instalments_due_in_one_period_produce_several_rows(self):
        loan = self._approved_loan(amount=400.0, instalment_count=4)
        loan.instalment_ids.sorted("due_date")[1].due_date = self.month_start
        payslip = self._payslip_for(loan, self.month_start)
        vals = payslip._get_loan_input_vals(
            payslip.contract_id, payslip.date_from, payslip.date_to
        )
        self.assertEqual(len(vals), 2)

    def test_confirming_a_payslip_recovers_the_instalment(self):
        loan = self._approved_loan(amount=400.0, instalment_count=4)
        first = loan.instalment_ids.sorted("due_date")[0]
        payslip = self._payslip_for(loan, first.due_date)
        payslip.write(
            {
                "input_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Loan repayment",
                            "code": "LOAN_REPAY",
                            "amount": first.total_amount,
                            "contract_id": payslip.contract_id.id,
                            "loan_instalment_id": first.id,
                        },
                    )
                ]
            }
        )
        payslip.action_payslip_done()
        self.assertEqual(first.state, "recovered")
        self.assertEqual(first.payslip_id, payslip)
        self.assertEqual(loan.recovered_amount, 100.0)
        self.assertEqual(loan.outstanding_amount, 300.0)
        self.assertEqual(loan.instalments_remaining, 3)

    def test_recovery_is_idempotent(self):
        loan = self._approved_loan(amount=400.0, instalment_count=4)
        first = loan.instalment_ids.sorted("due_date")[0]
        payslip = self._payslip_for(loan, first.due_date)
        payslip.write(
            {
                "input_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Loan repayment",
                            "code": "LOAN_REPAY",
                            "amount": first.total_amount,
                            "contract_id": payslip.contract_id.id,
                            "loan_instalment_id": first.id,
                        },
                    )
                ]
            }
        )
        payslip.action_payslip_done()
        payslip._recover_loan_instalments()
        payslip._recover_loan_instalments()
        self.assertEqual(first.state, "recovered")
        self.assertEqual(loan.recovered_amount, 100.0)

    def test_recovering_the_last_instalment_closes_the_loan(self):
        loan = self._approved_loan(amount=100.0, instalment_count=1)
        only = loan.instalment_ids
        payslip = self._payslip_for(loan, only.due_date)
        payslip.write(
            {
                "input_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Loan repayment",
                            "code": "LOAN_REPAY",
                            "amount": only.total_amount,
                            "contract_id": payslip.contract_id.id,
                            "loan_instalment_id": only.id,
                        },
                    )
                ]
            }
        )
        payslip.action_payslip_done()
        self.assertEqual(loan.state, "closed")
        self.assertEqual(loan.outstanding_amount, 0.0)

    def test_salary_rule_and_rule_input_are_installed(self):
        rule = self.env.ref("odomate_hr_loan.hr_salary_rule_loan_repayment")
        rule_input = self.env.ref("odomate_hr_loan.hr_rule_input_loan_repayment")
        self.assertEqual(rule.amount_select, "code")
        self.assertEqual(rule_input.code, "LOAN_REPAY")
        self.assertEqual(rule_input.input_id, rule)
        self.assertTrue(rule.category_id)
        self.assertEqual(rule.category_id.code, "DED")
