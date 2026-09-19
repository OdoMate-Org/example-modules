from collections import defaultdict

from odoo import api, models

MULTI_CURRENCY_GROUP = 'base.group_multi_currency'


class ReportOdomatePartnerLedger(models.AbstractModel):
    _name = 'report.odomate_account_ledger_reports.report_partner_ledger'
    _description = "Partner Ledger Report"

    @api.model
    def _odomate_items_domain(self, options):
        report_filter = self.env['odomate.account.report.filter']
        domain = report_filter._odomate_options_line_domain(options)
        domain += [
            ('account_id.account_type', 'in', options['account_types']),
            ('partner_id', '!=', False),
        ]
        if options['partners']:
            domain.append(('partner_id', 'in', options['partners'].ids))
        if not options['reconciled']:
            domain.append(('full_reconcile_id', '=', False))
        return domain

    @api.model
    def _get_report_values(self, docids, data=None):
        report_filter = self.env['odomate.account.report.filter']
        report_filter._odomate_check_report_access()
        options = self.env[
            'odomate.account.partner.ledger.wizard'
        ]._odomate_options_from_data(data)

        company = options['company']
        currency = company.currency_id
        show_currency = options['amount_currency'] and self.env.user.has_group(MULTI_CURRENCY_GROUP)

        lines = self.env['account.move.line'].search(
            self._odomate_items_domain(options), order='partner_id, date, move_name, id'
        )

        grouped = defaultdict(list)
        for line in lines:
            grouped[line.partner_id.id].append(line)

        partners = lines.partner_id.sorted(lambda partner: (partner.display_name or '', partner.id))

        blocks = []
        for partner in partners:
            partner_lines = grouped.get(partner.id, [])
            rows = []
            running = 0.0
            for line in partner_lines:
                running += line.balance
                rows.append({
                    'date': line.date,
                    'journal': line.journal_id.code or line.journal_id.name or '',
                    'account_label': report_filter._odomate_account_label(line.account_id),
                    'move_name': line.move_name or '',
                    'ref': line.ref or '',
                    'label': line.name or '',
                    'debit': line.debit,
                    'credit': line.credit,
                    'balance': running,
                    'amount_currency': line.amount_currency,
                    'currency': line.currency_id if line.currency_id != currency else False,
                })
            blocks.append({
                'partner': partner,
                'partner_label': partner.display_name or '',
                'rows': rows,
                'debit': sum(line.debit for line in partner_lines),
                'credit': sum(line.credit for line in partner_lines),
                'balance': running,
                'amount_owed': sum(line.amount_residual for line in partner_lines),
            })

        totals = {
            'debit': sum(block['debit'] for block in blocks),
            'credit': sum(block['credit'] for block in blocks),
            'balance': sum(block['balance'] for block in blocks),
            'amount_owed': sum(block['amount_owed'] for block in blocks),
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
        }
