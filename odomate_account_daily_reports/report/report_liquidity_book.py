from collections import defaultdict

from odoo import api, models

MULTI_CURRENCY_GROUP = 'base.group_multi_currency'

SORT_ORDERS = {
    'sort_date': 'date, move_name, id',
    'sort_journal_partner': 'journal_id, partner_id, date, id',
}


class ReportOdomateLiquidityBookMixin(models.AbstractModel):
    _name = 'report.odomate_account_daily_reports.report_liquidity_book_mixin'
    _description = "Liquidity Book Report"
    _table = 'odomate_liquidity_book_mixin'

    @api.model
    def _odomate_book_accounts(self, journals, account_types, lines):
        accounts = self.env['account.account'].browse()
        if not journals:
            return accounts
        company = journals.company_id[:1]
        accounts |= journals.default_account_id
        accounts |= journals.suspense_account_id
        for journal in journals:
            accounts |= journal._get_journal_inbound_outstanding_payment_accounts()
            accounts |= journal._get_journal_outbound_outstanding_payment_accounts()
        types = list(account_types)
        if types:
            accounts |= lines.account_id.filtered(
                lambda account: account.account_type in types
            )
        accounts = accounts.filtered(
            lambda account: bool(account.id) and company in account.company_ids
        )
        return accounts.sorted(lambda account: (account.code or '', account.id))

    @api.model
    def _odomate_opening_balances(self, options, accounts):
        if not options['initial_balance'] or not options['date_from'] or not accounts:
            return {}
        report_filter = self.env['odomate.account.report.filter']
        domain = report_filter._odomate_initial_balance_domain(
            options['company'],
            options['date_from'],
            journals=options['journals'],
            target_move=options['target_move'],
        ) + [('account_id', 'in', accounts.ids)]
        openings = {}
        for account, debit, credit, balance in self.env['account.move.line']._read_group(
            domain, ['account_id'], ['debit:sum', 'credit:sum', 'balance:sum']
        ):
            if account:
                openings[account.id] = {
                    'debit': debit,
                    'credit': credit,
                    'balance': balance,
                }
        return openings

    @api.model
    def _odomate_account_block(self, options, account, account_lines, opening, currency, show_currency):
        rows = []
        running = opening['balance'] if opening else 0.0
        if opening:
            rows.append({
                'opening': True,
                'date': False,
                'journal': '',
                'move_name': '',
                'partner': '',
                'ref': '',
                'label': '',
                'debit': opening['debit'],
                'credit': opening['credit'],
                'balance': opening['balance'],
                'amount_currency': 0.0,
                'currency': False,
            })
        for line in account_lines:
            running += line.debit - line.credit
            rows.append({
                'opening': False,
                'date': line.date,
                'journal': line.journal_id.code or line.journal_id.name or '',
                'move_name': line.move_name or '',
                'partner': line.partner_id.display_name or '',
                'ref': line.ref or '',
                'label': line.name or '',
                'debit': line.debit,
                'credit': line.credit,
                'balance': running,
                'amount_currency': line.amount_currency,
                'currency': (
                    line.currency_id
                    if show_currency and line.currency_id != currency
                    else False
                ),
            })
        debit = sum(line.debit for line in account_lines)
        credit = sum(line.credit for line in account_lines)
        return {
            'account': account,
            'account_label': ' '.join(
                part for part in (account.code, account.name) if part
            ),
            'rows': rows,
            'opening': opening['balance'] if opening else 0.0,
            'debit': debit,
            'credit': credit,
            'balance': (opening['balance'] if opening else 0.0) + debit - credit,
        }

    @api.model
    def _odomate_keep_block(self, options, block, account_lines, currency):
        if options['display_account'] == 'movement':
            return bool(account_lines) or not currency.is_zero(block['opening'])
        if options['display_account'] == 'not_zero':
            return not currency.is_zero(block['balance'])
        return True

    @api.model
    def _odomate_daily_header_values(self, options):
        labels = dict(
            self.env['odomate.account.report.filter']
            ._fields['target_move']._description_selection(self.env)
        )
        target_move = options.get('target_move') or 'posted'
        return {
            'company': options['company'],
            'date_from': options['date_from'],
            'date_to': options['date_to'],
            'journals': options['journals'] if options.get('explicit_journals') else False,
            'target_move_label': labels.get(target_move) or labels.get('posted'),
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        report_filter = self.env['odomate.account.report.filter']
        report_filter._odomate_check_report_access()
        options = self.env[
            'odomate.account.liquidity.book.wizard'
        ]._odomate_options_from_data(data)

        company = options['company']
        currency = company.currency_id
        show_currency = (
            self.env.user.has_group(MULTI_CURRENCY_GROUP) and options['amount_currency']
        )

        journals = options['journals']
        base_domain = report_filter._odomate_options_line_domain(options)
        order = SORT_ORDERS.get(options['sortby']) or SORT_ORDERS['sort_date']

        move_line = self.env['account.move.line']
        period_lines = move_line.search(base_domain, order=order)
        accounts = self._odomate_book_accounts(
            journals, options['account_types'], period_lines
        )
        lines = move_line.search(
            base_domain + [('account_id', 'in', accounts.ids)], order=order
        )

        openings = self._odomate_opening_balances(options, accounts)

        grouped = defaultdict(list)
        for line in lines:
            grouped[line.account_id.id].append(line)

        blocks = []
        for account in accounts:
            account_lines = grouped.get(account.id, [])
            block = self._odomate_account_block(
                options,
                account,
                account_lines,
                openings.get(account.id),
                currency,
                show_currency,
            )
            if self._odomate_keep_block(options, block, account_lines, currency):
                blocks.append(block)

        totals = {
            'opening': sum(block['opening'] for block in blocks),
            'debit': sum(block['debit'] for block in blocks),
            'credit': sum(block['credit'] for block in blocks),
            'balance': sum(block['balance'] for block in blocks),
        }

        return {
            'doc_ids': docids,
            'doc_model': options['wizard_model'],
            'data': data,
            'company': company,
            'currency': currency,
            'header': self._odomate_daily_header_values(options),
            'options': options,
            'blocks': blocks,
            'totals': totals,
            'show_currency': show_currency,
        }


class ReportOdomateCashBook(models.AbstractModel):
    _name = 'report.odomate_account_daily_reports.report_cash_book'
    _inherit = ['report.odomate_account_daily_reports.report_liquidity_book_mixin']
    _description = "Cash Book Report"


class ReportOdomateBankBook(models.AbstractModel):
    _name = 'report.odomate_account_daily_reports.report_bank_book'
    _inherit = ['report.odomate_account_daily_reports.report_liquidity_book_mixin']
    _description = "Bank Book Report"
