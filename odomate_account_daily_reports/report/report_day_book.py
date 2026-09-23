from odoo import api, models

MULTI_CURRENCY_GROUP = 'base.group_multi_currency'

DAY_BOOK_ORDER = 'date, journal_id, move_name, id'


class ReportOdomateDayBook(models.AbstractModel):
    _name = 'report.odomate_account_daily_reports.report_day_book'
    _description = "Day Book Report"

    @api.model
    def _odomate_day_blocks(self, lines, currency):
        blocks = []
        current = None
        for line in lines:
            if current is None or current['date'] != line.date:
                current = {
                    'date': line.date,
                    'rows': [],
                    'debit': 0.0,
                    'credit': 0.0,
                    'difference': 0.0,
                }
                blocks.append(current)
            current['rows'].append({
                'journal': line.journal_id.code or line.journal_id.name or '',
                'move_name': line.move_name or '',
                'partner': line.partner_id.display_name or '',
                'ref': line.ref or '',
                'label': line.name or '',
                'debit': line.debit,
                'credit': line.credit,
                'amount_currency': line.amount_currency,
                'currency': line.currency_id if line.currency_id != currency else False,
            })
            current['debit'] += line.debit
            current['credit'] += line.credit
        for block in blocks:
            block['difference'] = block['debit'] - block['credit']
        return blocks

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
            'odomate.account.day.book.wizard'
        ]._odomate_options_from_data(data)

        company = options['company']
        currency = company.currency_id
        show_currency = self.env.user.has_group(MULTI_CURRENCY_GROUP)

        domain = report_filter._odomate_options_line_domain(options)
        lines = self.env['account.move.line'].search(domain, order=DAY_BOOK_ORDER)

        blocks = self._odomate_day_blocks(lines, currency)

        totals = {
            'debit': sum(block['debit'] for block in blocks),
            'credit': sum(block['credit'] for block in blocks),
        }
        totals['difference'] = totals['debit'] - totals['credit']

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
