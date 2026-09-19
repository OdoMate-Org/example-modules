from odoo import api, models

MULTI_CURRENCY_GROUP = 'base.group_multi_currency'

SORT_ORDERS = {
    'date': 'date, move_name, id',
    'move_name': 'move_name, date, id',
}


class ReportOdomateJournalAudit(models.AbstractModel):
    _name = 'report.odomate_account_ledger_reports.report_journal_audit'
    _description = "Journals Audit Report"

    @api.model
    def _odomate_tax_table(self, journal_domain, currency):
        move_line = self.env['account.move.line']
        net_amounts = {}
        tax_amounts = {}
        taxes = self.env['account.tax']
        for tax, balance in move_line._read_group(
            journal_domain + [('tax_ids', '!=', False)], ['tax_ids'], ['balance:sum']
        ):
            if tax:
                net_amounts[tax.id] = balance
                taxes |= tax
        for tax, balance in move_line._read_group(
            journal_domain + [('tax_line_id', '!=', False)], ['tax_line_id'], ['balance:sum']
        ):
            if tax:
                tax_amounts[tax.id] = balance
                taxes |= tax

        rows = []
        for tax in taxes.sorted(lambda record: (record.sequence, record.id)):
            sign = -1.0 if tax.type_tax_use == 'sale' else 1.0
            net = sign * net_amounts.get(tax.id, 0.0)
            amount = sign * tax_amounts.get(tax.id, 0.0)
            if currency.is_zero(net) and currency.is_zero(amount):
                continue
            rows.append({'name': tax.name, 'net': net, 'tax': amount})
        return rows

    @api.model
    def _get_report_values(self, docids, data=None):
        report_filter = self.env['odomate.account.report.filter']
        report_filter._odomate_check_report_access()
        options = self.env[
            'odomate.account.journal.audit.wizard'
        ]._odomate_options_from_data(data)

        company = options['company']
        currency = company.currency_id
        show_currency = options['amount_currency'] and self.env.user.has_group(MULTI_CURRENCY_GROUP)
        move_line = self.env['account.move.line']

        base_domain = report_filter._odomate_options_line_domain(options)
        order = SORT_ORDERS.get(options['sort_selection']) or SORT_ORDERS['move_name']
        journals = self.env['account.journal'].search(
            [('id', 'in', options['journals'].ids)], order='sequence, type, code'
        )

        blocks = []
        for journal in journals:
            journal_domain = base_domain + [('journal_id', '=', journal.id)]
            lines = move_line.search(journal_domain, order=order)
            rows = [{
                'move_name': line.move_name or '',
                'date': line.date,
                'account_label': report_filter._odomate_account_label(line.account_id),
                'partner': line.partner_id.display_name or '',
                'label': line.name or '',
                'debit': line.debit,
                'credit': line.credit,
                'amount_currency': line.amount_currency,
                'currency': line.currency_id if line.currency_id != currency else False,
            } for line in lines]
            blocks.append({
                'journal': journal,
                'journal_label': ' '.join(part for part in (journal.code, journal.name) if part),
                'rows': rows,
                'debit': sum(line.debit for line in lines),
                'credit': sum(line.credit for line in lines),
                'tax_rows': self._odomate_tax_table(journal_domain, currency),
            })

        return {
            'doc_ids': docids,
            'doc_model': options['wizard_model'],
            'data': data,
            'company': company,
            'currency': currency,
            'header': report_filter._odomate_header_values(options),
            'options': options,
            'blocks': blocks,
            'show_currency': show_currency,
        }
