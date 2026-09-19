from odoo import api, models

SECTION_ORDER = ['sale', 'purchase']


class ReportOdomateTaxReport(models.AbstractModel):
    _name = 'report.odomate_account_ledger_reports.report_tax_report'
    _description = "Tax Report"

    @api.model
    def _odomate_represented_taxes(self, company):
        taxes = self.env['account.tax'].search(
            [
                ('company_id', '=', company.id),
                ('active', '=', True),
                ('type_tax_use', 'in', SECTION_ORDER),
            ],
            order='sequence, id',
        )
        represented = []
        seen = set()
        for tax in taxes:
            children = tax.children_tax_ids or tax
            for child in children:
                marker = (child.id, tax.type_tax_use)
                if marker in seen:
                    continue
                seen.add(marker)
                represented.append((child, tax.type_tax_use))
        return represented

    @api.model
    def _get_report_values(self, docids, data=None):
        report_filter = self.env['odomate.account.report.filter']
        report_filter._odomate_check_report_access()
        options = self.env[
            'odomate.account.tax.report.wizard'
        ]._odomate_options_from_data(data)

        company = options['company']
        currency = company.currency_id
        move_line = self.env['account.move.line']

        represented = self._odomate_represented_taxes(company)
        tax_ids = [tax.id for tax, _use in represented]
        base_domain = report_filter._odomate_options_line_domain(options)

        tax_amounts = {}
        net_amounts = {}
        if tax_ids:
            for tax, balance in move_line._read_group(
                base_domain + [('tax_line_id', 'in', tax_ids)],
                ['tax_line_id'], ['balance:sum'],
            ):
                if tax:
                    tax_amounts[tax.id] = balance
            for tax, balance in move_line._read_group(
                base_domain + [('tax_ids', 'in', tax_ids)],
                ['tax_ids'], ['balance:sum'],
            ):
                if tax:
                    net_amounts[tax.id] = balance

        sections = []
        for use in SECTION_ORDER:
            sign = -1.0 if use == 'sale' else 1.0
            rows = []
            for tax, tax_use in represented:
                if tax_use != use:
                    continue
                net = sign * net_amounts.get(tax.id, 0.0)
                amount = sign * tax_amounts.get(tax.id, 0.0)
                if currency.is_zero(net) and currency.is_zero(amount):
                    continue
                rows.append({'name': tax.name, 'net': net, 'tax': amount})
            sections.append({
                'key': use,
                'rows': rows,
                'net': sum(row['net'] for row in rows),
                'tax': sum(row['tax'] for row in rows),
            })

        return {
            'doc_ids': docids,
            'doc_model': options['wizard_model'],
            'data': data,
            'company': company,
            'currency': currency,
            'header': report_filter._odomate_header_values(options),
            'options': options,
            'sections': sections,
        }
