from odoo import api, fields, models

from .odomate_account_report_filter import (
    ACCOUNT_TYPES_BY_RESULT_SELECTION,
    RESULT_SELECTION,
)

MULTI_CURRENCY_GROUP = 'base.group_multi_currency'


class OdomateAccountPartnerLedgerWizard(models.TransientModel):
    _name = 'odomate.account.partner.ledger.wizard'
    _inherit = ['odomate.account.report.filter']
    _description = "Partner Ledger Report Dialog"

    _odomate_report_xmlid = 'action_report_odomate_partner_ledger'

    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='odomate_pl_wizard_partner_rel',
        column1='wizard_id',
        column2='partner_id',
        string="Partners",
        help="Leave empty to cover every partner with receivable or payable items.",
    )
    result_selection = fields.Selection(
        selection=RESULT_SELECTION,
        string="Account Type",
        required=True,
        default='customer',
    )
    reconciled = fields.Boolean(
        string="Include Settled Items",
        default=False,
        help="Also print journal items that are already fully reconciled.",
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
            'partner_ids': self.partner_ids.ids,
            'result_selection': self.result_selection,
            'reconciled': bool(self.reconciled),
            'amount_currency': amount_currency,
        })
        return data

    @api.model
    def _odomate_options_from_data(self, data):
        options = super()._odomate_options_from_data(data)
        result_selection = data.get('result_selection') or 'customer'
        options.update({
            'partners': self.env['res.partner'].browse(data.get('partner_ids') or []),
            'result_selection': result_selection,
            'account_types': ACCOUNT_TYPES_BY_RESULT_SELECTION[result_selection],
            'reconciled': bool(data.get('reconciled')),
            'amount_currency': bool(data.get('amount_currency')),
        })
        return options
