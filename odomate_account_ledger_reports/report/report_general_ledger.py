from collections import defaultdict

from odoo import api, models

ANALYTIC_GROUP = 'analytic.group_analytic_accounting'
MULTI_CURRENCY_GROUP = 'base.group_multi_currency'

SORT_ORDERS = {
    'sort_date': 'date, move_name, id',
    'sort_journal_partner': 'journal_id, partner_id, date, id',
}


class ReportOdomateGeneralLedger(models.AbstractModel):
    _name = 'report.odomate_account_ledger_reports.report_general_ledger'
    _description = "General Ledger Report"

    @api.model
    def _odomate_narrowing_domain(self, options):
        domain = []
        if options['accounts']:
            domain.append(('account_id', 'in', options['accounts'].ids))
        if options['partners']:
            domain.append(('partner_id', 'in', options['partners'].ids))
        if options['analytic_accounts']:
            domain.append(('analytic_distribution', 'in', options['analytic_accounts'].ids))
        return domain

    @api.model
    def _odomate_opening_balances(self, options, narrowing):
        if not options['initial_balance'] or not options['date_from']:
            return {}
        report_filter = self.env['odomate.account.report.filter']
        domain = report_filter._odomate_initial_balance_domain(
            options['company'],
            options['date_from'],
            journals=options['journals'],
            target_move=options['target_move'],
        ) + narrowing
        openings = {}
        for account, balance in self.env['account.move.line']._read_group(
            domain, ['account_id'], ['balance:sum']
        ):
            if account:
                openings[account.id] = balance
        return openings

    @api.model
    def _odomate_candidate_accounts(self, options, lines, openings):
        accounts = lines.account_id
        if openings:
            accounts |= self.env['account.account'].browse(sorted(openings)).exists()
        if options['display_account'] == 'all':
            domain = [('company_ids', 'in', options['company'].ids)]
            if options['accounts']:
                domain.append(('id', 'in', options['accounts'].ids))
            accounts |= self.env['account.account'].search(domain, order='id')
        return accounts.sorted(lambda account: (account.code or '', account.id))

    @api.model
    def _get_report_values(self, docids, data=None):
        report_filter = self.env['odomate.account.report.filter']
        report_filter._odomate_check_report_access()
        options = self.env[
            'odomate.account.general.ledger.wizard'
        ]._odomate_options_from_data(data)

        company = options['company']
        currency = company.currency_id
        show_currency = self.env.user.has_group(MULTI_CURRENCY_GROUP)
        show_analytic = self.env.user.has_group(ANALYTIC_GROUP)

        narrowing = self._odomate_narrowing_domain(options)
        domain = report_filter._odomate_options_line_domain(options) + narrowing
        order = SORT_ORDERS.get(options['sortby']) or SORT_ORDERS['sort_date']
        lines = self.env['account.move.line'].search(domain, order=order)

        openings = self._odomate_opening_balances(options, narrowing)
        analytic_labels = report_filter._odomate_analytic_labels(lines) if show_analytic else {}

        grouped = defaultdict(list)
        for line in lines:
            grouped[line.account_id.id].append(line)

        blocks = []
        for account in self._odomate_candidate_accounts(options, lines, openings):
            account_lines = grouped.get(account.id, [])
            opening = openings.get(account.id, 0.0)
            debit = sum(line.debit for line in account_lines)
            credit = sum(line.credit for line in account_lines)
            closing = opening + debit - credit

            if options['display_account'] == 'movement':
                if not account_lines and currency.is_zero(opening):
                    continue
            elif options['display_account'] == 'not_zero':
                if currency.is_zero(closing):
                    continue

            rows = []
            running = opening
            if options['initial_balance'] and options['date_from']:
                rows.append({
                    'opening': True,
                    'date': False,
                    'journal': '',
                    'partner': '',
                    'ref': '',
                    'move_name': '',
                    'label': '',
                    'debit': 0.0,
                    'credit': 0.0,
                    'balance': opening,
                    'amount_currency': 0.0,
                    'currency': False,
                    'analytic': '',
                })
            for line in account_lines:
                running += line.balance
                rows.append({
                    'opening': False,
                    'date': line.date,
                    'journal': line.journal_id.code or line.journal_id.name or '',
                    'partner': line.partner_id.display_name or '',
                    'ref': line.ref or '',
                    'move_name': line.move_name or '',
                    'label': line.name or '',
                    'debit': line.debit,
                    'credit': line.credit,
                    'balance': running,
                    'amount_currency': line.amount_currency,
                    'currency': line.currency_id if line.currency_id != currency else False,
                    'analytic': analytic_labels.get(line.id, ''),
                })

            blocks.append({
                'account': account,
                'account_label': report_filter._odomate_account_label(account),
                'rows': rows,
                'opening': opening,
                'debit': debit,
                'credit': credit,
                'balance': closing,
            })

        totals = {
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
            'header': report_filter._odomate_header_values(options),
            'options': options,
            'blocks': blocks,
            'totals': totals,
            'show_currency': show_currency,
            'show_analytic': show_analytic,
        }
