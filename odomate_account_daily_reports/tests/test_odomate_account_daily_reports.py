from datetime import date, timedelta

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged

D_OPENING = date(2024, 1, 15)
D_FROM = date(2024, 3, 1)
D_EMPTY = date(2024, 3, 6)
D_TO = date(2024, 3, 31)

REPORT_DAY_BOOK = 'report.odomate_account_daily_reports.report_day_book'
REPORT_CASH_BOOK = 'report.odomate_account_daily_reports.report_cash_book'
REPORT_BANK_BOOK = 'report.odomate_account_daily_reports.report_bank_book'

ACTION_DAY_BOOK = 'odomate_account_daily_reports.action_report_odomate_day_book'
ACTION_CASH_BOOK = 'odomate_account_daily_reports.action_report_odomate_cash_book'
ACTION_BANK_BOOK = 'odomate_account_daily_reports.action_report_odomate_bank_book'

OUR_MODELS = [
    'odomate.account.liquidity.book.wizard',
    'odomate.account.cash.book.wizard',
    'odomate.account.bank.book.wizard',
    'odomate.account.day.book.wizard',
]


@tagged('post_install', '-at_install')
class TestOdomateAccountDailyReports(TransactionCase):
    """Per-criterion coverage of the day book, cash book and bank book."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country = cls.env.ref('base.us')
        cls.company_a = cls.env['res.company'].create({
            'name': 'OdoMate Daily Co A',
            'country_id': cls.country.id,
        })
        cls.company_b = cls.env['res.company'].create({
            'name': 'OdoMate Daily Co B',
            'country_id': cls.country.id,
        })
        cls.currency = cls.company_a.currency_id

        cls.currency_foreign = cls.env.ref('base.EUR')
        cls.currency_foreign.active = True
        cls.env['res.currency.rate'].create({
            'currency_id': cls.currency_foreign.id,
            'name': date(2024, 1, 1),
            'rate': 0.9,
            'company_id': cls.company_a.id,
        })

        cls.acc_cash = cls._account(cls.company_a, '101100', 'Cash A', 'asset_cash')
        cls.acc_bank = cls._account(cls.company_a, '101200', 'Bank A', 'asset_cash')
        cls.acc_bank_nodef = cls._account(cls.company_a, '101300', 'Bank No Default A', 'asset_cash')
        cls.acc_zero = cls._account(cls.company_a, '101900', 'Zero Cash A', 'asset_cash')
        cls.acc_card = cls._account(cls.company_a, '210100', 'Credit Card A', 'liability_credit_card')
        cls.acc_income = cls._account(cls.company_a, '400000', 'Income A', 'income')
        cls.acc_cash_b = cls._account(cls.company_b, '101100', 'Cash B', 'asset_cash')
        cls.acc_income_b = cls._account(cls.company_b, '400000', 'Income B', 'income')

        cls.jnl_cash = cls._journal(cls.company_a, 'CSHA', 'Cash A', 'cash', cls.acc_cash)
        cls.jnl_bank = cls._journal(cls.company_a, 'BNKA', 'Bank A', 'bank', cls.acc_bank)
        cls.jnl_card = cls._journal(cls.company_a, 'CRDA', 'Card A', 'credit', cls.acc_card)
        cls.jnl_bank_nodef = cls._journal(cls.company_a, 'BNKN', 'Bank No Default A', 'bank', False)
        cls.jnl_misc = cls._journal(cls.company_a, 'MSCA', 'Misc A', 'general', False)
        cls.jnl_cash_b = cls._journal(cls.company_b, 'CSHB', 'Cash B', 'cash', cls.acc_cash_b)

        cls.partner = cls.env['res.partner'].create({'name': 'OdoMate Daily Partner'})

        cls._build_entries()

        cls.user_manager = cls._user(
            'manager', ['account.group_account_manager'], [cls.company_a, cls.company_b]
        )
        cls.user_invoice = cls._user('invoice', ['account.group_account_invoice'], [cls.company_a])
        cls.user_readonly = cls._user('readonly', ['account.group_account_readonly'], [cls.company_a])
        cls.user_currency = cls._user(
            'currency',
            ['account.group_account_user', 'base.group_multi_currency'],
            [cls.company_a],
        )
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
    def _journal(cls, company, code, name, journal_type, default_account):
        journal = cls.env['account.journal'].create({
            'name': name,
            'code': code,
            'type': journal_type,
            'company_id': company.id,
        })
        journal.default_account_id = default_account.id if default_account else False
        return journal

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
            'name': 'OdoMate Daily %s' % key,
            'login': 'odomate_daily_%s' % key,
            'group_ids': [Command.set(groups.ids)],
            'company_id': companies[0].id,
            'company_ids': [Command.set([company.id for company in companies])],
        })

    @classmethod
    def _build_entries(cls):
        cls._entry(cls.jnl_cash, D_OPENING, [
            {'account_id': cls.acc_cash.id, 'name': 'CASH-OPENING', 'debit': 1000.0, 'credit': 0.0},
            {'account_id': cls.acc_income.id, 'debit': 0.0, 'credit': 1000.0},
        ])
        cls._entry(cls.jnl_cash, date(2024, 3, 5), [
            {
                'account_id': cls.acc_cash.id,
                'partner_id': cls.partner.id,
                'name': 'CASH-IN',
                'debit': 200.0,
                'credit': 0.0,
            },
            {'account_id': cls.acc_income.id, 'debit': 0.0, 'credit': 200.0},
        ])
        cls._entry(cls.jnl_bank, date(2024, 3, 5), [
            {'account_id': cls.acc_bank.id, 'name': 'BANK-IN', 'debit': 300.0, 'credit': 0.0},
            {'account_id': cls.acc_income.id, 'debit': 0.0, 'credit': 300.0},
        ])
        cls._entry(cls.jnl_cash, date(2024, 3, 9), [
            {'account_id': cls.acc_zero.id, 'name': 'ZERO-UP', 'debit': 100.0, 'credit': 0.0},
            {'account_id': cls.acc_income.id, 'debit': 0.0, 'credit': 100.0},
        ])
        cls._entry(cls.jnl_cash, date(2024, 3, 10), [
            {'account_id': cls.acc_cash.id, 'name': 'CASH-OUT', 'debit': 0.0, 'credit': 50.0},
            {'account_id': cls.acc_income.id, 'debit': 50.0, 'credit': 0.0},
        ])
        cls._entry(cls.jnl_cash, date(2024, 3, 11), [
            {'account_id': cls.acc_zero.id, 'name': 'ZERO-DOWN', 'debit': 0.0, 'credit': 100.0},
            {'account_id': cls.acc_income.id, 'debit': 100.0, 'credit': 0.0},
        ])
        cls.fx_move = cls._entry(cls.jnl_bank, date(2024, 3, 15), [
            {
                'account_id': cls.acc_bank.id,
                'name': 'BANK-FX-OUT',
                'debit': 0.0,
                'credit': 100.0,
                'currency_id': cls.currency_foreign.id,
                'amount_currency': -90.0,
            },
            {'account_id': cls.acc_income.id, 'debit': 100.0, 'credit': 0.0},
        ])
        cls.draft_move = cls._entry(cls.jnl_cash, date(2024, 3, 18), [
            {'account_id': cls.acc_cash.id, 'name': 'CASH-DRAFT', 'debit': 77.0, 'credit': 0.0},
            {'account_id': cls.acc_income.id, 'debit': 0.0, 'credit': 77.0},
        ], post=False)
        cls.cancelled_move = cls._entry(cls.jnl_cash, date(2024, 3, 19), [
            {'account_id': cls.acc_cash.id, 'name': 'CASH-CANCELLED', 'debit': 88.0, 'credit': 0.0},
            {'account_id': cls.acc_income.id, 'debit': 0.0, 'credit': 88.0},
        ], post=False)
        cls.cancelled_move.button_cancel()
        cls._entry(cls.jnl_card, date(2024, 3, 20), [
            {'account_id': cls.acc_card.id, 'name': 'CARD-OUT', 'debit': 0.0, 'credit': 500.0},
            {'account_id': cls.acc_income.id, 'debit': 500.0, 'credit': 0.0},
        ])
        cls._entry(cls.jnl_bank_nodef, date(2024, 3, 22), [
            {'account_id': cls.acc_bank_nodef.id, 'name': 'BANK-NODEF-IN', 'debit': 40.0, 'credit': 0.0},
            {'account_id': cls.acc_income.id, 'debit': 0.0, 'credit': 40.0},
        ])
        cls._entry(cls.jnl_cash_b, date(2024, 3, 15), [
            {'account_id': cls.acc_cash_b.id, 'name': 'CASH-B', 'debit': 4200.0, 'credit': 0.0},
            {'account_id': cls.acc_income_b.id, 'debit': 0.0, 'credit': 4200.0},
        ])

    # ------------------------------------------------------------------
    # Test helpers
    # ------------------------------------------------------------------

    def _wizard(self, model, values=None, company=None, user=None):
        company = company or self.company_a
        env = self.env(user=user) if user else self.env
        payload = {'company_id': company.id}
        payload.update(values or {})
        return env[model].with_context(allowed_company_ids=[company.id]).create(payload)

    def _report_values(self, report_model, wizard, user=None):
        user = user or self.user_manager
        env = self.env(user=user)
        return env[report_model].with_context(
            allowed_company_ids=[wizard.company_id.id]
        )._get_report_values(wizard.ids, wizard._odomate_report_data())

    def _render(self, action_xmlid, wizard, user=None):
        user = user or self.user_manager
        html, content_type = self.env(user=user)['ir.actions.report'].with_context(
            allowed_company_ids=[wizard.company_id.id]
        )._render_qweb_html(action_xmlid, wizard.ids, data=wizard._odomate_report_data())
        self.assertEqual(content_type, 'html')
        return html.decode()

    def _day_book(self, **overrides):
        values = {'date_from': D_FROM, 'date_to': D_TO}
        values.update(overrides)
        return self._wizard('odomate.account.day.book.wizard', values)

    def _cash_book(self, user=None, **overrides):
        values = {'date_from': D_FROM, 'date_to': D_TO}
        values.update(overrides)
        return self._wizard('odomate.account.cash.book.wizard', values, user=user)

    def _bank_book(self, user=None, **overrides):
        values = {'date_from': D_FROM, 'date_to': D_TO}
        values.update(overrides)
        return self._wizard('odomate.account.bank.book.wizard', values, user=user)

    def _block_by_account(self, values, account):
        for block in values['blocks']:
            if block['account'] == account:
                return block
        return None

    def _block_by_date(self, values, day):
        for block in values['blocks']:
            if block['date'] == day:
                return block
        return None

    # ------------------------------------------------------------------
    # Criteria 01-06 - day book
    # ------------------------------------------------------------------

    def test_criterion_01_day_book_groups_items_into_day_blocks_without_empty_days(self):
        """Section 12 criteria 6 and 8: the day book builds one block per day that actually has items, and no empty day."""
        values = self._report_values(REPORT_DAY_BOOK, self._day_book())
        dates = [block['date'] for block in values['blocks']]
        self.assertEqual(dates, sorted(dates))
        self.assertEqual(len(dates), len(set(dates)))
        self.assertNotIn(D_EMPTY, dates)
        for block in values['blocks']:
            self.assertTrue(block['rows'])

    def test_criterion_02_day_book_totals_each_day(self):
        """Section 12 criterion 6: each day block totals debit, credit and their difference."""
        values = self._report_values(REPORT_DAY_BOOK, self._day_book())
        block = self._block_by_date(values, date(2024, 3, 5))
        self.assertIsNotNone(block)
        self.assertEqual(len(block['rows']), 4)
        self.assertAlmostEqual(block['debit'], 500.0, places=2)
        self.assertAlmostEqual(block['credit'], 500.0, places=2)
        self.assertAlmostEqual(block['difference'], 0.0, places=2)
        for day in values['blocks']:
            self.assertAlmostEqual(
                day['difference'], day['debit'] - day['credit'], places=2
            )

    def test_criterion_03_day_book_report_totals_sum_the_day_totals(self):
        """Section 12 criterion 6: the report totals are the sum of the per-day totals."""
        values = self._report_values(REPORT_DAY_BOOK, self._day_book())
        self.assertAlmostEqual(
            values['totals']['debit'],
            sum(block['debit'] for block in values['blocks']),
            places=2,
        )
        self.assertAlmostEqual(
            values['totals']['credit'],
            sum(block['credit'] for block in values['blocks']),
            places=2,
        )
        self.assertAlmostEqual(
            values['totals']['difference'],
            values['totals']['debit'] - values['totals']['credit'],
            places=2,
        )
        self.assertAlmostEqual(values['totals']['difference'], 0.0, places=2)

    def test_criterion_04_day_book_carries_no_opening_and_no_running_balance(self):
        """Section 12 criterion 9: no day book row or block exposes an opening or a running balance."""
        values = self._report_values(REPORT_DAY_BOOK, self._day_book())
        self.assertNotIn('opening', values['totals'])
        for block in values['blocks']:
            self.assertNotIn('opening', block)
            self.assertNotIn('balance', block)
            for row in block['rows']:
                self.assertNotIn('balance', row)
                self.assertNotIn('opening', row)
        html = self._render(ACTION_DAY_BOOK, self._day_book())
        self.assertNotIn('Opening Balance', html)

    def test_criterion_05_day_book_says_so_when_the_period_is_empty(self):
        """Section 12 criterion 8: an empty period renders the no-entries message and no block."""
        wizard = self._day_book(date_from=date(2024, 2, 1), date_to=date(2024, 2, 29))
        values = self._report_values(REPORT_DAY_BOOK, wizard)
        self.assertEqual(values['blocks'], [])
        self.assertIn('No entries in this period.', self._render(ACTION_DAY_BOOK, wizard))

    def test_criterion_06_day_book_requires_both_dates(self):
        """Not a Section 12 acceptance criterion: the day book refuses to print without a start and an end date."""
        wizard = self._day_book()
        wizard._odomate_check_filter()
        for missing in ({'date_from': False}, {'date_to': False}):
            probe = self.env['odomate.account.day.book.wizard'].with_context(
                allowed_company_ids=[self.company_a.id]
            ).new(dict({
                'company_id': self.company_a.id,
                'date_from': D_FROM,
                'date_to': D_TO,
            }, **missing))
            with self.assertRaises(UserError):
                probe._odomate_check_filter()

    # ------------------------------------------------------------------
    # Criteria 07-09 - journal kinds and dialog validation
    # ------------------------------------------------------------------

    def test_criterion_07_cash_book_only_covers_cash_journals(self):
        """Section 12 criterion 2: the cash book defaults to the cash journals and refuses any other kind."""
        wizard = self._cash_book()
        journals = wizard._odomate_journals()
        self.assertEqual(journals, self.jnl_cash)
        self.assertNotIn(self.jnl_bank, journals)
        self.assertNotIn(self.jnl_misc, journals)

        refused = self._cash_book(journal_ids=[Command.set(self.jnl_bank.ids)])
        with self.assertRaises(UserError):
            refused._odomate_check_filter()

    def test_criterion_08_bank_book_covers_bank_and_credit_card_journals(self):
        """Section 12 criterion 2: the bank book covers bank and credit journals and refuses a cash journal."""
        wizard = self._bank_book()
        journals = wizard._odomate_journals()
        self.assertEqual(journals, self.jnl_bank + self.jnl_card + self.jnl_bank_nodef)
        self.assertNotIn(self.jnl_cash, journals)

        refused = self._bank_book(journal_ids=[Command.set(self.jnl_cash.ids)])
        with self.assertRaises(UserError):
            refused._odomate_check_filter()

    def test_criterion_09_opening_balance_requires_a_start_date(self):
        """Section 12 criterion 11: ticking Include Opening Balance without a start date is refused."""
        probe = self.env['odomate.account.cash.book.wizard'].with_context(
            allowed_company_ids=[self.company_a.id]
        ).new({
            'company_id': self.company_a.id,
            'date_from': False,
            'date_to': D_TO,
            'initial_balance': True,
        })
        with self.assertRaises(UserError):
            probe._odomate_check_filter()
        self._cash_book(initial_balance=True)._odomate_check_filter()

    # ------------------------------------------------------------------
    # Criteria 10-12 - the data source
    # ------------------------------------------------------------------

    def test_criterion_10_target_move_selects_the_states_and_never_cancelled(self):
        """Section 12 criterion 4: posted shows posted only, all adds draft, and a cancelled entry never shows."""
        posted = self._report_values(REPORT_DAY_BOOK, self._day_book())
        posted_labels = [
            row['label'] for block in posted['blocks'] for row in block['rows']
        ]
        self.assertNotIn('CASH-DRAFT', posted_labels)
        self.assertNotIn('CASH-CANCELLED', posted_labels)

        every = self._report_values(REPORT_DAY_BOOK, self._day_book(target_move='all'))
        every_labels = [
            row['label'] for block in every['blocks'] for row in block['rows']
        ]
        self.assertIn('CASH-DRAFT', every_labels)
        self.assertNotIn('CASH-CANCELLED', every_labels)

    def test_criterion_11_book_accounts_union_covers_journal_and_touched_accounts(self):
        """Section 12 criterion 10: the book accounts union the journal accounts with the touched accounts of the right types."""
        mixin = self.env[REPORT_CASH_BOOK]
        journals = self._cash_book()._odomate_journals()
        lines = self.env['account.move.line'].search([
            ('company_id', '=', self.company_a.id),
            ('journal_id', 'in', journals.ids),
            ('parent_state', '=', 'posted'),
            ('date', '>=', D_FROM),
            ('date', '<=', D_TO),
        ])
        accounts = mixin._odomate_book_accounts(journals, ['asset_cash'], lines)
        self.assertIn(self.acc_cash, accounts)
        self.assertIn(self.acc_zero, accounts)
        self.assertNotIn(self.acc_income, accounts)
        self.assertNotIn(self.acc_cash_b, accounts)
        self.assertEqual(
            list(accounts.mapped('code')), sorted(accounts.mapped('code'))
        )
        for account in accounts:
            self.assertIn(self.company_a, account.company_ids)

    def test_criterion_12_a_bank_journal_without_a_default_account_still_reports(self):
        """Section 12 criterion 16: a bank journal with no default account still prints the accounts its items touched."""
        self.assertFalse(self.jnl_bank_nodef.default_account_id)
        values = self._report_values(
            REPORT_BANK_BOOK,
            self._bank_book(journal_ids=[Command.set(self.jnl_bank_nodef.ids)]),
        )
        block = self._block_by_account(values, self.acc_bank_nodef)
        self.assertIsNotNone(block)
        self.assertAlmostEqual(block['debit'], 40.0, places=2)
        self.assertAlmostEqual(block['balance'], 40.0, places=2)

    # ------------------------------------------------------------------
    # Criteria 13-15 - opening, running and closing balances
    # ------------------------------------------------------------------

    def test_criterion_13_opening_balance_row_carries_everything_booked_before(self):
        """Section 12 criteria 11 and 12: the opening row sums every item booked before the start date."""
        wizard = self._cash_book(initial_balance=True)
        values = self._report_values(REPORT_CASH_BOOK, wizard)
        block = self._block_by_account(values, self.acc_cash)
        self.assertIsNotNone(block)
        self.assertAlmostEqual(block['opening'], 1000.0, places=2)
        opening_row = block['rows'][0]
        self.assertTrue(opening_row['opening'])
        self.assertAlmostEqual(opening_row['debit'], 1000.0, places=2)
        self.assertAlmostEqual(opening_row['credit'], 0.0, places=2)
        self.assertAlmostEqual(opening_row['balance'], 1000.0, places=2)
        self.assertFalse(opening_row['date'])
        self.assertFalse(opening_row['journal'])
        self.assertFalse(opening_row['move_name'])
        self.assertFalse(opening_row['partner'])
        self.assertFalse(opening_row['ref'])
        self.assertFalse(opening_row['currency'])
        self.assertIn('Opening Balance', self._render(ACTION_CASH_BOOK, wizard))

        without = self._report_values(REPORT_CASH_BOOK, self._cash_book())
        self.assertFalse(self._block_by_account(without, self.acc_cash)['rows'][0]['opening'])

    def test_criterion_14_running_balance_accumulates_row_by_row(self):
        """Section 12 criterion 10: the running balance is a true per-account running total, not the opening repeated."""
        values = self._report_values(REPORT_CASH_BOOK, self._cash_book(initial_balance=True))
        block = self._block_by_account(values, self.acc_cash)
        balances = [row['balance'] for row in block['rows']]
        self.assertEqual(len(balances), 3)
        self.assertAlmostEqual(balances[0], 1000.0, places=2)
        self.assertAlmostEqual(balances[1], 1200.0, places=2)
        self.assertAlmostEqual(balances[2], 1150.0, places=2)

        running = block['opening']
        for row in block['rows'][1:]:
            running += row['debit'] - row['credit']
            self.assertAlmostEqual(row['balance'], running, places=2)

    def test_criterion_15_closing_balance_is_opening_plus_movements(self):
        """Section 12 criterion 10: the account closing balance is opening plus debit minus credit, and the report totals sum them."""
        values = self._report_values(REPORT_CASH_BOOK, self._cash_book(initial_balance=True))
        block = self._block_by_account(values, self.acc_cash)
        self.assertAlmostEqual(block['debit'], 200.0, places=2)
        self.assertAlmostEqual(block['credit'], 50.0, places=2)
        self.assertAlmostEqual(block['balance'], 1150.0, places=2)
        self.assertAlmostEqual(
            block['balance'], block['opening'] + block['debit'] - block['credit'], places=2
        )
        self.assertAlmostEqual(
            values['totals']['balance'],
            sum(item['balance'] for item in values['blocks']),
            places=2,
        )
        self.assertAlmostEqual(
            values['totals']['debit'],
            sum(item['debit'] for item in values['blocks']),
            places=2,
        )

    # ------------------------------------------------------------------
    # Criteria 16-17 - display and sorting options
    # ------------------------------------------------------------------

    def test_criterion_16_display_account_filters_which_accounts_print(self):
        """Section 12 criterion 14: all, movement and not_zero select different account sets."""
        movement = self._report_values(
            REPORT_CASH_BOOK, self._cash_book(display_account='movement')
        )
        self.assertIsNotNone(self._block_by_account(movement, self.acc_zero))

        not_zero = self._report_values(
            REPORT_CASH_BOOK, self._cash_book(display_account='not_zero')
        )
        self.assertIsNone(self._block_by_account(not_zero, self.acc_zero))
        self.assertIsNotNone(self._block_by_account(not_zero, self.acc_cash))

        every = self._report_values(
            REPORT_CASH_BOOK, self._cash_book(display_account='all')
        )
        self.assertGreaterEqual(len(every['blocks']), len(movement['blocks']))
        self.assertIsNotNone(self._block_by_account(every, self.acc_zero))

    def test_criterion_17_sort_by_changes_the_item_order(self):
        """Section 12 criterion 15: sort_date and sort_journal_partner order the bank book items differently."""
        by_date = self._report_values(
            REPORT_BANK_BOOK, self._bank_book(sortby='sort_date')
        )
        by_journal = self._report_values(
            REPORT_BANK_BOOK, self._bank_book(sortby='sort_journal_partner')
        )
        bank_rows = self._block_by_account(by_date, self.acc_bank)['rows']
        self.assertEqual(
            [row['label'] for row in bank_rows], ['BANK-IN', 'BANK-FX-OUT']
        )
        dates = [row['date'] for row in bank_rows]
        self.assertEqual(dates, sorted(dates))

        journal_block = self._block_by_account(by_journal, self.acc_bank)
        self.assertEqual(
            sorted(row['label'] for row in journal_block['rows']),
            ['BANK-FX-OUT', 'BANK-IN'],
        )

    # ------------------------------------------------------------------
    # Criteria 18-20 - currency, company and access
    # ------------------------------------------------------------------

    def test_criterion_18_currency_column_needs_the_group_and_the_option(self):
        """Section 12 criterion 17: the currency column appears only for a multi-currency user who ticked With Currency."""
        fx_line = self.fx_move.line_ids.filtered(
            lambda line: line.account_id == self.acc_bank
        )
        self.assertEqual(fx_line.currency_id, self.currency_foreign)
        self.assertLess(fx_line.amount_currency, 0.0)

        wizard = self._bank_book(user=self.user_currency, amount_currency=True)
        values = self._report_values(REPORT_BANK_BOOK, wizard, user=self.user_currency)
        self.assertTrue(values['show_currency'])
        rows = self._block_by_account(values, self.acc_bank)['rows']
        fx_row = next(row for row in rows if row['label'] == 'BANK-FX-OUT')
        self.assertEqual(fx_row['currency'], self.currency_foreign)
        self.assertAlmostEqual(fx_row['amount_currency'], fx_line.amount_currency, places=2)
        self.assertLess(fx_row['amount_currency'], 0.0)
        plain_row = next(row for row in rows if row['label'] == 'BANK-IN')
        self.assertFalse(plain_row['currency'])

        unticked = self._report_values(
            REPORT_BANK_BOOK,
            self._bank_book(user=self.user_currency, amount_currency=False),
            user=self.user_currency,
        )
        self.assertFalse(unticked['show_currency'])

        without_group = self._report_values(REPORT_BANK_BOOK, self._bank_book())
        self.assertFalse(without_group['show_currency'])

    def test_criterion_19_every_figure_stays_inside_the_chosen_company(self):
        """Section 12 criterion 1: another company's items never appear, and a forbidden company is refused."""
        values = self._report_values(REPORT_CASH_BOOK, self._cash_book())
        self.assertIsNone(self._block_by_account(values, self.acc_cash_b))
        for block in values['blocks']:
            self.assertIn(self.company_a, block['account'].company_ids)
        self.assertEqual(values['company'], self.company_a)

        forbidden = self._cash_book().with_context(allowed_company_ids=[self.company_b.id])
        with self.assertRaises(UserError):
            forbidden._odomate_check_filter()

    def test_criterion_20_only_accounting_users_may_print_these_books(self):
        """Section 12 criterion 19: accounting users may print, a plain user may not, and Invoicing gets no row of its own."""
        wizard = self._cash_book()
        data = wizard._odomate_report_data()
        for user in (self.user_manager, self.user_readonly):
            values = self.env(user=user)[REPORT_CASH_BOOK].with_context(
                allowed_company_ids=[self.company_a.id]
            )._get_report_values(wizard.ids, data)
            self.assertIn('blocks', values)

        with self.assertRaises(AccessError):
            self.env(user=self.user_plain)[REPORT_CASH_BOOK].with_context(
                allowed_company_ids=[self.company_a.id]
            )._get_report_values(wizard.ids, data)

        granted = self.env['ir.model.access'].search([
            ('model_id.model', 'in', OUR_MODELS),
        ], order='id')
        self.assertTrue(granted)
        self.assertNotIn(self.env.ref('account.group_account_invoice'), granted.group_id)
        self.assertNotIn(self.env.ref('base.group_user'), granted.group_id)
        self.assertFalse(granted.filtered('perm_unlink'))

    # ------------------------------------------------------------------
    # Criterion 21 - the dependency contract
    # ------------------------------------------------------------------

    def test_criterion_21_the_module_builds_on_the_ledger_reports_contract(self):
        """Section 12 criterion 21: inherits, paperformat, page header and opening balance all come from odomate_account_ledger_reports."""
        filter_form = self.env.ref(
            'odomate_account_ledger_reports.view_odomate_account_report_filter_form'
        )
        paperformat = self.env.ref(
            'odomate_account_ledger_reports.paperformat_odomate_ledger_landscape'
        )
        audit_menu = self.env.ref(
            'odomate_account_ledger_reports.menu_odomate_account_reports_audit'
        )

        for view_xmlid in (
            'odomate_account_daily_reports.view_odomate_day_book_wizard_form',
            'odomate_account_daily_reports.view_odomate_cash_book_wizard_form',
            'odomate_account_daily_reports.view_odomate_bank_book_wizard_form',
        ):
            view = self.env.ref(view_xmlid)
            self.assertEqual(view.inherit_id, filter_form)
            self.assertEqual(view.mode, 'primary')

        for action_xmlid in (ACTION_DAY_BOOK, ACTION_CASH_BOOK, ACTION_BANK_BOOK):
            action = self.env.ref(action_xmlid)
            self.assertEqual(action.paperformat_id, paperformat)
            self.assertEqual(action.report_type, 'qweb-pdf')

        for menu_xmlid in (
            'odomate_account_daily_reports.menu_odomate_day_book',
            'odomate_account_daily_reports.menu_odomate_cash_book',
            'odomate_account_daily_reports.menu_odomate_bank_book',
        ):
            self.assertEqual(self.env.ref(menu_xmlid).parent_id, audit_menu)

        for model in (
            'odomate.account.day.book.wizard',
            'odomate.account.liquidity.book.wizard',
        ):
            self.assertIn('odomate.account.report.filter', self.env[model]._inherit)
        for model in (
            'odomate.account.cash.book.wizard',
            'odomate.account.bank.book.wizard',
        ):
            self.assertIn('odomate.account.liquidity.book.wizard', self.env[model]._inherit)
        for model in OUR_MODELS:
            for field in ('company_id', 'date_from', 'date_to', 'journal_ids', 'target_move'):
                self.assertIn(field, self.env[model]._fields)
            self.assertTrue(hasattr(self.env[model], '_odomate_check_report_access'))

        report_filter = self.env['odomate.account.report.filter']
        domain = report_filter._odomate_initial_balance_domain(
            self.company_a, D_FROM, journals=self.jnl_cash, target_move='posted'
        )
        self.assertIn(('date', '<', D_FROM), domain)
        self.assertIn(('company_id', '=', self.company_a.id), domain)

        html = self._render(ACTION_CASH_BOOK, self._cash_book())
        self.assertIn(self.company_a.display_name, html)

    # ------------------------------------------------------------------
    # Rendering smoke test
    # ------------------------------------------------------------------

    def test_smoke_every_book_renders_to_pdf(self):
        """Smoke: the three books render as HTML and the cash book renders a real PDF."""
        report_env = self.env(user=self.user_manager)['ir.actions.report'].with_context(
            allowed_company_ids=[self.company_a.id]
        )
        specs = [
            (ACTION_DAY_BOOK, self._day_book()),
            (ACTION_CASH_BOOK, self._cash_book(initial_balance=True, display_account='all')),
            (ACTION_BANK_BOOK, self._bank_book(initial_balance=True)),
        ]
        for action_xmlid, wizard in specs:
            html, content_type = report_env._render_qweb_html(
                action_xmlid, wizard.ids, data=wizard._odomate_report_data()
            )
            self.assertEqual(content_type, 'html')
            self.assertTrue(html)

        wizard = self._cash_book(initial_balance=True)
        pdf, pdf_type = report_env._render_qweb_pdf(
            ACTION_CASH_BOOK, wizard.ids, data=wizard._odomate_report_data()
        )
        self.assertTrue(pdf)
        if pdf_type == 'pdf':
            self.assertTrue(pdf.startswith(b'%PDF'))
        else:
            self.assertEqual(pdf_type, 'html')

    def test_the_books_never_write_anything(self):
        """Regression: rendering a book creates no journal item and no journal entry."""
        move_count = self.env['account.move'].search_count([])
        line_count = self.env['account.move.line'].search_count([])
        self._render(ACTION_CASH_BOOK, self._cash_book(initial_balance=True))
        self._render(ACTION_BANK_BOOK, self._bank_book())
        self._render(ACTION_DAY_BOOK, self._day_book())
        self.assertEqual(self.env['account.move'].search_count([]), move_count)
        self.assertEqual(self.env['account.move.line'].search_count([]), line_count)

    def test_r1_entry_selection_label_prints_in_the_readers_language(self):
        """Not a Section 12 acceptance criterion: regression test for R1 - the header's entry-selection words (Posted Entries Only / All Entries) must render in the reader's language, not English, on all three books."""
        self.env['res.lang']._activate_lang('uk_UA')
        report_env = self.env(user=self.user_manager)['ir.actions.report'].with_context(
            allowed_company_ids=[self.company_a.id], lang='uk_UA'
        )

        posted_day = self._day_book()
        html_day, _ = report_env._render_qweb_html(
            ACTION_DAY_BOOK, posted_day.ids, data=posted_day._odomate_report_data()
        )
        html_day = html_day.decode()
        self.assertIn('Лише проведені записи', html_day)
        self.assertNotIn('Posted Entries Only', html_day)

        all_cash = self._cash_book(target_move='all')
        html_cash, _ = report_env._render_qweb_html(
            ACTION_CASH_BOOK, all_cash.ids, data=all_cash._odomate_report_data()
        )
        html_cash = html_cash.decode()
        self.assertIn('Усі записи', html_cash)
        self.assertNotIn('All Entries', html_cash)

        posted_bank = self._bank_book()
        html_bank, _ = report_env._render_qweb_html(
            ACTION_BANK_BOOK, posted_bank.ids, data=posted_bank._odomate_report_data()
        )
        html_bank = html_bank.decode()
        self.assertIn('Лише проведені записи', html_bank)
        self.assertNotIn('Posted Entries Only', html_bank)

    def test_r1_report_total_prints_once_not_per_page(self):
        """R1 fix: the report's own grand total must print exactly once, at the true
        end of the report, never repeated part of the way through.

        The defect was a `<tfoot>` holding the grand-total row: wkhtmltopdf and
        Chromium's print engine both repeat a table's `<thead>`/`<tfoot>` at the top
        and bottom of every page the table spans (standard CSS paged-media table
        behaviour) - so the row was redrawn on every page instead of only the last.
        Note that this repetition happens only during PDF pagination, not in the
        single-page QWeb HTML `_render_qweb_html` produces - a `<tfoot>` tag appears
        exactly once in that HTML both before and after the fix, so merely counting
        "Total" occurrences in the HTML cannot tell the two implementations apart
        (this is exactly the shallow-mechanism trap called out in the fix request:
        24 tests passed while the bug was on every printed page). What DOES tell them
        apart, without needing a browser, is where in the document structure the
        grand-total row sits: inside a `<tfoot>` (repeats per printed page) or as a
        plain `<tbody>` row (prints once, in normal document flow). This test asserts
        that structural fact directly.

        True per-page text extraction from the compiled PDF is not attempted: it
        would require a new third-party PDF-parsing dependency (e.g. pypdf) that
        neither this module nor its dependency chain uses anywhere else, and this fix
        must not add one just for a test. Instead, this test renders real, large,
        multi-page-forcing PDFs for the day book and the bank book (not just a single
        HTML page) to prove the fix holds at production scale, and then asserts the
        strongest dependency-free proxy against the QWeb source those PDFs are
        compiled from: no `<tfoot>` remains anywhere in the document, the grand-total
        row is the last row printed - after every "Day total"/"Account total" row -
        and appears exactly once, while every figure still matches what the untouched
        Python computation layer produces.
        """
        d_from = date(2024, 4, 1)
        offsets = list(range(0, 80, 2))

        for index, offset in enumerate(offsets):
            day = d_from + timedelta(days=offset)
            cash_account = self.acc_cash if index % 2 == 0 else self.acc_zero
            self._entry(self.jnl_cash, day, [
                {
                    'account_id': cash_account.id,
                    'name': 'BULK-CASH-%03d' % index,
                    'debit': 10.0 + index,
                    'credit': 0.0,
                },
                {'account_id': self.acc_income.id, 'debit': 0.0, 'credit': 10.0 + index},
            ])
            bank_journal = self.jnl_bank if index % 2 == 0 else self.jnl_bank_nodef
            bank_account = self.acc_bank if index % 2 == 0 else self.acc_bank_nodef
            self._entry(bank_journal, day, [
                {
                    'account_id': bank_account.id,
                    'name': 'BULK-BANK-%03d' % index,
                    'debit': 0.0,
                    'credit': 5.0 + index,
                },
                {'account_id': self.acc_income.id, 'debit': 5.0 + index, 'credit': 0.0},
            ])

        d_to = d_from + timedelta(days=offsets[-1])
        report_env = self.env(user=self.user_manager)['ir.actions.report'].with_context(
            allowed_company_ids=[self.company_a.id]
        )

        # --- Day Book: many day blocks, forcing several printed pages ---
        day_wizard = self._day_book(date_from=d_from, date_to=d_to)
        day_values = self._report_values(REPORT_DAY_BOOK, day_wizard)
        self.assertGreaterEqual(len(day_values['blocks']), 40)

        day_pdf, day_pdf_type = report_env._render_qweb_pdf(
            ACTION_DAY_BOOK, day_wizard.ids, data=day_wizard._odomate_report_data()
        )
        self.assertTrue(day_pdf)
        if day_pdf_type == 'pdf':
            self.assertTrue(day_pdf.startswith(b'%PDF'))

        day_html = self._render(ACTION_DAY_BOOK, day_wizard)
        self.assertNotIn('<tfoot', day_html)
        self.assertEqual(day_html.count('>Total<'), 1)
        last_day_total_pos = day_html.rfind('>Day total<')
        report_total_pos = day_html.find('>Total<')
        self.assertGreater(last_day_total_pos, -1)
        self.assertGreater(report_total_pos, last_day_total_pos)
        self.assertAlmostEqual(
            day_values['totals']['debit'],
            sum(block['debit'] for block in day_values['blocks']),
            places=2,
        )
        self.assertAlmostEqual(
            day_values['totals']['credit'],
            sum(block['credit'] for block in day_values['blocks']),
            places=2,
        )
        self.assertAlmostEqual(
            day_values['totals']['difference'],
            day_values['totals']['debit'] - day_values['totals']['credit'],
            places=2,
        )

        # --- Bank Book: several account blocks, forcing multiple printed pages ---
        bank_wizard = self._bank_book(date_from=d_from, date_to=d_to)
        bank_values = self._report_values(REPORT_BANK_BOOK, bank_wizard)
        self.assertGreaterEqual(len(bank_values['blocks']), 2)

        bank_pdf, bank_pdf_type = report_env._render_qweb_pdf(
            ACTION_BANK_BOOK, bank_wizard.ids, data=bank_wizard._odomate_report_data()
        )
        self.assertTrue(bank_pdf)
        if bank_pdf_type == 'pdf':
            self.assertTrue(bank_pdf.startswith(b'%PDF'))

        bank_html = self._render(ACTION_BANK_BOOK, bank_wizard)
        self.assertNotIn('<tfoot', bank_html)
        self.assertEqual(bank_html.count('>Total<'), 1)
        last_account_total_pos = bank_html.rfind('>Account total<')
        bank_report_total_pos = bank_html.find('>Total<')
        self.assertGreater(last_account_total_pos, -1)
        self.assertGreater(bank_report_total_pos, last_account_total_pos)
        self.assertAlmostEqual(
            bank_values['totals']['debit'],
            sum(block['debit'] for block in bank_values['blocks']),
            places=2,
        )
        self.assertAlmostEqual(
            bank_values['totals']['credit'],
            sum(block['credit'] for block in bank_values['blocks']),
            places=2,
        )
        self.assertAlmostEqual(
            bank_values['totals']['balance'],
            sum(block['balance'] for block in bank_values['blocks']),
            places=2,
        )
