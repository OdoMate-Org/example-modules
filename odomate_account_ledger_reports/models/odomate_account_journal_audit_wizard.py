from odoo import api, fields, models

MULTI_CURRENCY_GROUP = 'base.group_multi_currency'


def _default_journals(record):
    return record.env['account.journal'].search(
        [
            ('company_id', '=', record.env.company.id),
            ('type', 'in', ['sale', 'purchase']),
        ],
        order='sequence, type, code',
    ).ids


class OdomateAccountJournalAuditWizard(models.TransientModel):
    _name = 'odomate.account.journal.audit.wizard'
    _inherit = ['odomate.account.report.filter']
    _description = "Journals Audit Report Dialog"

    _odomate_report_xmlid = 'action_report_odomate_journal_audit'

    journal_ids = fields.Many2many(
        required=True,
        default=lambda self: _default_journals(self),
    )
    sort_selection = fields.Selection(
        selection=[
            ('date', "Date"),
            ('move_name', "Entry Number"),
        ],
        string="Sort Entries By",
        required=True,
        default='move_name',
    )
    amount_currency = fields.Boolean(
        string="Show Amount in Currency",
        groups=MULTI_CURRENCY_GROUP,
    )

    def _odomate_report_data(self):
        data = super()._odomate_report_data()
        amount_currency = False
        if self.env.user.has_group(MULTI_CURRENCY_GROUP):
            amount_currency = bool(self.amount_currency)
        data.update({
            'sort_selection': self.sort_selection,
            'amount_currency': amount_currency,
        })
        return data

    @api.model
    def _odomate_options_from_data(self, data):
        options = super()._odomate_options_from_data(data)
        options.update({
            'sort_selection': data.get('sort_selection') or 'move_name',
            'amount_currency': bool(data.get('amount_currency')),
        })
        return options
