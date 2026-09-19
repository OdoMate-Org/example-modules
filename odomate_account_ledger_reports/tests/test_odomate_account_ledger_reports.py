from datetime import date

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged

D_PREV_FY = date(2023, 6, 15)
D_FY_EARLY = date(2024, 2, 10)
D_FROM = date(2024, 3, 1)
D_MID = date(2024, 3, 15)
D_TO = date(2024, 3, 31)
D_BEFORE_PAYMENT = date(2024, 4, 30)
D_PAYMENT = date(2024, 5, 20)
D_AGE_REF = date(2024, 6, 30)

REPORT_GENERAL_LEDGER = 'report.odomate_account_ledger_reports.report_general_ledger'
REPORT_PARTNER_LEDGER = 'report.odomate_account_ledger_reports.report_partner_ledger'
REPORT_AGED = 'report.odomate_account_ledger_reports.report_aged_partner_balance'
REPORT_TAX = 'report.odomate_account_ledger_reports.report_tax_report'
REPORT_JOURNAL_AUDIT = 'report.odomate_account_ledger_reports.report_journal_audit'


@tagged('post_install', '-at_install')
class TestOdomateAccountLedgerReports(TransactionCase):
    """Per-criterion coverage of the accounting audit reports module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country = cls.env.ref('base.us')
        cls.company_a = cls.env['res.company'].create({
            'name': 'OdoMate Ledger Co A',
            'country_id': cls.country.id,
        })
        cls.company_b = cls.env['res.company'].create({
            'name': 'OdoMate Ledger Co B',
            'country_id': cls.country.id,
        })
        cls.currency = cls.company_a.currency_id

        cls.acc_recv_a = cls._account(cls.company_a, '121000', 'Receivable A', 'asset_receivable')
        cls.acc_recv_aged = cls._account(cls.company_a, '121500', 'Receivable Ageing', 'asset_receivable')
        cls.acc_pay_a = cls._account(cls.company_a, '221000', 'Payable A', 'liability_payable')
        cls.acc_income_a = cls._account(cls.company_a, '400000', 'Income A', 'income')
        cls.acc_cash_a = cls._account(cls.company_a, '101000', 'Cash A', 'asset_current')
        cls.acc_sort_a = cls._account(cls.company_a, '150000', 'Sorting A', 'asset_current')
        cls.acc_zero_a = cls._account(cls.company_a, '160000', 'Zero Balance A', 'asset_current')
        cls.acc_unused_a = cls._account(cls.company_a, '990000', 'Unused A', 'asset_current')
        cls.acc_recv_b = cls._account(cls.company_b, '121000', 'Receivable B', 'asset_receivable')
        cls.acc_income_b = cls._account(cls.company_b, '400000', 'Income B', 'income')

        cls.jnl_misc_a = cls._journal(cls.company_a, 'MSCA', 'Misc A', 'general')
        cls.jnl_sale_a = cls._journal(cls.company_a, 'SAJA', 'Sales A', 'sale')
        cls.jnl_purchase_a = cls._journal(cls.company_a, 'BAJA', 'Purchases A', 'purchase')
        cls.jnl_misc_b = cls._journal(cls.company_b, 'MSCB', 'Misc B', 'general')

        cls.tax_group_a = cls.env['account.tax.group'].create({
            'name': 'OdoMate Tax Group',
            'company_id': cls.company_a.id,
        })
        cls.tax_sale_a = cls.env['account.tax'].create({
            'name': 'OdoMate Sale Tax 20%',
            'amount': 20.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'company_id': cls.company_a.id,
            'tax_group_id': cls.tax_group_a.id,
        })

        partner_names = [
            'ob', 'aged', 'zero_residual', 'residual', 'ledger', 'supplier',
            'settled', 'tax', 'zero_balance', 'sort_aaa', 'sort_zzz',
        ]
        cls.partners = {}
        for key in partner_names:
            cls.partners[key] = cls.env['res.partner'].create({'name': 'OdoMate %s' % key})
        cls.partners['sort_aaa'].name = 'AAA OdoMate Sorting'
        cls.partners['sort_zzz'].name = 'ZZZ OdoMate Sorting'
        cls.partners['tax'].with_company(cls.company_a).property_account_receivable_id = cls.acc_recv_a

        cls._build_opening_balance_entries()
        cls._build_ageing_entries()
        cls._build_residual_entries()
        cls._build_partner_ledger_entries()
        cls._build_sorting_entries()
        cls._build_display_account_entries()
        cls._build_state_entries()
        cls._build_company_b_entries()
        cls._build_tax_documents()

        cls.user_manager = cls._user('manager', ['account.group_account_manager'], [cls.company_a, cls.company_b])
        cls.user_user = cls._user('user', ['account.group_account_user'], [cls.company_a])
        cls.user_readonly = cls._user('readonly', ['account.group_account_readonly'], [cls.company_a])
        cls.user_plain = cls._user('plain', [], [cls.company_a])

    # ------------------------------------------------------------------
    # Fixture helpers
    # ------------------------------------------------------------------

    @classmethod
    def _account(cls, company, code, name, account_type):
        return cls.env['account.account'].create({
            'name': name,
            'code': code,
            'account_type': account_type,
            'company_ids': [Command.set([company.id])],
        })

    @classmethod
    def _journal(cls, company, code, name, journal_type):
        return cls.env['account.journal'].create({
            'name': name,
            'code': code,
            'type': journal_type,
            'company_id': company.id,
        })

    @classmethod
    def _entry(cls, journal, move_date, lines, post=True):
        move = cls.env['account.move'].with_company(journal.company_id).create({
            'move_type': 'entry',
            'journal_id': journal.id,
            'date': move_date,
            'line_ids': [Command.create(line) for line in lines],
        })
        if post:
            move.action_post()
        return move

    @classmethod
    def _user(cls, key, group_xmlids, companies):
        groups = cls.env.ref('base.group_user')
        for xmlid in group_xmlids:
            groups |= cls.env.ref(xmlid)
        return cls.env['res.users'].create({
            'name': 'OdoMate Ledger %s' % key,
            'login': 'odomate_ledger_%s' % key,
            'group_ids': [Command.set(groups.ids)],
            'company_id': companies[0].id,
            'company_ids': [Command.set([company.id for company in companies])],
        })

    @classmethod
    def _build_opening_balance_entries(cls):
        partner = cls.partners['ob']
        for move_date, amount in ((D_PREV_FY, 1000.0), (D_FY_EARLY, 500.0), (D_MID, 250.0)):
            cls._entry(cls.jnl_misc_a, move_date, [
                {'account_id': cls.acc_recv_a.id, 'partner_id': partner.id, 'debit': amount, 'credit': 0.0},
                {'account_id': cls.acc_income_a.id, 'partner_id': partner.id, 'debit': 0.0, 'credit': amount},
            ])

    @classmethod
    def _build_ageing_entries(cls):
        partner = cls.partners['aged']
        specs = [
            (date(2024, 6, 30), 10.0),
            (date(2024, 6, 29), 20.0),
            (date(2024, 5, 31), 30.0),
            (date(2024, 5, 30), 40.0),
            (date(2024, 3, 1), 50.0),
        ]
        for due, amount in specs:
            cls._entry(cls.jnl_misc_a, due, [
                {
                    'account_id': cls.acc_recv_aged.id,
                    'partner_id': partner.id,
                    'debit': amount,
                    'credit': 0.0,
                    'date_maturity': due,
                },
                {'account_id': cls.acc_income_a.id, 'partner_id': partner.id, 'debit': 0.0, 'credit': amount},
            ])

        zero_partner = cls.partners['zero_residual']
        debit_move = cls._entry(cls.jnl_misc_a, date(2024, 4, 1), [
            {
                'account_id': cls.acc_recv_aged.id,
                'partner_id': zero_partner.id,
                'debit': 100.0,
                'credit': 0.0,
                'date_maturity': date(2024, 4, 1),
            },
            {'account_id': cls.acc_income_a.id, 'partner_id': zero_partner.id, 'debit': 0.0, 'credit': 100.0},
        ])
        credit_move = cls._entry(cls.jnl_misc_a, date(2024, 4, 2), [
            {
                'account_id': cls.acc_recv_aged.id,
                'partner_id': zero_partner.id,
                'debit': 0.0,
                'credit': 100.0,
                'date_maturity': date(2024, 4, 2),
            },
            {'account_id': cls.acc_cash_a.id, 'partner_id': zero_partner.id, 'debit': 100.0, 'credit': 0.0},
        ])
        settled_lines = (debit_move.line_ids + credit_move.line_ids).filtered(
            lambda line: line.account_id == cls.acc_recv_aged
        )
        settled_lines.reconcile()

        cls._entry(cls.jnl_misc_a, date(2024, 6, 15), [
            {
                'account_id': cls.acc_recv_aged.id,
                'debit': 70.0,
                'credit': 0.0,
                'date_maturity': date(2024, 6, 15),
            },
            {'account_id': cls.acc_income_a.id, 'debit': 0.0, 'credit': 70.0},
        ])

    @classmethod
    def _build_residual_entries(cls):
        partner = cls.partners['residual']
        invoice_move = cls._entry(cls.jnl_misc_a, date(2024, 3, 10), [
            {
                'account_id': cls.acc_recv_a.id,
                'partner_id': partner.id,
                'debit': 1000.0,
                'credit': 0.0,
                'date_maturity': date(2024, 3, 10),
            },
            {'account_id': cls.acc_income_a.id, 'partner_id': partner.id, 'debit': 0.0, 'credit': 1000.0},
        ])
        payment_move = cls._entry(cls.jnl_misc_a, D_PAYMENT, [
            {
                'account_id': cls.acc_recv_a.id,
                'partner_id': partner.id,
                'debit': 0.0,
                'credit': 400.0,
                'date_maturity': D_PAYMENT,
            },
            {'account_id': cls.acc_cash_a.id, 'partner_id': partner.id, 'debit': 400.0, 'credit': 0.0},
        ])
        cls.residual_invoice_line = invoice_move.line_ids.filtered(
            lambda line: line.account_id == cls.acc_recv_a
        )
        payment_line = payment_move.line_ids.filtered(lambda line: line.account_id == cls.acc_recv_a)
        (cls.residual_invoice_line + payment_line).reconcile()

    @classmethod
    def _build_partner_ledger_entries(cls):
        ledger_partner = cls.partners['ledger']
        cls._entry(cls.jnl_misc_a, date(2024, 3, 5), [
            {'account_id': cls.acc_recv_a.id, 'partner_id': ledger_partner.id, 'debit': 600.0, 'credit': 0.0},
            {'account_id': cls.acc_income_a.id, 'partner_id': ledger_partner.id, 'debit': 0.0, 'credit': 600.0},
        ])
        cls._entry(cls.jnl_misc_a, date(2024, 3, 20), [
            {'account_id': cls.acc_recv_a.id, 'partner_id': ledger_partner.id, 'debit': 0.0, 'credit': 250.0},
            {'account_id': cls.acc_cash_a.id, 'partner_id': ledger_partner.id, 'debit': 250.0, 'credit': 0.0},
        ])

        supplier = cls.partners['supplier']
        cls._entry(cls.jnl_misc_a, date(2024, 3, 8), [
            {'account_id': cls.acc_pay_a.id, 'partner_id': supplier.id, 'debit': 0.0, 'credit': 500.0},
            {'account_id': cls.acc_cash_a.id, 'partner_id': supplier.id, 'debit': 500.0, 'credit': 0.0},
        ])

        settled = cls.partners['settled']
        debit_move = cls._entry(cls.jnl_misc_a, date(2024, 3, 5), [
            {'account_id': cls.acc_recv_a.id, 'partner_id': settled.id, 'debit': 300.0, 'credit': 0.0},
            {'account_id': cls.acc_income_a.id, 'partner_id': settled.id, 'debit': 0.0, 'credit': 300.0},
        ])
        credit_move = cls._entry(cls.jnl_misc_a, date(2024, 3, 6), [
            {'account_id': cls.acc_recv_a.id, 'partner_id': settled.id, 'debit': 0.0, 'credit': 300.0},
            {'account_id': cls.acc_cash_a.id, 'partner_id': settled.id, 'debit': 300.0, 'credit': 0.0},
        ])
        (debit_move.line_ids + credit_move.line_ids).filtered(
            lambda line: line.account_id == cls.acc_recv_a
        ).reconcile()

        cls._entry(cls.jnl_misc_a, date(2024, 3, 12), [
            {'account_id': cls.acc_recv_a.id, 'debit': 90.0, 'credit': 0.0},
            {'account_id': cls.acc_income_a.id, 'debit': 0.0, 'credit': 90.0},
        ])

    @classmethod
    def _build_sorting_entries(cls):
        cls._entry(cls.jnl_misc_a, date(2024, 3, 5), [
            {
                'account_id': cls.acc_sort_a.id,
                'partner_id': cls.partners['sort_zzz'].id,
                'name': 'SORT-EARLY-ZZZ',
                'debit': 11.0,
                'credit': 0.0,
            },
            {'account_id': cls.acc_cash_a.id, 'debit': 0.0, 'credit': 11.0},
        ])
        cls._entry(cls.jnl_misc_a, date(2024, 3, 25), [
            {
                'account_id': cls.acc_sort_a.id,
                'partner_id': cls.partners['sort_aaa'].id,
                'name': 'SORT-LATE-AAA',
                'debit': 22.0,
                'credit': 0.0,
            },
            {'account_id': cls.acc_cash_a.id, 'debit': 0.0, 'credit': 22.0},
        ])

    @classmethod
    def _build_display_account_entries(cls):
        partner = cls.partners['zero_balance']
        cls._entry(cls.jnl_misc_a, date(2024, 3, 9), [
            {'account_id': cls.acc_zero_a.id, 'partner_id': partner.id, 'debit': 100.0, 'credit': 0.0},
            {'account_id': cls.acc_cash_a.id, 'debit': 0.0, 'credit': 100.0},
        ])
        cls._entry(cls.jnl_misc_a, date(2024, 3, 11), [
            {'account_id': cls.acc_zero_a.id, 'partner_id': partner.id, 'debit': 0.0, 'credit': 100.0},
            {'account_id': cls.acc_cash_a.id, 'debit': 100.0, 'credit': 0.0},
        ])

    @classmethod
    def _build_state_entries(cls):
        cls.draft_move = cls._entry(cls.jnl_misc_a, date(2024, 3, 18), [
            {'account_id': cls.acc_cash_a.id, 'name': 'DRAFT-ITEM', 'debit': 77.0, 'credit': 0.0},
            {'account_id': cls.acc_income_a.id, 'debit': 0.0, 'credit': 77.0},
        ], post=False)
        cls.cancelled_move = cls._entry(cls.jnl_misc_a, date(2024, 3, 19), [
            {'account_id': cls.acc_cash_a.id, 'name': 'CANCELLED-ITEM', 'debit': 88.0, 'credit': 0.0},
            {'account_id': cls.acc_income_a.id, 'debit': 0.0, 'credit': 88.0},
        ], post=False)
        cls.cancelled_move.button_cancel()

    @classmethod
    def _build_company_b_entries(cls):
        cls._entry(cls.jnl_misc_b, D_MID, [
            {'account_id': cls.acc_recv_b.id, 'debit': 4200.0, 'credit': 0.0},
            {'account_id': cls.acc_income_b.id, 'debit': 0.0, 'credit': 4200.0},
        ])

    @classmethod
    def _build_tax_documents(cls):
        move_model = cls.env['account.move'].with_company(cls.company_a)
        cls.tax_invoice = move_model.create({
            'move_type': 'out_invoice',
            'journal_id': cls.jnl_sale_a.id,
            'partner_id': cls.partners['tax'].id,
            'invoice_date': date(2024, 3, 5),
            'date': date(2024, 3, 5),
            'invoice_line_ids': [Command.create({
                'name': 'Taxed sale',
                'quantity': 1.0,
                'price_unit': 1000.0,
                'account_id': cls.acc_income_a.id,
                'tax_ids': [Command.set(cls.tax_sale_a.ids)],
            })],
        })
        cls.tax_invoice.action_post()
        cls.tax_credit_note = move_model.create({
            'move_type': 'out_refund',
            'journal_id': cls.jnl_sale_a.id,
            'partner_id': cls.partners['tax'].id,
            'invoice_date': date(2024, 3, 20),
            'date': date(2024, 3, 20),
            'invoice_line_ids': [Command.create({
                'name': 'Taxed sale refund',
                'quantity': 1.0,
                'price_unit': 400.0,
                'account_id': cls.acc_income_a.id,
                'tax_ids': [Command.set(cls.tax_sale_a.ids)],
            })],
        })
        cls.tax_credit_note.action_post()

    # ------------------------------------------------------------------
    # Test helpers
    # ------------------------------------------------------------------

    def _wizard(self, model, values=None, company=None, user=None, context=None):
        company = company or self.company_a
        env = self.env(user=user) if user else self.env
        ctx = {'allowed_company_ids': [company.id]}
        ctx.update(context or {})
        payload = {'company_id': company.id}
        payload.update(values or {})
        return env[model].with_context(**ctx).create(payload)

    def _report_values(self, report_model, wizard, user=None):
        user = user or self.user_manager
        env = self.env(user=user)
        return env[report_model].with_context(
            allowed_company_ids=[wizard.company_id.id]
        )._get_report_values(wizard.ids, wizard._odomate_report_data())

    def _block_by_account(self, values, account):
        for block in values['blocks']:
            if block['account'] == account:
                return block
        return None

    def _block_by_partner(self, values, partner):
        for block in values['blocks']:
            if block['partner'] == partner:
                return block
        return None

    def _aged_row(self, values, partner):
        for row in values['rows']:
            if row['partner'] == partner:
                return row
        return None

    # ------------------------------------------------------------------
    # Criteria 1-9 - the shared filter contract
    # ------------------------------------------------------------------

    def test_criterion_01_journals_default_to_every_company_journal(self):
        """Criterion 01: an empty journal selection covers every journal of the company."""
        wizard = self._wizard('odomate.account.general.ledger.wizard')
        journals = wizard._odomate_journals()
        self.assertIn(self.jnl_misc_a, journals)
        self.assertIn(self.jnl_sale_a, journals)
        self.assertIn(self.jnl_purchase_a, journals)
        self.assertNotIn(self.jnl_misc_b, journals)

    def test_criterion_02_journals_honour_an_explicit_selection(self):
        """Criterion 02: an explicit journal selection is used verbatim."""
        wizard = self._wizard('odomate.account.general.ledger.wizard', {
            'journal_ids': [Command.set(self.jnl_misc_a.ids)],
        })
        self.assertEqual(wizard._odomate_journals(), self.jnl_misc_a)

    def test_criterion_03_target_move_maps_to_states_and_never_cancel(self):
        """Criterion 03: posted covers posted only, all covers draft and posted, cancel is never included."""
        wizard = self._wizard('odomate.account.general.ledger.wizard')
        self.assertEqual(wizard._odomate_state_domain(), [('parent_state', 'in', ['posted'])])
        wizard.target_move = 'all'
        self.assertEqual(wizard._odomate_state_domain(), [('parent_state', 'in', ['draft', 'posted'])])

        wizard.write({'date_from': D_FROM, 'date_to': D_TO})
        draft_line = self.draft_move.line_ids.filtered(lambda line: line.account_id == self.acc_cash_a)
        found = self.env['account.move.line'].search(wizard._odomate_line_domain(), order='id')
        self.assertIn(draft_line, found)
        for line in self.cancelled_move.line_ids:
            self.assertNotIn(line, found)

        wizard.target_move = 'posted'
        posted_only = self.env['account.move.line'].search(wizard._odomate_line_domain(), order='id')
        self.assertNotIn(draft_line, posted_only)

    def test_criterion_04_line_domain_excludes_non_accountable_display_types(self):
        """Criterion 04: the base filter excludes section, subsection and note lines."""
        wizard = self._wizard('odomate.account.general.ledger.wizard')
        domain = wizard._odomate_line_domain()
        self.assertIn(
            ('display_type', 'not in', ['line_section', 'line_subsection', 'line_note']),
            domain,
        )

    def test_criterion_05_line_domain_is_restricted_to_the_chosen_company(self):
        """Criterion 05: journal items of another company never reach the report."""
        wizard = self._wizard('odomate.account.general.ledger.wizard')
        found = self.env['account.move.line'].search(wizard._odomate_line_domain(), order='id')
        self.assertTrue(found)
        self.assertEqual(found.company_id, self.company_a)
        self.assertFalse(found.filtered(lambda line: line.account_id == self.acc_recv_b))

    def test_criterion_06_line_domain_honours_the_date_range(self):
        """Criterion 06: date_from and date_to bound the journal items."""
        wizard = self._wizard('odomate.account.general.ledger.wizard', {
            'date_from': D_FROM,
            'date_to': D_TO,
        })
        found = self.env['account.move.line'].search(wizard._odomate_line_domain(), order='id')
        self.assertTrue(found)
        for line in found:
            self.assertGreaterEqual(line.date, D_FROM)
            self.assertLessEqual(line.date, D_TO)

    def test_criterion_07_check_filter_rejects_a_forbidden_company(self):
        """Criterion 07: printing for a company outside the allowed ones is refused."""
        wizard = self._wizard('odomate.account.general.ledger.wizard')
        wizard = wizard.with_context(allowed_company_ids=[self.company_b.id])
        with self.assertRaises(UserError):
            wizard._odomate_check_filter()

    def test_criterion_08_check_filter_rejects_an_inverted_date_range(self):
        """Criterion 08: a start date after the end date is refused."""
        wizard = self._wizard('odomate.account.general.ledger.wizard', {
            'date_from': D_TO,
            'date_to': D_FROM,
        })
        with self.assertRaises(UserError):
            wizard._odomate_check_filter()

    def test_criterion_09_check_filter_rejects_a_foreign_journal(self):
        """Criterion 09: a journal of another company is refused."""
        wizard = self._wizard('odomate.account.general.ledger.wizard', {
            'journal_ids': [Command.set(self.jnl_misc_b.ids)],
        })
        with self.assertRaises(UserError):
            wizard._odomate_check_filter()

    # ------------------------------------------------------------------
    # Criteria 10-14 - per-dialog validation and the data payload
    # ------------------------------------------------------------------

    def test_criterion_10_general_ledger_requires_a_start_date_for_the_opening(self):
        """Criterion 10: the opening balance option requires a start date."""
        wizard = self._wizard('odomate.account.general.ledger.wizard', {'initial_balance': True})
        with self.assertRaises(UserError):
            wizard._odomate_check_filter()
        wizard.date_from = D_FROM
        wizard._odomate_check_filter()

    def test_criterion_11_aged_rejects_a_non_positive_period_length(self):
        """Criterion 11: the ageing period length must be at least one day."""
        wizard = self._wizard('odomate.account.aged.partner.wizard', {
            'date_to': D_AGE_REF,
            'period_length': 0,
        })
        with self.assertRaises(UserError):
            wizard._odomate_check_filter()

    def test_criterion_12_aged_rejects_a_missing_as_of_date(self):
        """Criterion 12: the ageing date is mandatory."""
        wizard = self.env['odomate.account.aged.partner.wizard'].with_context(
            allowed_company_ids=[self.company_a.id]
        ).new({
            'company_id': self.company_a.id,
            'period_length': 30,
            'date_to': False,
        })
        with self.assertRaises(UserError):
            wizard._odomate_check_filter()

    def test_criterion_13_report_data_carries_only_primitive_values(self):
        """Criterion 13: the payload crossing the browser holds ids, strings and booleans only."""
        wizard = self._wizard('odomate.account.general.ledger.wizard', {
            'date_from': D_FROM,
            'date_to': D_TO,
            'account_ids': [Command.set(self.acc_recv_a.ids)],
        })
        data = wizard._odomate_report_data()
        for key, value in data.items():
            self.assertIsInstance(value, (bool, int, str, list), 'unexpected type for %s' % key)
            if isinstance(value, list):
                for item in value:
                    self.assertIsInstance(item, int, 'unexpected list item for %s' % key)
        self.assertEqual(data['date_from'], D_FROM.isoformat())
        self.assertEqual(data['wizard_model'], 'odomate.account.general.ledger.wizard')

    def test_criterion_14_options_round_trip_the_payload(self):
        """Criterion 14: the payload is parsed back into records and dates."""
        wizard = self._wizard('odomate.account.general.ledger.wizard', {
            'date_from': D_FROM,
            'date_to': D_TO,
            'journal_ids': [Command.set(self.jnl_misc_a.ids)],
            'account_ids': [Command.set(self.acc_recv_a.ids)],
        })
        options = self.env['odomate.account.general.ledger.wizard']._odomate_options_from_data(
            wizard._odomate_report_data()
        )
        self.assertEqual(options['company'], self.company_a)
        self.assertEqual(options['date_from'], D_FROM)
        self.assertEqual(options['date_to'], D_TO)
        self.assertEqual(options['journals'], self.jnl_misc_a)
        self.assertTrue(options['explicit_journals'])
        self.assertEqual(options['accounts'], self.acc_recv_a)

    # ------------------------------------------------------------------
    # Criteria 15-19 - general ledger
    # ------------------------------------------------------------------

    def _general_ledger_opening_values(self):
        wizard = self._wizard('odomate.account.general.ledger.wizard', {
            'date_from': D_FROM,
            'date_to': D_TO,
            'initial_balance': True,
            'display_account': 'all',
            'account_ids': [Command.set((self.acc_recv_a + self.acc_income_a).ids)],
            'partner_ids': [Command.set(self.partners['ob'].ids)],
        })
        return self._report_values(REPORT_GENERAL_LEDGER, wizard)

    def test_criterion_15_balance_sheet_account_opens_with_everything_before_the_start(self):
        """Criterion 15: a balance-sheet account opens with every entry booked before the start date."""
        values = self._general_ledger_opening_values()
        block = self._block_by_account(values, self.acc_recv_a)
        self.assertIsNotNone(block)
        self.assertAlmostEqual(block['opening'], 1500.0, places=2)

    def test_criterion_16_income_account_opens_with_the_fiscal_year_to_date_only(self):
        """Criterion 16: an income account opens with the current fiscal year only."""
        values = self._general_ledger_opening_values()
        block = self._block_by_account(values, self.acc_income_a)
        self.assertIsNotNone(block)
        self.assertAlmostEqual(block['opening'], -500.0, places=2)

    def test_criterion_17_running_balance_starts_at_the_opening_balance(self):
        """Criterion 17: the running balance starts at the opening and accumulates every item."""
        values = self._general_ledger_opening_values()
        block = self._block_by_account(values, self.acc_recv_a)
        self.assertTrue(block['rows'][0]['opening'])
        self.assertAlmostEqual(block['rows'][0]['balance'], 1500.0, places=2)
        self.assertAlmostEqual(block['rows'][1]['balance'], 1750.0, places=2)
        self.assertAlmostEqual(block['debit'], 250.0, places=2)
        self.assertAlmostEqual(block['credit'], 0.0, places=2)
        self.assertAlmostEqual(block['balance'], 1750.0, places=2)

    def test_criterion_18_display_account_not_zero_drops_balanced_accounts(self):
        """Criterion 18: not_zero hides an account whose opening plus movements is zero."""
        base_values = {
            'date_from': D_FROM,
            'date_to': D_TO,
            'account_ids': [Command.set(self.acc_zero_a.ids)],
        }
        with_movement = self._report_values(
            REPORT_GENERAL_LEDGER,
            self._wizard('odomate.account.general.ledger.wizard', dict(base_values, display_account='movement')),
        )
        self.assertIsNotNone(self._block_by_account(with_movement, self.acc_zero_a))
        not_zero = self._report_values(
            REPORT_GENERAL_LEDGER,
            self._wizard('odomate.account.general.ledger.wizard', dict(base_values, display_account='not_zero')),
        )
        self.assertIsNone(self._block_by_account(not_zero, self.acc_zero_a))

    def test_criterion_19_sort_by_changes_the_item_order(self):
        """Criterion 19: sort_date and sort_journal_partner order the items differently."""
        base_values = {
            'date_from': D_FROM,
            'date_to': D_TO,
            'account_ids': [Command.set(self.acc_sort_a.ids)],
        }
        by_date = self._report_values(
            REPORT_GENERAL_LEDGER,
            self._wizard('odomate.account.general.ledger.wizard', dict(base_values, sortby='sort_date')),
        )
        by_journal = self._report_values(
            REPORT_GENERAL_LEDGER,
            self._wizard(
                'odomate.account.general.ledger.wizard',
                dict(base_values, sortby='sort_journal_partner'),
            ),
        )
        date_labels = [row['label'] for row in self._block_by_account(by_date, self.acc_sort_a)['rows']]
        journal_labels = [row['label'] for row in self._block_by_account(by_journal, self.acc_sort_a)['rows']]
        self.assertEqual(date_labels, ['SORT-EARLY-ZZZ', 'SORT-LATE-AAA'])
        self.assertEqual(journal_labels, ['SORT-LATE-AAA', 'SORT-EARLY-ZZZ'])

    # ------------------------------------------------------------------
    # Criteria 20-22 - partner ledger
    # ------------------------------------------------------------------

    def _partner_ledger_values(self, **overrides):
        values = {'date_from': D_FROM, 'date_to': D_TO}
        values.update(overrides)
        wizard = self._wizard('odomate.account.partner.ledger.wizard', values)
        return self._report_values(REPORT_PARTNER_LEDGER, wizard)

    def test_criterion_20_result_selection_maps_to_account_types(self):
        """Criterion 20: receivable, payable and both map onto the right account types."""
        customer = self._partner_ledger_values(result_selection='customer')
        self.assertIsNotNone(self._block_by_partner(customer, self.partners['ledger']))
        self.assertIsNone(self._block_by_partner(customer, self.partners['supplier']))

        supplier = self._partner_ledger_values(result_selection='supplier')
        self.assertIsNotNone(self._block_by_partner(supplier, self.partners['supplier']))
        self.assertIsNone(self._block_by_partner(supplier, self.partners['ledger']))

        both = self._partner_ledger_values(result_selection='customer_supplier')
        self.assertIsNotNone(self._block_by_partner(both, self.partners['ledger']))
        self.assertIsNotNone(self._block_by_partner(both, self.partners['supplier']))

    def test_criterion_21_settled_items_are_hidden_unless_requested(self):
        """Criterion 21: fully reconciled items appear only with Include Settled Items."""
        without = self._partner_ledger_values(result_selection='customer', reconciled=False)
        self.assertIsNone(self._block_by_partner(without, self.partners['settled']))
        with_settled = self._partner_ledger_values(result_selection='customer', reconciled=True)
        self.assertIsNotNone(self._block_by_partner(with_settled, self.partners['settled']))

    def test_criterion_22_partner_ledger_has_no_partnerless_block_and_reports_amount_owed(self):
        """Criterion 22: items without a partner are skipped and each block reports the amount owed."""
        values = self._partner_ledger_values(result_selection='customer')
        self.assertTrue(values['blocks'])
        for block in values['blocks']:
            self.assertTrue(block['partner'])
        block = self._block_by_partner(values, self.partners['ledger'])
        self.assertAlmostEqual(block['debit'], 600.0, places=2)
        self.assertAlmostEqual(block['credit'], 250.0, places=2)
        self.assertAlmostEqual(block['balance'], 350.0, places=2)
        self.assertAlmostEqual(block['amount_owed'], 350.0, places=2)

    # ------------------------------------------------------------------
    # Criteria 23-25 - aged partner balance
    # ------------------------------------------------------------------

    def _aged_values(self, **overrides):
        values = {'date_to': D_AGE_REF, 'period_length': 30, 'result_selection': 'customer'}
        values.update(overrides)
        wizard = self._wizard('odomate.account.aged.partner.wizard', values)
        return self._report_values(REPORT_AGED, wizard)

    def test_criterion_23_ages_land_in_the_expected_buckets(self):
        """Criterion 23: items aged 0, 1, P, P+1 and 4P+1 days fall into the right columns."""
        values = self._aged_values(partner_ids=[Command.set(self.partners['aged'].ids)])
        row = self._aged_row(values, self.partners['aged'])
        self.assertIsNotNone(row)
        amounts = row['amounts']
        self.assertAlmostEqual(amounts['not_due'], 10.0, places=2)
        self.assertAlmostEqual(amounts['age_1'], 50.0, places=2)
        self.assertAlmostEqual(amounts['age_2'], 40.0, places=2)
        self.assertAlmostEqual(amounts['age_3'], 0.0, places=2)
        self.assertAlmostEqual(amounts['age_4'], 0.0, places=2)
        self.assertAlmostEqual(amounts['older'], 50.0, places=2)
        self.assertAlmostEqual(row['total'], 150.0, places=2)
        self.assertEqual(values['period_labels'], ['1 - 30', '31 - 60', '61 - 90', '91 - 120', '+120'])

    def test_criterion_24_residual_is_measured_as_of_the_ageing_date(self):
        """Criterion 24: a payment posted after the ageing date does not reduce the residual."""
        before = self._aged_values(
            date_to=D_BEFORE_PAYMENT,
            partner_ids=[Command.set(self.partners['residual'].ids)],
        )
        row_before = self._aged_row(before, self.partners['residual'])
        self.assertAlmostEqual(row_before['total'], 1000.0, places=2)

        after = self._aged_values(partner_ids=[Command.set(self.partners['residual'].ids)])
        row_after = self._aged_row(after, self.partners['residual'])
        self.assertAlmostEqual(row_after['total'], 600.0, places=2)

    def test_criterion_25_zero_residuals_drop_and_partnerless_items_are_grouped(self):
        """Criterion 25: settled items disappear and items without a partner form an Unknown Partner row."""
        values = self._aged_values()
        self.assertIsNone(self._aged_row(values, self.partners['zero_residual']))
        unknown = [row for row in values['rows'] if not row['partner']]
        self.assertEqual(len(unknown), 1)
        self.assertAlmostEqual(unknown[0]['total'], 160.0, places=2)
        self.assertFalse(unknown[0]['partner_label'])

    # ------------------------------------------------------------------
    # Criteria 26-28 - tax report, journals audit, access
    # ------------------------------------------------------------------

    def test_criterion_26_sales_taxes_are_negated_and_credit_notes_reduce_them(self):
        """Criterion 26: the Sales section is sign-flipped and a credit note lowers both figures."""
        wizard = self._wizard('odomate.account.tax.report.wizard', {
            'date_from': D_FROM,
            'date_to': D_TO,
        })
        values = self._report_values(REPORT_TAX, wizard)
        sales = next(section for section in values['sections'] if section['key'] == 'sale')
        row = next(row for row in sales['rows'] if row['name'] == self.tax_sale_a.name)
        self.assertAlmostEqual(row['net'], 600.0, places=2)
        self.assertAlmostEqual(row['tax'], 120.0, places=2)
        self.assertAlmostEqual(sales['net'], 600.0, places=2)
        self.assertAlmostEqual(sales['tax'], 120.0, places=2)

    def test_criterion_27_journals_audit_prints_one_block_per_journal(self):
        """Criterion 27: every selected journal gets its own section with its own totals."""
        wizard = self._wizard('odomate.account.journal.audit.wizard', {
            'date_from': D_FROM,
            'date_to': D_TO,
            'journal_ids': [Command.set((self.jnl_misc_a + self.jnl_sale_a).ids)],
        })
        values = self._report_values(REPORT_JOURNAL_AUDIT, wizard)
        self.assertEqual([block['journal'] for block in values['blocks']], [self.jnl_misc_a, self.jnl_sale_a])
        for block in values['blocks']:
            self.assertAlmostEqual(block['debit'], sum(row['debit'] for row in block['rows']), places=2)
            self.assertAlmostEqual(block['credit'], sum(row['credit'] for row in block['rows']), places=2)
            for row in block['rows']:
                self.assertTrue(row['account_label'])
        sale_block = values['blocks'][1]
        self.assertTrue(sale_block['tax_rows'])

    def test_criterion_28_only_accounting_users_may_print(self):
        """Criterion 28: the three accounting groups may print and nobody else gains access here."""
        wizard = self._wizard('odomate.account.general.ledger.wizard', {
            'date_from': D_FROM,
            'date_to': D_TO,
        })
        data = wizard._odomate_report_data()
        for user in (self.user_manager, self.user_user, self.user_readonly):
            values = self.env(user=user)[REPORT_GENERAL_LEDGER].with_context(
                allowed_company_ids=[self.company_a.id]
            )._get_report_values(wizard.ids, data)
            self.assertIn('blocks', values)
        with self.assertRaises(AccessError):
            self.env(user=self.user_plain)[REPORT_GENERAL_LEDGER].with_context(
                allowed_company_ids=[self.company_a.id]
            )._get_report_values(wizard.ids, data)

        granted = self.env['ir.model.access'].search([
            ('model_id.model', 'like', 'odomate.account.%'),
        ], order='id').group_id
        self.assertNotIn(self.env.ref('account.group_account_invoice'), granted)
        self.assertNotIn(self.env.ref('base.group_user'), granted)

    # ------------------------------------------------------------------
    # Rendering smoke test
    # ------------------------------------------------------------------

    def test_smoke_every_report_renders(self):
        """Smoke: every shipped QWeb report renders end to end for an accounting user."""
        report_env = self.env(user=self.user_manager)['ir.actions.report'].with_context(
            allowed_company_ids=[self.company_a.id]
        )
        specs = [
            ('odomate.account.general.ledger.wizard',
             'odomate_account_ledger_reports.action_report_odomate_general_ledger',
             {'date_from': D_FROM, 'date_to': D_TO, 'initial_balance': True, 'display_account': 'all'}),
            ('odomate.account.partner.ledger.wizard',
             'odomate_account_ledger_reports.action_report_odomate_partner_ledger',
             {'date_from': D_FROM, 'date_to': D_TO, 'result_selection': 'customer_supplier'}),
            ('odomate.account.aged.partner.wizard',
             'odomate_account_ledger_reports.action_report_odomate_aged_partner',
             {'date_to': D_AGE_REF, 'period_length': 30}),
            ('odomate.account.tax.report.wizard',
             'odomate_account_ledger_reports.action_report_odomate_tax_report',
             {'date_from': D_FROM, 'date_to': D_TO}),
            ('odomate.account.journal.audit.wizard',
             'odomate_account_ledger_reports.action_report_odomate_journal_audit',
             {'date_from': D_FROM, 'date_to': D_TO}),
        ]
        for model, report_xmlid, values in specs:
            wizard = self._wizard(model, values)
            html, content_type = report_env._render_qweb_html(
                report_xmlid, wizard.ids, data=wizard._odomate_report_data()
            )
            self.assertEqual(content_type, 'html')
            self.assertTrue(html)

        entry_html, entry_type = report_env._render_qweb_html(
            'odomate_account_ledger_reports.action_report_odomate_journal_entry',
            self.tax_invoice.ids,
        )
        self.assertEqual(entry_type, 'html')
        self.assertIn(self.tax_invoice.name.encode(), entry_html)

    # ------------------------------------------------------------------
    # R1 fix regression - part-paid invoice keeps its payment row
    # ------------------------------------------------------------------

    def test_part_paid_invoice_prints_its_payment_on_its_own_row(self):
        """R1: a part-paid invoice prints its own row and its payment's own row,
        so the closing balance is what is still outstanding, while Amount owed
        is unchanged."""
        values = self._partner_ledger_values(
            date_from=False,
            date_to=False,
            result_selection='customer',
            reconciled=False,
            partner_ids=[Command.set(self.partners['residual'].ids)],
        )
        block = self._block_by_partner(values, self.partners['residual'])
        self.assertIsNotNone(block)
        self.assertEqual(len(block['rows']), 2)
        self.assertAlmostEqual(block['debit'], 1000.0, places=2)
        self.assertAlmostEqual(block['credit'], 400.0, places=2)
        self.assertAlmostEqual(block['balance'], 600.0, places=2)
        self.assertAlmostEqual(block['amount_owed'], 600.0, places=2)
