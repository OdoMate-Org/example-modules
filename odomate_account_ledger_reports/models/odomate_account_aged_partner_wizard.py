from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .odomate_account_report_filter import (
    ACCOUNT_TYPES_BY_RESULT_SELECTION,
    RESULT_SELECTION,
)


class OdomateAccountAgedPartnerWizard(models.TransientModel):
    _name = 'odomate.account.aged.partner.wizard'
    _inherit = ['odomate.account.report.filter']
    _description = "Aged Partner Balance Report Dialog"

    _odomate_report_xmlid = 'action_report_odomate_aged_partner'

    date_to = fields.Date(
        string="As of Date",
        required=True,
        default=fields.Date.context_today,
    )
    period_length = fields.Integer(
        string="Period Length (days)",
        required=True,
        default=30,
    )
    result_selection = fields.Selection(
        selection=RESULT_SELECTION,
        string="Account Type",
        required=True,
        default='customer',
    )
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='odomate_aged_wizard_partner_rel',
        column1='wizard_id',
        column2='partner_id',
        string="Partners",
    )

    def _odomate_check_filter(self):
        super()._odomate_check_filter()
        if self.period_length <= 0:
            raise UserError(_("The period length must be at least one day."))
        if not self.date_to:
            raise UserError(_("Set the date the ageing is measured at."))

    def _odomate_report_data(self):
        data = super()._odomate_report_data()
        result_selection = self.result_selection
        data.update({
            'date_from': False,
            'period_length': self.period_length,
            'result_selection': result_selection,
            'partner_ids': self.partner_ids.ids,
        })
        return data

    @api.model
    def _odomate_options_from_data(self, data):
        options = super()._odomate_options_from_data(data)
        result_selection = data.get('result_selection') or 'customer'
        period_length = int(data.get('period_length') or 30)
        options.update({
            'date_from': False,
            'period_length': period_length,
            'result_selection': result_selection,
            'account_types': ACCOUNT_TYPES_BY_RESULT_SELECTION[result_selection],
            'partners': self.env['res.partner'].browse(data.get('partner_ids') or []),
            'buckets': self._odomate_aged_buckets(period_length),
        })
        return options

    @api.model
    def _odomate_aged_buckets(self, period_length):
        period_length = max(int(period_length or 30), 1)
        buckets = [{
            'key': 'not_due',
            'label': False,
            'min_age': None,
            'max_age': 0,
        }]
        for index in range(1, 5):
            low = (index - 1) * period_length + 1
            high = index * period_length
            buckets.append({
                'key': 'age_%s' % index,
                'label': '%s - %s' % (low, high),
                'min_age': low,
                'max_age': high,
            })
        buckets.append({
            'key': 'older',
            'label': '+%s' % (4 * period_length),
            'min_age': 4 * period_length + 1,
            'max_age': None,
        })
        return buckets

    @api.model
    def _odomate_bucket_key(self, buckets, age):
        for bucket in buckets:
            if bucket['min_age'] is not None and age < bucket['min_age']:
                continue
            if bucket['max_age'] is not None and age > bucket['max_age']:
                continue
            return bucket['key']
        return buckets[-1]['key']
