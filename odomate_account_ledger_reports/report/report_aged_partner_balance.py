from collections import defaultdict

from odoo import api, models

UNKNOWN_PARTNER_SORT_KEY = (1, '')


class ReportOdomateAgedPartnerBalance(models.AbstractModel):
    _name = 'report.odomate_account_ledger_reports.report_aged_partner_balance'
    _description = "Aged Partner Balance Report"
    _table = 'odomate_report_aged_partner_balance'

    @api.model
    def _odomate_items_domain(self, options):
        report_filter = self.env['odomate.account.report.filter']
        domain = report_filter._odomate_options_line_domain(options, date_from=False)
        domain.append(('account_id.account_type', 'in', options['account_types']))
        if options['partners']:
            domain.append(('partner_id', 'in', options['partners'].ids))
        return domain

    @api.model
    def _odomate_residuals_as_of(self, lines, date_to):
        adjustments = defaultdict(float)
        if lines:
            partials = self.env['account.partial.reconcile'].search(
                [
                    '|',
                    ('debit_move_id', 'in', lines.ids),
                    ('credit_move_id', 'in', lines.ids),
                    ('max_date', '<=', date_to),
                ],
                order='id',
            )
            for partial in partials:
                adjustments[partial.debit_move_id.id] -= partial.amount
                adjustments[partial.credit_move_id.id] += partial.amount
        return {line.id: line.balance + adjustments.get(line.id, 0.0) for line in lines}

    @api.model
    def _get_report_values(self, docids, data=None):
        report_filter = self.env['odomate.account.report.filter']
        report_filter._odomate_check_report_access()
        aged_wizard = self.env['odomate.account.aged.partner.wizard']
        options = aged_wizard._odomate_options_from_data(data)

        company = options['company']
        currency = company.currency_id
        date_to = options['date_to']
        buckets = options['buckets']
        bucket_keys = [bucket['key'] for bucket in buckets]

        lines = self.env['account.move.line'].search(
            self._odomate_items_domain(options), order='partner_id, date, id'
        )
        residuals = self._odomate_residuals_as_of(lines, date_to)

        per_partner = defaultdict(lambda: dict.fromkeys(bucket_keys, 0.0))
        partner_by_id = {}
        for line in lines:
            residual = residuals.get(line.id, 0.0)
            if currency.is_zero(residual):
                continue
            due_date = line.date_maturity or line.date
            age = (date_to - due_date).days
            key = aged_wizard._odomate_bucket_key(buckets, age)
            partner_id = line.partner_id.id or False
            partner_by_id[partner_id] = line.partner_id
            per_partner[partner_id][key] += residual

        rows = []
        for partner_id, amounts in per_partner.items():
            if all(currency.is_zero(amounts[key]) for key in bucket_keys):
                continue
            partner = partner_by_id.get(partner_id)
            rows.append({
                'partner': partner,
                'partner_label': partner.display_name if partner_id else False,
                'sort_key': (0, partner.display_name or '') if partner_id else UNKNOWN_PARTNER_SORT_KEY,
                'amounts': amounts,
                'total': sum(amounts[key] for key in bucket_keys),
            })
        rows.sort(key=lambda row: row['sort_key'])

        totals = {key: sum(row['amounts'][key] for row in rows) for key in bucket_keys}
        totals_grand = sum(totals[key] for key in bucket_keys)

        return {
            'doc_ids': docids,
            'doc_model': options['wizard_model'],
            'data': data,
            'company': company,
            'currency': currency,
            'header': report_filter._odomate_header_values(options),
            'options': options,
            'period_labels': [bucket['label'] for bucket in buckets[1:]],
            'bucket_keys': bucket_keys,
            'rows': rows,
            'totals': totals,
            'totals_grand': totals_grand,
        }
