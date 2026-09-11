from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestOdomateHrLoanAccounting(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.loan_allow_multiple = True
        cls.today = fields.Date.today()
        cls.month_start = cls.today.replace(day=1)

        cls.receivable_account = cls._make_account(
            "LOANREC", "Employee Loan Receivable", "asset_current"
        )
        cls.interest_account = cls._make_account(
            "LOANINT", "Employee Loan Interest Income", "income_other"
        )
        cls.payable_account = cls._make_account(
            "LOANPAY", "Employee Loan Counterpart", "liability_current"
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Employee Loans",
                "code": "ELOAN",
                "type": "general",
                "company_id": cls.company.id,
                "default_account_id": cls.payable_account.id,
            }
        )
        cls.journal_no_account = cls.env["account.journal"].create(
            {
                "name": "Employee Loans (unset)",
                "code": "ELOA2",
                "type": "general",
                "company_id": cls.company.id,
                "default_account_id": False,
            }
        )

        cls.company.loan_journal_id = cls.journal
        cls.company.loan_receivable_account_id = cls.receivable_account
        cls.company.loan_interest_income_account_id = cls.interest_account

        cls.partner = cls.env["res.partner"].create({"name": "Olena Borrower"})
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Olena Borrower",
                "company_id": cls.company.id,
                "work_contact_id": cls.partner.id,
            }
        )

        cls.officer_user = cls._make_internal_user(
            "Petro Officer", "petro.officer", ["base.group_user", "hr.group_hr_user"]
        )
        cls.plain_user = cls._make_internal_user(
            "Ivan Plain", "ivan.plain", ["base.group_user"]
        )
        cls.plain_partner = cls.env["res.partner"].create({"name": "Ivan Plain"})
        cls.plain_employee = cls.env["hr.employee"].create(
            {
                "name": "Ivan Plain",
                "company_id": cls.company.id,
                "work_contact_id": cls.plain_partner.id,
                "user_id": cls.plain_user.id,
            }
        )

    @classmethod
    def _make_internal_user(cls, name, login, group_xmlids):
        return cls.env["res.users"].create(
            {
                "name": name,
                "login": login,
                "email": "%s@example.com" % login,
                "company_id": cls.env.company.id,
                "company_ids": [Command.set([cls.env.company.id])],
                "group_ids": [
                    Command.set(
                        [cls.env.ref(xmlid).id for xmlid in group_xmlids]
                    )
                ],
            }
        )

    @classmethod
    def _make_account(cls, code, name, account_type):
        return cls.env["account.account"].create(
            {
                "code": code,
                "name": name,
                "account_type": account_type,
                "company_ids": [Command.set([cls.env.company.id])],
            }
        )

    def _make_loan(self, amount=1200.0, count=4, interest=0.0, employee=None):
        loan = self.env["odomate.hr.loan"].create(
            {
                "employee_id": (employee or self.employee).id,
                "amount": amount,
                "purpose": "Accounting acceptance walkthrough",
                "instalment_count": count,
                "interest_percentage": interest,
                "first_instalment_date": self.month_start,
            }
        )
        loan.action_build_schedule()
        loan.action_submit()
        return loan

    def _make_payslip(self, employee, period_start):
        return self.env["hr.payslip"].create(
            {
                "employee_id": employee.id,
                "date_from": period_start,
                "date_to": period_start + relativedelta(months=1, days=-1),
            }
        )

    def _lines_by_account(self, move):
        return {line.account_id: line for line in move.line_ids}

    # ------------------------------------------------------------------
    # Configuration defaults
    # ------------------------------------------------------------------
    def test_company_defaults_reach_a_new_loan(self):
        loan = self.env["odomate.hr.loan"].create(
            {
                "employee_id": self.employee.id,
                "amount": 500.0,
                "purpose": "Defaults check",
                "instalment_count": 1,
                "first_instalment_date": self.month_start,
            }
        )
        self.assertEqual(loan.journal_id, self.journal)
        self.assertEqual(loan.receivable_account_id, self.receivable_account)
        self.assertEqual(loan.interest_account_id, self.interest_account)

    def test_settings_expose_the_company_defaults(self):
        settings = self.env["res.config.settings"].create({})
        self.assertEqual(settings.loan_journal_id, self.journal)
        self.assertEqual(settings.loan_receivable_account_id, self.receivable_account)
        self.assertEqual(
            settings.loan_interest_income_account_id, self.interest_account
        )

    # ------------------------------------------------------------------
    # Disbursement
    # ------------------------------------------------------------------
    def test_approval_posts_the_disbursement_entry(self):
        loan = self._make_loan()
        loan.action_approve()

        move = loan.disbursement_move_id
        self.assertTrue(move, "Approval must post a disbursement entry")
        self.assertEqual(move.state, "posted")
        self.assertEqual(move.journal_id, self.journal)
        self.assertEqual(move.date, self.today)
        self.assertEqual(move.ref, "Loan %s - Disbursement" % loan.name)
        self.assertEqual(len(move.line_ids), 2)

        lines = self._lines_by_account(move)
        self.assertEqual(lines[self.receivable_account].debit, 1200.0)
        self.assertEqual(lines[self.receivable_account].credit, 0.0)
        self.assertEqual(lines[self.receivable_account].partner_id, self.partner)
        self.assertEqual(lines[self.payable_account].credit, 1200.0)

    def test_disbursement_is_posted_once(self):
        loan = self._make_loan()
        loan.action_approve()
        move = loan.disbursement_move_id
        loan._post_loan_disbursement_entry()
        self.assertEqual(loan.disbursement_move_id, move)

    def test_approval_refuses_a_loan_without_journal(self):
        loan = self._make_loan()
        loan.journal_id = False
        with self.assertRaises(UserError):
            loan.action_approve()
        self.assertEqual(loan.state, "submitted")
        self.assertFalse(loan.disbursement_move_id)

    def test_approval_refuses_a_journal_without_default_account(self):
        loan = self._make_loan()
        loan.journal_id = self.journal_no_account
        with self.assertRaises(UserError):
            loan.action_approve()
        self.assertEqual(loan.state, "submitted")

    def test_approval_refuses_a_loan_without_receivable_account(self):
        loan = self._make_loan()
        loan.receivable_account_id = False
        with self.assertRaises(UserError):
            loan.action_approve()
        self.assertEqual(loan.state, "submitted")

    def test_approval_refuses_interest_without_interest_account(self):
        loan = self._make_loan(amount=1000.0, count=2, interest=10.0)
        loan.interest_account_id = False
        with self.assertRaises(UserError):
            loan.action_approve()
        self.assertEqual(loan.state, "submitted")

    def test_approval_refuses_an_employee_without_a_contact(self):
        employee = self.env["hr.employee"].create(
            {"name": "Nameless Contact", "company_id": self.company.id}
        )
        loan = self._make_loan(employee=employee)
        employee.work_contact_id = False
        self.assertFalse(
            loan._find_loan_partner(),
            "The employee must have no contact for this test to mean anything",
        )
        with self.assertRaises(UserError):
            loan.action_approve()
        self.assertEqual(loan.state, "submitted")

    # ------------------------------------------------------------------
    # Recovery
    # ------------------------------------------------------------------
    def test_recovery_posts_one_entry_per_instalment(self):
        loan = self._make_loan(amount=1000.0, count=2, interest=10.0)
        loan.action_approve()
        instalment = loan.instalment_ids.sorted("due_date")[0]
        payslip = self._make_payslip(self.employee, self.month_start)

        instalment.write({"state": "recovered", "payslip_id": payslip.id})

        move = instalment.account_move_id
        self.assertTrue(move, "Recovering an instalment must post an entry")
        self.assertEqual(move.state, "posted")
        self.assertEqual(move.date, payslip.date_to)
        self.assertEqual(len(move.line_ids), 3)

        lines = self._lines_by_account(move)
        self.assertEqual(lines[self.payable_account].debit, instalment.total_amount)
        self.assertEqual(
            lines[self.receivable_account].credit, instalment.principal_amount
        )
        self.assertEqual(
            lines[self.interest_account].credit, instalment.interest_amount
        )
        self.assertEqual(lines[self.receivable_account].partner_id, self.partner)

    def test_recovery_omits_the_interest_line_when_there_is_none(self):
        loan = self._make_loan()
        loan.action_approve()
        instalment = loan.instalment_ids.sorted("due_date")[0]
        instalment.write(
            {
                "state": "recovered",
                "payslip_id": self._make_payslip(self.employee, self.month_start).id,
            }
        )
        move = instalment.account_move_id
        self.assertEqual(len(move.line_ids), 2)
        self.assertNotIn(self.interest_account, move.line_ids.account_id)

    def test_recovery_never_posts_twice(self):
        loan = self._make_loan()
        loan.action_approve()
        instalment = loan.instalment_ids.sorted("due_date")[0]
        instalment.write(
            {
                "state": "recovered",
                "payslip_id": self._make_payslip(self.employee, self.month_start).id,
            }
        )
        move = instalment.account_move_id
        instalment.write({"state": "recovered"})
        self.assertEqual(instalment.account_move_id, move)

    def test_recovery_is_skipped_silently_when_config_disappeared(self):
        loan = self._make_loan()
        loan.action_approve()
        loan.write({"journal_id": False})
        instalment = loan.instalment_ids.sorted("due_date")[0]

        instalment.write(
            {
                "state": "recovered",
                "payslip_id": self._make_payslip(self.employee, self.month_start).id,
            }
        )

        self.assertEqual(instalment.state, "recovered")
        self.assertFalse(instalment.account_move_id)

    def test_a_cancelled_instalment_gets_no_entry(self):
        loan = self._make_loan()
        loan.action_approve()
        instalment = loan.instalment_ids.sorted("due_date")[-1]
        instalment.write({"state": "cancelled"})
        self.assertFalse(instalment.account_move_id)

    # ------------------------------------------------------------------
    # Settlement
    # ------------------------------------------------------------------
    def test_settlement_posts_one_entry_for_the_outstanding_balance(self):
        loan = self._make_loan()
        loan.action_approve()
        instalment = loan.instalment_ids.sorted("due_date")[0]
        instalment.write(
            {
                "state": "recovered",
                "payslip_id": self._make_payslip(self.employee, self.month_start).id,
            }
        )
        outstanding = loan.outstanding_amount
        settlement_date = self.today + relativedelta(days=1)

        wizard = self.env["odomate.hr.loan.settle"].create(
            {
                "loan_id": loan.id,
                "settlement_date": settlement_date,
                "payment_reference": "BNK/SETTLE/0001",
            }
        )
        wizard.action_settle()

        move = loan.settlement_move_id
        self.assertTrue(move, "Settling a loan must post an entry")
        self.assertEqual(move.state, "posted")
        self.assertEqual(move.date, settlement_date)
        self.assertEqual(move.ref, "Loan %s - Settlement" % loan.name)

        lines = self._lines_by_account(move)
        self.assertEqual(lines[self.payable_account].debit, outstanding)
        self.assertEqual(lines[self.receivable_account].credit, outstanding)
        self.assertEqual(loan.state, "closed")

    def test_settling_a_loan_with_interest_clears_the_receivable(self):
        loan = self._make_loan(amount=1000.0, count=2, interest=10.0)
        loan.action_approve()
        instalment = loan.instalment_ids.sorted("due_date")[0]
        instalment.write(
            {
                "state": "recovered",
                "payslip_id": self._make_payslip(self.employee, self.month_start).id,
            }
        )
        remaining = loan.instalment_ids.sorted("due_date")[1]
        outstanding = loan.outstanding_amount

        wizard = self.env["odomate.hr.loan.settle"].create(
            {
                "loan_id": loan.id,
                "settlement_date": self.today,
                "payment_reference": "BNK/SETTLE/0004",
            }
        )
        wizard.action_settle()

        move = loan.settlement_move_id
        lines = self._lines_by_account(move)
        self.assertEqual(lines[self.payable_account].debit, outstanding)
        self.assertEqual(
            lines[self.receivable_account].credit, remaining.principal_amount
        )
        self.assertEqual(
            lines[self.interest_account].credit, remaining.interest_amount
        )

        receivable_lines = loan._get_account_moves().line_ids.filtered(
            lambda line: line.account_id == self.receivable_account
        )
        balance = sum(receivable_lines.mapped("debit")) - sum(
            receivable_lines.mapped("credit")
        )
        self.assertEqual(
            balance,
            0.0,
            "A closed loan must leave no balance on the receivable account",
        )

    def test_settlement_refuses_when_the_journal_was_cleared(self):
        loan = self._make_loan()
        loan.action_approve()
        loan.write({"journal_id": False})
        wizard = self.env["odomate.hr.loan.settle"].create(
            {
                "loan_id": loan.id,
                "settlement_date": self.today,
                "payment_reference": "BNK/SETTLE/0002",
            }
        )
        with self.assertRaises(UserError):
            wizard.action_settle()
        self.assertEqual(loan.state, "approved")
        self.assertFalse(loan.settlement_move_id)

    # ------------------------------------------------------------------
    # Counter and action
    # ------------------------------------------------------------------
    def test_counter_gathers_every_entry_of_the_loan(self):
        loan = self._make_loan()
        self.assertEqual(loan.account_move_count, 0)
        loan.action_approve()
        self.assertEqual(loan.account_move_count, 1)

        instalment = loan.instalment_ids.sorted("due_date")[0]
        instalment.write(
            {
                "state": "recovered",
                "payslip_id": self._make_payslip(self.employee, self.month_start).id,
            }
        )
        self.assertEqual(loan.account_move_count, 2)

        wizard = self.env["odomate.hr.loan.settle"].create(
            {
                "loan_id": loan.id,
                "settlement_date": self.today,
                "payment_reference": "BNK/SETTLE/0003",
            }
        )
        wizard.action_settle()
        self.assertEqual(loan.account_move_count, 3)

        action = loan.action_view_account_moves()
        self.assertEqual(action["res_model"], "account.move")
        expected = {
            loan.disbursement_move_id.id,
            loan.settlement_move_id.id,
            instalment.account_move_id.id,
        }
        self.assertEqual(set(action["domain"][0][2]), expected)

    # ------------------------------------------------------------------
    # Access rights: an HR officer with no accounting group
    # ------------------------------------------------------------------
    def _assertFieldsHidden(self, loan_as_user, field_names):
        for field_name in field_names:
            with self.assertRaises(
                AccessError,
                msg="%s must not reveal its real value to this user" % field_name,
            ):
                loan_as_user.read([field_name])

    def test_officer_without_accounting_rights_can_approve_a_loan(self):
        loan = self._make_loan()
        loan.with_user(self.officer_user).action_approve()

        self.assertEqual(loan.state, "approved")
        move = loan.disbursement_move_id
        self.assertTrue(
            move, "Approval by an HR officer must still post the disbursement entry"
        )
        self.assertEqual(move.state, "posted")
        self.assertEqual(move.journal_id, self.journal)

        lines = self._lines_by_account(move)
        self.assertEqual(lines[self.receivable_account].debit, loan.amount)
        self.assertEqual(lines[self.receivable_account].credit, 0.0)
        self.assertEqual(lines[self.payable_account].credit, loan.amount)

    def test_officer_cannot_read_the_entry_it_just_posted(self):
        loan = self._make_loan()
        loan.with_user(self.officer_user).action_approve()
        move = loan.disbursement_move_id

        with self.assertRaises(AccessError):
            move.with_user(self.officer_user).read(["ref"])

    def test_officer_cannot_read_accounting_fields_through_the_orm(self):
        loan = self._make_loan()
        loan.action_approve()

        self._assertFieldsHidden(
            loan.with_user(self.officer_user),
            [
                "journal_id",
                "receivable_account_id",
                "interest_account_id",
                "account_move_count",
                "disbursement_move_id",
            ],
        )

    def test_plain_user_sees_no_accounting_field_or_entry(self):
        loan = self._make_loan(employee=self.plain_employee)
        loan.action_approve()

        self._assertFieldsHidden(
            loan.with_user(self.plain_user),
            [
                "journal_id",
                "receivable_account_id",
                "interest_account_id",
                "account_move_count",
                "disbursement_move_id",
            ],
        )
        move = loan.disbursement_move_id
        with self.assertRaises(AccessError):
            move.with_user(self.plain_user).read(["ref"])

    def test_officer_approval_refuses_a_loan_without_journal_too(self):
        loan = self._make_loan()
        loan.journal_id = False
        with self.assertRaises(UserError) as failure:
            loan.with_user(self.officer_user).action_approve()
        self.assertIn(loan.name, str(failure.exception))
        self.assertEqual(loan.state, "submitted")
        self.assertFalse(loan.disbursement_move_id)

    def test_officer_approval_refuses_a_journal_without_default_account_too(self):
        loan = self._make_loan()
        loan.journal_id = self.journal_no_account
        with self.assertRaises(UserError) as failure:
            loan.with_user(self.officer_user).action_approve()
        self.assertIn(loan.name, str(failure.exception))
        self.assertEqual(loan.state, "submitted")

    def test_officer_approval_refuses_a_loan_without_receivable_account_too(self):
        loan = self._make_loan()
        loan.receivable_account_id = False
        with self.assertRaises(UserError) as failure:
            loan.with_user(self.officer_user).action_approve()
        self.assertIn(loan.name, str(failure.exception))
        self.assertEqual(loan.state, "submitted")

    def test_officer_approval_refuses_interest_without_interest_account_too(self):
        loan = self._make_loan(amount=1000.0, count=2, interest=10.0)
        loan.interest_account_id = False
        with self.assertRaises(UserError) as failure:
            loan.with_user(self.officer_user).action_approve()
        self.assertIn(loan.name, str(failure.exception))
        self.assertEqual(loan.state, "submitted")
