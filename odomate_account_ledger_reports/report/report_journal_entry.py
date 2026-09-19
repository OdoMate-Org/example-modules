from odoo import api, models

from ..models.odomate_account_report_filter import EXCLUDED_DISPLAY_TYPES

ANALYTIC_GROUP = 'analytic.group_analytic_accounting'
MULTI_CURRENCY_GROUP = 'base.group_multi_currency'


class ReportOdomateJournalEntry(models.AbstractModel):
    _name = 'report.odomate_account_ledger_reports.report_journal_entry'
    _description = "Journal Entry Printout"

    @api.model
    def _get_report_values(self, docids, data=None):
        report_filter = self.env['odomate.account.report.filter']
        report_filter._odomate_check_report_access()

        moves = self.env['account.move'].browse(docids)
        show_currency = self.env.user.has_group(MULTI_CURRENCY_GROUP)
        show_analytic = self.env.user.has_group(ANALYTIC_GROUP)
        state_labels = dict(
            self.env['account.move']._fields['state']._description_selection(self.env)
        )

        entries = []
        for move in moves:
            company = move.company_id
            currency = company.currency_id
            lines = move.line_ids.filtered(
                lambda line: line.display_type not in EXCLUDED_DISPLAY_TYPES
            ).sorted(lambda line: (line.sequence, line.id))
            analytic_labels = (
                report_filter._odomate_analytic_labels(lines) if show_analytic else {}
            )
            entries.append({
                'move': move,
                'company': company,
                'currency': currency,
                'state_label': state_labels.get(move.state, ''),
                'rows': [{
                    'account_label': report_filter._odomate_account_label(line.account_id),
                    'label': line.name or '',
                    'partner': line.partner_id.display_name or '',
                    'analytic': analytic_labels.get(line.id, ''),
                    'debit': line.debit,
                    'credit': line.credit,
                    'amount_currency': line.amount_currency,
                    'line_currency': line.currency_id if line.currency_id != currency else False,
                } for line in lines],
                'debit': sum(line.debit for line in lines),
                'credit': sum(line.credit for line in lines),
            })

        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': moves,
            'data': data,
            'entries': entries,
            'show_currency': show_currency,
            'show_analytic': show_analytic,
        }
